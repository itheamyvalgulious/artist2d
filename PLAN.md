# 商业级 2D 像素游戏美术资产生成 Agent 工程实现计划书

## 0. 全局技术栈与度量衡规范（Global Spec）

1. **核心技术栈**：
   - **3D 动作与真值渲染器**：本地 **Godot Engine 4.x**（通过无头命令行 `godot --headless --rendering-driver vulkan` 或 `opengl3` 执行 GDScript 批处理渲染脚本）。
   - **AI 图像生成与重绘引擎**：纯云端 API 调用，固定使用 **`gpt-image-2.5-flare`**（高频快速生成/局部重绘）与 **`gpt-image-2.5-sunburst`**（高复杂度整表重绘/母图生成），严禁引入任何本地 Diffusion 模型依赖。
   - **确定性像素后处理引擎**：Python (`numpy`, `scipy.ndimage`, `opencv-python`, `pillow`, `scikit-image`)。
2. **全局像素度量衡（`PixelPipelineConfig`）**：
   - 标准地块尺寸：`TILE_SIZE = 32`（真像素）。
   - 角色基准帧画布：`CHAR_CANVAS = (64, 64)`（真像素）。
   - API 画布倍率：`UPSCALE_FACTOR = 16`（即 `32x32` 真像素对应 `512x512` API 画布；`64x64` 真像素对应 `1024x1024` 画布）。
   - **全局调色板锁死（Master Palette Quantization）**：预置商业级 32/64 色调色板 $P$，所有 API 产出的图像在采样后必须转换至 CIE-LAB 空间，按最近邻欧氏距离强制吸附至 $P$，Alpha 通道按 $\alpha \ge 128 \Rightarrow 255, \alpha < 128 \Rightarrow 0$ 二值化。

---

## 模块一：角色序列帧管线（Godot 参数化木偶 $\rightarrow$ GPT-Image 整表重绘 $\rightarrow$ 众数重采样与连通块追踪）

### 1.1 基于 Godot 4 的参数化木偶与动作库渲染器
**目标**：利用 Godot 4 的 `SkeletonProfileHumanoid` 零成本挂载海量动作库（Mixamo / KayKit `.glb`），通过代码实时调整头身比，导出带 Z 轴透视深度的动作序列长图与像素级运动真值。

* **Godot 场景与骨骼架构（`MannequinRig.tscn`）**：
  - 根节点包含一个绑定了标准 `SkeletonProfileHumanoid` 的低模胶囊体/方块木偶人 `Skeleton3D`。
  - **刚体挂点（深度动作核心）**：在 `RightHand`、`LeftHand`、`Head` 骨骼下挂载 `BoneAttachment3D` 节点，用于挂载大剑、盾牌、头盔等基础几何体（如举剑格挡时，剑与手臂自动产生正确的 3D 前后遮挡与透视缩短）。
  - **参数化身体比例调节（GDScript 实现）**：
    - 接收 JSON 参数 `{"head_scale": 1.6, "torso_len": 1.0, "limb_len": 0.9, "shoulder_width": 1.2}`。
    - 遍历目标骨骼，通过 `skeleton.set_bone_pose_scale(bone_idx, scale_vec)` 调整比例；同时对子骨骼应用逆缩放补偿（或在 `BoneAttachment3D` 上重置正交基），防止旋转时产生剪切形变（Shear）。
* **双视口同步烘焙输出（GDScript Batch Renderer）**：
  - 架设正交相机 `Camera3D (projection = PROJECTION_ORTHOGONAL)`，从动作库 `AnimationLibrary` 加载指定动作（如 `sword_block`, `run`, `attack_combo`），均匀抽取 $N=8$ 帧，水平拼接输出三份对齐数据：
    1. `sheet_shaded.png`（分辨率 $4096 \times 512$，每帧 $512 \times 512$）：采用 Godot `StandardMaterial3D (diffuse_mode = TOON, specular_mode = TOON)` 渲染带清晰三阶明暗与体积感的彩色木偶序列长图。
    2. `sheet_part_id.png`（分辨率 $512 \times 64$，直接按真像素尺寸无抗锯齿渲染）：切换为 `ShadingMode = UNSHADED` 纯色材质，身体各部位固定唯一 RGB 值（头 `#FF0000`、躯干 `#00FF00`、左臂 `#0000FF`、右臂 `#FFFF00`、左腿 `#FF00FF`、右腿 `#8800FF`、武器 `#00FFFF`、盾牌 `#FFFFFF`）。
    3. `sheet_motion.json` / `.npy`：在每一帧采样 $64 \times 64$ 网格对应的 3D 表面点，通过 `camera.unproject_position(world_pos)` 计算第 $t$ 帧每个真像素 $(x, y)$ 相对于第 $t-1$ 帧与第 $0$ 帧的精确 2D 像素位移向量 $(\Delta x, \Delta y)$。

### 1.2 基于 `gpt-image-2.5-sunburst` 的融合立绘整表重绘
**目标**：无需本地 ControlNet，通过**复合拼板（Composite Sheet Prompting）**让 `gpt-image-2.5-sunburst` 一次性产出动作与外观高度统一的序列帧。

* **算法流程（`generate_character_spritesheet`）**：
  1. **基准角色立绘生成**：调用 `gpt-image-2.5-sunburst` 生成单张角色正侧视（45° Ortho）基准像素立绘 `char_ref.png`，经过【1.3 核内众数重采样】洗成纯净的 $64 \times 64$ 真像素后再放大回 $512 \times 512$（确保参考图本身是绝对标准的像素风格）。
  2. **构造视觉上下文复合长图（Visual Context Board）**：
     - 创建一张 $(N+1) \times 1$ 的画布（例如 $9$ 格，尺寸 $4608 \times 512$ 或分两批 $5 \times 1$ 拼板）。
     - **第 0 格（最左侧）**：放入 `char_ref.png`，并在其上方/下方叠加第 $0$ 帧的木偶人小图作为姿态映射示例（In-Context Pair）。
     - **第 $1 \sim N$ 格（右侧）**：依次排入 Godot 导出的 `sheet_shaded.png` 各帧木偶图。
  3. **调用 `gpt-image-2.5-sunburst` 编辑接口（Image-to-Image / Edit API）**：
     - 构造掩码 `mask.png`：第 $0$ 格全黑（锁定参考立绘不变），右侧 $1 \sim N$ 格全白（待重绘区域）。
     - 提示词工程（Prompt）：
       > `"A horizontal 2D pixel art sprite sheet on a solid #FF00FF magenta background. Panel 0 on the far left is the master character reference. Transform the 3D colored mannequins in Panels 1 to N into this exact same character, strictly preserving the exact limb positions, weapon angles, shield depth occlusion, and body proportions of each mannequin frame. Flat crisp pixel clusters, 32-color palette, 1px dark outline, zero anti-aliasing, zero motion blur."`

### 1.3 核心后处理：核内众数网格重采样（Core-Window Mode Pooling）
**目标**：直接重写像素，消除 `gpt-image-2.5` 产生的亚像素抗锯齿、网格偏移和杂色。

* **具体算法（`resample_to_true_pixel`）**：
  1. 将 API 返回的单帧高清图（$512 \times 512$）划分为 $64 \times 64$ 个网格单元，每格尺寸 $M \times M$（$M = 8$）。
  2. 对每个网格 $(i, j)$，切片出 $8 \times 8$ 像素块 $B_{i,j}$。
  3. **核心窗口裁切**：剔除四周各 $2\text{px}$ 的边缘抗锯齿污染区，仅保留中心 $4 \times 4$ 的核心窗口 $W_{i,j}$。
  4. **背景剥离与调色板众数投票**：
     - 若 $W_{i,j}$ 中距离背景色 `#FF00FF`（洋红）LAB 色差 $< 15$ 的像素占比 $> 50\%$，则输出透明像素 $O[i, j] = (0,0,0,0)$。
     - 否则，将 $W_{i,j}$ 内剩余像素全部映射至全局调色板 $P$ 的索引，取**出现频次最高（众数 Mode）**的调色板颜色写入 $O[i, j]$。

### 1.4 核心后处理：跨帧连通块追踪与静止像素覆写（Connected-Component Tracking & Overwrite）
**目标**：利用 Godot 导出的真值掩码 `sheet_part_id.png` 与位移场 `sheet_motion.npy`，直接修改像素，消灭帧间抖动（Boiling）与细节丢失。

* **算法步骤 A：静止部件像素级硬锁（Static Part Pixel Locking）**
  - 遍历第 $t$ 帧（$t \ge 1$）的每个真像素 $(x, y)$，读取 Godot 导出的位移向量 $\mathbf{v}_{t-1 \to t}(x, y)$ 与部件 ID $P_t(x, y)$。
  - 若 $\|\mathbf{v}_{t-1 \to t}(x, y)\|_2 < 0.25\text{px}$ 且 $P_t(x, y) == P_{t-1}(x, y) \neq \text{Background}$：
    - **执行像素硬覆写**：直接令 $O_t[x, y] = O_{t-1}[x, y]$（确保站立的腿部、未动的躯干在连续帧之间 1 个像素都不跳动）。
* **算法步骤 B：关键小连通块跨帧追踪与模板覆写（Feature Component Stamp Overwrite）**
  1. **基准帧特征提取**：在第 $0$ 帧真像素图 $O_0$ 中，使用 `scipy.ndimage.label` 按调色板颜色提取所有面积在 $1 \le \text{Area}(C) \le 10$ 像素的高对比度独立连通块（如眼睛高光、护额宝石、腰带扣），记录其像素坐标集、颜色及所属的 Godot `Part_ID`。
  2. **跨帧重定位与遮挡判定**：在第 $t$ 帧，根据该 `Part_ID` 从第 $0$ 帧到第 $t$ 帧的骨骼刚体位移 $(\Delta x_{0\to t}, \Delta y_{0\to t})$，推算连通块 $C_m$ 的目标中心 $(\hat{x}_t, \hat{y}_t) = \text{round}(x_0 + \Delta x_{0\to t}, y_0 + \Delta y_{0\to t})$。
  3. **遮挡检查**：读取 `sheet_part_id.png` 第 $t$ 帧在 $(\hat{x}_t, \hat{y}_t)$ 处的 ID。若该处已被其他部件覆盖（例如格挡动作中盾牌 `#FFFFFF` 挡住了胸口 `#00FF00`），则跳过修复。
  4. **缺失/畸变直接覆写**：若未被遮挡，在 $O_t$ 的 $(\hat{x}_t, \hat{y}_t)$ 周围 $3 \times 3$ 邻域内查找同色连通块 $C_m^{(t)}$。若未找到（AI 漏画）或像素数相差超过 $1\text{px}$，先用该部件周围的主色调填充清理 $3 \times 3$ 区域，再将第 $0$ 帧的特征块 $C_m^{(0)}$ **直接按像素粘贴覆写**至 $(\hat{x}_t, \hat{y}_t)$。

---

## 模块二：环境无缝地块管线（AI 多材质同步生成 $\rightarrow$ 环面平移无缝化 $\rightarrow$ 47-Tile 合成）

### 2.1 基于 `gpt-image-2.5-flare` 的多材质风格同步初始生成（Coherent Multi-Material Genesis）
**目标**：从零开始，确保草地、泥土、石砖、水面等基础材质在色温、像素颗粒度、明暗对比度上 100% 处于同一世界观，绝不单独盲抽。

* **算法流程（`generate_raw_material_pack`）**：
  1. **构造 $2 \times 2$ 材质网格约束板（Material Grid Template）**：
     - 创建一张 $1024 \times 1024$ 的引导底图，均分为 4 个 $512 \times 512$ 象限（左上：草地、右上：泥土、左下：青石砖、右下：深水）。
     - 在每个象限填入由全局调色板 $P$ 抽取的对应色系高频柏林噪声（Perlin Noise）底色块，用来锁死 AI 生成的整体明度与色相区间。
  2. **一次性同步生成**：
     - 调用 `gpt-image-2.5-flare`，提示词：
       > `"A 2x2 grid of top-down orthographic 2D pixel art terrain textures: [Top-Left] lush grass, [Top-Right] packed dirt, [Bottom-Left] ancient cobblestone, [Bottom-Right] water ripples. Strictly flat top-down view, no perspective horizon, uniform lighting from top-left, crisp large pixel clusters, shared color palette."`
     - 将返回的 $1024 \times 1024$ 图像切分为 4 张独立的 $512 \times 512$ 初始贴图 $I_{init}^{(1 \dots 4)}$。

### 2.2 环面循环平移与十字接缝重绘（Toroidal Offset & Cross-Seam Inpainting）
**目标**：将 2.1 生成的任意初始贴图 $I_{init}$ 转化为上下左右 100% 像素级无缝平铺的基准砖 $T$。

* **算法流程（`make_seamless_tile`）**：
  1. **环面循环平移**：对 $512 \times 512$ 的 $I_{init}$ 沿 X、Y 轴各循环平移 $256\text{px}$：
     $$I_{shifted} = \text{np.roll}(I_{init}, \text{shift}=(256, 256), \text{axis}=(0, 1))$$
     *此时原图四条不连续的外边缘集中在画面正中央 $(x=256, y=256)$ 形成十字接缝，而新图的外边缘天然连续。*
  2. **构造保护外框的十字掩码（Border-Safe Cross Mask）**：
     - 生成 $512 \times 512$ 掩码 $M$：令十字带 $|x - 256| \le 64$ 或 $|y - 256| \le 64$ 区域为待重绘区（白色 $255$）。
     - **外边缘死锁**：强制令距离四条外边框 $32\text{px}$ 以内的所有像素 $M[y, x] = 0$（黑色保留区），确保外边界绝对不被 API 改动。
  3. **API 局部重绘与真像素采样**：
     - 调用 `gpt-image-2.5-flare` 的 Inpaint 接口重绘 $(I_{shifted}, M)$，消除十字接缝。
     - 将重绘结果送入【1.3 核内众数重采样】（步长 $M = 16$），输出 $32 \times 32$ 真像素无缝基准砖 $T$。
     - **无缝度自检**：计算右边界列 $T[:, 31]$ 与左边界列 $T[:, 0]$、下边界行 $T[31, :]$ 与上边界行 $T[0, :]$ 的色差；若个别像素存在突变，用 $2\text{px}$ 宽度的邻域调色板中值滤波平滑接缝。

### 2.3 异质材质高度调制 47-Tile 自动合成器（Height-Modulated Blob Autotiler）
**目标**：输入两张无缝基准砖（上层材质 $T_A$ 如草地，下层材质 $T_B$ 如泥土），纯算法直接生成全套 47 张标准 Autotile 过渡图集。

* **算法流程（`synthesize_47_autotiles`）**：
  1. **纹理高度场提取**：根据 $T_A$ 的像素明度与连通色块中心距离，计算归一化高度图 $H_A(x, y) \in [0, 1]$（使整簇草叶或整块石头的中心高度接近 $1$，边缘缝隙接近 $0$）。
  2. **47 态距离场生成**：遍历 8-邻域有效组合（共 47 种拓扑状态），对每种状态生成 $32 \times 32$ 的基准掩码距离场 $W_{mask}(x, y) \in [0, 1]$。
  3. **有机凹凸硬裁切**：
     - 计算融合判别函数：$S(x, y) = W_{mask}(x, y) + 0.35 \cdot (H_A(x, y) - 0.5)$。
     - 若 $S(x, y) > 0.5$，输出上层像素 $T_A(x, y)$；否则输出下层像素 $T_B(x, y)$（保证石块或草丛以完整颗粒凸出到泥土上，绝不把单颗石头切碎或产生半透明混合）。
  4. **交界厚度阴影烘焙**：对所有满足 $S(x, y) \le 0.5$（下层泥土）但上方像素 $S(x, y-1) > 0.5$（上层草皮下沿）的坐标 $(x, y)$，将其颜色在全局调色板 $P$ 中向暗部降低 1 个色阶，形成 1px 立体咬合阴影。

---

## 模块三：中型巨构处理方法（Multi-Tile Stamp：接地融合生成 $\rightarrow$ 差异抠图 $\rightarrow$ 网格切分与遮挡分层）

**适用对象**：占 $2 \times 2$ 至 $6 \times 6$ 格（$64 \times 64$ 至 $192 \times 192$ 真像素）的独立建筑、古树、雕像、祭坛。

* **具体算法与流程（`generate_medium_megastructure`）**：
  1. **构造接地画布（Grounded Canvas Construction）**：
     - 设目标占 $W_g \times H_g$ 格（以 $4 \times 5$ 格即 $128 \times 160$ 真像素为例，API 画布为 $1024 \times 1280$）。
     - 底图构造：画布底部 $2$ 行网格（高度 $512\text{px}$）平铺填充模块二生成的无缝地面砖 $T_{ground}$（放大至 API 尺度），上部 $3$ 行网格填充纯洋红 `#FF00FF`。
     - 掩码构造：中心留出巨构轮廓包络区为白色（重绘），底部四角边缘保留一圈真实的 $T_{ground}$ 不变作为纹理锚点。
  2. **调用 `gpt-image-2.5-sunburst` 生成**：
     - 提示词要求生成完整物体，顶部与洋红背景分离，底部树根/台阶/墙基自然扎根并投射阴影在底部的 $T_{ground}$ 地面上。
  3. **真像素重采样与差异抠图（Difference Matting）**：
     - 经【1.3 核内众数重采样】还原为 $128 \times 160$ 真像素图 $I_{stamp}$。
     - **上部抠图**：洋红 `#FF00FF` 区域直接置为 $\alpha = 0$。
     - **底部接地抠图**：对比底部区域 $I_{stamp}[y, x]$ 与原地面平铺图 $T_{tiled}[y, x]$：
       - 若二者调色板索引相同（未被物体覆盖的原地面），置为 $\alpha = 0$；
       - 若 $I_{stamp}[y, x]$ 色相与地面一致但明度低 $1 \sim 2$ 档（AI 画出的接地阴影），转换为通用半透明阴影像素 $(0, 0, 0, 128)$；
       - 其余像素保留为不透明物体本体（$\alpha = 255$）。
  4. **网格切分与 Y-Sort 遮挡元数据生成**：
     - 按 $32 \times 32$ 切分为 $4 \times 5 = 20$ 张子图块，导出 `stamp_metadata.json`：
       - 底部 $2$ 行（$y \in \{3, 4\}$）标记 `layer = "sorted_body", collision = true`，记录底部中心点为 Y-Sort 排序锚点 `pivot_y`。
       - 上部 $3$ 行（$y \in \{0, 1, 2\}$）标记 `layer = "overhead_canopy", collision = false`（角色走到树后/屋檐后时由引擎自动遮挡角色）。

---

## 模块四：超大型巨构处理方法（九宫格结构件 + 跨网格覆盖物 + 确定性装配烘焙管线）

**适用对象**：占 $10 \times 10$ 至 $30 \times 30$ 格以上的巨型城墙、地下城遗迹、高塔、巨型机械体。

### 4.1 九宫格结构部件生成（Modular 9-Slice Kit Generation）
1. **母图同步生成（Master 9-Slice Sheet）**：
   - 调用 `gpt-image-2.5-sunburst` 生成一张 $1536 \times 1536$（对应 $3 \times 3$ 个 $64 \times 64$ 真像素大砖块，总计 $192 \times 192$ 真像素）的紧凑巨构立面母图（例如“古老黑曜石城墙立面，带顶部垛口、左右厚重包角石柱、底部斜坡基座、中心石砖墙面”），背景为 `#FF00FF`。
   - 经【1.3 核内众数重采样】得到 $192 \times 192$ 真像素母图，切分为 $3 \times 3$ 共 9 个 $64 \times 64$ 的基础部件：
     - 四角件：$K_{TL}, K_{TR}, K_{BL}, K_{BR}$
     - 四边件：顶部檐口 $E_T$、底部基座 $E_B$、左立柱 $E_L$、右立柱 $E_R$
     - 中心墙体件：$C_1$
2. **单轴/双轴无缝化与变体扩充（1D/2D Seamless Enforcement）**：
   - **中心件变体扩充（$C_1, C_2, C_3$）**：对 $C_1$ 执行【2.2 环面平移十字重绘】得到双向无缝砖；并再次调用 `gpt-image-2.5-flare` 在保持外框 $8\text{px}$ 锁死的前提下重绘内部两次，得到砖缝排布略有不同的 3 个无缝中心变体 $C_1, C_2, C_3$。
   - **水平延展边（$E_T, E_B$）单轴无缝化**：仅沿水平 X 轴平移半幅宽度（`np.roll(E_T, shift=32, axis=1)`），仅对垂直中线带 $x \in [24, 40]$ 调用 `gpt-image-2.5-flare` 重绘，实现左右无限无缝拼接，同时完整保留顶部垛口/底部基座与 `#FF00FF` 交界的凹凸轮廓。
   - **垂直延展边（$E_L, E_R$）单轴无缝化**：仅沿垂直 Y 轴平移半幅高度（`np.roll(E_L, shift=32, axis=0)`），仅对水平中线带 $y \in [24, 40]$ 重绘，实现上下无限无缝拼接。

### 4.2 跨网格覆盖物生成（Multi-Tile Breakup Decals Generation）
**目标**：生成跨越 $2 \times 3$ 或 $3 \times 4$ 格的大尺度非对称破坏件与装饰件，专门用于盖住结构件拼接缝。

* **生成流程（`generate_macro_decals`）**：
  1. 以4.1生成的中心墙体砖 $C_1$ 平铺拼成一块 $3 \times 3$ 格（$192 \times 192$ 真像素，API 画布 $1536 \times 1536$）的临时背景墙。
  2. 构造中心不规则椭圆形掩码（四周留出至少 $32\text{px}$ 原墙体不改），调用 `gpt-image-2.5-flare` Inpaint 接口，分别按以下三类提示词在墙体上直接生长出覆盖物：
     - **破损类**：`"A massive jagged structural crack and collapsed stone cavity spanning across the stone wall"`
     - **生态类**：`"Thick hanging pixel art ivy vines and overgrown moss patches clinging to the stone wall"`
     - **巨型构件类**：`"A weathered gothic stone gargoyle relief / heavy rusted iron chains bolted across the wall"`
  3. **差异提取覆盖物图层（Decal Layer Extraction）**：
     - 经【1.3 核内众数重采样】后，将生成的图与原平铺墙体 $C_1$ 逐像素比对：凡是与原墙体 $C_1$ 像素一致的外围区域全部置为透明 $\alpha = 0$，仅提取出裂缝、藤蔓、浮雕本体及其边缘 $1\text{px}$ 的接触阴影，存为带透明通道的独立大尺寸贴花资产 `decal_*.png`。

### 4.3 超大型巨构合成管线（Deterministic Macro-Assembly Pipeline）
**目标**：输入任意二值建筑蓝图矩阵 $B \in \{0, 1\}^{H \times W}$（例如 $20 \times 16$ 格的不规则城堡/遗迹拓扑），由纯确定性代码合成最终成品。

* **四步合成算法（`assemble_macro_megastructure`）**：
  1. **九宫格自动拓扑装配（Bitmask Placement）**：
     - 遍历 $B[r, c] == 1$ 的格点，根据其 4-邻域及对角邻域连通状态，自动填入对应的角件 $K_*$、边件 $E_*$。
     - 对于内部格点（上下左右均为 $1$），从中心变体池 $\{C_1, C_2, C_3\}$ 中采用 **图着色约束（Graph Coloring Constraint：保证 `(r + c)` 邻接格绝不取相同索引）** 填入，生成基础拼接大图 $I_{base}$ 与总轮廓掩码 $M_{total}$。
  2. **跨网格接缝靶向贴花（Seam-Targeted Decal Stamping）**：
     - 提取所有内部网格十字交点集合 $\mathcal{J}$。使用泊松盘采样（最小半径 $r_{\min} = 2.5$ 格）选出锚点：
       - 在屋檐下沿（$B[r-1, c] == 0$）锚点叠加**下垂生态藤蔓类** Decal；
       - 在内部墙面十字交点叠加**跨网格大裂缝 / 浮雕 / 铁链类** Decal（横跨 $2 \sim 3$ 个格子，彻底掩盖十字接缝）。
     - 使用 $M_{total}$ 对非下垂类 Decal 进行 Alpha 裁剪，防止裂缝伸出建筑外轮廓。
  3. **宏观光影与环境光遮蔽烘焙（Macro AO & Vertical Gradient Pass）**：
     - **垂直高度衰减**：计算每个像素距巨构底部的归一化高度 $h(y) \in [0, 1]$。对底部区域 $h(y) < 0.2$，结合 $4 \times 4$ Bayer 有序抖动矩阵（Ordered Dithering），将像素颜色在全局调色板 $P$ 中向暗部压低 $1$ 个色阶，赋予巨构沉重的接地体量感。
     - **内凹转角 AO**：检测布局矩阵 $B$ 的所有 L 型内凹折角，沿折角交界线两侧 $6\text{px}$ 范围内用 Bayer 抖动压暗 $1$ 个色阶。
  4. **图集去重与引擎格式导出（Tile Deduplication & Map Export）**：
     - 将烘焙好的巨构大图按 $32 \times 32$ 切分，自动哈希去重生成紧凑图集 `mega_atlas.png` 及对应的 Tilemap 布局文件 `mega_layout.json`（兼容 Godot `TileMapLayer` / Tiled 编辑器）。

---

## 5. 执行 Agent 交付架构与验收标准（Deliverables & Verification）

负责落地的 Coding Agent 需构建以下工程目录，且每一步必须通过自动化测试脚本输出可核验的图像产物：

```text
pixel_art_agent/
├── config/
│   └── pipeline_config.py       # 全局尺寸、LAB 调色板、gpt-image-2.5 API 密钥与并发配置
├── core/
│   ├── api_client.py            # 封装 gpt-image-2.5-flare / sunburst 生成与 Masked Inpaint 接口
│   ├── palette_quantizer.py     # CIE-LAB 最近邻锁色、Bayer 有序抖动、硬 Alpha 截断
│   └── grid_resampler.py        # 【模块 1.3】核内众数网格重采样（Core-Window Mode Pooling）
├── character/
│   ├── godot_mannequin/         # 【模块 1.1】Godot 4 工程：Humanoid 木偶、BoneAttachment3D、多通道导出脚本
│   ├── sheet_compositor.py      # 【模块 1.2】构造 Panel 0 参考立绘 + Panel 1..N 木偶复合长图并调用 sunburst
│   └── temporal_tracker.py      # 【模块 1.4】基于 Part_ID 与 Motion Vector 的静止锁死与连通块覆写修复
└── environment/
    ├── material_genesis.py      # 【模块 2.1】2x2 多材质同步生成
    ├── seamless_toroidal.py     # 【模块 2.2】np.roll 环面平移 + 保护外框十字重绘无缝化
    ├── autotile_47.py           # 【模块 2.3】高度场调制 47-Tile 自动合成器
    ├── stamp_medium.py          # 【模块 3】中型巨构接地 Inpaint、差异抠图与 Y-Sort 分层切分
    └── mega_macro.py            # 【模块 4】超大型巨构 9-Slice 单轴无缝、差异提取 Decal 与宏观 AO 组装管线
```

### 硬性验收指标（供独立审查会话逐项核对）：
1. **真像素纯净度**：任何输出资产放大检查，不得存在任何 $0 < \alpha < 255$ 的半透明像素，所有像素颜色 100% 属于预置调色板 $P$。
2. **角色帧间稳定性**：在待机或举剑格挡序列帧中，未发生位移的骨骼部位跨帧像素差分（Pixel Diff）必须严格为 `0`；特征小连通块（如眼睛、徽章）跨帧面积波动 $\le 1\text{px}$。
3. **地块无缝连续性**：模块二输出的无缝基准砖在 $3 \times 3$ 平铺检验图中，接缝处的梯度分布与砖块内部梯度分布无统计学显著差异（无可见十字网格线）。
4. **巨构去重复性**：模块四输出的 $15 \times 20$ 格巨构合成图中，不存在任何两个水平或垂直直接相邻的相同内部砖块，且至少 $30\%$ 的内部十字接缝被跨网格覆盖物（Decals）自然遮蔽。
