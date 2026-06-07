# Stage3 Hand-Relative Perception Test V0

Generated: 2026-06-04T01:03:51

## Scope

This test integrates the MuJoCo egg pose sensor with the mechanical hand anchors. The perception path uses image-derived egg position plus hand qpos/FK. The ground-truth path uses MuJoCo egg position plus the same hand qpos/FK. Ground truth is used only for comparison.

## Inputs

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Perception camera: `stage3_egg_closeup`
- Resolution: `640 x 480`
- Hand poses: `['open_default', 'preshape_hand', 'close_preview_hand']`
- Egg pose samples per hand pose: `5`
- Max relative error threshold: `0.002000 m`

## Result

- Overall status: `PASS`
- Max egg position error: `0.00005795 m`
- Max object-in-palm-frame error: `0.00005795 m`
- Max fingertip vector error: `0.00005795 m`

## Per Hand Pose Summary

| hand pose | samples | max egg error m | max palm-frame error m | max fingertip-vector error m |
|---|---:|---:|---:|---:|
| open_default | 5 | 0.00005795 | 0.00005795 | 0.00005795 |
| preshape_hand | 5 | 0.00005795 | 0.00005795 | 0.00005795 |
| close_preview_hand | 5 | 0.00005795 | 0.00005795 | 0.00005795 |

## Per-Sample Results

| hand pose | egg sample | egg error m | palm-frame error m | max fingertip-vector error m | mask pixels | confidence |
|---|---|---:|---:|---:|---:|---:|
| open_default | center | 0.00005728 | 0.00005728 | 0.00005728 | 14809 | 0.983 |
| open_default | left_low | 0.00005656 | 0.00005656 | 0.00005656 | 12946 | 0.983 |
| open_default | right_high | 0.00005795 | 0.00005795 | 0.00005795 | 17084 | 0.983 |
| open_default | lifted_center | 0.00005383 | 0.00005383 | 0.00005383 | 15123 | 0.983 |
| open_default | lifted_diag | 0.00005780 | 0.00005780 | 0.00005780 | 15777 | 0.983 |
| preshape_hand | center | 0.00005728 | 0.00005728 | 0.00005728 | 14809 | 0.983 |
| preshape_hand | left_low | 0.00005656 | 0.00005656 | 0.00005656 | 12946 | 0.983 |
| preshape_hand | right_high | 0.00005795 | 0.00005795 | 0.00005795 | 17084 | 0.983 |
| preshape_hand | lifted_center | 0.00005383 | 0.00005383 | 0.00005383 | 15123 | 0.983 |
| preshape_hand | lifted_diag | 0.00005780 | 0.00005780 | 0.00005780 | 15777 | 0.983 |
| close_preview_hand | center | 0.00005728 | 0.00005728 | 0.00005728 | 14809 | 0.983 |
| close_preview_hand | left_low | 0.00005656 | 0.00005656 | 0.00005656 | 12946 | 0.983 |
| close_preview_hand | right_high | 0.00005795 | 0.00005795 | 0.00005795 | 17084 | 0.983 |
| close_preview_hand | lifted_center | 0.00005383 | 0.00005383 | 0.00005383 | 15123 | 0.983 |
| close_preview_hand | lifted_diag | 0.00005780 | 0.00005780 | 0.00005780 | 15777 | 0.983 |

## Interpretation

- PASS means the image-derived egg position can be combined with mechanical-hand FK to reproduce the hand-relative pose that would be obtained from direct ground truth.
- The current test still uses clean MuJoCo segmentation and a fixed perception camera.
- The next risk to test is occlusion during actual approach/contact phases.

Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\metadata\stage3_hand_relative_perception_v0.json`
Visual checks: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\visual_checks\stage3_hand_relative_perception_v0`
