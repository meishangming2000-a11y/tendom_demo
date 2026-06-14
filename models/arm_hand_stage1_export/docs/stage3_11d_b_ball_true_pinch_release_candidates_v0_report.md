# Stage3.11D-B Ball True-Pinch Release Candidate Search v0

Generated: `2026-06-11T02:19:48`

## Boundary

- MuJoCo-only.
- Parameter search, not neural-network training.
- No hardware, real camera, tactile hardware, ultrasound, or full-action ACT/DP promotion.

## Goal

Find a small-ball demo candidate that separates lift success from true fingertip pinch and release success.

## Summary

- Candidates evaluated: `108`
- Full true-pinch-release success: `1 / 108`
- Lift gate success: `1 / 108`
- True-pinch morphology gate success: `1 / 108`
- Release gate success: `108 / 108`
- Terminal reasons: `{'success_true_pinch_lift_release_ball': 1, 'lift_gate_failed': 107}`

## Best Candidate

- Name: `thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p35_tmcpp0p28`
- Active finger: `middle`
- Score: `16.5903`
- Status: `PASS` / `success_true_pinch_lift_release_ball`
- Max transient lift: `0.16101 m`
- Hold lift max: `0.16101 m`
- Hold lift mean: `0.15656 m`
- Hold true two-tip fraction: `0.900`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`
- Visual contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_stage3_11d_b_ball_true_pinch_release_v0\thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p35_tmcpp0p28_contact_sheet.png`

## Top Candidates

| rank | candidate | active | status | score | hold lift | transient lift | two-tip | wrap | non-tip | release | reason |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p35_tmcpp0p28` | `middle` | PASS | 16.590 | 0.1610 | 0.1610 | 0.900 | 0.000 | 0.000 | `True` | `success_true_pinch_lift_release_ball` |
| 2 | `thumb_middle_tip_mu2p8_abdm0p65_pipm0p45_tabdm0p35_tmcpp0p28` | `middle` | FAIL | 3.195 | -0.0001 | 0.0736 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 3 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p45_tabdm0p50_tmcpp0p28` | `middle` | FAIL | 2.859 | -0.0001 | 0.0606 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 4 | `thumb_middle_tip_mu2p8_abdm0p65_pipm0p45_tabdm0p65_tmcpp0p28` | `middle` | FAIL | 2.192 | -0.0001 | 0.0393 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 5 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p50_tmcpp0p28` | `middle` | FAIL | 2.168 | -0.0001 | 0.0353 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 6 | `thumb_middle_tip_mu2p8_abdm0p85_pipm0p45_tabdm0p35_tmcpp0p28` | `middle` | FAIL | 1.633 | -0.0001 | 0.0188 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 7 | `thumb_middle_tip_mu2p8_abdm0p65_pipm0p70_tabdm0p35_tmcpp0p28` | `middle` | FAIL | 1.382 | -0.0001 | 0.0099 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 8 | `thumb_index_tip_mu2p8_abdm0p45_pipm0p45_tabdm0p50_tmcpp0p28` | `index` | FAIL | 1.332 | -0.0001 | 0.0099 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 9 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p45_tabdm0p50_tmcpp0p42` | `middle` | FAIL | 1.262 | -0.0001 | 0.0073 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 10 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p65_tmcpp0p28` | `middle` | FAIL | 1.225 | -0.0001 | 0.0061 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 11 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p50_tmcpp0p42` | `middle` | FAIL | 1.215 | -0.0001 | 0.0048 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 12 | `thumb_middle_tip_mu2p8_abdm0p65_pipm0p45_tabdm0p35_tmcpp0p42` | `middle` | FAIL | 1.202 | -0.0001 | 0.0045 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 13 | `thumb_index_tip_mu2p8_abdm0p45_pipm0p45_tabdm0p35_tmcpp0p28` | `index` | FAIL | 1.186 | -0.0001 | 0.0051 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 14 | `thumb_middle_tip_mu2p8_abdm0p65_pipm0p45_tabdm0p50_tmcpp0p28` | `middle` | FAIL | 1.182 | -0.0001 | 0.0033 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 15 | `thumb_index_tip_mu2p8_abdm0p85_pipm0p45_tabdm0p65_tmcpp0p28` | `index` | FAIL | 1.090 | -0.0001 | 0.0022 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 16 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p45_tabdm0p35_tmcpp0p42` | `middle` | FAIL | 1.079 | -0.0001 | 0.0033 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 17 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p45_tabdm0p35_tmcpp0p28` | `middle` | FAIL | 1.068 | -0.0001 | 0.0018 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 18 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p95_tabdm0p35_tmcpp0p28` | `middle` | FAIL | 1.054 | -0.0001 | 0.0029 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 19 | `thumb_middle_tip_mu2p8_abdm0p65_pipm0p45_tabdm0p50_tmcpp0p42` | `middle` | FAIL | 1.046 | -0.0001 | 0.0016 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |
| 20 | `thumb_middle_tip_mu2p8_abdm0p45_pipm0p95_tabdm0p65_tmcpp0p28` | `middle` | FAIL | 1.035 | -0.0001 | 0.0012 | 0.000 | 0.000 | 0.000 | `True` | `lift_gate_failed` |

## Next

- If a full success appears, promote it only as a Stage3.11D-B true-pinch-release candidate after visual review and randomized pose checks.
- If lift succeeds but morphology fails, continue morphology/material/approach search before neural training.
- If true two-tip frames remain zero, treat current proxy geometry/approach orientation as the blocker and add a geometry/material branch.
