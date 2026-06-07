# Stage3.7 Tactile Residual Teacher V0 Eval Report

Generated: 2026-06-05T02:18:21

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `stage3_phase_hand_policy_plus_tactile_residual_teacher`
- Residual phases: `['gentle_close_fingers', 'gentle_close_thumb', 'contact_settle', 'slow_lift', 'hold']`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Mean final lift: `0.103313 m`
- Mean hold stable fraction: `1.000`
- Max transient slip: `1.000`
- Max hold slip: `0.262`
- Max crush risk: `0.113`
- Max penetration: `0.002260 m`
- Mean residual active steps: `0.0`
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

## Episode Results

| ep | trial | status | reason | residual steps | max slip | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | success_gentle_grasp_hold | 0 | 0.585 | 0.09931 | 1.000 | 0.163 | 0.000 | 0.113 | 0.002260 | `[]` |
| 1 | left_low_nominal | PASS | success_gentle_grasp_hold | 0 | 1.000 | 0.10204 | 1.000 | 0.262 | 0.000 | 0.087 | 0.001737 | `[]` |
| 2 | right_high_nominal | PASS | success_gentle_grasp_hold | 0 | 0.578 | 0.09463 | 1.000 | 0.198 | 0.000 | 0.080 | 0.001602 | `[]` |
| 3 | left_high_zplus | PASS | success_gentle_grasp_hold | 0 | 0.792 | 0.10856 | 1.000 | 0.176 | 0.000 | 0.106 | 0.002120 | `[]` |
| 4 | right_low_zminus | PASS | success_gentle_grasp_hold | 0 | 1.000 | 0.10235 | 1.000 | 0.182 | 0.000 | 0.092 | 0.001846 | `[]` |
| 5 | front_small_lift | PASS | success_gentle_grasp_hold | 0 | 0.479 | 0.08564 | 1.000 | 0.146 | 0.000 | 0.085 | 0.001691 | `[]` |
| 6 | back_large_lift | PASS | success_gentle_grasp_hold | 0 | 0.603 | 0.11867 | 1.000 | 0.180 | 0.000 | 0.112 | 0.002232 | `[]` |
| 7 | lifted_center | PASS | success_gentle_grasp_hold | 0 | 0.787 | 0.09960 | 1.000 | 0.185 | 0.000 | 0.098 | 0.001964 | `[]` |
| 8 | lifted_diag | PASS | success_gentle_grasp_hold | 0 | 0.498 | 0.11109 | 1.000 | 0.192 | 0.000 | 0.101 | 0.002020 | `[]` |
| 9 | wide_diag | PASS | success_gentle_grasp_hold | 0 | 0.941 | 0.11125 | 1.000 | 0.174 | 0.000 | 0.110 | 0.002202 | `[]` |

## Interpretation

- This is a rule-based teacher, not a trained residual policy.
- It tests whether tactile/slip fields can provide useful corrective labels before training a model.
- Early approach contact is expected to remain unless the arm/wrist approach phase is changed.
- A learned residual should only be trained from this teacher if it preserves success and improves at least one risk metric.
