# Stage3.11D-C Geometry + Force-Feedback Refine v0

Generated: `2026-06-12T01:56:43`

## Boundary

- MuJoCo-only diagnostic training/search.
- Geometry and force-feedback-aware evaluation, not neural-network training yet.
- No real hardware, camera, tactile hardware, ultrasound, demo-gallery promotion, or full-action ACT/DP promotion.

## Local Search Summary

- Cases evaluated: `36`
- Local event true-pinch-release success: `33 / 36`
- Contact gate: `36 / 36`
- Lift gate: `34 / 36`
- True-pinch gate: `33 / 36`
- Release: `36 / 36`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 33, 'true_pinch_morphology_gate_failed': 1, 'lift_gate_failed': 2}`

## Robustness Probes

| rank | candidate | smoke success | final success | contact | lift | true pinch | release | reasons |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p056_tmcpp0p300_aabdm0p500_apipm0p700` | 10 / 12 | 33 / 50 | 48 | 33 | 33 | 48 | `{'success_event_contact_gated_true_pinch_release_ball': 33, 'lift_gate_failed': 15, 'contact_gate_failed': 2}` |
| 2 | `s311dc_thumb_middle_gxm0p0008_gzp0p0015_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700` | 9 / 12 | 36 / 50 | 48 | 41 | 36 | 48 | `{'success_event_contact_gated_true_pinch_release_ball': 36, 'true_pinch_morphology_gate_failed': 5, 'lift_gate_failed': 7, 'contact_gate_failed': 2}` |
| 3 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p064_tmcpp0p280_aabdm0p500_apipm0p700` | 9 / 12 | - / - | - | - | - | - | `{'lift_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 9, 'true_pinch_morphology_gate_failed': 1}` |
| 4 | `s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p060_tmcpp0p300_aabdm0p500_apipm0p700` | 9 / 12 | - / - | - | - | - | - | `{'lift_gate_failed': 3, 'success_event_contact_gated_true_pinch_release_ball': 9}` |
| 5 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p056_tmcpp0p280_aabdm0p500_apipm0p700` | 8 / 12 | - / - | - | - | - | - | `{'lift_gate_failed': 4, 'success_event_contact_gated_true_pinch_release_ball': 8}` |
| 6 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700` | 8 / 12 | - / - | - | - | - | - | `{'success_event_contact_gated_true_pinch_release_ball': 8, 'lift_gate_failed': 2, 'contact_gate_failed': 2}` |
| 7 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p300_aabdm0p500_apipm0p700` | 7 / 12 | - / - | - | - | - | - | `{'success_event_contact_gated_true_pinch_release_ball': 7, 'lift_gate_failed': 4, 'contact_gate_failed': 1}` |
| 8 | `s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p056_tmcpp0p300_aabdm0p500_apipm0p700` | 5 / 12 | - / - | - | - | - | - | `{'lift_gate_failed': 7, 'success_event_contact_gated_true_pinch_release_ball': 5}` |
| 9 | `s311dc_thumb_middle_gxm0p0006_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p470_apipm0p700` | 5 / 12 | - / - | - | - | - | - | `{'contact_gate_failed': 6, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` |
| 10 | `s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p064_tmcpp0p300_aabdm0p500_apipm0p700` | 4 / 12 | - / - | - | - | - | - | `{'lift_gate_failed': 8, 'success_event_contact_gated_true_pinch_release_ball': 4}` |

## Selected Candidate

- Name: `s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700`
- Final robustness: `43 / 50`
- Contact / lift / true-pinch / release: `49` / `44` / `43` / `50`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}`
- Hold lift mean/min/max: `0.11276` / `0.11093` / `0.11452 m`
- Mean slow-lift pair tension: `7.8862 N`
- Mean hold pair tension: `4.3746 N`
- Contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_11d_c_geometry_force_refine_vis\s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700_contact_sheet.png`

## Interpretation

- This stage keeps force feedback as an observation/gate/label signal.
- Direct preload remains opt-in and is not the default path.
- If the selected candidate beats the prior `34 / 50` probe, it becomes the next dense-capture center.
- If it does not beat `34 / 50`, keep the previous `gx -0.0008 m` candidate as the search center and widen geometry/material modeling next.

## Next

1. Use the selected candidate as Stage3.11D-C dense-capture center if final robustness improves.
2. Export dense per-step obs/action/force/morphology labels for LiftQualityHead and residual micro-adjust training.
3. Keep Stage3 MuJoCo-only boundaries and do not promote to demo gallery before close-up visual review.
