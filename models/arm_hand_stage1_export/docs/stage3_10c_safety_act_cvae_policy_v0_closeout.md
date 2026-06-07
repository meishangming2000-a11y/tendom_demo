# Stage3.10C-A safety ACT/CVAE-style policy closeout

日期：2026-06-07

## 这一步的目标

Stage3.10C-A 的目标是把 Stage3.10B-full 的 safety-labeled 数据真正接到一个 ACT/CVAE 风格的离线训练入口上，而不是继续停留在“数据已经 ready”。这一步仍然只属于 MuJoCo 仿真，不是硬件、真实摄像头、真实触觉或超声集成。

本轮新增的模型是 `SafetyACTCVAEChunkPolicy`：

- 输入：`obs_t`、`skill_id`、`phase_id`、当前 `safety_label_t`
- 输出：未来 `16` 步动作 chunk，以及未来 `16` 步 safety label 预测
- 结构：posterior encoder + latent `mu/logvar` + zero-latent prior inference + transformer chunk decoder
- 用途：作为 Stage3.10C 的第一版安全感知 ACT/CVAE-style 离线策略 baseline

## 产出

| 用途 | 文件 |
| --- | --- |
| 训练脚本 | `train_stage3_10c_safety_act_cvae_policy_v0.py` |
| 主数据集 | `data/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz` |
| 主 checkpoint | `checkpoints/stage3_10c_safety_act_cvae_policy_v0.pth` |
| 主训练 metadata | `metadata/stage3_10c_safety_act_cvae_policy_v0_train.json` |
| 主训练报告 | `docs/stage3_10c_safety_act_cvae_policy_v0_train_report.md` |
| smoke checkpoint | `checkpoints/stage3_10c_safety_act_cvae_policy_v0_smoke.pth` |
| smoke 训练报告 | `docs/stage3_10c_safety_act_cvae_policy_v0_smoke_train_report.md` |

## 复现命令

smoke 训练：

```powershell
python -u .\simulations\models\arm_hand_stage1_export\train_stage3_10c_safety_act_cvae_policy_v0.py --epochs 1 --max-train-windows 512 --max-val-windows 128 --batch-size 64 --d-model 64 --nhead 4 --num-layers 1 --latent-dim 16 --output .\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10c_safety_act_cvae_policy_v0_smoke.pth --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_10c_safety_act_cvae_policy_v0_smoke_train.json --report .\simulations\models\arm_hand_stage1_export\docs\stage3_10c_safety_act_cvae_policy_v0_smoke_train_report.md --device cpu
```

主训练：

```powershell
python -u .\simulations\models\arm_hand_stage1_export\train_stage3_10c_safety_act_cvae_policy_v0.py --epochs 8 --max-train-windows 24000 --max-val-windows 6000 --batch-size 256 --d-model 128 --nhead 4 --num-layers 2 --latent-dim 32 --device cpu
```

## 主训练结果

| 指标 | 数值 |
| --- | --- |
| best epoch | `8` |
| train windows | `24000` |
| val windows | `6000` |
| best val prior action loss | `0.0013452474` |
| final train action loss | `0.0034123266` |
| train prior RMSE raw | `0.0090611074` |
| val prior RMSE raw | `0.0093151014` |
| train prior hand RMSE raw | `0.0067716581` |
| val prior hand RMSE raw | `0.0072230357` |
| val safety accuracy | `0.9905235265` |
| val safety precision | `0.9993049615` |
| val safety recall | `0.9437992325` |

checkpoint 已验证可以用真实保存字段重建模型并加载，`missing_keys=[]`，`unexpected_keys=[]`。

## 这一步证明了什么

- Stage3.10B-full 的 safety-labeled 数据可以被正式训练入口消费。
- 模型可以同时学习动作 chunk 和 safety label 辅助任务。
- 离线验证集上，动作 prior loss 和 safety label 指标都已经跑通。
- 训练链路已经从 ACT-lite MLP 进入 ACT/CVAE-style transformer chunk policy。

## 这一步还没有证明什么

- 还没有证明这个 checkpoint 可以在 MuJoCo closed-loop 中抓起鸡蛋。
- 还没有证明 full-action 26 actuator 端到端控制可用。
- 还没有和 Stage3.10A safety layer 做同场景闭环对比。
- 还没有进入真实摄像头、真实触觉、超声或硬件机械手。

## 下一步

如果成功：

- 进入 Stage3.10C-B，写 closed-loop evaluator。
- 第一轮优先使用 `scripted_arm_predicted_hand`，让模型控制手指 chunk，手臂和手腕仍由视觉脚本控制。
- 与 Stage3.10A safety layer 在同一批场景对比，报告 full hand、pinch、slip、final vision 和 safety label 触发情况。

如果失败：

- 先判断失败来自数据分布、动作 chunk prior、phase/skill 条件、safety label 辅助头，还是 final vision 遮挡。
- 不回到 Stage3.9 小参数微调。
- 如果 full-action 闭环失败，继续保留 scripted arm/wrist，只把手指、残差或安全恢复阶段交给模型。

## 当前边界

当前状态应描述为：

`Stage3.10C-A offline safety ACT/CVAE-style baseline trained, not closed-loop promoted`

不要描述为：

- 已经完成 full-action ACT/DP 抓取
- 已经硬件集成
- 已经接入真实摄像头
- 已经接入真实触觉或超声
