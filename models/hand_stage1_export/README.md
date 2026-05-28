# Hand Stage1 Export4 MuJoCo Workspace

This folder contains the current simulation-side export4 hand work. It is a diagnostic and scripted-smoke workspace, not a training baseline yet.

## Current Active Experimental Candidate

Use this scene for the next local checks:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\run_export4_scripted_grasp_task.py --scene D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml --ball-y 0.08 --save-rollout
```

Active candidate files:

- `mjcf/hand_stage1_export4_palmar_ypos_collision_candidate.xml`
- `mjcf/scene_ball_export4_palmar_ypos_collision_candidate.xml`
- `docs/export4_palmar_ypos_candidate_regression_report.md`
- `metadata/export4_palmar_ypos_candidate_regression_results.json`

## Frozen Baseline

Do not overwrite these files:

- `mjcf/hand_stage1_export4_current_baseline.xml`
- `mjcf/scene_ball_export4_current_baseline.xml`
- `mjcf/scene_export4_current_baseline.xml`

The frozen baseline remains reference-only. New changes should be copied into an experiment file.

## Main Results

- `wrist_2_joint` is verified as active/revolute in the experiment branch.
- The older `-Y` tuned scene still fails scripted grasp smoke because the ball is on the wrong/far side.
- The user confirmed that `+Y` is the palm/grasp side for export4.
- The `+Y` palmar-side candidate with local fingertip collision spheres passes the small scripted smoke regression:
  - 7/7 regression tests pass;
  - 5/5 tiny smoke episodes pass;
  - hold stage creates 2 ball-hand contacts;
  - max penetration is about 1.04 mm.
- The active hand candidate has a first MuJoCo arm+hand assembly in `..\arm_hand_stage1_export\`.
- Training is still disabled.

## Start Here Tomorrow

Read:

- `docs/export4_active_file_index.md`
- `docs/export4_final_engineering_report.md`
- `docs/morning_status_export4.md`

Then run:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\run_export4_regression_tests.py --scene D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml --hand D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_palmar_ypos_collision_candidate.xml --label palmar_ypos_candidate --ball-y 0.08 --dataset D:\tendon_project\simulations\models\hand_stage1_export\data\export4_palmar_ypos_candidate_5ep_smoke_rollout.npz --report D:\tendon_project\simulations\models\hand_stage1_export\docs\export4_palmar_ypos_candidate_regression_report.md --metadata D:\tendon_project\simulations\models\hand_stage1_export\metadata\export4_palmar_ypos_candidate_regression_results.json
```

For the arm+hand assembly:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_export4_joints.py
```

## Guardrails

- Do not modify CAD.
- Do not modify STL.
- Do not rename joints.
- Do not overwrite current-baseline.
- Do not do RL/BC/training yet.
- Do not add tendon routing yet.
