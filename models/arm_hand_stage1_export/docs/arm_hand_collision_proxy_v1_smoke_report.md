# Arm-Hand Collision Proxy V1 Smoke Report

Generated: 2026-05-27T10:51:50

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v1_ball.xml`
- Status: **PASS**
- Model summary: `{'nbody': 32, 'njnt': 27, 'nu': 26, 'ngeom': 66, 'nsite': 14, 'nmesh': 29}`
- Free ball start contacts: `1`
- Free ball start ball-hand contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free ball displacement after `300` open steps: `1.413752 m`
- Free ball vertical drop after open steps: `1.394647 m`
- Scripted hold contacts: `6`
- Scripted hold ball-hand contacts: `6`
- Scripted hold max penetration: `0.004004 m`
- Four-finger avg tip-ball distance: `0.053854 m`
- Thumb-ball distance: `0.038849 m`

## Interpretation

- v1 adds a palm-side contact surface, so free-ball behavior is no longer only a pinned-ball artifact.
- If free-ball displacement is still large, that means the palm is tilted and the ball rolls/slides, not that the hand has no collision.
- Training remains blocked; this is still a smoke proxy.

## Screenshots

- `start`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_free_ball_start.png`
- `end`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_free_ball_after_open.png`
- `open_hand`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_scripted_open_hand.png`
- `preshape`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_scripted_preshape.png`
- `close_four_fingers`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_scripted_close_four_fingers.png`
- `close_thumb_smoke`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_scripted_close_thumb_smoke.png`
- `hold`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v1\v1_scripted_hold.png`
