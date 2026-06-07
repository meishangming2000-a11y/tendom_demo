# Stage3.9B Skill Episode Dataset v0 报告

- 生成时间：`2026-06-06T13:43:03`
- 状态：`PASS`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_episode_dataset_v0.jsonl`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_episode_dataset_v0.npz`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_skill_episode_dataset_v0.json`
- episode rows：`70`
- canonical training rows：`40`
- success rows：`64`

## 技能分布

| skill | episodes | success | canonical training | success rate |
| --- | --- | --- | --- | --- |
| full_hand_gentle_grasp | 30 | 30 | 30 | 1.000 |
| thumb_index_middle_pinch | 40 | 34 | 10 | 0.850 |

## 数据来源

| source stage | rows |
| --- | --- |
| Stage3.7D | 30 |
| Stage3.8B | 40 |

## 数据集 split

| split | rows |
| --- | --- |
| canonical_training | 40 |
| diagnostic_variant | 30 |

## 失败和风险信号

| type | name | count |
| --- | --- | --- |
| failure | egg_still_touching_floor | 2 |
| failure | final_vision_failed_or_occluded | 1 |
| failure | hold_slip_score_high | 5 |
| failure | hold_tactile_unstable | 1 |
| failure | pinch_not_maintained_in_hold | 1 |
| failure | true_lift_too_small | 2 |
| failure | vision_lift_too_small | 1 |
| risk | early_contact_in_approach | 70 |
| risk | final_vision_occluded_or_low_confidence | 1 |
| risk | low_pinch_purity | 2 |
| risk | recovery_budget_exhausted | 15 |
| risk | transient_or_hold_slip | 28 |
| risk | transient_slip_high | 40 |

## NPZ 特征

- shape：`[70, 24]`
- columns：`skill_code, canonical_training, success, vision_confidence_initial, vision_confidence_final, pose_error_m, vision_lift_height_m, true_lift_height_m, vision_true_lift_error_m, hold_stable_fraction, hold_pinch_fraction, hold_pinch_purity_mean, hold_max_slip_score, hold_final_slip_score, max_slip_score, pre_lift_max_slip_score, post_lift_max_slip_score, max_crush_risk, max_penetration_m, final_floor_contacts, contact_settle_steps_actual, recovery_steps, recovery_events, total_steps`

## 结论

Stage3.9B 已经把 Stage3.7D/3.8B 的 episode 结果统一成 skill episode rows。这个数据集是 episode-level 中间层，适合做路由器、失败分类、训练集筛选和下一步 LeRobot/ACT/Diffusion Policy 转换准备；它还不是低层逐时间步 action dataset。

如果成功：下一步可以做 Stage3.9B2，把 canonical rows 反查到 trace 或原始 action/obs，生成真正的小模型训练序列。

如果失败：先修 schema 映射和 failure taxonomy，不进入模型训练。
