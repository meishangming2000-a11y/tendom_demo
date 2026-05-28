# Export3 Thumb Limit Tuned Model Report

Status: experimental MJCF variant. Main export3 model is not overwritten.

- Source hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3.xml`
- Source scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Tuned hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3_thumb_limit_tuned.xml`
- Tuned scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_thumb_limit_tuned.xml`

## User-Confirmed Mechanical Semantics

- `D18d12H4.STEP` and `Trapezium3.STEP` are fixed root parts under `thumb_root_connector_link`.
- `Trapezium1.STEP` is the first moving CMC-abduction link: `thumb_trapezium1_link`.
- `Os metacarpale I 3.STEP` is after the second CMC joint: `thumb_metacarpal_link`.
- `thumb_cmc_abd_joint` must allow negative angles because negative direction improves opposition.
- `thumb_mcp_axis` has been confirmed mechanically credible in SolidWorks.

## Changed Joint Ranges

| Joint | Old range | New range |
|---|---:|---:|
| `thumb_cmc_abd_joint` | `-0.8 0.8` | `-1.2 1.2` |
| `thumb_cmc_flex_joint` | `0 1.2` | `-1.2 1.2` |
| `thumb_mcp_joint` | `0 1.2` | `-0.2 1.4` |
| `thumb_ip_joint` | `0 1.2` | `-0.2 1.2` |

## Changed Actuator Control Ranges

| Actuator | Joint | Old ctrlrange | New ctrlrange |
|---|---|---:|---:|
| `thumb_cmc_abd_joint_pos` | `thumb_cmc_abd_joint` | `-0.8 0.8` | `-1.2 1.2` |
| `thumb_cmc_flex_joint_pos` | `thumb_cmc_flex_joint` | `0 1.2` | `-1.2 1.2` |
| `thumb_mcp_joint_pos` | `thumb_mcp_joint` | `0 1.2` | `-0.2 1.4` |
| `thumb_ip_joint_pos` | `thumb_ip_joint` | `0 1.2` | `-0.2 1.2` |

## Constraints

- No CAD edits.
- No STL edits.
- No link tree edits.
- No joint renaming.
- No tendon routing or training.
- STL remains visual-only; collision remains primitive proxy.
