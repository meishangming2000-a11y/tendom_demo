# Stage3.7 Tactile Residual Teacher V0 Eval Report

Generated: 2026-06-05T02:33:08

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `stage3_phase_hand_policy_plus_tactile_residual_teacher`
- Residual phases: `['gentle_close_fingers', 'gentle_close_thumb', 'contact_settle', 'slow_lift', 'hold']`
- Episodes: `30`
- Success count: `30 / 30`
- Terminal reasons: `{'success_gentle_grasp_hold': 30}`
- Risk flags: `{'early_contact_in_approach': 30, 'transient_or_hold_slip': 30}`
- Mean final lift: `0.102795 m`
- Mean hold stable fraction: `1.000`
- Max transient slip: `1.000`
- Max hold slip: `0.330`
- Max crush risk: `0.129`
- Max penetration: `0.002574 m`
- Mean residual active steps: `0.0`
- Mean contact-settle steps: `1200.0`
- Max residual magnitude: `0.000000`

## Teacher Parameters

- slip deadband: `0.2`
- slip close gain: `0.0`
- unstable close gain: `0.0`
- no-contact close gain: `0.0`
- lift-start close gain: `0.0`
- lift-start fraction: `0.35`
- crush deadband: `0.35`
- penetration deadband: `0.004`
- relax gain: `0.03`
- thumb multiplier: `1.3`
- max abs residual: `0.025`

- adaptive contact settle: `True`
- min contact settle steps: `1200`
- max contact settle steps: `1200`
- settle stable window steps: `300`
- settle slip threshold: `0.18`

## Episode Results

| ep | trial | status | reason | residual steps | settle steps | max slip | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.693 | 0.10111 | 1.000 | 0.215 | 0.000 | 0.122 | 0.002434 | `[]` |
| 1 | left_low_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.679 | 0.10245 | 1.000 | 0.194 | 0.000 | 0.075 | 0.001504 | `[]` |
| 2 | right_high_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 1.000 | 0.09235 | 1.000 | 0.222 | 0.000 | 0.115 | 0.002306 | `[]` |
| 3 | left_high_zplus | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.737 | 0.10823 | 1.000 | 0.161 | 0.000 | 0.099 | 0.001990 | `[]` |
| 4 | right_low_zminus | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.728 | 0.10174 | 1.000 | 0.181 | 0.000 | 0.084 | 0.001671 | `[]` |
| 5 | front_small_lift | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.444 | 0.08601 | 1.000 | 0.150 | 0.000 | 0.082 | 0.001634 | `[]` |
| 6 | back_large_lift | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.679 | 0.11878 | 1.000 | 0.185 | 0.000 | 0.129 | 0.002573 | `[]` |
| 7 | lifted_center | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.576 | 0.10046 | 1.000 | 0.189 | 0.000 | 0.102 | 0.002039 | `[]` |
| 8 | lifted_diag | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.547 | 0.11212 | 1.000 | 0.202 | 0.000 | 0.099 | 0.001987 | `[]` |
| 9 | wide_diag | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.783 | 0.11299 | 1.000 | 0.178 | 0.000 | 0.088 | 0.001758 | `[]` |
| 10 | center_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.518 | 0.10044 | 1.000 | 0.157 | 0.000 | 0.093 | 0.001864 | `[]` |
| 11 | left_low_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.545 | 0.10326 | 1.000 | 0.106 | 0.000 | 0.082 | 0.001633 | `[]` |
| 12 | right_high_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.894 | 0.09446 | 1.000 | 0.241 | 0.000 | 0.112 | 0.002231 | `[]` |
| 13 | left_high_zplus | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.957 | 0.10845 | 1.000 | 0.164 | 0.000 | 0.119 | 0.002377 | `[]` |
| 14 | right_low_zminus | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.573 | 0.10066 | 1.000 | 0.166 | 0.000 | 0.097 | 0.001948 | `[]` |
| 15 | front_small_lift | PASS | success_gentle_grasp_hold | 0 | 1200 | 1.000 | 0.07966 | 1.000 | 0.276 | 0.000 | 0.111 | 0.002226 | `[]` |
| 16 | back_large_lift | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.835 | 0.11914 | 1.000 | 0.246 | 0.000 | 0.087 | 0.001732 | `[]` |
| 17 | lifted_center | PASS | success_gentle_grasp_hold | 0 | 1200 | 1.000 | 0.09978 | 1.000 | 0.199 | 0.000 | 0.108 | 0.002156 | `[]` |
| 18 | lifted_diag | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.566 | 0.11186 | 1.000 | 0.210 | 0.000 | 0.101 | 0.002011 | `[]` |
| 19 | wide_diag | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.816 | 0.11331 | 1.000 | 0.205 | 0.000 | 0.102 | 0.002033 | `[]` |
| 20 | center_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.532 | 0.09925 | 1.000 | 0.147 | 0.000 | 0.094 | 0.001885 | `[]` |
| 21 | left_low_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.570 | 0.10215 | 1.000 | 0.218 | 0.000 | 0.092 | 0.001842 | `[]` |
| 22 | right_high_nominal | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.655 | 0.09382 | 1.000 | 0.229 | 0.000 | 0.098 | 0.001952 | `[]` |
| 23 | left_high_zplus | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.997 | 0.10853 | 1.000 | 0.155 | 0.000 | 0.107 | 0.002139 | `[]` |
| 24 | right_low_zminus | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.585 | 0.10072 | 1.000 | 0.164 | 0.000 | 0.100 | 0.002008 | `[]` |
| 25 | front_small_lift | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.444 | 0.08425 | 1.000 | 0.145 | 0.000 | 0.081 | 0.001617 | `[]` |
| 26 | back_large_lift | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.680 | 0.11866 | 1.000 | 0.183 | 0.000 | 0.129 | 0.002574 | `[]` |
| 27 | lifted_center | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.887 | 0.08716 | 1.000 | 0.330 | 0.000 | 0.084 | 0.001690 | `[]` |
| 28 | lifted_diag | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.498 | 0.11176 | 1.000 | 0.179 | 0.000 | 0.097 | 0.001947 | `[]` |
| 29 | wide_diag | PASS | success_gentle_grasp_hold | 0 | 1200 | 0.806 | 0.11032 | 1.000 | 0.166 | 0.000 | 0.100 | 0.002002 | `[]` |

## Interpretation

- This is a rule-based teacher, not a trained residual policy.
- It tests whether tactile/slip fields can provide useful corrective labels before training a model.
- Early approach contact is expected to remain unless the arm/wrist approach phase is changed.
- A learned residual should only be trained from this teacher if it preserves success and improves at least one risk metric.
