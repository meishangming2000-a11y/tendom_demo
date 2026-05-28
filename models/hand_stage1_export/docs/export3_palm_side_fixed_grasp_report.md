# Export3 Palm-Side Fixed Grasp Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_palm_side_fixed.xml`
- Load success: yes
- Ball position: `[0.0, 0.045, 0.22]`
- Finger close scale: 1.3
- Actuator count: 21
- Missing actuators: None

## Stage Summary

| Stage | Contacts | Max penetration (m) | Mean 4-tip dist (m) | Thumb-ball (m) | Thumb-index (m) |
|---|---:|---:|---:|---:|---:|
| open_hand | 0 | 0.000000 | 0.105668 | 0.051687 | 0.117090 |
| approach_pre_shape | 0 | 0.000000 | 0.085438 | 0.047812 | 0.101227 |
| close_four_fingers | 4 | 0.008476 | 0.029235 | 0.048011 | 0.029707 |
| close_thumb | 4 | 0.003700 | 0.031355 | 0.035985 | 0.027774 |
| hold | 4 | 0.003700 | 0.031355 | 0.035744 | 0.028195 |

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\open_hand.png` camera=`palm_side` mean_pixel=48.47
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\preshape.png` camera=`palm_side` mean_pixel=47.02
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\four_fingers_closed.png` camera=`palm_side` mean_pixel=48.72
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\close_four_fingers_palm_high.png` camera=`palm_side_high` mean_pixel=79.18
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\thumb_closed.png` camera=`palm_side` mean_pixel=48.46
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\hold.png` camera=`palm_side` mean_pixel=48.45
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_side_fixed_grasp\hold_palm_high.png` camera=`palm_side_high` mean_pixel=78.63

## Interpretation

- This run uses the palm-side fixed export3 scene: ball at positive Y and long-finger closure axes negated in the experimental hand MJCF.
- The default ball is not the full mirror Y=+0.1; a small sweep found Y=+0.045, Z=0.22 to be inside the four-finger wrap region.
- CAD, STL files, link tree, and joint names were not changed.
- Thumb tuning remains intentionally conservative in this run; the goal is to verify palm-side ball placement and long-finger closure direction.
- Open hand has no initial ball overlap at the corrected palm-side ball position.
- Hold mean four-fingertip distance is 0.0314 m.
- The corrected scene produces ball contact during hold, so it is usable for the next visual sanity check.
