# Arm-Hand Stage1 Export Workspace

This workspace contains the current arm + export4 hand MuJoCo assembly.

## Current Status

- Stage1 arm+hand virtual prototype is now closed as the current simulation baseline.
- Frozen CAD mount reference is accepted and remains unchanged.
- Collision proxy v2 is the current smoke-test candidate.
- Clean STL meshes remain visual-only.
- The ball in the passive viewer can still slide/fall because gravity is active; use the scripted demo to see closure.
- A new arm+hand lift-ball scripted smoke demo can now close around a ball and lift it in pure-physics mode using collision proxy v2.
- Stage2 kickoff has started: the task API now defaults to collision proxy v2, a small lift-scene ball-pose sweep is available, the first observation/action/reward/done contract is frozen, dataset v0/v0.1/v0.2 replay QA passes, and experimental BC smoke policies have been trained.
- No promoted BC/RL training baseline exists yet. The v0.4 weighted obs+phase checkpoint passes the current v0.1/v0.2 reset sets and now has a long-hold smoke validation pass with a post-success hold controller, but still needs unseen holdout validation before promotion.

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

Stage2 dataset v0.1 and obs+phase retry:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_1.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --report D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_replay_report.md --metadata D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_dataset_v0_1_replay.json --all-episodes
python D:\tendon_project\simulations\models\arm_hand_stage1_export\review_arm_hand_stage1_v2_training_readiness.py --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --action-field expert_actions --feature-mode obs_phase --allow-terminal-failures
python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.30 --obs-dropout-prob 0.60 --epochs 100 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda
python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --all-episodes --max-steps 1300 --action-smoothing 0.2 --device cpu
```

Stage2 dataset v0.2 targeted recovery and selected obs+phase retry:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\analyze_arm_hand_stage1_v2_v0_1_failures.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_2.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --report D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_2_replay_report.md --metadata D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_dataset_v0_2_replay.json --all-episodes
python D:\tendon_project\simulations\models\arm_hand_stage1_export\review_arm_hand_stage1_v2_training_readiness.py --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --action-field expert_actions --feature-mode obs_phase
python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --output D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.12 --obs-dropout-prob 0.20 --epochs 120 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda
python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 1300 --action-smoothing 0.4 --device cpu
```

Stage2 v0.3 weighted upper-right obs+phase training:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --output D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.12 --obs-dropout-prob 0.20 --upper-right-sample-weight 6.0 --upper-right-y-min 0.015 --epochs 120 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda
python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 1300 --action-smoothing 0.5 --device cpu
```

Stage2 v0.4 weighted transition-band obs+phase training:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --output D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.12 --obs-dropout-prob 0.20 --upper-right-sample-weight 6.0 --upper-right-y-min 0.015 --extra-sample-region transition_band,0.008,0.012,0.008,0.012,6.0 --epochs 120 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda
python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 1300 --action-smoothing 0.5 --device cpu
```

Stage2 v0.4 long-hold validation and demo:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 3000 --action-smoothing 0.5 --hold-after-success-steps 900 --hold-lift-height-min 0.070 --hold-settle-steps 180 --freeze-action-after-settle --device cpu
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --episode-id 25 --max-steps 3000 --action-smoothing 0.5 --hold-after-success-steps 900 --hold-lift-height-min 0.070 --hold-settle-steps 180 --freeze-action-after-settle --render-video --device cpu
```

Stage2 standardized run initialization:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\init_arm_hand_stage1_run.py --task stage2_pick_place_v0_5 --seed 0 --config D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage2_pick_place_v0_5.yaml
```

Training run standard:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_training_run_standard.md`

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
- Dataset v0.1: `75 episodes / 77154 rows`, behavior success `68 / 75`, replay QA `PASS`.
- Dataset v0.1 action fields: `actions` are applied behavior actions for replay, `expert_actions` are BC targets.
- Raw v0.1 obs+phase BC online eval: `18 / 75` success.
- Regularized v0.1 obs+phase BC online eval: `51 / 75` success.
- Strong-regularized v0.1 obs+phase BC with action smoothing: `69 / 75` success, matching the phase-only reference on the same v0.1 reset set.
- v0.1 obs+phase demo episode 12: success, lift about `0.0805 m`, demo video rendered.
- v0.1 failure analysis: the remaining timeout cluster was concentrated at right-edge offsets, especially `[0.02, -0.01, 0.0]` and `[0.02, 0.02, 0.0]`.
- Dataset v0.2: `87 episodes / 87773 rows`, behavior success `87 / 87`, replay QA `PASS`, recovery modes `nominal/right_edge_mid_y/right_edge_high_y/right_edge_upper_y`.
- Selected v0.2 obs+phase checkpoint: moderate regularization, `0.12` normalized obs noise, `0.20` obs dropout, action smoothing `0.4`.
- Selected v0.2 obs+phase online eval: `81 / 87` on the v0.2 recovery set and `72 / 75` on the old v0.1 reset set.
- Remaining v0.2 failures are localized to the upper-right offsets `[0.02, 0.02, 0.0]` and `[0.02, 0.025, 0.0]`; keep RL blocked.
- v0.2 recovered demo episode 9 from the old v0.1 failure set: success, demo video rendered.
- V0.3 training attempts rejected a noisy dense v0.3 dataset, an offset-feature model, and an over-broad right-edge weighting run.
- Selected v0.3 weighted upper-right obs+phase online eval: `84 / 87` on the v0.2 recovery set and `72 / 75` on the old v0.1 reset set.
- Selected v0.3 recovered demo episode 24 from the old v0.1 failure set: success, demo video rendered.
- Remaining v0.3 failures are localized to `[0.01, 0.01, 0.0]` with action smoothing `0.5`; keep RL blocked.
- Selected v0.4 weighted transition-band obs+phase online eval: `87 / 87` on the v0.2 recovery set and `75 / 75` on the old v0.1 reset set.
- Selected v0.4 recovered demo episode 18 from the old v0.1 failure set: success, demo video rendered.
- V0.4 long-hold validation with post-success settle/freeze controller: `87 / 87` on the v0.2 recovery set and `75 / 75` on the old v0.1 reset set, terminal reason `success_lift_hold`.
- V0.4 long-hold demo episode 25: success, `900` consecutive hold steps, final lift `0.079840 m`, ball-floor contacts after lift `0`, demo video rendered.
- V0.4 is the strongest BC smoke result so far, but still requires unseen holdout sweep validation before promotion or RL warm-start.

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
- Stage2 dataset v0.1 report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_report.md`
- Stage2 dataset v0.1 replay QA: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_replay_report.md`
- Stage2 dataset v0.1 file: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Stage2 v0.1 obs+phase repair report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_1_obs_phase_repair_report.md`
- Stage2 v0.1 obs+phase checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth`
- Stage2 v0.1 obs+phase eval: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_1_obs_phase_strongreg_smooth_eval_report.md`
- Stage2 v0.1 obs+phase demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_1_obs_phase\obs_phase_strongreg_policy_demo.mp4`
- Stage2 v0.1 failure analysis: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_v0_1_failure_analysis_report.md`
- Stage2 dataset v0.2 report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_2_report.md`
- Stage2 dataset v0.2 replay QA: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_2_replay_report.md`
- Stage2 dataset v0.2 file: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Stage2 v0.2 obs+phase repair report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_2_obs_phase_repair_report.md`
- Stage2 v0.2 obs+phase checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth`
- Stage2 v0.2 obs+phase eval: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_2_obs_phase_moderatereg_smooth040_eval_report.md`
- Stage2 v0.2 obs+phase eval on v0.1 resets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_2_obs_phase_moderatereg_on_v0_1_smooth040_eval_report.md`
- Stage2 v0.2 recovered demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_2_obs_phase\obs_phase_moderatereg_recovered_ep09_demo.mp4`
- Stage2 v0.3 obs+phase training report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_3_obs_phase_training_report.md`
- Stage2 v0.3 obs+phase checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth`
- Stage2 v0.3 obs+phase eval: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_3_obs_phase_weighted_upperright_on_v0_2_smooth050_eval_report.md`
- Stage2 v0.3 obs+phase eval on v0.1 resets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_3_obs_phase_weighted_upperright_on_v0_1_smooth050_eval_report.md`
- Stage2 v0.3 recovered demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_3_obs_phase\obs_phase_weighted_upperright_recovered_ep24_demo.mp4`
- Stage2 v0.4 obs+phase training report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_obs_phase_training_report.md`
- Stage2 v0.4 obs+phase checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Stage2 v0.4 obs+phase eval: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_obs_phase_weighted_upperright_transition_on_v0_2_smooth050_eval_report.md`
- Stage2 v0.4 obs+phase eval on v0.1 resets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_obs_phase_weighted_upperright_transition_on_v0_1_smooth050_eval_report.md`
- Stage2 v0.4 recovered demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_obs_phase\obs_phase_weighted_transition_recovered_ep18_demo.mp4`
- Stage2 v0.4 long-hold validation: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_hold_validation_report.md`
- Stage2 v0.4 long-hold eval: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_freeze_settle180_hold900_min070_recover_on_v0_2_eval_report.md`
- Stage2 v0.4 long-hold eval on v0.1 resets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_freeze_settle180_hold900_min070_recover_on_v0_1_eval_report.md`
- Stage2 v0.4 long-hold demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_hold\obs_phase_weighted_transition_ep25_freeze_settle180_hold900_demo.mp4`
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
- Do not promote BC/RL training yet; the current checkpoints are experimental BC smoke artifacts only.
- Keep RL blocked until a broader reset distribution and reward QA are accepted.
- Collision proxy v2 is usable for smoke tests, not final contact-rich training.
