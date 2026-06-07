# Stage3 ACT-lite Chunk Policy v0 训练报告

- 生成时间：`2026-06-07T10:17:22`
- 状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v1_pinch30.npz`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_act_lite_chunk_policy_v1_pinch30_train.json`
- 模型：`ACT-lite MLP action chunk predictor`
- horizon：`16`
- stride：`8`
- obs dim：`130`
- action dim：`26`
- output dim：`416`
- skill count：`2`
- hidden dim：`256`
- depth：`3`
- epochs：`30`
- batch size：`512`
- device：`cpu`
- train episodes：`[0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 21, 22, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 53, 55, 56, 59]`
- val episodes：`[4, 17, 19, 20, 23, 29, 37, 45, 52, 54, 57, 58]`
- train windows：`22998`
- val windows：`5734`
- final train MSE normalized：`0.00193720`
- final val MSE normalized：`0.00051193`
- train chunk RMSE raw：`0.00226230`
- val chunk RMSE raw：`0.00332868`
- best val epoch：`28`
- best val MSE normalized：`0.00049575`

## 这次训练到底是什么

这是第一版 ACT-lite action chunk 训练：给当前 `obs_t` 和 `skill_id`，预测未来 `H` 步 actuator action chunk。它验证 ACT/DP 训练入口，但还不是完整 ACT CVAE/Transformer，也不是 Diffusion Policy。

## 技能窗口分布

| split | skill | windows |
| --- | --- | ---: |
| train | `full_hand_gentle_grasp` | 15403 |
| train | `thumb_index_middle_pinch` | 7595 |
| val | `full_hand_gentle_grasp` | 3850 |
| val | `thumb_index_middle_pinch` | 1884 |

## Loss Curve

| epoch | train MSE | val MSE |
| ---: | ---: | ---: |
| 1 | 0.23958867 | 0.02647470 |
| 2 | 0.02228181 | 0.00942807 |
| 3 | 0.01203607 | 0.00439332 |
| 4 | 0.00838356 | 0.00265939 |
| 5 | 0.00665648 | 0.00198314 |
| 6 | 0.00573325 | 0.00154557 |
| 7 | 0.00508489 | 0.00148611 |
| 8 | 0.00464272 | 0.00113258 |
| 9 | 0.00428360 | 0.00103705 |
| 10 | 0.00397509 | 0.00087453 |
| 11 | 0.00373705 | 0.00097559 |
| 12 | 0.00349752 | 0.00077359 |
| 13 | 0.00332402 | 0.00078393 |
| 14 | 0.00314433 | 0.00079652 |
| 15 | 0.00302018 | 0.00062373 |
| 16 | 0.00288323 | 0.00068236 |
| 17 | 0.00281563 | 0.00070559 |
| 18 | 0.00267997 | 0.00066496 |
| 19 | 0.00256544 | 0.00065398 |
| 20 | 0.00249736 | 0.00063679 |
| 21 | 0.00242844 | 0.00060519 |
| 22 | 0.00237169 | 0.00060418 |
| 23 | 0.00228859 | 0.00063363 |
| 24 | 0.00222250 | 0.00053879 |
| 25 | 0.00212998 | 0.00058401 |
| 26 | 0.00210122 | 0.00054596 |
| 27 | 0.00204301 | 0.00054094 |
| 28 | 0.00201933 | 0.00049575 |
| 29 | 0.00196018 | 0.00054394 |
| 30 | 0.00193720 | 0.00051193 |

## 如果成功

下一步做 MuJoCo closed-loop eval：把 chunk policy 接到 Stage3 技能执行器里，和 scripted SkillZoo baseline 对比成功率、滑移、挤压和穿透。

## 如果失败

先不要扩大模型。优先检查窗口切分、phase/skill 条件、action chunk horizon、以及 full-hand/pinch 混合训练是否需要分技能头。

## 重要边界

- 这个 checkpoint 只能说明 offline action chunk learning 已跑通。
- 不能说机械手已经由 ACT/DP 学会抓鸡蛋；闭环 MuJoCo eval 还没做。
