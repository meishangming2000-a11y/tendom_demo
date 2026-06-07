# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T10:19:33`
- 状态：`PARTIAL`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`8`
- 成功数：`9 / 10`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 5 / 5 | `{'success_gentle_grasp_hold': 5}` | `{}` | `{'early_contact_in_approach': 5, 'transient_or_hold_slip': 5}` |
| `thumb_index_middle_pinch` | 4 / 5 | `{'success_vision_confirmed_pinch_lift_hold': 4, 'vision_lift_too_small': 1}` | `{'vision_lift_too_small': 1, 'true_lift_too_small': 1, 'hold_slip_score_high': 1}` | `{'early_contact_in_approach': 5, 'transient_slip_high': 5}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.145 | 0.605 | `[]` |
| 1 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1022 | 1.000 | 0.260 | 0.607 | `[]` |
| 2 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0932 | 1.000 | 0.153 | 1.000 | `[]` |
| 3 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1082 | 1.000 | 0.175 | 0.572 | `[]` |
| 4 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1023 | 1.000 | 0.162 | 1.000 | `[]` |
| 5 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0995 | 1.000 | 0.192 | 1.000 | `[]` |
| 6 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1040 | 1.000 | 0.109 | 0.578 | `[]` |
| 7 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0878 | 1.000 | 0.227 | 1.000 | `[]` |
| 8 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1107 | 1.000 | 0.162 | 1.000 | `[]` |
| 9 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `vision_lift_too_small` | 0.0038 | 0.744 | 1.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high']` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
