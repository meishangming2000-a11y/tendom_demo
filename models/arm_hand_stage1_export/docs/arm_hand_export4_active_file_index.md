# Arm-Hand Export4 Active File Index

Generated: 2026-05-27 02:31

This file is kept for compatibility with earlier export4 notes. The current canonical index is:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\export4_active_file_index.md`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_active_file_index.md`

## Current Active Scene

- Active physics-v0 scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Active physics-v0 scene without ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy.xml`
- Active physics-v0 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_collision_proxy.xml`
- Frozen CAD mount reference: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`

## Latest Test Result

- Regression: PASS
- Joint smoke: `26 PASS / 0 FAIL / 1 SKIPPED`
- Open static contact: `0`
- Hold max penetration: `0.003885 m`
- Training: still blocked

## Run

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_physics_regression.py
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py
```
