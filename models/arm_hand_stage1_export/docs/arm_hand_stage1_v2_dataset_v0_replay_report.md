# Arm-Hand Stage1 V2 Dataset V0 Replay Report

Generated: 2026-05-28T20:10:07

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Contract: `stage2_lift_ball_v0_1`
- Episodes checked: `9`
- Status: **PASS**
- Shape check: `PASS`
- Max obs error: `0.000e+00`
- Max next_obs error: `0.000e+00`
- Max reward error: `0.000e+00`

## Shape Check

- obs_dim_matches: `True`
- next_obs_dim_matches: `True`
- action_dim_matches: `True`
- row_counts_match: `True`
- contract_version_matches: `True`

## Episode Replay

| ep | status | reason | frames | obs err | next obs err | reward err | failures |
|---:|---|---|---:|---:|---:|---:|---|
| 0 | PASS | success_lift_ball | 1009 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 1 | PASS | success_lift_ball | 1009 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 2 | PASS | success_lift_ball | 1006 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 3 | PASS | success_lift_ball | 1008 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 4 | PASS | success_lift_ball | 1006 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 5 | PASS | success_lift_ball | 1007 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 6 | PASS | success_lift_ball | 1008 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 7 | PASS | success_lift_ball | 1006 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 8 | PASS | success_lift_ball | 1008 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |

## Interpretation

- PASS means the dataset is structurally consistent with the frozen task contract and deterministic replay reproduces obs/reward labels within tolerance.
- This is still dataset QA, not model training.
