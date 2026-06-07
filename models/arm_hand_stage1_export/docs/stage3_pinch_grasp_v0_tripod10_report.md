# Stage3 Pinch Grasp V0 Eval Report

Generated: 2026-06-06T00:39:55

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
- Episodes: `10`
- Success count: `9 / 10`
- Terminal reasons: `{'success_vision_confirmed_pinch_lift_hold': 9, 'final_vision_failed_or_occluded': 1}`
- Failure reasons: `{'final_vision_failed_or_occluded': 1}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_slip_high': 10, 'final_vision_occluded_or_low_confidence': 1}`

## Candidate Summary

| candidate | success | vision lift mean | true lift mean | hold stable | hold pinch | purity | hold slip max | max slip max | failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tripod_support | 9/10 | 0.11615 | 0.10406 | 1.000 | 1.000 | 0.817 | 0.258 | 1.000 | `{'final_vision_failed_or_occluded': 1}` |

## Episode Results

| ep | candidate | trial | status | vision lift | true lift | final cam | final conf | hold pinch | stable | hold slip | crush | pen | failure reasons |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | tripod_support | center_nominal | PASS | 0.11245 | 0.09969 | stage3_egg_closeup | 0.458 | 1.000 | 1.000 | 0.130 | 0.108 | 0.002158 | `[]` |
| 1 | tripod_support | left_low_nominal | PASS | 0.09934 | 0.10302 | stage3_egg_closeup | 0.521 | 1.000 | 1.000 | 0.258 | 0.081 | 0.001629 | `[]` |
| 2 | tripod_support | right_high_nominal | PASS | 0.10953 | 0.09858 | stage3_egg_closeup | 0.565 | 1.000 | 1.000 | 0.181 | 0.090 | 0.001797 | `[]` |
| 3 | tripod_support | left_high_zplus | PASS | 0.12975 | 0.10897 | stage3_egg_closeup | 0.464 | 1.000 | 1.000 | 0.158 | 0.112 | 0.002234 | `[]` |
| 4 | tripod_support | right_low_zminus | FAIL | nan | 0.10251 | stage3_egg_closeup | 0.392 | 1.000 | 1.000 | 0.169 | 0.096 | 0.001917 | `['final_vision_failed_or_occluded']` |
| 5 | tripod_support | front_small_lift | PASS | 0.09341 | 0.08655 | stage3_egg_closeup | 0.479 | 1.000 | 1.000 | 0.134 | 0.100 | 0.001995 | `[]` |
| 6 | tripod_support | back_large_lift | PASS | 0.13557 | 0.11777 | stage3_egg_closeup | 0.517 | 1.000 | 1.000 | 0.154 | 0.119 | 0.002372 | `[]` |
| 7 | tripod_support | lifted_center | PASS | 0.10775 | 0.09988 | stage3_egg_closeup | 0.583 | 1.000 | 1.000 | 0.177 | 0.108 | 0.002159 | `[]` |
| 8 | tripod_support | lifted_diag | PASS | 0.12277 | 0.11109 | stage3_egg_closeup | 0.675 | 1.000 | 1.000 | 0.191 | 0.114 | 0.002272 | `[]` |
| 9 | tripod_support | wide_diag | PASS | 0.13481 | 0.11258 | stage3_egg_closeup | 0.568 | 1.000 | 1.000 | 0.164 | 0.118 | 0.002359 | `[]` |

## Interpretation

- 如果某个 candidate 成功率为 0，但 vision lift 明显为正，说明可能是触觉 pinch 判据或 hold 稳定性不足。
- 如果 final vision 经常失败，说明捏持后遮挡太强，需要换最终验收相机或调整手指姿态。
- 如果 true lift 很低，说明抓法本身没有把鸡蛋带起来，下一轮应优先改接近姿态和 thumb/index 闭合目标。
