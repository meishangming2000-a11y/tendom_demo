# Stage3.12C Quality-Gated Residual Teacher v0

Generated: `2026-06-13T19:55:05`

## Boundary

- MuJoCo-only bounded residual teacher/search.
- Uses Stage3.12B morphology-quality head as an intervention trigger for tiny residual probes.
- Keeps scripted/event-gated controller and compares against frozen D-I.
- No full-action ACT/DP, hardware runtime, real camera, real tactile, or demo-gallery promotion.

## Failure Window Mining

- Mining variants: `['baseline_di_off']`
- Evidence frames: `764`
- Low-quality frames: `189` (`0.247`)
- Low-quality phases: `{'contact_gate': 135, 'slow_lift': 43, 'post_contact_settle': 9, 'hold': 2}`
- Low-quality terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 145, 'contact_gate_failed': 44}`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_directional_gx_clamp_m0025_p0000` | 6 / 8 | 7 | 6 | 6 | 7 | 0 | 0.750 | 0.173 | `{'success_event_contact_gated_true_pinch_release_ball': 6, 'lift_gate_failed': 1, 'contact_gate_failed': 1}` | `advance_candidate` |
| 2 | `di_directional_gx_clamp_qhead_close` | 6 / 8 | 7 | 6 | 6 | 7 | 20 | 0.750 | 0.173 | `{'success_event_contact_gated_true_pinch_release_ball': 6, 'lift_gate_failed': 1, 'contact_gate_failed': 1}` | `advance_candidate` |
| 3 | `di_directional_gx_clamp_m0023_m0002` | 6 / 8 | 7 | 7 | 6 | 7 | 0 | 0.762 | 0.160 | `{'success_event_contact_gated_true_pinch_release_ball': 6, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}` | `reject_or_keep_diagnostic` |
| 4 | `baseline_di_off` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `frozen_anchor` |

## Validation Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_directional_gx_clamp_m0025_p0000` | 49 / 50 | 49 | 49 | 49 | 50 | 0 | 0.980 | 0.038 | `{'success_event_contact_gated_true_pinch_release_ball': 49, 'contact_gate_failed': 1}` | `advance_candidate` |
| 2 | `di_directional_gx_clamp_qhead_close` | 49 / 50 | 49 | 49 | 49 | 50 | 0 | 0.980 | 0.038 | `{'success_event_contact_gated_true_pinch_release_ball': 49, 'contact_gate_failed': 1}` | `advance_candidate` |
| 3 | `baseline_di_off` | 46 / 50 | 48 | 46 | 46 | 50 | 0 | 0.920 | 0.052 | `{'success_event_contact_gated_true_pinch_release_ball': 46, 'lift_gate_failed': 2, 'contact_gate_failed': 2}` | `frozen_anchor` |

## Selected Diagnostic Outcome

- Variant: `di_directional_gx_clamp_m0025_p0000`
- Candidate family: `vision_directional_teacher`
- Validation success: `49 / 50`
- Contact/lift/true-pinch/release: `49` / `49` / `49` / `50`
- Residual events: `0`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 49, 'contact_gate_failed': 1}`

## Decision

Selected candidate beat the frozen D-I anchor on the matched validation gate without a true-pinch morphology regression. It should advance to the 150-trial multiseed gate, not direct promotion yet.

## Next

- If validation beats frozen D-I without morphology regression, run the multiseed 150-trial gate.
- If residuals only trade lift/contact/morphology failures, keep D-I frozen and move to contact geometry or richer residual-policy data.
