# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-11T16:55:46`

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

- Full event true-pinch-release success: `15 / 24`
- Contact-gate success: `24 / 24`
- Lift gate success: `16 / 24`
- True-pinch morphology success: `15 / 24`
- Release success: `24 / 24`
- Terminal reasons: `{'lift_gate_failed': 8, 'success_event_contact_gated_true_pinch_release_ball': 15, 'true_pinch_morphology_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11269` / `0.11056` / `0.11438 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0779 A`
- Max tendon tension proxy: `287.0613 N`
- Max hand-side |Iq| proxy: `0.2104 A`
- Max hand-side tendon tension proxy: `19.4202 N`
- Mean slow-lift pair tension proxy: `6.8945 N`
- Mean hold pair tension proxy: `3.5245 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `True`
- Lift low-force samples total: `353`
- Lift wait steps total: `1415`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.714 | 0.1126 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.651 | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.601 | 0.1124 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.596 | 0.1125 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.590 | 0.1127 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.585 | 0.1121 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.571 | 0.1121 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.536 | 0.1115 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.525 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.524 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 20.493 | 0.1106 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 20.474 | 0.1131 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | PASS | 20.455 | 0.1144 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | PASS | 19.617 | 0.1132 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | PASS | 17.614 | 0.1135 | 0.650 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | FAIL | 11.479 | 0.1105 | 0.000 | 0.000 | `True` | `true_pinch_morphology_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
