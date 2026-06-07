# Stage3 Sensor Fusion BC Baseline V0 Eval Report

Generated: 2026-06-05T01:49:12

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_sensor_fusion_bc_baseline_v0_overfit.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Mean final lift: `0.103294 m`
- Mean hold stable fraction: `1.000`
- Max hold slip: `0.262`
- Max crush risk: `0.114`
- Max penetration: `0.002276 m`

- Hybrid control: `expert_arm_bc_hand`
- Expert prefix actuators: `6`

## Episode Results

| ep | trial | status | reason | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | success_gentle_grasp_hold | 0.09921 | 1.000 | 0.160 | 0.000 | 0.114 | 0.002276 | `[]` |
| 1 | left_low_nominal | PASS | success_gentle_grasp_hold | 0.10199 | 1.000 | 0.262 | 0.000 | 0.087 | 0.001730 | `[]` |
| 2 | right_high_nominal | PASS | success_gentle_grasp_hold | 0.09476 | 1.000 | 0.221 | 0.000 | 0.083 | 0.001665 | `[]` |
| 3 | left_high_zplus | PASS | success_gentle_grasp_hold | 0.10835 | 1.000 | 0.173 | 0.000 | 0.108 | 0.002162 | `[]` |
| 4 | right_low_zminus | PASS | success_gentle_grasp_hold | 0.10220 | 1.000 | 0.185 | 0.000 | 0.094 | 0.001875 | `[]` |
| 5 | front_small_lift | PASS | success_gentle_grasp_hold | 0.08563 | 1.000 | 0.155 | 0.000 | 0.086 | 0.001712 | `[]` |
| 6 | back_large_lift | PASS | success_gentle_grasp_hold | 0.11864 | 1.000 | 0.172 | 0.000 | 0.113 | 0.002256 | `[]` |
| 7 | lifted_center | PASS | success_gentle_grasp_hold | 0.09948 | 1.000 | 0.178 | 0.000 | 0.098 | 0.001962 | `[]` |
| 8 | lifted_diag | PASS | success_gentle_grasp_hold | 0.11093 | 1.000 | 0.191 | 0.000 | 0.100 | 0.002007 | `[]` |
| 9 | wide_diag | PASS | success_gentle_grasp_hold | 0.11175 | 1.000 | 0.169 | 0.000 | 0.111 | 0.002227 | `[]` |

## Interpretation

- This is closed-loop MuJoCo evaluation, not offline loss.
- The model still uses scripted phase timing and virtual-camera acquisition; it learns actuator targets from sensor abstraction observations.
- Compare this report against the scripted expert before promoting any policy.
