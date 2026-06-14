# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-11T13:50:17`

## Boundary

- MuJoCo-only randomized diagnostic probe.
- Parameter/action-phase evaluation, not neural-network training.
- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.
- No demo-gallery, full-action ACT/DP, or hardware-runtime promotion.

## Randomization

- Trials: `4`
- Object pose XY noise: `+/- 0.003 m`
- Grasp target XY noise: `+/- 0.002 m`
- Grasp target Z noise: `+/- 0.001 m`
- Radius jitter: `+/- 0.001 m`
- Mass jitter: `+/- 0.002 kg`
- Friction scale jitter: `+/- 0.08`

## Summary

- Full event true-pinch-release success: `3 / 4`
- Contact-gate success: `4 / 4`
- Lift gate success: `3 / 4`
- True-pinch morphology success: `3 / 4`
- Release success: `4 / 4`
- Terminal reasons: `{'lift_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 3}`
- Successful hold lift mean/min/max: `0.11286` / `0.11207` / `0.11427 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0431 A`
- Max tendon tension proxy: `286.4586 N`
- Saturation trial fraction: `0.000`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.811 | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.641 | 0.1122 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.579 | 0.1121 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | FAIL | 5.021 | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
