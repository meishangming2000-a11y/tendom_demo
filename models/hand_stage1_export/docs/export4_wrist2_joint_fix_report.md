# Export4 Wrist 2 Joint Fix Report

Generated: 2026-05-26T02:09:10

## Scope

This verifies the experimental export4 branch only. CAD, STL, joint names, and the frozen current baseline were not modified.

## XML Joint Info

- Hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_wrist2_collision_tuned.xml`
- Scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Parent body: `wrist_middle_link`
- Child body: `palm_link`
- Type: `hinge`
- Axis: `0 0 -1`
- Range: `-0.8 0.8`
- Limited: `true`

## Motion Result

- Negative test delta of palm relative to wrist_middle: `[0.0, 0.0, 0.0]` m
- Positive test delta of palm relative to wrist_middle: `[0.0, 0.0, 0.0]` m
- Motion norm, -0.3 rad: `0.000000` m
- Motion norm, +0.3 rad: `0.000000` m
- Relative orientation change, -0.3 rad: `0.300000` rad
- Relative orientation change, +0.3 rad: `0.300000` rad
- Status: **PASS**

## Pose Metrics

| requested angle | contact count | max penetration | ball-hand contacts | palm-wrist relative | relative rotation trace |
|---:|---:|---:|---:|---|---:|
| 0.000 | 0 | 0.000000 | 0 | `[0.000571, -0.000659, 0.020273]` | 0.983642 |
| -0.300 | 2 | 0.004361 | 2 | `[0.000571, -0.000659, 0.020273]` | 0.886475 |
| 0.300 | 0 | 0.000000 | 0 | `[0.000571, -0.000659, 0.020273]` | 0.992943 |

## Screenshots

- Before / zero: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 32.65107581018518, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 33.79681018518519, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 86.14264149305555, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 46.616938078703704, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- Negative: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 33.113944733796295, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 29.838747974537036, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 89.30706712962963, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 40.602815104166666, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- Positive: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 34.21515596064815, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 35.57588975694444, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 83.88386342592592, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 48.92626215277778, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`

## Notes

- The frozen baseline is preserved. This branch is the place to keep the wrist_2 revolute behavior if downstream checks remain stable.
- If the visual pose looks wrong later, inspect the wrist_2 axis/csys in SolidWorks before changing the joint tree.
