# Stage3.9F Random Pose Baseline Comparison Closeout

生成日期：2026-06-07

## 一句话结论

Stage3.9F 扩大随机 pose-noise 到 `100` 个 episode 后，确认了 Stage3.9D repair 的价值，但也证明它还不能直接提升为 `100 / 100` 的 SkillZoo safety layer。

关键结果：

- ACT-lite v1_pinch30 + Stage3.9D repair：`97 / 100`
- ACT-lite v1_pinch30 no-repair：`84 / 100`
- Stage3.7D scripted full-hand baseline：`50 / 50`
- Stage3.8B scripted selected pinch baseline：`38 / 50`
- 更强捏持 repair probe：`49 / 50`，剩余失败是最终视觉遮挡/低置信，不是滑移或真实抬升失败

这说明：

- repair 对捏持非常有效：捏持从 no-repair 的 `36 / 50` 提升到 `49 / 50`。
- ACT-lite repair 的捏持已经强于 Stage3.8B 原脚本 selected pinch baseline。
- ACT-lite 的全手分支还不如 Stage3.7D 脚本 baseline 稳，100 组里出现了 2 次 lift/floor 失败。
- 下一步不能直接训练更大模型糊过去，要先做两个小修补：全手 learned branch 回退/repair，捏持最终视觉验收抗遮挡。

## 实验目的

Stage3.9E 已在 30 组随机 pose-noise 中通过：

- repair：`30 / 30`
- no-repair：`27 / 30`

Stage3.9F 的目的不是继续微调一个 demo，而是放大样本并加 baseline 对照：

- repair 是否能在 `100` 组中继续保持满分。
- no-repair 与 repair 的差距是否稳定存在。
- ACT-lite + repair 和脚本 SkillZoo baseline 相比到底强在哪里、弱在哪里。

## 共同设置

- MuJoCo only，不接真实摄像头、不接真实触觉或硬件。
- 随机扰动：`--random-offset-std 0.005`
- trial：`cycle`
- ACT-lite checkpoint：`checkpoints/stage3_act_lite_chunk_policy_v1_pinch30.pth`
- ACT-lite execution mode：`scripted_arm_predicted_hand`
- replan interval：`16`
- 默认阈值不放宽：hold slip、crush、penetration、floor contact 仍按 evaluator 原 gate。

## 结果总表

| 组别 | episode | 成功 | 全手成功 | 捏持成功 | 主要失败 |
| --- | ---: | ---: | ---: | ---: | --- |
| ACT-lite repair `preclose=0.08` | 100 | `97 / 100` | `48 / 50` | `49 / 50` | 全手 lift/floor 2 次；捏持 hold slip 1 次 |
| ACT-lite no-repair | 100 | `84 / 100` | `48 / 50` | `36 / 50` | 捏持 lift/vision/hold/floor 多类失败 |
| scripted full-hand Stage3.7D | 50 | `50 / 50` | `50 / 50` | n/a | 无失败，但 recovery budget 常耗尽 |
| scripted selected pinch Stage3.8B | 50 | `38 / 50` | n/a | `38 / 50` | 捏持 lift/vision/hold slip 失败 |
| ACT-lite pinch repair probe `preclose=0.10` | 50 | `49 / 50` | n/a | `49 / 50` | 1 次 final vision failed/occluded |

## ACT-lite repair 100 组

输出：

- metadata：`metadata/stage3_9f_random_pose_repair_100.json`
- report：`docs/stage3_9f_random_pose_repair_100_report.md`

结果：

- 总成功：`97 / 100`
- 全手：`48 / 50`
- 捏持：`49 / 50`
- 捏持 true lift mean：`0.104330 m`
- 捏持 hold stable mean：`0.999943`
- 捏持 hold pinch fraction mean：`1.000`
- 捏持 hold max slip max：`0.354675`
- 捏持 max crush max：`0.172409`
- 捏持 max penetration max：`0.003448 m`

失败 episode：

| ep | skill | trial | terminal reason | true lift | hold slip | 解释 |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 37 | full hand | `lifted_center` | `insufficient_lift_height` | `-0.019151 m` | `0.000` | ACT-lite 全手分支没有建立有效抬升，最终仍落地 |
| 41 | full hand | `left_low_nominal` | `insufficient_lift_height` | `-0.016072 m` | `0.000` | 同上 |
| 64 | pinch | `right_low_zminus` | `hold_slip_score_high` | `0.098078 m` | `0.354675` | 真值/视觉抬升和 pinch 都成立，但 hold slip 比 `0.35` 高 `0.004675` |

## no-repair 100 组

输出：

- metadata：`metadata/stage3_9f_random_pose_no_repair_100.json`
- report：`docs/stage3_9f_random_pose_no_repair_100_report.md`

结果：

- 总成功：`84 / 100`
- 全手：`48 / 50`
- 捏持：`36 / 50`
- 捏持 true lift mean：`0.074393 m`
- 捏持 hold stable mean：`0.796171`
- 捏持 hold pinch fraction mean：`0.810486`
- 捏持 hold max slip max：`1.000`
- 主要失败：`vision_lift_too_small`、`true_lift_too_small`、`egg_still_touching_floor`、`hold_slip_score_high`、`final_vision_failed_or_occluded`

对照结论：

- repair 把捏持成功从 `36 / 50` 提高到 `49 / 50`。
- repair 明显提高了 true lift、hold stable、pinch fraction，并降低 hold slip。
- 全手失败与 pinch repair 无关，两组都是 `48 / 50`。

## 脚本 baseline 对照

### Stage3.7D full hand

输出：

- metadata：`metadata/stage3_9f_scripted_full_hand_recovery_50.json`
- report：`docs/stage3_9f_scripted_full_hand_recovery_50_report.md`

结果：

- 成功：`50 / 50`
- hold stable mean：`1.000`
- hold max slip max：`0.315078`
- max crush max：`0.127079`
- max penetration max：`0.002542 m`
- risk：`recovery_budget_exhausted` 出现 `26 / 50`

结论：

ACT-lite 全手分支的 2 次失败不是场景本身不可抓；Stage3.7D 脚本/阶段式全手 baseline 在同样随机扰动下更稳。

### Stage3.8B selected pinch

为避免重新跑完整搜索，本轮给 `eval_stage3_pinch_grasp_v0.py` 增加了 `--candidate-config`，可以直接加载：

- `metadata/stage3_pinch_grasp_training_v0_selected.json`

输出：

- metadata：`metadata/stage3_9f_scripted_pinch_selected_50.json`
- report：`docs/stage3_9f_scripted_pinch_selected_50_report.md`

结果：

- 成功：`38 / 50`
- hold max slip max：`1.000`
- max crush max：`0.186513`
- max penetration max：`0.003730 m`

结论：

ACT-lite + repair 的捏持分支已经明显强于 Stage3.8B 原脚本 selected pinch baseline。

## 小修补 probe

为了确认唯一捏持 hold-slip 失败是否能修，本轮额外跑了一个轻量 probe：

- `--pinch-repair-preclose-delta 0.10`
- `--pinch-repair-close-max 0.18`

输出：

- metadata：`metadata/stage3_9f_pinch_repair_preclose010_50.json`
- report：`docs/stage3_9f_pinch_repair_preclose010_50_report.md`

结果：

- 捏持成功：`49 / 50`
- hold max slip max：`0.268310`
- max crush max：`0.181231`
- max penetration max：`0.003625 m`
- 唯一失败：`final_vision_failed_or_occluded`
- 失败 episode 的真实抬升：`0.124330 m`

解释：

这个 probe 修掉了 slip 问题，但出现了一次最终视觉验收失败。因为该 episode 的 true lift、hold stable、pinch 和 slip 都是好的，所以这更像最终相机遮挡/置信度问题，而不是控制失败。

## 复现命令

ACT-lite repair 100：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills full_hand_gentle_grasp,thumb_index_middle_pinch --trials cycle --episodes-per-skill 50 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.08 --pinch-repair-close-max 0.16 --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9f_random_pose_repair_100.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9f_random_pose_repair_100_report.md
```

ACT-lite no-repair 100：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills full_hand_gentle_grasp,thumb_index_middle_pinch --trials cycle --episodes-per-skill 50 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode none --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9f_random_pose_no_repair_100.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9f_random_pose_no_repair_100_report.md
```

Stage3.7D full hand baseline：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_contact_transition_recovery_v0.py --episodes 50 --random-offset-std 0.005 --transition-slip-threshold 0.29 --max-transition-hold-steps-per-phase 200 --recovery-progress-drop 0.01 --recovery-stable-window-steps 0 --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9f_scripted_full_hand_recovery_50.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9f_scripted_full_hand_recovery_50_report.md
```

Stage3.8B selected pinch baseline：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_pinch_grasp_v0.py --candidate-config .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_training_v0_selected.json --episodes-per-candidate 50 --trial cycle --random-offset-std 0.005 --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9f_scripted_pinch_selected_50.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9f_scripted_pinch_selected_50_report.md
```

捏持 stronger repair probe：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills thumb_index_middle_pinch --trials cycle --episodes-per-skill 50 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.10 --pinch-repair-close-max 0.18 --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9f_pinch_repair_preclose010_50.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9f_pinch_repair_preclose010_50_report.md
```

## 边界

Stage3.9F 不能被表述为“完整 ACT/DP 已经通过”。

正确表述：

- `ACT-lite + tactile repair` 对捏持帮助很大。
- 更大随机集暴露出当前混合候选仍有边界失败。
- full hand 可以暂时以 Stage3.7D 脚本 baseline 作为回退。
- pinch slip 可以通过略强 preclose 修掉，但最终视觉验收还要抗遮挡。

不正确表述：

- `100 / 100` 已通过。
- 已经可以提升为完整 SkillZoo safety layer。
- 已经完成 ACT Transformer/CVAE 或 Diffusion Policy。

## 如果成功

如果下一轮修补通过：

- 将全手分支设置为 Stage3.7D fallback 或训练 full-hand repair residual。
- 将捏持 preclose `0.10` 方案和最终视觉抗遮挡方案一起纳入候选。
- 再跑 `100 / 100`，通过后再登记为 SkillZoo safety layer。

## 如果失败

如果下一轮仍失败：

- 全手失败继续看 learned hand chunk 是否在 lift/contact_settle 阶段偏离 Stage3.7D。
- 捏持失败如果是视觉遮挡，优先修 final camera / multi-camera voting，不放宽 slip。
- 捏持失败如果回到 hold slip，再检查 preclose 与 crush/penetration 的安全余量。

## 下一步建议

开 Stage3.9G：专门做 `100 / 100` 修补。

验收建议：

- full hand：使用 Stage3.7D fallback 或 learned full-hand residual 后 `50 / 50`。
- pinch：使用 preclose `0.10` 或等价 learned repair 后 `50 / 50`。
- 不放宽 slip/crush/penetration 阈值。
- 如果最终视觉失败但 true lift/hold/pinch 都成功，先修视觉验收，而不是把它当控制失败。
