# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-13T11:32:19`

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

- Full event true-pinch-release success: `10 / 12`
- Contact-gate success: `10 / 12`
- Lift gate success: `10 / 12`
- True-pinch morphology success: `10 / 12`
- Release success: `12 / 12`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 10, 'contact_gate_failed': 2}`
- Successful hold lift mean/min/max: `0.11419` / `0.11232` / `0.11521 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.1437 A`
- Max tendon tension proxy: `294.9748 N`
- Max hand-side |Iq| proxy: `0.1968 A`
- Max hand-side tendon tension proxy: `19.1205 N`
- Mean slow-lift pair tension proxy: `7.3236 N`
- Mean hold pair tension proxy: `4.9118 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.857 | 0.1150 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.770 | 0.1149 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.745 | 0.1147 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.710 | 0.1152 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.702 | 0.1142 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.695 | 0.1141 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.665 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.659 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.592 | 0.1123 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 19.697 | 0.1141 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | FAIL | 1.968 | 0.0000 | 0.000 | 0.000 | `True` | `contact_gate_failed` |
| 12 | FAIL | 1.968 | 0.0000 | 0.000 | 0.000 | `True` | `contact_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
