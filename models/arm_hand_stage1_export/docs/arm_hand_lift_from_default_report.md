# Arm-Hand Lift From Default Demo Report

Generated: 2026-06-07T21:15:26

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Mode: `pure_physics`
- Status: **PASS**
- Training used: **No**
- Video: `None`
- Contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_contact_sheet.png`

## Final Metrics

- Ball lift height: `0.158396 m`
- Ball displacement: `0.170917 m`
- Ball-hand contacts: `7`
- Ball-floor contacts: `0`
- Max penetration: `0.003416 m`
- Four-finger avg tip-ball distance: `0.062289 m`
- Thumb-ball distance: `0.041790 m`

## Phase Metrics

| phase | assisted | ball lift | ball-hand contacts | ball-floor contacts | max penetration | four avg | thumb-ball |
|---|---:|---:|---:|---:|---:|---:|---:|
| default_hold | 0 | -0.0002 | 0 | 1 | 0.000184 | 0.6880 | 0.5682 |
| move_to_pre_approach | 0 | -0.0002 | 0 | 1 | 0.000184 | 0.1138 | 0.1686 |
| approach_ball | 0 | -0.0006 | 2 | 1 | 0.000649 | 0.0999 | 0.0606 |
| preshape | 0 | -0.0013 | 3 | 1 | 0.001557 | 0.0880 | 0.0569 |
| close_four_fingers | 0 | -0.0013 | 4 | 1 | 0.003572 | 0.0657 | 0.0526 |
| close_thumb | 0 | -0.0014 | 7 | 1 | 0.003731 | 0.0631 | 0.0405 |
| lift | 0 | 0.1619 | 7 | 0 | 0.003430 | 0.0623 | 0.0415 |
| hold_lift | 0 | 0.1584 | 7 | 0 | 0.003416 | 0.0623 | 0.0418 |

## Interpretation

This demo starts from the model default posture, moves the arm to a pre-approach pose, approaches the ball, closes the fingers, and lifts. It is still scripted position control using collision proxy v2, not a learned policy.

The floor/table plane is the same raised demo plane used by the previous lift-ball smoke scene, chosen to keep the ball inside the current arm workspace.

