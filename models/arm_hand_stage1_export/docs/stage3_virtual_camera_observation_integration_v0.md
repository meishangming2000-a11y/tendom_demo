# Stage3.3 Virtual-Camera Observation Integration V0

Generated: 2026-06-04T18:32:42

- Status: `PASS`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`

## Checks

- clean_sensor_validation_pass: `True`
- noisy_sensor_validation_pass: `True`
- clean_vision_source_virtual_camera: `True`
- noisy_vision_source_virtual_camera: `True`
- clean_vector_dim_matches_schema: `True`
- noisy_vector_dim_matches_schema: `True`
- clean_pose_matches_sensor: `True`
- noisy_confidence_below_clean: `True`
- noisy_occlusion_positive: `True`
- policy_boundary_not_hardware: `True`

## Clean Observation

- Source: `virtual_camera`
- Confidence: `0.983`
- Occlusion: `0.000`
- Vector dim: `130`

## Noisy Observation

- Source: `virtual_camera`
- Confidence: `0.514`
- Occlusion: `0.553`
- Accepted update: `False`

## Interpretation

- The task API can now expose rendered virtual-camera perception as policy-visible vision fields.
- Ground truth remains available only for evaluation/logging unless explicitly passed as the old replay-safe abstraction path.
