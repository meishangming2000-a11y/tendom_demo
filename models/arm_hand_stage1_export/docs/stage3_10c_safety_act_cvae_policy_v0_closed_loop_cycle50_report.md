# Stage3.10C Safety ACT/CVAE Policy v0 闭环评估报告

- 生成时间：`2026-06-08T15:48:59`
- 状态：`PASS`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10c_safety_act_cvae_policy_v0.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`50 / 50`
- 训练状态：`stage3_10c_safety_act_cvae_policy_v0_offline_trained_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 25 / 25 | `{'success_gentle_grasp_hold': 25}` | `{}` | `{'early_contact_in_approach': 25, 'transient_or_hold_slip': 22}` |
| `thumb_index_middle_pinch` | 25 / 25 | `{'success_vision_confirmed_pinch_lift_hold': 25}` | `{}` | `{'early_contact_in_approach': 25, 'transient_slip_high': 25, 'low_pinch_purity': 2}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1002 | 1.000 | 0.164 | 0.365 | `[]` |
| 1 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1023 | 1.000 | 0.258 | 0.615 | `[]` |
| 2 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0948 | 1.000 | 0.190 | 0.377 | `[]` |
| 3 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1083 | 1.000 | 0.179 | 0.336 | `[]` |
| 4 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1026 | 1.000 | 0.160 | 0.558 | `[]` |
| 5 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0864 | 1.000 | 0.137 | 0.510 | `[]` |
| 6 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1197 | 1.000 | 0.167 | 0.403 | `[]` |
| 7 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1001 | 1.000 | 0.194 | 0.827 | `[]` |
| 8 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1116 | 1.000 | 0.192 | 0.583 | `[]` |
| 9 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1137 | 1.000 | 0.180 | 0.384 | `[]` |
| 10 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1002 | 1.000 | 0.164 | 0.365 | `[]` |
| 11 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1023 | 1.000 | 0.258 | 0.615 | `[]` |
| 12 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0948 | 1.000 | 0.190 | 0.377 | `[]` |
| 13 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1083 | 1.000 | 0.179 | 0.336 | `[]` |
| 14 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1026 | 1.000 | 0.160 | 0.558 | `[]` |
| 15 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0864 | 1.000 | 0.137 | 0.510 | `[]` |
| 16 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1197 | 1.000 | 0.167 | 0.403 | `[]` |
| 17 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1001 | 1.000 | 0.194 | 0.827 | `[]` |
| 18 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1116 | 1.000 | 0.192 | 0.583 | `[]` |
| 19 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1137 | 1.000 | 0.180 | 0.384 | `[]` |
| 20 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1002 | 1.000 | 0.164 | 0.365 | `[]` |
| 21 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1023 | 1.000 | 0.258 | 0.615 | `[]` |
| 22 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0948 | 1.000 | 0.190 | 0.377 | `[]` |
| 23 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1083 | 1.000 | 0.179 | 0.336 | `[]` |
| 24 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1026 | 1.000 | 0.160 | 0.558 | `[]` |
| 25 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1001 | 1.000 | 0.162 | 1.000 | `[]` |
| 26 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1044 | 1.000 | 0.106 | 1.000 | `[]` |
| 27 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0906 | 1.000 | 0.205 | 1.000 | `[]` |
| 28 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1110 | 1.000 | 0.175 | 1.000 | `[]` |
| 29 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1039 | 1.000 | 0.212 | 0.891 | `[]` |
| 30 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0877 | 1.000 | 0.166 | 1.000 | `[]` |
| 31 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1153 | 1.000 | 0.245 | 1.000 | `[]` |
| 32 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1021 | 1.000 | 0.195 | 0.671 | `[]` |
| 33 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1142 | 1.000 | 0.218 | 0.653 | `[]` |
| 34 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1163 | 1.000 | 0.193 | 1.000 | `[]` |
| 35 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1001 | 1.000 | 0.162 | 1.000 | `[]` |
| 36 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1044 | 1.000 | 0.106 | 1.000 | `[]` |
| 37 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0906 | 1.000 | 0.205 | 1.000 | `[]` |
| 38 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1110 | 1.000 | 0.175 | 1.000 | `[]` |
| 39 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1039 | 1.000 | 0.212 | 0.891 | `[]` |
| 40 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0877 | 1.000 | 0.166 | 1.000 | `[]` |
| 41 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1153 | 1.000 | 0.245 | 1.000 | `[]` |
| 42 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1021 | 1.000 | 0.195 | 0.671 | `[]` |
| 43 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1142 | 1.000 | 0.218 | 0.653 | `[]` |
| 44 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1163 | 1.000 | 0.193 | 1.000 | `[]` |
| 45 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1001 | 1.000 | 0.162 | 1.000 | `[]` |
| 46 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1044 | 1.000 | 0.106 | 1.000 | `[]` |
| 47 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0906 | 1.000 | 0.205 | 1.000 | `[]` |
| 48 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1110 | 1.000 | 0.175 | 1.000 | `[]` |
| 49 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1039 | 1.000 | 0.212 | 0.891 | `[]` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，Stage3.10C 模型只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- Stage3.10C 模型额外接收 `phase_id` 和当前 safety/risk 标签，并输出 action chunk 与 safety chunk；报告仍以真实闭环成功率为准，不用离线 loss 代替成功。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过 Stage3.10A safety layer baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.10A safety layer、Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认、safety 头是否提前预测风险。不要立刻回到小参数微调；优先调整 chunk 执行间隔、分技能头、phase-specific head 或 safety-conditioned 执行策略。
