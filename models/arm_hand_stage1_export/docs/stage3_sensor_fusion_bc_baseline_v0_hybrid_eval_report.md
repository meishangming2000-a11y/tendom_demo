# Stage3 Sensor Fusion BC Baseline V0 Eval Report

Generated: 2026-06-05T01:50:06

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_sensor_fusion_bc_baseline_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Mean final lift: `0.103356 m`
- Mean hold stable fraction: `1.000`
- Max hold slip: `0.262`
- Max crush risk: `0.110`
- Max penetration: `0.002199 m`

- Hybrid control: `expert_arm_bc_hand`
- Expert prefix actuators: `6`

## Episode Results

| ep | trial | status | reason | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | success_gentle_grasp_hold | 0.09909 | 1.000 | 0.165 | 0.000 | 0.110 | 0.002199 | `[]` |
| 1 | left_low_nominal | PASS | success_gentle_grasp_hold | 0.10197 | 1.000 | 0.262 | 0.000 | 0.080 | 0.001607 | `[]` |
| 2 | right_high_nominal | PASS | success_gentle_grasp_hold | 0.09479 | 1.000 | 0.220 | 0.000 | 0.075 | 0.001496 | `[]` |
| 3 | left_high_zplus | PASS | success_gentle_grasp_hold | 0.10851 | 1.000 | 0.175 | 0.000 | 0.104 | 0.002077 | `[]` |
| 4 | right_low_zminus | PASS | success_gentle_grasp_hold | 0.10181 | 1.000 | 0.188 | 0.000 | 0.079 | 0.001579 | `[]` |
| 5 | front_small_lift | PASS | success_gentle_grasp_hold | 0.08555 | 1.000 | 0.155 | 0.000 | 0.078 | 0.001563 | `[]` |
| 6 | back_large_lift | PASS | success_gentle_grasp_hold | 0.11899 | 1.000 | 0.197 | 0.000 | 0.101 | 0.002026 | `[]` |
| 7 | lifted_center | PASS | success_gentle_grasp_hold | 0.09961 | 1.000 | 0.178 | 0.000 | 0.100 | 0.001997 | `[]` |
| 8 | lifted_diag | PASS | success_gentle_grasp_hold | 0.11101 | 1.000 | 0.190 | 0.000 | 0.097 | 0.001941 | `[]` |
| 9 | wide_diag | PASS | success_gentle_grasp_hold | 0.11222 | 1.000 | 0.161 | 0.000 | 0.108 | 0.002158 | `[]` |

## Interpretation

- This is closed-loop MuJoCo evaluation, not offline loss.
- The model still uses scripted phase timing and virtual-camera acquisition; it learns actuator targets from sensor abstraction observations.
- Compare this report against the scripted expert before promoting any policy.
