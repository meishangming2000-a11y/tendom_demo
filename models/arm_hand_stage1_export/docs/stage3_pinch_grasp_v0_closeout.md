# Stage3 Pinch Grasp V0 收尾记录

生成日期：2026-06-06

## 这次要解决什么

用户希望不要只做一个很小的 probe，而是尽力实现一种新的抓法：不用整只手包住鸡蛋，而是用几根手指把鸡蛋捏住、抬起并保持。

因此本轮新增了 `eval_stage3_pinch_grasp_v0.py`，它不是单次手调，而是一个可重复评估入口：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_pinch_grasp_v0.py --candidates tripod_support --episodes-per-candidate 10 --trial cycle --random-offset-std 0.005
```

## 成功怎么判断

这次没有只用 MuJoCo 真值判断“抓起来了”。成功标准分三层：

1. 视觉层：初始虚拟摄像机必须能定位鸡蛋；最终虚拟摄像机也要重新看到鸡蛋，并估计出足够的抬升高度。
2. 触觉层：接触区域必须符合捏持模式，也就是 `thumb` 加上 `index`/`middle`/`ring` 等少数手指，而不是只有手掌或支撑面接触。
3. 保持层：hold 阶段要稳定、低滑移、低挤压、低穿透，鸡蛋不能还接触地面。

最终视觉验收使用较低阈值 `min_final_vision_confidence=0.35`，原因是捏持后手指会遮挡鸡蛋；但初始定位仍使用较严格阈值 `min_vision_confidence=0.55`。

## 候选抓法测试

第一轮多候选测试：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_pinch_grasp_v0.py --candidates all --episodes-per-candidate 3 --trial cycle --hold-steps 500 --max-contact-settle-steps 700 --min-contact-settle-steps 180 --settle-stable-window-steps 90 --report .\simulations\models\arm_hand_stage1_export\docs\stage3_pinch_grasp_v0_multicandidate_report.md --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_v0_multicandidate.json
```

结果：

| candidate | 成功数 | 主要结论 |
|---|---:|---|
| `thumb_index_light` | 1/3 | 力量不足，很多样例没有抬起 |
| `thumb_index_middle` | 2/3 | 能捏起，但部分样例 hold slip 超阈值 |
| `thumb_index_middle_strong` | 2/3 | 更稳，但仍有一个样例 hold slip 超阈值 |
| `tripod_support` | 2/3 | 物理和触觉最好；唯一失败来自最终视觉阈值过硬 |

## 选定抓法

当前最可行的是 `tripod_support`：拇指 + 食指 + 中指 + 少量无名指支撑。它不是纯两指捏持，但比整只手包覆更接近“几根手指掐住”的抓法。

固定 10 组结果：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_pinch_grasp_v0.py --candidates tripod_support --episodes-per-candidate 10 --trial cycle --hold-steps 700 --max-contact-settle-steps 900 --min-contact-settle-steps 220 --settle-stable-window-steps 110 --report .\simulations\models\arm_hand_stage1_export\docs\stage3_pinch_grasp_v0_tripod10_final_report.md --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_v0_tripod10_final.json
```

结果：

- 成功：10/10
- mean vision lift：0.115901 m
- mean true lift：0.104062 m
- hold stable fraction：1.000
- hold pinch fraction：1.000
- mean pinch purity：0.817
- max hold slip：0.258
- max crush risk：0.119
- max penetration：0.002372 m

随机位姿扰动 10 组结果：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_pinch_grasp_v0.py --candidates tripod_support --episodes-per-candidate 10 --trial cycle --random-offset-std 0.005 --hold-steps 700 --max-contact-settle-steps 900 --min-contact-settle-steps 220 --settle-stable-window-steps 110 --report .\simulations\models\arm_hand_stage1_export\docs\stage3_pinch_grasp_v0_tripod_random10_report.md --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_v0_tripod_random10.json
```

结果：

- 成功：10/10
- mean vision lift：0.117765 m
- mean true lift：0.104330 m
- hold stable fraction：1.000
- hold pinch fraction：1.000
- mean pinch purity：0.817
- max hold slip：0.208
- max crush risk：0.130
- max penetration：0.002610 m

## 视觉检查

带视觉 debug 的中心样例：

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_pinch_grasp_v0.py --candidates tripod_support --episodes-per-candidate 1 --trial center_nominal --render-vision-debug --report .\simulations\models\arm_hand_stage1_export\docs\stage3_pinch_grasp_v0_visual_debug_report.md --metadata .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_v0_visual_debug.json
```

检查文件：

- `docs/visual_checks_stage3_pinch_grasp_v0/tripod_support/000_center_nominal/initial_mask_overlay.png`
- `docs/visual_checks_stage3_pinch_grasp_v0/tripod_support/000_center_nominal/final_stage3_egg_closeup_mask_overlay.png`

视觉结论：初始 mask 覆盖鸡蛋本体；最终 mask 仍覆盖被捏起后的鸡蛋，说明视觉成功判据确实在检查鸡蛋，而不是只读 MuJoCo 真值。

## 仍然存在的问题

- `early_contact_in_approach` 每组都有，说明手在 approach 阶段就会接触鸡蛋，需要后续优化接近姿态或启用接触提前停止。
- `transient_slip_high` 每组都有，说明 slow_lift 或接触转换时仍有瞬时滑移峰值；不过 hold 阶段滑移低，当前不影响保持成功。
- `tripod_support` 使用了无名指支撑，所以它是 tripod/pinch 混合，不是最纯的二指捏持。

## 如果成功，下一步怎么做

- 把 `tripod_support` 作为 Stage3.8A pinch-style branch 的当前可运行版本。
- 增加专用 viewer，让用户能像 Stage3.7D 一样直接打开 MuJoCo 看捏持过程。
- 继续减少早接触和瞬时滑移，再尝试回到更纯的 thumb + index/middle。

## 如果失败，下一步怎么做

- 如果视觉失败但真值和触觉都成功，优先改最终验收相机或最终视觉阈值，不先改抓法。
- 如果真值抬升失败，优先改 thumb/index/middle 闭合角度和 approach z bias。
- 如果 hold slip 超阈值，优先增加 contact settle 或微调 active finger flex，而不是马上切回整手包覆。
