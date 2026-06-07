# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T17:49:29`
- 状态：`PASS`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`100 / 100`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 50 / 50 | `{'success_gentle_grasp_hold': 50}` | `{}` | `{'early_contact_in_approach': 50, 'transient_or_hold_slip': 45, 'recovery_budget_exhausted': 26}` |
| `thumb_index_middle_pinch` | 50 / 50 | `{'success_vision_confirmed_pinch_lift_hold': 50}` | `{}` | `{'early_contact_in_approach': 50, 'transient_slip_high': 50}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0996 | 1.000 | 0.165 | 0.450 | `[]` |
| 1 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1029 | 1.000 | 0.169 | 0.298 | `[]` |
| 2 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0936 | 1.000 | 0.199 | 0.438 | `[]` |
| 3 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1099 | 1.000 | 0.268 | 1.000 | `[]` |
| 4 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1015 | 1.000 | 0.156 | 0.539 | `[]` |
| 5 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0845 | 1.000 | 0.140 | 0.420 | `[]` |
| 6 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1197 | 1.000 | 0.175 | 0.403 | `[]` |
| 7 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1006 | 1.000 | 0.181 | 0.674 | `[]` |
| 8 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1119 | 1.000 | 0.203 | 0.545 | `[]` |
| 9 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1138 | 1.000 | 0.130 | 0.436 | `[]` |
| 10 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0974 | 1.000 | 0.182 | 0.441 | `[]` |
| 11 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1027 | 1.000 | 0.260 | 0.353 | `[]` |
| 12 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0946 | 1.000 | 0.193 | 0.342 | `[]` |
| 13 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1089 | 1.000 | 0.170 | 0.828 | `[]` |
| 14 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1004 | 1.000 | 0.285 | 0.509 | `[]` |
| 15 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0849 | 1.000 | 0.208 | 0.373 | `[]` |
| 16 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1160 | 1.000 | 0.178 | 0.495 | `[]` |
| 17 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.179 | 0.598 | `[]` |
| 18 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.204 | 0.572 | `[]` |
| 19 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1101 | 1.000 | 0.194 | 0.886 | `[]` |
| 20 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1014 | 1.000 | 0.155 | 0.337 | `[]` |
| 21 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1034 | 1.000 | 0.055 | 0.437 | `[]` |
| 22 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0957 | 1.000 | 0.168 | 0.430 | `[]` |
| 23 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1086 | 1.000 | 0.205 | 0.352 | `[]` |
| 24 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1004 | 1.000 | 0.147 | 0.384 | `[]` |
| 25 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0853 | 1.000 | 0.147 | 0.379 | `[]` |
| 26 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1198 | 1.000 | 0.269 | 0.342 | `[]` |
| 27 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.0996 | 1.000 | 0.156 | 0.626 | `[]` |
| 28 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.248 | 0.750 | `[]` |
| 29 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1112 | 1.000 | 0.165 | 0.794 | `[]` |
| 30 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1007 | 1.000 | 0.128 | 0.393 | `[]` |
| 31 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1029 | 1.000 | 0.192 | 0.319 | `[]` |
| 32 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0950 | 1.000 | 0.182 | 0.375 | `[]` |
| 33 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1093 | 1.000 | 0.159 | 0.371 | `[]` |
| 34 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.0983 | 1.000 | 0.284 | 0.503 | `[]` |
| 35 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0850 | 1.000 | 0.148 | 0.358 | `[]` |
| 36 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1199 | 1.000 | 0.180 | 0.402 | `[]` |
| 37 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1002 | 1.000 | 0.204 | 0.709 | `[]` |
| 38 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1115 | 1.000 | 0.185 | 0.596 | `[]` |
| 39 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1136 | 1.000 | 0.146 | 0.447 | `[]` |
| 40 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0994 | 1.000 | 0.128 | 0.429 | `[]` |
| 41 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1026 | 1.000 | 0.183 | 0.401 | `[]` |
| 42 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0939 | 1.000 | 0.191 | 0.390 | `[]` |
| 43 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1076 | 1.000 | 0.142 | 1.000 | `[]` |
| 44 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1006 | 1.000 | 0.149 | 0.447 | `[]` |
| 45 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0840 | 1.000 | 0.141 | 0.565 | `[]` |
| 46 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1203 | 1.000 | 0.177 | 0.431 | `[]` |
| 47 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.174 | 0.675 | `[]` |
| 48 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.157 | 0.590 | `[]` |
| 49 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1137 | 1.000 | 0.162 | 0.393 | `[]` |
| 50 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1027 | 1.000 | 0.148 | 1.000 | `[]` |
| 51 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1055 | 1.000 | 0.173 | 1.000 | `[]` |
| 52 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0936 | 1.000 | 0.278 | 1.000 | `[]` |
| 53 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1105 | 1.000 | 0.178 | 1.000 | `[]` |
| 54 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1027 | 1.000 | 0.206 | 1.000 | `[]` |
| 55 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0782 | 1.000 | 0.236 | 1.000 | `[]` |
| 56 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1204 | 1.000 | 0.179 | 1.000 | `[]` |
| 57 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1014 | 1.000 | 0.185 | 0.722 | `[]` |
| 58 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1126 | 1.000 | 0.210 | 0.797 | `[]` |
| 59 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1144 | 1.000 | 0.199 | 1.000 | `[]` |
| 60 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0995 | 1.000 | 0.150 | 1.000 | `[]` |
| 61 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1050 | 1.000 | 0.121 | 1.000 | `[]` |
| 62 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0960 | 1.000 | 0.190 | 1.000 | `[]` |
| 63 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1118 | 1.000 | 0.148 | 1.000 | `[]` |
| 64 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0975 | 1.000 | 0.218 | 1.000 | `[]` |
| 65 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0901 | 1.000 | 0.131 | 1.000 | `[]` |
| 66 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1213 | 1.000 | 0.154 | 1.000 | `[]` |
| 67 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0992 | 1.000 | 0.241 | 0.891 | `[]` |
| 68 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1123 | 1.000 | 0.221 | 0.879 | `[]` |
| 69 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1132 | 1.000 | 0.186 | 1.000 | `[]` |
| 70 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1003 | 1.000 | 0.155 | 1.000 | `[]` |
| 71 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1052 | 1.000 | 0.140 | 1.000 | `[]` |
| 72 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0961 | 1.000 | 0.289 | 1.000 | `[]` |
| 73 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1112 | 1.000 | 0.157 | 1.000 | `[]` |
| 74 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1022 | 1.000 | 0.211 | 1.000 | `[]` |
| 75 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0895 | 1.000 | 0.122 | 1.000 | `[]` |
| 76 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1224 | 1.000 | 0.178 | 1.000 | `[]` |
| 77 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1022 | 1.000 | 0.182 | 0.746 | `[]` |
| 78 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1099 | 1.000 | 0.209 | 0.708 | `[]` |
| 79 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1136 | 1.000 | 0.199 | 1.000 | `[]` |
| 80 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1039 | 1.000 | 0.247 | 1.000 | `[]` |
| 81 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0996 | 1.000 | 0.279 | 1.000 | `[]` |
| 82 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0970 | 1.000 | 0.195 | 1.000 | `[]` |
| 83 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1098 | 1.000 | 0.178 | 1.000 | `[]` |
| 84 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1008 | 1.000 | 0.219 | 1.000 | `[]` |
| 85 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0897 | 1.000 | 0.129 | 1.000 | `[]` |
| 86 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1161 | 1.000 | 0.210 | 1.000 | `[]` |
| 87 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1005 | 1.000 | 0.180 | 0.734 | `[]` |
| 88 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1129 | 1.000 | 0.201 | 0.750 | `[]` |
| 89 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1162 | 1.000 | 0.231 | 0.665 | `[]` |
| 90 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1001 | 1.000 | 0.163 | 1.000 | `[]` |
| 91 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1041 | 1.000 | 0.120 | 1.000 | `[]` |
| 92 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0943 | 1.000 | 0.242 | 1.000 | `[]` |
| 93 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1106 | 1.000 | 0.172 | 1.000 | `[]` |
| 94 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1016 | 1.000 | 0.209 | 1.000 | `[]` |
| 95 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0885 | 1.000 | 0.151 | 1.000 | `[]` |
| 96 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1132 | 1.000 | 0.214 | 1.000 | `[]` |
| 97 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0985 | 1.000 | 0.191 | 0.814 | `[]` |
| 98 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1126 | 1.000 | 0.208 | 0.706 | `[]` |
| 99 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1155 | 1.000 | 0.212 | 1.000 | `[]` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
