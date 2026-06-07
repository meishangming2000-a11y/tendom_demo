# Stage3 Pinch Grasp V0 Eval Report

Generated: 2026-06-06T00:42:38

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
- Episodes: `1`
- Success count: `1 / 1`
- Terminal reasons: `{'success_vision_confirmed_pinch_lift_hold': 1}`
- Failure reasons: `{}`
- Risk flags: `{'early_contact_in_approach': 1, 'transient_slip_high': 1}`

## Candidate Summary

| candidate | success | vision lift mean | true lift mean | hold stable | hold pinch | purity | hold slip max | max slip max | failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tripod_support | 1/1 | 0.11245 | 0.09969 | 1.000 | 1.000 | 0.868 | 0.130 | 1.000 | `{}` |

## Episode Results

| ep | candidate | trial | status | vision lift | true lift | final cam | final conf | hold pinch | stable | hold slip | crush | pen | failure reasons |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | tripod_support | center_nominal | PASS | 0.11245 | 0.09969 | stage3_egg_closeup | 0.458 | 1.000 | 1.000 | 0.130 | 0.108 | 0.002158 | `[]` |

## Interpretation

- 如果某个 candidate 成功率为 0，但 vision lift 明显为正，说明可能是触觉 pinch 判据或 hold 稳定性不足。
- 如果 final vision 经常失败，说明捏持后遮挡太强，需要换最终验收相机或调整手指姿态。
- 如果 true lift 很低，说明抓法本身没有把鸡蛋带起来，下一轮应优先改接近姿态和 thumb/index 闭合目标。
