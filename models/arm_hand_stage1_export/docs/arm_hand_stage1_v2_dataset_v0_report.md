# Arm-Hand Stage1 V2 Dataset V0 Report

Generated: 2026-05-28T20:07:24

- Task: `arm_hand_stage1_lift_ball`
- Contract: `stage2_lift_ball_v0_1`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Episodes: `9`
- Total rows: `9067`
- obs shape: `[9067, 124]`
- actions shape: `[9067, 26]`
- next_obs shape: `[9067, 124]`
- Success count: `9 / 9`
- Terminal reasons: `{'success_lift_ball': 9}`
- Training ready: **No**

## Episode Summary

| ep | offset xyz | rows | terminal phase | status | reason | lift m | reward | hand contacts | max pen m |
|---:|---|---:|---|---|---|---:|---:|---:|---:|
| 0 | `[-0.015, -0.015, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 11.7685 | 7 | 0.003134 |
| 1 | `[0.0, -0.015, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0806 | 11.7695 | 7 | 0.003128 |
| 2 | `[0.015, -0.015, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 11.7637 | 7 | 0.003447 |
| 3 | `[-0.015, 0.0, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0801 | 11.7647 | 6 | 0.003149 |
| 4 | `[0.0, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 11.7656 | 7 | 0.003449 |
| 5 | `[0.015, 0.0, 0.0]` | 1007 | lift | success | success_lift_ball | 0.0809 | 11.7674 | 7 | 0.003445 |
| 6 | `[-0.015, 0.015, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0802 | 11.7658 | 6 | 0.003171 |
| 7 | `[0.0, 0.015, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 11.7651 | 7 | 0.003449 |
| 8 | `[0.015, 0.015, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0810 | 11.7683 | 6 | 0.003311 |

## Dataset Fields

- `obs`: observation before action.
- `actions`: position-target action applied at that step.
- `next_obs`: observation after one MuJoCo step.
- `rewards`, `dones`, `successes`, `failures`, `terminal_reason_ids`: labels from the frozen task contract.
- `episode_ids`, `step_ids`, `phase_ids`, `phase_step_ids`: rollout indexing.
- `initial_ball_positions`, `ball_offsets`: reset context for replay.

## Next Step

Run `replay_arm_hand_stage1_v2_dataset_v0.py` and use the replay report as the dataset QA gate before any BC/RL discussion.
