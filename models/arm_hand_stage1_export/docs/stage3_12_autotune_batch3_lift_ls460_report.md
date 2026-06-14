# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-13T11:42:13`

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

- Full event true-pinch-release success: `11 / 12`
- Contact-gate success: `12 / 12`
- Lift gate success: `11 / 12`
- True-pinch morphology success: `11 / 12`
- Release success: `12 / 12`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 11, 'lift_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11499` / `0.11338` / `0.11575 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.1772 A`
- Max tendon tension proxy: `301.4136 N`
- Max hand-side |Iq| proxy: `0.2088 A`
- Max hand-side tendon tension proxy: `19.5012 N`
- Mean slow-lift pair tension proxy: `9.1920 N`
- Mean hold pair tension proxy: `6.0787 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.776 | 0.1156 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.719 | 0.1140 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.645 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.512 | 0.1144 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.488 | 0.1157 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.340 | 0.1156 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 19.854 | 0.1150 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 19.776 | 0.1154 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 19.760 | 0.1157 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 19.754 | 0.1156 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 19.698 | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | FAIL | 8.859 | 0.0650 | 0.000 | 0.000 | `True` | `lift_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
