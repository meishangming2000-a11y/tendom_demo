# Arm-Hand Collision Proxy V2 Smoke Report

Generated: 2026-05-27T23:36:13

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Status: **PASS**
- Model summary: `{'nbody': 32, 'njnt': 27, 'nu': 26, 'ngeom': 67, 'nsite': 14, 'nmesh': 29}`
- Free ball start contacts: `1`
- Free ball start ball-hand contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free ball displacement after `300` open steps: `0.018294 m`
- Free ball vertical drop after open steps: `0.013383 m`
- Scripted hold contacts: `6`
- Scripted hold ball-hand contacts: `6`
- Scripted hold max penetration: `0.004225 m`
- Four-finger avg tip-ball distance: `0.053593 m`
- Thumb-ball distance: `0.039061 m`

- Local ball sweep PASS: `9 / 9`

## Interpretation

- v2 keeps the v1 palm contact idea but adds a shallow local `-Z` palm rail based on measured free-ball slide direction.
- If free-ball displacement is still large, that means the palm is tilted and the ball rolls/slides; pinned scripted close remains the repeatable contact smoke.
- Training remains blocked; this is still a smoke proxy.

## Local Ball Sweep

| local xyz | start contact | start pen | free disp | free drop | hold contacts | hold pen | four avg | thumb-ball | pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `[0.035, 0.12, -0.03]` | 2 | 0.003000 | 0.0064 | 0.0049 | 8 | 0.006268 | 0.0602 | 0.0398 | 1 |
| `[0.035, 0.12, -0.02]` | 1 | 0.000500 | 0.0159 | 0.0125 | 7 | 0.005043 | 0.0564 | 0.0396 | 1 |
| `[0.035, 0.12, -0.01]` | 1 | 0.000500 | 0.0259 | 0.0202 | 8 | 0.005710 | 0.0535 | 0.0398 | 1 |
| `[0.04, 0.12, -0.03]` | 2 | 0.003000 | 0.0096 | 0.0052 | 5 | 0.005169 | 0.0575 | 0.0392 | 1 |
| `[0.04, 0.12, -0.02]` | 1 | 0.000500 | 0.0175 | 0.0128 | 6 | 0.004225 | 0.0536 | 0.0391 | 1 |
| `[0.04, 0.12, -0.01]` | 1 | 0.000500 | 0.0269 | 0.0205 | 8 | 0.003463 | 0.0508 | 0.0393 | 1 |
| `[0.045, 0.12, -0.03]` | 2 | 0.003000 | 0.0132 | 0.0055 | 6 | 0.003892 | 0.0548 | 0.0384 | 1 |
| `[0.045, 0.12, -0.02]` | 1 | 0.000500 | 0.0198 | 0.0131 | 5 | 0.003155 | 0.0506 | 0.0380 | 1 |
| `[0.045, 0.12, -0.01]` | 1 | 0.000500 | 0.0287 | 0.0208 | 7 | 0.002679 | 0.0480 | 0.0386 | 1 |

## Screenshots

- `start`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_free_ball_start.png`
- `end`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_free_ball_after_open.png`
- `open_hand`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_scripted_open_hand.png`
- `preshape`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_scripted_preshape.png`
- `close_four_fingers`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_scripted_close_four_fingers.png`
- `close_thumb_smoke`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_scripted_close_thumb_smoke.png`
- `hold`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy_v2\v2_scripted_hold.png`
