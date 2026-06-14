# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-11T16:47:29`

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

- Full event true-pinch-release success: `9 / 24`
- Contact-gate success: `24 / 24`
- Lift gate success: `11 / 24`
- True-pinch morphology success: `9 / 24`
- Release success: `24 / 24`
- Terminal reasons: `{'lift_gate_failed': 13, 'success_event_contact_gated_true_pinch_release_ball': 9, 'true_pinch_morphology_gate_failed': 2}`
- Successful hold lift mean/min/max: `0.11278` / `0.11124` / `0.11423 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0796 A`
- Max tendon tension proxy: `287.1242 N`
- Max hand-side |Iq| proxy: `0.2354 A`
- Max hand-side tendon tension proxy: `19.3552 N`
- Mean slow-lift pair tension proxy: `10.9482 N`
- Mean hold pair tension proxy: `4.2456 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `True`
- Lift low-force samples total: `58`
- Lift wait steps total: `290`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.808 | 0.1142 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.762 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.723 | 0.1127 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.704 | 0.1124 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.679 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.647 | 0.1127 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.606 | 0.1114 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 19.764 | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 17.883 | 0.1112 | 0.700 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | FAIL | 12.507 | 0.1116 | 0.100 | 0.000 | `True` | `true_pinch_morphology_gate_failed` |
| 11 | FAIL | 12.038 | 0.1104 | 0.050 | 0.000 | `True` | `true_pinch_morphology_gate_failed` |
| 12 | FAIL | 10.529 | 0.0922 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 13 | FAIL | 7.917 | 0.0473 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 14 | FAIL | 5.100 | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 15 | FAIL | 5.070 | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 16 | FAIL | 5.058 | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
