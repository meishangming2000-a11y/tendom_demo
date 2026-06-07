# Stage3.4 Tactile/Slip Sensor V0

Generated: 2026-06-04T16:19:15

- Status: `PASS`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Trials: `3`

## Trial Summary

| trial | status | first contact | max slip | max crush | max persistence | final lift m | final grip stable | risk flags |
|---|---|---|---:|---:|---:|---:|---:|---|
| center_nominal | PASS | `approach` | 1.000 | 0.118 | 1559 | 0.10004 | 1 | `['early_contact_in_approach', 'transient_slip_above_hold_gate']` |
| left_low_nominal | PASS | `approach` | 1.000 | 0.097 | 1560 | 0.10154 | 1 | `['early_contact_in_approach', 'transient_slip_above_hold_gate']` |
| right_high_nominal | PASS | `approach` | 1.000 | 0.092 | 1558 | 0.09614 | 1 | `['early_contact_in_approach', 'transient_slip_above_hold_gate']` |

## Interpretation

- The tactile/slip sensor is MuJoCo contact-derived and policy-visible; it does not use real tactile hardware.
- It separates pre-contact vision guidance from post-contact stability checks: contact acquisition, persistence, slip score, and crush risk.
- Risk flags are controller/expert tuning signals, not sensor schema failures.
