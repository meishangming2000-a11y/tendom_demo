# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-12T11:26:09`

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

- Full event true-pinch-release success: `17 / 24`
- Contact-gate success: `22 / 24`
- Lift gate success: `18 / 24`
- True-pinch morphology success: `17 / 24`
- Release success: `23 / 24`
- Terminal reasons: `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 17, 'lift_gate_failed': 4, 'true_pinch_morphology_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11472` / `0.11339` / `0.11614 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.2334 A`
- Max tendon tension proxy: `303.6003 N`
- Max hand-side |Iq| proxy: `0.2107 A`
- Max hand-side tendon tension proxy: `19.4507 N`
- Mean slow-lift pair tension proxy: `7.1020 N`
- Mean hold pair tension proxy: `4.1580 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.802 | 0.1161 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.793 | 0.1160 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.786 | 0.1138 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.782 | 0.1158 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.760 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.756 | 0.1151 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.695 | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.676 | 0.1140 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.673 | 0.1150 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.657 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 20.641 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 20.537 | 0.1158 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | PASS | 20.469 | 0.1144 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | PASS | 19.808 | 0.1142 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | PASS | 19.772 | 0.1159 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | PASS | 19.710 | 0.1146 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
