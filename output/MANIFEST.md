# Asset Manifest / 资产清单

所有交付资产按 **set 命名空间** 隔离，避免两套世界互相覆盖：

```text
output/character/knight
output/environment/{field,ship}
output/mega/{field,ship}
output/showcase/{field,ship}
```

`environment/`、`mega/`、`showcase/` 的直接子级只允许是 set 目录，`tests/test_isolation.py` 强制检查。

---

## 1. 新环境 `ship`（预览批次）

### 2.1 Tile / 材质

| 路径 | 规格 | 说明 |
|---|---|---|
| `environment/ship/tiles/{deck,wall,grate,conduit}_seamless.png` | 32×32 | 四张 AI 材质，双 KS 无缝 |
| `environment/ship/tiles/*.png` | 32×32 | 22 张完整侧视 tile（平台边缘/墙面/天花板/格栅/管道/警示/星空窗） |
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
- `work/environment/field/`：field 材质与 mega 中间件。
- `work/environment/ship/`：飞船材质板、tile 原始象限、结构 AI 原图。
- `work/mega/ship/`：mega 元素 AI 原图。
- `work/api_cache/`：API 结果缓存。

---

## 5. Purity check

`tests/test_integration.py` + `tests/test_ship.py` 对全部 shipped assets 逐像素检查：

- `0 < α < 255` 的半透明像素：**0**
- 不属于 64 色主调色板的像素：**0**
- 高精度 512 动画同样通过调色板锁与硬 Alpha。

当前测试：**122 passed**。
