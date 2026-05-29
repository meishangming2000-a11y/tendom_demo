# Arm-Hand Stage1 V2 Training Readiness Report

Generated: 2026-05-30T01:43:00

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Contract: `stage2_lift_ball_v0_1`
- Status: **PASS**
- BC smoke ready: `True`
- Training ready: **No, experimental BC smoke only**
- Rows: `87773`
- Action field: `expert_actions`
- Episodes: `87`
- Success terminals: `87 / 87`
- Replay QA: `PASS`
- Recommended feature mode: `obs_phase`
- Train episodes: `[0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 24, 26, 27, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 45, 46, 48, 49, 50, 52, 53, 55, 56, 57, 58, 59, 60, 61, 62, 64, 67, 68, 70, 71, 72, 73, 75, 76, 77, 78, 79, 81, 83, 85, 86]`
- Val episodes: `[1, 17, 22, 23, 25, 28, 36, 44, 47, 51, 54, 63, 65, 66, 69, 74, 80, 82, 84]`
- Train samples: `68473`
- Val samples: `19300`

## Hard Checks

| check | pass |
|---|---:|
| required_fields_present | True |
| obs_is_2d | True |
| actions_is_2d | True |
| next_obs_shape_matches | True |
| row_counts_match | True |
| obs_finite | True |
| actions_finite | True |
| next_obs_finite | True |
| contract_version_matches | True |
| all_episodes_terminal_success | True |
| episode_split_has_train | True |
| episode_split_has_val | True |
| replay_qa_pass | True |

## Phase Coverage

| phase | observed length | rows |
|---|---:|---:|
| default_hold | 94 | 7830 |
| move_to_pre_approach | 270 | 22620 |
| approach_ball | 187 | 15660 |
| preshape | 125 | 10440 |
| close_four_fingers | 125 | 10440 |
| close_thumb | 125 | 10440 |
| lift | 143 | 10343 |
| hold_lift | 0 | 0 |

## Ranges

- Observation range: `[-26.581330389687817, 27.88781431546295]`
- Action range: `[-1.5708, 3.0211226300000007]`
- Reward range: `[-0.5931706689464402, 11.772574990272231]`
- Low-variance action dims: `[4, 5, 23]`
- Low-variance obs dims count: `1`

## Interpretation

- PASS means the dataset is acceptable for one experimental offline BC smoke run.
- This does not promote the dataset to a maintained training baseline.
- If terminal failures were allowed, they are treated as boundary-state coverage, not task success evidence.
- RL remains blocked until the reset distribution, reward design, and broader data quality are accepted.

## Next Step

Run train_arm_hand_stage1_v2_bc_smoke.py only if status is PASS.
