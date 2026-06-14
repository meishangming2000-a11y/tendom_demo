# Stage3.11D-F Bounded Residual Micro-Adjust v0

Generated: `2026-06-12T15:00:06`

## Boundary

- MuJoCo-only bounded residual teacher/probe.
- Keeps the event/contact-gated controller; residual is small, slow-lift-only, and bounded.
- Uses simulated contact/tactile morphology and simulated motor force feedback from MuJoCo loads.
- Not demo-gallery promotion, full-action ACT/DP, hardware runtime, real camera, or real tactile integration.

## Inputs

- Selected center: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_11d_c_geometry_force_refine_selected_v0.json`
- Smoke seed/trials: `20260612` / `4`
- Final seed/trials: `20260612` / `50`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | reasons |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `prelift_xneg_close_s0004_c004_m0012_steps60` | 4 / 4 | 4 | 4 | 4 | 4 | 0 | `{'success_event_contact_gated_true_pinch_release_ball': 4}` |
| 2 | `prelift_xneg_s0006_m0012_steps60` | 4 / 4 | 4 | 4 | 4 | 4 | 0 | `{'success_event_contact_gated_true_pinch_release_ball': 4}` |
| 3 | `baseline_off` | 4 / 4 | 4 | 4 | 4 | 4 | 0 | `{'success_event_contact_gated_true_pinch_release_ball': 4}` |
| 4 | `prelift_xneg_s0004_m0008_steps40` | 4 / 4 | 4 | 4 | 4 | 4 | 0 | `{'success_event_contact_gated_true_pinch_release_ball': 4}` |

## Final Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | reasons |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `baseline_off` | 36 / 50 | 47 | 36 | 36 | 49 | 0 | `{'success_event_contact_gated_true_pinch_release_ball': 36, 'lift_gate_failed': 11, 'contact_gate_failed': 3}` |
| 2 | `prelift_xneg_s0004_m0008_steps40` | 32 / 50 | 47 | 32 | 32 | 49 | 449 | `{'success_event_contact_gated_true_pinch_release_ball': 32, 'lift_gate_failed': 15, 'contact_gate_failed': 3}` |
| 3 | `prelift_xneg_s0006_m0012_steps60` | 30 / 50 | 47 | 31 | 30 | 49 | 474 | `{'success_event_contact_gated_true_pinch_release_ball': 30, 'lift_gate_failed': 16, 'contact_gate_failed': 3, 'true_pinch_morphology_gate_failed': 1}` |
| 4 | `prelift_xneg_close_s0004_c004_m0012_steps60` | 30 / 50 | 47 | 30 | 30 | 49 | 533 | `{'success_event_contact_gated_true_pinch_release_ball': 30, 'lift_gate_failed': 17, 'contact_gate_failed': 3}` |

## Selected Diagnostic Candidate

- Variant: `baseline_off`
- Final success: `36 / 50`
- Contact/lift/true-pinch/release: `47` / `36` / `36` / `49`
- Residual events total: `0`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 36, 'lift_gate_failed': 11, 'contact_gate_failed': 3}`

## Next

- If a residual variant beats the no-residual baseline on the same final seed, rerun it on the D-D capture seed and create residual teacher rows.
- If no residual variant improves robustness, keep D-E shadow as diagnostic and return to geometry/material/phase-timing repair.
