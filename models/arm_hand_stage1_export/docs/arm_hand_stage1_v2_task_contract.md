# Arm-Hand Stage1 V2 Task Contract

Generated: 2026-05-28T20:07:18

## Purpose

This document freezes the first Stage2 contract for the current arm+hand v2 lift-ball task. It defines what a future dataset row means, how a step is scored, and when an episode ends. No training is performed here.

## Contract Summary

- Task name: `arm_hand_stage1_lift_ball`
- Contract version: `stage2_lift_ball_v0_1`
- Baseline: `collision_proxy_v2`
- Recommended rollout scene: `lift_demo`
- Training ready: **No**

## Observation

- Type: `flat_vector`
- Dimension: `124`
- Slices: `{"qpos": {"start": 0, "stop": 33, "length": 33}, "qvel": {"start": 33, "stop": 65, "length": 32}, "ctrl": {"start": 65, "stop": 91, "length": 26}, "fingertip_positions_xyz": {"start": 91, "stop": 106, "length": 15}, "ball_position_xyz": {"start": 106, "stop": 109, "length": 3}, "ball_velocity_6d": {"start": 109, "stop": 115, "length": 6}, "contact_and_distance_scalars": {"start": 115, "stop": 124, "length": 9}}`
- Finger order: `["index", "middle", "ring", "little", "thumb"]`
- Scalar names: `["contact_count", "max_penetration", "ball_hand_contact_count", "ball_arm_contact_count", "index_tip_ball_distance", "middle_tip_ball_distance", "ring_tip_ball_distance", "little_tip_ball_distance", "thumb_tip_ball_distance"]`

Plain meaning: each observation records the model state, current controls, fingertip positions, ball pose/velocity, contact counts, penetration, and fingertip-ball distances.

## Action

- Type: `position_target_vector`
- Dimension: `26`
- Meaning: one position target per actuator, clipped by each actuator's control range.

## Reward

- Type: `candidate_shaping_reward_v0`
- Weights: `{"lift_height": 10.0, "hand_contact_bonus": 1.0, "floor_contact_after_lift_penalty": -2.0, "penetration_penalty": -50.0, "four_finger_distance_penalty": -0.5, "thumb_distance_penalty": -0.25, "success_bonus": 10.0, "failure_penalty": -10.0}`
- Positive terms: lift height, hand-ball contact, terminal success bonus.
- Negative terms: floor contact after lift, excessive penetration, large fingertip-ball distances, terminal failure penalty.
- Note: This reward is for dataset-v0 labeling and later training discussion; it is not a tuned RL reward.

## Done / Terminal Rules

- Max episode steps: `1230`
- Thresholds: `{"success_lift_height_m": 0.08, "success_min_ball_hand_contacts": 1, "success_max_ball_floor_contacts": 0, "success_max_penetration_m": 0.015, "failure_max_penetration_m": 0.03, "failure_ball_drop_below_start_m": 0.03, "dropped_after_lift_height_m": 0.03}`
- Success: ball is lifted high enough, still has hand contact, has no floor contact, has acceptable penetration, and the state is finite.
- Failure: non-finite state, severe penetration, ball drop, floor contact after the ball has been lifted, or timeout.
- Note: Initial floor/table contact is allowed; floor contact becomes failure only after the ball has been lifted.

## Episode Result Schema

`{"task_name": "string", "contract_version": "string", "episode_status": "success | failure | running", "terminal_reason": "success_lift_ball | non_finite_state | excessive_penetration | ball_dropped | floor_contact_after_lift | timeout | running", "success": "bool", "failure": "bool", "done": "bool", "step_count": "int", "initial_ball_position": "[3] float", "official_metrics": "dict", "reward": "dict with total and named terms", "debug_metrics": "optional dict; keep out of official dataset rows unless requested"}`

## Validation

- Contract JSON: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_task_contract.json`
- API observation dim matches schema: `True`
- API action dim matches schema: `True`
- Initial lift-scene state: `running` / `running`
- Initial reward total: `-0.492739`
- Sweep metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_ball_pose_sweep.json`
- Sweep status: `PASS`
- Sweep success count: `9 / 9`
- Sweep lift range: `0.151663 m` to `0.158818 m`

## Next Step

Use this contract as the authority for dataset-v0 rows, replay QA, and any later training-readiness review. Keep BC/RL training blocked until dataset QA and policy-readiness criteria are explicitly accepted.
