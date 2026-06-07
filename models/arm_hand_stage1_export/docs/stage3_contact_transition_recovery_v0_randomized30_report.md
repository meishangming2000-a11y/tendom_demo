# Stage3.7D Contact Transition Recovery V0 Eval Report

Generated: 2026-06-05T18:32:49

This is a MuJoCo-only virtual-camera + synthetic tactile/slip evaluation.

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate_and_recovery_microphase`
- Episodes: `30`
- Success count: `30 / 30`
- Terminal reasons: `{'success_gentle_grasp_hold': 30}`
- Risk flags: `{'early_contact_in_approach': 30, 'transient_or_hold_slip': 28, 'recovery_budget_exhausted': 15}`
- Gate release reasons: `{'stable_window_met': 30}`
- Top-slip phases: `{'contact_settle': 9, 'slow_lift': 13, 'gentle_close_thumb': 7, 'approach': 1}`
- Recovery steps by phase: `{'slow_lift': 3758}`
- Recovery budget exhaustion: `{'slow_lift': 922}`
- Mean final lift: `0.103057 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.570`
- Max transient slip: `1.000`
- Max hold slip: `0.315`
- Max crush risk: `0.127`
- Max penetration: `0.002542 m`
- Mean recovery steps: `125.3`
- Mean recovery events: `41.8`

## Recovery Parameters

- recovery phases: `['slow_lift']`
- recovery slip threshold: `0.29`
- recovery crush threshold: `0.35`
- recovery penetration threshold: `0.004`
- recovery progress drop: `0.01`
- recovery stable window steps: `0`
- max recovery steps per phase: `200`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | recovery steps | recovery budget | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.395 | contact_settle | 6 | `{}` | 2000 | 0.10058 | 1.000 | 0.167 | 0.120 | 0.002409 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | 0.324 | slow_lift | 29 | `{}` | 2000 | 0.10254 | 1.000 | 0.194 | 0.077 | 0.001548 | `['early_contact_in_approach']` |
| 2 | right_high_nominal | PASS | 0.917 | slow_lift | 82 | `{}` | 2000 | 0.09528 | 1.000 | 0.235 | 0.115 | 0.002294 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 0.824 | gentle_close_thumb | 200 | `{'slow_lift': 25}` | 2000 | 0.10854 | 1.000 | 0.160 | 0.100 | 0.001996 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 4 | right_low_zminus | PASS | 0.477 | slow_lift | 74 | `{}` | 2000 | 0.10173 | 1.000 | 0.179 | 0.081 | 0.001611 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | 0.430 | contact_settle | 5 | `{}` | 2000 | 0.08608 | 1.000 | 0.151 | 0.080 | 0.001605 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.443 | slow_lift | 200 | `{'slow_lift': 48}` | 2000 | 0.11884 | 1.000 | 0.189 | 0.127 | 0.002542 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 7 | lifted_center | PASS | 0.561 | gentle_close_thumb | 5 | `{}` | 2000 | 0.10049 | 1.000 | 0.189 | 0.102 | 0.002045 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | 0.542 | contact_settle | 200 | `{'slow_lift': 37}` | 2000 | 0.11232 | 1.000 | 0.146 | 0.099 | 0.001980 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 9 | wide_diag | PASS | 0.785 | gentle_close_thumb | 200 | `{'slow_lift': 47}` | 2000 | 0.11276 | 1.000 | 0.145 | 0.089 | 0.001778 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 10 | center_nominal | PASS | 0.417 | slow_lift | 200 | `{'slow_lift': 18}` | 2000 | 0.10068 | 1.000 | 0.133 | 0.091 | 0.001820 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 11 | left_low_nominal | PASS | 0.456 | slow_lift | 200 | `{'slow_lift': 30}` | 2000 | 0.10330 | 1.000 | 0.085 | 0.083 | 0.001652 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 12 | right_high_nominal | PASS | 0.433 | contact_settle | 25 | `{}` | 2000 | 0.09383 | 1.000 | 0.202 | 0.109 | 0.002177 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 13 | left_high_zplus | PASS | 0.803 | contact_settle | 172 | `{}` | 2000 | 0.10853 | 1.000 | 0.183 | 0.117 | 0.002342 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 14 | right_low_zminus | PASS | 0.375 | slow_lift | 39 | `{}` | 2000 | 0.10050 | 1.000 | 0.153 | 0.094 | 0.001889 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 15 | front_small_lift | PASS | 0.534 | slow_lift | 200 | `{'slow_lift': 41}` | 2000 | 0.08016 | 1.000 | 0.262 | 0.111 | 0.002228 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 16 | back_large_lift | PASS | 0.470 | slow_lift | 189 | `{}` | 2000 | 0.12008 | 1.000 | 0.272 | 0.085 | 0.001695 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 17 | lifted_center | PASS | 0.997 | gentle_close_thumb | 13 | `{}` | 2000 | 0.10010 | 1.000 | 0.200 | 0.108 | 0.002166 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 18 | lifted_diag | PASS | 0.463 | contact_settle | 200 | `{'slow_lift': 40}` | 2000 | 0.11208 | 1.000 | 0.158 | 0.100 | 0.002002 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 19 | wide_diag | PASS | 1.000 | gentle_close_thumb | 65 | `{}` | 2000 | 0.11367 | 1.000 | 0.204 | 0.103 | 0.002054 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 20 | center_nominal | PASS | 0.484 | slow_lift | 200 | `{'slow_lift': 41}` | 2000 | 0.09932 | 1.000 | 0.156 | 0.093 | 0.001854 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 21 | left_low_nominal | PASS | 0.342 | slow_lift | 21 | `{}` | 2000 | 0.10219 | 1.000 | 0.217 | 0.095 | 0.001894 | `['early_contact_in_approach']` |
| 22 | right_high_nominal | PASS | 0.687 | contact_settle | 200 | `{'slow_lift': 39}` | 2000 | 0.09369 | 1.000 | 0.156 | 0.093 | 0.001864 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 23 | left_high_zplus | PASS | 0.781 | gentle_close_thumb | 200 | `{'slow_lift': 47}` | 2000 | 0.10865 | 1.000 | 0.143 | 0.107 | 0.002143 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 24 | right_low_zminus | PASS | 0.472 | slow_lift | 200 | `{'slow_lift': 39}` | 2000 | 0.10052 | 1.000 | 0.251 | 0.098 | 0.001968 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 25 | front_small_lift | PASS | 0.402 | contact_settle | 13 | `{}` | 2000 | 0.08415 | 1.000 | 0.147 | 0.079 | 0.001583 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 26 | back_large_lift | PASS | 0.389 | slow_lift | 20 | `{}` | 2000 | 0.11849 | 1.000 | 0.186 | 0.127 | 0.002541 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 27 | lifted_center | PASS | 0.600 | approach | 200 | `{'slow_lift': 405}` | 2000 | 0.09049 | 1.000 | 0.315 | 0.084 | 0.001689 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 28 | lifted_diag | PASS | 0.489 | contact_settle | 200 | `{'slow_lift': 35}` | 2000 | 0.11205 | 1.000 | 0.141 | 0.097 | 0.001948 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 29 | wide_diag | PASS | 0.804 | gentle_close_thumb | 200 | `{'slow_lift': 30}` | 2000 | 0.11010 | 1.000 | 0.166 | 0.101 | 0.002024 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |

## Interpretation

- This probe keeps the Stage3.6 learned hand policy and Stage3.7B lift gate.
- It differs from Stage3.7C by commanding a slightly lower lift progress during recovery, not just repeating the same progress.
- Success still requires the normal Stage3 gentle-grasp hold criteria. Full-episode transient slip remains a reported risk flag.
