# Stage3 Sensor Fusion Dataset Replay QA Report

Generated: 2026-06-05T01:30:35

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_sensor_fusion_expert_dataset_v0.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Episodes checked: `10`
- Status: **PASS**
- Shape status: `PASS`
- Replay status: `PASS`
- Max obs error: `0.000e+00`
- Max next_obs error: `0.000e+00`
- Max object position error: `0.000e+00`
- Success replay count: `10 / 10`
- Training ready: **True**

## Shape Check

- obs_dim_matches: `True`
- next_obs_dim_matches: `True`
- action_dim_matches: `True`
- row_counts_match: `True`
- nq_matches_model: `True`
- nv_matches_model: `True`
- nu_matches_model: `True`

## Episode Replay

| ep | status | reason | frames | obs err | next err | object err | failures |
|---:|---|---|---:|---:|---:|---:|---|
| 0 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 1 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 2 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 3 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 4 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 5 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 6 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 7 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 8 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |
| 9 | PASS | success_gentle_grasp_hold | 3100 | 0.000e+00 | 0.000e+00 | 0.000e+00 | - |

## Interpretation

- PASS means the saved action sequence deterministically reproduces the saved sensor observations and object trajectory.
- This gate must pass before using the dataset for BC or residual-policy training.
