# Export4 Task API Report

Generated: 2026-05-26T01:59:58

## Scope

Minimal task API scaffold for the export4 tuned experimental scene. This is not a Gym wrapper, and no training is performed.

## Model

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Bodies: `26`
- Joints: `23`
- Actuators/action dim: `22`
- Geoms: `50`
- Sites: `5`
- Observation vector dim: `112`

## Interface

- `load_model(scene_path)`
- `reset_hand_open()`
- `set_ball_pose(x, y, z)`
- `get_joint_names()`
- `get_actuator_names()`
- `get_action_dim()`
- `apply_action(action)`
- `get_observation()`
- `get_fingertip_positions()`
- `get_ball_pose()`
- `get_contact_summary()`
- `compute_fingertip_ball_distances()`
- `step(n=1)`
- `render_or_save_frame_if_available()`

## Notes

- `*_mcp_flex_joint` names are preserved but semantically treated as lateral spread / abduction-adduction for now.
- The API is suitable for scripted smoke tests and adapter work, not training readiness.
- TODO: finalize canonical palmar ball side before expanding dataset collection.
