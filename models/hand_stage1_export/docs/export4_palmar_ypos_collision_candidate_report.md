# Export4 +Y Palmar Collision Candidate Report

Generated: 2026-05-26T02:10:29

## Scope

Experimental MJCF-only branch. CAD, STL, URDF joint tree, joint names, and frozen/current-baseline files were not modified.

## Changes

- Source hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_wrist2_collision_tuned.xml`
- Output hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_palmar_ypos_collision_candidate.xml`
- Output scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml`
- Default candidate ball: `[0.0, 0.08, 0.21]`
- Added fingertip collision sphere radius: `0.015` m

| finger | body | site | geom | pos | radius |
|---|---|---|---|---|---:|
| index | `index_distal_link` | `index_tip_site` | `index_tip_collision_proxy_sphere` | `0.011092007 0.025709199 -6.7060969e-05` | 0.0150 |
| little | `little_distal_link` | `little_tip_site` | `little_tip_collision_proxy_sphere` | `0.026961146 -0.0075560895 -4.619485e-05` | 0.0150 |
| middle | `middle_distal_link` | `middle_tip_site` | `middle_tip_collision_proxy_sphere` | `0.027301483 -0.006215095 -4.054405e-05` | 0.0150 |
| ring | `ring_distal_link` | `ring_tip_site` | `ring_tip_collision_proxy_sphere` | `0.026733217 -0.0083266507 -4.4813101e-05` | 0.0150 |
| thumb | `thumb_distal_link` | `thumb_tip_site` | `thumb_tip_collision_proxy_sphere` | `0.00052061935 -0.027995157 -1.2280723e-05` | 0.0150 |

## Rationale

- Prior diagnostics show the default `-Y` ball side is far from the closing fingertips.
- The mirror/+Y side is visually closer but still lacked contact with conservative capsule-only proxy.
- This branch adds only local fingertip spheres instead of inflating palm or whole-finger collision geoms.
- TODO: promote only if regression shows improved contact without open-pose penetration.
