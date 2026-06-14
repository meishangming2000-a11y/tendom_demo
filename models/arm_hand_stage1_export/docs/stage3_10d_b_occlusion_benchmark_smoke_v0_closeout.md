# Stage3.10D-B Occlusion Benchmark v0 Closeout

- 生成时间：`2026-06-08T18:18:30`
- 状态：`PASS`
- 总成功：`4 / 4`
- 执行模式：`scripted_arm_predicted_hand`
- 边界：这不是 full-action 26 actuator ACT/DP，也不是硬件或真实摄像头集成。

## 这一步做了什么

Stage3.10D-B 在 10D-A 的基础上扩大样本，并加入显式视觉压力：初始 noisy-mask、最终 noisy-mask、最终 synthetic occluder，以及 occlusion-aware 视觉/触觉融合验收。

## Case 汇总

| case | 含义 | 成功 | 视觉压力 | final accepted_by | 主要风险 |
| --- | --- | ---: | --- | --- | --- |
| `final_occluder45_occlusionaware_pose008` | 最终视觉 synthetic occluder 45% + occlusion-aware 融合验收 | 4 / 4 | `initial=none, final=synthetic_occluder_45` | `{'none': 2, 'vision_tactile_occlusion_aware': 2}` | `{'early_contact_in_approach': 4, 'transient_or_hold_slip': 2, 'recovery_budget_exhausted': 2, 'transient_slip_high': 2}` |

## 关键观察

- D-B 合计 `4 / 4`。
- `strict_vision` case 用来检查最终视觉能否独立验收；`vision_tactile_occlusion_aware` case 用来检查最终视觉被污染但仍有 mask 证据时，触觉稳定持握能否作为融合兜底。
- 如果 occlusion-aware 通过，它不是“纯视觉量到了 lift”，而是“低置信视觉仍看到目标局部 + 触觉持握稳定 + 无地面接触”的传感器融合判定。
- 仍需要继续报告 `early_contact_in_approach`、`transient_slip_high`、hold slip、crush 和 penetration；不能因为最终验收过了就忽略过程风险。

## 如果成功

下一步可以进入 Stage3.10D-C：把失败/边界 case 纳入 safety-labeled 数据，训练或评估一个显式 occlusion-aware safety head，或者开始 staged full-action repair。

## 如果失败

先按失败来源拆：初始视觉污染导致接近误差、最终视觉完全不可见、触觉 hold 实际失败，还是 occlusion-aware 判定条件太松/太紧。不要放宽 slip、crush、penetration 阈值。
