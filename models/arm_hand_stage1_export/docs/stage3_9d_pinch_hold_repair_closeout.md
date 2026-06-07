# Stage3.9D Pinch Hold-Slip Repair Closeout

生成日期：2026-06-07

## 一句话结论

Stage3.9D 已经把 ACT-lite v1_pinch30 在 `right_low_zminus` 上的确定性 hold-slip 失败修到通过。修补方式不是放宽阈值，而是在捏持的 `contact_settle / slow_lift / hold` 阶段加入一个很小的触觉安全残差：

- 非主动手指回拉到脚本捏持安全姿态，避免 ring/little 抢接触。
- thumb/index/middle 预加载 `0.08` 的轻微闭合量，防止抬升刚开始时滑移已经发生。
- 保持原有 hold slip、crush、penetration、floor contact 验收阈值。

## 为什么这样修

v1_pinch30 在 cycle 评估中是 `9 / 10`，唯一失败是 `right_low_zminus`。失败细节：

- 真实抬升已经足够：约 `0.0986 m`。
- 视觉抬升也足够：约 `0.1010 m`。
- pinch contact fraction 是 `1.0`。
- 失败只来自 hold slip：`0.692 > 0.35`。
- 最终接触区域出现 thumb/middle/little，说明非主动手指和主动捏持接触之间有漂移。

单纯加宽 MLP 只把 right_low hold slip 从 `0.692` 降到 `0.680`，仍失败。所以这不是简单容量问题。

## 实现位置

主文件：

- `eval_stage3_act_lite_chunk_policy_v0.py`

新增参数：

- `--pinch-repair-mode inactive_anchor_slip_close`
- `--pinch-repair-phases contact_settle,slow_lift,hold`
- `--pinch-repair-inactive-alpha 1.0`
- `--pinch-repair-preclose-delta 0.08`
- `--pinch-repair-close-max 0.16`

默认 `--pinch-repair-mode none` 保持原 baseline 可复现；Stage3.9D 需要显式打开 repair 参数。

## 验收结果

### right_low_zminus 单场景

命令输出：

- metadata：`metadata/stage3_9d_pinch_hold_repair_right_low_x5.json`
- report：`docs/stage3_9d_pinch_hold_repair_right_low_x5_report.md`

结果：

- 成功：`5 / 5`
- true lift mean：`0.102960 m`
- vision lift mean：`0.109371 m`
- hold stable fraction：`1.000`
- hold pinch fraction：`1.000`
- hold max slip：`0.202691`
- max crush risk：`0.124869`
- max penetration：`0.002497 m`

### cycle 10 组

命令输出：

- metadata：`metadata/stage3_9d_pinch_hold_repair_cycle10.json`
- report：`docs/stage3_9d_pinch_hold_repair_cycle10_report.md`

结果：

- 成功：`10 / 10`
- full hand：`5 / 5`
- thumb/index/middle pinch：`5 / 5`
- pinch true lift mean：`0.101945 m`
- pinch hold stable fraction：`1.000`
- pinch hold pinch fraction：`1.000`
- pinch hold max slip max：`0.203477`
- pinch max crush risk max：`0.170027`
- pinch max penetration max：`0.003401 m`

## 推荐复现实验命令

right_low 验收：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills thumb_index_middle_pinch --trials right_low_zminus --episodes-per-skill 5 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.08 --pinch-repair-close-max 0.16
```

cycle 10 组验收：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills full_hand_gentle_grasp,thumb_index_middle_pinch --trials cycle --episodes-per-skill 5 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.08 --pinch-repair-close-max 0.16
```

## 边界

这仍然不是完整 ACT/DP：

- 手臂/手腕还是脚本化视觉引导。
- ACT-lite 仍是 MLP action chunk predictor，不是 ACT Transformer/CVAE，也不是 Diffusion Policy。
- repair 是一个规则残差，不是神经网络学出来的 residual。

但这一步很有价值：它证明了 learned chunk hand policy 可以和触觉安全残差组合，通过 previously failing 的确定性捏持边界。

## 如果成功

下一步可以进入 Stage3.9E：

- 把 repair residual 做成 SkillZoo 的 learned-policy safety layer。
- 做随机 pose-noise 评估，而不只看 10 个固定 cycle。
- 再决定是否训练正式 ACT Transformer/CVAE 或 Diffusion Policy。

## 如果失败

如果随机姿态下失败，优先检查：

- preclose 是否过强导致 crush/penetration 上升。
- 非主动手指 anchor 是否影响其他捏持姿态。
- 是否需要把 repair 从规则残差改成 phase-specific learned residual。
