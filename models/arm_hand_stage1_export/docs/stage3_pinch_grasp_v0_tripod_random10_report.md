# Stage3 Pinch Grasp V0 Eval Report

Generated: 2026-06-06T00:41:53

这是 MuJoCo-only 的虚拟摄像机 + 合成触觉/滑移实验，不使用现实摄像头或真实硬件。

目标是尽力实现 pinch-style grasp（捏持式抓取）：用拇指和少数手指把鸡蛋掐住、抬起并保持。

## Success Criteria

- 初始虚拟摄像机必须成功估计鸡蛋位置。
- 最终虚拟摄像机必须再次看到鸡蛋，并估计出足够抬升高度。
- MuJoCo 真值也记录为验证项，防止视觉估计误判。
- 触觉接触必须包含 thumb + index/middle 等主动手指区域。
- hold 阶段要维持足够的 pinch contact fraction、低滑移、低挤压和低穿透。

## Summary

- Status: **PASS**
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_vision_confirmed_pinch_lift_hold': 10}`
- Failure reasons: `{}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_slip_high': 10}`

## Candidate Summary

| candidate | success | vision lift mean | true lift mean | hold stable | hold pinch | purity | hold slip max | max slip max | failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tripod_support | 10/10 | 0.11776 | 0.10433 | 1.000 | 1.000 | 0.817 | 0.208 | 1.000 | `{}` |

## Episode Results

| ep | candidate | trial | status | vision lift | true lift | final cam | final conf | hold pinch | stable | hold slip | crush | pen | failure reasons |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | tripod_support | center_nominal | PASS | 0.10364 | 0.09943 | stage3_egg_closeup | 0.475 | 1.000 | 1.000 | 0.146 | 0.125 | 0.002494 | `[]` |
| 1 | tripod_support | left_low_nominal | PASS | 0.10238 | 0.10377 | stage3_egg_closeup | 0.588 | 1.000 | 1.000 | 0.141 | 0.073 | 0.001459 | `[]` |
| 2 | tripod_support | right_high_nominal | PASS | 0.10937 | 0.09842 | stage3_egg_closeup | 0.526 | 1.000 | 1.000 | 0.185 | 0.089 | 0.001778 | `[]` |
| 3 | tripod_support | left_high_zplus | PASS | 0.12983 | 0.10923 | stage3_egg_closeup | 0.419 | 1.000 | 1.000 | 0.154 | 0.130 | 0.002610 | `[]` |
| 4 | tripod_support | right_low_zminus | PASS | 0.11444 | 0.10195 | stage3_egg_closeup | 0.437 | 1.000 | 1.000 | 0.134 | 0.100 | 0.002004 | `[]` |
| 5 | tripod_support | front_small_lift | PASS | 0.09357 | 0.08500 | stage3_egg_closeup | 0.485 | 1.000 | 1.000 | 0.177 | 0.099 | 0.001985 | `[]` |
| 6 | tripod_support | back_large_lift | PASS | 0.13883 | 0.11876 | stage3_egg_closeup | 0.508 | 1.000 | 1.000 | 0.190 | 0.107 | 0.002148 | `[]` |
| 7 | tripod_support | lifted_center | PASS | 0.10951 | 0.10050 | stage3_egg_closeup | 0.566 | 1.000 | 1.000 | 0.175 | 0.112 | 0.002247 | `[]` |
| 8 | tripod_support | lifted_diag | PASS | 0.12790 | 0.11209 | stage3_egg_closeup | 0.674 | 1.000 | 1.000 | 0.203 | 0.111 | 0.002217 | `[]` |
| 9 | tripod_support | wide_diag | PASS | 0.14819 | 0.11414 | stage3_egg_closeup | 0.496 | 1.000 | 1.000 | 0.208 | 0.111 | 0.002210 | `[]` |

## Interpretation

- 如果某个 candidate 成功率为 0，但 vision lift 明显为正，说明可能是触觉 pinch 判据或 hold 稳定性不足。
- 如果 final vision 经常失败，说明捏持后遮挡太强，需要换最终验收相机或调整手指姿态。
- 如果 true lift 很低，说明抓法本身没有把鸡蛋带起来，下一轮应优先改接近姿态和 thumb/index 闭合目标。
