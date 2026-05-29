# Arm-Hand Stage1 V2 Training Readiness Report

Generated: 2026-05-30T00:38:54

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Contract: `stage2_lift_ball_v0_1`
- Status: **PASS**
- BC smoke ready: `True`
- Training ready: **No, experimental BC smoke only**
- Rows: `77154`
- Action field: `expert_actions`
- Episodes: `75`
- Success terminals: `68 / 75`
- Replay QA: `PASS`
- Recommended feature mode: `obs_phase`
- Train episodes: `[2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 14, 15, 16, 18, 19, 20, 21, 23, 24, 25, 26, 27, 29, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 67, 68, 69, 70, 71, 72]`
- Val episodes: `[0, 1, 6, 13, 17, 22, 28, 30, 33, 45, 51, 52, 53, 64, 73, 74]`
- Train samples: `60948`
- Val samples: `16206`

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
| default_hold | 94 | 6750 |
| move_to_pre_approach | 270 | 19500 |
| approach_ball | 187 | 13500 |
| preshape | 125 | 9000 |
| close_four_fingers | 125 | 9000 |
| close_thumb | 125 | 9000 |
| lift | 229 | 9579 |
| hold_lift | 125 | 825 |

## Ranges

- Observation range: `[-22.772077008859284, 18.44202311595627]`
- Action range: `[-1.5439603100000001, 2.8411226300000005]`
- Reward range: `[-10.148466196154828, 11.772856625917475]`
- Low-variance action dims: `[4, 5, 23]`
- Low-variance obs dims count: `1`

## Interpretation

- PASS means the dataset is acceptable for one experimental offline BC smoke run.
- This does not promote the dataset to a maintained training baseline.
- If terminal failures were allowed, they are treated as boundary-state coverage, not task success evidence.
- RL remains blocked until the reset distribution, reward design, and broader data quality are accepted.

## Next Step

Run train_arm_hand_stage1_v2_bc_smoke.py only if status is PASS.
