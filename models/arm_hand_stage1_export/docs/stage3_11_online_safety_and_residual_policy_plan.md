# Stage3.11 Online Safety Head and Residual Policy Plan

- 生成时间：`2026-06-09`
- 状态：`Stage3.11D-A diagnostic PASS，ready for Stage3.11D-B`
- 当前基线：`Stage3.10E MuJoCo mixed-control safety baseline + Stage3.11B online safety-head shadow observer + Stage3.11C trace-frame safety labels + Stage3.11D-A pinch morphology/friction audit`
- 下一步：`Stage3.11D-B morphology-gated safety-conditioned hand/residual policy`
- 边界：MuJoCo-only；不是 full-action ACT/DP promotion；不是硬件、真实摄像头、真实触觉或超声集成。

## 总目标

Stage3.11 的目标不是继续为了一个 demo 调几个参数，而是把 Stage3.10E 已经验证过的混合控制基线，推进成更像“可训练系统”的结构：

1. 把 Stage3.10D-C 的 safety head 从事后复扫工具，接到在线 evaluator 里。
2. 把遮挡、noisy vision、tactile handoff、repair/risk 这些状态导出成逐帧标签。
3. 在不放宽 slip/crush/penetration/final-vision 阈值的前提下，尝试 staged residual/full-action policy。
4. 让每一次成功或失败都能回流到数据、标签、可视化和下一轮训练里。

通俗讲：Stage3.10E 已经说明“混合控制路线可以稳定抓住”；Stage3.11 要让系统自己在运行时知道“现在视觉可靠不可靠、什么时候该交给触觉、什么时候该修复、什么时候该拒绝”，再用这些信号去训练更强的策略。

## 当前基线

- Stage3.10B-full_success_v0：`60 / 60` episodes，`231421` rows，`obs [231421,130]`，`actions [231421,26]`，`safety_labels [231421,9]`。
- Stage3.10C-C：`scripted_arm_predicted_hand` cycle50 `50 / 50`，random100_pose005 `100 / 100`。
- Stage3.10D-B：遮挡/noisy-vision v0 `88 / 100` blocked；v1 合计 `100 / 100`。
- Stage3.10D-C：`200` 个 episode-level safety-head 样本，random validation F1 `1.000`。
- Stage3.10D-D：D-B v1 safety-head rescan PASS；新增 depth/noise 与 false-positive stress `12 / 12`。
- Stage3.11B：online safety-head shadow mode PASS；D-B v1 `100 / 100`，stress `13 / 14`（其中 `combined_hard` 仍是合理拒绝边界），unsafe hold-safe prediction `0`。
- Stage3.11C：trace-frame safety labels PASS；`164` episodes，`2663` trace frames，`17` labels，clean / pose-noise / mask dropout / occlusion / depth-noise / false-positive / combined_hard 覆盖齐全。
- Stage3.11D-A：pinch morphology/friction audit PASS；当前 selected pinch 在 egg-only 与 matched-hand 摩擦 sweep 中 `8 / 8` 成功，但 `two_finger_tip_pinch_fraction = 0`、`wrap_frame_fraction = 1`，说明用户观察到的“包裹/夹娃娃机式三指夹持”主要是 grasp morphology/objective 问题，不只是鸡蛋表面摩擦问题。
- 保留边界：`combined_hard` 初始视觉拒绝是合理边界；`full_action` 26 actuator smoke 仍失败，不能宣称 ACT/DP 已经闭环成功。

## 阶段拆分

### Stage3.11A 计划与地图契约

产出：
- 本计划文档。
- `metadata/stage3_11_online_safety_and_residual_policy_plan.json`。
- Stage3 子思维导图新增 Stage3.11 节点。
- 项目总思维导图、快速入口、agentic index、nervous-system capsule 同步。

验收：
- `python .\simulations\models\arm_hand_stage1_export\stage3_progress_mindmap_viewer.py --check`
- `python .\project_progress_mindmap_viewer.py --check`
- `python .\tools\check_project_nervous_system.py --tier light`

如果成功：
- 进入 Stage3.11B，把 safety head 接入在线 evaluator 的 shadow mode。

如果失败：
- 先修文档、metadata、思维导图和索引一致性，不进入代码实现。

### Stage3.11B Online Safety-Head Shadow Mode

当前状态：已完成并通过。主报告见 `docs/stage3_11b_online_safety_head_shadow_v0_closeout.md`，metadata 见 `metadata/stage3_11b_online_safety_head_shadow_v0.json`。

目的：
把 Stage3.10D-C 的 safety-head checkpoint 接到 evaluator 中，但先不让它影响动作，只记录在线预测和真实结果的差异。

产出：
- 一个 Stage3.11B runner 或 evaluator 扩展。
- 每个 episode 的 safety-head prediction summary。
- shadow-mode closeout/report。

验收：
- D-B v1 复扫仍 PASS。
- 新增 depth/noise 与 false-positive stress 仍 `12 / 12`。
- `unsafe_hold_safe_prediction = 0`。
- `combined_hard` 仍作为 reject boundary，不靠放宽阈值过关。

如果成功：
- 进入 Stage3.11C，把在线预测展开成逐帧标签。
- 已发现的 C 入口问题：`combined_hard` 拒绝边界中有两个非危险 label mismatch，说明 `initial_quality_adapter_required` 和 `pinch_repair_required_or_active` 需要拆得更细，尤其要区分 `repair_configured` 和 `repair_active`。

如果失败：
- 区分是 safety-head 特征输入错位、checkpoint 加载错、标签定义不一致，还是 online/offline 分布不一致；先修 shadow mode，不进入 residual policy。

### Stage3.11C Frame-Level Noisy/Occlusion Safety Labels

当前状态：已完成并通过。主报告见 `docs/stage3_11c_frame_safety_labels_v0_closeout.md`，dataset 见 `data/stage3_11c_frame_safety_labels_v0.npz`，metadata 见 `metadata/stage3_11c_frame_safety_labels_v0.json`。

目的：
把 episode-level 安全判断变成逐帧训练标签，让后续 ACT/DP 或 residual policy 能看到“视觉退化发生在哪一帧、触觉交接从哪一帧开始、repair 从哪一帧启动”。

建议标签：
- `vision_degraded`
- `vision_freeze`
- `tactile_handoff`
- `repair_active`
- `risk_any`
- `hold_safe`
- `failure_risk`

产出：
- NPZ/JSONL 逐帧安全标签数据。
- 标签覆盖率报告。
- 与 Stage3.10B safety labels 的对齐说明。

验收：
- 正样本非零，不是全 0 标签。
- 回放 episode 数、frame 数、skill/phase 分布与来源数据可对齐。
- 至少覆盖 clean、pose-noise、mask dropout、final occlusion、depth noise、false positive stress。

如果成功：
- 进入 Stage3.11D，用这些标签训练或评估 safety-conditioned hand/residual policy。
- 可选分支：如果 D 需要 dense obs/action 对齐，而不是 trace-frame 标签，先做 Stage3.11C2 dense capture，不直接把 trace-frame 数据伪装成 dense ACT/DP 数据。

如果失败：
- 先修标签定义和数据采样，不把错标签喂给策略训练。

### Stage3.11D-A Pinch Morphology / Friction Audit

当前状态：已完成并通过。主报告见 `docs/stage3_11d_a_pinch_morphology_friction_audit_v0_closeout.md`，metadata 见 `metadata/stage3_11d_a_pinch_morphology_friction_audit_v0.json`。

目的：
在进入 hand/residual policy 训练前，先把用户在 demo 中看到的“像三指包裹而不是指尖捏持”量化。这个步骤不改变当前 controller，只审计 selected pinch candidate 在不同接触材料条件下的真实接触形态。

产出：
- `run_stage3_11d_a_pinch_morphology_friction_audit_v0.py`。
- egg-only 与 matched-hand 摩擦 sweep 报告。
- morphology 指标：`two_finger_tip_pinch_fraction`、`three_digit_clamp_fraction`、`wrap_frame_fraction`、`tip_contact_ratio`、`non_tip_contact_ratio`。

验收：
- 脚本可复现运行并生成 report/metadata。
- 不把结果提升成新 controller baseline。
- 明确区分 material/friction sensitivity 和 grasp objective/morphology 问题。

结果：
- `8 / 8` episode 成功抓取，说明当前夹持仍稳定。
- `two_finger_tip_pinch_fraction = 0`，说明当前不是纯二指指尖捏持。
- `wrap_frame_fraction = 1`，且非指尖接触占比约 `0.63 - 0.78`，说明包裹/多段接触主导。
- 改鸡蛋摩擦会改变三指夹持比例和接触数量，但没有把动作变成 true pinch；后续应把 morphology gate/objective 加入训练与搜索目标。

如果成功：
- 进入 Stage3.11D-B：先定义 true-pinch morphology gate，再做 safety-conditioned hand/residual policy。

如果失败：
- 先修接触分类、摩擦 sweep 或 morphology 指标，不把模糊的“看起来像捏”喂给训练。

### Stage3.11D-B Safety-Conditioned Hand/Residual Policy

目的：
先不要直接冲 full_action。优先训练手指/手部 residual 或 safety-conditioned hand policy，让它在视觉不可靠、触觉接管、repair 激活时更稳定；同时加入 true-pinch morphology gate，避免继续优化“能抓住但像包裹”的动作。

产出：
- 一个手部 residual 或 safety-conditioned policy 训练脚本。
- closed-loop evaluator。
- 与 Stage3.10E mixed-control baseline 的同场景对比。
- 与 Stage3.11D-A morphology 指标的同场景对比。

验收：
- Stage3.10E canonical gate 不下降：`100 / 100` 或同等规模不低于当前 baseline。
- D-D stress 不下降。
- hold slip、crush、penetration 不因 residual 变差。
- 必须有 ablation：有 safety labels vs 无 safety labels。
- 必须报告 morphology ablation：有 true-pinch morphology conditioning/objective vs 无 morphology conditioning/objective。
- 不允许只用“抬起来了”替代 true pinch；至少要降低 `wrap_frame_fraction` 或提高 `two_finger_tip_pinch_fraction`，否则只能算稳定夹持，不算捏持进步。

如果成功：
- 把 residual policy 作为 Stage3.11 candidate，不立刻宣称 full_action 成功；如果 morphology 没改善，只能作为 safety/stability candidate，不能作为 true-pinch candidate。

如果失败：
- 判断失败来自策略表示、标签噪声、数据覆盖不足、residual 注入过强，还是 morphology objective 与现有几何/摩擦冲突；回到 C、D-A 或 D-B 的数据/结构修复。

### Stage3.11E Staged Full-Action / Residual Attempt

目的：
在前面稳定后，再尝试更接近 full_action 的分阶段策略。这里仍然不是一口气端到端输出 26 个 actuator，而是约束在 scripted trajectory 周围做 residual。

建议顺序：
1. arm/wrist residual 很小，hand policy 保持当前强基线。
2. 只在 approach 或 preshape 阶段允许 arm/wrist residual。
3. smoke `2 / 2` 后再做 cycle10。
4. cycle10 `10 / 10` 后再做 random30/50。

验收：
- 不允许靠放宽 slip/crush/penetration/final-vision 阈值过关。
- 任一阶段低于 mixed-control baseline，就保留为失败记录，不 promotion。

如果成功：
- 进入 Stage3.11F，把 safety/residual 行为可视化，方便检查。

如果失败：
- 将失败原因记录为 full_action/residual boundary，不回退到单 demo 微调。

### Stage3.11F 可视化

目的：
让 demo 一眼能看出：系统正在用视觉、触觉、safety head 和 repair/residual，而不是一个黑盒动作回放。

建议 overlay：
- 绿色：视觉估计 OK。
- 黄色：视觉退化/冻结。
- 蓝色：触觉接管。
- 橙色：repair/residual 激活。
- 红色：safety head 预测风险或拒绝。

验收：
- 有一条命令能打开 MuJoCo viewer。
- viewer 中能看到 safety-head 状态、vision/tactile handoff、repair/residual 事件。
- Demo Gallery 和 `open_demo.py` 更新。

如果成功：
- 进入 Stage3.11G closeout，决定是否提升 Stage3.11 candidate。

如果失败：
- 可视化先作为 diagnostic，不影响控制 baseline；修 overlay 和日志对齐。

### Stage3.11G Closeout / Promotion Decision

目的：
整理 Stage3.11 是否真正提升了系统。

Promotion 条件：
- 至少不弱于 Stage3.10E mixed-control baseline。
- safety-head online shadow 或在线 evaluator 有明确收益或明确拒绝边界。
- frame-level labels 可复用。
- residual/full-action 如果失败，也有可复现失败原因和下一步路线。

如果成功：
- Stage3.11 成为新的 MuJoCo safety/residual baseline。

如果失败：
- Stage3.10E 仍是当前 baseline，Stage3.11 产物保留为诊断和数据工程基础。

## 思维导图位置

Stage3.11 应挂在：

`Stage3 总目标 -> 控制和学习路线 -> Stage3.10 mixed-control safety baseline -> Stage3.11 在线 safety head 与 residual policy`

项目总图中对应：

`Tendon Project 项目总览 -> 当前主线 -> Stage3.11A`

## 立刻可运行的检查命令

```powershell
python .\simulations\models\arm_hand_stage1_export\stage3_progress_mindmap_viewer.py
python .\project_progress_mindmap_viewer.py
python .\simulations\models\arm_hand_stage1_export\stage3_progress_mindmap_viewer.py --check
python .\project_progress_mindmap_viewer.py --check
python .\tools\check_project_nervous_system.py --tier light
```
