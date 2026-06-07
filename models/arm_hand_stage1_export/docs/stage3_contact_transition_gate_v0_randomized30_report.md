# Stage3.7C Contact Transition Gate V0 Eval Report

Generated: 2026-06-05T09:30:36

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_and_transition_gates`
- Episodes: `30`
- Success count: `30 / 30`
- Terminal reasons: `{'success_gentle_grasp_hold': 30}`
- Risk flags: `{'early_contact_in_approach': 30, 'transient_or_hold_slip': 30, 'transition_gate_budget_exhausted': 19}`
- Gate release reasons: `{'stable_window_met': 30}`
- Top-slip phases: `{'contact_settle': 9, 'slow_lift': 14, 'gentle_close_thumb': 7}`
- Transition holds by phase: `{'slow_lift': 3285}`
- Transition budget exhaustion: `{'slow_lift': 1995}`
- Mean final lift: `0.103054 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.602`
- Max transient slip: `1.000`
- Max hold slip: `0.315`
- Max crush risk: `0.127`
- Max penetration: `0.002542 m`
- Mean transition hold steps: `109.5`
- Mean approach contact-stop events: `0.0`

## Gate Parameters

- stop approach on contact: `False`
- approach contact stop error: `0.014`
- transition gate phases: `['slow_lift']`
- transition slip threshold: `0.28`
- transition crush threshold: `0.35`
- transition penetration threshold: `0.004`
- max transition hold steps per phase: `150`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | transition holds | approach stop | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.395 | contact_settle | 26 | 0 | 2000 | 0.10057 | 1.000 | 0.166 | 0.120 | 0.002409 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | 0.370 | slow_lift | 75 | 0 | 2000 | 0.10254 | 1.000 | 0.191 | 0.077 | 0.001548 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | 1.000 | slow_lift | 150 | 0 | 2000 | 0.09525 | 1.000 | 0.239 | 0.115 | 0.002294 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 3 | left_high_zplus | PASS | 0.824 | gentle_close_thumb | 150 | 0 | 2000 | 0.10852 | 1.000 | 0.152 | 0.100 | 0.001996 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 4 | right_low_zminus | PASS | 0.505 | slow_lift | 51 | 0 | 2000 | 0.10173 | 1.000 | 0.177 | 0.081 | 0.001611 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | 0.430 | contact_settle | 31 | 0 | 2000 | 0.08609 | 1.000 | 0.152 | 0.080 | 0.001605 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.405 | slow_lift | 150 | 0 | 2000 | 0.11885 | 1.000 | 0.190 | 0.127 | 0.002542 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 7 | lifted_center | PASS | 0.561 | gentle_close_thumb | 10 | 0 | 2000 | 0.10049 | 1.000 | 0.189 | 0.102 | 0.002045 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | 0.542 | contact_settle | 150 | 0 | 2000 | 0.11230 | 1.000 | 0.194 | 0.099 | 0.001980 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 9 | wide_diag | PASS | 0.785 | gentle_close_thumb | 150 | 0 | 2000 | 0.11277 | 1.000 | 0.173 | 0.089 | 0.001778 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 10 | center_nominal | PASS | 0.453 | slow_lift | 150 | 0 | 2000 | 0.10069 | 1.000 | 0.131 | 0.091 | 0.001820 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 11 | left_low_nominal | PASS | 0.461 | slow_lift | 150 | 0 | 2000 | 0.10329 | 1.000 | 0.101 | 0.083 | 0.001652 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 12 | right_high_nominal | PASS | 0.433 | contact_settle | 150 | 0 | 2000 | 0.09382 | 1.000 | 0.195 | 0.109 | 0.002177 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 13 | left_high_zplus | PASS | 0.803 | contact_settle | 150 | 0 | 2000 | 0.10854 | 1.000 | 0.153 | 0.117 | 0.002342 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 14 | right_low_zminus | PASS | 0.370 | slow_lift | 22 | 0 | 2000 | 0.10050 | 1.000 | 0.149 | 0.094 | 0.001889 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 15 | front_small_lift | PASS | 0.895 | slow_lift | 150 | 0 | 2000 | 0.08006 | 1.000 | 0.272 | 0.111 | 0.002228 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 16 | back_large_lift | PASS | 0.566 | slow_lift | 150 | 0 | 2000 | 0.12006 | 1.000 | 0.266 | 0.085 | 0.001695 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 17 | lifted_center | PASS | 0.997 | gentle_close_thumb | 13 | 0 | 2000 | 0.10010 | 1.000 | 0.200 | 0.108 | 0.002166 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 18 | lifted_diag | PASS | 0.463 | contact_settle | 150 | 0 | 2000 | 0.11207 | 1.000 | 0.203 | 0.100 | 0.002002 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 19 | wide_diag | PASS | 1.000 | gentle_close_thumb | 101 | 0 | 2000 | 0.11368 | 1.000 | 0.207 | 0.103 | 0.002054 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 20 | center_nominal | PASS | 0.469 | slow_lift | 150 | 0 | 2000 | 0.09932 | 1.000 | 0.148 | 0.093 | 0.001854 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 21 | left_low_nominal | PASS | 0.377 | slow_lift | 150 | 0 | 2000 | 0.10219 | 1.000 | 0.220 | 0.095 | 0.001894 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 22 | right_high_nominal | PASS | 0.687 | contact_settle | 59 | 0 | 2000 | 0.09372 | 1.000 | 0.170 | 0.093 | 0.001864 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 23 | left_high_zplus | PASS | 0.781 | gentle_close_thumb | 150 | 0 | 2000 | 0.10863 | 1.000 | 0.153 | 0.107 | 0.002143 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 24 | right_low_zminus | PASS | 0.371 | slow_lift | 22 | 0 | 2000 | 0.10058 | 1.000 | 0.145 | 0.098 | 0.001968 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 25 | front_small_lift | PASS | 0.402 | contact_settle | 150 | 0 | 2000 | 0.08417 | 1.000 | 0.108 | 0.079 | 0.001583 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 26 | back_large_lift | PASS | 0.410 | slow_lift | 25 | 0 | 2000 | 0.11849 | 1.000 | 0.186 | 0.127 | 0.002541 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 27 | lifted_center | PASS | 1.000 | slow_lift | 150 | 0 | 2000 | 0.09049 | 1.000 | 0.315 | 0.084 | 0.001689 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 28 | lifted_diag | PASS | 0.489 | contact_settle | 150 | 0 | 2000 | 0.11202 | 1.000 | 0.167 | 0.097 | 0.001948 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |
| 29 | wide_diag | PASS | 0.804 | gentle_close_thumb | 150 | 0 | 2000 | 0.11010 | 1.000 | 0.161 | 0.101 | 0.002024 | `['early_contact_in_approach', 'transient_or_hold_slip', 'transition_gate_budget_exhausted']` |

## Interpretation

- This is a MuJoCo-only repair probe layered on Stage3.7B.
- It tests whether contact-transition pauses reduce transient slip before changing the learned hand policy.
- Success is still judged by the Stage3 gentle-grasp hold criteria; full-episode transient slip is reported as a risk flag.
