# Arm-Hand Stage1 V2 Training Readiness Report

Generated: 2026-05-29T01:20:07

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Contract: `stage2_lift_ball_v0_1`
- Status: **PASS**
- BC smoke ready: `True`
- Training ready: **No, experimental BC smoke only**
- Rows: `9067`
- Episodes: `9`
- Success terminals: `9 / 9`
- Replay QA: `PASS`
- Recommended feature mode: `phase_only`
- Train episodes: `[0, 2, 3, 4, 5, 7, 8]`
- Val episodes: `[1, 6]`
- Train samples: `7050`
- Val samples: `2017`

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
| default_hold | 90 | 810 |
| move_to_pre_approach | 260 | 2340 |
| approach_ball | 180 | 1620 |
| preshape | 120 | 1080 |
| close_four_fingers | 120 | 1080 |
| close_thumb | 120 | 1080 |
| lift | 119 | 1057 |
| hold_lift | 0 | 0 |

## Ranges

- Observation range: `[-20.939607618016897, 11.478420647066349]`
- Action range: `[-1.5439603100000001, 2.8411226300000005]`
- Reward range: `[-0.591198534649208, 11.769515623223855]`
- Low-variance action dims: `[4, 5, 23]`
- Low-variance obs dims count: `4`

## Interpretation

- PASS means the dataset is acceptable for one experimental offline BC smoke run.
- This does not promote the dataset to a maintained training baseline.
- RL remains blocked until the reset distribution, reward design, and broader data quality are accepted.

## Next Step

Run train_arm_hand_stage1_v2_bc_smoke.py only if status is PASS.
