# Stage3 Sensor Fusion Expert Dataset V0 Report

Generated: 2026-06-05T01:30:15

- Task: `stage3_sensor_aware_gentle_grasp_hold`
- Contract: `stage3_sensor_aware_gentle_grasp_hold_v0`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_sensor_fusion_expert_dataset_v0.npz`
- Episodes: `10`
- Total rows: `31000`
- Obs shape: `[31000, 130]`
- Actions shape: `[31000, 26]`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_nonhold_slip': 10}`
- Mean final lift: `0.103056 m`
- Min final lift: `0.085651 m`
- Max hold slip: `0.262`
- Max final hold slip: `0.000`
- Max crush risk: `0.113`
- Max penetration: `0.002259 m`
- Training ready: **No, replay QA required first**

## Episode Summary

| ep | trial | profile | rows | success | terminal | lift m | hold slip | final slip | crush | pen m | risks |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.09927 | 0.161 | 0.000 | 0.113 | 0.002259 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 1 | left_low_nominal | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.10199 | 0.262 | 0.000 | 0.088 | 0.001751 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 2 | right_high_nominal | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.09483 | 0.221 | 0.000 | 0.081 | 0.001617 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 3 | left_high_zplus | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.10840 | 0.174 | 0.000 | 0.107 | 0.002134 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 4 | right_low_zminus | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.10220 | 0.185 | 0.000 | 0.093 | 0.001861 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 5 | front_small_lift | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.08565 | 0.161 | 0.000 | 0.085 | 0.001701 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 6 | back_large_lift | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.11653 | 0.161 | 0.000 | 0.112 | 0.002246 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 7 | lifted_center | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.09948 | 0.179 | 0.000 | 0.098 | 0.001959 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 8 | lifted_diag | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.11095 | 0.191 | 0.000 | 0.101 | 0.002017 | `['early_contact_in_approach', 'transient_nonhold_slip']` |
| 9 | wide_diag | clean_nominal | 3100 | 1 | success_gentle_grasp_hold | 0.11127 | 0.178 | 0.000 | 0.111 | 0.002213 | `['early_contact_in_approach', 'transient_nonhold_slip']` |

## Interpretation

- This dataset is the first Stage3 learning-track data source.
- It records sensor-abstraction observations from virtual vision and MuJoCo contact-derived tactile/slip.
- Ground-truth object positions are present for evaluation and replay QA only.
- The known Stage3.5 risks are expected to appear: early approach contact and transient non-hold slip.

## Next Gate

Run replay QA before any BC or residual-policy training:

```powershell
python .\simulations\models\arm_hand_stage1_export\replay_stage3_sensor_fusion_dataset.py
```
