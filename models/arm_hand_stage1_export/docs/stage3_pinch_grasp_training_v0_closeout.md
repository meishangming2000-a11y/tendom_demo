# Stage3.8B Pinch Grasp Training V0 Closeout

生成日期：2026-06-06

## 这次做了什么

这次不是只做一个小 probe，而是把捏持式抓取做成了一个可复现训练/筛选流程。

新增训练脚本：

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_pinch_grasp_candidates_v0.py
```

新增成功 demo：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_pinch_grasp_viewer.py --candidate-config .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_training_v0_selected.json
```

无窗口快速验收：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_pinch_grasp_viewer.py --headless-smoke --trial center_nominal
```

这仍然是 MuJoCo-only：虚拟摄像机负责定位和最终抬升确认，合成触觉/滑移负责捏持接触、稳定性、滑移、挤压和穿透判断。不使用现实摄像头，也不使用真实硬件。

## 训练方式

这里的“训练”是参数搜索和课程式评估，不是神经网络训练。

流程：

1. 4 个方法族：
   - `thumb_index_light`
   - `thumb_index_middle`
   - `thumb_index_middle_strong`
   - `tripod_support`
2. 每个方法族生成 7 个参数变体。
3. 训练阶段：28 个候选，共 56 次 episode。
4. 家族验证：每个方法族选 1 个赢家，共 12 次 episode。
5. 最终验收：4 个 finalist 各跑 10 次，共 40 次 episode。

完整报告：

```text
simulations/models/arm_hand_stage1_export/docs/stage3_pinch_grasp_training_v0_report.md
```

完整数据：

```text
simulations/models/arm_hand_stage1_export/metadata/stage3_pinch_grasp_training_v0.json
```

## 最终结果

最终胜出候选：

```text
thumb_index_middle_strong__higher_approach
```

含义：

- active fingers：`thumb + index + middle`
- 比 `tripod_support` 更接近“几根手指掐住鸡蛋”
- 不再依赖 ring finger 作为主要支撑
- approach 稍微更高，减少部分早期几何干扰

最终 10 次随机扰动验收：

| 指标 | 结果 |
| --- | ---: |
| success | `10 / 10` |
| mean true lift | `0.10347 m` |
| mean vision lift | `0.11433 m` |
| hold stable fraction mean | `1.000` |
| hold pinch fraction mean | `1.000` |
| hold pinch purity mean | `0.779` |
| max hold slip | `0.276` |
| max crush risk | `0.143` |
| max penetration | `0.002866 m` |
| failure reasons | `{}` |

最终 finalist 对比：

| candidate | success | 结论 |
| --- | ---: | --- |
| `thumb_index_middle_strong__higher_approach` | `10 / 10` | 当前 Stage3.8B 成功 demo baseline |
| `tripod_support__higher_approach` | `9 / 10` | 很稳，但有一次 hold slip 超阈值，而且 ring support 更强 |
| `thumb_index_middle__higher_approach` | `9 / 10` | 可用但不如 strong 版本稳 |
| `thumb_index_light__higher_approach` | `6 / 10` | 单 index 方法仍不够稳，容易抬升不足或 hold slip 高 |

## 成功 demo 验收

已通过：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_pinch_grasp_viewer.py --headless-smoke --trial center_nominal
```

输出摘要：

```text
candidate=thumb_index_middle_strong__higher_approach
status=PASS
reason=success_vision_confirmed_pinch_lift_hold
vision_lift=0.1061
true_lift=0.1014
pinch=1.000
stable=1.000
hold_slip=0.185
```

带视觉 debug 的无窗口验收也已通过：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_pinch_grasp_viewer.py --headless-smoke --trial center_nominal --render-vision-debug --debug-dir .\simulations\models\arm_hand_stage1_export\docs\visual_checks_stage3_pinch_viewer_v0
```

视觉证据：

```text
simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_pinch_viewer_v0/thumb_index_middle_strong__higher_approach/000_center_nominal/initial_mask_overlay.png
simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_pinch_viewer_v0/thumb_index_middle_strong__higher_approach/000_center_nominal/final_stage3_egg_closeup_mask_overlay.png
simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_pinch_viewer_v0/thumb_index_middle_strong__higher_approach/000_center_nominal/final_stage3_egg_overview_mask_overlay.png
```

视觉检查结论：

- 初始图能清楚看到鸡蛋和虚拟相机定位。
- 最终 closeup 图中鸡蛋被手指明显遮挡，但仍能看到被夹起后的鸡蛋局部和最终 mask。
- overview 图提供整机远景，能看到手臂已经进入抬升姿态。

## 仍然存在的问题

虽然 selected candidate 是 10/10 成功，但仍有两个风险旗标：

1. `early_contact_in_approach`
   - 说明 approach 阶段仍然可能提前触碰鸡蛋。
   - 当前没有造成最终失败，但会影响动作干净程度。

2. `transient_slip_high`
   - 说明接触转换或 slow lift 中仍然有瞬时高滑移。
   - hold 阶段已经稳定，当前不等于保持失败。

这两个问题应该作为下一轮优化方向，而不是否定本轮 demo 成功。

## 如果成功

把 `thumb_index_middle_strong__higher_approach` 作为 Stage3.8B 当前成功 demo baseline。后续可以：

- 把 demo 给用户检查。
- 继续优化早接触和瞬时滑移。
- 尝试更纯的 `thumb + index`，但不要把它作为当前默认 baseline。
- 比较 Stage3.7D 全手温和抓取和 Stage3.8B 两指/三指捏持的优缺点。

## 如果失败

如果后续 demo 在别的 trial 失败，优先按失败类型处理：

- `hold_slip_score_high`：先增加 contact settle 或降低手指闭合强度。
- `vision_lift_too_small`：先检查最终视觉相机和真实抬升，不要只调视觉阈值。
- `true_lift_too_small`：调 approach z、thumb 角度和 active finger 闭合。
- `final_vision_failed_or_occluded`：优先换最终验收相机或增加多相机最终检查。
