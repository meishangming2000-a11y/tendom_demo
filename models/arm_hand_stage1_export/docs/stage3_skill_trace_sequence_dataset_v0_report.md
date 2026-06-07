# Stage3.9B2 Skill Trace Sequence Dataset v0 报告

- 生成时间：`2026-06-06T21:36:03`
- 状态：`PASS`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_trace_sequence_dataset_v0.jsonl`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_trace_sequence_dataset_v0.npz`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_skill_trace_sequence_dataset_v0.json`
- sequence count：`70`
- canonical training sequences：`40`
- success sequences：`64`
- total sampled timesteps：`1161`
- trace length：min `9` / mean `16.59` / max `27`

## 重要边界

这份数据是 `trace-level sequence dataset`，不是 ACT / Diffusion Policy 可直接训练的低层动作数据。

原因：现有 Stage3.7D/3.8B metadata 只保存稀疏状态 trace，没有保存每一步完整 observation 和 actuator action。

它现在适合做：时序失败分类、路由器边界分析、技能选择模型预备、后续数据管线 smoke。真正小模型训练还需要下一步 replay/重采集 obs-action sequence。

## 技能分布

| skill | sequences | success | canonical training | success rate |
| --- | --- | --- | --- | --- |
| full_hand_gentle_grasp | 30 | 30 | 30 | 1.000 |
| thumb_index_middle_pinch | 40 | 34 | 10 | 0.850 |

## 数据集 split

| split | sequences |
| --- | --- |
| canonical_training | 40 |
| diagnostic_variant | 30 |

## NPZ

- sequence tensor shape：`[70, 27, 23]`
- feature columns：`raw_step, step_norm, phase_code, progress, control_progress, lift_height_m, contact, stable, pinch_contact, learned_hand, recovery_active, slip, crush, penetration, gate_window, recovery_reason_count, recovery_reason_slip_high, region_thumb, region_index, region_middle, region_ring, region_palm, region_support`
- phase vocab：`{'approach': 0, 'contact_settle': 1, 'gentle_close_fingers': 2, 'gentle_close_thumb': 3, 'hold': 4, 'pinch_close': 5, 'preshape': 6, 'slow_lift': 7}`

## 失败和风险信号

| type | name | count |
| --- | --- | --- |
| failure | egg_still_touching_floor | 2 |
| failure | final_vision_failed_or_occluded | 1 |
| failure | hold_slip_score_high | 5 |
| failure | hold_tactile_unstable | 1 |
| failure | pinch_not_maintained_in_hold | 1 |
| failure | true_lift_too_small | 2 |
| failure | vision_lift_too_small | 1 |
| risk | early_contact_in_approach | 70 |
| risk | final_vision_occluded_or_low_confidence | 1 |
| risk | low_pinch_purity | 2 |
| risk | recovery_budget_exhausted | 15 |
| risk | transient_or_hold_slip | 28 |
| risk | transient_slip_high | 40 |

## 如果成功

下一步做 Stage3.9B3：用 replay 或重新评估脚本导出完整 observation/action 序列，形成真正 ACT/Diffusion Policy/LeRobot 可读的数据。

## 如果失败

先修 trace schema、phase vocab、feature columns 和源 metadata 对齐，不进入模型训练。
