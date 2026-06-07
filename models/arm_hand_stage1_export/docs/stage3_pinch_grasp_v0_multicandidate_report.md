# Stage3 Pinch Grasp V0 Eval Report

Generated: 2026-06-06T00:38:25

这是 MuJoCo-only 的虚拟摄像机 + 合成触觉/滑移实验，不使用现实摄像头或真实硬件。

目标是尽力实现 pinch-style grasp（捏持式抓取）：用拇指和少数手指把鸡蛋掐住、抬起并保持。

## Success Criteria

- 初始虚拟摄像机必须成功估计鸡蛋位置。
- 最终虚拟摄像机必须再次看到鸡蛋，并估计出足够抬升高度。
- MuJoCo 真值也记录为验证项，防止视觉估计误判。
- 触觉接触必须包含 thumb + index/middle 等主动手指区域。
- hold 阶段要维持足够的 pinch contact fraction、低滑移、低挤压和低穿透。

## Summary

- Status: **PARTIAL**
- Episodes: `12`
- Success count: `7 / 12`
- Terminal reasons: `{'vision_lift_too_small': 2, 'success_vision_confirmed_pinch_lift_hold': 7, 'hold_slip_score_high': 2, 'final_vision_failed_or_occluded': 1}`
- Failure reasons: `{'vision_lift_too_small': 2, 'true_lift_too_small': 2, 'pinch_not_maintained_in_hold': 2, 'hold_tactile_unstable': 2, 'egg_still_touching_floor': 2, 'hold_slip_score_high': 2, 'final_vision_failed_or_occluded': 1}`
- Risk flags: `{'early_contact_in_approach': 12, 'transient_slip_high': 12, 'low_pinch_purity': 2, 'final_vision_occluded_or_low_confidence': 1}`

## Candidate Summary

| candidate | success | vision lift mean | true lift mean | hold stable | hold pinch | purity | hold slip max | max slip max | failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| thumb_index_light | 1/3 | 0.01891 | 0.02790 | 0.333 | 0.333 | 0.222 | 0.258 | 1.000 | `{'vision_lift_too_small': 2, 'true_lift_too_small': 2, 'pinch_not_maintained_in_hold': 2, 'hold_tactile_unstable': 2, 'egg_still_touching_floor': 2}` |
| thumb_index_middle | 2/3 | 0.08624 | 0.08493 | 0.950 | 0.963 | 0.747 | 1.000 | 1.000 | `{'hold_slip_score_high': 1}` |
| thumb_index_middle_strong | 2/3 | 0.09289 | 0.09444 | 0.997 | 1.000 | 0.780 | 0.556 | 1.000 | `{'hold_slip_score_high': 1}` |
| tripod_support | 2/3 | 0.10456 | 0.10024 | 1.000 | 1.000 | 0.827 | 0.258 | 1.000 | `{'final_vision_failed_or_occluded': 1}` |

## Episode Results

| ep | candidate | trial | status | vision lift | true lift | final cam | final conf | hold pinch | stable | hold slip | crush | pen | failure reasons |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | thumb_index_light | center_nominal | FAIL | -0.02596 | -0.00772 | stage3_egg_overview | 0.481 | 0.000 | 0.000 | 0.000 | 0.108 | 0.002151 | `['vision_lift_too_small', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 1 | thumb_index_light | left_low_nominal | PASS | 0.10453 | 0.10277 | stage3_egg_closeup | 0.530 | 1.000 | 1.000 | 0.258 | 0.056 | 0.001128 | `[]` |
| 2 | thumb_index_light | right_high_nominal | FAIL | -0.02185 | -0.01136 | stage3_egg_closeup | 0.483 | 0.000 | 0.000 | 0.000 | 0.127 | 0.002537 | `['vision_lift_too_small', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 3 | thumb_index_middle | center_nominal | FAIL | 0.06301 | 0.05944 | stage3_egg_closeup | 0.751 | 0.890 | 0.850 | 1.000 | 0.086 | 0.001723 | `['hold_slip_score_high']` |
| 4 | thumb_index_middle | left_low_nominal | PASS | 0.09917 | 0.10224 | stage3_egg_closeup | 0.529 | 1.000 | 1.000 | 0.262 | 0.069 | 0.001381 | `[]` |
| 5 | thumb_index_middle | right_high_nominal | PASS | 0.09654 | 0.09309 | stage3_egg_closeup | 0.781 | 1.000 | 1.000 | 0.228 | 0.062 | 0.001244 | `[]` |
| 6 | thumb_index_middle_strong | center_nominal | PASS | 0.08506 | 0.09264 | stage3_egg_closeup | 0.557 | 1.000 | 1.000 | 0.243 | 0.143 | 0.002867 | `[]` |
| 7 | thumb_index_middle_strong | left_low_nominal | PASS | 0.10070 | 0.10164 | stage3_egg_closeup | 0.620 | 1.000 | 1.000 | 0.109 | 0.098 | 0.001956 | `[]` |
| 8 | thumb_index_middle_strong | right_high_nominal | FAIL | 0.09290 | 0.08905 | stage3_egg_closeup | 0.585 | 1.000 | 0.992 | 0.556 | 0.084 | 0.001684 | `['hold_slip_score_high']` |
| 9 | tripod_support | center_nominal | FAIL | nan | 0.09936 | stage3_egg_closeup | 0.447 | 1.000 | 1.000 | 0.129 | 0.108 | 0.002158 | `['final_vision_failed_or_occluded']` |
| 10 | tripod_support | left_low_nominal | PASS | 0.09916 | 0.10294 | stage3_egg_closeup | 0.519 | 1.000 | 1.000 | 0.258 | 0.081 | 0.001629 | `[]` |
| 11 | tripod_support | right_high_nominal | PASS | 0.10997 | 0.09844 | stage3_egg_closeup | 0.547 | 1.000 | 1.000 | 0.180 | 0.090 | 0.001797 | `[]` |

## Interpretation

- 如果某个 candidate 成功率为 0，但 vision lift 明显为正，说明可能是触觉 pinch 判据或 hold 稳定性不足。
- 如果 final vision 经常失败，说明捏持后遮挡太强，需要换最终验收相机或调整手指姿态。
- 如果 true lift 很低，说明抓法本身没有把鸡蛋带起来，下一轮应优先改接近姿态和 thumb/index 闭合目标。
