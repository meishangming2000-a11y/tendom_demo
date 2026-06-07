# Stage3.9 SkillZoo v0 启动记录

日期：2026-06-06

## 为什么开 Stage3.9

Stage3.7D 和 Stage3.8B 已经说明：MuJoCo 虚拟视觉 + 合成触觉/滑移能指导全手温和抓取，也能指导二三指捏持。但这两个能力目前还是偏 demo 和参数搜索入口。

Stage3.9 的目的不是马上训练一个大模型，而是把这些 demo 变成可以复用、训练、比较和调度的技能。

## Stage3.9 的范围

Stage3.9 仍然是 MuJoCo 仿真阶段：

- 不接真实摄像头。
- 不接真实触觉或超声。
- 不接电机或真实机械手。
- 不让 LLM/VLA 直接输出 actuator。

第一版只做 `SkillZoo v0`：

```text
视觉/触觉状态
  -> 规则路由器
  -> 选择已注册技能
  -> 现有 demo/eval 入口或未来小模型
  -> 统一验收和失败原因
```

## 已落地文件

| 用途 | 文件 |
| --- | --- |
| 技能注册表 | `configs/stage3_skill_registry_v0.json` |
| SkillZoo 核心模块 | `stage3_skillzoo_v0.py` |
| 规则路由器命令 | `run_stage3_skill_router_v0.py` |
| 路由样例场景 | `metadata/stage3_skill_router_v0_sample_scenes.json` |
| 启动报告 | `docs/stage3_skill_router_v0_startup_report.md` |
| 启动 metadata | `metadata/stage3_skill_router_v0_startup.json` |
| Stage3.9B 数据导出器 | `export_stage3_skill_episode_dataset_v0.py` |
| Stage3.9B JSONL 数据 | `data/stage3_skill_episode_dataset_v0.jsonl` |
| Stage3.9B NPZ 数据 | `data/stage3_skill_episode_dataset_v0.npz` |
| Stage3.9B 数据报告 | `docs/stage3_skill_episode_dataset_v0_report.md` |
| Stage3.9B2 trace 序列导出器 | `export_stage3_skill_trace_sequence_dataset_v0.py` |
| Stage3.9B2 trace JSONL 数据 | `data/stage3_skill_trace_sequence_dataset_v0.jsonl` |
| Stage3.9B2 trace NPZ 数据 | `data/stage3_skill_trace_sequence_dataset_v0.npz` |
| Stage3.9B2 trace 报告 | `docs/stage3_skill_trace_sequence_dataset_v0_report.md` |
| Stage3.9B3 ACT/DP 就绪定义 | `docs/stage3_act_dp_readiness_definition_v0.md` |
| Stage3.9B3 dense obs/action 导出器 | `export_stage3_skill_act_dp_sequence_dataset_v0.py` |
| Stage3.9B3 ACT/DP NPZ 数据 | `data/stage3_skill_act_dp_sequence_dataset_v0.npz` |
| Stage3.9B3 ACT/DP 报告 | `docs/stage3_skill_act_dp_sequence_dataset_v0_report.md` |
| Stage3 ACT-lite 训练脚本 | `train_stage3_act_dp_baseline_v0.py` |
| Stage3 ACT-lite checkpoint | `checkpoints/stage3_act_lite_chunk_policy_v0.pth` |
| Stage3 ACT-lite 训练报告 | `docs/stage3_act_lite_chunk_policy_v0_train_report.md` |
| Stage3 ACT-lite 闭环评估器 | `eval_stage3_act_lite_chunk_policy_v0.py` |
| Stage3 ACT-lite v1_pinch30 数据 | `data/stage3_skill_act_dp_sequence_dataset_v1_pinch30.npz` |
| Stage3 ACT-lite v1_pinch30 checkpoint | `checkpoints/stage3_act_lite_chunk_policy_v1_pinch30.pth` |
| Stage3 ACT-lite v1_pinch30 closeout | `docs/stage3_act_lite_chunk_policy_v1_pinch30_closeout.md` |
| Stage3.9D pinch hold-slip repair closeout | `docs/stage3_9d_pinch_hold_repair_closeout.md` |
| Stage3.9D cycle10 验收报告 | `docs/stage3_9d_pinch_hold_repair_cycle10_report.md` |
| Stage3.9E random pose repair closeout | `docs/stage3_9e_random_pose_repair_closeout.md` |
| Stage3.9E repair 随机 30 组报告 | `docs/stage3_9e_random_pose_repair_30_report.md` |
| Stage3.9E no-repair 随机 30 组对照报告 | `docs/stage3_9e_random_pose_no_repair_30_report.md` |
| Stage3.9F 更大随机集和脚本 baseline 对照 closeout | `docs/stage3_9f_random_pose_baseline_comparison_closeout.md` |
| Stage3.9F ACT-lite repair 100 组报告 | `docs/stage3_9f_random_pose_repair_100_report.md` |
| Stage3.9F ACT-lite no-repair 100 组对照报告 | `docs/stage3_9f_random_pose_no_repair_100_report.md` |
| Stage3.9F 全手脚本 baseline 50 组报告 | `docs/stage3_9f_scripted_full_hand_recovery_50_report.md` |
| Stage3.9F 捏持脚本 selected baseline 50 组报告 | `docs/stage3_9f_scripted_pinch_selected_50_report.md` |
| Stage3.9G 最后一轮微调 closeout | `docs/stage3_9g_final_microtuning_closeout.md` |
| Stage3.9G 100 组主验收报告 | `docs/stage3_9g_full_fallback_pinch_verify_100_report.md` |
| Stage3.9G 捏持 final vision 验证报告 | `docs/stage3_9g_pinch_verify_preclose010_50_report.md` |
| Stage3.10A safety layer 冻结配置 | `configs/stage3_10a_skillzoo_safety_layer_v0.json` |
| Stage3.10A safety layer closeout | `docs/stage3_10a_skillzoo_safety_layer_v0_closeout.md` |
| Stage3.10A safety layer 检查入口 | `run_stage3_10a_safety_layer_v0.py` |
| Stage3.10A safety layer smoke 报告 | `docs/stage3_10a_safety_layer_v0_smoke_report.md` |
| Stage3.10B safety-labeled 数据导出 | `export_stage3_10b_safety_labeled_act_dp_dataset_v0.py` |
| Stage3.10B safety-labeled NPZ | `data/stage3_10b_safety_labeled_act_dp_dataset_v0.npz` |
| Stage3.10B safety-labeled 报告 | `docs/stage3_10b_safety_labeled_act_dp_dataset_v0_report.md` |
| Stage3.10B closeout | `docs/stage3_10b_safety_labeled_dataset_v0_closeout.md` |
| Stage3.10B-full safety-labeled train-ready NPZ | `data/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz` |
| Stage3.10B-full safety-labeled train-ready 报告 | `docs/stage3_10b_safety_labeled_act_dp_dataset_full_success_v0_report.md` |
| Stage3.10B-full closeout | `docs/stage3_10b_full_safety_labeled_dataset_v0_closeout.md` |
| Stage3.10B-full 59/60 诊断报告 | `docs/stage3_10b_safety_labeled_act_dp_dataset_full_v0_report.md` |
| Stage3.10B 8mm stress 报告 | `docs/stage3_10b_safety_labeled_act_dp_dataset_stress_pose008_v0_report.md` |
| Stage3.10 微调后模型训练计划 | `docs/stage3_10_model_training_after_microtuning_plan.md` |
| Stage3.10C safety ACT/CVAE-style 训练脚本 | `train_stage3_10c_safety_act_cvae_policy_v0.py` |
| Stage3.10C safety ACT/CVAE-style checkpoint | `checkpoints/stage3_10c_safety_act_cvae_policy_v0.pth` |
| Stage3.10C safety ACT/CVAE-style 训练报告 | `docs/stage3_10c_safety_act_cvae_policy_v0_train_report.md` |
| Stage3.10C safety ACT/CVAE-style closeout | `docs/stage3_10c_safety_act_cvae_policy_v0_closeout.md` |

## 当前注册的技能

1. `acquire_vision_pose`
   - 来源：Stage3.2c 虚拟摄像机感知。
   - 作用：在视觉置信度不足时先重新获取鸡蛋位姿。

2. `full_hand_gentle_grasp`
   - 来源：Stage3.7D。
   - 作用：全手温和抓取，适合低空间余量、低可见性或用户强调 gentle 的场景。
   - 当前可执行：有 eval 和 MuJoCo viewer smoke。

3. `thumb_index_middle_pinch`
   - 来源：Stage3.8B。
   - 作用：拇指 + 食指 + 中指捏持，适合空间余量高、视觉清晰、希望使用捏持的场景。
   - 当前可执行：有 selected candidate 和 MuJoCo viewer smoke。

4. `contact_settle`
   - 来源：Stage3.7B-3.7D。
   - 作用：触觉稳定等待，目前仍嵌在现有 eval 里。

5. `slow_lift_hold`
   - 来源：Stage3.7D 和 Stage3.8B。
   - 作用：慢抬升并保持，目前仍嵌在现有 eval 里。

6. `slip_recovery`
   - 来源：Stage3.7D。
   - 作用：滑移恢复，目前是 embedded microphase，下一步可以提出来做独立技能。

7. `release_or_abort`
   - 来源：Stage3.9。
   - 作用：安全中止或释放，当前是 planned safety skill。

## 怎么运行

只检查注册表和规则路由：

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_skill_router_v0.py
```

同时对可执行技能跑无窗口 smoke：

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_skill_router_v0.py --run-smoke --smoke-skill full_hand_gentle_grasp --smoke-skill thumb_index_middle_pinch
```

## 当前验收标准

Stage3.9A：

- `configs/stage3_skill_registry_v0.json` 能被解析。
- 每个 skill 都有输入、输出、成功标准、失败原因和来源阶段。
- 已验证 demo 有可追溯 report / metadata / smoke command。

Stage3.9B：

- 每个 episode 至少能表示 `skill_id`、视觉状态、触觉状态、动作摘要、成功/失败、失败原因。
- 这一步先定义中间 schema，不直接强行改成最终 LeRobot 格式。
- 当前已导出 `70` 条 episode rows：Stage3.7D `30` 条，Stage3.8B `40` 条。
- 当前 canonical training rows 是 `40` 条：Stage3.7D 全手抓 `30` 条 + Stage3.8B 选中捏持 `10` 条。
- 另外 `30` 条非选中捏持候选保留为 `diagnostic_variant`，用于失败分类和边界分析。
- B2 已导出 trace-level sequence：`70` 条 sequences、`1161` 个稀疏采样点、NPZ shape `[70, 27, 23]`。
- B2 明确不是 ACT/Diffusion Policy 可直接训练数据，因为现有 metadata 没有保存完整 observation/action。
- B3 已导出 dense obs/action sequence：`40` 条 canonical successful episodes、`179714` rows、`obs` shape `[179714, 130]`、`actions` shape `[179714, 26]`、padded obs shape `[40, 5220, 130]`。
- B3 当前 `act_ready=True`、`dp_ready=True`、`act_dp_ready=True`；这表示已经能训练 ACT/DP 风格模型，但不表示模型闭环通过。
- B3 训练集只保留成功 demo；捏持采集中有 `1` 条 `right_low_zminus` 失败 attempt 被单独记录为 diagnostic，没有进入 canonical training episodes。
- 第一版 ACT-lite offline training 已完成：`train_stage3_act_dp_baseline_v0.py` 使用 `obs_t + skill_id -> 16-step action chunk`，训练 `17933` 个 train windows、`4478` 个 val windows，best val MSE normalized `0.00084683`，val chunk RMSE raw `0.00412405`。
- 第一版 closed-loop evaluator 已完成：`eval_stage3_act_lite_chunk_policy_v0.py`。`full_action` smoke 为 `0 / 2`，说明完整 26 actuator 端到端控制仍不可用。
- v0 使用 `scripted_arm_predicted_hand` + `replan_interval=16` 的 10 组闭环小验收为 `9 / 10`，全手 `5 / 5`，捏持 `4 / 5`。
- v1_pinch30 补强数据集已生成：`60 / 60` successful canonical episodes，`230450` rows，full hand `30`，pinch `30`，另有 `3` 条捏持失败 attempt 进入 diagnostic。
- v1_pinch30 offline training 已完成：best val MSE normalized `0.0004957450`，val chunk RMSE raw `0.00332868`。
- v1_pinch30 closed-loop eval 仍为 `9 / 10`：右低场景 `right_low_zminus` 捏持能抬起，但 hold slip 仍高于阈值。宽 MLP 只把该 slip 从 `0.692` 小幅降到 `0.680`，没有解决。
- Stage3.9D 已完成 pinch hold-slip repair：在 `contact_settle / slow_lift / hold` 阶段锚定非主动手指，并给 thumb/index/middle 加 `0.08` 预闭合残差；不放宽 slip 阈值。
- Stage3.9D 验收通过：`right_low_zminus` 捏持 `5 / 5`，cycle 10 组 `10 / 10`；pinch hold max slip max 降到 `0.203477`，max crush `0.170027`，max penetration `0.003401 m`。
- Stage3.9E 随机 pose-noise 对照已完成：同一个 v1_pinch30 checkpoint，no-repair 为 `27 / 30`，repair 为 `30 / 30`。
- Stage3.9E repair 组中，全手 `15 / 15`，捏持 `15 / 15`；捏持 hold max slip max 为 `0.294448`，max crush `0.172517`，max penetration `0.003450 m`，仍低于现有阈值。
- Stage3.9E no-repair 对照的 3 个捏持失败集中在 `back_large_lift`、`lifted_diag` 和 `right_low_zminus`，主要失败项是 `vision_lift_too_small`、`true_lift_too_small`、`hold_slip_score_high` 和 `egg_still_touching_floor`。
- Stage3.9F 更大随机 pose-noise 对照已完成：v1_pinch30 + repair 为 `97 / 100`，no-repair 为 `84 / 100`。
- Stage3.9F repair 的全手分支为 `48 / 50`，捏持分支为 `49 / 50`；no-repair 的捏持分支只有 `36 / 50`，说明 repair 的收益稳定存在。
- Stage3.9F 脚本 baseline 对照：Stage3.7D 全手脚本 `50 / 50`，Stage3.8B selected pinch 脚本 `38 / 50`。这说明 ACT-lite + repair 的捏持强于原脚本捏持，但全手 learned branch 还弱于 Stage3.7D 脚本全手。
- Stage3.9F 小修补 probe：捏持 preclose `0.10` / close max `0.18` 达到 `49 / 50`，hold slip max 降到 `0.268310`，剩余失败是 `final_vision_failed_or_occluded` 且 true lift 为 `0.124330 m`。
- Stage3.9G 最后一轮微调已完成：full-hand 走 Stage3.7D fallback，pinch 使用 preclose `0.10` / close max `0.18`，final verification 使用 `vision_tactile_corroborated`。
- Stage3.9G 主验收为 `100 / 100`：full-hand `50 / 50`，pinch `50 / 50`。
- Stage3.9G pinch-only final vision 验证为 `50 / 50`，复现并修掉 9F 的 final vision low-confidence case。
- Stage3.10A 已冻结 safety layer v0：配置在 `configs/stage3_10a_skillzoo_safety_layer_v0.json`，检查入口是 `run_stage3_10a_safety_layer_v0.py --check`。
- Stage3.10B 已导出第一版 safety-labeled 数据：`10 / 10` episode，`38560` rows，`safety_labels` shape `[38560, 9]`。
- Stage3.10B-full 已扩展出主训练候选：`60 / 60` episode，`231421` rows，`obs [231421,130]`，`actions [231421,26]`，`safety_labels [231421,9]`，`stage3_10b_train_ready=True`。
- Stage3.10B-full 的边界诊断已保留：第一轮 `full_v0` 为 `59 / 60`，唯一失败是真抓取失败；8mm pose-noise stress 为 `19 / 20`，唯一失败是 final vision 低置信/遮挡，真实 lift 与触觉 hold 已通过。
- Stage3.10C-A 已完成第一版 safety ACT/CVAE-style 离线训练：使用 `full_success_v0`，`24000` train windows，`6000` val windows，best epoch `8`，val prior RMSE raw `0.0093151014`，val hand RMSE raw `0.0072230357`，val safety accuracy `0.9905235265`。
- Stage3.10C-A 仍不是 closed-loop promotion：还没有 MuJoCo 闭环评估，也不能宣称 full-action 26 actuator ACT/DP 抓取成功。

Stage3.9C：

- 规则路由器能在样例场景中自动选择技能。
- 当前样例必须覆盖：清晰空间选捏持、低空间选全手抓、接触滑移选恢复、低视觉先重定位、安全超阈值中止。

## 如果成功

Stage3.9G 已成功，Stage3.10A 已把它冻结为 safety layer v0，Stage3.10B 已跑通第一版 safety-labeled 数据出口，所以现在进入 Stage3.10B-full，不再继续 Stage3.9 小参数微调：

- 以 Stage3.10A safety layer v0 作为训练护栏和对照基线：视觉脚本控制手臂/手腕，ACT-lite 控制捏持手指，Stage3.7D 作为 full-hand fallback，tactile repair 和 visual-tactile final verification 作为 safety layer。
- 扩展 ACT/DP 训练数据，保留 skill_id、phase、failure reason、risk flags 和 safety layer 介入记录；下一步是把 `--episodes-per-skill` 放大，并加入更多 pose-noise、遮挡和失败/恢复场景。
- 训练正式 ACT Transformer/CVAE 或 Diffusion Policy baseline，并与 Stage3.9G safety layer 同场景对比。
- 建立更大 benchmark，不再只看一个 demo 或一组小参数。

## 如果失败

如果 Stage3.10 的模型训练失败，不回到 Stage3.9 小参数微调：

- 数据覆盖不足就补数据。
- 视觉遮挡失败就改 final verification / 多视角。
- 动作表示不合适就改 phase-specific、residual 或 chunk 表示。
- full_action 仍不稳定就继续保持 scripted arm/wrist，不强推端到端。

## 当前结论

Stage3.9 已经从 SkillZoo 数据面推进到 ACT-lite 闭环评估、触觉安全残差和最后一轮视觉/触觉验收修补。当前不是“已经学会完整 ACT/DP 抓取”，而是得到一个通过当前 `100 / 100` gate 的混合控制候选：Stage3.7D full-hand fallback + ACT-lite pinch hand chunk + tactile repair + visual-tactile final verification。下一步进入 Stage3.10 模型训练路线，不再继续做 Stage3.9 小参数微调。

## Stage3.10C-A 更新

Stage3.10C-A 已经把 Stage3.10B-full 的 safety-labeled 数据接入 safety ACT/CVAE-style 离线训练入口，并生成可加载 checkpoint。当前可以说“第一版离线 ACT/CVAE-style baseline 已训练”，但不能说“闭环抓取已经通过”。

如果成功：

- Stage3.10C-B 写 closed-loop evaluator，优先使用 `scripted_arm_predicted_hand`。
- 与 Stage3.10A safety layer 做同场景对比，至少报告成功率、full hand/pinch 分支、slip、final vision 和 safety label 触发情况。

如果失败：

- 先拆数据分布、动作 chunk、phase/skill 条件、safety label 辅助头和 final vision 遮挡。
- 不回到 Stage3.9 小参数微调；full-action 失败时继续保留 scripted arm/wrist，只把手指或安全残差交给模型。
