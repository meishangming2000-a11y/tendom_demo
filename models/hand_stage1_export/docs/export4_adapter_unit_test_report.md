# Export4 Adapter Unit Test Report

Generated: 2026-05-26T02:09:11

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Status: **PASS**
- Action dim: `22`
- Obs dim: `86`
- wrist_2 in action mapping: `True`

## Tests

| test | pass | detail |
|---|---:|---|
| `joint_name_list_nonempty` | True | `23` |
| `actuator_name_list_nonempty` | True | `22` |
| `action_dim_equals_actuator_count` | True | `{'action_dim': 22, 'actuators': 22}` |
| `wrist_2_joint_in_joint_list` | True | `['wrist_1_joint', 'wrist_2_joint', 'index_mcp_flex_joint', 'index_mcp_abd_joint', 'index_pip_joint', 'index_dip_joint', 'little_mcp_flex_joint', 'little_mcp_abd_joint', 'little_pip_joint', 'little_dip_joint', 'middle_mcp_flex_joint', 'middle_mcp_abd_joint', 'middle_pip_joint', 'middle_dip_joint', 'ring_mcp_flex_joint', 'ring_mcp_abd_joint', 'ring_pip_joint', 'ring_dip_joint', 'thumb_cmc_abd_joint', 'thumb_cmc_joint', 'thumb_mcp_joint', 'thumb_ip_joint', 'ball_freejoint']` |
| `wrist_2_joint_in_action_mapping` | True | `['wrist_1_joint_pos', 'wrist_2_joint_pos', 'index_mcp_flex_joint_pos', 'index_mcp_abd_joint_pos', 'index_pip_joint_pos', 'index_dip_joint_pos', 'middle_mcp_flex_joint_pos', 'middle_mcp_abd_joint_pos', 'middle_pip_joint_pos', 'middle_dip_joint_pos', 'ring_mcp_flex_joint_pos', 'ring_mcp_abd_joint_pos', 'ring_pip_joint_pos', 'ring_dip_joint_pos', 'little_mcp_flex_joint_pos', 'little_mcp_abd_joint_pos', 'little_pip_joint_pos', 'little_dip_joint_pos', 'thumb_cmc_abd_joint_pos', 'thumb_cmc_joint_pos', 'thumb_mcp_joint_pos', 'thumb_ip_joint_pos']` |
| `obs_contains_qpos` | True | `{'obs_qpos': 29, 'model_nq': 29}` |
| `obs_contains_qvel` | True | `{'obs_qvel': 28, 'model_nv': 28}` |
| `obs_contains_fingertips` | True | `{'index_tip_site': 0, 'middle_tip_site': 2, 'ring_tip_site': 3, 'little_tip_site': 1, 'thumb_tip_site': 4}` |
| `obs_contains_ball_pose` | True | `[0.0, -0.1, 0.21, 1.0, 0.0, 0.0, 0.0]` |
| `obs_contains_contact_summary` | True | `{'contact_count': 0, 'max_penetration': 0.0, 'ball_hand_contact_count': 0, 'ball_hand_max_penetration': 0.0, 'source_counts': {}}` |
| `reset_qpos_consistent` | True | `0.0` |
| `scripted_target_writes_ctrl` | True | `{'ctrl_norm': 2.262719602602143}` |
| `obs_vector_stable_length` | True | `{'obs0': 86, 'obs1': 86}` |

## Notes

- This is an adapter smoke/unit test, not a learning experiment.
- Current unresolved grasp-side/contact issues are tracked separately in `collision_proxy_tuning_report.md`.
