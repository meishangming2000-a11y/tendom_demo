# Stage3.10C Safety ACT/CVAE Policy v0 闭环评估报告

- 生成时间：`2026-06-08T16:01:56`
- 状态：`PASS`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10c_safety_act_cvae_policy_v0.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`100 / 100`
- 训练状态：`stage3_10c_safety_act_cvae_policy_v0_offline_trained_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 50 / 50 | `{'success_gentle_grasp_hold': 50}` | `{}` | `{'early_contact_in_approach': 50, 'transient_or_hold_slip': 45}` |
| `thumb_index_middle_pinch` | 50 / 50 | `{'success_vision_confirmed_pinch_lift_hold': 50}` | `{}` | `{'early_contact_in_approach': 50, 'transient_slip_high': 50}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0995 | 1.000 | 0.155 | 0.480 | `[]` |
| 1 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1030 | 1.000 | 0.161 | 0.348 | `[]` |
| 2 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0959 | 1.000 | 0.200 | 0.371 | `[]` |
| 3 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1098 | 1.000 | 0.282 | 1.000 | `[]` |
| 4 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1019 | 1.000 | 0.161 | 0.566 | `[]` |
| 5 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0864 | 1.000 | 0.133 | 0.380 | `[]` |
| 6 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1199 | 1.000 | 0.174 | 0.410 | `[]` |
| 7 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1010 | 1.000 | 0.187 | 0.661 | `[]` |
| 8 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.218 | 0.616 | `[]` |
| 9 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1145 | 1.000 | 0.177 | 0.395 | `[]` |
| 10 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0986 | 1.000 | 0.163 | 0.480 | `[]` |
| 11 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1027 | 1.000 | 0.117 | 0.393 | `[]` |
| 12 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0962 | 1.000 | 0.194 | 0.377 | `[]` |
| 13 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1084 | 1.000 | 0.181 | 0.333 | `[]` |
| 14 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1009 | 1.000 | 0.154 | 0.536 | `[]` |
| 15 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0862 | 1.000 | 0.233 | 0.539 | `[]` |
| 16 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1169 | 1.000 | 0.174 | 0.613 | `[]` |
| 17 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1009 | 1.000 | 0.161 | 0.559 | `[]` |
| 18 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.224 | 0.658 | `[]` |
| 19 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1102 | 1.000 | 0.194 | 0.961 | `[]` |
| 20 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1014 | 1.000 | 0.159 | 0.502 | `[]` |
| 21 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1034 | 1.000 | 0.117 | 0.385 | `[]` |
| 22 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0978 | 1.000 | 0.176 | 0.382 | `[]` |
| 23 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1094 | 1.000 | 0.147 | 0.327 | `[]` |
| 24 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1007 | 1.000 | 0.151 | 0.533 | `[]` |
| 25 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0867 | 1.000 | 0.142 | 0.849 | `[]` |
| 26 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1209 | 1.000 | 0.242 | 0.564 | `[]` |
| 27 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.0995 | 1.000 | 0.180 | 0.598 | `[]` |
| 28 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1113 | 1.000 | 0.231 | 0.703 | `[]` |
| 29 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1132 | 1.000 | 0.200 | 0.742 | `[]` |
| 30 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1005 | 1.000 | 0.163 | 0.339 | `[]` |
| 31 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1029 | 1.000 | 0.185 | 0.414 | `[]` |
| 32 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0971 | 1.000 | 0.189 | 0.378 | `[]` |
| 33 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1095 | 1.000 | 0.159 | 0.392 | `[]` |
| 34 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.0981 | 1.000 | 0.141 | 0.542 | `[]` |
| 35 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0867 | 1.000 | 0.143 | 0.321 | `[]` |
| 36 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1200 | 1.000 | 0.176 | 0.408 | `[]` |
| 37 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1002 | 1.000 | 0.195 | 0.507 | `[]` |
| 38 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.217 | 0.614 | `[]` |
| 39 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1140 | 1.000 | 0.188 | 0.473 | `[]` |
| 40 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0992 | 1.000 | 0.144 | 0.366 | `[]` |
| 41 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1026 | 1.000 | 0.196 | 0.379 | `[]` |
| 42 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0960 | 1.000 | 0.191 | 0.369 | `[]` |
| 43 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1076 | 1.000 | 0.163 | 0.613 | `[]` |
| 44 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1015 | 1.000 | 0.148 | 0.551 | `[]` |
| 45 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0860 | 1.000 | 0.131 | 0.381 | `[]` |
| 46 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1203 | 1.000 | 0.181 | 0.467 | `[]` |
| 47 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1007 | 1.000 | 0.175 | 0.626 | `[]` |
| 48 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1113 | 1.000 | 0.201 | 0.622 | `[]` |
| 49 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1142 | 1.000 | 0.184 | 0.386 | `[]` |
| 50 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1012 | 1.000 | 0.176 | 1.000 | `[]` |
| 51 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1058 | 1.000 | 0.175 | 1.000 | `[]` |
| 52 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0932 | 1.000 | 0.266 | 1.000 | `[]` |
| 53 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1111 | 1.000 | 0.177 | 1.000 | `[]` |
| 54 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1011 | 1.000 | 0.202 | 0.997 | `[]` |
| 55 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0858 | 1.000 | 0.199 | 0.710 | `[]` |
| 56 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1200 | 1.000 | 0.204 | 1.000 | `[]` |
| 57 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1023 | 1.000 | 0.184 | 0.795 | `[]` |
| 58 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1134 | 1.000 | 0.208 | 0.768 | `[]` |
| 59 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1152 | 1.000 | 0.195 | 1.000 | `[]` |
| 60 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1002 | 1.000 | 0.153 | 1.000 | `[]` |
| 61 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1052 | 1.000 | 0.120 | 1.000 | `[]` |
| 62 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0957 | 1.000 | 0.245 | 1.000 | `[]` |
| 63 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1119 | 1.000 | 0.148 | 1.000 | `[]` |
| 64 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1041 | 1.000 | 0.208 | 0.841 | `[]` |
| 65 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0888 | 1.000 | 0.129 | 1.000 | `[]` |
| 66 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1106 | 1.000 | 0.273 | 1.000 | `[]` |
| 67 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1002 | 1.000 | 0.241 | 1.000 | `[]` |
| 68 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1134 | 1.000 | 0.216 | 1.000 | `[]` |
| 69 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1142 | 1.000 | 0.186 | 1.000 | `[]` |
| 70 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1013 | 1.000 | 0.152 | 1.000 | `[]` |
| 71 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1055 | 1.000 | 0.140 | 1.000 | `[]` |
| 72 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0971 | 1.000 | 0.295 | 1.000 | `[]` |
| 73 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1112 | 1.000 | 0.159 | 1.000 | `[]` |
| 74 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0993 | 1.000 | 0.216 | 1.000 | `[]` |
| 75 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0902 | 1.000 | 0.137 | 1.000 | `[]` |
| 76 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1227 | 1.000 | 0.178 | 1.000 | `[]` |
| 77 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1029 | 1.000 | 0.180 | 0.846 | `[]` |
| 78 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1117 | 1.000 | 0.199 | 0.684 | `[]` |
| 79 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1144 | 1.000 | 0.200 | 1.000 | `[]` |
| 80 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1029 | 1.000 | 0.252 | 1.000 | `[]` |
| 81 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1051 | 1.000 | 0.252 | 1.000 | `[]` |
| 82 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0977 | 1.000 | 0.206 | 1.000 | `[]` |
| 83 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1105 | 1.000 | 0.177 | 1.000 | `[]` |
| 84 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0979 | 1.000 | 0.231 | 1.000 | `[]` |
| 85 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0877 | 1.000 | 0.152 | 1.000 | `[]` |
| 86 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1145 | 1.000 | 0.239 | 1.000 | `[]` |
| 87 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1015 | 1.000 | 0.180 | 0.714 | `[]` |
| 88 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1137 | 1.000 | 0.200 | 0.657 | `[]` |
| 89 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1160 | 1.000 | 0.232 | 1.000 | `[]` |
| 90 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1007 | 1.000 | 0.166 | 1.000 | `[]` |
| 91 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1041 | 1.000 | 0.122 | 1.000 | `[]` |
| 92 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0935 | 1.000 | 0.258 | 1.000 | `[]` |
| 93 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1112 | 1.000 | 0.172 | 1.000 | `[]` |
| 94 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0987 | 1.000 | 0.216 | 1.000 | `[]` |
| 95 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0873 | 1.000 | 0.162 | 1.000 | `[]` |
| 96 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1191 | 1.000 | 0.201 | 1.000 | `[]` |
| 97 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1000 | 1.000 | 0.187 | 0.812 | `[]` |
| 98 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1135 | 1.000 | 0.206 | 0.688 | `[]` |
| 99 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1160 | 1.000 | 0.205 | 1.000 | `[]` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，Stage3.10C 模型只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- Stage3.10C 模型额外接收 `phase_id` 和当前 safety/risk 标签，并输出 action chunk 与 safety chunk；报告仍以真实闭环成功率为准，不用离线 loss 代替成功。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过 Stage3.10A safety layer baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.10A safety layer、Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认、safety 头是否提前预测风险。不要立刻回到小参数微调；优先调整 chunk 执行间隔、分技能头、phase-specific head 或 safety-conditioned 执行策略。
