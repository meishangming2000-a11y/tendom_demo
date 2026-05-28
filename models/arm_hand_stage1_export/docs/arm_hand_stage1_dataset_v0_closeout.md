# Arm-Hand Stage1 Dataset V0 Closeout

Generated: 2026-05-27 09:12

## Scope

This is a tiny scripted smoke dataset for adapter/replay validation only.

It is not RL/BC training data.

## Files

- Task API: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py`
- Dataset collector: `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_smoke_dataset.py`
- Replay checker: `D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_smoke_dataset.py`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_scripted_smoke_dataset_v0.npz`
- Dataset report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_scripted_smoke_dataset_report.md`
- Replay report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_replay_report.md`

## Results

- Episodes: `5`
- Total steps: `1200`
- qpos shape: `[1200, 33]`
- qvel shape: `[1200, 32]`
- ctrl/action shape: `[1200, 26]`
- obs shape: `[1200, 124]`
- Labels: `5 / 5 contact_smoke_pass`
- Replay: PASS

Replay keyframes:

- `docs\visual_checks_arm_hand_stage1_replay\episode_0_frame_0000_open_hand.png`
- `docs\visual_checks_arm_hand_stage1_replay\episode_0_frame_0120_close_four_fingers.png`
- `docs\visual_checks_arm_hand_stage1_replay\episode_0_frame_0239_hold.png`

## Interpretation

The current physics-v0 scene can now produce and replay a small, structured rollout artifact.

This validates:

- model load;
- action dimension stability;
- observation dimension stability;
- qpos/qvel/ctrl replay;
- staged scripted control;
- pinned-ball contact smoke.

It does not validate:

- stable free-object grasp;
- learned policy readiness;
- high-fidelity collision;
- Shadow-equivalent dexterity.

## Next Step

Build a Shadow-style scripted task wrapper on top of the same `ArmHandStage1TaskAPI`, then run side-by-side metrics without starting training.
