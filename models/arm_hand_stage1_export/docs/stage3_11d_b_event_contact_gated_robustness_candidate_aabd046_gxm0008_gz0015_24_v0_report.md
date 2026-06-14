# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-12T11:23:03`

## Boundary

- MuJoCo-only randomized diagnostic probe.
- Parameter/action-phase evaluation, not neural-network training.
- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.
- No demo-gallery, full-action ACT/DP, or hardware-runtime promotion.

## Randomization

- Trials: `24`
- Object pose XY noise: `+/- 0.003 m`
- Grasp target XY noise: `+/- 0.002 m`
- Grasp target Z noise: `+/- 0.001 m`
- Radius jitter: `+/- 0.001 m`
- Mass jitter: `+/- 0.002 kg`
- Friction scale jitter: `+/- 0.08`

## Summary

- Full event true-pinch-release success: `7 / 24`
- Contact-gate success: `8 / 24`
- Lift gate success: `8 / 24`
- True-pinch morphology success: `7 / 24`
- Release success: `10 / 24`
- Terminal reasons: `{'contact_gate_failed': 16, 'success_event_contact_gated_true_pinch_release_ball': 7, 'true_pinch_morphology_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11336` / `0.11219` / `0.11458 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.1130 A`
- Max tendon tension proxy: `289.4572 N`
- Max hand-side |Iq| proxy: `0.2059 A`
- Max hand-side tendon tension proxy: `18.9930 N`
- Mean slow-lift pair tension proxy: `1.9617 N`
- Mean hold pair tension proxy: `1.2092 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.723 | 0.1146 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.646 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.606 | 0.1126 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.601 | 0.1126 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.572 | 0.1122 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 19.796 | 0.1138 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 17.197 | 0.1143 | 0.600 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | FAIL | 12.425 | 0.1111 | 0.100 | 0.000 | `True` | `true_pinch_morphology_gate_failed` |
| 9 | FAIL | 1.974 | 0.0000 | 0.000 | 0.000 | `True` | `contact_gate_failed` |
| 10 | FAIL | 1.974 | 0.0000 | 0.000 | 0.000 | `True` | `contact_gate_failed` |
| 11 | FAIL | -0.026 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |
| 12 | FAIL | -0.026 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |
| 13 | FAIL | -0.026 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |
| 14 | FAIL | -0.026 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |
| 15 | FAIL | -0.026 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |
| 16 | FAIL | -0.026 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
