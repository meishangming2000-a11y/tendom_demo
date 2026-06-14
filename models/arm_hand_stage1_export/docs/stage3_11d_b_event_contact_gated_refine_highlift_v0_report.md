# Stage3.11D-B Event Contact-Gated Refinement v0

Generated: `2026-06-11T09:21:32`

## Boundary

- MuJoCo-only.
- Local parameter/action-phase search, not neural-network training.
- Provisional diagnostic work; no full-action ACT/DP or hardware promotion.

## Summary

- Cases evaluated: `30`
- Full event true-pinch-release success: `18 / 30`
- Contact-gate success: `20 / 30`
- Lift gate success: `18 / 30`
- True-pinch morphology success: `18 / 30`
- Release success: `20 / 30`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 18, 'lift_gate_failed': 2, 'contact_gate_failed': 10}`

## Best Case

- Name: `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100`
- Status: `PASS` / `success_event_contact_gated_true_pinch_release_ball`
- Score: `20.7209`
- Contact gate: `True` at step `35`
- Lift break: `lifted_tip_window_met`
- Hold break: `stable_hold_window_met`
- Hold lift max: `0.11381 m`
- Hold lift mean: `0.11131 m`
- Hold true two-tip fraction: `1.000`
- Gate true two-tip fraction: `0.250`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`
- Visual contact sheet: `simulations\models\arm_hand_stage1_export\docs\v11db_highlift_vis\event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100_contact_sheet.png`

## Top Cases

| rank | case | status | score | gate | hold lift | two-tip | wrap | release | reason |
|---:|---|---|---:|---|---:|---:|---:|---|---|
| 1 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.721 | `True` | 0.1138 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p900_ls520_hs100_ml0p100` | PASS | 20.716 | `True` | 0.1143 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.663 | `True` | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs120_ml0p100` | PASS | 20.663 | `True` | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs80_ml0p100` | PASS | 20.663 | `True` | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p003_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.642 | `True` | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p003_lj2m0p950_ls520_hs120_ml0p100` | PASS | 20.642 | `True` | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p003_lj2m0p950_ls520_hs80_ml0p100` | PASS | 20.642 | `True` | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m1p000_ls520_hs100_ml0p100` | PASS | 20.467 | `True` | 0.1102 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p900_ls520_hs100_ml0p080` | PASS | 20.438 | `True` | 0.0949 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m1p000_ls520_hs100_ml0p080` | PASS | 20.271 | `True` | 0.0915 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p080` | PASS | 20.252 | `True` | 0.0912 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs120_ml0p080` | PASS | 20.252 | `True` | 0.0912 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs80_ml0p080` | PASS | 20.252 | `True` | 0.0912 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p080` | PASS | 20.192 | `True` | 0.0896 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p003_lj2m0p950_ls520_hs100_ml0p080` | PASS | 20.081 | `True` | 0.0918 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 17 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p003_lj2m0p950_ls520_hs120_ml0p080` | PASS | 20.081 | `True` | 0.0918 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 18 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p003_lj2m0p950_ls520_hs80_ml0p080` | PASS | 20.081 | `True` | 0.0918 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 19 | `event_thumb_middle_tabdm0p300_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | FAIL | 4.380 | `True` | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 20 | `event_thumb_middle_tabdm0p300_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p080` | FAIL | 4.379 | `True` | -0.0001 | 0.000 | 0.000 | `True` | `lift_gate_failed` |

## Next

- If success count widens, run randomized pose/object checks and close-up visual review.
- If the pass region remains narrow, branch into fingertip proxy geometry and material/contact modeling.
- Do not promote to demo gallery until visual cleanliness and robustness both pass.
