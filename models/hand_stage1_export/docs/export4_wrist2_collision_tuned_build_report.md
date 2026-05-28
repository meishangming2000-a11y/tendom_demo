# Export4 Wrist2 + Collision Tuned Build Report

Generated: 2026-05-26 01:40:16

## Scope

Current baseline was copied to an experimental MJCF. CAD, STL, joint names, visual mesh, and current-baseline files were not modified.

## Files

- Baseline: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_current_baseline.xml`
- Experimental hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_wrist2_collision_tuned.xml`
- Experimental ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`

## Wrist 2

- `wrist_2_joint` is verified as `type="hinge"` with range `-0.8 0.8`.
- `wrist_2_joint_pos` position actuator is verified with `kp=5` and ctrlrange `-0.8 0.8`.
- Note: current-baseline already contained wrist_2 as a hinge; this experimental file preserves and verifies that state.

## Collision Proxy Tuning

- Tuned proxy geoms: `20`
- Tuning mainly reduces long-finger and thumb proxy radii plus palm ellipsoid size. Visual mesh remains unchanged.
