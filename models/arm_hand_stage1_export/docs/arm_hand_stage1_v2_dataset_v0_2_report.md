# Arm-Hand Stage1 V2 Dataset V0.2 Report

Generated: 2026-05-30T01:42:40

- Task: `arm_hand_stage1_lift_ball`
- Contract: `stage2_lift_ball_v0_1`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Episodes: `87`
- Total rows: `87773`
- obs shape: `[87773, 124]`
- behavior actions shape: `[87773, 26]`
- expert actions shape: `[87773, 26]`
- Success count: `87 / 87`
- Terminal reasons: `{'success_lift_ball': 87}`
- Profile counts: `{'clean_nominal': 29, 'mild_fast_jitter': 29, 'mild_slow_jitter': 29}`
- Recovery mode counts: `{'nominal': 63, 'right_edge_mid_y': 15, 'right_edge_high_y': 6, 'right_edge_upper_y': 3}`
- BC target field: `expert_actions`
- Training ready: **No, experimental BC smoke only**

## Recovery Modes

| mode | arm delta | reason |
|---|---|---|
| nominal | `{}` | Use the original v0.1 scripted arm path. |
| right_edge_mid_y | `{'j1': 0.04, 'j3': 0.0, 'j4': -0.1}` | Right-edge offsets with y below the upper boundary need a slightly shifted approach. |
| right_edge_high_y | `{'j1': 0.18, 'j3': 0.05, 'j4': -0.1}` | Upper right-edge offsets need a stronger approach yaw/shape correction. |
| right_edge_upper_y | `{'j1': 0.18, 'j2': -0.04, 'j3': 0.05, 'j4': -0.1}` | The uppermost right-edge recovery offset needs a slightly deeper arm approach. |

## Episode Summary

| ep | profile | mode | offset xyz | rows | terminal phase | status | reason | lift m | hand contacts | max pen m |
|---:|---|---|---|---:|---|---|---|---:|---:|---:|
| 0 | clean_nominal | nominal | `[-0.02, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003148 |
| 1 | clean_nominal | nominal | `[-0.01, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003149 |
| 2 | clean_nominal | nominal | `[0.0, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003129 |
| 3 | clean_nominal | nominal | `[0.01, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003133 |
| 4 | clean_nominal | nominal | `[0.02, -0.02, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003447 |
| 5 | clean_nominal | nominal | `[-0.02, -0.01, 0.0]` | 1014 | lift | success | success_lift_ball | 0.0802 | 4 | 0.002825 |
| 6 | clean_nominal | nominal | `[-0.01, -0.01, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003188 |
| 7 | clean_nominal | nominal | `[0.0, -0.01, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003131 |
| 8 | clean_nominal | nominal | `[0.01, -0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003446 |
| 9 | clean_nominal | right_edge_mid_y | `[0.02, -0.01, 0.0]` | 1012 | lift | success | success_lift_ball | 0.0805 | 5 | 0.002829 |
| 10 | clean_nominal | nominal | `[-0.02, 0.0, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0807 | 6 | 0.003241 |
| 11 | clean_nominal | nominal | `[-0.01, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0803 | 8 | 0.003372 |
| 12 | clean_nominal | nominal | `[0.0, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003449 |
| 13 | clean_nominal | nominal | `[0.01, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003450 |
| 14 | clean_nominal | right_edge_mid_y | `[0.02, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003202 |
| 15 | clean_nominal | nominal | `[-0.02, 0.01, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0804 | 6 | 0.003195 |
| 16 | clean_nominal | nominal | `[-0.01, 0.01, 0.0]` | 1007 | lift | success | success_lift_ball | 0.0808 | 6 | 0.003386 |
| 17 | clean_nominal | nominal | `[0.0, 0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003450 |
| 18 | clean_nominal | nominal | `[0.01, 0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003452 |
| 19 | clean_nominal | right_edge_mid_y | `[0.02, 0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003200 |
| 20 | clean_nominal | nominal | `[-0.02, 0.02, 0.0]` | 1010 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003146 |
| 21 | clean_nominal | nominal | `[-0.01, 0.02, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0805 | 6 | 0.003209 |
| 22 | clean_nominal | nominal | `[0.0, 0.02, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003449 |
| 23 | clean_nominal | nominal | `[0.01, 0.02, 0.0]` | 1007 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003414 |
| 24 | clean_nominal | right_edge_high_y | `[0.02, 0.02, 0.0]` | 1000 | lift | success | success_lift_ball | 0.0808 | 7 | 0.003451 |
| 25 | clean_nominal | right_edge_mid_y | `[0.02, -0.015, 0.0]` | 1014 | lift | success | success_lift_ball | 0.0804 | 5 | 0.002664 |
| 26 | clean_nominal | right_edge_mid_y | `[0.02, -0.005, 0.0]` | 1011 | lift | success | success_lift_ball | 0.0805 | 5 | 0.002972 |
| 27 | clean_nominal | right_edge_high_y | `[0.02, 0.015, 0.0]` | 1004 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003167 |
| 28 | clean_nominal | right_edge_upper_y | `[0.02, 0.025, 0.0]` | 1020 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003183 |
| 29 | mild_fast_jitter | nominal | `[-0.02, -0.02, 0.0]` | 969 | lift | success | success_lift_ball | 0.0803 | 5 | 0.002902 |
| 30 | mild_fast_jitter | nominal | `[-0.01, -0.02, 0.0]` | 968 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003194 |
| 31 | mild_fast_jitter | nominal | `[0.0, -0.02, 0.0]` | 968 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003180 |
| 32 | mild_fast_jitter | nominal | `[0.01, -0.02, 0.0]` | 969 | lift | success | success_lift_ball | 0.0802 | 6 | 0.003135 |
| 33 | mild_fast_jitter | nominal | `[0.02, -0.02, 0.0]` | 965 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003467 |
| 34 | mild_fast_jitter | nominal | `[-0.02, -0.01, 0.0]` | 969 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003194 |
| 35 | mild_fast_jitter | nominal | `[-0.01, -0.01, 0.0]` | 969 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003203 |
| 36 | mild_fast_jitter | nominal | `[0.0, -0.01, 0.0]` | 968 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003141 |
| 37 | mild_fast_jitter | nominal | `[0.01, -0.01, 0.0]` | 965 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003453 |
| 38 | mild_fast_jitter | right_edge_mid_y | `[0.02, -0.01, 0.0]` | 970 | lift | success | success_lift_ball | 0.0803 | 5 | 0.002875 |
| 39 | mild_fast_jitter | nominal | `[-0.02, 0.0, 0.0]` | 968 | lift | success | success_lift_ball | 0.0806 | 6 | 0.003131 |
| 40 | mild_fast_jitter | nominal | `[-0.01, 0.0, 0.0]` | 967 | lift | success | success_lift_ball | 0.0800 | 6 | 0.003260 |
| 41 | mild_fast_jitter | nominal | `[0.0, 0.0, 0.0]` | 965 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003452 |
| 42 | mild_fast_jitter | nominal | `[0.01, 0.0, 0.0]` | 965 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003458 |
| 43 | mild_fast_jitter | right_edge_mid_y | `[0.02, 0.0, 0.0]` | 970 | lift | success | success_lift_ball | 0.0802 | 5 | 0.002713 |
| 44 | mild_fast_jitter | nominal | `[-0.02, 0.01, 0.0]` | 968 | lift | success | success_lift_ball | 0.0805 | 6 | 0.003152 |
| 45 | mild_fast_jitter | nominal | `[-0.01, 0.01, 0.0]` | 966 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003456 |
| 46 | mild_fast_jitter | nominal | `[0.0, 0.01, 0.0]` | 966 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003458 |
| 47 | mild_fast_jitter | nominal | `[0.01, 0.01, 0.0]` | 966 | lift | success | success_lift_ball | 0.0802 | 6 | 0.003402 |
| 48 | mild_fast_jitter | right_edge_mid_y | `[0.02, 0.01, 0.0]` | 965 | lift | success | success_lift_ball | 0.0802 | 7 | 0.003181 |
| 49 | mild_fast_jitter | nominal | `[-0.02, 0.02, 0.0]` | 969 | lift | success | success_lift_ball | 0.0807 | 6 | 0.003115 |
| 50 | mild_fast_jitter | nominal | `[-0.01, 0.02, 0.0]` | 965 | lift | success | success_lift_ball | 0.0806 | 8 | 0.003373 |
| 51 | mild_fast_jitter | nominal | `[0.0, 0.02, 0.0]` | 965 | lift | success | success_lift_ball | 0.0802 | 7 | 0.003468 |
| 52 | mild_fast_jitter | nominal | `[0.01, 0.02, 0.0]` | 967 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003429 |
| 53 | mild_fast_jitter | right_edge_high_y | `[0.02, 0.02, 0.0]` | 960 | lift | success | success_lift_ball | 0.0802 | 7 | 0.003480 |
| 54 | mild_fast_jitter | right_edge_mid_y | `[0.02, -0.015, 0.0]` | 971 | lift | success | success_lift_ball | 0.0805 | 5 | 0.002752 |
| 55 | mild_fast_jitter | right_edge_mid_y | `[0.02, -0.005, 0.0]` | 970 | lift | success | success_lift_ball | 0.0805 | 5 | 0.002865 |
| 56 | mild_fast_jitter | right_edge_high_y | `[0.02, 0.015, 0.0]` | 969 | lift | success | success_lift_ball | 0.0803 | 5 | 0.002849 |
| 57 | mild_fast_jitter | right_edge_upper_y | `[0.02, 0.025, 0.0]` | 978 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003170 |
| 58 | mild_slow_jitter | nominal | `[-0.02, -0.02, 0.0]` | 1056 | lift | success | success_lift_ball | 0.0800 | 5 | 0.002848 |
| 59 | mild_slow_jitter | nominal | `[-0.01, -0.02, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003195 |
| 60 | mild_slow_jitter | nominal | `[0.0, -0.02, 0.0]` | 1052 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003196 |
| 61 | mild_slow_jitter | nominal | `[0.01, -0.02, 0.0]` | 1053 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003124 |
| 62 | mild_slow_jitter | nominal | `[0.02, -0.02, 0.0]` | 1045 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003409 |
| 63 | mild_slow_jitter | nominal | `[-0.02, -0.01, 0.0]` | 1056 | lift | success | success_lift_ball | 0.0804 | 6 | 0.003035 |
| 64 | mild_slow_jitter | nominal | `[-0.01, -0.01, 0.0]` | 1051 | lift | success | success_lift_ball | 0.0802 | 7 | 0.003202 |
| 65 | mild_slow_jitter | nominal | `[0.0, -0.01, 0.0]` | 1053 | lift | success | success_lift_ball | 0.0801 | 6 | 0.003181 |
| 66 | mild_slow_jitter | nominal | `[0.01, -0.01, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003542 |
| 67 | mild_slow_jitter | right_edge_mid_y | `[0.02, -0.01, 0.0]` | 1056 | lift | success | success_lift_ball | 0.0803 | 5 | 0.002681 |
| 68 | mild_slow_jitter | nominal | `[-0.02, 0.0, 0.0]` | 1052 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003187 |
| 69 | mild_slow_jitter | nominal | `[-0.01, 0.0, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0806 | 6 | 0.003258 |
| 70 | mild_slow_jitter | nominal | `[0.0, 0.0, 0.0]` | 1048 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003470 |
| 71 | mild_slow_jitter | nominal | `[0.01, 0.0, 0.0]` | 1047 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003463 |
| 72 | mild_slow_jitter | right_edge_mid_y | `[0.02, 0.0, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003253 |
| 73 | mild_slow_jitter | nominal | `[-0.02, 0.01, 0.0]` | 1049 | lift | success | success_lift_ball | 0.0807 | 6 | 0.003296 |
| 74 | mild_slow_jitter | nominal | `[-0.01, 0.01, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003525 |
| 75 | mild_slow_jitter | nominal | `[0.0, 0.01, 0.0]` | 1048 | lift | success | success_lift_ball | 0.0804 | 6 | 0.003350 |
| 76 | mild_slow_jitter | nominal | `[0.01, 0.01, 0.0]` | 1044 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003449 |
| 77 | mild_slow_jitter | right_edge_mid_y | `[0.02, 0.01, 0.0]` | 1069 | lift | success | success_lift_ball | 0.0803 | 4 | 0.002012 |
| 78 | mild_slow_jitter | nominal | `[-0.02, 0.02, 0.0]` | 1055 | lift | success | success_lift_ball | 0.0803 | 6 | 0.002825 |
| 79 | mild_slow_jitter | nominal | `[-0.01, 0.02, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0802 | 6 | 0.003231 |
| 80 | mild_slow_jitter | nominal | `[0.0, 0.02, 0.0]` | 1043 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003439 |
| 81 | mild_slow_jitter | nominal | `[0.01, 0.02, 0.0]` | 1047 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003422 |
| 82 | mild_slow_jitter | right_edge_high_y | `[0.02, 0.02, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003049 |
| 83 | mild_slow_jitter | right_edge_mid_y | `[0.02, -0.015, 0.0]` | 1053 | lift | success | success_lift_ball | 0.0802 | 5 | 0.002828 |
| 84 | mild_slow_jitter | right_edge_mid_y | `[0.02, -0.005, 0.0]` | 1056 | lift | success | success_lift_ball | 0.0800 | 5 | 0.002974 |
| 85 | mild_slow_jitter | right_edge_high_y | `[0.02, 0.015, 0.0]` | 1045 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003148 |
| 86 | mild_slow_jitter | right_edge_upper_y | `[0.02, 0.025, 0.0]` | 1060 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003170 |

## Interpretation

- Replay should validate against `actions`, because those were applied in MuJoCo.
- BC should train against `expert_actions`, because those are the scripted recovery targets.
- The recovery modes are targeted data fixes for the v0.1 right-edge timeout cluster.
