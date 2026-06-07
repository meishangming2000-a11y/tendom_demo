# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T11:41:27`
- 状态：`PARTIAL`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`27 / 30`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 15 / 15 | `{'success_gentle_grasp_hold': 15}` | `{}` | `{'early_contact_in_approach': 15, 'transient_or_hold_slip': 14}` |
| `thumb_index_middle_pinch` | 12 / 15 | `{'success_vision_confirmed_pinch_lift_hold': 12, 'vision_lift_too_small': 3}` | `{'vision_lift_too_small': 3, 'true_lift_too_small': 3, 'hold_slip_score_high': 2, 'no_thumb_finger_pinch_before_lift': 1, 'pinch_not_maintained_in_hold': 1, 'hold_tactile_unstable': 1, 'egg_still_touching_floor': 2}` | `{'early_contact_in_approach': 15, 'transient_slip_high': 15, 'low_pinch_purity': 2}` |

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
| 15 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1021 | 1.000 | 0.155 | 1.000 | `[]` |
| 16 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1045 | 1.000 | 0.111 | 1.000 | `[]` |
| 17 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0951 | 1.000 | 0.258 | 0.939 | `[]` |
| 18 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1107 | 1.000 | 0.171 | 1.000 | `[]` |
| 19 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1034 | 1.000 | 0.183 | 1.000 | `[]` |
| 20 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0790 | 1.000 | 0.178 | 1.000 | `[]` |
| 21 | `thumb_index_middle_pinch` | `back_large_lift` | FAIL | `vision_lift_too_small` | 0.0437 | 0.746 | 1.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high']` |
| 22 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1017 | 1.000 | 0.173 | 0.957 | `[]` |
| 23 | `thumb_index_middle_pinch` | `lifted_diag` | FAIL | `vision_lift_too_small` | -0.0221 | 0.000 | 0.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 24 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1142 | 1.000 | 0.185 | 1.000 | `[]` |
| 25 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1014 | 1.000 | 0.159 | 0.869 | `[]` |
| 26 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1045 | 1.000 | 0.159 | 0.548 | `[]` |
| 27 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0863 | 1.000 | 0.260 | 1.000 | `[]` |
| 28 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1068 | 1.000 | 0.202 | 1.000 | `[]` |
| 29 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `vision_lift_too_small` | -0.0018 | 0.673 | 1.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
