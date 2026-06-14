# Stage3.10D-C Occlusion Safety Head v0 Closeout

- 生成时间：`2026-06-09T02:49:34`
- 状态：`PASS`
- episode 样本：`200`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_10d_c_occlusion_safety_head_dataset_v0.npz`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10d_c_occlusion_safety_head_v0.npz`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_10d_c_occlusion_safety_head_v0.json`
- 边界：这是 MuJoCo episode-level safety evidence head；不是 full-action ACT/DP，也不是硬件/真实摄像头集成。

## 这一步做了什么

D-B v1 已经能在遮挡/noisy-vision 下通过 `100 / 100`，但里面仍有经验规则：多帧视觉选择、`accepted_nominal` 质量适配、最终视觉/触觉融合验收，以及更早的 pinch tactile fallback。D-C 把 D-B v0/v1 的闭环结果抽成监督数据，训练一个轻量多标签 safety head，用来检查这些规则是否能被机器可读地表达出来。

## 标签分布

| label | positive / total | 含义 |
| --- | ---: | --- |
| `initial_quality_adapter_required` | `20 / 200` | 初始视觉通过但质量字段偏 noisy，需要控制侧质量适配 |
| `final_tactile_handoff_required` | `40 / 200` | 最终视觉不够强，需要触觉 hold/局部视觉共同兜底 |
| `final_occlusion_aware_required` | `39 / 200` | 最终遮挡场景下应走 occlusion-aware 验收 |
| `pinch_repair_required_or_active` | `100 / 200` | 捏持过程中需要或触发 repair/fallback |
| `strict_final_vision_safe` | `48 / 200` | 严格最终视觉足够确认捏持成功 |
| `hold_safe` | `188 / 200` | 真实 hold/slip/crush/penetration/floor-contact 均在门内 |
| `failure_or_blocked` | `12 / 200` | episode 失败或被 failure reason 阻塞 |
| `floor_or_hold_failure` | `11 / 200` | 地面接触或 hold 不稳定类失败 |

## Random validation

- val mean accuracy：`1.000000`
- val mean evaluable recall：`1.000000`
- val mean evaluable F1：`1.000000`

| label | acc | precision | recall | F1 | positives | predicted positives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `initial_quality_adapter_required` | `1.000` | `1.000` | `1.000` | `1.000` | `6` | `6` |
| `final_tactile_handoff_required` | `1.000` | `1.000` | `1.000` | `1.000` | `7` | `7` |
| `final_occlusion_aware_required` | `1.000` | `1.000` | `1.000` | `1.000` | `7` | `7` |
| `pinch_repair_required_or_active` | `1.000` | `1.000` | `1.000` | `1.000` | `18` | `18` |
| `strict_final_vision_safe` | `1.000` | `1.000` | `1.000` | `1.000` | `10` | `10` |
| `hold_safe` | `1.000` | `1.000` | `1.000` | `1.000` | `39` | `39` |
| `failure_or_blocked` | `1.000` | `1.000` | `1.000` | `1.000` | `1` | `1` |
| `floor_or_hold_failure` | `1.000` | `1.000` | `1.000` | `1.000` | `1` | `1` |

## v0 -> v1 holdout

额外检查：只用 D-B v0 训练，再在 D-B v1 上测试，看看安全头能否识别修补后的 v1 事件分布。这个不是最终推广门槛，因为 v1 没有失败样本，但它能检查 occlusion/adapter/repair 标签是否仍可读。

- v1 holdout mean accuracy：`0.760000`
- v1 holdout mean evaluable recall：`1.000000`
- v1 holdout mean evaluable F1：`0.858399`

## 判断

- `stage3_10d_c_ready_for_d_d`：`True`
- 这一步说明：我们已经不只是会跑过 D-B，而是能把“视觉质量异常、最终遮挡、触觉兜底、捏持 repair、真实 hold 失败”整理成可训练/可评估的安全证据。
- 仍然不能夸大：这个 head 使用 episode-level 事后证据，下一步要么把它接进 evaluator 的在线 summary 检查，要么导出逐帧版本接回 ACT/DP 数据。

## 如果成功

进入 Stage3.10D-D：用 D-C 的 safety head 重新扫描 D-B v1 和一个新增 stress 小基准，确认它不会把遮挡成功样本误判成失败，也不会把真实 hold/floor-contact 失败放过。

## 如果失败

先查标签定义和样本覆盖：尤其是失败样本只有 D-B v0 的 12 条，不能靠放宽 slip/crush/penetration 阈值过关。必要时再补跑专门的失败采样，而不是继续微调单个 demo。
