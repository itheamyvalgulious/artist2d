# Pixel Art Agent — 商业级 2D 像素游戏美术资产生成管线

按 [`PLAN.md`](PLAN.md) 落地的完整工程：**Godot 4 参数化木偶 / 动作库真值渲染 → Gemini 图像模型整表重绘 → 确定性像素后处理 → 可直接进引擎的资产**。

---

## 0. 最新批次：ship 环境（预览）

本轮按“先确认风格、再批量生成”的要求，只生成了**预览批次**。

### 0.2 新环境 `ship`（侧视角飞船内景）

- 风格：科幻 + 赛博朋克，深枪灰/海军蓝金属、青色全息灯带、紫色面板、暖色警示条。
- Tile：22 张 32px 图块，含地板/平台边缘、墙面、天花板、格栅、管道、通风口、
  警示条、星空窗；四种主材质全部通过双 KS 无缝检验。
- 中型结构（预览 3/10）：`console_bank`、`cargo_stack`、`server_rack`。
- Mega 基本元素（预览 3/20）：`hull_frame`、`viewport`、`reactor_core`。
- 整套飞船内景（mega 装配）：`output/mega/ship/ship_mega_preview.png`。
- 综合场景：`output/showcase/ship/scene.png`。
- 预览清单：
  - 图块：`output/environment/ship/tileset_preview_x8.png`
  - 图块拼合样例：`output/environment/ship/tileset_sample_x4.png`
  - 中型结构：`output/environment/ship/props/catalog_preview.png`
  - Mega 元素：`output/mega/ship/elements/catalog_preview.png`

### 0.3 隔离（本轮同时完成）

```text
output/
  character/
    knight/                 原有骑士
  environment/
    field/                  原有 2D 俯视地形
    ship/                   新 2D 侧视飞船内景 tile + 中型结构
  mega/
    field/                  原有城堡 mega
    ship/                   飞船 mega 元素 + 整船装配
  showcase/
    field/                  原有地形综合场景
    ship/                   新飞船内景综合场景
```

`environment/`、`mega/`、`showcase/` 的**直接子级只允许是 set 目录**，
`tests/test_isolation.py` 会强制检查；两套世界的同名文件不会再互相覆盖。

### 0.4 生成命令

```bash
# 飞船环境（tile + 3 中型 + 3 mega + 整船装配 + showcase）
.venv/bin/python scripts/build_ship.py

# 一键跑完 ship 预览 + 测试
.venv/bin/python scripts/run_all.py --ship
```

### 0.5 待确认后继续

- 中型结构：剩余 7 种（`med_pod`、`holo_table`、`locker_bench`、`security_door`、
  `turret`、`vending_unit`、`escape_pod`）。
- Mega 元素：剩余 17 种（目录见 `config/ship_config.py`）。
- 角色动作：`jump`、`in_air`、`shoot1`、`shoot3`、`slash1`、`slash3`、`block`，
  以及完整的 `idle→shoot1→idle` / `jump→in_air` / `in_air→shoot3→in_air` 衔接链。

确认后直接扩展 `config/ship_config.py` 的目录或 `--actions` 列表即可，代码路径已经就绪。

---

生成后端已按项目要求从 GPT Image 切换为 **Gemini 图像模型**，通过本机 **NewAPI** 网关（`http://127.0.0.1:3000`）调用：

| 管线角色 | PLAN 原模型 | 实际模型 |
|---|---|---|
| `flare`（快速局部重绘/材质细化） | `gpt-image-2.5-flare` | `gemini-3.1-flash-lite-image` |
| `sunburst`（母图/整表高质量重绘） | `gpt-image-2.5-sunburst` | `gemini-nano-banana-2.1` |

> 说明：knight 使用 3×3 复合板（1 张参考 + 8 个木偶姿势，一次调用）。

Python 环境由本目录下的 **uv** 管理（`.venv`），Godot 为 4.7.2。

---

## 1. 快速开始

```bash
# 依赖
uv sync

# 凭据（只在环境变量里；仓库不含任何 key）
export NEWAPI_KEY=...

# 环境（若没有桌面会话，可用 Xvfb 起一个虚拟 X）
export DISPLAY=:0

# 角色（全分辨率参考图 + 6 套 8 帧动作表：idle/running/attack/defend/jump/in_air）
.venv/bin/python scripts/build_character.py --character knight

# 环境材质 / 无缝砖 / 47-tile
.venv/bin/python scripts/build_environment.py

# 巨型结构（中型 4x5 + 超大型 15x20 + Tiled .tmj 导出）
.venv/bin/python scripts/build_mega.py
.venv/bin/python scripts/export_tiled.py

# 综合场景 + 可播放预览（角色 APNG/GIF、完整地形、动态水/草）
.venv/bin/python scripts/build_showcase.py
.venv/bin/python scripts/build_animations.py
.venv/bin/python -m pytest tests -q

# 或者一条命令跑完全部模块
.venv/bin/python scripts/run_all.py

# 自动审查（3D 轨迹选 clip + 视觉模型审图 + 纯净度 + 测试）
.venv/bin/python -m agent.orchestrator --verify
```

API Key / 模型可用环境变量覆盖：`NEWAPI_BASE`、`NEWAPI_KEY`、`PIXEL_MODEL_SUNBURST`、`PIXEL_MODEL_FLARE`、`GODOT_DISPLAY`。
`NEWAPI_KEY` **没有内置默认值**，缺少时脚本会直接报错；可参照 `.env.example` 用
`set -a; . ./.env; set +a` 载入（管线本身不解析 `.env`）。

---

## 2. 工程结构

```text
config/pipeline_config.py        全局尺寸、64 色主调色板、API/路径配置
config/namespaces.py             character/environment/mega/showcase 的 set 命名空间
config/ship_config.py            飞船 tile / 10 中型 / 20 mega 目录与风格提示词
core/api_client.py               Gemini generate / edit / masked-inpaint（带缓存、重试、并发）
core/palette_quantizer.py        CIE-LAB 最近邻锁色、Bayer 抖动、硬 Alpha
core/grid_resampler.py           核内众数网格重采样（Core-Window Mode Pooling）
character/godot_mannequin/       Godot 工程：参数化木偶 + KayKit 动作重定向 + 批渲染
character/sheet_compositor.py    参考图、3x3 复合整表、API 重绘、切帧、对齐
character/temporal_tracker.py    静止像素硬锁、特征块追踪/覆写、稳定性审计
character/presets.py            knight 的身份、动作、武器状态与衔接契约
environment/material_genesis.py  2x2 多材质同步生成
environment/seamless_toroidal.py 环面平移 + 十字掩膜重绘 + KS 无缝检验
environment/autotile_47.py       高度场调制 47-Tile 自动合成
environment/stamp_medium.py      中型巨构：接地生成、差异抠图、Y-Sort 分层
environment/mega_macro.py        超大型巨构：九宫格、跨格贴花、宏观 AO、图集去重
environment/ship_tiles.py        飞船 2x2 材质板 -> 22 张侧视 tile 图集
environment/ship_objects.py      中型结构 / mega 元素的生成、拟合、抠图与元数据
environment/ship_assembly.py     整船内景装配 + showcase
scripts/build_animations.py      APNG/GIF 播放、完整地形拼合、动态水/草
scripts/build_ship.py            飞船预览批次编排（tile + 3 中型 + 3 mega）
agent/motion_audit.py            3D 剑尖轨迹审计：选 attack clip、验证剑在近侧
agent/visual_review.py           NewAPI 视觉模型审核（严格 JSON rubric）
agent/orchestrator.py            串起审计/审查/纯净度/测试，写 output/AGENT_RUN.md
scripts/                         CLI 编排
tests/                           验收测试
output/                          全部生成资产 + 报告
```

---

## 3. 关键实现

### 3.1 角色管线

1. **Godot 木偶**（`character/godot_mannequin`）
   - 程序化 `Skeleton3D`，骨长/肩宽/躯干长度由 JSON 参数重建 rest 变换（无剪切）；
     `head_scale` 通过 `set_bone_pose_scale()` 作用于叶骨骼，并输出
     `SkeletonProfileHumanoid` + `BoneMap`（`assets/humanoid_bonemap.tres`）完成标准人形绑定。
   - 着色使用 `StandardMaterial3D(diffuse_mode=TOON, specular_mode=TOON)` + 平行光。
   - **KayKit Adventurers（CC0）** 的 76 个专业动作按世界旋转增量重定向到参数化骨架；姿态来自真实动作库，骨骼比例仍可调。
   - 相机固定在 `(-70, 37, 20)`（约 74° 的近侧视，从角色右侧/剑侧看）：剑臂在近景、盾在远侧，前方劈砍不会被读成盾击。
   - 武器挂点继承 KayKit `1H_Sword` 相对 `hand.r` 的真实朝向，而不是强制世界竖直；否则 `Chop` 的 3D 劈砍会被投影成侧向动作。
   - 每帧同时输出：`sheet_shaded.png`（512px/帧，三阶 Toon）、`sheet_part_id.png`（64px/帧，8 部位）、`sheet_bone_id.png`（64px/帧，刚体 ID）、`sheet_motion.json`（每根骨骼投影出的屏幕仿射，用于像素级运动真值）。
2. **复合整表重绘**：3×3 母板（左上角色参考 + 8 个木偶姿势）一次调用重绘，保证 8 帧同一角色、同一朝向。
3. **核内众数重采样**：512→64 每格 8×8，仅取中心 4×4，背景投票 >50% 置透明，其余取调色板众数。复合板的 Panel 0 使用 **全分辨率参考图**（`char_ref_canvas.png`，512，75° 右近侧视提示），不用 64px 像素化母版放大，避免剑宽/面甲细节被重新诠释。
4. **时序稳定**：
   - 逐像素计算位移，**用 `panels_to_sprites` 的每帧对齐 warp 把 Godot 仿射共轭到 sprite 空间**（`W_{t-1} A_{t-1} A_t^-1 W_t^-1`）；位移 <0.25px 且部件 ID 相同的像素从上帧硬覆盖（PLAN 1.4-A）。8 帧面板全部保留，idle / block 的盾牌与手臂位移不会被冻结。
   - 小高对比特征（眼睛、铆钉、护额）在 3×3 邻域内追踪；找不到或面积差 >1px 时，用第 0 帧同位置颜色清理后逐像素回贴第 0 帧模板（PLAN 1.4-B）。
   - 对 idle / defend 这类近静止动作，特征在画面上的位置几乎不随骨骼仿射漂移，因此以第 0 帧图像位置为搜索中心；running / attack / jump / in_air 位移大，保留 AI 原画、不做模板回贴，避免把特征贴到错误肢体（`features_repaired=0`）。
   - 清理填充色直接取第 0 帧同位置颜色，而不是“部件主色调”，避免把 1px 黑色描边涂到特征周围形成悬浮黑块。

### 3.2 环境管线

- 2×2 Perlin 约束板作为 **image-to-image 引导**，一次同步生成四种同世界观材质；草/土/石在 32×32 设计尺度生成，水改为 **同向 1px 细浪**（短断线、无圆圈、无大浪），所有材质共享同一板的色温与明暗。
- 环面平移半幅 + 保护外框十字掩膜；同时计算 **2px 邻域调色板中值**（PLAN 2.2 接缝平滑）候选，按“通过双 KS + 最大保留 2×2 结构”选择，`REPORT.md` 的 method 如实标注。草/水/石使用 `seam_median`，土使用 Gemini inpaint；并拒绝烤进亮/暗/均匀十字的 inpaint 结果（之前草地出现过整块白色十字）。
- 无缝验收采用 full-sample 与 3×3 平铺两项两样本 KS，**两项 p 都 >0.05 才算通过**；环面平移后在全部 32×32 相位中选择接缝梯度统计最典型的一个相位。
- `terrain_preview.png` 把草地/泥土/石台/水塘拼成一张完整地形图（所有边界走 47-Tile），`water_anim/`、`grass_anim/` 提供 4 帧无缝动画。
- 最终交付的无缝砖来自 AI 材质 + 调色板锁 + 相位选择；草/水/石走确定性中值接缝路径，不含 `structure_pass` 硬编码结构叠加。
- 47-Tile：连通边带状并集 + 对角切角 + 高度场调制；47 张图块两两不同（哈希测试），
  连通边 100% 上层（形状测试），并烘焙 1px 咬合阴影。水/土对的 3 水 + 1 陆凹角不再切
  `concave_notch`（否则陆地会朝水里伸出 3px 三角），改用 1px 水色 marker 保持 47 状态唯一；
  水塘内部与岸砖共用同一张 `water_seamless.png`。
  地形动态预览的水面保持统一静态基准砖，水砖动画单独放在 `water_anim/`，避免两种水混用。

### 3.3 巨构管线

- 中型（4×5 格）：接地画布 + 差异抠图 + Y-Sort 分层元数据；差异抠图保留 AI 的中央石阶/树根与接地阴影，两侧碎石噪点清理后用 AI 自身底部色带的中值纹理补齐，再把中央基座像素逐像素贴回，脚下烘焙不透明抖动阴影。Y-Sort 演示使用真实 knight 精灵，分别展示“角色在后（建筑遮挡）”与“角色在前”。
- 超大型（15×20 格）：3×3 九宫格母图 → 单轴无缝边件 + 3 个中心变体 → 图着色装配（相邻内部砖不同）→ 泊松盘接缝贴花（覆盖率 ≥30%）→ Bayer 抖动宏观 AO → 图集哈希去重 + Tiled/Godot 布局。

### 3.4 验收口径（与 PLAN 对齐）

- **调色板纯净度**作用于全部美术交付资产（单帧、`sheet.png`/`sheet_1x.png`、材质、47-Tile、巨构、
  showcase）。Godot 3D 真值通道（`sheet_shaded/part_id/bone_id/motion`）与 API 原始返回属于
  过程文件，已在 `output/MANIFEST.md` 中单独列出，不计入美术资产。
- **角色稳定性**：PLAN 指标限定在待机/格挡序列。8 帧 AI 面板全部保留（唯一帧哈希均为 8），
  静止掩膜在 sprite 空间计算（idle 701 次、defend 613 次 opaque 检查，差分均为 0）；特征审计覆盖
  **全部**被追踪特征（idle 350 次、defend 339 次检查），以图像实际位置为搜索中心；idle 的靴缝
  切开后有 2 个 1px 高光缺失（视觉审查确认无可见孔洞），defend 为 0 丢失。
  报告另给出 3D 仿射直接投影的交叉核对（idle drift 42/322、defend 48/346，idle missing 1），
  这是 AI 逐帧重绘与 3D 骨骼投影的错位，如实保留。running / attack / jump / in_air 保留 AI 原画、不做模板回贴。
- **参考面板锁定**：3×3 母板生成后，Panel 0 由 `lock_reference_panel()` 逐像素回填，
  与输入母板最大差异为 0，并输出 `mask.png`（黑=锁定，白=重绘）。
- **地块无缝**：优先环面平移 + 十字掩膜 + Gemini inpaint；随后做相位选择；若两项 KS 仍不
  通过则退回确定性镜像混合。报告逐项标注 `method` 与 `phase`，并**对最终交付砖重新测量**。
- **巨构贴花覆盖率**：按贴花实际 alpha 是否落在内部十字接缝 ±2px 内严格统计（不是外接矩形）。

### 3.5 硬性验收

| 要求 | 实现 | 验证 |
|---|---|---|
| 无半透明、颜色 100% 属调色板 | `lock_palette()` 全局收口 | `tests/test_character.py`、环境/巨构测试 |
| 静止部位跨帧像素差 = 0 | 刚体静止锁（bone-ID + 位移） | 报告 `static_diff_after == 0` |
| 特征小连通块面积波动 ≤1px | 特征追踪/模板覆写 + 审计 | `feature_audit`：idle/defend 全特征 drift=0；idle missing ≤2（靴缝切开的 1px 高光）、defend missing=0 |
| 地块无缝 | 环面平移 + 十字重绘 + 相位选择 | full-sample **与** 3×3 KS 均 p>0.05 |
| 巨构去重 / 贴花覆盖 | 图着色 + 泊松盘 | `tests/test_mega.py` |

> 说明：PLAN 模块三提到接地阴影用 `(0,0,0,128)`，与硬性验收第 1 条“禁止 0<α<255”冲突。本实现按硬性验收优先，改用调色板暗档 + Bayer 抖动的不透明阴影；地面带的 AI 石阶/纹理保留，仅清理与 32px 网格不对齐的碎块。

---

## 4. 验收与产物

```bash
.venv/bin/python -m pytest tests -q      # 81 tests
.venv/bin/python scripts/verify_all.py   # 汇总报告（尺寸/纯净度/锁定/覆盖率）
.venv/bin/python -m agent.orchestrator --verify  # 审查：方向/clip/视觉/纯净度/测试
```

- 预览总览：`output/SHOWCASE.md`
- 资产清单：`output/MANIFEST.md`
- 角色稳定性：`output/character/knight/<action>/report.json`
- 环境无缝性：`output/environment/field/REPORT.md`
- 巨构指标：`output/mega/field/report.json`
- 综合场景：`output/showcase/field/scene.png`

## 5. 过程文件与交付隔离

`output/` **只保留调色板纯净的美术资产**（全部 PNG 全量扫描：半透明 0、调色板外 0）。
Godot 3D 真值通道、API 原始返回、mask、装配中间件统一移动到项目根目录的 `work/`：

- `work/character/knight/mannequin/<action>/`：`sheet_shaded/part_id/bone_id/motion`
- `work/character/knight/<action>/`：`board/remaster/panel_*/raw_*/mask`
- `work/environment/field/mega/`、`work/environment/field/stamp/`：AI 母图、九宫格中间件、API 返回
- `work/environment/ship/`、`work/mega/ship/`：飞船材质板、tile 原始象限、结构/元素 AI 原图

`scripts/cleanup_work.py` 负责这一步，`run_all.py` 会在测试前自动执行。

## 6. 资产与许可

- 角色动作库：[KayKit Adventurers](https://kaylousberg.itch.io/kaykit-adventurers)，**CC0**，可商用，已随工程放在 `character/godot_mannequin/assets/kaykit/`。
- 生成的像素资产位于 `output/`，调色板与像素度量定义见 `config/pipeline_config.py`。


---

## 7. 仓库与凭据

- 仓库只提交**源码 + `output/` 交付产物**。`.venv/`、`work/` 中间件（约 100 MB）、
  `archive_trajectory/` 的原始轨迹导出（约 340 MB，其中 `messages.raw.jsonl` 单文件 104 MB，
  超过 GitHub 100 MB 硬限制）由 `.gitignore` 排除，只保留在本机。
- `NEWAPI_KEY` 只从环境变量读取，源码中不含任何默认密钥；缺省时生成 / 审查脚本直接报错。
  模板见 `.env.example`。
- 需要重新取回轨迹归档时，用 `archive_trajectory/export_opencode_trajectory.py` 从本地
  `opencode.db` 重新导出，或另行冷存储。

## 8. 美术 Agent（判断与审查）

交付物包含一个可复跑的 agent 层，负责“看”和“判断”，而不是由人手工挑图：

- **`agent/motion_audit.py`**：从 Godot 读取剑尖、双手、盾牌、髋部的 3D 轨迹，按
  前向/垂直/横向位移给候选 clip 分类打分。本次选 `1H_Melee_Attack_Chop`
  （Z 31.1 / Y 32.1 / X 9.0），拒绝 `Slice_Diagonal`（X 36.2 横向为主），并验证
  剑手在相机近侧的比例为 1.0。
- **`agent/visual_review.py`**：把六套动作表、完整地形、综合场景发给本机 NewAPI 的
  Gemma/Gemini 视觉模型，按严格 JSON rubric 审核朝向、attack 语义、defend 语义、
  粉色背景块、孤立碎片、接缝、水波方向与落地。
- **`agent/orchestrator.py`**：串起 motion audit → visual review → 调色板纯净度 →
  `pytest`，写 `output/AGENT_RUN.md`。

本次 agent 结论：角色六动作 **PASS**、环境 **PASS**、纯净度 **PASS**、测试 **PASS**；
综合场景 **FAIL**（巨构 9-slice 门洞/墙缝在像素级拼接下仍有重复与错位，已知弱项，
报告如实保留，不伪装成通过）。
