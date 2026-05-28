# Arm-Hand Collision Proxy V2 Visual Check Report

Generated: 2026-05-28

## Files

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Ball scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Smoke report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_smoke_report.md`
- Screenshots: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\`

## Visual Observations

- `v2_free_ball_start.png`: ball begins on the palm side, with visible palm-side support.
- `v2_free_ball_after_open.png`: after free simulation the ball remains near the palm instead of falling far away.
- `v2_scripted_close_four_fingers.png`: four fingers close toward the ball; no obvious explosive behavior.
- `v2_scripted_hold.png`: ball is visually wrapped by the fingers and palm-side support; no obvious full pass-through.

## Metric Summary

- Free-ball displacement after 300 open steps: `0.018294 m`
- Free-ball vertical drop after 300 open steps: `0.013383 m`
- V1 reference free-ball displacement: about `1.413752 m`
- V1 reference free-ball vertical drop: about `1.394647 m`
- Scripted hold contacts: `6`
- Scripted hold ball-hand contacts: `6`
- Scripted hold max penetration: `0.004225 m`
- Local ball sweep: `9 / 9` PASS

## Conclusion

Status: **PASS for adjusted collision-proxy smoke**.

V2 is a clear improvement over V1 for palm-side ball retention. The shallow palm rail prevents the ball from immediately sliding off the tilted palm while preserving low initial penetration. This is still a simplified collision proxy, not a final anatomical/contact model and not training-ready.

## Remaining Caution

- The rail is an engineered support proxy. It should not be interpreted as final CAD-accurate palm geometry.
- Free-object grasp is still not solved; this only makes the contact model less fake than V1.
- Before training, v2 needs a wider ball-size/pose sweep and a policy-independent contact stability benchmark.
