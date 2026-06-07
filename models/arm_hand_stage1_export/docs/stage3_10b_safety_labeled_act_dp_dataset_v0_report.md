# Stage3.10B Safety-Labeled ACT/DP Dataset v0 Report

- 生成时间：`2026-06-07T18:53:02`
- 状态：`PASS`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_v0.npz`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_v0.jsonl`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_10b_safety_labeled_act_dp_dataset_v0.json`
- safety layer config：`D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage3_10a_skillzoo_safety_layer_v0.json`

## 这一步做了什么

Stage3.10B 的第一步不是训练模型，而是把 Stage3.10A 冻结的 safety layer 跑成可训练数据。这个数据仍保留 `obs/action/next_obs/done/skill/phase`，同时新增 safety 标签，告诉后续模型哪些时刻发生了触觉恢复、捏持 repair、最终视觉/触觉佐证和滑移风险。

## 数据规模

- episodes：`10`
- success：`10 / 10`
- total rows：`38560`
- obs shape：`[38560, 130]`
- actions shape：`[38560, 26]`
- padded obs shape：`[10, 5220, 130]`
- padded actions shape：`[10, 5220, 26]`

## Safety 标签

- safety label shape：`[38560, 9]`
- safety intervention steps：`9860`
- full-hand recovery steps：`724`
- pinch repair steps：`9136`
- final vision corroborated episodes：`0`
- risk label steps：`956`
- slip-high steps：`840`
- episodes with safety intervention：`10`
- episodes with risk label：`10`

## 技能分布

| skill | episodes | success |
| --- | ---: | ---: |
| `full_hand_gentle_grasp` | 5 | 5 |
| `thumb_index_middle_pinch` | 5 | 5 |

## 验收

- finite obs/action：`True`
- one done per episode：`True`
- action range ok：`True`
- safety schema ready：`True`
- blockers：`[]`

注意：本轮默认是 Stage3.10B smoke/seed 数据，不声称已经完成大规模 ACT/DP 训练集。完整数据扩展要继续把 `--episodes-per-skill` 放大，并加入更多 pose-noise、遮挡和失败场景。

## 如果成功

下一步进入 Stage3.10B-full：扩大采集规模，并把这个 schema 固化为正式 ACT/CVAE 或 Diffusion Policy dataloader 的输入。

## 如果失败

先修 sequence capture、safety 标签或 action range；不进入模型训练，也不回到 Stage3.9 小参数微调。
