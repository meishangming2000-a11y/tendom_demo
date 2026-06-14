# Stage3.11D-B Event Contact-Gated Refinement v0

Generated: `2026-06-11T09:13:51`

## Boundary

- MuJoCo-only.
- Local parameter/action-phase search, not neural-network training.
- Provisional diagnostic work; no full-action ACT/DP or hardware promotion.

## Summary

- Cases evaluated: `40`
- Full event true-pinch-release success: `27 / 40`
- Contact-gate success: `30 / 40`
- Lift gate success: `27 / 40`
- True-pinch morphology success: `27 / 40`
- Release success: `30 / 40`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 27, 'lift_gate_failed': 3, 'contact_gate_failed': 10}`

## Best Case

- Name: `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p050`
- Status: `PASS` / `success_event_contact_gated_true_pinch_release_ball`
- Score: `19.1975`
- Contact gate: `True` at step `35`
- Lift break: `lifted_tip_window_met`
- Hold break: `stable_hold_window_met`
- Hold lift max: `0.06427 m`
- Hold lift mean: `0.06140 m`
- Hold true two-tip fraction: `1.000`
- Gate true two-tip fraction: `0.250`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`
- Visual contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_stage3_11d_b_event_contact_gated_refine_v0\event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p050_contact_sheet.png`

## Top Cases

| rank | case | status | score | gate | hold lift | two-tip | wrap | release | reason |
|---:|---|---|---:|---|---:|---:|---:|---|---|
| 1 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p050` | PASS | 19.197 | `True` | 0.0643 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs120_ml0p050` | PASS | 19.197 | `True` | 0.0643 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs80_ml0p050` | PASS | 19.197 | `True` | 0.0643 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | `event_thumb_middle_tabdm0p350_tmcpp0p320_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p050` | PASS | 19.014 | `True` | 0.0628 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | `event_thumb_middle_tabdm0p350_tmcpp0p320_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs120_ml0p050` | PASS | 19.014 | `True` | 0.0628 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | `event_thumb_middle_tabdm0p350_tmcpp0p320_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs80_ml0p050` | PASS | 19.014 | `True` | 0.0628 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p900_ls520_hs100_ml0p050` | PASS | 18.714 | `True` | 0.0667 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p900_ls520_hs120_ml0p050` | PASS | 18.714 | `True` | 0.0667 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p900_ls520_hs80_ml0p050` | PASS | 18.714 | `True` | 0.0667 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p056_gzp0p002_lj2m0p950_ls520_hs100_ml0p050` | PASS | 18.688 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p056_gzp0p002_lj2m0p950_ls520_hs120_ml0p050` | PASS | 18.688 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p056_gzp0p002_lj2m0p950_ls520_hs80_ml0p050` | PASS | 18.688 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p050` | PASS | 18.668 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs120_ml0p050` | PASS | 18.668 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs80_ml0p050` | PASS | 18.668 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p064_gzp0p002_lj2m0p950_ls520_hs100_ml0p050` | PASS | 18.648 | `True` | 0.0653 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 17 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p060` | PASS | 18.470 | `True` | 0.0728 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 18 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs120_ml0p060` | PASS | 18.470 | `True` | 0.0728 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 19 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs80_ml0p060` | PASS | 18.470 | `True` | 0.0728 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 20 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p450_apipm0p700_sep0p060_gzp0p002_lj2m1p000_ls520_hs100_ml0p050` | PASS | 18.455 | `True` | 0.0627 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If success count widens, run randomized pose/object checks and close-up visual review.
- If the pass region remains narrow, branch into fingertip proxy geometry and material/contact modeling.
- Do not promote to demo gallery until visual cleanliness and robustness both pass.
