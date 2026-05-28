# Arm-Hand Stage1 Replay Report

Generated: 2026-05-27T09:15:51

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_scripted_smoke_dataset_v0.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Episode: `0`
- Frames replayed: `240`
- Status: **PASS**

## Shape Check

- qpos shape: `[1200, 33]`; matches model: `True`
- qvel shape: `[1200, 32]`; matches model: `True`
- ctrl shape: `[1200, 26]`; action dim matches: `True`
- obs shape: `[1200, 124]`; task obs dim: `124`; matches: `True`

## Final Frame Metrics

- Contact count: `7`
- Max penetration: `0.003999 m`
- Fingertip-ball distances: `{"index": 0.042666816821857044, "middle": 0.0531688497809357, "ring": 0.0514614477270782, "little": 0.06269889351260935, "thumb": 0.042645666697796285}`

## Screenshots

- `frame_0_open_hand`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_replay\episode_0_frame_0000_open_hand.png`
- `frame_120_close_four_fingers`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_replay\episode_0_frame_0120_close_four_fingers.png`
- `frame_239_hold`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_replay\episode_0_frame_0239_hold.png`

## Notes

- Replay PASS means the smoke dataset is structurally consistent with the current task API.
- It does not imply training readiness.
