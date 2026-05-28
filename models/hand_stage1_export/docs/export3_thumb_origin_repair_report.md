# Export3 Thumb Origin Repair Report

## Summary

- This is a temporary MJCF-only repair for visual/kinematic debugging.
- CAD, STL files, URDF, link names, joint names, and joint tree were not changed.
- Source hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3_palm_side_fixed.xml`
- Repaired hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3_thumb_origin_repaired.xml`
- Repaired scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_thumb_origin_repaired.xml`

## Why

- `thumb_cmc_flex_joint` was exported with an adjacent-body offset of about `0.1506 m`.
- `thumb_mcp_joint` was exported with an adjacent-body offset of about `0.1330 m`.
- Those values make the thumb appear separated/suspended in the viewer.
- After the body-origin repair, `thumb_metacarpal_link` still had a large visual mesh offset, so only its visual geom was shifted back to the repaired collision-proxy region.

## Changes

| Element | Old | New |
|---|---|---|
| `body thumb_metacarpal_link pos` | `0.022854 0.085965 0.12154` | `0.002731 0.010273 0.014527` |
| `geom thumb_trapezium1_link_collision_proxy fromto` | `0 0 0 0.022854 0.085965 0.12154` | `0 0 0 0.002731 0.010273 0.014527` |
| `body thumb_proximal_link pos` | `-0.11064 0.054899 0.049241` | `-0.016224 0.049404 -0.000175` |
| `geom thumb_metacarpal_link_collision_proxy fromto` | `0 0 0 -0.11064 0.054899 0.049241` | `0 0 0 -0.016224 0.049404 -0.000175` |
| `geom thumb_metacarpal_link_export3_visual pos` | `0 0 0` | `0.119732 -0.014053 -0.039847` |

## Status

- Use this only to continue simulation smoke testing.
- For final mechanical truth, fix the SolidWorks CSYS/origin for `thumb_cmc_flex_joint` and `thumb_mcp_joint` and re-export.
