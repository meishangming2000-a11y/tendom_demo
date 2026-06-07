# Stage3 Sensor Abstraction V0 Report

Generated: 2026-06-03T21:20:54

- Status: **PASS**
- Task: `stage3_sensor_aware_gentle_grasp_hold`
- Contract: `stage3_sensor_aware_gentle_grasp_hold_v0`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Seed: `80`
- Observation dim: `130`

## Checks

- scene_exists: `True`
- same_key_reconstructs_across_api_instances: `True`
- same_key_reconstructs_after_other_keys: `True`
- different_step_changes_vision_pose: `True`
- different_episode_changes_vision_pose: `True`
- sensor_field_ranges_pass: `True`
- policy_vector_excludes_gt: `True`

## Replay Errors

- Same key across API instances max error: `0.000e+00`
- Same key after other keys max error: `0.000e+00`
- Next-step vision pose delta: `2.724e-03`
- Other-episode vision pose delta: `3.908e-03`

## Sensor Config

- Base seed: `80`
- Replay key: `sha256(base_seed, episode_id, step_index, stream)`
- Vision config: `{"pose_noise_std_m": 0.002, "axis_noise_std": 0.01, "shape_noise_std_m": 0.001, "confidence_nominal": 0.95, "occlusion": 0.0, "latency_steps": 2}`
- Tactile config: `{"slip_tangential_scale_mps": 0.12, "slip_downward_scale_mps": 0.08, "grip_stable_min_persistence_steps": 30, "release_max_hand_contacts": 0}`

## Boundary

This validates replay-safe simulated sensor abstractions only. It does not validate a scripted expert, dataset collection, real camera, real tactile sensor, ultrasound hardware, or real-hand integration.
