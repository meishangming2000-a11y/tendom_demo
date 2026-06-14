# Stage3.12C Quality-Gated Residual Teacher v0

Generated: `2026-06-13T19:56:22`

## Boundary

- MuJoCo-only bounded residual teacher/search.
- Uses Stage3.12B morphology-quality head as an intervention trigger for tiny residual probes.
- Keeps scripted/event-gated controller and compares against frozen D-I.
- No full-action ACT/DP, hardware runtime, real camera, real tactile, or demo-gallery promotion.

## Failure Window Mining

- Mining variants: `['baseline_di_off']`
- Evidence frames: `97`
- Low-quality frames: `12` (`0.124`)
- Low-quality phases: `{'contact_gate': 10, 'slow_lift': 2}`
- Low-quality terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 12}`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_directional_gx_clamp_m0025_p0000` | 1 / 1 | 1 | 1 | 1 | 1 | 0 | 1.000 | 0.333 | `{'success_event_contact_gated_true_pinch_release_ball': 1}` | `advance_candidate` |
| 2 | `baseline_di_off` | 0 / 1 | 0 | 0 | 0 | 1 | 0 | 0.000 | 0.000 | `{'contact_gate_failed': 1}` | `frozen_anchor` |

## Validation Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_directional_gx_clamp_m0025_p0000` | 45 / 50 | 47 | 45 | 45 | 49 | 0 | 0.900 | 0.061 | `{'success_event_contact_gated_true_pinch_release_ball': 45, 'lift_gate_failed': 2, 'contact_gate_failed': 3}` | `advance_candidate` |
| 2 | `baseline_di_off` | 44 / 50 | 47 | 44 | 44 | 50 | 0 | 0.880 | 0.078 | `{'success_event_contact_gated_true_pinch_release_ball': 44, 'lift_gate_failed': 3, 'contact_gate_failed': 3}` | `frozen_anchor` |

## Selected Diagnostic Outcome

- Variant: `di_directional_gx_clamp_m0025_p0000`
- Candidate family: `vision_directional_teacher`
- Validation success: `45 / 50`
- Contact/lift/true-pinch/release: `47` / `45` / `45` / `49`
- Residual events: `0`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 45, 'lift_gate_failed': 2, 'contact_gate_failed': 3}`

## Decision

Selected candidate beat the frozen D-I anchor on the matched validation gate without a true-pinch morphology regression. It should advance to the 150-trial multiseed gate, not direct promotion yet.

## Next

- If validation beats frozen D-I without morphology regression, run the multiseed 150-trial gate.
- If residuals only trade lift/contact/morphology failures, keep D-I frozen and move to contact geometry or richer residual-policy data.
