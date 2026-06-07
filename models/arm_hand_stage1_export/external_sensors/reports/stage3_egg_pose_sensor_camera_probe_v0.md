# Stage3 Egg Pose Sensor Accuracy V0

Generated: 2026-06-04T00:57:46

## Scope

This is a MuJoCo-only Stage3.2b perception-geometry experiment. It tests whether an external sensor tool can estimate the egg position from rendered depth and segmentation. MuJoCo ground truth is used only for evaluation.

## Inputs

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Cameras: `['stage3_egg_closeup', 'stage3_egg_overview']`
- Resolution: `640 x 480`
- Max pass error: `0.002000 m`
- Pose samples: `11`

## Result

- Overall status: `FAIL`
- Overall max error: `0.000059 m`

## Camera Summary

| camera | samples | mean error m | max error m | rms error m | min mask pixels |
|---|---:|---:|---:|---:|---:|
| stage3_egg_closeup | 11 | 0.00005723 | 0.00005858 | 0.00005724 | 12946 |
| stage3_egg_overview | 0 | - | - | - | - |

## Per-Sample Results

| camera | sample | gt xyz m | estimated xyz m | error m | mask pixels | confidence |
|---|---|---|---|---:|---:|---:|
| stage3_egg_closeup | floor_dx-0.020_dy-0.015 | `[0.170224, 0.172702, -0.05538]` | `[0.170174, 0.172683, -0.055362]` | 0.00005656 | 12946 | 0.983 |
| stage3_egg_closeup | floor_dx-0.020_dy+0.000 | `[0.170224, 0.187702, -0.05538]` | `[0.170174, 0.187684, -0.055362]` | 0.00005644 | 13533 | 0.983 |
| stage3_egg_closeup | floor_dx-0.020_dy+0.015 | `[0.170224, 0.202702, -0.05538]` | `[0.170172, 0.202686, -0.055362]` | 0.00005712 | 14144 | 0.983 |
| stage3_egg_closeup | floor_dx+0.000_dy-0.015 | `[0.190224, 0.172702, -0.05538]` | `[0.190174, 0.172681, -0.055361]` | 0.00005781 | 14151 | 0.983 |
| stage3_egg_closeup | floor_dx+0.000_dy+0.000 | `[0.190224, 0.187702, -0.05538]` | `[0.190173, 0.187683, -0.055361]` | 0.00005728 | 14809 | 0.983 |
| stage3_egg_closeup | floor_dx+0.000_dy+0.015 | `[0.190224, 0.202702, -0.05538]` | `[0.190172, 0.202686, -0.055361]` | 0.00005782 | 15515 | 0.983 |
| stage3_egg_closeup | floor_dx+0.020_dy-0.015 | `[0.210224, 0.172702, -0.05538]` | `[0.210174, 0.172679, -0.05536]` | 0.00005858 | 15541 | 0.983 |
| stage3_egg_closeup | floor_dx+0.020_dy+0.000 | `[0.210224, 0.187702, -0.05538]` | `[0.210173, 0.187682, -0.05536]` | 0.00005828 | 16283 | 0.983 |
| stage3_egg_closeup | floor_dx+0.020_dy+0.015 | `[0.210224, 0.202702, -0.05538]` | `[0.210173, 0.202684, -0.055359]` | 0.00005795 | 17084 | 0.983 |
| stage3_egg_closeup | lifted_center_z+0.015 | `[0.190224, 0.187702, -0.04038]` | `[0.190176, 0.187684, -0.040365]` | 0.00005383 | 15123 | 0.983 |
| stage3_egg_closeup | lifted_diag_z+0.012 | `[0.204224, 0.177702, -0.04338]` | `[0.204173, 0.177681, -0.043362]` | 0.00005780 | 15777 | 0.983 |
| stage3_egg_overview | floor_dx-0.020_dy-0.015 | `[0.17022382, 0.17270200000000002, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx-0.020_dy+0.000 | `[0.17022382, 0.187702, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx-0.020_dy+0.015 | `[0.17022382, 0.202702, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx+0.000_dy-0.015 | `[0.19022382, 0.17270200000000002, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx+0.000_dy+0.000 | `[0.19022382, 0.187702, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx+0.000_dy+0.015 | `[0.19022382, 0.202702, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx+0.020_dy-0.015 | `[0.21022381999999998, 0.17270200000000002, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx+0.020_dy+0.000 | `[0.21022381999999998, 0.187702, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | floor_dx+0.020_dy+0.015 | `[0.21022381999999998, 0.202702, -0.05538044]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | lifted_center_z+0.015 | `[0.19022382, 0.187702, -0.040380440000000004]` | failed | - | 0 | 0.000 |
| stage3_egg_overview | lifted_diag_z+0.012 | `[0.20422382, 0.177702, -0.043380440000000006]` | failed | - | 0 | 0.000 |

## Interpretation

- PASS here means the geometry sensor can recover egg center position from rendered images for fixed test poses.
- This does not yet test fingertip-relative pose, occlusion during grasp, or real camera images.
- The next Stage3.2b step is to add palm/fingertip FK and report object-to-hand relative vectors.

Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\metadata\stage3_egg_pose_sensor_camera_probe_v0.json`
Visual checks: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\visual_checks\stage3_egg_pose_sensor_camera_probe_v0`
