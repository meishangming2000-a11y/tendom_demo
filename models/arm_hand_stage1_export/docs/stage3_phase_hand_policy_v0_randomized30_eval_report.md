# Stage3.6 Phase Hand Policy V0 Eval Report

Generated: 2026-06-05T02:35:24

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy`
- Learned phases: `['gentle_close_fingers', 'gentle_close_thumb', 'contact_settle', 'slow_lift', 'hold']`
- Episodes: `30`
- Success count: `30 / 30`
- Terminal reasons: `{'success_gentle_grasp_hold': 30}`
- Risk flags: `{'early_contact_in_approach': 30, 'transient_or_hold_slip': 30}`
- Mean final lift: `0.103251 m`
- Mean hold stable fraction: `1.000`
- Max hold slip: `0.263`
- Max crush risk: `0.129`
- Max penetration: `0.002573 m`
- Mean learned-control steps: `2740.0`

## Episode Results

| ep | trial | status | reason | learned steps | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.09844 | 1.000 | 0.167 | 0.000 | 0.092 | 0.001849 | `[]` |
| 1 | left_low_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.10348 | 1.000 | 0.252 | 0.000 | 0.091 | 0.001823 | `[]` |
| 2 | right_high_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.09555 | 1.000 | 0.201 | 0.000 | 0.072 | 0.001445 | `[]` |
| 3 | left_high_zplus | PASS | success_gentle_grasp_hold | 2740 | 0.10741 | 1.000 | 0.187 | 0.000 | 0.096 | 0.001912 | `[]` |
| 4 | right_low_zminus | PASS | success_gentle_grasp_hold | 2740 | 0.09981 | 1.000 | 0.176 | 0.000 | 0.095 | 0.001890 | `[]` |
| 5 | front_small_lift | PASS | success_gentle_grasp_hold | 2740 | 0.08737 | 1.000 | 0.165 | 0.000 | 0.085 | 0.001707 | `[]` |
| 6 | back_large_lift | PASS | success_gentle_grasp_hold | 2740 | 0.11964 | 1.000 | 0.169 | 0.000 | 0.088 | 0.001757 | `[]` |
| 7 | lifted_center | PASS | success_gentle_grasp_hold | 2740 | 0.10038 | 1.000 | 0.176 | 0.000 | 0.100 | 0.001994 | `[]` |
| 8 | lifted_diag | PASS | success_gentle_grasp_hold | 2740 | 0.10974 | 1.000 | 0.216 | 0.000 | 0.109 | 0.002170 | `[]` |
| 9 | wide_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11410 | 1.000 | 0.235 | 0.000 | 0.094 | 0.001889 | `[]` |
| 10 | center_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.10173 | 1.000 | 0.175 | 0.000 | 0.095 | 0.001895 | `[]` |
| 11 | left_low_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.10163 | 1.000 | 0.131 | 0.000 | 0.105 | 0.002101 | `[]` |
| 12 | right_high_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.09453 | 1.000 | 0.205 | 0.000 | 0.072 | 0.001435 | `[]` |
| 13 | left_high_zplus | PASS | success_gentle_grasp_hold | 2740 | 0.10925 | 1.000 | 0.263 | 0.000 | 0.110 | 0.002198 | `[]` |
| 14 | right_low_zminus | PASS | success_gentle_grasp_hold | 2740 | 0.09827 | 1.000 | 0.181 | 0.000 | 0.078 | 0.001553 | `[]` |
| 15 | front_small_lift | PASS | success_gentle_grasp_hold | 2740 | 0.08446 | 1.000 | 0.171 | 0.000 | 0.074 | 0.001471 | `[]` |
| 16 | back_large_lift | PASS | success_gentle_grasp_hold | 2740 | 0.11649 | 1.000 | 0.188 | 0.000 | 0.112 | 0.002241 | `[]` |
| 17 | lifted_center | PASS | success_gentle_grasp_hold | 2740 | 0.10016 | 1.000 | 0.211 | 0.000 | 0.105 | 0.002108 | `[]` |
| 18 | lifted_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11190 | 1.000 | 0.213 | 0.000 | 0.102 | 0.002032 | `[]` |
| 19 | wide_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11255 | 1.000 | 0.195 | 0.000 | 0.101 | 0.002015 | `[]` |
| 20 | center_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.10134 | 1.000 | 0.173 | 0.000 | 0.122 | 0.002434 | `[]` |
| 21 | left_low_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.10220 | 1.000 | 0.194 | 0.000 | 0.075 | 0.001504 | `[]` |
| 22 | right_high_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.08872 | 1.000 | 0.252 | 0.000 | 0.115 | 0.002306 | `[]` |
| 23 | left_high_zplus | PASS | success_gentle_grasp_hold | 2740 | 0.10801 | 1.000 | 0.178 | 0.000 | 0.099 | 0.001990 | `[]` |
| 24 | right_low_zminus | PASS | success_gentle_grasp_hold | 2740 | 0.10145 | 1.000 | 0.191 | 0.000 | 0.084 | 0.001671 | `[]` |
| 25 | front_small_lift | PASS | success_gentle_grasp_hold | 2740 | 0.08600 | 1.000 | 0.170 | 0.000 | 0.082 | 0.001634 | `[]` |
| 26 | back_large_lift | PASS | success_gentle_grasp_hold | 2740 | 0.11875 | 1.000 | 0.189 | 0.000 | 0.129 | 0.002573 | `[]` |
| 27 | lifted_center | PASS | success_gentle_grasp_hold | 2740 | 0.10027 | 1.000 | 0.188 | 0.000 | 0.102 | 0.002039 | `[]` |
| 28 | lifted_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11181 | 1.000 | 0.201 | 0.000 | 0.099 | 0.001987 | `[]` |
| 29 | wide_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11209 | 1.000 | 0.193 | 0.000 | 0.088 | 0.001758 | `[]` |

## Interpretation

- This is closed-loop MuJoCo evaluation of the formal Stage3.6 hand-only learned policy.
- Arm and wrist targets remain scripted expert actions throughout the episode.
- The learned policy replaces hand/finger actuator targets only in the configured contact/lift/hold phases.
- Compare risk flags and contact metrics against the scripted expert before promotion.
