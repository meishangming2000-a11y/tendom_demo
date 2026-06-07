# Stage3.9E Random Pose Repair Closeout

生成日期：2026-06-07

## 一句话结论

Stage3.9E 已经通过随机位姿扰动验收：同一个 ACT-lite v1_pinch30 checkpoint，在 `scripted_arm_predicted_hand` 模式下，不加 Stage3.9D repair 是 `27 / 30`，加上 `inactive_anchor_slip_close` repair 后提升到 `30 / 30`。

这说明 Stage3.9D 的捏持触觉安全残差不只是修好了固定的 `right_low_zminus`，在 `0.005 m` pose-noise 随机扰动下也能修掉多种捏持失败。

## 实验目的

Stage3.9D 的固定验收已经通过：

- `right_low_zminus` 单场景捏持：`5 / 5`
- 固定 cycle 10 组：`10 / 10`

Stage3.9E 要回答的是：这个 repair 是否只是针对固定 10 组过拟合，还是能在随机位姿扰动下继续提升闭环表现。

## 实验设置

共同条件：

- checkpoint：`checkpoints/stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 技能：`full_hand_gentle_grasp,thumb_index_middle_pinch`
- trials：`cycle`
- episodes per skill：`15`
- 总 episode：`30`
- pose-noise：`--random-offset-std 0.005`
- execution mode：`scripted_arm_predicted_hand`
- replan interval：`16`

唯一主要变量：

- 对照组：`--pinch-repair-mode none`
- repair 组：`--pinch-repair-mode inactive_anchor_slip_close`

repair 参数：

- `--pinch-repair-phases contact_settle,slow_lift,hold`
- `--pinch-repair-inactive-alpha 1.0`
- `--pinch-repair-preclose-delta 0.08`
- `--pinch-repair-close-max 0.16`

## 结果对比

| 组别 | 总成功 | 全手成功 | 捏持成功 | 捏持 true lift mean | 捏持 hold max slip mean | 捏持 hold max slip max | 捏持 max crush max | 捏持 max penetration max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no repair | `27 / 30` | `15 / 15` | `12 / 15` | `0.081956 m` | `0.279706` | `1.000000` | `0.148082` | `0.002962 m` |
| repair | `30 / 30` | `15 / 15` | `15 / 15` | `0.103208 m` | `0.192206` | `0.294448` | `0.172517` | `0.003450 m` |

主要结论：

- full hand 全手抓取两组都是 `15 / 15`，所以差异主要来自捏持分支。
- no repair 的捏持分支失败 `3 / 15`，失败集中在抬升不足、视觉确认不足、hold slip 和 floor contact。
- repair 把捏持分支提升到 `15 / 15`，并把捏持 hold max slip 的最大值从 `1.000000` 压到 `0.294448`。
- repair 会让捏持 max crush 和 max penetration 有所上升，但仍低于现有安全阈值：crush `< 0.35`，penetration `< 0.004 m`。

## 对照组失败详情

不加 repair 的 3 个失败 episode：

| ep | 场景 | 主要失败 | true lift | hold slip | 备注 |
| ---: | --- | --- | ---: | ---: | --- |
| 21 | `back_large_lift` | `vision_lift_too_small` | `0.0437 m` | `1.000` | 抬升不足并伴随 hold slip 高 |
| 23 | `lifted_diag` | `vision_lift_too_small` | `-0.0221 m` | `0.000` | 没有建立有效捏持，鸡蛋仍接触地面 |
| 29 | `right_low_zminus` | `vision_lift_too_small` | `-0.0018 m` | `1.000` | 复现了右低边界下的捏持保持失败 |

对照组失败原因计数：

- `vision_lift_too_small`：`3`
- `true_lift_too_small`：`3`
- `hold_slip_score_high`：`2`
- `egg_still_touching_floor`：`2`
- `no_thumb_finger_pinch_before_lift`：`1`
- `pinch_not_maintained_in_hold`：`1`
- `hold_tactile_unstable`：`1`

## 复现命令

repair 组：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills full_hand_gentle_grasp,thumb_index_middle_pinch --trials cycle --episodes-per-skill 15 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.08 --pinch-repair-close-max 0.16 --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9e_random_pose_repair_30.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9e_random_pose_repair_30_report.md
```

no-repair 对照组：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills full_hand_gentle_grasp,thumb_index_middle_pinch --trials cycle --episodes-per-skill 15 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode none --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9e_random_pose_no_repair_30.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9e_random_pose_no_repair_30_report.md
```

## 边界

这一步仍然不是完整 ACT/DP：

- 手臂/手腕仍然是视觉脚本控制。
- ACT-lite 只控制手指/手部 actuator，是 MLP action chunk predictor。
- Stage3.9D repair 是规则触觉残差，不是 ACT Transformer/CVAE 或 Diffusion Policy 学出来的策略。
- 所有结果仍然是 MuJoCo 虚拟摄像机 + 合成触觉/滑移，不是 Stage4 真实硬件。

## 当前可提升判断

可以把 `v1_pinch30 + inactive_anchor_slip_close repair` 视为 Stage3.9 当前最稳的混合控制候选，但还不应称为完整 learned policy baseline。

推荐表述：

- 正确：`scripted_arm_predicted_hand + ACT-lite hand chunk + tactile repair`
- 不正确：`完整 ACT/DP 已经学会抓鸡蛋`

## 如果成功

下一步进入 Stage3.9F：

- 做更大的随机评估，例如 `60` 或 `100` episode。
- 和纯脚本 Stage3.7D 全手、Stage3.8B 捏持 baseline 做同条件对比。
- 把 repair 参数和安全阈值登记成 SkillZoo 的可选 safety layer。
- 继续记录 transient slip 和 early contact，不因为最终成功率高就忽略过程风险。

## 如果失败

如果更大随机评估暴露失败，优先按下面顺序诊断：

- true lift 失败：检查 approach z、active finger closure 和 preclose 是否不足。
- hold slip 失败：检查 inactive finger anchor 与主动捏持是否冲突。
- crush/penetration 上升：降低 `preclose_delta` 或限制 `close_max`。
- 视觉确认失败：区分最终相机遮挡和真实没有抬起。
