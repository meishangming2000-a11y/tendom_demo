# Stage3.7B Tactile Phase Gate V0 Eval Report

Generated: 2026-06-05T05:59:11

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate`
- Episodes: `30`
- Success count: `30 / 30`
- Terminal reasons: `{'success_gentle_grasp_hold': 30}`
- Risk flags: `{'early_contact_in_approach': 30, 'transient_or_hold_slip': 30}`
- Gate release reasons: `{'stable_window_met': 30}`
- Mean final lift: `0.103031 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.625`
- Max transient slip: `1.000`
- Mean pre-lift max slip: `0.484`
- Mean post-lift max slip: `0.476`
- Max hold slip: `0.318`
- Max crush risk: `0.127`
- Max penetration: `0.002542 m`
- Mean contact-settle steps: `2000.0`
- Mean gate stable window at release: `1873.6`

## Gate Parameters

- min contact-settle steps: `2000`
- max contact-settle steps: `2000`
- stable window steps: `300`
- gate slip threshold: `0.18`
- gate crush threshold: `0.35`
- gate penetration threshold: `0.004`

## Episode Results

| ep | trial | status | gate reason | settle | gate window | max slip | pre-lift slip | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | stable_window_met | 2000 | 1398 | 0.395 | 0.076 | 0.10058 | 1.000 | 0.166 | 0.120 | 0.002409 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | stable_window_met | 2000 | 2000 | 0.434 | 0.003 | 0.10253 | 1.000 | 0.195 | 0.077 | 0.001548 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | stable_window_met | 2000 | 2000 | 1.000 | 0.026 | 0.09532 | 1.000 | 0.236 | 0.115 | 0.002294 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | stable_window_met | 2000 | 1800 | 0.824 | 0.015 | 0.10844 | 1.000 | 0.160 | 0.100 | 0.001996 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | stable_window_met | 2000 | 1934 | 0.548 | 0.032 | 0.10174 | 1.000 | 0.174 | 0.081 | 0.001611 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | stable_window_met | 2000 | 1744 | 0.430 | 0.019 | 0.08608 | 1.000 | 0.150 | 0.080 | 0.001605 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | stable_window_met | 2000 | 2000 | 0.397 | 0.002 | 0.11886 | 1.000 | 0.186 | 0.127 | 0.002542 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | stable_window_met | 2000 | 1931 | 0.561 | 0.002 | 0.10049 | 1.000 | 0.188 | 0.102 | 0.002045 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | stable_window_met | 2000 | 1857 | 0.542 | 0.003 | 0.11229 | 1.000 | 0.201 | 0.099 | 0.001980 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 9 | wide_diag | PASS | stable_window_met | 2000 | 1972 | 0.785 | 0.011 | 0.11280 | 1.000 | 0.173 | 0.089 | 0.001778 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 10 | center_nominal | PASS | stable_window_met | 2000 | 1937 | 0.500 | 0.031 | 0.10071 | 1.000 | 0.154 | 0.091 | 0.001820 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 11 | left_low_nominal | PASS | stable_window_met | 2000 | 2000 | 0.351 | 0.001 | 0.10328 | 1.000 | 0.107 | 0.083 | 0.001652 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 12 | right_high_nominal | PASS | stable_window_met | 2000 | 1575 | 0.474 | 0.052 | 0.09383 | 1.000 | 0.202 | 0.109 | 0.002177 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 13 | left_high_zplus | PASS | stable_window_met | 2000 | 1821 | 0.803 | 0.004 | 0.10853 | 1.000 | 0.164 | 0.117 | 0.002342 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 14 | right_low_zminus | PASS | stable_window_met | 2000 | 1871 | 0.504 | 0.030 | 0.10051 | 1.000 | 0.149 | 0.094 | 0.001889 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 15 | front_small_lift | PASS | stable_window_met | 2000 | 2000 | 0.898 | 0.021 | 0.07965 | 1.000 | 0.276 | 0.111 | 0.002228 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 16 | back_large_lift | PASS | stable_window_met | 2000 | 2000 | 0.802 | 0.040 | 0.11997 | 1.000 | 0.267 | 0.085 | 0.001695 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 17 | lifted_center | PASS | stable_window_met | 2000 | 1964 | 0.997 | 0.002 | 0.10010 | 1.000 | 0.198 | 0.108 | 0.002166 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 18 | lifted_diag | PASS | stable_window_met | 2000 | 1869 | 0.463 | 0.003 | 0.11205 | 1.000 | 0.208 | 0.100 | 0.002002 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 19 | wide_diag | PASS | stable_window_met | 2000 | 1840 | 1.000 | 0.014 | 0.11363 | 1.000 | 0.203 | 0.103 | 0.002054 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 20 | center_nominal | PASS | stable_window_met | 2000 | 1737 | 0.480 | 0.018 | 0.09927 | 1.000 | 0.149 | 0.093 | 0.001854 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 21 | left_low_nominal | PASS | stable_window_met | 2000 | 2000 | 0.453 | 0.001 | 0.10219 | 1.000 | 0.218 | 0.095 | 0.001894 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 22 | right_high_nominal | PASS | stable_window_met | 2000 | 1766 | 0.687 | 0.043 | 0.09373 | 1.000 | 0.168 | 0.093 | 0.001864 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 23 | left_high_zplus | PASS | stable_window_met | 2000 | 1796 | 0.781 | 0.014 | 0.10857 | 1.000 | 0.154 | 0.107 | 0.002143 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 24 | right_low_zminus | PASS | stable_window_met | 2000 | 1876 | 0.505 | 0.029 | 0.10058 | 1.000 | 0.146 | 0.098 | 0.001968 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 25 | front_small_lift | PASS | stable_window_met | 2000 | 1758 | 0.402 | 0.025 | 0.08415 | 1.000 | 0.145 | 0.079 | 0.001583 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 26 | back_large_lift | PASS | stable_window_met | 2000 | 2000 | 0.439 | 0.024 | 0.11848 | 1.000 | 0.186 | 0.127 | 0.002541 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 27 | lifted_center | PASS | stable_window_met | 2000 | 2000 | 1.000 | 0.012 | 0.09050 | 1.000 | 0.318 | 0.084 | 0.001689 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 28 | lifted_diag | PASS | stable_window_met | 2000 | 1913 | 0.489 | 0.002 | 0.11199 | 1.000 | 0.178 | 0.097 | 0.001948 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 29 | wide_diag | PASS | stable_window_met | 2000 | 1849 | 0.804 | 0.017 | 0.11009 | 1.000 | 0.165 | 0.101 | 0.002024 | `['early_contact_in_approach', 'transient_or_hold_slip']` |

## Interpretation

- This is a MuJoCo-only virtual-camera + synthetic-tactile evaluation.
- It preserves the Stage3.6 learned hand policy and adds only lift-permission timing.
- It intentionally does not produce hand-residual training labels.
- `transient_or_hold_slip` is reported as a risk flag even when hold slip remains below the success threshold.
- Early approach contact remains a separate approach-gating problem unless the arm/wrist path is changed.
