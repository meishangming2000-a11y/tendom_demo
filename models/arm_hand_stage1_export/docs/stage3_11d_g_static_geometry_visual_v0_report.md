# Stage3.11D-B Event Contact-Gated Refinement v0

Generated: `2026-06-12T15:15:23`

## Boundary

- MuJoCo-only.
- Local parameter/action-phase search, not neural-network training.
- Provisional diagnostic work; no full-action ACT/DP or hardware promotion.

## Summary

- Cases evaluated: `1`
- Full event true-pinch-release success: `1 / 1`
- Contact-gate success: `1 / 1`
- Lift gate success: `1 / 1`
- True-pinch morphology success: `1 / 1`
- Release success: `1 / 1`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 1}`

## Best Case

- Name: `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0014_gyp0p0000_gzp0p0020_lj2m0p950_ls520_hs100_ml0p100`
- Status: `PASS` / `success_event_contact_gated_true_pinch_release_ball`
- Score: `20.6175`
- Contact gate: `True` at step `60`
- Lift break: `lifted_tip_window_met`
- Hold break: `stable_hold_window_met`
- Hold lift max: `0.11295 m`
- Hold lift mean: `0.11040 m`
- Hold true two-tip fraction: `1.000`
- Gate true two-tip fraction: `0.154`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`
- Visual contact sheet: `simulations\models\arm_hand_stage1_export\docs\stage3_11d_g_static_geometry_vis\event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0014_gyp0p0000_gzp0p0020_lj2m0p950_ls520_hs100_ml0p100_contact_sheet.png`

## Top Cases

| rank | case | status | score | gate | hold lift | two-tip | wrap | release | reason |
|---:|---|---|---:|---|---:|---:|---:|---|---|
| 1 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0014_gyp0p0000_gzp0p0020_lj2m0p950_ls520_hs100_ml0p100` | PASS | 20.618 | `True` | 0.1130 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If success count widens, run randomized pose/object checks and close-up visual review.
- If the pass region remains narrow, branch into fingertip proxy geometry and material/contact modeling.
- Do not promote to demo gallery until visual cleanliness and robustness both pass.
