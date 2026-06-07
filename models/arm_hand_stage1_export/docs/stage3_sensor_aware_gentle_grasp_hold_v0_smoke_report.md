# Stage3 Sensor-Aware Gentle Grasp/Hold Smoke Report

Generated: 2026-06-03T21:20:54

- Status: **PASS**
- Task: `stage3_sensor_aware_gentle_grasp_hold`
- Contract: `stage3_sensor_aware_gentle_grasp_hold_v0`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Action dim: `26`
- Observation dim: `130`

## Checks

- scene_exists: `True`
- scene_loads: `True`
- action_dim_positive: `True`
- observation_dim_positive: `True`
- vision_fields_present: `True`
- tactile_fields_present: `True`
- sensor_validation_pass: `True`
- contract_mujoco_only: `True`
- hardware_integration_false: `True`
- initial_eval_running: `True`

## Initial Evaluation

- Terminal reason: `running`
- Episode status: `running`
- Vision confidence: `0.934`
- Slip score: `0.000`
- Crush risk: `0.000`

## Boundary

This smoke check validates the Stage3 contract, scene load, and sensor abstraction schema only. Scripted expert, dataset collection, replay QA, and visual QA remain pending.
