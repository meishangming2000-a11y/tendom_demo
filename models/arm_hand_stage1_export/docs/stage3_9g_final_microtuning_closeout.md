# Stage3.9G Final Microtuning Closeout

生成日期：2026-06-07

## 一句话结论

Stage3.9G 通过了本轮设定的同阈值 `100 / 100` gate。

这不是完整 ACT Transformer/CVAE 或 Diffusion Policy 已经成功，也不是 full-action 26 actuator 端到端控制已经可用。正确表述是：

- 当前可提升为 Stage3.9 的混合控制候选：视觉脚本手臂/手腕 + ACT-lite 捏持手指 chunk + Stage3.7D 全手 fallback + 触觉 repair + 视觉/触觉最终验收。
- 微调到这里应该停止。下一段进入 Stage3.10：从可用技能和安全层转向可训练模型。

## 本轮修了什么

Stage3.9F 暴露出 3 个失败：

1. full-hand learned branch 有 `2 / 50` lift/floor 失败。
2. pinch repair `preclose=0.08` 有 1 次 hold slip 略高于阈值。
3. pinch `preclose=0.10` 修掉 hold slip 后，出现 1 次 final vision low-confidence / occlusion。

Stage3.9G 对应修补：

1. full-hand 使用 Stage3.7D fallback，而不是继续微调 ACT-lite full-hand hand chunk。
2. pinch repair 使用 `preclose_delta=0.10`、`close_max=0.18`。
3. final verification 使用 `vision_tactile_corroborated`：严格视觉优先；如果最终视觉有可用 mask 但置信度略低，则必须同时满足 hold stable、pinch maintained、hold slip、crush、penetration、floor contact 等触觉/接触 gate 才能通过。

## 关键结果

| 评估 | episode | 结果 | 说明 |
| --- | ---: | ---: | --- |
| Stage3.9F ACT-lite + repair | 100 | `97 / 100` | 上一轮基线 |
| Stage3.9G full fallback + pinch verify | 100 | `100 / 100` | 本轮主验收 |
| Stage3.9G pinch-only known occlusion check | 50 | `50 / 50` | 复现并修掉 9F 的 final vision low-confidence case |

主验收：

- metadata：`metadata/stage3_9g_full_fallback_pinch_verify_100.json`
- report：`docs/stage3_9g_full_fallback_pinch_verify_100_report.md`
- total：`100 / 100`
- full hand：`50 / 50`
- pinch：`50 / 50`

full-hand summary：

- final lift mean：`0.103461 m`
- final lift min：`0.084014 m`
- hold stable mean：`1.000`
- hold max slip max：`0.285324`
- max crush max：`0.116773`
- max penetration max：`0.002335 m`

pinch summary：

- true lift mean：`0.104520 m`
- true lift min：`0.078207 m`
- vision lift mean：`0.116743 m`
- hold stable mean：`1.000`
- hold pinch fraction mean：`1.000`
- hold max slip max：`0.289010`
- max crush max：`0.176283`
- max penetration max：`0.003526 m`

仍然需要记录的风险：

- `early_contact_in_approach` 仍普遍存在。
- full-hand 仍有 `recovery_budget_exhausted`：`26 / 50`。
- transient max slip 仍高；本轮 gate 看的是 hold slip / 成功保持，不代表接触全过程已经优雅。

## final vision 修补是否真的生效

补充验证：

- metadata：`metadata/stage3_9g_pinch_verify_preclose010_50.json`
- report：`docs/stage3_9g_pinch_verify_preclose010_50_report.md`
- result：`50 / 50`

这组专门复现了 9F 的 pinch-only episode 36：

- trial：`back_large_lift`
- final vision confidence：`0.329125`
- final vision mask pixels：`624`
- vision lift：`0.131589 m`
- true lift：`0.124330 m`
- hold slip：`0.187913`
- 通过方式：`vision_tactile_corroborated`

解释：这不是放宽 slip/crush/penetration，而是承认最终相机在手遮挡时会低置信；只在视觉仍有 mask 和位置估计，并且触觉 hold 证据同时满足时才让它通过。

## 复现命令

Stage3.9G 主验收：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills full_hand_gentle_grasp,thumb_index_middle_pinch --trials cycle --episodes-per-skill 50 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --full-hand-control-mode stage3_7d_fallback --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.10 --pinch-repair-close-max 0.18 --pinch-final-verification-mode vision_tactile_corroborated --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9g_full_fallback_pinch_verify_100.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9g_full_fallback_pinch_verify_100_report.md
```

pinch-only final verification check：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_act_lite_chunk_policy_v0.py --checkpoint .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth --skills thumb_index_middle_pinch --trials cycle --episodes-per-skill 50 --random-offset-std 0.005 --execution-mode scripted_arm_predicted_hand --replan-interval 16 --pinch-repair-mode inactive_anchor_slip_close --pinch-repair-phases contact_settle,slow_lift,hold --pinch-repair-inactive-alpha 1.0 --pinch-repair-preclose-delta 0.10 --pinch-repair-close-max 0.18 --pinch-final-verification-mode vision_tactile_corroborated --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_9g_pinch_verify_preclose010_50.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_9g_pinch_verify_preclose010_50_report.md
```

## 如果成功

本轮已经成功，所以处理方式是：

- 停止继续微调 `preclose_delta` / `close_max` 这类小参数。
- 把 Stage3.9G 登记为当前 SkillZoo safety layer 候选。
- 进入 Stage3.10：围绕这个安全层扩展数据、训练正式 ACT/DP baseline、建立更大 benchmark。

## 如果失败

如果后续更大 benchmark 暴露失败，不回到随机调参，而按下面拆：

- full hand：查 fallback、lift/floor、recovery budget。
- pinch：查 final vision、hold slip、crush/penetration。
- 数据/模型：如果规则层修不到，再训练 phase-specific residual 或正式 ACT/DP。

## 边界

Stage3.9G 通过的是当前 MuJoCo 随机 pose-noise gate，不是硬件集成，不是真实摄像头，也不是完整端到端大模型。

下一段如果要推进模型，应该从 Stage3.10 开始，不再叫 Stage3.9 的微调。
