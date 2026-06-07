# Stage3.10C Safety ACT/CVAE Policy v0 Train Report

- 生成时间：`2026-06-07T19:54:14`
- 状态：`stage3_10c_safety_act_cvae_policy_v0_offline_trained_not_closed_loop_promoted`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10c_safety_act_cvae_policy_v0_smoke.pth`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_10c_safety_act_cvae_policy_v0_smoke_train.json`
- 模型：`SafetyACTCVAEChunkPolicy`
- horizon：`16`
- stride：`8`
- obs dim：`130`
- action dim：`26`
- safety dim：`9`
- d_model：`64`
- latent dim：`16`
- epochs：`1`
- batch size：`64`
- device：`cpu`

## 训练数据

- train episodes：`[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 14, 15, 16, 17, 18, 19, 20, 22, 25, 26, 27, 28, 29, 31, 32, 34, 35, 36, 37, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 54, 55, 56, 59]`
- val episodes：`[10, 12, 13, 21, 23, 24, 30, 33, 41, 53, 57, 58]`
- train windows：`512`
- val windows：`128`
- Stage3.10B train ready：`True`

## 训练结果

- best epoch：`1`
- best val prior action loss：`0.67184776`
- final train action loss：`0.83723699`
- final val prior action loss：`0.67184776`
- train raw RMSE：`0.19457600`
- val raw RMSE：`0.17651817`
- train hand raw RMSE：`0.21230452`
- val hand raw RMSE：`0.19263197`
- val safety accuracy：`0.658637`
- val safety precision：`0.258649`
- val safety recall：`0.475405`

## 技能窗口分布

| split | skill | windows |
| --- | --- | ---: |
| train | `full_hand_gentle_grasp` | 336 |
| train | `thumb_index_middle_pinch` | 176 |
| val | `full_hand_gentle_grasp` | 87 |
| val | `thumb_index_middle_pinch` | 41 |

## Loss Curve

| epoch | train action | val prior action | val safety BCE | KL |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.83723699 | 0.67184776 | 0.65558296 | 0.28260032 |

## 这一步说明什么

这一步说明 Stage3.10B-full 的安全标签数据已经能被模型训练入口直接读取，并能训练出一个带 latent 的 action chunk baseline。它比旧 ACT-lite 多了 phase 输入、safety-label 输入和 safety-label 辅助预测头。

## 重要边界

- 这是 offline 训练结果，不是闭环 MuJoCo 成功。
- 这个模型仍然不能被描述为 full-action ACT/DP 已经学会抓鸡蛋。
- 下一步必须做 Stage3.10C-B closed-loop eval，并和 Stage3.10A safety layer 同场景对比。

## 如果成功

进入 Stage3.10C-B：写闭环评估器，用 `scripted_arm_predicted_hand` 方式先评估 hand/finger chunk，再报告 success、hold slip、crush、penetration、floor contact 和 final vision。

## 如果失败

先检查 skill/phase 分层、action loss 权重、safety auxiliary head 的正负样本不平衡，以及是否需要分技能模型头；不要放宽抓取成功阈值。
