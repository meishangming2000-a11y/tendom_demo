# Stage3.10B Safety-Labeled Dataset v0 Closeout

生成日期：2026-06-07

## 这一步的目的

Stage3.10B 的第一步，是把 Stage3.10A 冻结的 safety layer 跑成真正可训练的数据，而不只是保留成功/失败报告。

这份数据保留旧 ACT/DP 数据面的核心字段：

- `obs`
- `actions`
- `next_obs`
- `dones`
- `episode_ids`
- `skill_ids`
- `phase_ids`

同时新增 safety 标签，让后续模型知道哪些时刻发生了：

- full-hand recovery
- pinch repair
- safety intervention
- slip/crush/penetration/floor-contact risk

## 本轮产出

- exporter：`export_stage3_10b_safety_labeled_act_dp_dataset_v0.py`
- NPZ：`data/stage3_10b_safety_labeled_act_dp_dataset_v0.npz`
- JSONL：`data/stage3_10b_safety_labeled_act_dp_dataset_v0.jsonl`
- metadata：`metadata/stage3_10b_safety_labeled_act_dp_dataset_v0.json`
- report：`docs/stage3_10b_safety_labeled_act_dp_dataset_v0_report.md`

运行命令：

```powershell
python .\simulations\models\arm_hand_stage1_export\export_stage3_10b_safety_labeled_act_dp_dataset_v0.py --episodes-per-skill 5
```

## 本轮结果

- 总 episode：`10`
- 成功：`10 / 10`
- full-hand：`5 / 5`
- pinch：`5 / 5`
- 总行数：`38560`
- `obs` shape：`[38560, 130]`
- `actions` shape：`[38560, 26]`
- `safety_labels` shape：`[38560, 9]`
- safety intervention steps：`9860`
- full-hand recovery steps：`724`
- pinch repair steps：`9136`
- risk label steps：`956`
- slip-high steps：`840`
- finite obs/action：`True`
- one done per episode：`True`
- action range ok：`True`

## 重要边界

这轮是 Stage3.10B smoke/seed 数据，说明 schema、采集入口和 safety 标签已经跑通。它还不是完整大规模 ACT/DP 训练集，因为 episode 数量只有 `10`，低于旧 B3 的 train-ready 门槛。

所以 metadata 里旧 ACT/DP readiness 会显示：

- `act_ready=False`
- `dp_ready=False`
- `act_dp_ready=False`

这不是失败，而是规模边界。10B 当前验收的是 `stage3_10b_smoke_ready=True`。

## 如果成功

进入 Stage3.10B-full：扩大采集规模，至少补到旧 B3 等级或更高，并加入更多 pose-noise、遮挡、失败/恢复场景。然后把这份 schema 作为 Stage3.10C 正式 ACT/CVAE 或 Diffusion Policy dataloader 的输入。

## 如果失败

不进入模型训练。先修 sequence capture、safety 标签、action range 或 episode 成功率；也不回到 Stage3.9 小参数微调。
