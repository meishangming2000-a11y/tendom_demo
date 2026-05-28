# Export4 Long Finger Joint Tuning

Generated: 2026-05-25 01:17:13

## Scope

This is an experimental simulation-side tuning pass for index/middle/ring/little only. The thumb is held neutral except for existing model geometry, and no CAD/STL/joint-tree edits are made.

## Outputs

- Tuned hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_long_finger_tuned.xml`
- No-ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_export4_long_finger_tuned.xml`
- Ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_long_finger_tuned.xml`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export4_long_finger_joint_tuning.json`
- Visual sheets:
  - `full_hand`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\full_hand_tuning_sheet.png`
  - `full_hand_side`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\full_hand_tuning_side_sheet.png`
  - `full_hand_top`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\full_hand_tuning_top_sheet.png`
  - `index`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\index_joint_tuning_sheet.png`
  - `middle`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\middle_joint_tuning_sheet.png`
  - `ring`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\ring_joint_tuning_sheet.png`
  - `little`: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_long_finger_tuning\little_joint_tuning_sheet.png`

## Tuned Limits

| joint | range |
|---|---:|
| `index_mcp_flex_joint` | `-0.3 0.18` |
| `middle_mcp_flex_joint` | `-0.3 0.18` |
| `ring_mcp_flex_joint` | `-0.3 0.18` |
| `little_mcp_flex_joint` | `-0.28 0.16` |
| `index_mcp_abd_joint` | `-0.78 0.08` |
| `middle_mcp_abd_joint` | `-0.86 0.08` |
| `ring_mcp_abd_joint` | `-0.84 0.08` |
| `little_mcp_abd_joint` | `-0.76 0.08` |
| `index_pip_joint` | `-1.1 0.04` |
| `middle_pip_joint` | `-1.16 0.04` |
| `ring_pip_joint` | `-1.1 0.04` |
| `little_pip_joint` | `-1 0.04` |
| `index_dip_joint` | `-0.66 0.04` |
| `middle_dip_joint` | `-0.7 0.04` |
| `ring_dip_joint` | `-0.68 0.04` |
| `little_dip_joint` | `-0.62 0.04` |

## Recommended Scripted Targets

| joint | natural close target |
|---|---:|
| `index_mcp_flex_joint` | `-0.0600` |
| `middle_mcp_flex_joint` | `-0.0600` |
| `ring_mcp_flex_joint` | `-0.0500` |
| `little_mcp_flex_joint` | `-0.0400` |
| `index_mcp_abd_joint` | `-0.5800` |
| `middle_mcp_abd_joint` | `-0.6400` |
| `ring_mcp_abd_joint` | `-0.6200` |
| `little_mcp_abd_joint` | `-0.5400` |
| `index_pip_joint` | `-0.8200` |
| `middle_pip_joint` | `-0.8800` |
| `ring_pip_joint` | `-0.8400` |
| `little_pip_joint` | `-0.7600` |
| `index_dip_joint` | `-0.4200` |
| `middle_dip_joint` | `-0.4600` |
| `ring_dip_joint` | `-0.4400` |
| `little_dip_joint` | `-0.4000` |

## Visual Notes

- `full_hand_tuning_sheet.png` compares open, hook, natural close, and stronger safe close.
- `full_hand_tuning_side_sheet.png` and `full_hand_tuning_top_sheet.png` were added to check for dorsal-side motion and obvious interpenetration.
- Each `*_joint_tuning_sheet.png` shows open, single-joint motion, and one-finger combined motion.
- Current visual pass: long fingers close toward the palm side in the tuned `natural_close` pose.
- Current visual pass: no obvious palm stabbing or severe self-intersection is visible in the fixed camera sheets.
- `full_but_safe` is tighter and should be treated as a range stress pose, not the default scripted target.
- Current pass intentionally leaves thumb tuning for later.
- If any finger still crosses through the palm in live viewer, reduce that finger's PIP/DIP target before increasing MCP flexion.
