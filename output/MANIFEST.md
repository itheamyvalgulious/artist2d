# Asset Manifest / 资产清单

所有交付资产按 **set / character 命名空间** 隔离，避免两套世界互相覆盖：

```text
output/character/{knight,agent}
output/environment/{field,ship}
output/mega/{field,ship}
output/showcase/{field,ship}
```

`environment/`、`mega/`、`showcase/` 的直接子级只允许是 set 目录；
`config/namespaces.py` 是路径命名空间的唯一来源，所有构建脚本都通过它取路径。

---

## 1. 角色 `agent`（预览批次）

银白长发、紫瞳的美少女特工；深海军蓝 / 枪灰 / 银 / 青 / 紫配色，
短袖上衣 + 套袖 + 短裤 + 黑色战术靴；武士刀斜背，手枪挂在右腰。

| 路径 | 规格 | 说明 |
|---|---|---|
| `character/agent/design_sheet.png` | 1024×512 | 全身立绘 + 武士刀 / 空刀鞘 / 手枪独立零件图 |
| `character/agent/design_sheet_x2.png` | 2048×1024 | 2× 预览 |
| `character/agent/parts/{katana,scabbard,pistol}.png` | 单件 | 从武器参考图切出的独立零件 |
| `character/agent/char_ref_512.png` | 512×512 | 全身参考（透明底、调色板锁） |
| `character/agent/char_ref_64.png` | 64×64 | 真像素母版 |
| `character/agent/char_ref_64_x16.png` | 1024×1024 | 母版 16× 预览 |
| `character/agent/char_ref_weapons_512.png` | 512×512 | 武器零件参考原图（透明底） |
| `character/agent/<action>/frames/frame_00..07.png` | 64×64 | **游戏用真像素帧** |
| `character/agent/<action>/frames_hi/frame_00..07.png` | 512×512 | 高分辨率对照帧 |
| `character/agent/<action>/sheet.png` | 4096×512 | 8 帧 8× 静态表 |
| `character/agent/<action>/sheet_hi.png` | 4096×512 | 8 帧 512px 静态表 |
| `character/agent/<action>/preview.png` / `.gif` | 256×256×8 | 64px 帧 4× 播放预览 |
| `character/agent/<action>/preview_hi.png` / `.gif` | 512×512×8 | 高分辨率播放预览 |
| `character/agent/<action>/report.json` | — | 帧数、稳定锁、特征审计、衔接锚点 |
| `character/agent/transitions.json` | — | 所有锚点的 SHA-256 |
| `character/agent/build_report.json` | — | 本轮动作、设计图、衔接总报告 |

本轮动作：`idle`、`run`（锚点）、`slash2`、`shoot2`、`roll`，每个 8 帧。
衔接：

```text
run       自循环
slash2    run:0  -> ... -> run:7
shoot2    run:0  -> ... -> run:7
roll      idle:0 -> ... -> idle:7
```

`roll` 使用程序化团身姿势（首末帧为 Idle）+ 3D 骨架 360° 俯仰真值；
`transitions.json` 中所有锚点与源帧逐字节一致。

---

## 2. 环境 `ship`（预览批次）

### 2.1 Tile / 材质

| 路径 | 规格 | 说明 |
|---|---|---|
| `environment/ship/tiles/{deck,wall,grate,conduit}_seamless.png` | 32×32 | 四张 AI 材质，双 KS 无缝 |
| `environment/ship/tiles/*.png` | 32×32 | 25 张完整侧视 tile（22 原 + 3 平台台阶；平台边缘/墙面/天花板/格栅/管道/警示/星空窗） |
| `environment/ship/tileset.png` | 256×96 | 图集 |
| `environment/ship/tileset.json` | — | 名称 → 索引 |
| `environment/ship/tileset_preview_x8.png` | 2048×768 | 图块总览 |
| `environment/ship/tileset_sample_x4.png` | 1792×1024 | 图块拼合样例 |
| `environment/ship/materials.json` | — | 材质 KS / 相位 / 纯净度 |
| `environment/ship/REPORT.md` | — | 飞船环境报告 |

### 2.2 中型结构（3 / 10）

| id | 尺寸 | 路径 |
|---|---|---|
| `console_bank` | 128×64 | `environment/ship/props/console_bank/sprite.png` |
| `cargo_stack` | 64×96 | `environment/ship/props/cargo_stack/sprite.png` |
| `server_rack` | 64×112 | `environment/ship/props/server_rack/sprite.png` |

总览：`environment/ship/props/catalog_preview.png`。
其余 7 种已在 `config/ship_config.py` 定义，待风格确认后生成。

### 2.3 Mega 元素（3 / 20）

| id | 尺寸 | 路径 |
|---|---|---|
| `hull_frame` | 128×256 | `mega/ship/elements/hull_frame/sprite.png` |
| `viewport` | 128×96 | `mega/ship/elements/viewport/sprite.png` |
| `reactor_core` | 128×192 | `mega/ship/elements/reactor_core/sprite.png` |

总览：`mega/ship/elements/catalog_preview.png`。
其余 17 种已在 `config/ship_config.py` 定义，待风格确认后生成。

### 2.4 整船装配 + 综合场景

| 路径 | 规格 | 说明 |
|---|---|---|
| `mega/ship/ship_mega_1x.png` | 1536×640 | 整船内景（不含角色） |
| `mega/ship/ship_mega_preview.png` | 3072×1280 | 整船 2× 预览 |
| `mega/ship/ship_layout.json` | — | 模块 / 家具 / 角色布局 |
| `mega/ship/report.json` | — | 元素与装配指标 |
| `showcase/ship/scene_1x.png` | 1536×640 | 飞船内景综合场景 |
| `showcase/ship/scene.png` | 3072×1280 | 综合场景 2× 预览 |
| `showcase/ship/report.json` | — | showcase 指标 |

---

## 3. 原有 `field` / `knight`（保持兼容）

| 路径 | 说明 |
|---|---|
| `environment/field/{grass,dirt,stone,water}_seamless.png` | 原有俯视地形材质 |
| `environment/field/autotile_*.png` | 47-Tile 图集 |
| `environment/field/stamp/` | 原有中型巨构（shrine） |
| `mega/field/mega_atlas.png` 等 | 原有城堡 mega |
| `showcase/field/scene.png` | 原有地形综合场景 |
| `character/knight/` | 原有骑士 6 动作 |

详细说明见根目录 `README.md` 与 `environment/field/REPORT.md`。

---

## 4. 过程文件 / 真值通道

以下内容不属于调色板纯净的美术资产，位于 `work/`：

- `work/character/<name>/mannequin/<action>/`：Godot 3D 真值（shaded / part_id / bone_id / motion）。
- `work/character/<name>/<action>/`：board / remaster / mask / panel / raw / warps。
- `work/character/<name>/char_ref_raw.png` / `char_ref_canvas.png`：API 原始参考与带洋红底的 512 画布。
- `work/character/<name>/weapon_ref_raw.png` / `weapon_ref_canvas.png`：武器参考原图。
- `work/environment/field/`：field 材质与 mega 中间件。
- `work/environment/ship/`：飞船材质板、tile 原始象限、结构 AI 原图。
- `work/mega/ship/`：mega 元素 AI 原图。
- `work/review/`：独立多模态审查用的 100% 覆盖联系表。
- `work/api_cache/`：API 结果缓存。

---

## 5. Purity check（确定性扫描，不是单元测试）

对 `output/` 下全部交付 PNG（排除 `work/` 过程文件与 3D 真值）做：

- `0 < α < 255` 的半透明像素：**0**
- 不属于 64 色主调色板的 opaque 像素：**0**

高精度 512 动画、64px 游戏帧、tile、结构、整船装配与 showcase 均通过调色板锁与硬 Alpha。

---

## 6. 多模态验收

本项目**没有代码单元测试**。验收由独立的
`dawnfm/deepseek-v4.1-flash-1017`（effort high）subagent 完成：

- 角色：每个动作全部 8 帧 ×（512px、64px、3D 真值）+ 跨动作一致性 + 衔接锚点 + run 循环；
- 环境：25 张 tile 全图、3 中型、3 mega、整船装配、showcase；
- 报告（每轮保留）：`output/reviews/character_review_v1..v4.md`、
  `output/reviews/ship_review_v1..v5.md`。
- 判定记录：
  - `ship v5` 的 PASS 已被 `acceptance_v3_ship.md` 推翻：v3 独立审核为 **FAIL**
    （2 blockers / 10 majors：缺门、地板/天花板接缝、管道/格栅接缝、天花灯、
    窗、server、hull 非整数缩放、接触阴影、右舱拥挤、tile 重复、旧布局数据、
    墙面拼贴）。
  - `character v4` = FAIL；`acceptance_v1` 总体也是 **FAIL**。
  - 本轮已按 v3 报告修复：新增 `door`、全部可平铺 tile 做边缘自洽、天花灯/窗
    重绘、去墙面噪点、空枪套常驻、眼睛不再被抠掉、roll 共享缩放与 360° 落地、
    审核包改为 1:1/8×、布局与 showcase 报告改为单角色。
  - 当前产物正在接受 `acceptance-v4`（DeepSeek max）复验，报告写入
    `output/reviews/acceptance_v4_character.md` / `acceptance_v4_ship.md`；
    在报告出来前不把任何未复验项写成通过。
