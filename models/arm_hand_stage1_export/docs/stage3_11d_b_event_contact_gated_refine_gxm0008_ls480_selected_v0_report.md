# Stage3.11D-B Event Contact-Gated Refinement v0

Generated: `2026-06-12T11:27:27`

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

- Name: `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0008_gyp0p0000_gzp0p0020_lj2m0p950_ls480_hs100_ml0p100`
- Status: `PASS` / `success_event_contact_gated_true_pinch_release_ball`
- Score: `20.7281`
- Contact gate: `True` at step `50`
- Lift break: `lifted_tip_window_met`
- Hold break: `stable_hold_window_met`
- Hold lift max: `0.11475 m`
- Hold lift mean: `0.11185 m`
- Hold true two-tip fraction: `1.000`
- Gate true two-tip fraction: `0.182`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`
- Visual contact sheet: `simulations\models\arm_hand_stage1_export\docs\v11db_gxm0008_ls480_vis\event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0008_gyp0p0000_gzp0p0020_lj2m0p950_ls480_hs100_ml0p100_contact_sheet.png`

## Best Motor Force Feedback Proxy

- Samples: `97`
- Max |Iq|: `3.1160 A`
- Mean |Iq|: `2.0192 A`
- Max output torque proxy: `2.34331 Nm`
- Max tendon tension proxy: `292.9142 N`
- Max hand-side |Iq| proxy: `0.2044 A`
- Max hand-side tendon tension proxy: `18.8556 N`
- Active-pair total tension mean/max: `9.9254` / `63.5479 N`
- Active-pair balance mean/min: `0.751` / `0.467`
- Slow-lift pair tension mean/min/max: `8.4043` / `6.2977` / `11.3377 N`
- Hold pair tension mean/min/max: `5.3453` / `4.4513` / `6.5026 N`
- Max bus current proxy: `1.0925 A`
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
| 1 | `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0008_gyp0p0000_gzp0p0020_lj2m0p950_ls480_hs100_ml0p100` | PASS | 20.728 | `True` | 0.1148 | 1.000 | 0.000 | `True` | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If success count widens, run randomized pose/object checks and close-up visual review.
- If the pass region remains narrow, branch into fingertip proxy geometry and material/contact modeling.
- Do not promote to demo gallery until visual cleanliness and robustness both pass.
