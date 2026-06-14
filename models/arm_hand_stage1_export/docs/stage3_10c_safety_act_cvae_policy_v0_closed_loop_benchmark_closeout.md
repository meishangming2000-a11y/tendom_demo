# Stage3.10C-C Safety ACT/CVAE Closed-Loop Benchmark Closeout

日期：2026-06-08

## 这一步做了什么

Stage3.10C-C 把 Stage3.10C-B 的 `scripted_arm_predicted_hand` 闭环初验扩大为正式 benchmark，并与 Stage3.10A safety layer 的 canonical benchmark 对齐。

Stage3.10C-C 的执行模式仍然是：

```text
scripted_arm_predicted_hand
```

含义：

- 手臂/手腕继续由虚拟视觉脚本控制。
- Stage3.10C safety ACT/CVAE 模型控制手指 action chunk。
- pinch 分支仍保留 safety repair 与 final vision/tactile corroboration。
- 这不是 full-action 26 actuator promotion。

## 新增/使用的入口

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_10c_safety_act_cvae_policy_v0.py
```

核心输出：

```text
simulations/models/arm_hand_stage1_export/docs/stage3_10c_safety_act_cvae_policy_v0_closed_loop_cycle50_report.md
simulations/models/arm_hand_stage1_export/docs/stage3_10c_safety_act_cvae_policy_v0_closed_loop_random100_pose005_report.md
```

## Stage3.10C-C 结果

### cycle50

- 报告：`docs/stage3_10c_safety_act_cvae_policy_v0_closed_loop_cycle50_report.md`
- 状态：`PASS`
- 总成功：`50 / 50`
- full hand gentle grasp：`25 / 25`
- thumb index middle pinch：`25 / 25`
- full hand mean final lift：`0.103493 m`
- pinch mean true lift：`0.104035 m`
- full hand mean hold slip：`0.183636`
- pinch mean hold slip：`0.184492`

### random100_pose005

- 报告：`docs/stage3_10c_safety_act_cvae_policy_v0_closed_loop_random100_pose005_report.md`
- 状态：`PASS`
- 总成功：`100 / 100`
- full hand gentle grasp：`50 / 50`
- thumb index middle pinch：`50 / 50`
- random offset std：`0.005 m`
- full hand mean final lift：`0.104006 m`
- pinch mean true lift：`0.104818 m`
- full hand mean hold slip：`0.177207`
- pinch mean hold slip：`0.195535`
- full hand max hold slip：`0.281960`
- pinch max hold slip：`0.294834`

## 与 Stage3.10A safety layer 对照

Stage3.10A canonical baseline 仍然通过 `run_stage3_10a_safety_layer_v0.py --check`。

Stage3.10A canonical benchmark：

- 总成功：`100 / 100`
- full hand gentle grasp：`50 / 50`
- thumb index middle pinch：`50 / 50`
- random offset std：`0.005 m`
- full hand mean hold slip：`0.179356`
- pinch mean hold slip：`0.190889`

Stage3.10C-C random100_pose005：

- 总成功：`100 / 100`
- full hand gentle grasp：`50 / 50`
- thumb index middle pinch：`50 / 50`
- random offset std：`0.005 m`
- full hand mean hold slip：`0.177207`
- pinch mean hold slip：`0.195535`

结论：Stage3.10C-C 在 `scripted_arm_predicted_hand` 模式下已经达到 Stage3.10A canonical baseline 的同规模成功率；full hand hold slip 略低，pinch hold slip 略高，但都在成功阈值内。

## 仍然存在的边界

- `full_action` smoke 仍是 `0 / 1`，不能宣称 26 actuator end-to-end ACT/DP 成功。
- 每组仍记录 `early_contact_in_approach`，说明接近阶段还不是干净接触。
- pinch 分支仍有高 transient slip，虽然 hold slip 在阈值内。
- 还没有 viewer demo；如果要展示画面，仍看 `pinch_egg` 或 `full_hand_egg`。
- 这仍是 MuJoCo-only，不是硬件集成。

## 如果成功

下一步可以进入 Stage3.10D：

- 增加 held-out trial。
- 增加遮挡/低视觉置信场景。
- 增加更强 pose-noise。
- 单独分析 safety head 是否提前预测风险。
- 设计 full-action 的分阶段修复，而不是直接要求一个模型控制全部 26 actuator。

## 如果失败

不回到 Stage3.9 小参数微调，也不放宽成功阈值。优先拆：

- arm/wrist 动作表示是否需要 phase-specific/residual policy。
- action chunk 执行间隔是否需要 adaptive replan。
- safety head 是否能提前预测 transient slip。
- 训练数据是否缺少失败恢复样本。
