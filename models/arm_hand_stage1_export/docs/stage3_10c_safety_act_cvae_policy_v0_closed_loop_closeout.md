# Stage3.10C-B Safety ACT/CVAE Closed-Loop Closeout

日期：2026-06-08

## 这一步做了什么

本轮不再继续微调 Stage3.9/Stage3.10A 的参数，而是把 Stage3.10C-A 训练出的 `SafetyACTCVAEChunkPolicy` 放回 MuJoCo 做闭环评估。

新增入口：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_10c_safety_act_cvae_policy_v0.py
```

这个 evaluator 复用 Stage3 ACT-lite 的闭环执行框架，但加载 Stage3.10C 的 safety ACT/CVAE 模型，并在预测 action chunk 时输入：

- 当前 `obs`
- `skill_id`
- `phase_id`
- 当前 safety/risk 标签

模型输出：

- `16` step action chunk
- `16` step safety label logits

## 结果

### scripted_arm_predicted_hand

命令对应报告：

```text
simulations/models/arm_hand_stage1_export/docs/stage3_10c_safety_act_cvae_policy_v0_closed_loop_cycle10_report.md
```

结果：`10 / 10` PASS。

- full hand gentle grasp：`5 / 5`
- thumb index middle pinch：`5 / 5`
- full hand mean final lift：`0.101617 m`
- pinch mean true lift：`0.101988 m`
- full hand mean hold slip：`0.190060`
- pinch mean hold slip：`0.171844`

边界：

- 这不是 viewer demo。
- 这不是真实硬件。
- 这不是 full-action 26 actuator 成功。
- 风险仍然存在：`early_contact_in_approach` 每组都有；pinch 分支仍有 `transient_slip_high`。

### full_action

命令对应报告：

```text
simulations/models/arm_hand_stage1_export/docs/stage3_10c_safety_act_cvae_policy_v0_closed_loop_full_action_smoke.md
```

结果：`0 / 1` FAIL。

失败原因集中在：

- `vision_lift_too_small`
- `true_lift_too_small`
- `no_thumb_finger_pinch_before_lift`
- `pinch_not_maintained_in_hold`
- `hold_tactile_unstable`
- `egg_still_touching_floor`

这说明当前 Stage3.10C 模型可以先作为“视觉脚本手臂/手腕 + 学习手指 chunk”的闭环候选，但还不能提升为 full-action ACT/DP 控制器。

## 当前结论

Stage3.10C 已经从“离线训练完成”推进到“初步闭环验证通过”。但这个通过只限于 `scripted_arm_predicted_hand` 模式。

当前推荐表述：

```text
Stage3.10C-B initial closed-loop eval passed 10/10 in scripted_arm_predicted_hand mode, but full_action smoke failed 0/1. Not hardware, not full-action ACT/DP promotion.
```

## 如果成功

下一步进入 Stage3.10C-C 或 Stage3.10D：扩大 benchmark。

推荐验收：

- `scripted_arm_predicted_hand`：至少 `50 / 50`
- 同时覆盖 full hand 和 pinch
- 加入 pose-noise、遮挡、held-out trial
- 与 Stage3.10A safety layer 同场景对比
- 报告 success、final vision、hold slip、transient slip、crush、penetration、floor contact、safety head 预测

## 如果失败

不回到简单阈值微调。优先拆：

- full-action 的 arm/wrist 表示是否需要分阶段模型或 residual policy
- action chunk 的执行间隔是否过长
- phase-specific head 是否比单一 head 更稳
- safety head 是否提前预测了风险
- 训练数据是否缺少失败恢复样本
