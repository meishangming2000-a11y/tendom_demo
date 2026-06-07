# Stage3.7C Contact Transition Gate V0 Eval Report

Generated: 2026-06-05T09:22:37

- Status: **PARTIAL**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_and_transition_gates`
- Episodes: `10`
- Success count: `9 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 9, 'hold_slip_score_high': 1}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10, 'hold_slip_high': 1}`
- Gate release reasons: `{'stable_window_met': 10}`
- Top-slip phases: `{'contact_settle': 6, 'slow_lift': 3, 'gentle_close_thumb': 1}`
- Transition holds by phase: `{'slow_lift': 842, 'gentle_close_thumb': 16}`
- Transition budget exhaustion: `{}`
- Mean final lift: `0.103276 m`
- Mean hold stable fraction: `0.999`
- Mean max transient slip: `0.572`
- Max transient slip: `0.965`
- Max hold slip: `0.388`
- Max crush risk: `0.113`
- Max penetration: `0.002258 m`
- Mean transition hold steps: `85.8`
- Mean approach contact-stop events: `1.0`

## Gate Parameters

- stop approach on contact: `True`
- approach contact stop error: `0.014`
- transition gate phases: `['gentle_close_thumb', 'slow_lift']`
- transition slip threshold: `0.35`
- transition crush threshold: `0.35`
- transition penetration threshold: `0.004`
- max transition hold steps per phase: `500`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | transition holds | approach stop | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.382 | contact_settle | 19 | 1 | 2000 | 0.09941 | 1.000 | 0.145 | 0.105 | 0.002101 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | 0.491 | slow_lift | 185 | 1 | 2000 | 0.10215 | 1.000 | 0.270 | 0.100 | 0.001991 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | 0.442 | contact_settle | 79 | 1 | 2000 | 0.09423 | 1.000 | 0.168 | 0.082 | 0.001631 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 0.818 | contact_settle | 45 | 1 | 2000 | 0.10902 | 1.000 | 0.151 | 0.106 | 0.002125 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | 0.457 | slow_lift | 32 | 1 | 2000 | 0.10254 | 1.000 | 0.163 | 0.092 | 0.001835 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | 0.360 | contact_settle | 0 | 1 | 2000 | 0.08555 | 1.000 | 0.142 | 0.083 | 0.001668 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.439 | slow_lift | 35 | 1 | 2000 | 0.11735 | 1.000 | 0.153 | 0.113 | 0.002258 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | 0.778 | contact_settle | 5 | 1 | 2000 | 0.09996 | 1.000 | 0.188 | 0.095 | 0.001899 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | FAIL | 0.589 | contact_settle | 188 | 1 | 2000 | 0.11161 | 0.988 | 0.388 | 0.102 | 0.002032 | `['early_contact_in_approach', 'transient_or_hold_slip', 'hold_slip_high']` |
| 9 | wide_diag | PASS | 0.965 | gentle_close_thumb | 270 | 1 | 2000 | 0.11094 | 1.000 | 0.323 | 0.111 | 0.002226 | `['early_contact_in_approach', 'transient_or_hold_slip']` |

## Interpretation

- This is a MuJoCo-only repair probe layered on Stage3.7B.
- It tests whether contact-transition pauses reduce transient slip before changing the learned hand policy.
- Success is still judged by the Stage3 gentle-grasp hold criteria; full-episode transient slip is reported as a risk flag.
