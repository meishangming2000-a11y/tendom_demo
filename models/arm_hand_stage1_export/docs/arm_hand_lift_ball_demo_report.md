# Arm-Hand Lift Ball Scripted Demo Report

Generated: 2026-05-28T09:15:39

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Mode: `pure_physics`
- Status: **PURE_PHYSICS_PASS**
- Render camera: `lift_demo_side`
- Training used: **No**
- Model summary: `{'nbody': 32, 'njnt': 27, 'nu': 26, 'ngeom': 67, 'nsite': 14, 'nmesh': 29}`

## Interpretation

This run disables ball assistance and reports whether the current contact proxy can physically lift the ball.

## Final Metrics

- Ball lift height: `0.152621 m`
- Ball displacement: `0.159507 m`
- Ball-hand contacts: `6`
- Ball-floor contacts: `0`
- Max penetration: `0.003056 m`
- Four-finger avg tip-ball distance: `0.052516 m`
- Thumb-ball distance: `0.038009 m`

## Phases

| phase | assisted | ball lift | ball-hand contacts | ball-floor contacts | max penetration | four avg | thumb-ball |
|---|---:|---:|---:|---:|---:|---:|---:|
| open_high | 0 | -0.0002 | 0 | 1 | 0.000184 | 0.0886 | 0.1405 |
| approach_ball | 0 | -0.0012 | 1 | 1 | 0.001996 | 0.1026 | 0.0562 |
| preshape | 0 | -0.0013 | 2 | 1 | 0.001876 | 0.0843 | 0.0590 |
| close_four_fingers | 0 | -0.0012 | 4 | 1 | 0.003781 | 0.0600 | 0.0558 |
| close_thumb | 0 | -0.0011 | 5 | 1 | 0.004331 | 0.0561 | 0.0384 |
| lift | 0 | 0.1568 | 6 | 0 | 0.003121 | 0.0534 | 0.0380 |
| hold_lift | 0 | 0.1526 | 6 | 0 | 0.003056 | 0.0525 | 0.0380 |

## Screenshots

- `open_high`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\00_open_high.png`
- `approach_ball`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\01_approach_ball.png`
- `preshape`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\02_preshape.png`
- `close_four_fingers`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\03_close_four_fingers.png`
- `close_thumb`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\04_close_thumb.png`
- `lift`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\05_lift.png`
- `hold_lift`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\06_hold_lift.png`

## Next Steps

- Run `--pure-physics` to quantify how far the current collision/friction model is from an unassisted lift.
- If pure physics fails, tune fingertip/thumb/palm collision and friction with a wider ball pose sweep.
- Do not use this as training evidence until pure physics lift criteria are meaningful.
