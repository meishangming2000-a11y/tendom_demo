# Export4 Wrist 2 Joint Fix Report

Generated: 2026-05-26T10:14:49

## Scope

This verifies the experimental export4 branch only. CAD, STL, joint names, and the frozen current baseline were not modified.

## XML Joint Info

- Hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_palmar_ypos_collision_candidate.xml`
- Scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml`
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
| -0.300 | 0 | 0.000000 | 0 | `[0.000571, -0.000659, 0.020273]` | 0.886475 |
| 0.300 | 0 | 0.000000 | 0 | `[0.000571, -0.000659, 0.020273]` | 0.992943 |

## Screenshots

- Before / zero: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 31.97195630787037, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 34.97266898148148, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 86.25585243055555, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_zero_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 45.36450752314815, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- Negative: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 33.28634461805556, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 31.152660590277776, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 89.75270659722223, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_negative_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 41.99844241898148, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- Positive: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 33.42501765046296, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 38.00629658564815, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 84.2673449074074, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2\\wrist2_positive_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 46.06667824074074, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`

## Notes

- The frozen baseline is preserved. This branch is the place to keep the wrist_2 revolute behavior if downstream checks remain stable.
- If the visual pose looks wrong later, inspect the wrist_2 axis/csys in SolidWorks before changing the joint tree.
