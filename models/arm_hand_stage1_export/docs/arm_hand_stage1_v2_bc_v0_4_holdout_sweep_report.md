# Arm-Hand Stage1 V2 BC V0.4 Holdout Sweep Report

Generated: 2026-05-31T01:24:47

- Status: **PARTIAL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `12`
- Success count: `11 / 12`
- Terminal reasons: `{'success_lift_hold': 11, 'timeout': 1}`
- Failure buckets: `{'passed': 11, 'no_lift_timeout': 1}`
- Final lift range: `-0.000184 m` to `0.092694 m`
- Final lift mean: `0.077033 m`
- Hold min lift range: `0.06727131699123147` to `0.08158973053083222`
- Offset grid: `{'x_values': [0.0125, 0.015, 0.0175], 'y_values': [0.005, 0.0075, 0.0125, 0.0175], 'z_values': [0.0], 'raw_offset_count': 12, 'excluded_seen_count': 0, 'exclude_seen_datasets': ['D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\data\\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz', 'D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\data\\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz'], 'selected_offsets': [[0.0125, 0.005, 0.0], [0.0125, 0.0075, 0.0], [0.0125, 0.0125, 0.0], [0.0125, 0.0175, 0.0], [0.015, 0.005, 0.0], [0.015, 0.0075, 0.0], [0.015, 0.0125, 0.0], [0.015, 0.0175, 0.0], [0.0175, 0.005, 0.0], [0.0175, 0.0075, 0.0], [0.0175, 0.0125, 0.0], [0.0175, 0.0175, 0.0]]}`
- Action smoothing: `0.5`
- Hold after success steps: `900`
- Hold settle steps: `180`
- Freeze after settle: `True`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | offset xyz | status | reason | bucket | steps | first success | hold steps | hold min m | final lift m | floor-after | no-contact-after | max pen after |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `[0.0125, 0.005, 0.0]` | success | success_lift_hold | passed | 2124 | 1044 | 900 | 0.081240 | 0.092546 | 0 | 0 | 0.003440 |
| 1 | `[0.0125, 0.0075, 0.0]` | success | success_lift_hold | passed | 2125 | 1045 | 900 | 0.081181 | 0.092404 | 0 | 0 | 0.003438 |
| 2 | `[0.0125, 0.0125, 0.0]` | success | success_lift_hold | passed | 2124 | 1044 | 900 | 0.081590 | 0.092694 | 0 | 0 | 0.003437 |
| 3 | `[0.0125, 0.0175, 0.0]` | success | success_lift_hold | passed | 2127 | 1047 | 900 | 0.075773 | 0.085536 | 0 | 0 | 0.003208 |
| 4 | `[0.015, 0.005, 0.0]` | success | success_lift_hold | passed | 2137 | 1057 | 900 | 0.070109 | 0.079127 | 0 | 0 | 0.002665 |
| 5 | `[0.015, 0.0075, 0.0]` | success | success_lift_hold | passed | 2137 | 1057 | 900 | 0.070022 | 0.079127 | 0 | 0 | 0.002660 |
| 6 | `[0.015, 0.0125, 0.0]` | success | success_lift_hold | passed | 2134 | 1054 | 900 | 0.070489 | 0.083044 | 0 | 0 | 0.003073 |
| 7 | `[0.015, 0.0175, 0.0]` | success | success_lift_hold | passed | 2137 | 1057 | 900 | 0.068786 | 0.080244 | 0 | 0 | 0.003156 |
| 8 | `[0.0175, 0.005, 0.0]` | success | success_lift_hold | passed | 2138 | 1058 | 900 | 0.068933 | 0.078957 | 0 | 0 | 0.002543 |
| 9 | `[0.0175, 0.0075, 0.0]` | failure | timeout | no_lift_timeout | 3000 | n/a | 0 | n/a | -0.000184 | 0 | 0 | 0.000000 |
| 10 | `[0.0175, 0.0125, 0.0]` | success | success_lift_hold | passed | 2135 | 1055 | 900 | 0.068715 | 0.081724 | 0 | 0 | 0.003081 |
| 11 | `[0.0175, 0.0175, 0.0]` | success | success_lift_hold | passed | 2139 | 1059 | 900 | 0.067271 | 0.079177 | 0 | 0 | 0.003162 |

## Interpretation

- This sweep uses unseen offset midpoints between the accepted v0.1/v0.2 reset grid points.
- PASS here is a promotion gate candidate, not a final maintained baseline by itself.
- If any episode fails, collect targeted diagnostics before RL warm-start.
