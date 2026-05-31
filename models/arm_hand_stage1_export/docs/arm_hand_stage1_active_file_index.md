# Arm-Hand Stage1 Active File Index

Generated: 2026-05-31 21:50

## Current Recommendation

Use collision proxy v2 for visual smoke, scripted close, Shadow/video comparison, and the new lift-ball integration demo. Keep the CAD mount candidate as the frozen alignment reference. Keep v1 and older physics-v0 files for regression history and comparison.

Stage1 is closed as a virtual prototype baseline. The current Stage2 smoke path starts from task API / dataset v0.2 / experimental obs+phase BC smoke, not from CAD alignment.

## Open/View

- Frozen CAD mount reference: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Current model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Current scene without ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- Current scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Current lift-ball demo scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Current pick-place demo scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_demo.xml`
- Previous collision v1 scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v1_ball.xml`
- Previous physics-v0 scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`

## Run

- Passive viewer, current v2 scene:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py`
- Scripted close viewer, ball pinned by default:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py`
- Same scripted viewer with raw gravity ball:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py --free-ball`
- Collision v2 smoke:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_collision_proxy_v2.py`
- Previous arm+hand v1 vs Shadow video comparison:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v1_shadow_video_comparison.py --max-keyframes 5`
- Arm+hand v2 vs Shadow video comparison:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_shadow_video_comparison.py --max-keyframes 5`
- Arm+hand lift-ball scripted smoke demo, pure physics:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics`
- Same lift-ball demo with live viewer:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics --viewer`
- Render lift-ball demo to MP4:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\render_arm_hand_lift_ball_video.py`
- Default-posture to lift-ball full demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py`
- Default-posture full demo with live viewer:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py --viewer --no-render-video`
- Stage2 task API report:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py`
- Stage2 ball-pose sweep:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_ball_pose_sweep.py`
- Stage2 task contract:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\write_arm_hand_stage1_v2_task_contract.py`
- Stage2 dataset v0 collection:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0.py`
- Stage2 dataset v0 replay QA:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py`
- Stage2 training readiness review:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\review_arm_hand_stage1_v2_training_readiness.py`
- Stage2 BC smoke training:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --feature-mode phase_only --epochs 200 --batch-size 256 --hidden-dim 256 --depth 3 --no-cuda`
- Stage2 BC smoke online eval:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --all-episodes --max-steps 1230 --device cpu`
- Stage2 BC smoke demo video:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --episode-id 4 --render-video --device cpu`
- Stage2 dataset v0.1 collection:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_1.py`
- Stage2 dataset v0.1 replay QA:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --report D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_replay_report.md --metadata D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_dataset_v0_1_replay.json --all-episodes`
- Stage2 v0.1 obs+phase training:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.30 --obs-dropout-prob 0.60 --epochs 100 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda`
- Stage2 v0.1 obs+phase eval:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --all-episodes --max-steps 1300 --action-smoothing 0.2 --device cpu`
- Stage2 v0.1 obs+phase demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --episode-id 12 --max-steps 1300 --action-smoothing 0.2 --render-video --device cpu`
- Stage2 v0.1 failure analysis:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\analyze_arm_hand_stage1_v2_v0_1_failures.py`
- Stage2 dataset v0.2 collection:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_2.py`
- Stage2 dataset v0.2 replay QA:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --report D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_2_replay_report.md --metadata D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_dataset_v0_2_replay.json --all-episodes`
- Stage2 v0.2 obs+phase training:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --output D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.12 --obs-dropout-prob 0.20 --epochs 120 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda`
- Stage2 v0.2 obs+phase eval:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 1300 --action-smoothing 0.4 --device cpu`
- Stage2 v0.2 recovered demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz --episode-id 9 --max-steps 1300 --action-smoothing 0.4 --render-video --device cpu`
- Stage2 v0.3 weighted upper-right training:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --output D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.12 --obs-dropout-prob 0.20 --upper-right-sample-weight 6.0 --upper-right-y-min 0.015 --epochs 120 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda`
- Stage2 v0.3 weighted upper-right eval:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 1300 --action-smoothing 0.5 --device cpu`
- Stage2 v0.4 weighted transition-band training:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py --data D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --output D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --action-field expert_actions --feature-mode obs_phase --normalized-obs-noise-std 0.12 --obs-dropout-prob 0.20 --upper-right-sample-weight 6.0 --upper-right-y-min 0.015 --extra-sample-region transition_band,0.008,0.012,0.008,0.012,6.0 --epochs 120 --batch-size 512 --hidden-dim 256 --depth 3 --no-cuda`
- Stage2 v0.4 weighted transition-band eval:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 1300 --action-smoothing 0.5 --device cpu`
- Stage2 v0.4 long-hold eval:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --all-episodes --max-steps 3000 --action-smoothing 0.5 --hold-after-success-steps 900 --hold-lift-height-min 0.070 --hold-settle-steps 180 --freeze-action-after-settle --device cpu`
- Stage2 v0.4 long-hold demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --dataset D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz --episode-id 25 --max-steps 3000 --action-smoothing 0.5 --hold-after-success-steps 900 --hold-lift-height-min 0.070 --hold-settle-steps 180 --freeze-action-after-settle --render-video --device cpu`
- Stage2 v0.4 unseen midpoint holdout sweep:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_holdout_sweep.py --action-smoothing 0.2 --report D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020_report.md --metadata D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020.json`
- Stage2 v0.4 unseen midpoint holdout demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py --checkpoint D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth --ball-offset 0.0175,0.0075,0.0 --episode-id 9001 --max-steps 3000 --action-smoothing 0.2 --hold-after-success-steps 900 --hold-lift-height-min 0.070 --hold-settle-steps 180 --freeze-action-after-settle --render-video --device cpu`
- Stage2 v3 pick-place task contract:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_v3_pick_place_task_api.py`
- Stage2 v3 same-platform pick-place scripted demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v3_pick_place_scripted.py --render-video`
- Stage2 v3 pick-place target-neighborhood sweep:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v3_pick_place_sweep.py`
- Stage2 v3 pick-place wider margin sweep:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v3_pick_place_sweep.py --x-offsets=-0.03,-0.02,-0.01,0.0,0.01,0.02,0.03 --y-offsets=-0.03,-0.02,-0.01,0.0,0.01,0.02,0.03 --report D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v3_pick_place_target_sweep_wide_report.md --metadata D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v3_pick_place_target_sweep_wide.json`
- Previous physics-v0 regression:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_physics_regression.py`
- Previous tiny dataset v0:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_smoke_dataset.py --episodes 5 --steps-per-phase 48`

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
- Stage2 v0.4 unseen holdout sweep script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_holdout_sweep.py`
- Stage2 v0.4 unseen holdout sweep selected report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020_report.md`
- Stage2 v0.4 unseen holdout sweep selected metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020.json`
- Stage2 v0.4 unseen holdout sweep diagnostic report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_report.md`
- Stage2 v0.4 unseen holdout demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_offset_0175_0075_smooth020_demo_report.md`
- Stage2 v0.4 unseen holdout demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_holdout\holdout_offset_0175_0075_smooth020_demo.mp4`
- Stage2 v3 pick-place task API/contract script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_v3_pick_place_task_api.py`
- Stage2 v3 pick-place task contract: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v3_pick_place_task_contract.md`
- Stage2 v3 pick-place scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_demo.xml`
- Stage2 v3 pick-place scripted demo script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v3_pick_place_scripted.py`
- Stage2 v3 pick-place scripted demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v3_pick_place_scripted_demo_report.md`
- Stage2 v3 pick-place scripted demo metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v3_pick_place_scripted_demo.json`
- Stage2 v3 pick-place scripted demo MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v3_pick_place\pick_place_same_platform_scripted_demo.mp4`
- Stage2 v3 pick-place contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v3_pick_place\pick_place_same_platform_contact_sheet.png`
- Stage2 v3 pick-place target sweep script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v3_pick_place_sweep.py`
- Stage2 v3 pick-place target sweep report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v3_pick_place_target_sweep_report.md`
- Stage2 v3 pick-place target sweep metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v3_pick_place_target_sweep.json`
- Stage2 v3 pick-place wider target sweep report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v3_pick_place_target_sweep_wide_report.md`
- Stage2 v3 pick-place wider target sweep metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v3_pick_place_target_sweep_wide.json`
- Collision v2 design: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_report.md`
- Collision v2 smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_smoke_report.md`
- Collision v2 visual check: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_visual_check_report.md`
- Collision v1 smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v1_smoke_report.md`
- Shadow/video comparison v2: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_shadow_video_comparison_report.md`
- Shadow/video comparison v1: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v1_shadow_video_comparison_report.md`
- Lift-ball demo metrics: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_report.md`
- Lift-ball demo visual check: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_visual_check.md`
- Lift-ball MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_pure_physics.mp4`
- Lift-ball contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_contact_sheet.png`
- Default-posture lift demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_from_default_report.md`
- Default-posture lift MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_pure_physics.mp4`
- Default-posture lift contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_contact_sheet.png`
- Previous final engineering report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\export4_final_engineering_report.md`
- Morning status: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\morning_status_export4.md`

## Latest Collision V2 Smoke

- Status: `PASS`
- Free ball start contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free ball displacement after 300 open steps: `0.018294 m`
- Free ball vertical drop after 300 open steps: `0.013383 m`
- Scripted pinned hold contacts: `6`
- Scripted pinned hold max penetration: about `0.0042 m`
- Four-finger average fingertip-ball distance: about `0.0536 m`
- Thumb-ball distance: about `0.0391 m`
- Local ball sweep: `9 / 9` PASS
- Compared with v1, the passive free-ball no longer falls far away during the 300-step open test.

## Latest Shadow Comparison

- Videos processed: `12 / 12`
- Shadow failures: `0`
- Arm+hand v2 failures: `0`
- Shadow mean closure score: `0.3136`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646`
- Visual sheets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\`

## Latest Lift-Ball Demo

- Mode: `pure_physics`
- Status: `PURE_PHYSICS_PASS`
- Final ball lift height: `0.1526 m`
- Final ball-hand contacts: `6`
- Final ball-floor contacts: `0`
- Final max penetration: `0.0031 m`
- Scripted phases: open high, approach ball, preshape, close four fingers, close thumb, lift, hold lift.
- Screenshots: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\`

## Latest Default-Posture Lift Demo

- Mode: `pure_physics`
- Status: `PASS`
- Final ball lift height: `0.1584 m`
- Final ball-hand contacts: `7`
- Final ball-floor contacts: `0`
- Final max penetration: `0.0034 m`
- Scripted phases: default hold, move to pre-approach, approach ball, preshape, close four fingers, close thumb, lift, hold lift.
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_pure_physics.mp4`

## Latest Stage2 Kickoff

- Task API default scene: collision proxy v2 with ball.
- Action dim: `26`.
- Observation dim: `124`.
- Ball-pose sweep scene: lift-ball demo scene.
- Ball-pose sweep grid: x/y offsets `[-0.015, 0.0, 0.015]`, z offset `[0.0]`.
- Ball-pose sweep result: `9 / 9` PASS.
- Final lift range across sweep: about `0.1517 m` to `0.1588 m`.
- Task contract version: `stage2_lift_ball_v0_1`.
- Observation/action/reward/done status: frozen for dataset-v0 collection.
- Max episode steps: `1230`.
- Dataset v0: `9 episodes / 9067 rows`, all terminal reason `success_lift_ball`.
- Dataset v0 replay QA: `PASS`, max obs/next_obs/reward error `0`.
- Training readiness: `PASS` for experimental BC smoke only.
- BC smoke repair: obs+phase offline BC failed online (`0 / 9`), then phase-only schedule-conditioned BC passed online.
- BC smoke training: feature mode `phase_only`, feature dim `10`, hidden dim `256`, depth `3`, epochs `200`, val raw action RMSE about `0.00035`.
- BC smoke online eval: `9 / 9` success, lift range about `0.0801 m` to `0.0809 m`, terminal reason `success_lift_ball`.
- BC smoke demo: episode 4 success, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_smoke\bc_smoke_policy_demo.mp4`.
- Dataset v0.1: `75 episodes / 77154 rows`, behavior success `68 / 75`, replay QA `PASS`.
- Dataset v0.1 action semantics: `actions` are applied behavior actions for replay; `expert_actions` are BC labels.
- V0.1 obs+phase retry: raw obs+phase `18 / 75`, regularized `51 / 75`, strong regularization plus smoothing `69 / 75`.
- V0.1 phase-only reference on the same reset set: `69 / 75`.
- V0.1 obs+phase demo: episode 12 success, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_1_obs_phase\obs_phase_strongreg_policy_demo.mp4`.
- V0.1 failure analysis: six retained obs+phase timeout failures clustered on right-edge offsets with near-zero lift and zero ball-hand contacts.
- Dataset v0.2: `87 episodes / 87773 rows`, behavior success `87 / 87`, replay QA `PASS`.
- Dataset v0.2 recovery modes: `nominal=63`, `right_edge_mid_y=15`, `right_edge_high_y=6`, `right_edge_upper_y=3`.
- V0.2 obs+phase selected policy: moderate regularization (`obs noise=0.12`, `obs dropout=0.20`) with action smoothing `0.4`.
- V0.2 obs+phase selected eval: `81 / 87` on v0.2 recovery resets and `72 / 75` on the old v0.1 reset set.
- V0.2 recovered demo: episode 9 from v0.1 succeeds, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_2_obs_phase\obs_phase_moderatereg_recovered_ep09_demo.mp4`.
- V0.3 obs+phase weighted upper-right selected eval: `84 / 87` on v0.2 recovery resets and `72 / 75` on the old v0.1 reset set.
- V0.3 recovered demo: episode 24 from v0.1 succeeds, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_3_obs_phase\obs_phase_weighted_upperright_recovered_ep24_demo.mp4`.
- V0.4 obs+phase weighted upper-right plus transition-band selected eval: `87 / 87` on v0.2 recovery resets and `75 / 75` on the old v0.1 reset set.
- V0.4 recovered demo: episode 18 from v0.1 succeeds, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_obs_phase\obs_phase_weighted_transition_recovered_ep18_demo.mp4`.
- V0.4 long-hold validation: `87 / 87` on v0.2 recovery resets and `75 / 75` on old v0.1 resets with `900` required hold steps.
- V0.4 long-hold demo: episode 25 succeeds, final lift `0.079840 m`, ball-floor contacts after lift `0`, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_hold\obs_phase_weighted_transition_ep25_freeze_settle180_hold900_demo.mp4`.
- V0.4 unseen midpoint holdout: original smoothing `0.5` reached `11 / 12`; selected smoothing `0.2` reached `12 / 12` with terminal reason `success_lift_hold`.
- V0.4 holdout final lift range with smoothing `0.2`: `0.075788 m` to `0.092617 m`; report at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020_report.md`.
- V0.4 holdout demo: offset `[0.0175, 0.0075, 0.0]` succeeds, final lift `0.078270 m`, ball-floor contacts after lift `0`, video at `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_holdout\holdout_offset_0175_0075_smooth020_demo.mp4`.
- V3 pick-place task scaffold: same-platform target pad scene and contract are in place; target center `[0.165, 0.230, -0.06538044]`, target radius `0.035 m`, required stable target steps `240`.
- V3 pick-place scripted demo: `PASS`, terminal reason `success_pick_place_ball`, final target XY distance `0.003190 m`, stable target steps `1169`, transport floor contacts before release `0`, final ball-hand contacts `0`.
- V3 pick-place demo video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v3_pick_place\pick_place_same_platform_scripted_demo.mp4`.
- V3 pick-place target-neighborhood sweep: `25 / 25` PASS for target offsets `[-0.02, -0.01, 0, 0.01, 0.02]` on x/y, max target XY miss `0.031068 m`, stable steps minimum `545`, transport floor contacts total `0`.
- V3 pick-place wider margin sweep: `37 / 49` on target offsets `[-0.03..0.03]` x/y, with failures at the outer rim (`target_miss=9`, `placement_not_stable=3`).

## Current Limits

- Collision proxy v2 is still a smoke proxy, not final physics.
- Lift-ball is a scripted integration smoke demo on a raised demo floor/table plane; it is not evidence of robust arbitrary object grasp.
- Thumb is usable for smoke, not Shadow-equivalent.
- Promoted training remains blocked. The current BC checkpoints are experimental smoke artifacts, not robust maintained baselines.
- Pick-place has one same-platform scripted smoke pass plus target-label tolerance sweeps; no pick-place dataset or learned policy is promoted yet.
- RL remains blocked until broader holdout coverage and reward QA are accepted.
