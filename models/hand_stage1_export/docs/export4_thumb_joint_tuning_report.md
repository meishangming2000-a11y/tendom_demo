# Export4 Thumb Joint Tuning

Generated: 2026-05-25 01:38:55

## Scope

This pass tunes thumb target ranges on top of the long-finger-tuned export4 hand. Long fingers are held in the natural close pose. No CAD, STL, joint names, axes, or joint tree are changed.

## Outputs

- Thumb tuned hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_thumb_tuned.xml`
- No-ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_export4_thumb_tuned.xml`
- Ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_thumb_tuned.xml`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export4_thumb_joint_tuning.json`
- `front_sheet`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb_tuning\thumb_candidates_front_sheet.png`
- `side_sheet`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb_tuning\thumb_candidates_side_sheet.png`
- `top_sheet`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb_tuning\thumb_candidates_top_sheet.png`
- `preshape_top_colored_sheet`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb_tuning\focus_pass_colored\preshape_top_colored_sheet.png`
- `fullclose_top_colored_sheet`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb_tuning\focus_pass_colored\fullclose_top_colored_sheet.png`
- `fullclose_visual_recommended_top`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb_tuning\focus_pass_colored\fullclose_visual_recommended_top.png`

## Tuned Thumb Limits

| joint | range |
|---|---:|
| `thumb_cmc_abd_joint` | `-1.05 1.05` |
| `thumb_cmc_joint` | `-0.95 0.95` |
| `thumb_mcp_joint` | `-0.1 1.2` |
| `thumb_ip_joint` | `-0.85 0.05` |

## Score-Best Thumb Target

| joint | target |
|---|---:|
| `thumb_cmc_abd_joint` | `-0.3000` |
| `thumb_cmc_joint` | `0.2500` |
| `thumb_mcp_joint` | `0.0000` |
| `thumb_ip_joint` | `0.0000` |

Metrics for best target:

- thumb-index distance: `0.0204 m`
- thumb-middle distance: `0.0266 m`
- thumb-palm distance: `0.1021 m`
- palmar advancement Y: `0.0220 m`

## Visual Recommended Thumb Target

The visual recommendation is preferred for scripted grasp because it adds mild thumb MCP/IP flexion and looks more like opposition in the color-coded focus renders. It is not the pure minimum-distance candidate.

| joint | target |
|---|---:|
| `thumb_cmc_abd_joint` | `-0.3000` |
| `thumb_cmc_joint` | `0.0000` |
| `thumb_mcp_joint` | `0.2500` |
| `thumb_ip_joint` | `-0.2500` |

Metrics for visual recommended target in full-close context:

- thumb-index distance: `0.0196 m`
- thumb-middle distance: `0.0333 m`
- thumb-palm distance: `0.0980 m`
- palmar advancement Y: `0.0232 m`

## Candidate Table

| rank | score | cmc_abd | cmc | mcp | ip | thumb-index | thumb-middle | note |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 0.0607 | -0.30 | 0.25 | 0.00 | 0.00 | 0.0204 | 0.0266 | score best |
| 2 | 0.0643 | -0.30 | 0.00 | 0.25 | -0.25 | 0.0196 | 0.0333 | visual recommended |
| 3 | 0.0671 | -0.30 | 0.25 | 0.00 | -0.25 | 0.0272 | 0.0280 |  |
| 4 | 0.0692 | -0.30 | 0.00 | 0.50 | 0.00 | 0.0261 | 0.0331 |  |
| 5 | 0.0694 | -0.30 | 0.00 | 0.00 | -0.75 | 0.0220 | 0.0377 |  |
| 6 | 0.0708 | -0.30 | 0.00 | 0.25 | -0.50 | 0.0262 | 0.0353 |  |
| 7 | 0.0713 | -0.30 | -0.20 | 0.50 | 0.00 | 0.0192 | 0.0422 |  |
| 8 | 0.0719 | -0.30 | -0.20 | 0.50 | -0.25 | 0.0220 | 0.0409 |  |
| 9 | 0.0754 | -0.30 | -0.20 | 0.25 | -0.50 | 0.0216 | 0.0449 |  |
| 10 | 0.0755 | -0.30 | 0.25 | 0.25 | 0.00 | 0.0349 | 0.0310 |  |

## Visual Notes

- Candidate sheets include front, side, and top fixed-camera views.
- Color-coded focus sheets use orange thumb links, red thumb tip, green index tip, and cyan middle tip.
- The scoring function rewards thumb-index/thumb-middle proximity and palmar movement, while penalizing extremely tiny distances that likely indicate visual overlap.
- Visual inspection selected the mild MCP/IP flexion target because it shows the thumb crossing toward the index/middle side without the fully extended thumb look.
- This remains a target tuning pass; final thumb CMC axis semantics still need SolidWorks confirmation if the motion looks mechanically implausible in viewer.
