# Stage3.7C Contact Transition Gate V0 Eval Report

Generated: 2026-06-05T09:22:41

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_and_transition_gates`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10, 'transition_gate_budget_exhausted': 5}`
- Gate release reasons: `{'stable_window_met': 10}`
- Top-slip phases: `{'slow_lift': 4, 'contact_settle': 5, 'gentle_close_thumb': 1}`
- Transition holds by phase: `{'slow_lift': 1213, 'gentle_close_thumb': 64}`
- Transition budget exhaustion: `{'slow_lift': 319}`
- Mean final lift: `0.103291 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.582`
- Max transient slip: `0.965`
- Max hold slip: `0.258`
- Max crush risk: `0.113`
- Max penetration: `0.002258 m`
- Mean transition hold steps: `127.7`
- Mean approach contact-stop events: `1.0`

## Gate Parameters

- stop approach on contact: `True`
- approach contact stop error: `0.014`
- transition gate phases: `['gentle_close_thumb', 'slow_lift']`
- transition slip threshold: `0.28`
- transition crush threshold: `0.35`
- transition penetration threshold: `0.004`
- max transition hold steps per phase: `200`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | transition holds | approach stop | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.507 | slow_lift | 200 | 1 | 2000 | 0.09944 | 1.000 | 0.169 | 0.105 | 0.002101 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 1 | left_low_nominal | PASS | 0.481 | slow_lift | 200 | 1 | 2000 | 0.10215 | 1.000 | 0.258 | 0.100 | 0.001991 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 2 | right_high_nominal | PASS | 0.442 | contact_settle | 57 | 1 | 2000 | 0.09423 | 1.000 | 0.182 | 0.082 | 0.001631 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 0.823 | contact_settle | 226 | 1 | 2000 | 0.10910 | 1.000 | 0.171 | 0.106 | 0.002125 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 4 | right_low_zminus | PASS | 0.442 | slow_lift | 43 | 1 | 2000 | 0.10254 | 1.000 | 0.163 | 0.092 | 0.001835 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | 0.360 | contact_settle | 28 | 1 | 2000 | 0.08556 | 1.000 | 0.142 | 0.083 | 0.001668 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.434 | slow_lift | 46 | 1 | 2000 | 0.11735 | 1.000 | 0.152 | 0.113 | 0.002258 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | 0.778 | contact_settle | 39 | 1 | 2000 | 0.09997 | 1.000 | 0.188 | 0.095 | 0.001899 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | 0.589 | contact_settle | 200 | 1 | 2000 | 0.11163 | 1.000 | 0.216 | 0.102 | 0.002032 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 9 | wide_diag | PASS | 0.965 | gentle_close_thumb | 238 | 1 | 2000 | 0.11095 | 1.000 | 0.162 | 0.111 | 0.002226 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |

## Interpretation

- This is a MuJoCo-only repair probe layered on Stage3.7B.
- It tests whether contact-transition pauses reduce transient slip before changing the learned hand policy.
- Success is still judged by the Stage3 gentle-grasp hold criteria; full-episode transient slip is reported as a risk flag.
