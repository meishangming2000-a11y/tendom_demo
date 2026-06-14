# Stage3.10D Robustness Probe v0 Closeout

- 生成时间：`2026-06-08T17:45:46`
- 状态：`PASS`
- 总成功：`40 / 40`
- 执行模式：`scripted_arm_predicted_hand`
- 边界：这仍然不是 full-action 26 actuator ACT/DP，也不是硬件或真实摄像头集成。

## 这一步做了什么

Stage3.10D-A 把 Stage3.10C-C 已通过的 5mm 随机位姿 benchmark 往外推，先做小规模但多条件的鲁棒性探针：更强随机位姿噪声、严格最终视觉验收，以及两者组合。

## Case 汇总

| case | 含义 | 成功 | 状态 | 主要风险 |
| --- | --- | ---: | --- | --- |
| `pose008` | 8mm 随机位姿噪声 + 视觉/触觉终验 | 10 / 10 | `PASS` | `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 5, 'recovery_budget_exhausted': 4, 'transient_slip_high': 5}` |
| `pose010` | 10mm 随机位姿噪声 + 视觉/触觉终验 | 10 / 10 | `PASS` | `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 5, 'recovery_budget_exhausted': 3, 'transient_slip_high': 5}` |
| `strictvision_pose005` | 5mm 随机位姿噪声 + 严格最终视觉验收 | 10 / 10 | `PASS` | `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 4, 'recovery_budget_exhausted': 2, 'transient_slip_high': 5}` |
| `strictvision_pose008` | 8mm 随机位姿噪声 + 严格最终视觉验收 | 10 / 10 | `PASS` | `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 5, 'recovery_budget_exhausted': 4, 'transient_slip_high': 5}` |

## 关键观察

- 这批探针合计 `40 / 40`。
- `pose008` 和 `pose010` 说明 8mm/10mm 位姿噪声下，当前混合控制闭环还没有直接掉成功率。
- `strictvision_pose005` 和 `strictvision_pose008` 说明当前 pinch 结果不是完全靠 tactile 兜底才能通过最终验收；严格视觉终验短测仍然通过。
- 风险没有消失：`early_contact_in_approach` 仍然几乎每组都出现，pinch 的 `transient_slip_high` 仍然稳定出现，full hand 有时会触发 recovery budget exhaustion。
- 所以 Stage3.10D-A 的结论是：鲁棒性初探通过，但下一步应该扩大样本和引入更真实的遮挡/低可见度注入，而不是宣布模型已经泛化。

## 如果成功

进入 Stage3.10D-B：用同一个入口扩大到更正式的 benchmark，例如每个 case 40-100 组，并加入显式 noisy-mask / occlusion injector，把最终视觉失效从“自然遮挡”变成可控压力。

## 如果失败

不要放宽 slip 或 vision 阈值。先按失败来源拆开：随机位姿导致接近误差、严格视觉导致 final confidence 不足、还是 tactile hold 实际失败。之后再决定修 perception freeze、pinch repair，或者 staged full-action repair。
