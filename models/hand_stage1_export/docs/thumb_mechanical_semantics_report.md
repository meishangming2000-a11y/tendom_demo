# Thumb Mechanical Semantics Report

- MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_visual_clean_collision_proxy.xml`
- URDF: `D:\tendon_project\simulations\models\hand_stage1_export\robot.urdf`
- Ball position used for audit: `[0.0, -0.1, 0.195]`

## Expected Thumb Chain

| Joint | Expected parent | Expected child | URDF parent/child/type | MJCF parent/child/type | Status |
|---|---|---|---|---|---|
| `thumb_root_connector_fixed_joint` | `palm_link` | `thumb_root_connector_link` | `palm_link -> thumb_root_connector_link (fixed)` | `palm_link -> thumb_root_connector_link (fixed_implicit_body_parent)` | OK |
| `thumb_cmc_joint` | `thumb_root_connector_link` | `thumb_metacarpal_link` | `thumb_root_connector_link -> thumb_metacarpal_link (revolute)` | `thumb_root_connector_link -> thumb_metacarpal_link (hinge)` | OK |
| `thumb_mcp_joint` | `thumb_metacarpal_link` | `thumb_proximal_link` | `thumb_metacarpal_link -> thumb_proximal_link (revolute)` | `thumb_metacarpal_link -> thumb_proximal_link (hinge)` | OK |
| `thumb_ip_joint` | `thumb_proximal_link` | `thumb_distal_link` | `thumb_proximal_link -> thumb_distal_link (revolute)` | `thumb_proximal_link -> thumb_distal_link (hinge)` | OK |

## Joint Axes And Positive Motion

| Joint | Local axis | World axis at zero | +angle | delta thumb tip | delta dist to ball | delta dist to index | delta dist to palm |
|---|---|---|---:|---:|---:|---:|---:|
| `thumb_cmc_joint` | `[0.0, 0.0, -1.0]` | `[-0.220760124602412, 0.7996951023075736, -0.5583481984665188]` | 0.200 | 0.022174 | 0.001121 | 0.002016 | -0.002931 |
| `thumb_mcp_joint` | `[0.0, 0.0, -1.0]` | `[-0.220760124602412, 0.7996951023075736, -0.5583481984665188]` | 0.200 | 0.011969 | -0.000607 | 0.000689 | -0.003382 |
| `thumb_ip_joint` | `[0.0, 0.0, 1.0]` | `[0.22076012460241204, -0.7996951023075736, 0.5583481984665188]` | 0.200 | 0.005591 | 0.000046 | 0.000092 | 0.001062 |

## Baseline Distances

- thumb to ball: 0.170603 m
- thumb to index: 0.130438 m
- thumb to palm: 0.144673 m

## Interpretation

- Positive motion of each individual thumb joint does not move thumb_tip_site meaningfully toward the ball.
- Most likely issue to inspect first: thumb_cmc_joint axis/body frame, because CMC should provide the main opposition sweep.
- Do not automatically flip axes from this report; confirm axis/csys in SolidWorks/URDF first.

## TODO

- Verify `thumb_cmc_axis` and `thumb_cmc_csys` in SolidWorks first.
- Verify whether the CMC joint has enough modeled DOF for opposition, or if one axis is missing in stage1.
- Verify that the thumb root connector body frame is not rotated so the CMC axis points along the wrong local direction.
- Keep joint names and axes unchanged until the CAD/URDF semantics are confirmed.
