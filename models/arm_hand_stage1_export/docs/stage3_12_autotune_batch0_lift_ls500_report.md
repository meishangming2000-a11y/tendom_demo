# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-13T11:31:58`

## Boundary

- MuJoCo-only randomized diagnostic probe.
- Parameter/action-phase evaluation, not neural-network training.
- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.
- No demo-gallery, full-action ACT/DP, or hardware-runtime promotion.

## Randomization

- Trials: `12`
- Object pose XY noise: `+/- 0.003 m`
- Grasp target XY noise: `+/- 0.002 m`
- Grasp target Z noise: `+/- 0.001 m`
- Radius jitter: `+/- 0.001 m`
- Mass jitter: `+/- 0.002 kg`
- Friction scale jitter: `+/- 0.08`

## Summary

- Full event true-pinch-release success: `9 / 12`
- Contact-gate success: `11 / 12`
- Lift gate success: `10 / 12`
- True-pinch morphology success: `9 / 12`
- Release success: `12 / 12`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 9, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1, 'lift_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11368` / `0.11269` / `0.11457 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0996 A`
- Max tendon tension proxy: `291.1479 N`
- Max hand-side |Iq| proxy: `0.1989 A`
- Max hand-side tendon tension proxy: `19.3229 N`
- Mean slow-lift pair tension proxy: `8.3519 N`
- Mean hold pair tension proxy: `4.4068 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.829 | 0.1146 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.805 | 0.1142 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.778 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.755 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.754 | 0.1144 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.634 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.612 | 0.1127 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.426 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.314 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | FAIL | 12.446 | 0.1115 | 0.100 | 0.000 | `True` | `true_pinch_morphology_gate_failed` |
| 11 | FAIL | 6.862 | 0.0308 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 12 | FAIL | 1.963 | 0.0000 | 0.000 | 0.000 | `True` | `contact_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
