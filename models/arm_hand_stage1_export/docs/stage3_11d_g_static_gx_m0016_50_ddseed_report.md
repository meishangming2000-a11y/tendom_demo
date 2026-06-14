# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-12T15:06:32`

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

- Full event true-pinch-release success: `41 / 50`
- Contact-gate success: `44 / 50`
- Lift gate success: `41 / 50`
- True-pinch morphology success: `41 / 50`
- Release success: `48 / 50`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 41, 'contact_gate_failed': 6, 'lift_gate_failed': 3}`
- Successful hold lift mean/min/max: `0.11306` / `0.11068` / `0.11479 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0590 A`
- Max tendon tension proxy: `287.4376 N`
- Max hand-side |Iq| proxy: `0.2094 A`
- Max hand-side tendon tension proxy: `19.4924 N`
- Mean slow-lift pair tension proxy: `7.4439 N`
- Mean hold pair tension proxy: `4.5963 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.825 | 0.1145 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.777 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.773 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.765 | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.764 | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.761 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.724 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.699 | 0.1144 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.672 | 0.1141 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.660 | 0.1132 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 20.660 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 20.633 | 0.1148 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | PASS | 20.625 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | PASS | 20.623 | 0.1126 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | PASS | 20.610 | 0.1128 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | PASS | 20.587 | 0.1124 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
