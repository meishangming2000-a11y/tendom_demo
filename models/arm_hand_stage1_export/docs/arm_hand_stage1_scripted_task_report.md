# Arm-Hand Stage1 Scripted Task Report

Generated: 2026-05-27T09:17:50

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Episodes: `3`
- Success count: `3`
- Status: **PASS**
- Rollout path: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_scripted_task_rollout_v0.npz`
- Training ready: **No**

## Episode Results

| ep | success | ball | hold contacts | hold pen | four avg | thumb-ball | failure reasons |
|---:|---:|---|---:|---:|---:|---:|---|
| 0 | 1 | `[0.02284, 0.15034, 0.52047]` | 7 | 0.004443 | 0.051154 | 0.042710 | - |
| 1 | 1 | `[0.01804, 0.14317, 0.52106]` | 6 | 0.003744 | 0.053245 | 0.042462 | - |
| 2 | 1 | `[0.0154, 0.14943, 0.5206]` | 8 | 0.004877 | 0.055273 | 0.042914 | - |

## Notes

- This is a Shadow-style task scaffold shape, not a Shadow-equivalent dexterity claim.
- The ball remains pinned for this smoke task.
- No training was performed.
