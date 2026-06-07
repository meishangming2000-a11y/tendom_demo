# Stage3.10B-full_success_safety_labeled_ACT_DP_dataset_v0 Report

- 生成时间：`2026-06-07T19:35:32`
- schema/smoke 状态：`PASS`
- 训练前数据状态：`READY`
- dataset version：`stage3_10b_safety_labeled_act_dp_dataset_full_success_v0`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.jsonl`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.json`
- safety layer config：`D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage3_10a_skillzoo_safety_layer_v0.json`

## 这一步做了什么

这一步把 Stage3.10A 冻结的 safety layer 跑成可训练序列数据。数据保留 `obs/action/next_obs/done/skill/phase`，同时加入 safety 标签，用来记录 full-hand recovery、pinch repair、最终视觉/触觉校验和触觉风险。

## 数据规模

- episodes：`60`
- success：`60 / 60`
- total rows：`231421`
- obs shape：`[231421, 130]`
- actions shape：`[231421, 26]`
- padded obs shape：`[60, 5220, 130]`
- padded actions shape：`[60, 5220, 26]`

## Safety 标签

- safety label shape：`[231421, 9]`
- safety intervention steps：`59221`
- full-hand recovery steps：`4222`
- pinch repair steps：`54999`
- final vision corroborated episodes：`0`
- risk label steps：`5408`
- slip-high steps：`5070`
- episodes with safety intervention：`60`
- episodes with risk label：`60`

## 技能分布

| skill | episodes | success |
| --- | ---: | ---: |
| `full_hand_gentle_grasp` | 30 | 30 |
| `thumb_index_middle_pinch` | 30 | 30 |

## 验收

- finite obs/action：`True`
- one done per episode：`True`
- action range ok：`True`
- old ACT ready gate：`True`
- old DP ready gate：`True`
- old ACT/DP ready gate：`True`
- safety schema ready：`True`
- smoke blockers：`[]`
- train-readiness blockers：`[]`

说明：`stage3_10b_smoke_ready` 只表示采集链路和 safety schema 跑通；`stage3_10b_train_ready` 才表示规模、成功率和 safety 标签都足够进入下一步 ACT/CVAE 或 DP 训练准备。

## 如果成功

进入 Stage3.10C：把这份 safety-labeled 数据接到正式 ACT Transformer/CVAE 或 Diffusion Policy dataloader，并和 Stage3.10A safety layer 做同场景闭环对比。

## 如果失败

先看失败属于规模不足、episode 失败、sequence capture 错误、动作越界，还是 safety/risk 标签太稀疏；只修对应问题，不回到 Stage3.9 的小参数微调。
