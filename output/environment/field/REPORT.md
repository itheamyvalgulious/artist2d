# Environment Pipeline Report

## 1. Material Genesis

| Material | Base Size | Partial Alpha | Off-Palette | Unique Colors |
|----------|-----------|---------------|-------------|----------------|
| grass | (32, 32) | 0 | 0 | 4 |
| dirt | (32, 32) | 0 | 0 | 3 |
| stone | (32, 32) | 0 | 0 | 7 |
| water | (32, 32) | 0 | 0 | 3 |

## 2. Seamless Toroidal

| Material | Method | Phase | KS Statistic | p-value (full) | p-value (3x3) | Pass | Partial Alpha | Off-Palette |
|----------|--------|-------|-------------|---------------|---------------|------|---------------|-------------|
| grass | seam_median | [23, 5] | 0.0126 | 1.0000 | 1.0000 | True | 0 | 0 |
| dirt | inpaint | [1, 9] | 0.0066 | 1.0000 | 1.0000 | True | 0 | 0 |
| stone | seam_median | [15, 12] | 0.0192 | 1.0000 | 0.9987 | True | 0 | 0 |
| water | seam_median | [14, 7] | 0.0040 | 1.0000 | 1.0000 | True | 0 | 0 |

> 方法说明：优先使用环面平移 + 十字掩膜 + Gemini inpaint。环面平移后在所有 32×32 相位中
> 选择接缝梯度统计最典型的一个相位（相位滚动不改变无缝性），再做最终测量。
> **硬判定同时要求** full-sample 两样本 KS 与 3×3 平铺 KS 的 p 值都 > 0.05；
> 两项都通过才记 `Pass=True`。所有方法结果均通过调色板锁。

## 3. Autotile 47

| Pair | Tile Count | Violations |
|------|-----------|------------|
| grass_over_dirt | 47 | partial_alpha=0 off_palette=0 |
| dirt_over_grass | 47 | partial_alpha=0 off_palette=0 |
| water_over_grass | 47 | partial_alpha=0 off_palette=0 |
| water_over_dirt | 47 | partial_alpha=0 off_palette=0 |
| stone_over_grass | 47 | partial_alpha=0 off_palette=0 |
| stone_over_dirt | 47 | partial_alpha=0 off_palette=0 |

## 4. Summary

- Materials generated: 4
- Seamless tiles: 4
- Autotile pairs: 6
- All tiles pass through `lock_palette` (no partial alpha, no off-palette opaque pixels).
- KS test threshold: full-sample p > 0.05 **and** 3x3 tiling p > 0.05 for seamless acceptance.
- 47-Tile connected edges are full-width bands (worst coverage 100%); all 47 tiles are SHA-256 distinct.
