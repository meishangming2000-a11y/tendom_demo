# Arm-Hand Collision Proxy V1 Report

Generated: 2026-05-27T10:42:44

- Source model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_collision_proxy.xml`
- V1 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v1.xml`
- V1 scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v1.xml`
- V1 ball scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v1_ball.xml`
- Ball radius: `0.028 m`
- Ball palm-local offset: `[0.04, 0.12, -0.02]`
- Ball world position: `[0.021334, 0.145571, 0.518815]`

## Changes

- Added a thin palmar pad on `palm_link` so the free ball has a physical palm-side surface to contact.
- Reduced fingertip collision spheres from `0.015 m` to `0.012 m` to reduce over-large fingertip contact.
- Did not modify CAD, STL, joint names, or joint tree.

## Tip Geoms Changed

- `index_tip_collision_proxy_sphere`
- `little_tip_collision_proxy_sphere`
- `middle_tip_collision_proxy_sphere`
- `ring_tip_collision_proxy_sphere`
- `thumb_tip_collision_proxy_sphere`

## TODO

- Run free-ball and scripted close smoke before promoting v1 to active.
- Visually inspect palm pad and fingertip proxy behavior.
