# Stage3 ACT-lite Chunk Policy v0 训练报告

- 生成时间：`2026-06-07T10:21:28`
- 状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 数据集：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v1_pinch30.npz`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30_wide.pth`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_act_lite_chunk_policy_v1_pinch30_wide_train.json`
- 模型：`ACT-lite MLP action chunk predictor`
- horizon：`16`
- stride：`8`
- obs dim：`130`
- action dim：`26`
- output dim：`416`
- skill count：`2`
- hidden dim：`512`
- depth：`4`
- epochs：`40`
- batch size：`512`
- device：`cpu`
- train episodes：`[0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 21, 22, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 53, 55, 56, 59]`
- val episodes：`[4, 17, 19, 20, 23, 29, 37, 45, 52, 54, 57, 58]`
- train windows：`22998`
- val windows：`5734`
- final train MSE normalized：`0.00108993`
- final val MSE normalized：`0.00073968`
- train chunk RMSE raw：`0.00233507`
- val chunk RMSE raw：`0.00337744`
- best val epoch：`25`
- best val MSE normalized：`0.00049597`

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
| 1 | 0.14780216 | 0.01658274 |
| 2 | 0.01362962 | 0.00477620 |
| 3 | 0.00708624 | 0.00215439 |
| 4 | 0.00516770 | 0.00130234 |
| 5 | 0.00436925 | 0.00127927 |
| 6 | 0.00380201 | 0.00104088 |
| 7 | 0.00339588 | 0.00081713 |
| 8 | 0.00309905 | 0.00087042 |
| 9 | 0.00287623 | 0.00075829 |
| 10 | 0.00268452 | 0.00074948 |
| 11 | 0.00255570 | 0.00063075 |
| 12 | 0.00239744 | 0.00067092 |
| 13 | 0.00223667 | 0.00066596 |
| 14 | 0.00217286 | 0.00065041 |
| 15 | 0.00205873 | 0.00059791 |
| 16 | 0.00196831 | 0.00072318 |
| 17 | 0.00191288 | 0.00062500 |
| 18 | 0.00181861 | 0.00060436 |
| 19 | 0.00176561 | 0.00051450 |
| 20 | 0.00169451 | 0.00052918 |
| 21 | 0.00164157 | 0.00056840 |
| 22 | 0.00161960 | 0.00073239 |
| 23 | 0.00156072 | 0.00067686 |
| 24 | 0.00148909 | 0.00059123 |
| 25 | 0.00147065 | 0.00049597 |
| 26 | 0.00145332 | 0.00059490 |
| 27 | 0.00143140 | 0.00063800 |
| 28 | 0.00138457 | 0.00062337 |
| 29 | 0.00136405 | 0.00085235 |
| 30 | 0.00134152 | 0.00076521 |
| 31 | 0.00129903 | 0.00067449 |
| 32 | 0.00126390 | 0.00055365 |
| 33 | 0.00126056 | 0.00077446 |
| 34 | 0.00119767 | 0.00057663 |
| 35 | 0.00115537 | 0.00060027 |
| 36 | 0.00114798 | 0.00066998 |
| 37 | 0.00121152 | 0.00062911 |
| 38 | 0.00115480 | 0.00062551 |
| 39 | 0.00110956 | 0.00062025 |
| 40 | 0.00108993 | 0.00073968 |

## 如果成功

下一步做 MuJoCo closed-loop eval：把 chunk policy 接到 Stage3 技能执行器里，和 scripted SkillZoo baseline 对比成功率、滑移、挤压和穿透。

## 如果失败

先不要扩大模型。优先检查窗口切分、phase/skill 条件、action chunk horizon、以及 full-hand/pinch 混合训练是否需要分技能头。

## 重要边界

- 这个 checkpoint 只能说明 offline action chunk learning 已跑通。
- 不能说机械手已经由 ACT/DP 学会抓鸡蛋；闭环 MuJoCo eval 还没做。
