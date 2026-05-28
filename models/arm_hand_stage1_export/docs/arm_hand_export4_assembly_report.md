# Arm + Export4 Hand Assembly Report

Generated: 2026-05-26T11:08:53

## Scope

Experimental MuJoCo assembly only. CAD, STL, URDF joint tree, hand current-baseline, and arm current model were not overwritten.

## Sources

- Arm source: `D:\tendon_project\simulations\models\arm_stage1_export\robot.xml`
- Hand source: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_palmar_ypos_collision_candidate.xml`

## Outputs

- Combined hand-arm MJCF: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_palmar_ypos_candidate.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_palmar_ypos_candidate.xml`

## Attachment

- Parent frame/body: `ee_tool_frame`
- Attached hand root: `hand_base_link`
- Hand root local pos: `[0.0, 0.0, 0.0]`
- Hand root local quat: `[1.0, 0.0, 0.0, 0.0]`

## Notes

- This attaches the hand as a real child body under the arm end-effector frame, avoiding the prior one-point separate-model look.
- First pass uses identity hand orientation relative to `ee_tool_frame` and zero translation.
- TODO: inspect close-up renders and tune the fixed hand mount transform if flange and wrist are rotated or offset.
