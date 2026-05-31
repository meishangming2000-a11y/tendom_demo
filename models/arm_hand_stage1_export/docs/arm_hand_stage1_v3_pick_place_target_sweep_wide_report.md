# Arm-Hand Stage1 V3 Pick-Place Target Sweep Report

Generated: 2026-05-31T21:43:37

- Status: **PARTIAL**
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_demo.xml`
- Episodes: `49`
- Success count: `37 / 49`
- Terminal reasons: `{'target_miss': 9, 'placement_not_stable': 3, 'success_pick_place_ball': 37}`
- Target center base: `[0.165, 0.23, -0.06538044]`
- Target radius: `0.035 m`
- Required stable steps: `240`
- Target distance XY range: `0.003190 m` to `0.045197 m`
- Target distance XY mean: `0.026698 m`
- Stable steps range: `0` to `1169`
- Transport floor contacts total: `0`
- Training ready: **No, scripted smoke sweep only**

## Episode Results

| ep | target offset xy | target center xy | status | reason | final ball xy | target dist xy m | stable steps | transport floor | final hand | final floor |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|
| 0 | `[-0.03, -0.03]` | `[0.135, 0.2]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.040886 | 0 | 0 | 0 | 1 |
| 1 | `[-0.03, -0.02]` | `[0.135, 0.21]` | PARTIAL | placement_not_stable | `[0.1619, 0.2308]` | 0.034000 | 172 | 0 | 0 | 1 |
| 2 | `[-0.03, -0.01]` | `[0.135, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.028988 | 536 | 0 | 0 | 1 |
| 3 | `[-0.03, 0.0]` | `[0.135, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.026919 | 542 | 0 | 0 | 1 |
| 4 | `[-0.03, 0.01]` | `[0.135, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.028442 | 386 | 0 | 0 | 1 |
| 5 | `[-0.03, 0.02]` | `[0.135, 0.25]` | PARTIAL | placement_not_stable | `[0.1619, 0.2308]` | 0.033065 | 110 | 0 | 0 | 1 |
| 6 | `[-0.03, 0.03]` | `[0.135, 0.26]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.039719 | 0 | 0 | 0 | 1 |
| 7 | `[-0.02, -0.03]` | `[0.145, 0.2]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.035122 | 0 | 0 | 0 | 1 |
| 8 | `[-0.02, -0.02]` | `[0.145, 0.21]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.026793 | 1169 | 0 | 0 | 1 |
| 9 | `[-0.02, -0.01]` | `[0.145, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.020054 | 1169 | 0 | 0 | 1 |
| 10 | `[-0.02, 0.0]` | `[0.145, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.016926 | 1141 | 0 | 0 | 1 |
| 11 | `[-0.02, 0.01]` | `[0.145, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.019256 | 898 | 0 | 0 | 1 |
| 12 | `[-0.02, 0.02]` | `[0.145, 0.25]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.025595 | 545 | 0 | 0 | 1 |
| 13 | `[-0.02, 0.03]` | `[0.145, 0.26]` | PARTIAL | placement_not_stable | `[0.1619, 0.2308]` | 0.033755 | 78 | 0 | 0 | 1 |
| 14 | `[-0.01, -0.03]` | `[0.155, 0.2]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.031550 | 1169 | 0 | 0 | 1 |
| 15 | `[-0.01, -0.02]` | `[0.155, 0.21]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.021902 | 1169 | 0 | 0 | 1 |
| 16 | `[-0.01, -0.01]` | `[0.155, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.012807 | 1169 | 0 | 0 | 1 |
| 17 | `[-0.01, 0.0]` | `[0.155, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.006952 | 1169 | 0 | 0 | 1 |
| 18 | `[-0.01, 0.01]` | `[0.155, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.011517 | 1169 | 0 | 0 | 1 |
| 19 | `[-0.01, 0.02]` | `[0.155, 0.25]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.020420 | 923 | 0 | 0 | 1 |
| 20 | `[-0.01, 0.03]` | `[0.155, 0.26]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.030021 | 358 | 0 | 0 | 1 |
| 21 | `[0.0, -0.03]` | `[0.165, 0.2]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.030939 | 1169 | 0 | 0 | 1 |
| 22 | `[0.0, -0.02]` | `[0.165, 0.21]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.021013 | 1169 | 0 | 0 | 1 |
| 23 | `[0.0, -0.01]` | `[0.165, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.011219 | 1169 | 0 | 0 | 1 |
| 24 | `[0.0, 0.0]` | `[0.165, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.003190 | 1169 | 0 | 0 | 1 |
| 25 | `[0.0, 0.01]` | `[0.165, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.009721 | 1169 | 0 | 0 | 1 |
| 26 | `[0.0, 0.02]` | `[0.165, 0.25]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.019463 | 1169 | 0 | 0 | 1 |
| 27 | `[0.0, 0.03]` | `[0.165, 0.26]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.029379 | 538 | 0 | 0 | 1 |
| 28 | `[0.01, -0.03]` | `[0.175, 0.2]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.033453 | 1169 | 0 | 0 | 1 |
| 29 | `[0.01, -0.02]` | `[0.175, 0.21]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.024564 | 1169 | 0 | 0 | 1 |
| 30 | `[0.01, -0.01]` | `[0.175, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.016962 | 1169 | 0 | 0 | 1 |
| 31 | `[0.01, 0.0]` | `[0.175, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.013116 | 1169 | 0 | 0 | 1 |
| 32 | `[0.01, 0.01]` | `[0.175, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.016011 | 1169 | 0 | 0 | 1 |
| 33 | `[0.01, 0.02]` | `[0.175, 0.25]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.023252 | 1169 | 0 | 0 | 1 |
| 34 | `[0.01, 0.03]` | `[0.175, 0.26]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.032015 | 524 | 0 | 0 | 1 |
| 35 | `[0.02, -0.03]` | `[0.185, 0.2]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.038483 | 0 | 0 | 0 | 1 |
| 36 | `[0.02, -0.02]` | `[0.185, 0.21]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.031068 | 1169 | 0 | 0 | 1 |
| 37 | `[0.02, -0.01]` | `[0.185, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.025486 | 1169 | 0 | 0 | 1 |
| 38 | `[0.02, 0.0]` | `[0.185, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.023106 | 1169 | 0 | 0 | 1 |
| 39 | `[0.02, 0.01]` | `[0.185, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.024863 | 1169 | 0 | 0 | 1 |
| 40 | `[0.02, 0.02]` | `[0.185, 0.25]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.030042 | 1169 | 0 | 0 | 1 |
| 41 | `[0.02, 0.03]` | `[0.185, 0.26]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.037240 | 0 | 0 | 0 | 1 |
| 42 | `[0.03, -0.03]` | `[0.195, 0.2]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.045197 | 0 | 0 | 0 | 1 |
| 43 | `[0.03, -0.02]` | `[0.195, 0.21]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.039078 | 0 | 0 | 0 | 1 |
| 44 | `[0.03, -0.01]` | `[0.195, 0.22]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.034805 | 1169 | 0 | 0 | 1 |
| 45 | `[0.03, 0.0]` | `[0.195, 0.23]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.033102 | 1169 | 0 | 0 | 1 |
| 46 | `[0.03, 0.01]` | `[0.195, 0.24]` | PASS | success_pick_place_ball | `[0.1619, 0.2308]` | 0.034352 | 1169 | 0 | 0 | 1 |
| 47 | `[0.03, 0.02]` | `[0.195, 0.25]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.038267 | 0 | 0 | 0 | 1 |
| 48 | `[0.03, 0.03]` | `[0.195, 0.26]` | PARTIAL | target_miss | `[0.1619, 0.2308]` | 0.044144 | 0 | 0 | 0 | 1 |

## Interpretation

- This sweep changes the target label around the current same-platform target pad while using the same scripted motion.
- It measures placement tolerance for the first v3 scaffold; it is not yet a target-conditioned expert controller.
- Dataset v0.5 can start as a fixed-target pick-place dataset after replay QA, then expand to target-conditioned motion once the scripted arm pose is parameterized by target center.
