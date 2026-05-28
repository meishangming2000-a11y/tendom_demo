# Export4 +Y / -Y Visual Demo

Generated: 2026-05-26T10:30:05

## Scope

Same export4 candidate scene, same scripted close target, only the ball Y side changes. This is for visual confirmation of palm/grasp side; no CAD/STL/joint names/current-baseline files were changed.

## Files To Open First

- Front hold comparison: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_y_side_demo\comparison_hold_front_plus_y_vs_minus_y.png`
- Top hold comparison: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_y_side_demo\comparison_hold_top_plus_y_vs_minus_y.png`
- +Y hold front: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_y_side_demo\plus_y\plus_y_hold_front.png`
- -Y hold front: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_y_side_demo\minus_y\minus_y_hold_front.png`

## Metrics

| side | stage | contacts | ball-hand contacts | max penetration | four-tip avg | thumb-ball |
|---|---|---:|---:|---:|---:|---:|
| plus_y | open | 0 | 0 | 0.000000 | 0.145999 | 0.048946 |
| plus_y | preshape | 0 | 0 | 0.000000 | 0.110701 | 0.049076 |
| plus_y | close_four_fingers | 0 | 0 | 0.000000 | 0.052713 | 0.049027 |
| plus_y | close_thumb | 2 | 2 | 0.001045 | 0.046504 | 0.041427 |
| plus_y | hold | 2 | 2 | 0.001043 | 0.046509 | 0.043271 |
| minus_y | open | 0 | 0 | 0.000000 | 0.084294 | 0.151132 |
| minus_y | preshape | 0 | 0 | 0.000000 | 0.108481 | 0.151200 |
| minus_y | close_four_fingers | 0 | 0 | 0.000000 | 0.133790 | 0.151450 |
| minus_y | close_thumb | 0 | 0 | 0.000000 | 0.135210 | 0.126728 |
| minus_y | hold | 0 | 0 | 0.000000 | 0.135198 | 0.122235 |

## Visual Interpretation

- `+Y` places the ball near the closing fingertips in the current candidate scene and generates ball-hand contact in hold.
- `-Y` places the ball on the far/opposite side for this same scripted close and remains visually far from the fingertips.
- Please use these images to confirm whether `+Y` is the intended palm/grasp side for export4 task scenes.
