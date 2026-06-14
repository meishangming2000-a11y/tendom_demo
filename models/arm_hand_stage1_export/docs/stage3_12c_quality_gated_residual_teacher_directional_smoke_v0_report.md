# Stage3.12C Quality-Gated Residual Teacher v0

Generated: `2026-06-13T19:52:36`

## Boundary

- MuJoCo-only bounded residual teacher/search.
- Uses Stage3.12B morphology-quality head as an intervention trigger for tiny residual probes.
- Keeps scripted/event-gated controller and compares against frozen D-I.
- No full-action ACT/DP, hardware runtime, real camera, real tactile, or demo-gallery promotion.

## Failure Window Mining

- Mining variants: `['baseline_di_off']`
- Evidence frames: `348`
- Low-quality frames: `105` (`0.302`)
- Low-quality phases: `{'contact_gate': 80, 'slow_lift': 20, 'post_contact_settle': 5}`
- Low-quality terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 61, 'contact_gate_failed': 44}`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_directional_gx_clamp_m0023_m0002` | 6 / 8 | 7 | 7 | 6 | 7 | 0 | 0.762 | 0.160 | `{'success_event_contact_gated_true_pinch_release_ball': 6, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}` | `reject_or_keep_diagnostic` |
| 2 | `di_directional_gx_clamp_m0025_p0000` | 6 / 8 | 7 | 6 | 6 | 7 | 0 | 0.750 | 0.173 | `{'success_event_contact_gated_true_pinch_release_ball': 6, 'lift_gate_failed': 1, 'contact_gate_failed': 1}` | `advance_candidate` |
| 3 | `di_directional_gx_clamp_qhead_close` | 6 / 8 | 7 | 6 | 6 | 7 | 20 | 0.750 | 0.173 | `{'success_event_contact_gated_true_pinch_release_ball': 6, 'lift_gate_failed': 1, 'contact_gate_failed': 1}` | `advance_candidate` |
| 4 | `baseline_di_off` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `frozen_anchor` |

## Validation Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|

## Selected Diagnostic Outcome

- Variant: `di_directional_gx_clamp_m0023_m0002`
- Candidate family: `vision_directional_teacher`
- Validation success: `6 / 8`
- Contact/lift/true-pinch/release: `7` / `7` / `6` / `7`
- Residual events: `0`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 6, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}`

## Decision

No residual candidate clearly beat frozen D-I on this gate. Keep D-I frozen and use the mined windows to guide the next contact-geometry or richer residual-policy step.

## Next

- If validation beats frozen D-I without morphology regression, run the multiseed 150-trial gate.
- If residuals only trade lift/contact/morphology failures, keep D-I frozen and move to contact geometry or richer residual-policy data.
