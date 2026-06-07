# Stage3.10A SkillZoo Safety Layer v0 Closeout

生成日期：2026-06-07

## 这一步的目的

Stage3.10A 不是继续微调抓取参数，而是把 Stage3.9G 已经通过的混合控制系统冻结成一个可复现的 safety layer v0。后面训练 ACT Transformer/CVAE 或 Diffusion Policy 时，都要拿它当安全护栏和对照基线。

通俗地说：先把“现在这套确实能稳定跑起来的办法”装进一个带说明书的盒子里。以后新模型只有在同样场景下接近或超过这个盒子的表现，才值得继续往主线提。

## 冻结的控制栈

- 视觉：MuJoCo 虚拟 RGB-D/segmentation 相机，主相机是 `stage3_egg_closeup`。
- 手臂/手腕：仍然是视觉引导脚本控制，不交给 ACT/DP 直接输出。
- 全手抓取：使用 Stage3.7D fallback，也就是带触觉/滑移恢复的 full-hand gentle grasp。
- 捏持抓取：使用 `stage3_act_lite_chunk_policy_v1_pinch30.pth` 的手指 chunk 预测，再叠加 tactile repair。
- 捏持 repair：`inactive_anchor_slip_close`，阶段覆盖 `contact_settle,slow_lift,hold`。
- 关键参数：`preclose_delta=0.10`，`close_max=0.18`，`inactive_alpha=1.0`。
- 最终验收：捏持最终视觉采用 `vision_tactile_corroborated`，也就是视觉低置信但触觉和真实抬升证据一致时可以通过。

这里没有放宽主要安全阈值：hold slip、crush、penetration 和 floor contact 仍按原 gate 检查。

## 新增产出

- 冻结配置：`configs/stage3_10a_skillzoo_safety_layer_v0.json`
- 一键检查入口：`run_stage3_10a_safety_layer_v0.py`
- 本 closeout：`docs/stage3_10a_skillzoo_safety_layer_v0_closeout.md`

检查命令：

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_10a_safety_layer_v0.py --check
```

打印 100 组 canonical eval 命令：

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_10a_safety_layer_v0.py --print-command
```

运行 4 组 smoke：

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_10a_safety_layer_v0.py --run-smoke
```

本轮 smoke 已通过：

- metadata：`metadata/stage3_10a_safety_layer_v0_smoke.json`
- report：`docs/stage3_10a_safety_layer_v0_smoke_report.md`
- 总结果：`4 / 4`
- 全手：`2 / 2`
- 捏持：`2 / 2`
- 注意：smoke 中仍出现 `early_contact_in_approach`、`transient_slip_high` 和少量 `recovery_budget_exhausted` 风险标记，所以它证明的是可复现入口可用，不是风险消失。

## 9G 证据

主验收：

- metadata：`metadata/stage3_9g_full_fallback_pinch_verify_100.json`
- report：`docs/stage3_9g_full_fallback_pinch_verify_100_report.md`
- 总结果：`100 / 100`
- 全手：`50 / 50`
- 捏持：`50 / 50`

捏持最终视觉复查：

- metadata：`metadata/stage3_9g_pinch_verify_preclose010_50.json`
- report：`docs/stage3_9g_pinch_verify_preclose010_50_report.md`
- 总结果：`50 / 50`

这些结果说明当前 safety layer 可以作为 Stage3.10 训练前的冻结基线，但它仍然是 mixed control，不是 full-action ACT/DP。

## 仍要盯住的风险

- `early_contact_in_approach`：接近阶段仍有提前接触。
- `transient_or_hold_slip`：全手分支仍有瞬时或保持阶段滑移标记。
- `transient_slip_high`：捏持分支仍有瞬时高滑移峰值。
- `recovery_budget_exhausted`：部分全手 episode 会用尽恢复预算。
- `final_vision_occluded_or_low_confidence`：最终视觉仍可能被手遮挡，需要触觉佐证。

这些风险不会阻止 Stage3.10A 冻结，但会进入 Stage3.10B 以后数据集和 benchmark 的 failure taxonomy。

## 如果成功

进入 Stage3.10B：扩展 ACT/DP 训练数据。数据要记录视觉状态、触觉/滑移、skill id、phase、safety layer 介入时刻、成功/失败原因和风险标记。后续正式 ACT/CVAE 或 DP baseline 必须和这个 safety layer 同场景对比。

## 如果失败

不回到 Stage3.9 小参数微调。先检查三件事：

1. 配置引用是否缺文件或路径错误。
2. 9G 证据是否仍能解析并满足 `100/100` 和 `50/50`。
3. smoke 是否暴露复现 bug。

如果是复现 bug，就修入口或报告；如果是模型训练失败，则进入 Stage3.10B/10C 的数据覆盖、动作表示或 phase-specific residual 分析。
