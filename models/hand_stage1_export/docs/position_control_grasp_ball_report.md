# Position Control Grasp Ball Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Load success: yes
- Ball position requested: `[0.0, -0.1, 0.195]`
- Gravity enabled: False
- Pin ball: True
- Actuator count: 21
- Missing actuators: None

## Stage Summary

| Stage | Ball contacts | Max penetration (m) | Mean 4-tip distance (m) | Thumb distance (m) |
|---|---:|---:|---:|---:|
| open_hand | 0 | 0.000000 | 0.105781 | 0.17060341375977248 |
| approach_pre_shape | 0 | 0.000000 | 0.093458 | 0.17112778600193487 |
| close_four_fingers | 1 | 0.001986 | 0.038688 | 0.1712595315557234 |
| close_thumb | 2 | 0.003937 | 0.035196 | 0.1705673628069524 |
| hold | 2 | 0.003938 | 0.035195 | 0.17048114994958743 |

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_position_control_grasp\open_hand.png` camera=`full_hand_with_ball` mean_pixel=32.25
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_position_control_grasp\preshape.png` camera=`full_hand_with_ball` mean_pixel=31.78
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_position_control_grasp\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=31.48
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_position_control_grasp\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=31.60
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_position_control_grasp\hold.png` camera=`full_hand_with_ball` mean_pixel=31.59

## Notes

- Hand joints are controlled through position actuators via data.ctrl; hand qpos is not directly written during the demo.
- Default runtime gravity is zero so the ball-placement smoke test does not immediately drop the ball.
- Clean STL geoms remain visual-only; simplified primitive geoms provide collision proxy contacts.
- Thumb opposition remains a separate audit item and is not corrected here.
