# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-12T11:24:37`

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
- Lift gate success: `17 / 24`
- True-pinch morphology success: `17 / 24`
- Release success: `23 / 24`
- Terminal reasons: `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 17, 'lift_gate_failed': 5}`
- Successful hold lift mean/min/max: `0.11355` / `0.11201` / `0.11540 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.1092 A`
- Max tendon tension proxy: `291.7600 N`
- Max hand-side |Iq| proxy: `0.2107 A`
- Max hand-side tendon tension proxy: `19.4507 N`
- Mean slow-lift pair tension proxy: `6.7909 N`
- Mean hold pair tension proxy: `3.7849 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.757 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.756 | 0.1149 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.727 | 0.1128 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.653 | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.648 | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.639 | 0.1131 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.629 | 0.1132 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.629 | 0.1130 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.609 | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.605 | 0.1141 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 20.591 | 0.1123 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 20.582 | 0.1124 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | PASS | 20.574 | 0.1120 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | PASS | 20.203 | 0.1154 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | PASS | 19.871 | 0.1153 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | PASS | 19.699 | 0.1144 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
