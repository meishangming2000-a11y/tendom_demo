# Arm-Hand Stage1 V2 Ball-Pose Sweep Report

Generated: 2026-05-28T17:52:14

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Base ball: `[0.19022382, 0.187702, -0.06538044]`
- Grid: `{"x_offsets": [-0.015, 0.0, 0.015], "y_offsets": [-0.015, 0.0, 0.015], "z_offsets": [0.0]}`
- Episodes: `9`
- Success count: `9`
- Status: **PASS**
- Training used: **No**

## Success Criteria

- final lift height >= 0.080 m
- ball-hand contacts >= 1
- ball-floor contacts <= 0
- max penetration <= 0.015 m
- state remains finite

## Results

| idx | offset xyz | label | success | lift m | hand contacts | floor contacts | max pen m | four avg m | thumb m | failure reasons |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | `[-0.015, -0.015, 0.0]` | lift_success | 1 | 0.1517 | 7 | 0 | 0.003143 | 0.0511 | 0.0381 | - |
| 1 | `[0.0, -0.015, 0.0]` | lift_success | 1 | 0.1518 | 7 | 0 | 0.003134 | 0.0513 | 0.0381 | - |
| 2 | `[0.015, -0.015, 0.0]` | lift_success | 1 | 0.1588 | 7 | 0 | 0.003416 | 0.0625 | 0.0419 | - |
| 3 | `[-0.015, 0.0, 0.0]` | lift_success | 1 | 0.1519 | 7 | 0 | 0.003119 | 0.0515 | 0.0381 | - |
| 4 | `[0.0, 0.0, 0.0]` | lift_success | 1 | 0.1587 | 7 | 0 | 0.003416 | 0.0625 | 0.0419 | - |
| 5 | `[0.015, 0.0, 0.0]` | lift_success | 1 | 0.1587 | 7 | 0 | 0.003415 | 0.0625 | 0.0418 | - |
| 6 | `[-0.015, 0.015, 0.0]` | lift_success | 1 | 0.1520 | 7 | 0 | 0.003108 | 0.0516 | 0.0381 | - |
| 7 | `[0.0, 0.015, 0.0]` | lift_success | 1 | 0.1587 | 7 | 0 | 0.003415 | 0.0625 | 0.0419 | - |
| 8 | `[0.015, 0.015, 0.0]` | lift_success | 1 | 0.1585 | 7 | 0 | 0.003404 | 0.0624 | 0.0418 | - |

## Interpretation

- This sweep checks whether the scripted pure-physics lift has a local success region around the validated demo ball pose.
- It is a Stage2 task/API smoke artifact, not a training dataset and not a final collision-geometry validation.
- The next step is to freeze observation/action/reward/done contracts before collecting dataset v0.
