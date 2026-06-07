# Stage3 ACT-lite Chunk Policy v0 训练报告

- 生成时间：`2026-06-07T02:48:57`
- 状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v0.npz`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v0.pth`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_act_lite_chunk_policy_v0_train.json`
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
- train episodes：`[0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 21, 22, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 39]`
- val episodes：`[4, 17, 19, 20, 23, 29, 37, 38]`
- train windows：`17933`
- val windows：`4478`
- final train MSE normalized：`0.00237677`
- final val MSE normalized：`0.00085625`
- train chunk RMSE raw：`0.00271970`
- val chunk RMSE raw：`0.00412405`
- best val epoch：`29`
- best val MSE normalized：`0.00084683`

## 这次训练到底是什么

这是第一版 ACT-lite action chunk 训练：给当前 `obs_t` 和 `skill_id`，预测未来 `H` 步 actuator action chunk。它验证 ACT/DP 训练入口，但还不是完整 ACT CVAE/Transformer，也不是 Diffusion Policy。

## 技能窗口分布

| split | skill | windows |
| --- | --- | ---: |
| train | `full_hand_gentle_grasp` | 15403 |
| train | `thumb_index_middle_pinch` | 2530 |
| val | `full_hand_gentle_grasp` | 3850 |
| val | `thumb_index_middle_pinch` | 628 |

## Loss Curve

| epoch | train MSE | val MSE |
| ---: | ---: | ---: |
| 1 | 0.31626819 | 0.03525325 |
| 2 | 0.02991326 | 0.01211886 |
| 3 | 0.01416436 | 0.00639376 |
| 4 | 0.01014129 | 0.00472273 |
| 5 | 0.00800807 | 0.00317806 |
| 6 | 0.00676747 | 0.00276360 |
| 7 | 0.00589697 | 0.00248931 |
| 8 | 0.00525232 | 0.00184791 |
| 9 | 0.00487132 | 0.00209972 |
| 10 | 0.00490991 | 0.00181379 |
| 11 | 0.00434110 | 0.00201591 |
| 12 | 0.00430383 | 0.00168166 |
| 13 | 0.00393911 | 0.00141909 |
| 14 | 0.00384873 | 0.00124081 |
| 15 | 0.00363912 | 0.00131010 |
| 16 | 0.00343331 | 0.00130995 |
| 17 | 0.00342513 | 0.00111643 |
| 18 | 0.00322280 | 0.00133091 |
| 19 | 0.00318213 | 0.00165825 |
| 20 | 0.00325806 | 0.00116608 |
| 21 | 0.00292636 | 0.00154170 |
| 22 | 0.00293290 | 0.00131906 |
| 23 | 0.00293651 | 0.00143267 |
| 24 | 0.00274422 | 0.00111283 |
| 25 | 0.00255890 | 0.00100858 |
| 26 | 0.00251191 | 0.00119769 |
| 27 | 0.00270855 | 0.00133309 |
| 28 | 0.00307259 | 0.00093902 |
| 29 | 0.00246637 | 0.00084683 |
| 30 | 0.00237677 | 0.00085625 |

## 如果成功

下一步做 MuJoCo closed-loop eval：把 chunk policy 接到 Stage3 技能执行器里，和 scripted SkillZoo baseline 对比成功率、滑移、挤压和穿透。

## 如果失败

先不要扩大模型。优先检查窗口切分、phase/skill 条件、action chunk horizon、以及 full-hand/pinch 混合训练是否需要分技能头。

## 重要边界

- 这个 checkpoint 只能说明 offline action chunk learning 已跑通。
- 不能说机械手已经由 ACT/DP 学会抓鸡蛋；闭环 MuJoCo eval 还没做。
