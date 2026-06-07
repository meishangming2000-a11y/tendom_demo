# Stage3.7D Contact Transition Recovery V0 Eval Report

Generated: 2026-06-05T18:16:36

This is a MuJoCo-only virtual-camera + synthetic tactile/slip evaluation.

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate_and_recovery_microphase`
- Episodes: `5`
- Success count: `5 / 5`
- Terminal reasons: `{'success_gentle_grasp_hold': 5}`
- Risk flags: `{'early_contact_in_approach': 5, 'transient_or_hold_slip': 5, 'recovery_budget_exhausted': 1}`
- Gate release reasons: `{'stable_window_met': 5}`
- Top-slip phases: `{'slow_lift': 4, 'gentle_close_thumb': 1}`
- Recovery steps by phase: `{'slow_lift': 601}`
- Recovery budget exhaustion: `{'slow_lift': 37}`
- Mean final lift: `0.101521 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.490`
- Max transient slip: `0.789`
- Max hold slip: `0.260`
- Max crush risk: `0.109`
- Max penetration: `0.002188 m`
- Mean recovery steps: `120.2`
- Mean recovery events: `20.0`

## Recovery Parameters

- recovery phases: `['slow_lift']`
- recovery slip threshold: `0.3`
- recovery crush threshold: `0.35`
- recovery penetration threshold: `0.004`
- recovery progress drop: `0.01`
- recovery stable window steps: `0`
- max recovery steps per phase: `200`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | recovery steps | recovery budget | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.436 | slow_lift | 179 | `{}` | 2000 | 0.09932 | 1.000 | 0.159 | 0.109 | 0.002188 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | 0.376 | slow_lift | 72 | `{}` | 2000 | 0.10215 | 1.000 | 0.260 | 0.089 | 0.001781 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | 0.411 | slow_lift | 52 | `{}` | 2000 | 0.09423 | 1.000 | 0.186 | 0.079 | 0.001582 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | 0.789 | gentle_close_thumb | 200 | `{'slow_lift': 37}` | 2000 | 0.10941 | 1.000 | 0.143 | 0.106 | 0.002122 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |
| 4 | right_low_zminus | PASS | 0.437 | slow_lift | 98 | `{}` | 2000 | 0.10250 | 1.000 | 0.161 | 0.090 | 0.001798 | `['early_contact_in_approach', 'transient_or_hold_slip']` |

## Interpretation

- This probe keeps the Stage3.6 learned hand policy and Stage3.7B lift gate.
- It differs from Stage3.7C by commanding a slightly lower lift progress during recovery, not just repeating the same progress.
- Success still requires the normal Stage3 gentle-grasp hold criteria. Full-episode transient slip remains a reported risk flag.
