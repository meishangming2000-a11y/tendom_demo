# Stage3.6 Phase Hand Policy V0 Eval Report

Generated: 2026-06-05T02:01:08

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy`
- Learned phases: `['gentle_close_fingers', 'gentle_close_thumb', 'contact_settle', 'slow_lift', 'hold']`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Mean final lift: `0.103050 m`
- Mean hold stable fraction: `1.000`
- Max hold slip: `0.262`
- Max crush risk: `0.113`
- Max penetration: `0.002260 m`
- Mean learned-control steps: `2740.0`

## Episode Results

| ep | trial | status | reason | learned steps | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.09926 | 1.000 | 0.162 | 0.000 | 0.113 | 0.002260 | `[]` |
| 1 | left_low_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.10198 | 1.000 | 0.262 | 0.000 | 0.087 | 0.001737 | `[]` |
| 2 | right_high_nominal | PASS | success_gentle_grasp_hold | 2740 | 0.09483 | 1.000 | 0.220 | 0.000 | 0.080 | 0.001602 | `[]` |
| 3 | left_high_zplus | PASS | success_gentle_grasp_hold | 2740 | 0.10840 | 1.000 | 0.174 | 0.000 | 0.106 | 0.002120 | `[]` |
| 4 | right_low_zminus | PASS | success_gentle_grasp_hold | 2740 | 0.10221 | 1.000 | 0.185 | 0.000 | 0.092 | 0.001846 | `[]` |
| 5 | front_small_lift | PASS | success_gentle_grasp_hold | 2740 | 0.08565 | 1.000 | 0.157 | 0.000 | 0.085 | 0.001691 | `[]` |
| 6 | back_large_lift | PASS | success_gentle_grasp_hold | 2740 | 0.11650 | 1.000 | 0.163 | 0.000 | 0.112 | 0.002232 | `[]` |
| 7 | lifted_center | PASS | success_gentle_grasp_hold | 2740 | 0.09948 | 1.000 | 0.179 | 0.000 | 0.098 | 0.001964 | `[]` |
| 8 | lifted_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11095 | 1.000 | 0.191 | 0.000 | 0.101 | 0.002020 | `[]` |
| 9 | wide_diag | PASS | success_gentle_grasp_hold | 2740 | 0.11125 | 1.000 | 0.179 | 0.000 | 0.110 | 0.002202 | `[]` |

## Interpretation

- This is closed-loop MuJoCo evaluation of the formal Stage3.6 hand-only learned policy.
- Arm and wrist targets remain scripted expert actions throughout the episode.
- The learned policy replaces hand/finger actuator targets only in the configured contact/lift/hold phases.
- Compare risk flags and contact metrics against the scripted expert before promotion.
