# Stage3.10E Stage3.10 Closeout

- 生成时间：`2026-06-09`
- 状态：`PASS`
- 结论：Stage3.10 可以作为 MuJoCo mixed-control safety baseline 收口。
- 边界：这不是 full-action 26 actuator ACT/DP 成功，不是硬件集成，不是真实摄像头或真实触觉。

## 这阶段到底完成了什么

Stage3.10 的目标不是再做一个单独 demo，而是把 Stage3.9 里有效的 SkillZoo / ACT-lite / repair 经验整理成一个可训练、可评估、可复现的安全控制基线。

当前成功边界是：

- arm/wrist 仍由视觉引导脚本控制；
- hand/fingers 由 learned ACT/CVAE-style chunk policy 控制；
- safety/fallback 处理触觉恢复、pinch repair、最终视觉/触觉验收；
- 视觉与触觉都来自 MuJoCo 虚拟传感器和合成 tactile/slip proxy。

## 关键结果

| step | 产出 | 验收 |
| --- | --- | ---: |
| Stage3.10A | 冻结 Stage3.9G safety layer 配置 | check/smoke 可复现 |
| Stage3.10B | safety-labeled ACT/DP 数据导出 | full_success 数据 `60 / 60`，`231421` rows，`safety_labels [231421, 9]` |
| Stage3.10C | safety ACT/CVAE-style offline policy + 闭环评估 | cycle50 `50 / 50`，random100_pose005 `100 / 100` |
| Stage3.10D-A | 鲁棒性探针 | `40 / 40` |
| Stage3.10D-B | 遮挡/noisy-vision 正式 benchmark | v0 `88 / 100` blocked，v1 修复后 `100 / 100` |
| Stage3.10D-C | occlusion/noisy-vision safety evidence head | 200 episode 样本，8 个 safety label，random val F1 `1.000` |
| Stage3.10D-D | safety-head 复扫 + 新 stress | D-B v1 rescan PASS；新增 depth/noise 与 false-positive stress `12 / 12` |

## 今天新增的实质进展

1. D-C 把 D-B v0 失败、v1 修复、occlusion-aware 终验、accepted_nominal 质量适配和 pinch repair 事件整理成 episode-level safety-head 数据。
2. D-D 用 safety head 复扫 D-B v1：`100` 条记录，mean evaluable F1 `1.000`，没有把 hold-safe 成功误报成失败，也没有漏掉 failure/blocker。
3. D-D 新增 stress 小基准：`initial_depthnoise5_pose005` 为 `6 / 6`，`final_falseblob_occlusionaware_pose005` 为 `6 / 6`。
4. 修复 noisy virtual-camera estimator：`depth_noise_5mm` 曾导致捏持初始视觉失败，原因是深度噪声让椭球拟合中心跑飞；现在加入 median-depth ray fallback 后通过闭环。
5. 明确保留失败边界：`initial_combinedhard_pose003_boundary` 为 `1 / 2`，捏持分支在初始 combined_hard 下被视觉门拒绝。这个拒绝是合理的，不能通过放宽抓取阈值硬过。

## 现在可以怎么复现

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_10d_c_occlusion_safety_head_v0.py
```

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_10d_d_safety_head_rescan_v0.py
```

```powershell
python .\open_demo.py stage3_10d --dry-run
```

`stage3_10d` 是 report/gallery 入口，不是 live MuJoCo viewer。想看可视化抓取，仍然用：

```powershell
python .\open_demo.py pinch_egg --speed 10
python .\open_demo.py full_hand_egg --speed 3
```

## 仍然不能声称什么

- 不能声称 full-action ACT/DP 已经能闭环控制 26 个 actuator；旧 `full_action` smoke 仍是失败边界。
- 不能声称真实摄像头、真实触觉、超声或硬件已经接入 Stage3。
- 不能声称 `combined_hard` 初始视觉已经解决；它需要更强视觉路线。
- 不能说 safety head 已经是在线控制器；D-C/D-D 目前是 episode-level evidence head 和复扫工具。

## 如果成功

Stage3.10 收口，进入 Stage3.11：把当前 mixed-control baseline 变成更强的 staged full-action / residual-policy 训练路线。推荐先做三件事：

1. 把 D-C safety head 接入 evaluator 的在线检查，而不是只做事后复扫。
2. 导出逐帧 noisy/occlusion safety labels，让 ACT/DP 训练直接看到视觉退化与 tactile handoff。
3. 单独开 full-action repair/residual policy，不再把它塞进 Stage3.10。

## 如果失败

如果后续卡在 `combined_hard`，优先补视觉能力，而不是调抓取参数：多相机一致性、时序滤波、显式 false-positive 分割、训练式 pose estimator 都比放宽 slip/crush/penetration 阈值更合理。
