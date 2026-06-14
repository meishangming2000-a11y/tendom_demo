# Stage3.10C Safety ACT/CVAE Policy v0 闭环评估报告

- 生成时间：`2026-06-08T18:55:27`
- 状态：`PASS`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10c_safety_act_cvae_policy_v0.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`20 / 20`
- 训练状态：`stage3_10c_safety_act_cvae_policy_v0_offline_trained_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 10 / 10 | `{'success_gentle_grasp_hold': 10}` | `{}` | `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 9, 'recovery_budget_exhausted': 5}` |
| `thumb_index_middle_pinch` | 10 / 10 | `{'success_vision_confirmed_pinch_lift_hold': 10}` | `{}` | `{'early_contact_in_approach': 10, 'transient_slip_high': 10}` |

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
| 10 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1002 | 1.000 | 0.184 | 1.000 | `[]` |
| 11 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1041 | 1.000 | 0.129 | 1.000 | `[]` |
| 12 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0954 | 1.000 | 0.293 | 1.000 | `[]` |
| 13 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1120 | 1.000 | 0.177 | 1.000 | `[]` |
| 14 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1031 | 1.000 | 0.174 | 1.000 | `[]` |
| 15 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0895 | 1.000 | 0.124 | 1.000 | `[]` |
| 16 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1211 | 1.000 | 0.189 | 1.000 | `[]` |
| 17 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1010 | 1.000 | 0.199 | 1.000 | `[]` |
| 18 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1133 | 1.000 | 0.206 | 1.000 | `[]` |
| 19 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1156 | 1.000 | 0.188 | 1.000 | `[]` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，Stage3.10C 模型只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- Stage3.10C 模型额外接收 `phase_id` 和当前 safety/risk 标签，并输出 action chunk 与 safety chunk；报告仍以真实闭环成功率为准，不用离线 loss 代替成功。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过 Stage3.10A safety layer baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.10A safety layer、Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认、safety 头是否提前预测风险。不要立刻回到小参数微调；优先调整 chunk 执行间隔、分技能头、phase-specific head 或 safety-conditioned 执行策略。
