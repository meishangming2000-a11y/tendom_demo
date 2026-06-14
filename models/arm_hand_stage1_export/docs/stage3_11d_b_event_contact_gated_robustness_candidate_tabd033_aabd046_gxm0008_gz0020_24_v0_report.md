# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-12T11:23:32`

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

- Full event true-pinch-release success: `12 / 24`
- Contact-gate success: `13 / 24`
- Lift gate success: `12 / 24`
- True-pinch morphology success: `12 / 24`
- Release success: `14 / 24`
- Terminal reasons: `{'contact_gate_failed': 11, 'success_event_contact_gated_true_pinch_release_ball': 12, 'lift_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11288` / `0.11092` / `0.11470 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0725 A`
- Max tendon tension proxy: `286.0041 N`
- Max hand-side |Iq| proxy: `0.2031 A`
- Max hand-side tendon tension proxy: `18.7278 N`
- Mean slow-lift pair tension proxy: `2.7957 N`
- Mean hold pair tension proxy: `2.0656 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.850 | 0.1147 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.721 | 0.1125 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.667 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.662 | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.659 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.617 | 0.1127 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.559 | 0.1115 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.528 | 0.1109 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.528 | 0.1109 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.218 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 19.837 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 19.680 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | FAIL | 4.440 | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 14 | FAIL | 1.976 | 0.0000 | 0.000 | 0.000 | `True` | `contact_gate_failed` |
| 15 | FAIL | -0.023 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |
| 16 | FAIL | -0.023 | 0.0000 | 0.000 | 0.000 | `False` | `contact_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
