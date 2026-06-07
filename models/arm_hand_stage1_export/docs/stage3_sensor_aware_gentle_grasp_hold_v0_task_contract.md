# Stage3 Sensor-Aware Gentle Grasp/Hold Task Contract

Generated: 2026-06-03T21:27:11

- Task name: `stage3_sensor_aware_gentle_grasp_hold`
- Contract version: `stage3_sensor_aware_gentle_grasp_hold_v0`
- Stage: `stage3_sensor_aware_mujoco_manipulation`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Training ready: **False**
- MuJoCo only: **True**
- Hardware integration: **False**

## Object

- Body: `egg`
- Shape: `ellipsoid`
- Shape params XYZ m: `[0.022, 0.032, 0.038]`
- Default position XYZ: `[0.19022382, 0.187702, -0.05538044]`

## Phases

- `default_hold`
- `vision_acquire`
- `approach`
- `pre_contact_align`
- `gentle_close`
- `contact_settle`
- `grasp_secure_check`
- `lift`
- `hold`
- `slip_recover_or_abort`
- `release_or_reset`

## Sensor Observation

- `vision.object_pose_xyz_est`
- `vision.object_axis_est`
- `vision.object_shape_params_est`
- `vision.goal_pose_xyz_est`
- `vision.object_to_goal_est`
- `vision.confidence`
- `vision.occlusion`
- `vision.latency_steps`
- `vision.noise_std`
- `tactile.contact_present`
- `tactile.contact_regions`
- `tactile.normal_contact_proxy`
- `tactile.contact_persistence`
- `tactile.relative_tangential_motion`
- `tactile.slip_score`
- `tactile.grip_stable`
- `tactile.crush_risk`
- `tactile.release_contact_clear`

## Sensor Abstraction

- Version: `stage3_sensor_abstraction_v0`
- Requirements doc: `docs/stage3_sensor_requirements_v0.md`
- Replay safe: **True**
- Replay key: `sha256(base_seed, episode_id, step_index, stream)`
- Base seed: `0`
- Policy input boundary: sensor abstractions only; ground-truth fields are logging/eval/replay QA only.

## Success Contract

- object_lift_height >= 0.05 m
- hold_duration_s >= 3.0 s
- object_pose_drift_xy <= success_max_pose_drift_m
- slip_score <= success_max_slip_score
- crush_risk <= success_max_crush_risk
- max_penetration <= success_max_penetration_m
- finite_state is true

## Failure Reasons

- `running`
- `success_gentle_grasp_hold`
- `non_finite_state`
- `premature_object_push`
- `no_contact_timeout`
- `grasp_not_secure`
- `slip_detected`
- `object_dropped`
- `crush_risk_exceeded`
- `excessive_penetration`
- `bad_vision_confidence`
- `unstable_hold`
- `timeout`

## Boundary

- Stage3 uses simulated vision and synthetic tactile/slip abstractions only.
- Ground-truth MuJoCo object state may be logged for labels, replay QA, and evaluation, but is not the default learned-policy input.
- This contract does not claim a scripted expert, dataset, replay QA, trained policy, or hardware readiness yet.
