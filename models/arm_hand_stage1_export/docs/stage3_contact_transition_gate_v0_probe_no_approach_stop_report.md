# Stage3.7C Contact Transition Gate V0 Eval Report

Generated: 2026-06-05T09:20:29

- Status: **PARTIAL**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_and_transition_gates`
- Episodes: `10`
- Success count: `9 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 9, 'hold_slip_score_high': 1}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10, 'hold_slip_high': 1}`
- Gate release reasons: `{'stable_window_met': 10}`
- Top-slip phases: `{'contact_settle': 3, 'slow_lift': 4, 'gentle_close_thumb': 3}`
- Transition holds by phase: `{'slow_lift': 2078, 'gentle_close_thumb': 59}`
- Transition budget exhaustion: `{}`
- Mean final lift: `0.103147 m`
- Mean hold stable fraction: `0.999`
- Mean max transient slip: `0.584`
- Max transient slip: `0.986`
- Max hold slip: `0.373`
- Max crush risk: `0.111`
- Max penetration: `0.002223 m`
- Mean transition hold steps: `213.7`
- Mean approach contact-stop events: `0.0`

## Gate Parameters

- stop approach on contact: `False`
- approach contact stop error: `0.014`
- transition gate phases: `['gentle_close_thumb', 'slow_lift']`
- transition slip threshold: `0.28`
- transition crush threshold: `0.35`
- transition penetration threshold: `0.004`
- max transition hold steps per phase: `500`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | transition holds | approach stop | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.414 | contact_settle | 325 | 0 | 2000 | 0.09937 | 1.000 | 0.263 | 0.109 | 0.002188 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | 0.442 | slow_lift | 370 | 0 | 2000 | 0.10218 | 1.000 | 0.310 | 0.089 | 0.001781 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | 0.402 | contact_settle | 56 | 0 | 2000 | 0.09423 | 1.000 | 0.185 | 0.079 | 0.001582 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 0.986 | gentle_close_thumb | 316 | 0 | 2000 | 0.10950 | 1.000 | 0.259 | 0.106 | 0.002122 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | 0.457 | slow_lift | 44 | 0 | 2000 | 0.10250 | 1.000 | 0.163 | 0.090 | 0.001798 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | 0.389 | slow_lift | 213 | 0 | 2000 | 0.08561 | 1.000 | 0.277 | 0.083 | 0.001667 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.440 | slow_lift | 43 | 0 | 2000 | 0.11541 | 1.000 | 0.155 | 0.111 | 0.002212 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | 0.769 | contact_settle | 40 | 0 | 2000 | 0.09999 | 1.000 | 0.186 | 0.096 | 0.001923 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | 0.598 | gentle_close_thumb | 335 | 0 | 2000 | 0.11168 | 1.000 | 0.287 | 0.101 | 0.002024 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 9 | wide_diag | FAIL | 0.941 | gentle_close_thumb | 395 | 0 | 2000 | 0.11099 | 0.989 | 0.373 | 0.111 | 0.002223 | `['early_contact_in_approach', 'transient_or_hold_slip', 'hold_slip_high']` |

## Interpretation

- This is a MuJoCo-only repair probe layered on Stage3.7B.
- It tests whether contact-transition pauses reduce transient slip before changing the learned hand policy.
- Success is still judged by the Stage3 gentle-grasp hold criteria; full-episode transient slip is reported as a risk flag.
