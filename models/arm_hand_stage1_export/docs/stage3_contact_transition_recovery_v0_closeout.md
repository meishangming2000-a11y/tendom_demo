# Stage3.7D 接触转换恢复微阶段收尾记录

生成日期：2026-06-05

## 这一步要解决什么

Stage3.7C 的思路是：如果 `slow_lift`（慢速抬升）阶段滑移偏高，就先暂停一会儿。

这一步有用，但问题也很明显：它只是“等一等”，并没有改变手的动作。因此很多测试会出现 `transition_gate_budget_exhausted`（接触转换门控预算耗尽），意思是已经等到上限了，滑移风险还是没有完全消掉。

Stage3.7D 的目标是把“只等待”升级成“轻微恢复动作”：当 `slow_lift` 滑移偏高时，不只是卡住阶段进度，而是让控制进度轻微后退一点点，给接触重新稳定的机会。

## 最终采用的参数

- 脚本：`eval_stage3_contact_transition_recovery_v0.py`
- 基线：Stage3.6 learned hand policy（学习手指策略）+ Stage3.7B tactile lift gate（触觉抬升许可门控）+ Stage3.7D recovery microphase（恢复微阶段）
- 恢复阶段：`slow_lift`
- 滑移阈值：`0.29`
- 每个阶段最大恢复预算：`200` steps
- 恢复进度回退：`0.01`
- 恢复稳定窗口：`0`

## 和 Stage3.7C 的对比

| 测试 | Stage3.7C | Stage3.7D |
|---|---:|---:|
| 固定 10 组成功率 | 10/10 | 10/10 |
| 固定 10 组 mean max slip | 0.563551 | 0.554890 |
| 固定 10 组 max hold slip | 0.264026 | 0.253566 |
| 固定 10 组预算耗尽 | 6/10 | 5/10 |
| 随机 30 组成功率 | 30/30 | 30/30 |
| 随机 30 组 mean max slip | 0.601636 | 0.569917 |
| 随机 30 组 max hold slip | 0.315310 | 0.315078 |
| 随机 30 组预算耗尽 | 19/30 | 15/30 |

结论：Stage3.7D 可以作为新的 Stage3 候选基线。它没有牺牲成功率，也没有让保持阶段滑移超标；平均最大滑移和预算耗尽次数都比 Stage3.7C 更好。

## 还没有解决的问题

- 最大瞬时滑移仍然可能到 `0.941` 或 `1.000`，所以不能说滑移问题已经完全解决。
- `early_contact_in_approach`（接近阶段过早接触）仍然每组都会出现，这是单独的路径/接近策略风险。
- 随机 30 组里仍有 `15/30` 出现恢复预算耗尽，说明恢复微阶段有帮助，但还不是最终策略。
- 滑移峰值仍主要集中在 `slow_lift`、`contact_settle` 和 `gentle_close_thumb` 附近。

## 如果成功

本次结果满足成功分支：

- 把 Stage3.7D 记录为新的 Stage3 候选基线。
- 更新项目总思维导图和 Stage3 子思维导图。
- 更新本地 `tendon-project` 技能记忆，之后对齐时可以直接知道当前主线不是 Stage3.7C，而是 Stage3.7D。
- 下一步不要继续只微调等待时间，而是进入更高层的鲁棒性验证：更多位姿扰动、更多视觉噪声、更复杂遮挡、更多接触边界。

## 如果失败

如果后续更大规模测试发现 Stage3.7D 退步，处理方式是：

- 立即回退到 Stage3.7C，不把 Stage3.7D 当作主线。
- 按失败类型拆开看：成功率下降、hold slip 超过 0.35、mean max slip 没改善、预算耗尽仍过多。
- 只做小规模 probe（探针测试）定位失败 phase（阶段），不要直接开大规模训练。
- 如果多轮 probe 都无改善，就把这个恢复微阶段方向标为 rejected（否决方向），转向更细的触觉稳定判据或 residual（残差）策略。

## 相关产物

- 固定 10 组报告：`docs/stage3_contact_transition_recovery_v0_eval_report.md`
- 固定 10 组 metadata：`metadata/stage3_contact_transition_recovery_v0_eval.json`
- 随机 30 组报告：`docs/stage3_contact_transition_recovery_v0_randomized30_report.md`
- 随机 30 组 metadata：`metadata/stage3_contact_transition_recovery_v0_randomized30.json`
- 对比基线：`docs/stage3_contact_transition_gate_v0_closeout.md`
