# Arm-Hand Stage1 Task API Report

Generated: 2026-05-27T09:15:24

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Model summary: `{'nbody': 32, 'njnt': 27, 'nu': 26, 'ngeom': 65, 'nsite': 14, 'nmesh': 29, 'nq': 33, 'nv': 32}`
- Action dim: `26`
- Observation dim: `124`
- Default ball position: `[0.0213343049, 0.145570505, 0.518815052]`
- Open contact count: `0`
- Open max penetration: `0.000000 m`

## Interface

- `load_model(scene_path)`
- `reset_hand_open()`
- `set_ball_pose(x, y, z)`
- `get_joint_names()`
- `get_actuator_names()`
- `get_action_dim()`
- `apply_action(action)`
- `action_from_targets(targets)`
- `get_observation()`
- `get_fingertip_positions()`
- `get_ball_pose()`
- `get_contact_summary()`
- `compute_fingertip_ball_distances()`
- `step(n=1, pin_ball=True)`

## Notes

- This is an adapter scaffold, not a training environment.
- Observation includes qpos, qvel, ctrl, fingertip positions, ball pose/velocity, contact summary, and fingertip-ball distances.
- Current `*_mcp_flex_joint` names are preserved; semantic aliases should be handled above this API.
