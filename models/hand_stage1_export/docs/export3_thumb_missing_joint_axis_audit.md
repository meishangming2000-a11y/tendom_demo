# Export3 Thumb Missing-Joint And Axis Audit

Status: diagnostic report. No CAD/STL/tree/name edits were made.

- URDF: `D:\tendon_project\simulations\models\hand_stage1_export\export3\urdf\hand_export3.urdf`
- MJCF scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_thumb_limit_tuned.xml`
- Axis test angle: `0.6` rad

## Actual Export3 Thumb Chain

| Parent | Joint | Type | Axis | Origin xyz | Origin rpy | Child |
|---|---|---|---|---|---|---|
| `palm_link` | `thumb_root_connector_fixed_joint` | `fixed` | `0 0 0` | `0.00646877694946816 0.0193318572130217 -0.0164182261940455` | `-1.25378447702592 0.117658476534027 2.43554294725702` | `thumb_root_connector_link` |
| `thumb_root_connector_link` | `thumb_cmc_abd_joint` | `revolute` | `-0.95043 -0.31095 0` | `-6.3364E-05 0.00012377 -0.011586` | `-1.5515 -0.31614 -1.8718` | `thumb_trapezium1_link` |
| `thumb_trapezium1_link` | `thumb_cmc_flex_joint` | `revolute` | `-0.70578 0.7006 0.105` | `0.022854 0.085965 0.12154` | `-1.7196 -0.78353 1.6123` | `thumb_metacarpal_link` |
| `thumb_metacarpal_link` | `thumb_mcp_joint` | `revolute` | `0 0 -1` | `-0.11064 0.054899 0.049241` | `2.5976 1.4478 1.8125` | `thumb_proximal_link` |
| `thumb_proximal_link` | `thumb_ip_joint` | `revolute` | `0 0 1` | `-0.0033345 0.031826 -0.000105` | `0 0 3.1416` | `thumb_distal_link` |

## Missing-Joint Finding

- Thumb-related links exported: `['thumb_root_connector_link', 'thumb_trapezium1_link', 'thumb_metacarpal_link', 'thumb_proximal_link', 'thumb_distal_link']`
- Thumb active revolute/continuous joint count: `4`
- Thumb fixed joint count: `1`
- Export3 has one fixed root connector plus four active thumb joints: CMC abd, CMC flex, MCP, IP.
- If the real SolidWorks thumb root should contain another active joint between palm/root connector and `thumb_trapezium1_link`, it is absent from export3 URDF/MJCF.
- There is no exported link between `thumb_root_connector_link` and `thumb_trapezium1_link` other than `thumb_cmc_abd_joint`.

## Axis Direction Audit

| Joint | + angle thumb-ball delta | - angle thumb-ball delta | + toward ball? | - toward ball? | + thumb-index delta | - thumb-index delta |
|---|---:|---:|---|---|---:|---:|
| `thumb_cmc_abd_joint` | 0.047794 | -0.060895 | False | True | 0.063612 | -0.057888 |
| `thumb_cmc_flex_joint` | 0.011681 | -0.012889 | False | True | 0.002484 | 0.004322 |
| `thumb_mcp_joint` | -0.002738 | 0.000046 | True | False | 0.005420 | 0.000514 |
| `thumb_ip_joint` | -0.001079 | -0.000471 | True | True | 0.001115 | 0.000197 |

## Rendered Evidence

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\baseline_thumb_root.png` camera=`thumb_root_closeup` mean_pixel=65.99
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_cmc_abd_joint_positive_0d60.png` camera=`thumb_root_closeup` mean_pixel=66.80
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_cmc_abd_joint_negative_0d60.png` camera=`thumb_root_closeup` mean_pixel=61.38
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_cmc_flex_joint_positive_0d60.png` camera=`thumb_root_closeup` mean_pixel=65.05
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_cmc_flex_joint_negative_0d60.png` camera=`thumb_root_closeup` mean_pixel=62.46
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_mcp_joint_positive_0d60.png` camera=`thumb_root_closeup` mean_pixel=65.99
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_mcp_joint_negative_0d60.png` camera=`thumb_root_closeup` mean_pixel=66.10
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_ip_joint_positive_0d60.png` camera=`thumb_root_closeup` mean_pixel=65.99
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_axis_audit\thumb_ip_joint_negative_0d60.png` camera=`thumb_root_closeup` mean_pixel=65.99

## Interpretation

- `thumb_cmc_abd_joint` is numerically reversed relative to the desired intuitive positive-opposition convention: negative angle moves the thumb toward the ball/index side.
- `thumb_cmc_flex_joint` also shows direction ambiguity and should be checked in SolidWorks against the intended flexion axis.
- `thumb_mcp_joint` was mechanically confirmed by the user, but export3 still needs sign convention confirmation because a negative MCP value was selected by the tuned scripted pose.
- The likely missing item is not a mesh file; it is a missing active root/CMC degree of freedom or a missing exported intermediate moving link at the thumb base.
- Do not fix this by more target tuning. The next correct step is SolidWorks joint/CSYS/export correction or an explicitly named experimental MJCF with axis-sign flips for visualization only.

## SolidWorks / Export4 Checklist

1. Confirm whether there should be an additional active thumb root joint between `thumb_root_connector_link` and `thumb_trapezium1_link`, or between `palm_link` and `thumb_root_connector_link`.
2. If yes, add/export a distinct link and joint name, for example `thumb_cmc_root_joint` / `thumb_cmc_root_link` or the CAD-native name you prefer.
3. Verify that `thumb_cmc_abd_joint` positive rotation should oppose toward palm/index. If so, flip the SolidWorks CSYS/axis so positive angle, not negative angle, gives opposition.
4. Verify `thumb_cmc_flex_joint` positive direction in SolidWorks; current export3 range originally blocked negative values and may still have reversed sign convention.
5. Re-export as export4 without overwriting export3, then rerun this audit and thumb opposition/grasp smoke tests.
