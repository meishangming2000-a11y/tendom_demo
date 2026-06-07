# Stage3.10B-full Safety-Labeled Dataset v0 Closeout

生成日期：2026-06-07

## 这一步的目的

Stage3.10B v0 只证明了 safety-labeled 数据 schema 能跑通。Stage3.10B-full 的目的，是把这个 schema 扩大到 ACT/CVAE 或 Diffusion Policy 训练前可用的规模，同时保留 safety layer 介入、触觉风险、失败原因和最终视觉校验信息。

这一步仍然是 MuJoCo 仿真，不是真实摄像头、真实触觉、超声硬件或真实机械手集成。

## 本轮主训练候选

主训练候选是：

- NPZ：`data/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz`
- JSONL：`data/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.jsonl`
- metadata：`metadata/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.json`
- report：`docs/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0_report.md`

运行命令：

```powershell
python -u .\simulations\models\arm_hand_stage1_export\export_stage3_10b_safety_labeled_act_dp_dataset_v0.py `
  --episodes-per-skill 30 `
  --trials cycle `
  --seed 5100 `
  --random-offset-std 0.005 `
  --dataset simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz `
  --jsonl simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.jsonl `
  --metadata simulations\models\arm_hand_stage1_export\metadata\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.json `
  --report simulations\models\arm_hand_stage1_export\docs\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0_report.md `
  --dataset-version stage3_10b_safety_labeled_act_dp_dataset_full_success_v0 `
  --experiment-name Stage3.10B-full_success_safety_labeled_ACT_DP_dataset_v0
```

结果：

- 总 episode：`60`
- 成功：`60 / 60`
- full-hand：`30 / 30`
- pinch：`30 / 30`
- 总行数：`231421`
- `obs` shape：`[231421, 130]`
- `actions` shape：`[231421, 26]`
- `safety_labels` shape：`[231421, 9]`
- safety intervention steps：`59221`
- recovery steps：`4377`
- repair steps：`54844`
- risk label steps：`5408`
- old ACT/DP gate：`act_dp_ready=True`
- Stage3.10B 训练前 gate：`stage3_10b_train_ready=True`

## 诊断集和失败样本

第一轮扩大采集保留下来作为诊断集：

- metadata：`metadata/stage3_10b_safety_labeled_act_dp_dataset_full_v0.json`
- report：`docs/stage3_10b_safety_labeled_act_dp_dataset_full_v0_report.md`
- 结果：`59 / 60`

唯一失败：

- episode：`31`
- skill：`thumb_index_middle_pinch`
- trial：`left_low_nominal`
- terminal reason：`vision_lift_too_small`
- 失败原因：`vision_lift_too_small`、`true_lift_too_small`、`pinch_not_maintained_in_hold`、`hold_tactile_unstable`、`egg_still_touching_floor`
- 解释：这是一次真正抓取失败，不是数据结构错误。最终 lift 为负，hold pinch 没有保持住，鸡蛋仍然触地。

这个诊断集不作为主训练集，但它很适合后续分析“安全层介入很多仍然失败”的边界样本。

## 8mm 位姿噪声 stress sweep

为了测试更难的位姿扰动，本轮还跑了一个小规模 stress sweep：

- NPZ：`data/stage3_10b_safety_labeled_act_dp_dataset_stress_pose008_v0.npz`
- metadata：`metadata/stage3_10b_safety_labeled_act_dp_dataset_stress_pose008_v0.json`
- report：`docs/stage3_10b_safety_labeled_act_dp_dataset_stress_pose008_v0_report.md`
- 位姿噪声：`0.008 m`
- 总 episode：`20`
- 成功：`19 / 20`
- full-hand：`10 / 10`
- pinch：`9 / 10`

唯一失败：

- skill：`thumb_index_middle_pinch`
- trial：`back_large_lift`
- terminal reason：`final_vision_failed_or_occluded`
- true lift：`0.124109 m`
- hold stable fraction：`1.0`
- hold pinch fraction：`1.0`
- final vision confidence：`0.272823`
- final vision mask pixels：`574`

解释：这次更像最终视觉验证被遮挡或置信度过低，而不是机械手没有抓住。它指向后续的 final verification / 多视角 / 遮挡处理，而不是继续放宽抓取成功阈值。

## 验收结论

Stage3.10B-full 主训练候选通过：

- 数据规模达到旧 B3 ACT/DP readiness 门槛。
- 两个技能都达到 `30 / 30` 成功。
- safety/risk 标签存在且不为空。
- 失败/边界样本被单独保留，没有混进主训练候选。

## 如果成功

进入 Stage3.10C：把 `stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz` 接到正式 ACT Transformer/CVAE 或 Diffusion Policy dataloader，先训练一个小 baseline，再和 Stage3.10A safety layer 做同场景闭环对比。

## 如果失败

如果 Stage3.10C 训练失败，不回到 Stage3.9 小参数微调。优先检查：

- 数据是否需要按 skill/phase 分层采样。
- safety labels 是否应该作为辅助预测头，而不是直接并进动作输入。
- final vision failure 是否需要多视角或触觉佐证策略。
- full-action 仍不稳定时，继续保留 scripted arm/wrist，只训练 hand/finger 或 residual。
