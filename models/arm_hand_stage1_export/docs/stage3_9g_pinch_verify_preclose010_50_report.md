# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T17:53:43`
- 状态：`PASS`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`50 / 50`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `thumb_index_middle_pinch` | 50 / 50 | `{'success_vision_confirmed_pinch_lift_hold': 50}` | `{}` | `{'early_contact_in_approach': 50, 'transient_slip_high': 50}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1003 | 1.000 | 0.194 | 1.000 | `[]` |
| 1 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1044 | 1.000 | 0.129 | 1.000 | `[]` |
| 2 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0913 | 1.000 | 0.207 | 1.000 | `[]` |
| 3 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1110 | 1.000 | 0.175 | 1.000 | `[]` |
| 4 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1030 | 1.000 | 0.174 | 0.798 | `[]` |
| 5 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0876 | 1.000 | 0.222 | 1.000 | `[]` |
| 6 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1225 | 1.000 | 0.158 | 1.000 | `[]` |
| 7 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1000 | 1.000 | 0.167 | 0.777 | `[]` |
| 8 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1124 | 1.000 | 0.210 | 0.713 | `[]` |
| 9 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1156 | 1.000 | 0.199 | 1.000 | `[]` |
| 10 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0990 | 1.000 | 0.221 | 1.000 | `[]` |
| 11 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1046 | 1.000 | 0.122 | 1.000 | `[]` |
| 12 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0984 | 1.000 | 0.182 | 1.000 | `[]` |
| 13 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1118 | 1.000 | 0.178 | 1.000 | `[]` |
| 14 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1004 | 1.000 | 0.195 | 1.000 | `[]` |
| 15 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0899 | 1.000 | 0.124 | 1.000 | `[]` |
| 16 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1229 | 1.000 | 0.197 | 1.000 | `[]` |
| 17 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0996 | 1.000 | 0.198 | 0.770 | `[]` |
| 18 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1126 | 1.000 | 0.210 | 0.797 | `[]` |
| 19 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1167 | 1.000 | 0.179 | 1.000 | `[]` |
| 20 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1026 | 1.000 | 0.155 | 1.000 | `[]` |
| 21 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1034 | 1.000 | 0.140 | 1.000 | `[]` |
| 22 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0970 | 1.000 | 0.210 | 1.000 | `[]` |
| 23 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1108 | 1.000 | 0.169 | 1.000 | `[]` |
| 24 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1005 | 1.000 | 0.209 | 1.000 | `[]` |
| 25 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0883 | 1.000 | 0.119 | 1.000 | `[]` |
| 26 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1193 | 1.000 | 0.196 | 0.894 | `[]` |
| 27 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1023 | 1.000 | 0.181 | 1.000 | `[]` |
| 28 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1113 | 1.000 | 0.227 | 0.727 | `[]` |
| 29 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1142 | 1.000 | 0.170 | 1.000 | `[]` |
| 30 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1036 | 1.000 | 0.141 | 1.000 | `[]` |
| 31 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1052 | 1.000 | 0.149 | 1.000 | `[]` |
| 32 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0955 | 1.000 | 0.239 | 1.000 | `[]` |
| 33 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1099 | 1.000 | 0.219 | 1.000 | `[]` |
| 34 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0996 | 1.000 | 0.244 | 1.000 | `[]` |
| 35 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0879 | 1.000 | 0.199 | 1.000 | `[]` |
| 36 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1243 | 1.000 | 0.188 | 1.000 | `[]` |
| 37 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1032 | 1.000 | 0.175 | 1.000 | `[]` |
| 38 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1140 | 1.000 | 0.218 | 0.718 | `[]` |
| 39 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1159 | 1.000 | 0.229 | 1.000 | `[]` |
| 40 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1017 | 1.000 | 0.163 | 1.000 | `[]` |
| 41 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1056 | 1.000 | 0.115 | 1.000 | `[]` |
| 42 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1007 | 1.000 | 0.183 | 1.000 | `[]` |
| 43 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1112 | 1.000 | 0.158 | 1.000 | `[]` |
| 44 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1017 | 1.000 | 0.212 | 1.000 | `[]` |
| 45 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0893 | 1.000 | 0.123 | 1.000 | `[]` |
| 46 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1181 | 1.000 | 0.227 | 1.000 | `[]` |
| 47 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1003 | 1.000 | 0.188 | 0.891 | `[]` |
| 48 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1101 | 1.000 | 0.268 | 0.739 | `[]` |
| 49 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1153 | 1.000 | 0.202 | 1.000 | `[]` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
