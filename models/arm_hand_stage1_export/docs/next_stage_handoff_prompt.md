# Next Stage Handoff Prompt

Continue `tendon_project` from the closed Stage1 arm-hand virtual prototype baseline.

Current baseline:

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Lift scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Closeout report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage1_virtual_prototype_closeout.md`
- Baseline manifest: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\current_baseline_manifest.json`
- Default-posture lift demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py`

Latest known result:

- default-posture lift demo status: `PASS`
- pure physics final lift: about `0.158 m`
- ball-hand contacts: `7`
- max penetration: about `0.0034 m`

Stage2 kickoff status:

- Task API: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py`
- Task API report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_task_api_report.md`
- Task API default scene: collision proxy v2 with ball
- Action dim: `26`
- Observation dim: `124`
- Ball-pose sweep script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_ball_pose_sweep.py`
- Ball-pose sweep report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_ball_pose_sweep_report.md`
- Default sweep: x/y offsets `[-0.015, 0.0, 0.015]`, z offset `[0.0]`
- Default sweep result: `9 / 9` PASS
- Task contract script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\write_arm_hand_stage1_v2_task_contract.py`
- Task contract report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_task_contract.md`
- Task contract version: `stage2_lift_ball_v0_1`
- Observation/action/reward/done status: frozen for dataset-v0 collection
- Dataset v0:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Dataset v0 collection script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0.py`
- Dataset v0 report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_report.md`
- Dataset v0 replay QA script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py`
- Dataset v0 replay QA report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_replay_report.md`
- Dataset v0 result: `9 episodes / 9067 rows`, `9 / 9` success, replay QA `PASS`
- Training readiness review:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_training_readiness_report.md`
- BC smoke training script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py`
- BC smoke checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- BC smoke train report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_train_report.md`
- BC smoke eval script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py`
- BC smoke eval report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_eval_report.md`
- BC smoke demo script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py`
- BC smoke demo video:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_smoke\bc_smoke_policy_demo.mp4`
- Latest BC smoke result: readiness `PASS`; phase-only schedule-conditioned BC train final val MSE about `5.43e-7`; online eval `9 / 9` success; demo episode 4 success.
- Repair note: the first obs+phase BC attempt fit offline but failed online rollout (`0 / 9` success), so the retained smoke checkpoint uses `phase_only` features. This is a schedule-conditioned smoke artifact, not a robust closed-loop policy.

Guardrails:

- Do not modify CAD/STL.
- Do not overwrite the Stage1 baseline unless explicitly promoted.
- Do not promote BC/RL training yet.
- Do not add tendon routing yet.
- Treat collision proxy v2 as smoke-test geometry, not final physics.
- Treat the current BC checkpoint as experimental smoke only; it is not a maintained baseline.
- Keep RL blocked until broader reset coverage and reward QA are accepted.

Recommended Stage2 continuation:

1. inspect the BC smoke demo video and online eval report;
2. decide whether to expand dataset v0.1 with more ball offsets and perturbed phase timings;
3. replace the schedule-conditioned smoke policy with a real closed-loop obs+phase BC only after dataset coverage is broadened;
4. keep Shadow/video comparison as regression;
5. keep RL blocked until a broader reset distribution and reward QA are accepted.
