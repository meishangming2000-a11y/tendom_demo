# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-11T16:57:31`

## Boundary

- MuJoCo-only randomized diagnostic probe.
- Parameter/action-phase evaluation, not neural-network training.
- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.
- No demo-gallery, full-action ACT/DP, or hardware-runtime promotion.

## Randomization

- Trials: `50`
- Object pose XY noise: `+/- 0.003 m`
- Grasp target XY noise: `+/- 0.002 m`
- Grasp target Z noise: `+/- 0.001 m`
- Radius jitter: `+/- 0.001 m`
- Mass jitter: `+/- 0.002 kg`
- Friction scale jitter: `+/- 0.08`

## Summary

- Full event true-pinch-release success: `29 / 50`
- Contact-gate success: `49 / 50`
- Lift gate success: `29 / 50`
- True-pinch morphology success: `29 / 50`
- Release success: `49 / 50`
- Terminal reasons: `{'lift_gate_failed': 20, 'success_event_contact_gated_true_pinch_release_ball': 29, 'contact_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11274` / `0.11083` / `0.11459 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0807 A`
- Max tendon tension proxy: `287.4547 N`
- Max hand-side |Iq| proxy: `0.2097 A`
- Max hand-side tendon tension proxy: `19.3552 N`
- Mean slow-lift pair tension proxy: `6.7411 N`
- Mean hold pair tension proxy: `3.4427 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.811 | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.806 | 0.1142 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.777 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.753 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.736 | 0.1130 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.699 | 0.1123 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.695 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.675 | 0.1132 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.658 | 0.1116 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.657 | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 20.641 | 0.1122 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 20.639 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | PASS | 20.633 | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | PASS | 20.615 | 0.1131 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | PASS | 20.604 | 0.1127 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | PASS | 20.594 | 0.1125 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
