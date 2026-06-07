# Stage3 ACT-lite Chunk Policy v0 训练报告

- 生成时间：`2026-06-07T02:48:18`
- 状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v0.npz`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v0_smoke.pth`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_act_lite_chunk_policy_v0_smoke_train.json`
- 模型：`ACT-lite MLP action chunk predictor`
- horizon：`8`
- stride：`16`
- obs dim：`130`
- action dim：`26`
- output dim：`208`
- skill count：`2`
- hidden dim：`128`
- depth：`2`
- epochs：`3`
- batch size：`256`
- device：`cpu`
- train episodes：`[0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 21, 22, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 39]`
- val episodes：`[4, 17, 19, 20, 23, 29, 37, 38]`
- train windows：`1024`
- val windows：`512`
- final train MSE normalized：`0.64913602`
- final val MSE normalized：`0.53397393`
- train chunk RMSE raw：`0.12259632`
- val chunk RMSE raw：`0.12004931`
- best val epoch：`3`
- best val MSE normalized：`0.53397393`

## 这次训练到底是什么

这是第一版 ACT-lite action chunk 训练：给当前 `obs_t` 和 `skill_id`，预测未来 `H` 步 actuator action chunk。它验证 ACT/DP 训练入口，但还不是完整 ACT CVAE/Transformer，也不是 Diffusion Policy。

## 技能窗口分布

| split | skill | windows |
| --- | --- | ---: |
| train | `full_hand_gentle_grasp` | 868 |
| train | `thumb_index_middle_pinch` | 156 |
| val | `full_hand_gentle_grasp` | 449 |
| val | `thumb_index_middle_pinch` | 63 |

## Loss Curve

| epoch | train MSE | val MSE |
| ---: | ---: | ---: |
| 1 | 1.00083670 | 0.82167304 |
| 2 | 0.80295436 | 0.66455054 |
| 3 | 0.64913602 | 0.53397393 |

## 如果成功

下一步做 MuJoCo closed-loop eval：把 chunk policy 接到 Stage3 技能执行器里，和 scripted SkillZoo baseline 对比成功率、滑移、挤压和穿透。

## 如果失败

先不要扩大模型。优先检查窗口切分、phase/skill 条件、action chunk horizon、以及 full-hand/pinch 混合训练是否需要分技能头。

## 重要边界

- 这个 checkpoint 只能说明 offline action chunk learning 已跑通。
- 不能说机械手已经由 ACT/DP 学会抓鸡蛋；闭环 MuJoCo eval 还没做。
