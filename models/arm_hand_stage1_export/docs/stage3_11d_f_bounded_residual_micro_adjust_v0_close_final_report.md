# Stage3.11D-F Bounded Residual Micro-Adjust v0

Generated: `2026-06-12T14:45:29`

## Boundary

- MuJoCo-only bounded residual teacher/probe.
- Keeps the event/contact-gated controller; residual is small, slow-lift-only, and bounded.
- Uses simulated contact/tactile morphology and simulated motor force feedback from MuJoCo loads.
- Not demo-gallery promotion, full-action ACT/DP, hardware runtime, real camera, or real tactile integration.

## Inputs

- Selected center: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_11d_c_geometry_force_refine_selected_v0.json`
- Smoke seed/trials: `20260612` / `12`
- Final seed/trials: `20265612` / `50`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | reasons |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `close_s004_m020_q80_w120` | 10 / 12 | 12 | 10 | 10 | 12 | 48 | `{'success_event_contact_gated_true_pinch_release_ball': 10, 'lift_gate_failed': 2}` |
| 2 | `close_s006_m030_q80_w160` | 10 / 12 | 12 | 10 | 10 | 12 | 63 | `{'success_event_contact_gated_true_pinch_release_ball': 10, 'lift_gate_failed': 2}` |
| 3 | `close_s008_m032_q100_w160` | 10 / 12 | 12 | 10 | 10 | 12 | 64 | `{'success_event_contact_gated_true_pinch_release_ball': 10, 'lift_gate_failed': 2}` |
| 4 | `close_s006_m030_q80_w180_drop5` | 10 / 12 | 12 | 10 | 10 | 12 | 65 | `{'success_event_contact_gated_true_pinch_release_ball': 10, 'lift_gate_failed': 2}` |

## Final Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | reasons |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `close_s004_m020_q80_w120` | 43 / 50 | 49 | 44 | 43 | 50 | 120 | `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}` |
| 2 | `close_s006_m030_q80_w160` | 43 / 50 | 49 | 44 | 43 | 50 | 160 | `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}` |
| 3 | `close_s008_m032_q100_w160` | 43 / 50 | 49 | 44 | 43 | 50 | 160 | `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}` |
| 4 | `close_s006_m030_q80_w180_drop5` | 43 / 50 | 49 | 44 | 43 | 50 | 170 | `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}` |

## Selected Diagnostic Candidate

- Variant: `close_s004_m020_q80_w120`
- Final success: `43 / 50`
- Contact/lift/true-pinch/release: `49` / `44` / `43` / `50`
- Residual events total: `120`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}`

## Next

- If a residual variant beats the no-residual baseline on the same final seed, rerun it on the D-D capture seed and create residual teacher rows.
- If no residual variant improves robustness, keep D-E shadow as diagnostic and return to geometry/material/phase-timing repair.
