# Arm-Hand Stage1 V2 BC V0.4 Holdout Sweep Report

Generated: 2026-05-31T01:29:34

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `12`
- Success count: `12 / 12`
- Terminal reasons: `{'success_lift_hold': 12}`
- Failure buckets: `{'passed': 12}`
- Final lift range: `0.075788 m` to `0.092617 m`
- Final lift mean: `0.083053 m`
- Hold min lift range: `0.05257597589228052` to `0.08189961051772995`
- Offset grid: `{'x_values': [0.0125, 0.015, 0.0175], 'y_values': [0.005, 0.0075, 0.0125, 0.0175], 'z_values': [0.0], 'raw_offset_count': 12, 'excluded_seen_count': 0, 'exclude_seen_datasets': ['D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\data\\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz', 'D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\data\\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz'], 'selected_offsets': [[0.0125, 0.005, 0.0], [0.0125, 0.0075, 0.0], [0.0125, 0.0125, 0.0], [0.0125, 0.0175, 0.0], [0.015, 0.005, 0.0], [0.015, 0.0075, 0.0], [0.015, 0.0125, 0.0], [0.015, 0.0175, 0.0], [0.0175, 0.005, 0.0], [0.0175, 0.0075, 0.0], [0.0175, 0.0125, 0.0], [0.0175, 0.0175, 0.0]]}`
- Action smoothing: `0.2`
- Hold after success steps: `900`
- Hold settle steps: `180`
- Freeze after settle: `True`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | offset xyz | status | reason | bucket | steps | first success | hold steps | hold min m | final lift m | floor-after | no-contact-after | max pen after |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `[0.0125, 0.005, 0.0]` | success | success_lift_hold | passed | 2124 | 1044 | 900 | 0.081038 | 0.092617 | 0 | 0 | 0.003445 |
| 1 | `[0.0125, 0.0075, 0.0]` | success | success_lift_hold | passed | 2124 | 1044 | 900 | 0.081900 | 0.092323 | 0 | 0 | 0.003437 |
| 2 | `[0.0125, 0.0125, 0.0]` | success | success_lift_hold | passed | 2123 | 1043 | 900 | 0.081306 | 0.091990 | 0 | 0 | 0.003436 |
| 3 | `[0.0125, 0.0175, 0.0]` | success | success_lift_hold | passed | 2131 | 1051 | 900 | 0.074653 | 0.084937 | 0 | 0 | 0.003150 |
| 4 | `[0.015, 0.005, 0.0]` | success | success_lift_hold | passed | 2136 | 1056 | 900 | 0.070400 | 0.079227 | 0 | 0 | 0.002657 |
| 5 | `[0.015, 0.0075, 0.0]` | success | success_lift_hold | passed | 2137 | 1057 | 900 | 0.068558 | 0.078668 | 0 | 0 | 0.002548 |
| 6 | `[0.015, 0.0125, 0.0]` | success | success_lift_hold | passed | 2133 | 1053 | 900 | 0.055076 | 0.081862 | 0 | 0 | 0.002934 |
| 7 | `[0.015, 0.0175, 0.0]` | success | success_lift_hold | passed | 2133 | 1053 | 900 | 0.071514 | 0.082479 | 0 | 0 | 0.003125 |
| 8 | `[0.0175, 0.005, 0.0]` | success | success_lift_hold | passed | 2135 | 1055 | 900 | 0.065638 | 0.078607 | 0 | 0 | 0.002574 |
| 9 | `[0.0175, 0.0075, 0.0]` | success | success_lift_hold | passed | 2143 | 1063 | 900 | 0.052576 | 0.078270 | 0 | 0 | 0.002279 |
| 10 | `[0.0175, 0.0125, 0.0]` | success | success_lift_hold | passed | 2239 | 1059 | 900 | 0.060327 | 0.075788 | 0 | 0 | 0.002809 |
| 11 | `[0.0175, 0.0175, 0.0]` | success | success_lift_hold | passed | 2136 | 1056 | 900 | 0.067562 | 0.079870 | 0 | 0 | 0.003133 |

## Interpretation

- This sweep uses unseen offset midpoints between the accepted v0.1/v0.2 reset grid points.
- PASS here is a promotion gate candidate, not a final maintained baseline by itself.
- If any episode fails, collect targeted diagnostics before RL warm-start.
