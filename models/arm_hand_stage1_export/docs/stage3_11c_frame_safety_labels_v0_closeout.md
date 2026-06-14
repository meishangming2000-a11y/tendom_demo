# Stage3.11C Frame-Level Safety Labels v0 Closeout

- 生成时间：`2026-06-09T14:47:15`
- 状态：`PASS`
- 粒度：`trace_frame_sampled_from_evaluator`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_11c_frame_safety_labels_v0.npz`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_11c_frame_safety_labels_v0.jsonl`
- 边界：MuJoCo-only；不是 full-action ACT/DP promotion；不是真实摄像头、真实触觉、超声或硬件 runtime。

## 做了什么

Stage3.11C 把 Stage3.10C clean evaluator trace 和 Stage3.11B shadow evaluator trace 导出成逐 trace-frame 标签。每一行保留 source/case/episode/skill/phase/step，并给出视觉退化、视觉冻结、触觉接管、repair 配置、repair 实际激活、recovery、物理风险和失败边界标签。

这版先解决 Stage3.11B 暴露出的标签定义问题：`repair_configured` 和 `repair_active` 被拆成两个标签。前者表示这个 episode 配置了 repair，后者只在 trace frame 里真的触发 repair 时为 1。

## 总结果

- trace frames：`2663`
- episodes：`164`
- label shape：`[2663, 17]`
- 缺失的必需正样本：`[]`
- 缺失的必需覆盖桶：`[]`
- repair 配置/激活拆分检查：`True`

## Label 正样本计数

| label | trace-frame count | span-weighted step count |
| --- | ---: | ---: |
| `vision_degraded` | 1604 | 375851 |
| `vision_freeze` | 1449 | 341611 |
| `initial_quality_adapter_required` | 750 | 180000 |
| `final_occlusion_aware_required` | 138 | 30408 |
| `tactile_handoff` | 144 | 31728 |
| `repair_configured` | 900 | 206797 |
| `repair_active` | 652 | 147277 |
| `recovery_active` | 34 | 8160 |
| `safety_intervention_active` | 686 | 155437 |
| `risk_slip_high` | 91 | 21840 |
| `risk_crush_high` | 0 | 0 |
| `risk_penetration_high` | 0 | 0 |
| `physical_risk_any` | 91 | 21840 |
| `hold_safe` | 1261 | 289620 |
| `failure_or_blocked` | 1 | 240 |
| `floor_or_hold_failure` | 1 | 240 |
| `risk_any` | 697 | 158077 |

## 覆盖范围

| bucket | source count | trace frames |
| --- | ---: | ---: |
| `clean` | 1 | 807 |
| `combined_hard` | 1 | 23 |
| `depth_noise` | 1 | 97 |
| `false_positive` | 1 | 97 |
| `mask_dropout` | 2 | 653 |
| `occlusion` | 1 | 328 |
| `pose_noise` | 2 | 658 |

## 发现的问题

- Stage3.11C v0 通过数据门槛：必需标签都有正样本，clean / pose-noise / mask dropout / occlusion / depth-noise / false-positive / combined_hard 覆盖齐全。
- 当前粒度是 evaluator trace-frame，不是 dense obs/action 每步数据；这适合先验收标签定义和覆盖率，后续如果要直接训练 ACT/DP 可做 Stage3.11C2 dense capture。
- `repair_configured` 明显多于 `repair_active`，说明 B 中的问题已经被结构性拆开，不再把配置当成真实触发。
- `risk_crush_high` 和 `risk_penetration_high` 为 0 不是失败：当前通过/边界数据没有超过 crush 或 penetration 阈值的帧，不能为了凑正样本伪造危险标签。

## 如果成功

进入 Stage3.11D：先训练或评估 safety-conditioned hand/residual policy，并与 Stage3.10E/Stage3.11B baseline 同场景对比。

## 如果失败

先修 label definition、source coverage、trace/frame 对齐或 dense capture，不把不可靠标签喂给策略训练。
