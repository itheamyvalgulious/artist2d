# Pixel Art Agent — 商业级 2D 像素游戏美术资产生成管线

Godot 4 参数化木偶 / 动作库真值渲染 → Gemini 图像模型整表重绘 → 确定性像素后处理 →
可直接进引擎的资产。详细算法见 [`PLAN.md`](PLAN.md)。

> **本仓库不使用代码单元测试。** 验收方式是独立多模态 subagent 的 100% 资产覆盖审查，
> 见第 5 节。`pytest` 与 `tests/` 已移除。

---

## 0. 当前批次（预览 / pilot）

### 0.1 新角色 `agent`

银白长发、紫瞳的美少女特工；深海军蓝 / 枪灰 / 银 / 青 / 紫配色，
短袖上衣 + 深色套袖 + 短裤 + 黑色战术靴；武士刀斜背在背后，手枪挂在右腰。

本轮只生成 **4 个确认动作**（外加作为衔接锚点的 `run`）：

| 动作 | 说明 | 衔接 |
|---|---|---|
| `idle` | 放松呼吸待机，双手空置，刀在背、枪在腰 | 自循环 |
| `run` | 侧视跑步循环，作为 `slash2` / `shoot2` 的锚点 | 自循环 |
| `slash2` | 跑动中挥刀；完整刀身，向前下方扫 | 首帧 = `run:0`，末帧 = `run:7` |
| `shoot2` | 跑动中开枪；手枪在伸出的右手中，水平指向画面右 | 首帧 = `run:0`，末帧 = `run:7` |
| `roll` | 前滚翻躲避；3D 骨架绕身体中心俯仰 360° | 首帧 = `idle:0`，末帧 = `idle:7` |

- 立绘交付为**完整设定图**：`design_sheet.png` 左侧是全身立绘，右侧是
  **武士刀 / 空刀鞘 / 手枪**的独立零件图；`parts/` 下还有按连通块切出的三张单件图。
- 每个动作 8 帧，同时交付 64×64 真像素游戏帧与 512×512 高分辨率对照帧。
- `run` 是 `slash2` / `shoot2` 的过渡依赖，因此本轮虽然是 4 个动作的预览，也会生成 `run`。
- 其余动作（`jump`、`in_air`、`shoot1/3`、`slash1/3`、`block`）已在
  `character/presets.py` 定义，等风格确认后继续。

完整预览：

- 角色总览：`output/character/agent/design_sheet.png`
- 各动作：`output/character/agent/<action>/sheet.png`（8×）、`sheet_hi.png`（512px/帧）
- 播放：`output/character/agent/<action>/preview_hi.png` / `.gif`
- 构建报告：`output/character/agent/build_report.json`

### 0.2 新环境 `ship`（侧视飞船内景）

科幻 + 赛博朋克飞船内景；深枪灰 / 海军蓝金属、青色全息灯带、紫色面板、暖色警示条。

- **Tile**：25 张 32px 图块（22 原 + 3 平台台阶），含地板 / 平台边缘、墙面、天花板、格栅、管道、通风口、
  警示条、星空窗；四种主材质通过双 KS 无缝检验。
- **中型结构（预览 3 / 10）**：`console_bank`、`cargo_stack`、`server_rack`。
- **Mega 基本元素（预览 3 / 20）**：`hull_frame`、`viewport`、`reactor_core`。
- **整船内景**：整艘飞船本身作为一个 mega 装配，见
  `output/mega/ship/ship_mega_preview.png`。
- **综合场景**：`output/showcase/ship/scene.png`（含 `agent` 角色）。

预览文件：

- `output/environment/ship/tileset_preview_x8.png`
- `output/environment/ship/tileset_sample_x4.png`
- `output/environment/ship/props/catalog_preview.png`
- `output/mega/ship/elements/catalog_preview.png`
- `output/mega/ship/ship_mega_preview.png`
- `output/showcase/ship/scene.png`

剩余 7 种中型结构与 17 种 mega 元素已在 `config/ship_config.py` 定义；
确认风格后扩展 `PILOT_MEDIUM` / `PILOT_MEGA` 或传 `--medium/--mega` 即可。

### 0.3 审查状态（预览批次）

- **飞船环境：PASS**（`output/reviews/ship_review_v5.md`）。
  v1→v5 依次修复了 tile 不可平铺、管道断头、grate 噪声、cargo 缺少阴影/卡扣/警示带、
  reactor 未裁切、hull 双层法兰等问题；v5 判定 **无 BLOCKER / 无 MAJOR**，仅剩
  polish（1px 平台边缘、角色悬停 1–2px、两对 deck 变体重复等）。
- **角色：FAIL**（`output/reviews/character_review_v4.md`）。
  v1→v4 已修复 shoot2 双枪/空腰套、idle 头跳、idle 循环 pop、512→64 的派生关系、
  过渡锚点（6 对逐字节一致），并把 idle 的紫瞳修好。仍剩 **6 个 BLOCKER**：
  1. idle/run/shoot2 背后刀鞘仍是两根带 chape 的杆（重复武器）；run/shoot2 还多一个
     肩上刀柄；
  2. `slash2` f1 只有裸刀柄、f6 有两把刀，刀尖钝/贴边；
  3. 紫瞳只在 idle 正确，run/slash2/shoot2 是白巩膜+1px 紫边，roll 几乎无紫；
  4. 挥刀长度/厚度仍不一致（约 161×13 到 308×40）；
  5. run 仍是 4 帧循环重复，far leg 不领跑；
  6. roll 的背刀画在头发前/脸旁，64px 下 f2–f4 糊成一团。
  另有 512 与 64 仍是“两张不同的画”、shoot2 f1 手枪不可读等 MAJOR。
- 最终验收员 `acceptance-v1`（`dawnfm/deepseek-v4.1-flash-1017`，max）的结论同样是
  **FAIL**，报告：`output/reviews/acceptance_v1.md`。它额外指出 ship 场景的
  window 贴花、server 无透明轮廓、reactor 底座裁切、角色悬停/黑色矩形阴影、
  重复克隆等问题；这些 ship 侧问题已在最新 `output/showcase/ship/scene.png` 中
  做了修复（单角色、抖动接触阴影、内容底边对齐、window 重绘、server 透明缺口、
  reactor 底座、rib 翻转变体），但尚未重新跑一轮验收。
- 下一轮必须改为**部件级合成**：单一 rigid 背刀 sprite（hilt+tsuba+一根 scabbard/chape）、
  参数化刀身（固定长度/厚度/tsuba/cyan edge）、五动作共用的眼睛 tile、
  真正的 2-step run（镜像 f4–f7）、roll 的 stow 层序与 64px 可读性重排。
  在确认优先级后再扩展 10 中型 / 20 mega / 全部角色动作。

### 0.4 隔离

```text
output/
  character/
    knight/                 原有骑士
    agent/                  新美少女特工
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

`environment/`、`mega/`、`showcase/` 的直接子级只允许是 set 目录；
`config/namespaces.py` 是路径命名空间的唯一来源，所有构建脚本都通过它取路径，
两套世界的同名文件不会互相覆盖。

---

## 1. 快速开始

```bash
# 依赖（uv 管理 .venv）
uv sync

# 凭据（只从环境变量读取；仓库不含 key）
export NEWAPI_KEY=...
export GODOT_DISPLAY=:10       # 有桌面/虚拟 X 时
export DISPLAY=:10

# 新角色（本轮：idle / slash2 / shoot2 / roll，自动补 run 锚点）
.venv/bin/python scripts/build_character.py \
    --character agent --actions idle,slash2,shoot2,roll

# 飞船环境（tile + 3 中型 + 3 mega + 整船装配 + showcase）
.venv/bin/python scripts/build_ship.py

# 重新装配整船 / 综合场景（不重跑 AI 生成）
.venv/bin/python -m environment.ship_assembly

# 生成供独立审查用的 100% 覆盖包
.venv/bin/python scripts/build_review_packets.py

# 原有 field / knight 全流程
.venv/bin/python scripts/run_all.py
```

API Key / 模型可用环境变量覆盖：`NEWAPI_BASE`、`NEWAPI_KEY`、
`PIXEL_MODEL_SUNBURST`、`PIXEL_MODEL_FLARE`、`GODOT_DISPLAY`。
可参照 `.env.example` 用 `set -a; . ./.env; set +a` 载入（管线本身不解析 `.env`）。

---

## 2. 工程结构

```text
config/pipeline_config.py        全局尺寸、64 色主调色板、API/路径配置
config/namespaces.py             character/environment/mega/showcase 的 set 命名空间
config/ship_config.py            飞船 25 tile / 10 中型 / 20 mega 目录与风格提示词
core/api_client.py               Gemini generate / edit / masked-inpaint（缓存、重试、并发）
core/palette_quantizer.py        CIE-LAB 最近邻锁色、Bayer 抖动、硬 Alpha
core/grid_resampler.py           核内众数网格重采样
character/godot_mannequin/       Godot 工程：参数化木偶 + KayKit 动作重定向 + 批渲染
character/sheet_compositor.py    参考图、3×3 复合整表、API 重绘、鲁棒切帧
character/temporal_tracker.py    静止像素硬锁、特征块追踪/覆写、稳定性审计
character/presets.py             knight / agent 的身份、动作、武器状态与衔接契约
environment/material_genesis.py  2×2 多材质同步生成
environment/seamless_toroidal.py 环面平移 + 十字掩膜重绘 + KS 无缝检验
environment/autotile_47.py       高度场调制 47-Tile 自动合成
environment/stamp_medium.py      中型巨构：接地生成、差异抠图、Y-Sort 分层
environment/mega_macro.py        超大型巨构：九宫格、跨格贴花、宏观 AO、图集去重
environment/ship_tiles.py        飞船 2×2 材质板 → 25 张侧视 tile 图集
environment/ship_objects.py      中型结构 / mega 元素的生成、拟合、抠图与元数据
environment/ship_assembly.py     整船内景装配 + showcase
scripts/build_character.py       角色端到端编排
scripts/build_ship.py            飞船预览批次编排
scripts/build_review_packets.py  独立审查用 100% 覆盖包
agent/                           3D 轨迹审计、旧版 NewAPI 视觉审查、报告编排
work/review/                     审查用联系表（不是交付资产）
output/reviews/                  独立多模态审查报告
output/                          全部生成资产 + 报告
```

---

## 3. 角色管线

### 3.1 Godot 木偶与真值

- 程序化 `Skeleton3D`；骨长/肩宽/躯干长度由 JSON 参数重建 rest 变换（无剪切）；
  `head_scale` 通过 `set_bone_pose_scale()` 作用于叶骨骼，并输出
  `SkeletonProfileHumanoid` + `BoneMap` 完成标准人形绑定。
- KayKit Adventurers（CC0）的动作按世界旋转增量重定向到参数化骨架。
- `agent` 使用独立几何：银发块、面部/紫瞳、短袖、套袖、短裤、靴子、背后刀鞘、
  腰间枪套、手持刀/枪挂点。
- 相机固定在 `(-70, 37, 0)`（纯 90° 侧视，从角色右侧看，角色面向画面右）。
- 每帧同时输出：`sheet_shaded.png`（512px/帧）、`sheet_part_id.png`（64px/帧）、
  `sheet_bone_id.png`、`sheet_motion.json`（骨骼投影真值）。

### 3.2 复合整表重绘

- 3×3 母板：左上角是全身参考，其余 8 格是木偶姿势。
- 本轮把**武器零件参考图**也作为输入图传给每一次动作重绘，避免模型把长刀画成短匕首、
  或把手枪画成黑袖套。
- 重绘使用“每个木偶剪影膨胀 32px”的白色掩码，尽量把模型限制在各自格子内；
  生成后仍会在格子四周的洋红沟槽里寻找真实前景包围盒，做**鲁棒切帧**，
  防止抬手/刀尖出格后被 512 格线切断。
- 切帧后再做连通块清洗：只保留主体和贴近主体的部件，丢掉相邻格子漏进来的
  靴子/头发碎片。

### 3.3 时序与衔接

- 逐像素计算位移；位移 <0.25px 且骨骼/部件 ID 相同的像素从上帧硬覆盖。
- 小高对比特征（眼睛、铆钉、饰边）在 3×3 邻域内追踪并按需回贴。
- 衔接锚点按 `character/presets.py` 的 `TRANSITIONS` 强制执行，并记录 SHA-256：

  ```text
  run       自循环
  slash2    run:0  -> ... -> run:7
  shoot2    run:0  -> ... -> run:7
  roll      idle:0 -> ... -> idle:7
  ```

  本轮 `transitions.json` 中所有锚点均逐字节一致。

### 3.4 前滚翻

KayKit 没有前滚翻 clip。`render_actor.gd` 的做法是：

1. 取 `Dodge_Forward` 的中段蹲姿作为团身姿势；
2. 首末帧使用 `Idle` 姿势（以便和 idle 锚点一致）；
3. 对整副 `Skeleton3D` 绕身体中心（髋部高度）做 360° 俯仰，
   每帧写入 `sheet_motion` 真值；
4. 图像模型按这 8 个真实旋转姿势重绘，而不是凭空画一个球。

### 3.5 稳定帧 bug 修复

本轮修复了一个会静默复制最后一帧的索引 bug：
`frames/frame_*.png` 的读取循环必须用 `i` 作为帧号，不能用外层遗留的 `f`。
修复后 5 个动作的 64px 帧均为 8 张不同图像，且 `run:0/run:7`、
`idle:0/idle:7` 锚点在 `slash2` / `shoot2` / `roll` 中逐字节一致。

---

## 4. 飞船环境管线

- **材质**：2×2 Perlin 约束板一次生成 deck / wall / grate / conduit 四种同世界观材质，
  再用环面平移 + 十字掩膜 + 中值/重绘做成 32×32 无缝砖，双 KS 验收。
- **Tile**：由材质派生 25 张侧视 tile（平台边缘、墙面变体、天花板、格栅、管道、
  通风口、警示条、星空窗），统一调色板锁与硬 Alpha。
- **中型结构**：接地画布 + AI 生成 + 差异抠图 + Y-Sort 元数据。
- **Mega 元素**：模块化侧视元素，输出尺寸/锚点元数据，可重复拼装。
- **整船装配**：48×20 格（1536×640）的飞船大厅，把 hull frame、viewport、reactor、
  console、cargo、server 与 tile 拼成一个完整场景；整艘船本身就是一个 mega。
- **Showcase**：把 `agent` 的 idle / shoot2 帧按 Y-Sort 贴进场景，角色落地并有接触阴影。

---

## 5. 验收：独立多模态审查（没有代码单元测试）

本项目**故意不写代码单元测试**。指标会诱导模型刷分，而不是真正看画面。验收流程是：

1. `scripts/build_review_packets.py` 把**每一个最终交付资产**排成联系表：
   - 角色：5 个动作 × 8 帧 ×（512px + 64px + 3D 真值）全部展开；
     另加跨动作一致性、6 组衔接锚点、run 循环回绕；
   - 环境：25 张 tile 全图、3 中型、3 mega、整船装配、showcase；
2. 派生一个**独立的** `dawnfm/deepseek-v4.1-flash-1017`（effort high）subagent，
   用 `read` 工具逐张看图，不允许抽样；报告写到 `output/reviews/`；
3. 发现问题 → 修 → 从 3D 木偶真值到最终帧做**全链路**多模态复查；
4. 只有 100% 覆盖审查通过，才把这一批称为完成。

审查报告（每一轮都保留，不覆盖旧报告）：

- `output/reviews/character_review_v1.md` → `v2` → `v3`
- `output/reviews/ship_review_v1.md` → `v2` → `v3` → `v4`

每轮报告都包含 100% 文件清单、逐项 PASS/FAIL、BLOCKER/MAJOR/MINOR 与具体修复建议。
审查联系表在 `work/review/`（不是交付资产，可随时重建）。

---

## 6. 资产与许可

- 角色动作库：[KayKit Adventurers](https://kaylousberg.itch.io/kaykit-adventurers)，
  **CC0**，可商用，已随工程放在 `character/godot_mannequin/assets/kaykit/`。
- 生成的像素资产位于 `output/`；调色板与像素度量见 `config/pipeline_config.py`。

## 7. 仓库与凭据

- 仓库只提交源码 + `output/` 交付产物。`.venv/`、`work/`、`archive_trajectory/` 的原始轨迹
  由 `.gitignore` 排除。
- `NEWAPI_KEY` 只从环境变量读取，源码中不含默认密钥；缺省时生成/审查脚本直接报错。
  模板见 `.env.example`。
