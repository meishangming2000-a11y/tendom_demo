# Export2 Grasp Direction Fix Report

- Source XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- Fixed XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_export2_graspfix.xml`
- Fixed scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_export2_graspfix.xml`
- Joint tree changed: False
- Joint names changed: False
- Flipped joint count: 15

## Flipped Flexion-Like Hinge Axes

| Joint | Old axis | New axis | Range |
|---|---|---|---|
| `index_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` | `-0.2 1.2` |
| `middle_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` | `-0.2 1.2` |
| `ring_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` | `-0.2 1.2` |
| `little_mcp_abd_joint` | `0 0 -1` | `-0 -0 1` | `-0.2 1.2` |
| `index_pip_joint` | `0.10977 -0.048393 -0.99278` | `-0.10977 0.048393 0.99278` | `0 1.57` |
| `middle_pip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.57` |
| `ring_pip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.57` |
| `little_pip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.57` |
| `index_dip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.2` |
| `middle_dip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.2` |
| `ring_dip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.2` |
| `little_dip_joint` | `0 0 -1` | `-0 -0 1` | `0 1.2` |
| `thumb_cmc_joint` | `0 0 -1` | `-0 -0 1` | `-0.8 0.8` |
| `thumb_mcp_joint` | `0 0 -1` | `-0 -0 1` | `0 1.2` |
| `thumb_ip_joint` | `0 0 1` | `-0 -0 -1` | `0 1.2` |

## Notes

- This is a diagnostic MJCF-only fix for the observed reversed grasp direction.
- The fix inverts flexion-like hinge axes while preserving positive scripted grasp targets.
- The four long-finger *_mcp_abd_joint entries are treated as MCP curl joints for this draft because flex/abd naming semantics remain suspect.
- Primitive collision geoms are retained; clean mesh geoms remain visual-only.
