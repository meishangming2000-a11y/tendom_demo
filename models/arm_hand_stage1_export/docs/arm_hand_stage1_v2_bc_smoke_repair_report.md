# Arm-Hand Stage1 V2 BC Smoke Repair Report

Generated: 2026-05-29T01:18:00

- Scope: first experimental BC smoke training on dataset v0.
- Status: **PASS after one repair**
- Final checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- Final train report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_train_report.md`
- Final eval report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_eval_report.md`
- Final demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_demo_report.md`
- Demo video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_smoke\bc_smoke_policy_demo.mp4`

## Attempt 1

- Feature mode: `obs_phase`
- Offline result: learned the dataset action mapping.
- Online result: `0 / 9` success.
- Failure modes: mostly `timeout`, with some `floor_contact_after_lift`.
- Diagnosis: the tiny 9-episode dataset was too narrow for closed-loop observation-conditioned BC. Small online state drift pushed observations off the training manifold, and action errors compounded before contact.

## Repair

- Feature mode changed to `phase_only`.
- Meaning: the model learns the scripted phase schedule and action trajectory, rather than claiming robust closed-loop state feedback.
- This is acceptable for a first smoke demo because the goal is to validate the train/load/eval/demo pipeline.
- This is not acceptable as a promoted manipulation policy.

## Final Result

- Training readiness: `PASS` for experimental BC smoke only.
- Feature dim: `10`
- Hidden dim: `256`
- Depth: `3`
- Epochs: `200`
- Final val MSE normalized: about `5.43e-7`
- Val action RMSE raw units: about `0.00035`
- Online eval: `9 / 9` success.
- Terminal reason: `success_lift_ball` for all 9 episodes.
- Lift range: about `0.0801 m` to `0.0809 m`.
- Demo episode 4: success, lift about `0.0806 m`, ball-hand contacts `7`, max penetration about `0.00345 m`.

## Next Step

Expand dataset v0.1 before trying a real observation-conditioned policy again. Recommended additions: more ball offsets, phase timing perturbations, small action noise around the scripted trajectory, and explicit failure/near-miss coverage.
