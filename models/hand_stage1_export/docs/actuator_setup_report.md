# Actuator Setup Report

- Output hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_visual_clean_collision_proxy.xml`
- Output scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Compiled actuator count: 21
- Missing controlled joints: None

## Position Actuators

| Joint | Actuator | kp | ctrlrange |
|---|---|---:|---|
| `wrist_1_joint` | `wrist_1_joint_pos` | 5 | `[-0.8, 0.8]` |
| `wrist_2_joint` | `wrist_2_joint_pos` | 5 | `[-0.8, 0.8]` |
| `index_mcp_flex_joint` | `index_mcp_flex_joint_pos` | 3 | `[-0.5, 0.5]` |
| `index_mcp_abd_joint` | `index_mcp_abd_joint_pos` | 3 | `[-0.2, 1.2]` |
| `index_pip_joint` | `index_pip_joint_pos` | 2 | `[0.0, 1.57]` |
| `index_dip_joint` | `index_dip_joint_pos` | 2 | `[0.0, 1.2]` |
| `middle_mcp_flex_joint` | `middle_mcp_flex_joint_pos` | 3 | `[-0.5, 0.5]` |
| `middle_mcp_abd_joint` | `middle_mcp_abd_joint_pos` | 3 | `[-0.2, 1.2]` |
| `middle_pip_joint` | `middle_pip_joint_pos` | 2 | `[0.0, 1.57]` |
| `middle_dip_joint` | `middle_dip_joint_pos` | 2 | `[0.0, 1.2]` |
| `ring_mcp_flex_joint` | `ring_mcp_flex_joint_pos` | 3 | `[-0.5, 0.5]` |
| `ring_mcp_abd_joint` | `ring_mcp_abd_joint_pos` | 3 | `[-0.2, 1.2]` |
| `ring_pip_joint` | `ring_pip_joint_pos` | 2 | `[0.0, 1.57]` |
| `ring_dip_joint` | `ring_dip_joint_pos` | 2 | `[0.0, 1.2]` |
| `little_mcp_flex_joint` | `little_mcp_flex_joint_pos` | 3 | `[-0.5, 0.5]` |
| `little_mcp_abd_joint` | `little_mcp_abd_joint_pos` | 3 | `[-0.2, 1.2]` |
| `little_pip_joint` | `little_pip_joint_pos` | 2 | `[0.0, 1.57]` |
| `little_dip_joint` | `little_dip_joint_pos` | 2 | `[0.0, 1.2]` |
| `thumb_cmc_joint` | `thumb_cmc_joint_pos` | 2 | `[-0.8, 0.8]` |
| `thumb_mcp_joint` | `thumb_mcp_joint_pos` | 2 | `[0.0, 1.2]` |
| `thumb_ip_joint` | `thumb_ip_joint_pos` | 2 | `[0.0, 1.2]` |

## Notes

- Wrist kp=5, MCP kp=3, PIP/DIP kp=2, thumb kp=2.
- If runtime oscillation appears, lower kp before changing joint axes or limits.
- Actuators are for scripted position-control smoke tests only; no tendon routing or training is introduced.
