# Stage3.10D-B Occlusion Benchmark v1 Closeout

- 生成时间：`2026-06-08T18:57:53`
- 状态：`PASS`
- 总成功：`100 / 100`
- 执行模式：`scripted_arm_predicted_hand`
- 边界：这不是 full-action 26 actuator ACT/DP 成功，也不是硬件、真实摄像头或真实触觉集成。

## 这一步做了什么

Stage3.10D-B v0 扩大了 10D-A 的鲁棒性测试，并加入显式视觉压力：初始 noisy mask、最终 noisy mask、最终 synthetic occluder，以及 occlusion-aware 视觉/触觉融合验收。v0 的正式结果是 `88 / 100`，主要卡在三类问题：

- `initial_maskdrop30_pose005`：初始视觉 mask dropout 30% 时，捏持分支 `0 / 10`。
- `pose010_corroborated`：10mm 位姿噪声下有 1 个真实捏持失败。
- `final_maskdrop55_occlusionaware_pose005`：最终 mask dropout 55% 下有 1 个“真实抓住但最终视觉证据过少”的失败。

v1 做了三项修补：

- noisy virtual-camera 估计结果补充 `visibility_fraction`、`clean_visibility_fraction` 和失败时的 `mask_retention_ratio`，避免把 30% mask dropout 误表达成“完全遮挡”。
- 初始/最终压力视觉支持多帧候选选择：本次正式 v1 用 `initial x3`、`final x5`。
- 对已通过感知门的初始视觉，控制策略使用 `policy_vision_quality_mode=accepted_nominal`：位姿仍来自 noisy estimator，原始 confidence/mask/visibility 仍写入报告，但给 learned hand policy 的质量字段拉回训练分布，避免 clean-only 训练模型被 out-of-distribution 质量字段带坏。
- 捏持触觉 fallback 从 `slow_lift,hold` 提前扩展到 `pinch_close,contact_settle,slow_lift,hold`，并使用 `pinch_repair_mode=all`、`expert_alpha=0.35`，在接触异常时更早回到保守 scripted hand shape。

## 验收结果

| case | 含义 | v1 成功 | 视觉压力/策略 | final accepted_by |
| --- | --- | ---: | --- | --- |
| `pose008_strictvision` | 8mm 位姿噪声 + 严格最终视觉 | `20 / 20` | `initial=none x3, final=none x5, policy_quality=accepted_nominal` | `{'none': 10, 'strict_vision': 10}` |
| `pose010_corroborated` | 10mm 位姿噪声 + 视觉/触觉终验 | `20 / 20` | `initial=none x3, final=none x5, policy_quality=accepted_nominal` | `{'none': 10, 'strict_vision': 9, 'vision_tactile_corroborated': 1}` |
| `initial_maskdrop30_pose005` | 初始视觉 mask dropout 30% + 5mm 位姿噪声 | `20 / 20` | `initial=mask_dropout_30 x3, final=none x5, policy_quality=accepted_nominal` | `{'none': 10, 'strict_vision': 10}` |
| `final_maskdrop55_occlusionaware_pose005` | 最终视觉 mask dropout 55% + occlusion-aware 融合验收 | `20 / 20` | `initial=none x3, final=mask_dropout_55 x5, policy_quality=accepted_nominal` | `{'none': 10, 'vision_tactile_occlusion_aware': 10}` |
| `final_occluder45_occlusionaware_pose008` | 最终视觉 synthetic occluder 45% + occlusion-aware 融合验收 | `20 / 20` | `initial=none x3, final=synthetic_occluder_45 x5, policy_quality=accepted_nominal` | `{'none': 10, 'vision_tactile_occlusion_aware': 10}` |

关键对比：

- v0：`88 / 100`，状态 `BLOCKED`。
- v1：`100 / 100`，状态 `PASS`。
- `initial_maskdrop30_pose005` 从 v0 的 `10 / 20` 修到 v1 的 `20 / 20`。
- `pose010_corroborated` 从 v0 的 `19 / 20` 修到 v1 的 `20 / 20`。
- `final_maskdrop55_occlusionaware_pose005` 从 v0 的 `19 / 20` 修到 v1 的 `20 / 20`。

## 仍然不能夸大的地方

- `vision_tactile_occlusion_aware` 不是纯视觉量到 lift；它表示低置信/局部视觉证据 + 触觉稳定持握 + 无地面接触共同通过。
- `accepted_nominal` 是控制侧 OOD 防护，不等于模型已经在 noisy vision 质量字段上学会了泛化。下一步应该把 noisy/occlusion 样本纳入 safety-labeled 数据或训练集。
- v1 仍然持续出现 `early_contact_in_approach` 和 `transient_slip_high` 风险；hold slip、crush、penetration 在本次门内通过，但过程风险仍要继续报告。
- full-action 26 actuator ACT/DP 仍未通过闭环门槛，当前成功边界仍是 scripted arm/wrist + learned hand/fingers + safety/fallback。

## 如果成功

进入 Stage3.10D-C：把 v0 失败样本、v1 修复样本、occlusion-aware final verification、accepted_nominal quality adapter、提前触觉 fallback 都整理进 safety-labeled 数据/评估，准备训练或评估更显式的 occlusion/noisy-vision safety head。

## 如果失败

优先拆分失败来源：位姿估计错误、质量字段 OOD、最终视觉证据不足、真实触觉 hold 失败、还是 fallback 引入 crush/penetration 风险。不要通过放宽 slip、crush、penetration 阈值来过关。
