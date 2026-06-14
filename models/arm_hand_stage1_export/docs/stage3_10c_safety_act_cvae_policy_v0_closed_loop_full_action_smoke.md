# Stage3.10C Safety ACT/CVAE Policy v0 闭环评估报告

- 生成时间：`2026-06-08T14:40:55`
- 状态：`FAIL`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10c_safety_act_cvae_policy_v0.pth`
- 执行模式：`full_action`
- chunk 重规划间隔：`16`
- 成功数：`0 / 1`
- 训练状态：`stage3_10c_safety_act_cvae_policy_v0_offline_trained_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `thumb_index_middle_pinch` | 0 / 1 | `{'vision_lift_too_small': 1}` | `{'vision_lift_too_small': 1, 'true_lift_too_small': 1, 'no_thumb_finger_pinch_before_lift': 1, 'pinch_not_maintained_in_hold': 1, 'hold_tactile_unstable': 1, 'egg_still_touching_floor': 1}` | `{'early_contact_in_approach': 1, 'transient_slip_high': 1, 'low_pinch_purity': 1}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `thumb_index_middle_pinch` | `center_nominal` | FAIL | `vision_lift_too_small` | -0.0105 | 0.000 | 0.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，Stage3.10C 模型只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- Stage3.10C 模型额外接收 `phase_id` 和当前 safety/risk 标签，并输出 action chunk 与 safety chunk；报告仍以真实闭环成功率为准，不用离线 loss 代替成功。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过 Stage3.10A safety layer baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.10A safety layer、Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认、safety 头是否提前预测风险。不要立刻回到小参数微调；优先调整 chunk 执行间隔、分技能头、phase-specific head 或 safety-conditioned 执行策略。
