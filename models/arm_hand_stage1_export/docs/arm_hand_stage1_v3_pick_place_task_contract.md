# Arm-Hand Stage1 V3 Pick-Place Task Contract

Generated: 2026-05-31T21:22:39

- Task name: `arm_hand_stage1_pick_place_ball`
- Contract version: `stage2_pick_place_v0_1`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_demo.xml`
- Training ready: **False**
- Default target center: `[0.165, 0.23, -0.06538044]`
- Target radius: `0.035 m`
- Required stable steps: `240`

## Feature Extension

- Add `target_center_xyz` and `ball_to_target_xyz` to the current v2 observation vector.
- Keep phase-conditioning explicit; pick-place needs transport, release, retreat, and settle phases.

## Success Contract

- ball was lifted at least once
- release phase has started
- ball center XY is within target radius
- ball-floor contact is present after release
- ball-hand contact count is zero after release
- target stability count reaches required stable steps
- max penetration is within lift-task success threshold
- finite_state is true

## Failure Contract

- finite_state is false
- max penetration exceeds lift-task failure threshold
- ball touches floor during transport before release
- timeout before stable target placement

## Current Limits

- Same-platform target pad only; not yet a two-platform task.
- Scripted expert is pure-physics but tuned for a small target displacement.
- No dataset v0.5 or trained policy is promoted yet.
- Collision proxy v2 remains smoke geometry.
