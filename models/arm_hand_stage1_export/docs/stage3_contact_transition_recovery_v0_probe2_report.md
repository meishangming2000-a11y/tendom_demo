# Stage3.7D Contact Transition Recovery V0 Eval Report

Generated: 2026-06-05T18:10:28

This is a MuJoCo-only virtual-camera + synthetic tactile/slip evaluation.

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate_and_recovery_microphase`
- Episodes: `2`
- Success count: `2 / 2`
- Terminal reasons: `{'success_gentle_grasp_hold': 2}`
- Risk flags: `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 2, 'recovery_budget_exhausted': 1}`
- Gate release reasons: `{'stable_window_met': 2}`
- Top-slip phases: `{'slow_lift': 2}`
- Recovery steps by phase: `{'slow_lift': 269}`
- Recovery budget exhaustion: `{'slow_lift': 431}`
- Mean final lift: `0.100732 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.489`
- Max transient slip: `0.553`
- Max hold slip: `0.261`
- Max crush risk: `0.109`
- Max penetration: `0.002188 m`
- Mean recovery steps: `134.5`
- Mean recovery events: `219.0`

## Recovery Parameters

- recovery phases: `['slow_lift']`
- recovery slip threshold: `0.28`
- recovery crush threshold: `0.35`
- recovery penetration threshold: `0.004`
- recovery progress drop: `0.02`
- recovery stable window steps: `20`
- max recovery steps per phase: `150`
- contact-settle gate: `2000 / 2000`

## Episode Results

| ep | trial | status | max slip | top phase | recovery steps | recovery budget | settle | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | 0.426 | slow_lift | 119 | `{}` | 2000 | 0.09931 | 1.000 | 0.149 | 0.109 | 0.002188 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | 0.553 | slow_lift | 150 | `{'slow_lift': 431}` | 2000 | 0.10216 | 1.000 | 0.261 | 0.089 | 0.001781 | `['early_contact_in_approach', 'transient_or_hold_slip', 'recovery_budget_exhausted']` |

## Interpretation

- This probe keeps the Stage3.6 learned hand policy and Stage3.7B lift gate.
- It differs from Stage3.7C by commanding a slightly lower lift progress during recovery, not just repeating the same progress.
- Success still requires the normal Stage3 gentle-grasp hold criteria. Full-episode transient slip remains a reported risk flag.
