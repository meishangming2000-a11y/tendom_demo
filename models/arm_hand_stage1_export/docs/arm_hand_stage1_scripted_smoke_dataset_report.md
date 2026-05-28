# Arm-Hand Stage1 Scripted Smoke Dataset Report

Generated: 2026-05-27T09:15:25

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_scripted_smoke_dataset_v0.npz`
- Episodes: `5`
- Total steps: `1200`
- qpos shape: `[1200, 33]`
- qvel shape: `[1200, 32]`
- ctrl/action shape: `[1200, 26]`
- obs shape: `[1200, 124]`
- Labels: `{'contact_smoke_pass': 5}`
- Training ready: **No**

## Episodes

| ep | label | ball | contacts | max pen | four avg | thumb-ball | thumb-index |
|---:|---|---|---:|---:|---:|---:|---:|
| 0 | contact_smoke_pass | `[0.02133, 0.14557, 0.51882]` | 7 | 0.003999 | 0.052499 | 0.042646 | 0.029876 |
| 1 | contact_smoke_pass | `[0.02733, 0.14557, 0.51882]` | 6 | 0.003289 | 0.049853 | 0.041361 | 0.029330 |
| 2 | contact_smoke_pass | `[0.01533, 0.14557, 0.51882]` | 7 | 0.004854 | 0.055043 | 0.042721 | 0.028140 |
| 3 | contact_smoke_pass | `[0.02133, 0.15157, 0.51882]` | 7 | 0.005653 | 0.051999 | 0.042836 | 0.034264 |
| 4 | contact_smoke_pass | `[0.02133, 0.13957, 0.51882]` | 3 | 0.002184 | 0.053860 | 0.042533 | 0.025403 |

## Notes

- This is intentionally small and pinned-ball. It verifies data shapes, staged control, contacts, and replayability.
- It should not be used for RL/BC training yet.
