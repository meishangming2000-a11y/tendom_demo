# Stage3.7D Contact Transition Recovery V0 Eval Report

Generated: 2026-06-07T17:41:06

This is a MuJoCo-only virtual-camera + synthetic tactile/slip evaluation.

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate_and_recovery_microphase`
- Episodes: `50`
- Success count: `50 / 50`
- Terminal reasons: `{'success_gentle_grasp_hold': 50}`
- Risk flags: `{'early_contact_in_approach': 50, 'transient_or_hold_slip': 45, 'recovery_budget_exhausted': 26}`
- Gate release reasons: `{'stable_window_met': 50}`
- Top-slip phases: `{'slow_lift': 26, 'contact_settle': 11, 'gentle_close_thumb': 11, 'gentle_close_fingers': 1, 'approach': 1}`
- Recovery steps by phase: `{'slow_lift': 6739}`
- Recovery budget exhaustion: `{'slow_lift': 1185}`
- Mean final lift: `0.103461 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.505`
- Max transient slip: `1.000`
- Max hold slip: `0.285`
- Max crush risk: `0.117`
- Max penetration: `0.002335 m`
- Mean recovery steps: `134.8`
- Mean recovery events: `31.6`

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
| 0 | center_nominal | PASS | 0.450 | slow_lift | 200 | `{'slow_lift': 30}` | 2000 | 0.09956 | 1.000 | 0.165 | 0.090 | 0.001805 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 1 | left_low_nominal | PASS | 0.298 | slow_lift | 10 | `{}` | 2000 | 0.10293 | 1.000 | 0.169 | 0.084 | 0.001677 | `['early_contact_in_approach']` |
| 2 | right_high_nominal | PASS | 0.438 | contact_settle | 15 | `{}` | 2000 | 0.09364 | 1.000 | 0.199 | 0.072 | 0.001439 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 1.000 | gentle_close_thumb | 167 | `{}` | 2000 | 0.10990 | 1.000 | 0.268 | 0.103 | 0.002052 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | 0.539 | slow_lift | 200 | `{'slow_lift': 84}` | 2000 | 0.10150 | 1.000 | 0.156 | 0.087 | 0.001745 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 5 | front_small_lift | PASS | 0.420 | contact_settle | 0 | `{}` | 2000 | 0.08445 | 1.000 | 0.140 | 0.085 | 0.001707 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.403 | slow_lift | 200 | `{'slow_lift': 63}` | 2000 | 0.11970 | 1.000 | 0.175 | 0.105 | 0.002101 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 7 | lifted_center | PASS | 0.674 | contact_settle | 10 | `{}` | 2000 | 0.10060 | 1.000 | 0.181 | 0.089 | 0.001776 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | 0.545 | gentle_close_thumb | 200 | `{'slow_lift': 46}` | 2000 | 0.11186 | 1.000 | 0.203 | 0.102 | 0.002048 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 9 | wide_diag | PASS | 0.436 | slow_lift | 200 | `{'slow_lift': 46}` | 2000 | 0.11385 | 1.000 | 0.130 | 0.110 | 0.002203 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 10 | center_nominal | PASS | 0.441 | slow_lift | 200 | `{'slow_lift': 43}` | 2000 | 0.09745 | 1.000 | 0.182 | 0.084 | 0.001685 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 11 | left_low_nominal | PASS | 0.353 | slow_lift | 141 | `{}` | 2000 | 0.10267 | 1.000 | 0.260 | 0.092 | 0.001833 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 12 | right_high_nominal | PASS | 0.342 | slow_lift | 16 | `{}` | 2000 | 0.09462 | 1.000 | 0.193 | 0.067 | 0.001339 | `['early_contact_in_approach']` |
| 13 | left_high_zplus | PASS | 0.828 | contact_settle | 200 | `{'slow_lift': 42}` | 2000 | 0.10892 | 1.000 | 0.170 | 0.104 | 0.002086 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 14 | right_low_zminus | PASS | 0.509 | slow_lift | 200 | `{'slow_lift': 40}` | 2000 | 0.10041 | 1.000 | 0.285 | 0.090 | 0.001797 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 15 | front_small_lift | PASS | 0.373 | slow_lift | 40 | `{}` | 2000 | 0.08486 | 1.000 | 0.208 | 0.116 | 0.002324 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 16 | back_large_lift | PASS | 0.495 | slow_lift | 200 | `{'slow_lift': 73}` | 2000 | 0.11601 | 1.000 | 0.178 | 0.083 | 0.001651 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 17 | lifted_center | PASS | 0.598 | contact_settle | 198 | `{}` | 2000 | 0.10078 | 1.000 | 0.179 | 0.097 | 0.001944 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 18 | lifted_diag | PASS | 0.572 | contact_settle | 200 | `{'slow_lift': 45}` | 2000 | 0.11180 | 1.000 | 0.204 | 0.106 | 0.002118 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 19 | wide_diag | PASS | 0.886 | gentle_close_thumb | 200 | `{'slow_lift': 65}` | 2000 | 0.11009 | 1.000 | 0.194 | 0.084 | 0.001672 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 20 | center_nominal | PASS | 0.337 | slow_lift | 77 | `{}` | 2000 | 0.10136 | 1.000 | 0.155 | 0.093 | 0.001870 | `['early_contact_in_approach']` |
| 21 | left_low_nominal | PASS | 0.437 | slow_lift | 186 | `{}` | 2000 | 0.10336 | 1.000 | 0.055 | 0.079 | 0.001575 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 22 | right_high_nominal | PASS | 0.430 | slow_lift | 62 | `{}` | 2000 | 0.09574 | 1.000 | 0.168 | 0.074 | 0.001487 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 23 | left_high_zplus | PASS | 0.352 | slow_lift | 179 | `{}` | 2000 | 0.10862 | 1.000 | 0.205 | 0.104 | 0.002089 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 24 | right_low_zminus | PASS | 0.384 | slow_lift | 27 | `{}` | 2000 | 0.10041 | 1.000 | 0.147 | 0.094 | 0.001881 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 25 | front_small_lift | PASS | 0.379 | contact_settle | 0 | `{}` | 2000 | 0.08530 | 1.000 | 0.147 | 0.102 | 0.002044 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 26 | back_large_lift | PASS | 0.342 | slow_lift | 116 | `{}` | 2000 | 0.11983 | 1.000 | 0.269 | 0.110 | 0.002208 | `['early_contact_in_approach']` |
| 27 | lifted_center | PASS | 0.626 | gentle_close_thumb | 200 | `{'slow_lift': 16}` | 2000 | 0.09962 | 1.000 | 0.156 | 0.107 | 0.002132 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 28 | lifted_diag | PASS | 0.750 | gentle_close_thumb | 200 | `{'slow_lift': 44}` | 2000 | 0.11139 | 1.000 | 0.248 | 0.107 | 0.002141 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 29 | wide_diag | PASS | 0.794 | gentle_close_thumb | 200 | `{'slow_lift': 52}` | 2000 | 0.11120 | 1.000 | 0.165 | 0.105 | 0.002098 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 30 | center_nominal | PASS | 0.393 | slow_lift | 200 | `{'slow_lift': 30}` | 2000 | 0.10068 | 1.000 | 0.128 | 0.097 | 0.001934 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 31 | left_low_nominal | PASS | 0.319 | slow_lift | 18 | `{}` | 2000 | 0.10286 | 1.000 | 0.192 | 0.083 | 0.001661 | `['early_contact_in_approach']` |
| 32 | right_high_nominal | PASS | 0.375 | contact_settle | 11 | `{}` | 2000 | 0.09502 | 1.000 | 0.182 | 0.072 | 0.001441 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 33 | left_high_zplus | PASS | 0.371 | slow_lift | 98 | `{}` | 2000 | 0.10934 | 1.000 | 0.159 | 0.116 | 0.002311 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 34 | right_low_zminus | PASS | 0.503 | slow_lift | 200 | `{'slow_lift': 41}` | 2000 | 0.09827 | 1.000 | 0.284 | 0.088 | 0.001763 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 35 | front_small_lift | PASS | 0.358 | contact_settle | 3 | `{}` | 2000 | 0.08500 | 1.000 | 0.148 | 0.079 | 0.001585 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 36 | back_large_lift | PASS | 0.402 | slow_lift | 200 | `{'slow_lift': 64}` | 2000 | 0.11986 | 1.000 | 0.180 | 0.106 | 0.002113 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 37 | lifted_center | PASS | 0.709 | gentle_close_thumb | 133 | `{}` | 2000 | 0.10023 | 1.000 | 0.204 | 0.098 | 0.001954 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 38 | lifted_diag | PASS | 0.596 | gentle_close_thumb | 200 | `{'slow_lift': 40}` | 2000 | 0.11147 | 1.000 | 0.185 | 0.104 | 0.002080 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 39 | wide_diag | PASS | 0.447 | slow_lift | 200 | `{'slow_lift': 41}` | 2000 | 0.11364 | 1.000 | 0.146 | 0.117 | 0.002335 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 40 | center_nominal | PASS | 0.429 | slow_lift | 200 | `{'slow_lift': 45}` | 2000 | 0.09936 | 1.000 | 0.128 | 0.099 | 0.001986 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 41 | left_low_nominal | PASS | 0.401 | gentle_close_fingers | 17 | `{}` | 2000 | 0.10257 | 1.000 | 0.183 | 0.100 | 0.002009 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 42 | right_high_nominal | PASS | 0.390 | contact_settle | 15 | `{}` | 2000 | 0.09391 | 1.000 | 0.191 | 0.070 | 0.001395 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 43 | left_high_zplus | PASS | 1.000 | gentle_close_thumb | 200 | `{'slow_lift': 46}` | 2000 | 0.10757 | 1.000 | 0.142 | 0.103 | 0.002064 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 44 | right_low_zminus | PASS | 0.447 | slow_lift | 200 | `{'slow_lift': 56}` | 2000 | 0.10062 | 1.000 | 0.149 | 0.084 | 0.001681 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 45 | front_small_lift | PASS | 0.565 | gentle_close_thumb | 0 | `{}` | 2000 | 0.08401 | 1.000 | 0.141 | 0.087 | 0.001737 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 46 | back_large_lift | PASS | 0.431 | approach | 200 | `{'slow_lift': 44}` | 2000 | 0.12029 | 1.000 | 0.177 | 0.102 | 0.002038 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 47 | lifted_center | PASS | 0.675 | contact_settle | 200 | `{'slow_lift': 16}` | 2000 | 0.10077 | 1.000 | 0.174 | 0.099 | 0.001974 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 48 | lifted_diag | PASS | 0.590 | gentle_close_thumb | 200 | `{'slow_lift': 30}` | 2000 | 0.11141 | 1.000 | 0.157 | 0.101 | 0.002025 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 49 | wide_diag | PASS | 0.393 | slow_lift | 200 | `{'slow_lift': 43}` | 2000 | 0.11371 | 1.000 | 0.162 | 0.115 | 0.002295 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |

## Interpretation

- This probe keeps the Stage3.6 learned hand policy and Stage3.7B lift gate.
- It differs from Stage3.7C by commanding a slightly lower lift progress during recovery, not just repeating the same progress.
- Success still requires the normal Stage3 gentle-grasp hold criteria. Full-episode transient slip remains a reported risk flag.
