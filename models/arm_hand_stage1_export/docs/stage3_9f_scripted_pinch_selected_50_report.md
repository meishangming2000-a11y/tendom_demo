# Stage3 Pinch Grasp V0 Eval Report

Generated: 2026-06-07T12:23:18

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
- Episodes: `50`
- Success count: `38 / 50`
- Terminal reasons: `{'hold_slip_score_high': 2, 'success_vision_confirmed_pinch_lift_hold': 38, 'vision_lift_too_small': 9, 'final_vision_failed_or_occluded': 1}`
- Failure reasons: `{'hold_slip_score_high': 12, 'vision_lift_too_small': 9, 'true_lift_too_small': 10, 'egg_still_touching_floor': 9, 'pinch_not_maintained_in_hold': 3, 'hold_tactile_unstable': 3, 'final_vision_failed_or_occluded': 1}`
- Risk flags: `{'early_contact_in_approach': 50, 'transient_slip_high': 48, 'low_pinch_purity': 7, 'final_vision_occluded_or_low_confidence': 1}`

## Candidate Summary

| candidate | success | vision lift mean | true lift mean | hold stable | hold pinch | purity | hold slip max | max slip max | failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| thumb_index_middle_strong__higher_approach | 38/50 | 0.09306 | 0.08178 | 0.921 | 0.933 | 0.703 | 1.000 | 1.000 | `{'hold_slip_score_high': 12, 'vision_lift_too_small': 9, 'true_lift_too_small': 10, 'egg_still_touching_floor': 9, 'pinch_not_maintained_in_hold': 3, 'hold_tactile_unstable': 3, 'final_vision_failed_or_occluded': 1}` |

## Episode Results

| ep | candidate | trial | status | vision lift | true lift | final cam | final conf | hold pinch | stable | hold slip | crush | pen | failure reasons |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | thumb_index_middle_strong__higher_approach | center_nominal | FAIL | 0.10516 | 0.09922 | stage3_egg_closeup | 0.676 | 1.000 | 0.919 | 0.437 | 0.113 | 0.002261 | `['hold_slip_score_high']` |
| 1 | thumb_index_middle_strong__higher_approach | left_low_nominal | PASS | 0.10347 | 0.10407 | stage3_egg_closeup | 0.602 | 1.000 | 1.000 | 0.125 | 0.118 | 0.002369 | `[]` |
| 2 | thumb_index_middle_strong__higher_approach | right_high_nominal | FAIL | 0.00179 | -0.00086 | stage3_egg_closeup | 0.484 | 0.792 | 0.778 | 1.000 | 0.126 | 0.002519 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 3 | thumb_index_middle_strong__higher_approach | left_high_zplus | PASS | 0.11386 | 0.10739 | stage3_egg_closeup | 0.753 | 1.000 | 1.000 | 0.212 | 0.106 | 0.002110 | `[]` |
| 4 | thumb_index_middle_strong__higher_approach | right_low_zminus | FAIL | -0.00152 | -0.00788 | stage3_egg_closeup | 0.418 | 0.371 | 0.356 | 1.000 | 0.187 | 0.003730 | `['vision_lift_too_small', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 5 | thumb_index_middle_strong__higher_approach | front_small_lift | PASS | 0.06851 | 0.07630 | stage3_egg_closeup | 0.522 | 1.000 | 1.000 | 0.247 | 0.113 | 0.002253 | `[]` |
| 6 | thumb_index_middle_strong__higher_approach | back_large_lift | FAIL | -0.00032 | -0.00268 | stage3_egg_closeup | 0.565 | 0.803 | 0.703 | 1.000 | 0.170 | 0.003395 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 7 | thumb_index_middle_strong__higher_approach | lifted_center | PASS | 0.13055 | 0.10101 | stage3_egg_closeup | 0.506 | 1.000 | 1.000 | 0.198 | 0.142 | 0.002841 | `[]` |
| 8 | thumb_index_middle_strong__higher_approach | lifted_diag | PASS | 0.15129 | 0.11161 | stage3_egg_closeup | 0.619 | 1.000 | 1.000 | 0.228 | 0.138 | 0.002753 | `[]` |
| 9 | thumb_index_middle_strong__higher_approach | wide_diag | PASS | 0.14858 | 0.11614 | stage3_egg_closeup | 0.586 | 1.000 | 1.000 | 0.168 | 0.135 | 0.002708 | `[]` |
| 10 | thumb_index_middle_strong__higher_approach | center_nominal | PASS | 0.10622 | 0.10159 | stage3_egg_closeup | 0.686 | 1.000 | 1.000 | 0.167 | 0.110 | 0.002206 | `[]` |
| 11 | thumb_index_middle_strong__higher_approach | left_low_nominal | PASS | 0.10457 | 0.10462 | stage3_egg_closeup | 0.627 | 1.000 | 1.000 | 0.115 | 0.100 | 0.001999 | `[]` |
| 12 | thumb_index_middle_strong__higher_approach | right_high_nominal | PASS | 0.09484 | 0.09200 | stage3_egg_closeup | 0.633 | 1.000 | 1.000 | 0.321 | 0.092 | 0.001844 | `[]` |
| 13 | thumb_index_middle_strong__higher_approach | left_high_zplus | PASS | 0.13201 | 0.11065 | stage3_egg_closeup | 0.486 | 1.000 | 1.000 | 0.162 | 0.158 | 0.003151 | `[]` |
| 14 | thumb_index_middle_strong__higher_approach | right_low_zminus | FAIL | -0.00730 | -0.00233 | stage3_egg_overview | 0.682 | 0.423 | 0.342 | 1.000 | 0.155 | 0.003092 | `['vision_lift_too_small', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 15 | thumb_index_middle_strong__higher_approach | front_small_lift | PASS | 0.09407 | 0.08992 | stage3_egg_closeup | 0.463 | 1.000 | 1.000 | 0.117 | 0.135 | 0.002699 | `[]` |
| 16 | thumb_index_middle_strong__higher_approach | back_large_lift | FAIL | -0.00830 | -0.00554 | stage3_egg_closeup | 0.582 | 0.714 | 0.614 | 1.000 | 0.149 | 0.002988 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high']` |
| 17 | thumb_index_middle_strong__higher_approach | lifted_center | PASS | 0.12559 | 0.09928 | stage3_egg_closeup | 0.511 | 1.000 | 1.000 | 0.220 | 0.119 | 0.002374 | `[]` |
| 18 | thumb_index_middle_strong__higher_approach | lifted_diag | PASS | 0.09997 | 0.10283 | stage3_egg_closeup | 0.626 | 1.000 | 1.000 | 0.262 | 0.098 | 0.001957 | `[]` |
| 19 | thumb_index_middle_strong__higher_approach | wide_diag | PASS | 0.15384 | 0.11631 | stage3_egg_closeup | 0.601 | 1.000 | 1.000 | 0.273 | 0.124 | 0.002478 | `[]` |
| 20 | thumb_index_middle_strong__higher_approach | center_nominal | PASS | 0.10677 | 0.10190 | stage3_egg_closeup | 0.751 | 1.000 | 1.000 | 0.164 | 0.111 | 0.002227 | `[]` |
| 21 | thumb_index_middle_strong__higher_approach | left_low_nominal | PASS | 0.10468 | 0.10424 | stage3_egg_closeup | 0.613 | 1.000 | 1.000 | 0.123 | 0.104 | 0.002080 | `[]` |
| 22 | thumb_index_middle_strong__higher_approach | right_high_nominal | FAIL | 0.07559 | 0.07053 | stage3_egg_closeup | 0.779 | 0.963 | 0.949 | 1.000 | 0.092 | 0.001838 | `['hold_slip_score_high']` |
| 23 | thumb_index_middle_strong__higher_approach | left_high_zplus | PASS | 0.11861 | 0.11167 | stage3_egg_closeup | 0.540 | 1.000 | 1.000 | 0.181 | 0.139 | 0.002782 | `[]` |
| 24 | thumb_index_middle_strong__higher_approach | right_low_zminus | FAIL | nan | -0.00723 | stage3_egg_closeup | 0.318 | 0.750 | 0.717 | 1.000 | 0.162 | 0.003247 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 25 | thumb_index_middle_strong__higher_approach | front_small_lift | PASS | 0.07098 | 0.08277 | stage3_egg_closeup | 0.477 | 1.000 | 1.000 | 0.175 | 0.125 | 0.002495 | `[]` |
| 26 | thumb_index_middle_strong__higher_approach | back_large_lift | PASS | 0.13088 | 0.12167 | stage3_egg_closeup | 0.710 | 1.000 | 1.000 | 0.191 | 0.112 | 0.002242 | `[]` |
| 27 | thumb_index_middle_strong__higher_approach | lifted_center | PASS | 0.12705 | 0.10252 | stage3_egg_closeup | 0.590 | 1.000 | 1.000 | 0.202 | 0.135 | 0.002696 | `[]` |
| 28 | thumb_index_middle_strong__higher_approach | lifted_diag | PASS | 0.14107 | 0.11242 | stage3_egg_closeup | 0.686 | 1.000 | 1.000 | 0.215 | 0.130 | 0.002600 | `[]` |
| 29 | thumb_index_middle_strong__higher_approach | wide_diag | PASS | 0.13797 | 0.11488 | stage3_egg_closeup | 0.650 | 1.000 | 1.000 | 0.172 | 0.115 | 0.002298 | `[]` |
| 30 | thumb_index_middle_strong__higher_approach | center_nominal | PASS | 0.11105 | 0.09953 | stage3_egg_closeup | 0.715 | 1.000 | 1.000 | 0.168 | 0.136 | 0.002720 | `[]` |
| 31 | thumb_index_middle_strong__higher_approach | left_low_nominal | PASS | 0.10126 | 0.10499 | stage3_egg_closeup | 0.508 | 1.000 | 1.000 | 0.108 | 0.117 | 0.002330 | `[]` |
| 32 | thumb_index_middle_strong__higher_approach | right_high_nominal | FAIL | -0.01166 | -0.00520 | stage3_egg_closeup | 0.559 | 0.891 | 0.872 | 1.000 | 0.123 | 0.002462 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 33 | thumb_index_middle_strong__higher_approach | left_high_zplus | PASS | 0.12575 | 0.10930 | stage3_egg_closeup | 0.704 | 1.000 | 1.000 | 0.275 | 0.113 | 0.002269 | `[]` |
| 34 | thumb_index_middle_strong__higher_approach | right_low_zminus | FAIL | -0.00590 | -0.00605 | stage3_egg_closeup | 0.485 | 0.437 | 0.341 | 1.000 | 0.166 | 0.003322 | `['vision_lift_too_small', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 35 | thumb_index_middle_strong__higher_approach | front_small_lift | PASS | 0.09150 | 0.08865 | stage3_egg_closeup | 0.721 | 1.000 | 1.000 | 0.161 | 0.105 | 0.002101 | `[]` |
| 36 | thumb_index_middle_strong__higher_approach | back_large_lift | FAIL | -0.04211 | -0.01114 | stage3_egg_overview | 0.431 | 0.654 | 0.632 | 1.000 | 0.180 | 0.003609 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 37 | thumb_index_middle_strong__higher_approach | lifted_center | PASS | 0.11897 | 0.10180 | stage3_egg_closeup | 0.561 | 1.000 | 1.000 | 0.182 | 0.132 | 0.002633 | `[]` |
| 38 | thumb_index_middle_strong__higher_approach | lifted_diag | PASS | 0.14345 | 0.11356 | stage3_egg_closeup | 0.691 | 1.000 | 1.000 | 0.188 | 0.124 | 0.002484 | `[]` |
| 39 | thumb_index_middle_strong__higher_approach | wide_diag | PASS | 0.13900 | 0.11540 | stage3_egg_closeup | 0.626 | 1.000 | 1.000 | 0.151 | 0.119 | 0.002373 | `[]` |
| 40 | thumb_index_middle_strong__higher_approach | center_nominal | PASS | 0.10527 | 0.09936 | stage3_egg_closeup | 0.722 | 1.000 | 1.000 | 0.217 | 0.105 | 0.002105 | `[]` |
| 41 | thumb_index_middle_strong__higher_approach | left_low_nominal | PASS | 0.10460 | 0.10460 | stage3_egg_closeup | 0.615 | 1.000 | 1.000 | 0.114 | 0.099 | 0.001977 | `[]` |
| 42 | thumb_index_middle_strong__higher_approach | right_high_nominal | FAIL | 0.00013 | -0.00338 | stage3_egg_closeup | 0.608 | 0.831 | 0.816 | 1.000 | 0.147 | 0.002944 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 43 | thumb_index_middle_strong__higher_approach | left_high_zplus | PASS | 0.12627 | 0.10990 | stage3_egg_closeup | 0.453 | 1.000 | 1.000 | 0.153 | 0.145 | 0.002900 | `[]` |
| 44 | thumb_index_middle_strong__higher_approach | right_low_zminus | PASS | 0.10634 | 0.10158 | stage3_egg_closeup | 0.716 | 1.000 | 1.000 | 0.206 | 0.105 | 0.002104 | `[]` |
| 45 | thumb_index_middle_strong__higher_approach | front_small_lift | PASS | 0.09116 | 0.08850 | stage3_egg_closeup | 0.708 | 1.000 | 1.000 | 0.163 | 0.104 | 0.002085 | `[]` |
| 46 | thumb_index_middle_strong__higher_approach | back_large_lift | PASS | 0.13553 | 0.12190 | stage3_egg_closeup | 0.676 | 1.000 | 1.000 | 0.179 | 0.120 | 0.002403 | `[]` |
| 47 | thumb_index_middle_strong__higher_approach | lifted_center | PASS | 0.11224 | 0.10060 | stage3_egg_closeup | 0.561 | 1.000 | 1.000 | 0.173 | 0.126 | 0.002523 | `[]` |
| 48 | thumb_index_middle_strong__higher_approach | lifted_diag | PASS | 0.14302 | 0.11250 | stage3_egg_closeup | 0.681 | 1.000 | 1.000 | 0.206 | 0.129 | 0.002587 | `[]` |
| 49 | thumb_index_middle_strong__higher_approach | wide_diag | PASS | 0.13350 | 0.11352 | stage3_egg_closeup | 0.592 | 1.000 | 1.000 | 0.174 | 0.147 | 0.002931 | `[]` |

## Interpretation

- 如果某个 candidate 成功率为 0，但 vision lift 明显为正，说明可能是触觉 pinch 判据或 hold 稳定性不足。
- 如果 final vision 经常失败，说明捏持后遮挡太强，需要换最终验收相机或调整手指姿态。
- 如果 true lift 很低，说明抓法本身没有把鸡蛋带起来，下一轮应优先改接近姿态和 thumb/index 闭合目标。
