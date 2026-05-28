# Arm-Hand Stage1 Task API Report

Generated: 2026-05-28T19:47:19

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Scene role: `v2_ball`
- Baseline version: `collision_proxy_v2`
- Model summary: `{'nbody': 32, 'njnt': 27, 'nu': 26, 'ngeom': 67, 'nsite': 14, 'nmesh': 29, 'nq': 33, 'nv': 32}`
- Action dim: `26`
- Observation dim: `124`
- Default ball position: `[0.0213343049, 0.145570505, 0.518815052]`
- Open contact count: `1`
- Open max penetration: `0.000500 m`

## Task Contract

- Task name: `arm_hand_stage1_lift_ball`
- Contract version: `stage2_lift_ball_v0_1`
- Max episode steps: `1230`
- Training ready: **No**

## Schema

- Action schema: `{"type": "position_target_vector", "dim": 26, "entries": [{"index": 0, "actuator": "a_j1", "joint": "j1", "ctrl_limited": true, "ctrlrange": [-3.1416, 3.1416]}, {"index": 1, "actuator": "a_j2", "joint": "j2", "ctrl_limited": true, "ctrlrange": [-1.5708, 1.5708]}, {"index": 2, "actuator": "a_j3", "joint": "j3", "ctrl_limited": true, "ctrlrange": [-1.5708, 1.5708]}, {"index": 3, "actuator": "a_j4", "joint": "j4", "ctrl_limited": true, "ctrlrange": [-3.1416, 3.1416]}, {"index": 4, "actuator": "wrist_1_joint_pos", "joint": "wrist_1_joint", "ctrl_limited": true, "ctrlrange": [-0.8, 0.8]}, {"index": 5, "actuator": "wrist_2_joint_pos", "joint": "wrist_2_joint", "ctrl_limited": true, "ctrlrange": [-0.8, 0.8]}, {"index": 6, "actuator": "index_mcp_flex_joint_pos", "joint": "index_mcp_flex_joint", "ctrl_limited": true, "ctrlrange": [-0.3, 0.18]}, {"index": 7, "actuator": "index_mcp_abd_joint_pos", "joint": "index_mcp_abd_joint", "ctrl_limited": true, "ctrlrange": [-0.78, 0.08]}, {"index": 8, "actuator": "index_pip_joint_pos", "joint": "index_pip_joint", "ctrl_limited": true, "ctrlrange": [-1.1, 0.04]}, {"index": 9, "actuator": "index_dip_joint_pos", "joint": "index_dip_joint", "ctrl_limited": true, "ctrlrange": [-0.66, 0.04]}, {"index": 10, "actuator": "middle_mcp_flex_joint_pos", "joint": "middle_mcp_flex_joint", "ctrl_limited": true, "ctrlrange": [-0.3, 0.18]}, {"index": 11, "actuator": "middle_mcp_abd_joint_pos", "joint": "middle_mcp_abd_joint", "ctrl_limited": true, "ctrlrange": [-0.86, 0.08]}, {"index": 12, "actuator": "middle_pip_joint_pos", "joint": "middle_pip_joint", "ctrl_limited": true, "ctrlrange": [-1.16, 0.04]}, {"index": 13, "actuator": "middle_dip_joint_pos", "joint": "middle_dip_joint", "ctrl_limited": true, "ctrlrange": [-0.7, 0.04]}, {"index": 14, "actuator": "ring_mcp_flex_joint_pos", "joint": "ring_mcp_flex_joint", "ctrl_limited": true, "ctrlrange": [-0.3, 0.18]}, {"index": 15, "actuator": "ring_mcp_abd_joint_pos", "joint": "ring_mcp_abd_joint", "ctrl_limited": true, "ctrlrange": [-0.84, 0.08]}, {"index": 16, "actuator": "ring_pip_joint_pos", "joint": "ring_pip_joint", "ctrl_limited": true, "ctrlrange": [-1.1, 0.04]}, {"index": 17, "actuator": "ring_dip_joint_pos", "joint": "ring_dip_joint", "ctrl_limited": true, "ctrlrange": [-0.68, 0.04]}, {"index": 18, "actuator": "little_mcp_flex_joint_pos", "joint": "little_mcp_flex_joint", "ctrl_limited": true, "ctrlrange": [-0.28, 0.16]}, {"index": 19, "actuator": "little_mcp_abd_joint_pos", "joint": "little_mcp_abd_joint", "ctrl_limited": true, "ctrlrange": [-0.76, 0.08]}, {"index": 20, "actuator": "little_pip_joint_pos", "joint": "little_pip_joint", "ctrl_limited": true, "ctrlrange": [-1.0, 0.04]}, {"index": 21, "actuator": "little_dip_joint_pos", "joint": "little_dip_joint", "ctrl_limited": true, "ctrlrange": [-0.62, 0.04]}, {"index": 22, "actuator": "thumb_cmc_abd_joint_pos", "joint": "thumb_cmc_abd_joint", "ctrl_limited": true, "ctrlrange": [-1.05, 1.05]}, {"index": 23, "actuator": "thumb_cmc_joint_pos", "joint": "thumb_cmc_joint", "ctrl_limited": true, "ctrlrange": [-0.95, 0.95]}, {"index": 24, "actuator": "thumb_mcp_joint_pos", "joint": "thumb_mcp_joint", "ctrl_limited": true, "ctrlrange": [-0.1, 1.2]}, {"index": 25, "actuator": "thumb_ip_joint_pos", "joint": "thumb_ip_joint", "ctrl_limited": true, "ctrlrange": [-0.85, 0.05]}]}`
- Observation schema: `{"type": "flat_vector", "dim": 124, "finger_order": ["index", "middle", "ring", "little", "thumb"], "scalar_names": ["contact_count", "max_penetration", "ball_hand_contact_count", "ball_arm_contact_count", "index_tip_ball_distance", "middle_tip_ball_distance", "ring_tip_ball_distance", "little_tip_ball_distance", "thumb_tip_ball_distance"], "slices": {"qpos": {"start": 0, "stop": 33, "length": 33}, "qvel": {"start": 33, "stop": 65, "length": 32}, "ctrl": {"start": 65, "stop": 91, "length": 26}, "fingertip_positions_xyz": {"start": 91, "stop": 106, "length": 15}, "ball_position_xyz": {"start": 106, "stop": 109, "length": 3}, "ball_velocity_6d": {"start": 109, "stop": 115, "length": 6}, "contact_and_distance_scalars": {"start": 115, "stop": 124, "length": 9}}}`

## Interface

- `load_model(scene_path)`
- `load_current_baseline(scene_role='v2_ball')`
- `reset_hand_open()`
- `set_ball_pose(x, y, z)`
- `set_ball_pose_world(position, quat=None)`
- `set_ball_pose_body_local(body_name, local_xyz)`
- `world_from_body_local(body_name, local_xyz)`
- `get_joint_names()`
- `get_actuator_names()`
- `get_action_schema()`
- `get_observation_schema()`
- `get_action_dim()`
- `apply_action(action)`
- `action_from_targets(targets)`
- `targets_from_current_qpos()`
- `step_action(action, n=1, pin_ball=False)`
- `get_observation()`
- `get_fingertip_positions()`
- `get_ball_pose()`
- `get_contact_summary()`
- `compute_fingertip_ball_distances()`
- `step(n=1, pin_ball=True)`

## Notes

- This is an adapter scaffold, not a training environment.
- Default loading now targets collision proxy v2 with ball; legacy physics-v0 scenes remain available by explicit path.
- Observation includes qpos, qvel, ctrl, fingertip positions, ball pose/velocity, contact summary, and fingertip-ball distances.
- Current `*_mcp_flex_joint` names are preserved; semantic aliases should be handled above this API.
