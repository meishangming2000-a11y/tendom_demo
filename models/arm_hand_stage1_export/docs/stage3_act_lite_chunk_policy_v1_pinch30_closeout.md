# Stage3 ACT-lite Chunk Policy v1_pinch30 Closeout

生成日期：2026-06-07

## 一句话结论

ACT-lite action chunk 训练已经能进入 MuJoCo 闭环评估；当前可用边界是“脚本化视觉引导手臂/手腕 + ACT-lite 控制手指”。它不是完整 ACT/DP，也不能说已经学会全机械手端到端抓取。

当前最好候选是 `stage3_act_lite_chunk_policy_v1_pinch30.pth`：

- 离线验证：val chunk RMSE raw `0.00332868`，优于 v0 的 `0.00412405`。
- 10 组闭环小验收：`9 / 10` 成功。
- 全手温和抓取：`5 / 5` 成功。
- thumb/index/middle 捏持：`4 / 5` 成功。
- 失败集中在 `right_low_zminus` 捏持 hold 阶段，真实抬升已经足够，但 hold slip 过高。

## 已完成

1. 写入闭环评估器：
   - `eval_stage3_act_lite_chunk_policy_v0.py`
   - 支持 `full_action` 和 `scripted_arm_predicted_hand` 两种执行模式。

2. 评估 v0 模型：
   - checkpoint：`checkpoints/stage3_act_lite_chunk_policy_v0.pth`
   - 正式报告：`docs/stage3_act_lite_chunk_policy_v0_eval_report.md`
   - `scripted_arm_predicted_hand` + `replan_interval=16`：`9 / 10`
   - `full_action` smoke：`0 / 2`

3. 生成补强数据集：
   - dataset：`data/stage3_skill_act_dp_sequence_dataset_v1_pinch30.npz`
   - episodes：`60 / 60` successful canonical episodes
   - full hand：`30`
   - pinch：`30`
   - rows：`230450`
   - diagnostic failed attempts：`3`

4. 训练 v1_pinch30：
   - checkpoint：`checkpoints/stage3_act_lite_chunk_policy_v1_pinch30.pth`
   - report：`docs/stage3_act_lite_chunk_policy_v1_pinch30_train_report.md`
   - best val MSE normalized：`0.0004957450`
   - val chunk RMSE raw：`0.00332868`

5. 评估 v1_pinch30：
   - report：`docs/stage3_act_lite_chunk_policy_v1_pinch30_eval_report.md`
   - `scripted_arm_predicted_hand` + `replan_interval=16`：`9 / 10`
   - right_low_zminus 失败项：`hold_slip_score_high`
   - right_low_zminus hold slip：v0 `0.767` -> v1 `0.692`

6. 排除单纯加宽 MLP：
   - checkpoint：`checkpoints/stage3_act_lite_chunk_policy_v1_pinch30_wide.pth`
   - right_low_zminus hold slip：`0.680`
   - 只比 v1 略好，仍失败。

## 为什么这很重要

离线 loss 下降不等于能抓起来。这轮工作第一次把 ACT-lite chunk policy 接回 MuJoCo 闭环，发现了三个关键事实：

- action chunk 执行方式很关键：`replan_interval=1` 会退化成每步只用 chunk 第 0 个动作，效果明显更差。
- 学习手指、脚本控制手臂是当前合理边界：`full_action` 直接控制 26 个 actuator 仍然失败。
- 捏持 hold-slip 是下一步主要瓶颈：补更多捏持数据能改善但不能完全解决。

## 如果成功

如果下一轮能把 `right_low_zminus` 捏持也压到 hold slip 阈值以内，就把 v1/v2 policy 放入 SkillZoo 的 learned candidate，对照 Stage3.7D 和 Stage3.8B 脚本 baseline 做更大规模随机姿态评估。

## 如果失败

不要继续只加大 MLP。优先做下面三条：

1. 分技能或分阶段 head：全手和捏持不要强行共享同一个动作头。
2. 专门做 pinch hold-slip residual：只在 `slow_lift/hold` 阶段调手指压力和接触保持。
3. 引入 temporal ensemble 或 DP/ACT 正式结构：当前 ACT-lite 只是 MLP chunk predictor，没有 ACT 的 CVAE/Transformer，也没有 DP 的去噪过程。

## 推荐下一步

进入 Stage3.9D：`pinch hold-slip repair for learned chunk policy`。

验收标准建议：

- right_low_zminus pinch 单场景至少 `5 / 5` 成功。
- 10 组 cycle eval 达到 `10 / 10`。
- 不允许用放宽 hold slip 阈值来过关。
- 保持 `full_action` 标记为失败诊断，不作为当前路线。
