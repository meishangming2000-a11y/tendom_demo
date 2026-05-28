# Arm-Hand Stage1 Export Workspace

This workspace contains the current arm + export4 hand MuJoCo assembly.

## Current Status

- Stage1 arm+hand virtual prototype is now closed as the current simulation baseline.
- Frozen CAD mount reference is accepted and remains unchanged.
- Collision proxy v2 is the current smoke-test candidate.
- Clean STL meshes remain visual-only.
- The ball in the passive viewer can still slide/fall because gravity is active; use the scripted demo to see closure.
- A new arm+hand lift-ball scripted smoke demo can now close around a ball and lift it in pure-physics mode using collision proxy v2.
- Stage2 kickoff has started: the task API now defaults to collision proxy v2, a small lift-scene ball-pose sweep is available, the first observation/action/reward/done contract is frozen, dataset v0 replay QA passes, and one experimental BC smoke policy has been trained.
- No promoted BC/RL training baseline exists yet. The BC smoke checkpoint is schedule-conditioned and experimental.

## Current Files

- Frozen CAD mount scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Collision v2 hand-arm model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Collision v2 scene without ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- Collision v2 scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Lift-ball demo scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`

## Recommended Commands

Visual passive load:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py
```

Scripted visible close demo:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py
```

Collision v2 smoke test:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_collision_proxy_v2.py
```

Arm+hand v2 vs Shadow video comparison:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_shadow_video_comparison.py --max-keyframes 5
```

Arm+hand lift-ball scripted smoke demo:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics
```

Live MuJoCo viewer for the same demo:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics --viewer
```

Render the same demo to MP4:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\render_arm_hand_lift_ball_video.py
```

Default-posture to lift-ball full demo:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py
```

Stage2 task API report:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py
```

Stage2 ball-pose sweep:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_ball_pose_sweep.py
```

Stage2 task contract:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\write_arm_hand_stage1_v2_task_contract.py
```

Stage2 dataset v0 collection:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0.py
```

Stage2 dataset v0 replay QA:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py
```

Stage2 BC smoke readiness, training, online eval, and demo:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\review_arm_hand_stage1_v2_training_readiness.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --feature-mode phase_only --epochs 200 --batch-size 256 --hidden-dim 256 --depth 3 --no-cuda
python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --all-episodes --max-steps 1230 --device cpu
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --episode-id 4 --render-video --device cpu
```

Older physics-v0 regression and tiny dataset scaffold are still available:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_physics_regression.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_smoke_dataset.py --episodes 5 --steps-per-phase 48
python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_smoke_dataset.py --episode-id 0 --save-keyframes
```

## Latest Results

Collision proxy v2:

- Model: `32 bodies / 27 joints / 26 actuators / 67 geoms / 14 sites / 29 meshes`
- Free ball start ball-hand contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free ball displacement after 300 open steps: `0.018294 m`
- Free ball vertical drop after 300 open steps: `0.013383 m`
- Scripted pinned hold ball-hand contacts: `6`
- Scripted pinned hold max penetration: about `0.0042 m`
- Four-finger average fingertip-ball distance: about `0.0536 m`
- Thumb-ball distance: about `0.0391 m`
- Local ball sweep: `9 / 9` PASS

Shadow/video comparison on arm+hand v2:

- Videos processed: `12 / 12`
- Shadow failures: `0`
- Arm+hand v2 failures: `0`
- Shadow mean closure score: `0.3136`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646`

Lift-ball scripted smoke demo:

- Mode: `pure_physics`
- Status: `PURE_PHYSICS_PASS`
- Final ball lift height: `0.1526 m`
- Final ball-hand contacts: `6`
- Final ball-floor contacts: `0`
- Final max penetration: `0.0031 m`
- Note: this uses a raised demo floor/table plane and collision proxy v2; it is a presentation/integration smoke test, not training evidence.

Default-posture lift-ball demo:

- Mode: `pure_physics`
- Status: `PASS`
- Final ball lift height: `0.1584 m`
- Final ball-hand contacts: `7`
- Final ball-floor contacts: `0`
- Final max penetration: `0.0034 m`
- Phases: default hold, move to pre-approach, approach ball, preshape, close four fingers, close thumb, lift, hold lift.

Stage2 kickoff:

- Task API default scene: collision proxy v2 with ball.
- Task API action dim: `26`.
- Task API observation dim: `124`.
- Ball-pose sweep scene: lift-ball demo scene.
- Ball-pose sweep grid: x/y offsets `[-0.015, 0.0, 0.015]`, z offset `[0.0]`.
- Ball-pose sweep result: `9 / 9` PASS.
- Final lift range across sweep: about `0.1517 m` to `0.1588 m`.
- Task contract version: `stage2_lift_ball_v0_1`.
- Task contract status: observation/action/reward/done frozen for dataset-v0 collection.
- Max episode steps: `1230`.
- Dataset v0: `9 episodes / 9067 rows`, all terminal reason `success_lift_ball`.
- Dataset v0 replay QA: `PASS`, max obs/next_obs/reward error `0`.
- Training readiness: `PASS` for experimental BC smoke only.
- First BC attempt with obs+phase features fit offline but failed online rollout (`0 / 9` success), so it was not kept as the final smoke checkpoint.
- Repaired BC smoke checkpoint uses `phase_only` schedule-conditioned features, feature dim `10`, hidden dim `256`, depth `3`, `200` epochs.
- Repaired BC smoke train result: final val MSE normalized about `5.43e-7`, raw val action RMSE about `0.00035`.
- Repaired BC smoke online eval: `9 / 9` success, terminal reason `success_lift_ball`, lift range about `0.0801 m` to `0.0809 m`.
- BC smoke demo episode 4: success, lift about `0.0806 m`, ball-hand contacts `7`, max penetration about `0.00345 m`.

## Reports

- Stage closeout: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage1_virtual_prototype_closeout.md`
- Current baseline manifest: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\current_baseline_manifest.json`
- Next-stage handoff prompt: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\next_stage_handoff_prompt.md`
- Stage2 task API report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_task_api_report.md`
- Stage2 ball-pose sweep report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_ball_pose_sweep_report.md`
- Stage2 task contract: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_task_contract.md`
- Stage2 dataset v0 report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_report.md`
- Stage2 dataset v0 replay QA: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_replay_report.md`
- Stage2 dataset v0 file: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Stage2 training readiness: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_training_readiness_report.md`
- Stage2 BC smoke train report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_train_report.md`
- Stage2 BC smoke eval report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_eval_report.md`
- Stage2 BC smoke demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_demo_report.md`
- Stage2 BC smoke repair note: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_repair_report.md`
- Stage2 BC smoke checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- Stage2 BC smoke demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_smoke\bc_smoke_policy_demo.mp4`
- Collision v2 smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_smoke_report.md`
- Collision v2 visual check: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_visual_check_report.md`
- Shadow comparison: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_shadow_video_comparison_report.md`
- Lift-ball demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_report.md`
- Lift-ball visual check: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_visual_check.md`
- Lift-ball MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_pure_physics.mp4`
- Lift-ball contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_contact_sheet.png`
- Default-posture lift report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_from_default_report.md`
- Default-posture lift MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_pure_physics.mp4`
- Default-posture lift contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_contact_sheet.png`
- Active file index: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_active_file_index.md`
- Morning status: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\morning_status_export4.md`

## Guardrails

- Do not edit CAD/STL from this workspace.
- Do not overwrite the frozen CAD mount candidate.
- Do not promote BC/RL training yet; the current checkpoint is an experimental BC smoke artifact only.
- Keep RL blocked until a broader reset distribution and reward QA are accepted.
- Collision proxy v2 is usable for smoke tests, not final contact-rich training.
