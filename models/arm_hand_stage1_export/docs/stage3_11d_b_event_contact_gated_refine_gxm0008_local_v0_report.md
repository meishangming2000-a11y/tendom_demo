# Stage3.11D-B Event Contact-Gated Refinement v0

Generated: `2026-06-12T11:18:46`

## Boundary

- MuJoCo-only.
- Local parameter/action-phase search, not neural-network training.
- Provisional diagnostic work; no full-action ACT/DP or hardware promotion.

## Summary

- Cases evaluated: `80`
- Full event true-pinch-release success: `52 / 80`
- Contact-gate success: `52 / 80`
- Lift gate success: `52 / 80`
- True-pinch morphology success: `52 / 80`
- Release success: `52 / 80`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 52, 'contact_gate_failed': 28}`

## Best Case

- Name: `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100`
- Status: `PASS` / `success_event_contact_gated_true_pinch_release_ball`
- Score: `20.6889`
- Contact gate: `True` at step `145`
- Lift break: `lifted_tip_window_met`
- Hold break: `stable_hold_window_met`
- Hold lift max: `0.11398 m`
- Hold lift mean: `0.11141 m`
- Hold true two-tip fraction: `1.000`
- Gate true two-tip fraction: `0.067`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`
- Visual contact sheet: `simulations\models\arm_hand_stage1_export\docs\v11db_gxm0008_local_vis\event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100_contact_sheet.png`

## Best Motor Force Feedback Proxy

- Samples: `121`
- Max |Iq|: `3.0380 A`
- Mean |Iq|: `1.8245 A`
- Max output torque proxy: `2.27392 Nm`
- Max tendon tension proxy: `284.2403 N`
- Max hand-side |Iq| proxy: `0.2016 A`
- Max hand-side tendon tension proxy: `18.5862 N`
- Active-pair total tension mean/max: `7.5109` / `61.4567 N`
- Active-pair balance mean/min: `0.829` / `0.515`
- Slow-lift pair tension mean/min/max: `5.9463` / `4.9076` / `7.9945 N`
- Hold pair tension mean/min/max: `4.1994` / `3.6828` / `4.9786 N`
- Max bus current proxy: `1.0652 A`
- Current saturation sample fraction: `0.000`

## Best Force-Feedback Gate

- Enabled: `False`
- Preload level: `0.0000`
- Preload break reason: `disabled`
- Lift low-force samples: `0`
- Lift wait steps: `0`

## Top Cases

| rank | case | status | score | gate | hold lift | two-tip | wrap | release | reason |
|---:|---|---|---:|---|---:|---:|---:|---|---|
| 1 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.689 | `True` | 0.1140 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 2 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p740_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.687 | `True` | 0.1122 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 3 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p480_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.687 | `True` | 0.1140 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 4 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.684 | `True` | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 5 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs120_ml0p100` | PASS | 20.684 | `True` | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 6 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p480_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.678 | `True` | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 7 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p930_ls520_hs100_ml0p100` | PASS | 20.677 | `True` | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 8 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p930_ls520_hs120_ml0p100` | PASS | 20.677 | `True` | 0.1139 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 9 | `event_thumb_middle_tabdm0p330_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.677 | `True` | 0.1138 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 10 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p930_ls520_hs100_ml0p100` | PASS | 20.673 | `True` | 0.1138 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 11 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p930_ls520_hs120_ml0p100` | PASS | 20.673 | `True` | 0.1138 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 12 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p480_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.666 | `True` | 0.1137 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 13 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p930_ls520_hs100_ml0p100` | PASS | 20.656 | `True` | 0.1135 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 14 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p930_ls520_hs100_ml0p100` | PASS | 20.651 | `True` | 0.1134 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 15 | `event_thumb_middle_tabdm0p350_tmcpp0p300_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.628 | `True` | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `event_thumb_middle_tabdm0p350_tmcpp0p300_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.627 | `True` | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 17 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p970_ls520_hs100_ml0p100` | PASS | 20.627 | `True` | 0.1129 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 18 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p058_gxm0p001_gyp0p000_gzp0p002_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.627 | `True` | 0.1128 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 19 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p970_ls520_hs100_ml0p100` | PASS | 20.622 | `True` | 0.1128 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |
| 20 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p460_apipm0p700_sep0p060_gxm0p001_gyp0p000_gzp0p002_lj2m0p970_ls520_hs120_ml0p100` | PASS | 20.622 | `True` | 0.1128 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If success count widens, run randomized pose/object checks and close-up visual review.
- If the pass region remains narrow, branch into fingertip proxy geometry and material/contact modeling.
- Do not promote to demo gallery until visual cleanliness and robustness both pass.
