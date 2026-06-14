# Stage3.11D-C Geometry + Force-Feedback Refine v0

Generated: `2026-06-12T01:49:26`

## Boundary

- MuJoCo-only diagnostic training/search.
- Geometry and force-feedback-aware evaluation, not neural-network training yet.
- No real hardware, camera, tactile hardware, ultrasound, demo-gallery promotion, or full-action ACT/DP promotion.

## Local Search Summary

- Cases evaluated: `6`
- Local event true-pinch-release success: `6 / 6`
- Contact gate: `6 / 6`
- Lift gate: `6 / 6`
- True-pinch gate: `6 / 6`
- Release: `6 / 6`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 6}`

## Robustness Probes

| rank | candidate | smoke success | final success | contact | lift | true pinch | release | reasons |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p300_aabdm0p500_apipm0p700` | 3 / 3 | 2 / 6 | 6 | 2 | 2 | 6 | `{'lift_gate_failed': 4, 'success_event_contact_gated_true_pinch_release_ball': 2}` |
| 2 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p056_tmcpp0p280_aabdm0p500_apipm0p700` | 2 / 3 | - / - | - | - | - | - | `{'lift_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2}` |
| 3 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700` | 0 / 3 | - / - | - | - | - | - | `{'lift_gate_failed': 3}` |

## Selected Candidate

- Name: `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p300_aabdm0p500_apipm0p700`
- Final robustness: `2 / 6`
- Contact / lift / true-pinch / release: `6` / `2` / `2` / `6`
- Terminal reasons: `{'lift_gate_failed': 4, 'success_event_contact_gated_true_pinch_release_ball': 2}`
- Hold lift mean/min/max: `0.11260` / `0.11242` / `0.11278 m`
- Mean slow-lift pair tension: `6.2600 N`
- Mean hold pair tension: `2.8402 N`
- Contact sheet: `simulations\models\arm_hand_stage1_export\docs\stage3_11d_c_geometry_force_refine_smoke_vis\s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p300_aabdm0p500_apipm0p700_contact_sheet.png`

## Interpretation

- This stage keeps force feedback as an observation/gate/label signal.
- Direct preload remains opt-in and is not the default path.
- If the selected candidate beats the prior `34 / 50` probe, it becomes the next dense-capture center.
- If it does not beat `34 / 50`, keep the previous `gx -0.0008 m` candidate as the search center and widen geometry/material modeling next.

## Next

1. Use the selected candidate as Stage3.11D-C dense-capture center if final robustness improves.
2. Export dense per-step obs/action/force/morphology labels for LiftQualityHead and residual micro-adjust training.
3. Keep Stage3 MuJoCo-only boundaries and do not promote to demo gallery before close-up visual review.
