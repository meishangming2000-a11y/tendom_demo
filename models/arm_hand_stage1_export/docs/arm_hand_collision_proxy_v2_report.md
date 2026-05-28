# Arm-Hand Collision Proxy V2 Report

Generated: 2026-05-27T23:35:40

- Source model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v1.xml`
- V2 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- V2 scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- V2 ball scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Ball radius: `0.028 m`
- Ball palm-local offset: `[0.04, 0.12, -0.02]`
- Ball world position: `[0.021334, 0.145571, 0.518815]`

## Design

- V2 is separate from v1 and does not overwrite the frozen mount or old proxy models.
- Replaced the v1 palm pad with `palm_link_palmar_pad_collision_proxy_v2`.
- Added `palm_link_negative_z_cup_rail_collision_proxy_v2` on the measured local `-Z` slide side.
- Increased palm-pad friction modestly; this is still a smoke proxy, not a final physical material model.
- Did not edit CAD, STL, joint tree, joint names, tendon routing, or training code.

## Evaluation Goal

- Preserve low initial penetration near the palm.
- Increase early palm-side contact stability without trapping the ball artificially.
- Keep scripted hold max penetration below about `5 mm`.
- Keep contact geoms interpretable: palm pad / palm rail / finger / thumb, not hand back or flange.
