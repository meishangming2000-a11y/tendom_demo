# Stage3.12B Morphology Quality Shadow v0

Generated: `2026-06-13T12:54:53`

## Boundary

- Fresh MuJoCo-only shadow evaluation of the Stage3.12B morphology-quality head.
- Controller actions are unchanged; model predictions are logged only.
- No bounded residual, demo-gallery, full-action ACT/DP, or hardware-runtime promotion is made here.

## Summary

- Candidates: `['baseline_di', 'lift_ls460']`
- Trials per candidate: `12`
- Episodes: `24`
- Success: `18 / 24`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 18, 'contact_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1}`
- Shadow evidence frames: `10801`

## Shadow Metrics

| label | accuracy | precision | recall | F1 | positive fraction | fp | fn |
|---|---:|---:|---:|---:|---:|---:|---:|
| `morphology_clean_now` | 0.9999 | 1.0000 | 0.9999 | 0.9999 | 0.7077 | 0 | 1 |
| `good_two_tip_now` | 0.9994 | 0.9997 | 0.9995 | 0.9996 | 0.7993 | 3 | 4 |
| `low_non_tip_now` | 0.9993 | 1.0000 | 0.9991 | 0.9995 | 0.8092 | 0 | 8 |
| `wrap_now` | 0.9994 | 0.9966 | 1.0000 | 0.9983 | 0.1908 | 7 | 0 |
| `floor_contact_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.1532 | 0 | 0 |
| `penetration_risk_now` | 0.9860 | 0.0000 | 0.0000 | 0.0000 | 0.0066 | 80 | 71 |
| `lift_quality_now` | 0.9988 | 0.9986 | 0.9997 | 0.9991 | 0.7067 | 11 | 2 |
| `future_success` | 0.9098 | 0.9499 | 0.9434 | 0.9466 | 0.8480 | 456 | 518 |

## Candidate Slices

| candidate | episodes | success | morphology-clean F1 | future-success F1 | reasons |
|---|---:|---:|---:|---:|---|
| `baseline_di` | 12 | 8 | 1.0000 | 0.9130 | `{'success_event_contact_gated_true_pinch_release_ball': 8, 'contact_gate_failed': 4}` |
| `lift_ls460` | 12 | 10 | 0.9999 | 0.9734 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 10, 'true_pinch_morphology_gate_failed': 1}` |

## Next

- Use high-confidence false/low morphology windows to design a bounded residual teacher.
- Do not alter control until the residual branch beats frozen D-I on the same multiseed gate without morphology regression.
