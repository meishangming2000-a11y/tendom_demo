# Export4 Current Baseline Collision Proxy Audit

Generated: 2026-05-25 14:57:12

Ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_current_baseline.xml`

Status: `PASS_FOR_SMOKE_NEEDS_TRAINING_PROXY_TUNING`

Visual sheet: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_current_baseline_audit\collision\collision_audit_stage_sheet.png`

## Proxy Summary

- collision proxy geom count: `24`
- collision-enabled mesh geom count: `0`
- visual geoms accidentally collision-enabled: `0`

## Stage Contact Summary

| stage | contacts | ball-hand | ball-ground | max hand-ball penetration | thumb-ball | index-ball | middle-ball |
|---|---:|---:|---:|---:|---:|---:|---:|
| open_ball | 0 | 0 | 0 | 0.00000 | 0.0517 | 0.1058 | 0.1210 |
| preshape_ball | 0 | 0 | 0 | 0.00000 | 0.0517 | 0.0569 | 0.0654 |
| four_fingers_closed_ball | 5 | 5 | 0 | 0.01099 | 0.0517 | 0.0293 | 0.0245 |
| thumb_visual_close_ball | 6 | 6 | 0 | 0.01298 | 0.0182 | 0.0293 | 0.0245 |

## Issues

| severity | item | detail |
|---|---|---|
| MAJOR | `closed_ball_proxy_penetration` | Closed static ball check has hand-ball penetration above 8 mm. Acceptable for visual smoke, too high for contact-rich training. |

## Interpretation

- Clean STL remains visual-only; collision relies on primitive proxy geoms.
- Stage checks are static pose checks that keep the free ball at its XML initial pose; dynamic ball-gravity behavior is not audited here.
- Passing this audit means the proxy is usable for smoke tests, not final contact-rich training.
