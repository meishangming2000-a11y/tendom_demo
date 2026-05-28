# Export4 Active File Index

Generated: 2026-05-27 02:30

## Current Model To Open

- Active arm+hand physics-v0 scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Active arm+hand physics-v0 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_collision_proxy.xml`
- Frozen CAD mount reference scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`

The default viewer now opens the active physics-v0 scene:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py
```

To inspect the frozen mount reference instead:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py --scene D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml
```

## Current Tests

- Physics regression: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_physics_regression.py`
- Legacy CAD-mount joint smoke: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_export4_joints.py`
- Phase generation: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\advance_arm_hand_stage1_physics.py`
- Task API report: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py`
- Tiny dataset v0: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_smoke_dataset.py --episodes 5 --steps-per-phase 48`
- Replay v0: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_smoke_dataset.py --episode-id 0 --save-keyframes`
- Scripted task scaffold: `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_scripted_task.py --episodes 3 --phase-steps 70 --hold-steps 100 --save-rollout --save-screenshots`

## Current Reports

- Freeze: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_virtual_entry_freeze.md`
- Joint tuning: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_joint_limit_tuning_report.md`
- Collision proxy: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_report.md`
- Regression: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_physics_regression_report.md`
- Closeout: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_phase_closeout_report.md`
- Task API: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_task_api_report.md`
- Dataset v0: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_scripted_smoke_dataset_report.md`
- Replay v0: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_replay_report.md`
- Scripted task: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_scripted_task_report.md`

## Current Status

- CAD-frame wrist/flange mount: PASS, user visually accepted.
- `wrist_2_joint`: hinge/revolute in active arm+hand model.
- Arm collision proxy: added primitive box proxies for `base_link`, `link_1`, `link_2`, `link_3`, `ee_mount`.
- Hand collision proxy: inherited from export4 smoke model.
- Ball default: palm-side, radius `0.028 m`, palm local offset `[0.04, 0.12, -0.02]`.
- Task API: generated, action dim `26`, obs dim `124`.
- Tiny smoke dataset v0: generated, `5 episodes / 1200 steps`, replay PASS.
- Scripted task scaffold: `3 / 3` smoke episodes PASS, rollout saved.
- Training: still blocked.
