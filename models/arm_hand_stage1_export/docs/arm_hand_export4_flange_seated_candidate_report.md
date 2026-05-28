# Arm + Export4 Flange-Seated Candidate

Generated: 2026-05-26T17:29:04

## What Changed

Only the fixed local transform of `hand_base_link` under arm `ee_tool_frame` was changed.

- Hand root local pos: `[0.0, 0.0, 0.01455]`
- Hand root local quat: `[1.0, 0.0, 0.0, 0.0]`
- CAD/STL/joint tree/joint names unchanged.

## Why

The first identity attachment was kinematically correct, but it used the arm's internal `ee_tool_frame` origin rather than the visible flange face. Axis debug showed that the visible bolt/flange plate is on the `ee_mount` local `+Y` side. The `ee_tool_frame` is about `14.5 mm` inside that mesh boundary, and this direction maps to approximately `ee_tool_frame` local `+Z`. A `+14.55 mm` local Z offset is selected as the first flange-face candidate.

## Outputs

- MJCF: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_flange_seated_candidate.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_flange_seated_candidate.xml`

## Caveat

This is still not final mechanical flange calibration. If the exact flange face or bolt pattern matters, the arm CAD/export should expose a dedicated flange-mount frame and the hand should expose a dedicated wrist-mount frame.
