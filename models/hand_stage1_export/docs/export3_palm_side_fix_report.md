# Export3 Palm-Side Fix Report

## Summary

- User visual check indicates the previous ball side was the anatomical dorsal/back side.
- This fix keeps CAD, STL files, link tree, joint names, and original export3 files unchanged.
- New hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3_palm_side_fixed.xml`
- New scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_palm_side_fixed.xml`
- Corrected ball position: `[0.0, 0.045, 0.22]`

## Sim-Side Changes

- Ball moved from the old dorsal-side `Y=-0.1` scene to the corrected visual palm-side position `Y=+0.045`.
- The long-finger closure axes below were negated in the corrected MJCF so the existing positive flexion targets close toward the corrected palm side.
- `*_mcp_flex_joint` is left unchanged because it is being used as lateral/spread control in the current scripted policy.

| Joint | Old axis | New axis |
|---|---|---|
| `index_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` |
| `index_pip_joint` | `0.109773553624728 -0.0483929965230635 -0.992777862772996` | `-0.109773553625 0.0483929965231 0.992777862773` |
| `index_dip_joint` | `0 0 -1` | `-0 -0 1` |
| `middle_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` |
| `middle_pip_joint` | `0 0 -1` | `-0 -0 1` |
| `middle_dip_joint` | `0 0 -1` | `-0 -0 1` |
| `ring_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` |
| `ring_pip_joint` | `0 0 -1` | `-0 -0 1` |
| `ring_dip_joint` | `0 0 -1` | `-0 -0 1` |
| `little_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` |
| `little_pip_joint` | `0 0 -1` | `-0 -0 1` |
| `little_dip_joint` | `0 0 -1` | `-0 -0 1` |

## Notes

- This is an experimental simulation-side orientation fix, not a CAD or URDF source edit.
- If this visually matches the anatomical palm side, export4 should add explicit palm/dorsal reference CSYS markers so future scripts do not infer the wrong side.
- Thumb target tuning remains paused; this fix only addresses ball side and long-finger close direction.
