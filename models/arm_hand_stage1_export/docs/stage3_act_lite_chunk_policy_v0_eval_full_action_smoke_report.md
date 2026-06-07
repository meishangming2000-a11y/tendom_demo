# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T10:08:28`
- 状态：`FAIL`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v0.pth`
- 执行模式：`full_action`
- chunk 重规划间隔：`12`
- 成功数：`0 / 2`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 0 / 1 | `{'functional_approach_missed_true_egg': 1}` | `{'functional_approach_missed_true_egg': 1, 'insufficient_lift_height': 1, 'unstable_hold_tactile': 1, 'hold_slip_score_high': 1, 'egg_on_floor_after_hold': 1}` | `{'early_contact_in_approach': 1, 'transient_or_hold_slip': 1, 'hold_slip_high': 1}` |
| `thumb_index_middle_pinch` | 0 / 1 | `{'final_vision_failed_or_occluded': 1}` | `{'final_vision_failed_or_occluded': 1, 'true_lift_too_small': 1, 'pinch_not_maintained_in_hold': 1, 'hold_tactile_unstable': 1, 'egg_still_touching_floor': 1}` | `{'early_contact_in_approach': 1, 'transient_slip_high': 1, 'low_pinch_purity': 1, 'final_vision_occluded_or_low_confidence': 1}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | FAIL | `functional_approach_missed_true_egg` | -0.0054 | 0.000 | 1.000 | 1.000 | `['functional_approach_missed_true_egg', 'insufficient_lift_height', 'unstable_hold_tactile', 'hold_slip_score_high', 'egg_on_floor_after_hold']` |
| 1 | `thumb_index_middle_pinch` | `center_nominal` | FAIL | `final_vision_failed_or_occluded` | -0.0007 | 0.000 | 0.000 | 1.000 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
