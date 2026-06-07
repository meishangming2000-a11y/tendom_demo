# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T12:04:16`
- 状态：`PARTIAL`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`97 / 100`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 48 / 50 | `{'success_gentle_grasp_hold': 48, 'insufficient_lift_height': 2}` | `{'insufficient_lift_height': 2, 'unstable_hold_tactile': 2, 'egg_on_floor_after_hold': 2}` | `{'early_contact_in_approach': 50, 'transient_or_hold_slip': 47}` |
| `thumb_index_middle_pinch` | 49 / 50 | `{'success_vision_confirmed_pinch_lift_hold': 49, 'hold_slip_score_high': 1}` | `{'hold_slip_score_high': 1}` | `{'early_contact_in_approach': 50, 'transient_slip_high': 50}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0994 | 1.000 | 0.155 | 0.495 | `[]` |
| 1 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1109 | 1.000 | 0.168 | 1.000 | `[]` |
| 2 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0938 | 1.000 | 0.199 | 0.382 | `[]` |
| 3 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1103 | 1.000 | 0.297 | 0.826 | `[]` |
| 4 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1013 | 1.000 | 0.160 | 0.569 | `[]` |
| 5 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0858 | 1.000 | 0.137 | 0.483 | `[]` |
| 6 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1199 | 1.000 | 0.185 | 0.377 | `[]` |
| 7 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1016 | 1.000 | 0.189 | 0.563 | `[]` |
| 8 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.217 | 0.625 | `[]` |
| 9 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1145 | 1.000 | 0.175 | 0.395 | `[]` |
| 10 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0974 | 1.000 | 0.166 | 0.460 | `[]` |
| 11 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1027 | 1.000 | 0.116 | 0.334 | `[]` |
| 12 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0945 | 1.000 | 0.182 | 0.407 | `[]` |
| 13 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1091 | 1.000 | 0.183 | 0.788 | `[]` |
| 14 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1005 | 1.000 | 0.147 | 0.511 | `[]` |
| 15 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0848 | 1.000 | 0.230 | 0.706 | `[]` |
| 16 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1162 | 1.000 | 0.170 | 0.610 | `[]` |
| 17 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1014 | 1.000 | 0.155 | 0.526 | `[]` |
| 18 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.223 | 0.488 | `[]` |
| 19 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1119 | 1.000 | 0.210 | 0.942 | `[]` |
| 20 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.163 | 0.517 | `[]` |
| 21 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1051 | 1.000 | 0.102 | 0.644 | `[]` |
| 22 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0959 | 1.000 | 0.178 | 0.391 | `[]` |
| 23 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1095 | 1.000 | 0.150 | 0.328 | `[]` |
| 24 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.0999 | 1.000 | 0.147 | 0.514 | `[]` |
| 25 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0863 | 1.000 | 0.147 | 0.947 | `[]` |
| 26 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1225 | 1.000 | 0.247 | 0.538 | `[]` |
| 27 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.0990 | 1.000 | 0.183 | 0.573 | `[]` |
| 28 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.228 | 0.611 | `[]` |
| 29 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1116 | 1.000 | 0.167 | 1.000 | `[]` |
| 30 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1006 | 1.000 | 0.160 | 0.328 | `[]` |
| 31 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1032 | 1.000 | 0.194 | 0.407 | `[]` |
| 32 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0950 | 1.000 | 0.189 | 0.392 | `[]` |
| 33 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1096 | 1.000 | 0.156 | 0.367 | `[]` |
| 34 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.0977 | 1.000 | 0.138 | 0.556 | `[]` |
| 35 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0860 | 1.000 | 0.148 | 0.359 | `[]` |
| 36 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1200 | 1.000 | 0.188 | 0.383 | `[]` |
| 37 | `full_hand_gentle_grasp` | `lifted_center` | FAIL | `insufficient_lift_height` | -0.0192 | 0.000 | 0.000 | 1.000 | `['insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 38 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.216 | 0.625 | `[]` |
| 39 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1141 | 1.000 | 0.184 | 0.461 | `[]` |
| 40 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0979 | 1.000 | 0.148 | 0.519 | `[]` |
| 41 | `full_hand_gentle_grasp` | `left_low_nominal` | FAIL | `insufficient_lift_height` | -0.0161 | 0.000 | 0.000 | 1.000 | `['insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 42 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0938 | 1.000 | 0.181 | 0.397 | `[]` |
| 43 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1081 | 1.000 | 0.161 | 1.000 | `[]` |
| 44 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.148 | 0.520 | `[]` |
| 45 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0846 | 1.000 | 0.134 | 0.472 | `[]` |
| 46 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1203 | 1.000 | 0.170 | 0.511 | `[]` |
| 47 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1010 | 1.000 | 0.172 | 0.519 | `[]` |
| 48 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1113 | 1.000 | 0.199 | 0.495 | `[]` |
| 49 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1142 | 1.000 | 0.179 | 0.383 | `[]` |
| 50 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1025 | 1.000 | 0.141 | 1.000 | `[]` |
| 51 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1054 | 1.000 | 0.173 | 1.000 | `[]` |
| 52 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0936 | 1.000 | 0.288 | 1.000 | `[]` |
| 53 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1104 | 1.000 | 0.187 | 1.000 | `[]` |
| 54 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1030 | 1.000 | 0.208 | 0.808 | `[]` |
| 55 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0778 | 1.000 | 0.240 | 1.000 | `[]` |
| 56 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1202 | 1.000 | 0.174 | 0.738 | `[]` |
| 57 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1012 | 1.000 | 0.184 | 0.801 | `[]` |
| 58 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1124 | 1.000 | 0.210 | 0.721 | `[]` |
| 59 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1143 | 1.000 | 0.198 | 1.000 | `[]` |
| 60 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0994 | 1.000 | 0.156 | 1.000 | `[]` |
| 61 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1050 | 1.000 | 0.121 | 1.000 | `[]` |
| 62 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0960 | 1.000 | 0.190 | 1.000 | `[]` |
| 63 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1119 | 1.000 | 0.148 | 1.000 | `[]` |
| 64 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `hold_slip_score_high` | 0.0981 | 0.997 | 0.355 | 1.000 | `['hold_slip_score_high']` |
| 65 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0898 | 1.000 | 0.129 | 1.000 | `[]` |
| 66 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1211 | 1.000 | 0.156 | 1.000 | `[]` |
| 67 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0993 | 1.000 | 0.241 | 0.895 | `[]` |
| 68 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1121 | 1.000 | 0.219 | 0.890 | `[]` |
| 69 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1131 | 1.000 | 0.186 | 1.000 | `[]` |
| 70 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1002 | 1.000 | 0.154 | 1.000 | `[]` |
| 71 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1052 | 1.000 | 0.140 | 1.000 | `[]` |
| 72 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0958 | 1.000 | 0.270 | 1.000 | `[]` |
| 73 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1113 | 1.000 | 0.157 | 1.000 | `[]` |
| 74 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1022 | 1.000 | 0.216 | 0.833 | `[]` |
| 75 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0893 | 1.000 | 0.120 | 1.000 | `[]` |
| 76 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1224 | 1.000 | 0.176 | 1.000 | `[]` |
| 77 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1020 | 1.000 | 0.184 | 0.888 | `[]` |
| 78 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1096 | 1.000 | 0.209 | 0.705 | `[]` |
| 79 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1134 | 1.000 | 0.194 | 1.000 | `[]` |
| 80 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1039 | 1.000 | 0.246 | 1.000 | `[]` |
| 81 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0925 | 1.000 | 0.306 | 1.000 | `[]` |
| 82 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0977 | 1.000 | 0.183 | 1.000 | `[]` |
| 83 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1097 | 1.000 | 0.177 | 1.000 | `[]` |
| 84 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1005 | 1.000 | 0.337 | 0.958 | `[]` |
| 85 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0895 | 1.000 | 0.125 | 1.000 | `[]` |
| 86 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1179 | 1.000 | 0.220 | 1.000 | `[]` |
| 87 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1004 | 1.000 | 0.182 | 0.901 | `[]` |
| 88 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1127 | 1.000 | 0.201 | 0.677 | `[]` |
| 89 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1162 | 1.000 | 0.231 | 0.690 | `[]` |
| 90 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0999 | 1.000 | 0.140 | 1.000 | `[]` |
| 91 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1041 | 1.000 | 0.122 | 1.000 | `[]` |
| 92 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0943 | 1.000 | 0.253 | 1.000 | `[]` |
| 93 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1105 | 1.000 | 0.172 | 1.000 | `[]` |
| 94 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1011 | 1.000 | 0.320 | 0.941 | `[]` |
| 95 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0883 | 1.000 | 0.151 | 1.000 | `[]` |
| 96 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1131 | 1.000 | 0.328 | 1.000 | `[]` |
| 97 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0982 | 1.000 | 0.192 | 0.776 | `[]` |
| 98 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1125 | 1.000 | 0.208 | 0.713 | `[]` |
| 99 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1155 | 1.000 | 0.196 | 1.000 | `[]` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
