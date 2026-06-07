# Stage3.7D Contact Transition Recovery V0 Eval Report

Generated: 2026-06-05T18:36:30

This is a MuJoCo-only virtual-camera + synthetic tactile/slip evaluation.

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate_and_recovery_microphase`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10, 'recovery_budget_exhausted': 5}`
- Gate release reasons: `{'stable_window_met': 10}`
- Top-slip phases: `{'slow_lift': 5, 'gentle_close_thumb': 2, 'contact_settle': 3}`
- Recovery steps by phase: `{'slow_lift': 1300}`
- Recovery budget exhaustion: `{'slow_lift': 206}`
- Mean final lift: `0.103116 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.555`
- Max transient slip: `0.941`
- Max hold slip: `0.254`
- Max crush risk: `0.111`
- Max penetration: `0.002223 m`
- Mean recovery steps: `130.0`
- Mean recovery events: `30.8`

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
| 0 | center_nominal | PASS | 0.420 | slow_lift | 200 | `{'slow_lift': 29}` | 2000 | 0.09933 | 1.000 | 0.115 | 0.109 | 0.002188 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 1 | left_low_nominal | PASS | 0.376 | slow_lift | 91 | `{}` | 2000 | 0.10215 | 1.000 | 0.254 | 0.089 | 0.001781 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | 0.412 | slow_lift | 57 | `{}` | 2000 | 0.09423 | 1.000 | 0.186 | 0.079 | 0.001582 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 0.789 | gentle_close_thumb | 200 | `{'slow_lift': 27}` | 2000 | 0.10941 | 1.000 | 0.159 | 0.106 | 0.002122 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 4 | right_low_zminus | PASS | 0.437 | slow_lift | 136 | `{}` | 2000 | 0.10249 | 1.000 | 0.171 | 0.090 | 0.001798 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | 0.361 | contact_settle | 5 | `{}` | 2000 | 0.08559 | 1.000 | 0.142 | 0.083 | 0.001667 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | 0.452 | slow_lift | 200 | `{'slow_lift': 59}` | 2000 | 0.11533 | 1.000 | 0.173 | 0.111 | 0.002212 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 7 | lifted_center | PASS | 0.769 | contact_settle | 11 | `{}` | 2000 | 0.09999 | 1.000 | 0.188 | 0.096 | 0.001923 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | 0.592 | contact_settle | 200 | `{'slow_lift': 34}` | 2000 | 0.11165 | 1.000 | 0.147 | 0.101 | 0.002024 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 9 | wide_diag | PASS | 0.941 | gentle_close_thumb | 200 | `{'slow_lift': 57}` | 2000 | 0.11099 | 1.000 | 0.161 | 0.111 | 0.002223 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |

## Interpretation

- This probe keeps the Stage3.6 learned hand policy and Stage3.7B lift gate.
- It differs from Stage3.7C by commanding a slightly lower lift progress during recovery, not just repeating the same progress.
- Success still requires the normal Stage3 gentle-grasp hold criteria. Full-episode transient slip remains a reported risk flag.
