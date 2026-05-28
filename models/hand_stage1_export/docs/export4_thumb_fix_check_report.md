# Export4 Thumb Fix Check Report

- Source: `D:\tendon_project\hardwares\hand\hand_export4`
- Imported to: `D:\tendon_project\simulations\models\hand_stage1_export\export4`
- URDF: `D:\tendon_project\simulations\models\hand_stage1_export\export4\urdf\hand_export4.urdf`
- Mesh dir: `D:\tendon_project\simulations\models\hand_stage1_export\export4\meshes`
- Generated hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4.xml`
- Generated scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4.xml`

## Thumb Chain

| Joint | Parent | Child | Axis | Origin xyz | Origin norm (m) | Limit |
|---|---|---|---|---|---:|---|
| `thumb_root_connector_fixed_joint` | `palm_link` | `thumb_root_connector_link` | `0 0 0` | `0.0064687769 0.019331857 -0.016418226` | 0.026175 | `None` |
| `thumb_cmc_abd_joint` | `thumb_root_connector_link` | `thumb_trapezium1_link` | `0 0 -1` | `-6.3364e-05 0.00012377 -0.011586` | 0.011587 | `{'lower': '-1.2', 'upper': '1.2', 'effort': '1', 'velocity': '1'}` |
| `thumb_cmc_joint` | `thumb_trapezium1_link` | `thumb_metacarpal_link` | `0 0 -1` | `0 0 0` | 0.000000 | `{'lower': '-1.2', 'upper': '1.2', 'effort': '1', 'velocity': '1'}` |
| `thumb_mcp_joint` | `thumb_metacarpal_link` | `thumb_proximal_link` | `0 0 -1` | `-0.016224 0.049404 -0.000175` | 0.052000 | `{'lower': '-0.2', 'upper': '1.4', 'effort': '1', 'velocity': '1'}` |
| `thumb_ip_joint` | `thumb_proximal_link` | `thumb_distal_link` | `0 0 1` | `-0.0033345 0.031826 -0.000105` | 0.032000 | `{'lower': '-0.2', 'upper': '1.2', 'effort': '1', 'velocity': '1'}` |

## MuJoCo Load

- Load success: True
- Bodies / joints / actuators / geoms / sites / meshes: 26 / 23 / 22 / 50 / 5 / 24

## Thumb Body Distances

| From | To | Distance (m) |
|---|---|---:|
| `palm_link` | `thumb_root_connector_link` | 0.026175 |
| `thumb_root_connector_link` | `thumb_trapezium1_link` | 0.011587 |
| `thumb_trapezium1_link` | `thumb_metacarpal_link` | 0.000000 |
| `thumb_metacarpal_link` | `thumb_proximal_link` | 0.052000 |
| `thumb_proximal_link` | `thumb_distal_link` | 0.032000 |

## Visual Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb\thumb_root_front.png` camera=`thumb_root_front` mean_pixel=51.21
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb\thumb_root_high.png` camera=`thumb_root_high` mean_pixel=82.00
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb\thumb_root_side.png` camera=`thumb_root_side` mean_pixel=60.26
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb\full_hand.png` camera=`full_hand` mean_pixel=45.30
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb\thumb_motion_open.png` camera=`thumb_root_front` mean_pixel=56.39
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_thumb\thumb_motion_combined.png` camera=`thumb_root_front` mean_pixel=54.72

## Visual Conclusion

- PASS for the specific export3 failure: the thumb no longer appears separated/suspended from the palm/root in the checked open pose.
- PASS for a small motion sanity check: after commanding `thumb_cmc_abd_joint=-0.6`, `thumb_cmc_joint=0.6`, `thumb_mcp_joint=0.5`, `thumb_ip_joint=0.25`, the thumb visual mesh moves as a continuous chain rather than splitting into distant floating parts.
- The second CMC joint is present but named `thumb_cmc_joint`, not `thumb_cmc_flex_joint`; downstream scripts should be updated to accept this export4 name.
- The zero translation at `thumb_cmc_joint` should be manually confirmed as intended. It may be acceptable if the second CMC rotation center is coincident with the `thumb_trapezium1_link` frame, but this should not be assumed silently.

## Interpretation

- Export4 keeps a 2-DoF CMC chain, but the second CMC joint is named `thumb_cmc_joint`, not `thumb_cmc_flex_joint`.
- The previous 0.13-0.15 m thumb body separation is fixed at the body/joint level.
- `thumb_cmc_joint` now has zero translation from `thumb_trapezium1_link` to `thumb_metacarpal_link`; visually verify whether this is intended or whether the joint center is coincident by design.
- The saved renders show the thumb visual STL pieces attached well enough to continue export4 MuJoCo scripted checks.
