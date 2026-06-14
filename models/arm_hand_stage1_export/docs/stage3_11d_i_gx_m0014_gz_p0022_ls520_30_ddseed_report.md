# Stage3.11D-B Event Contact-Gated Robustness v0

Generated: `2026-06-12T15:28:56`

## Boundary

- MuJoCo-only randomized diagnostic probe.
- Parameter/action-phase evaluation, not neural-network training.
- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.
- No demo-gallery, full-action ACT/DP, or hardware-runtime promotion.

## Randomization

- Trials: `30`
- Object pose XY noise: `+/- 0.003 m`
- Grasp target XY noise: `+/- 0.002 m`
- Grasp target Z noise: `+/- 0.001 m`
- Radius jitter: `+/- 0.001 m`
- Mass jitter: `+/- 0.002 kg`
- Friction scale jitter: `+/- 0.08`

## Summary

- Full event true-pinch-release success: `26 / 30`
- Contact-gate success: `29 / 30`
- Lift gate success: `27 / 30`
- True-pinch morphology success: `26 / 30`
- Release success: `30 / 30`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 26, 'lift_gate_failed': 2, 'contact_gate_failed': 1, 'true_pinch_morphology_gate_failed': 1}`
- Successful hold lift mean/min/max: `0.11308` / `0.11052` / `0.11478 m`

## Simulated Motor Force Feedback

- Max |Iq| proxy: `3.0655 A`
- Max tendon tension proxy: `287.0086 N`
- Max hand-side |Iq| proxy: `0.2093 A`
- Max hand-side tendon tension proxy: `19.4321 N`
- Mean slow-lift pair tension proxy: `8.0028 N`
- Mean hold pair tension proxy: `4.7490 N`
- Saturation trial fraction: `0.000`

## Force-Feedback Gate

- Enabled: `False`
- Lift low-force samples total: `0`
- Lift wait steps total: `0`

## Top Trials

| trial | status | score | hold lift | two-tip | wrap | release | reason |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PASS | 20.778 | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | PASS | 20.770 | 0.1136 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | PASS | 20.755 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | PASS | 20.709 | 0.1148 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | PASS | 20.708 | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | PASS | 20.694 | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | PASS | 20.677 | 0.1133 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | PASS | 20.660 | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | PASS | 20.632 | 0.1132 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | PASS | 20.627 | 0.1131 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | PASS | 20.599 | 0.1126 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | PASS | 20.596 | 0.1126 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | PASS | 20.575 | 0.1122 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | PASS | 20.569 | 0.1123 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | PASS | 20.551 | 0.1116 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | PASS | 20.530 | 0.1114 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.
- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.
- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.
