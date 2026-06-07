# Stage3.8B Pinch Grasp Training V0

Generated: 2026-06-06T09:56:04

这次训练仍然是 MuJoCo-only：使用虚拟摄像机定位/验收，使用合成触觉和滑移判断捏持质量，不使用现实摄像头或真实硬件。

这里的“训练”是参数搜索和课程式评估，不是神经网络训练。每个捏持方法先生成多个参数变体，经过训练筛选、家族验证和最终随机扰动验收后，再选择一个 demo-ready 抓法。

## Training Setup

- Families: `['thumb_index_light', 'thumb_index_middle', 'thumb_index_middle_strong', 'tripod_support']`
- Variants tested: `28`
- Train episodes: `56`
- Validation episodes: `12`
- Final episodes: `40`
- Selected candidate: `thumb_index_middle_strong__higher_approach`
- Demo command: `python .\simulations\models\arm_hand_stage1_export\demo_stage3_pinch_grasp_viewer.py --candidate-config .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_training_v0_selected.json`

## Train Ranking

| rank | candidate | family | score | success | true lift mean | hold pinch | purity | hold slip max | failures |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | tripod_support__higher_approach | tripod_support | 126.95 | 2/2 | 0.10359 | 1.000 | 0.804 | 0.179 | `{}` |
| 2 | tripod_support__firmer_close | tripod_support | 126.57 | 2/2 | 0.10107 | 1.000 | 0.814 | 0.191 | `{}` |
| 3 | tripod_support__base | tripod_support | 126.56 | 2/2 | 0.10074 | 1.000 | 0.812 | 0.188 | `{}` |
| 4 | thumb_index_middle_strong__higher_approach | thumb_index_middle_strong | 126.32 | 2/2 | 0.10091 | 1.000 | 0.791 | 0.202 | `{}` |
| 5 | tripod_support__gentler_close | tripod_support | 126.32 | 2/2 | 0.10005 | 1.000 | 0.790 | 0.195 | `{}` |
| 6 | thumb_index_middle__higher_approach | thumb_index_middle | 126.22 | 2/2 | 0.10199 | 1.000 | 0.776 | 0.222 | `{}` |
| 7 | thumb_index_middle__lift_plus | thumb_index_middle | 126.20 | 2/2 | 0.10356 | 1.000 | 0.827 | 0.264 | `{}` |
| 8 | tripod_support__lift_plus | tripod_support | 126.13 | 2/2 | 0.10541 | 1.000 | 0.812 | 0.287 | `{}` |
| 9 | tripod_support__lower_approach | tripod_support | 126.00 | 2/2 | 0.09755 | 1.000 | 0.826 | 0.211 | `{}` |
| 10 | thumb_index_middle__base | thumb_index_middle | 125.87 | 2/2 | 0.09989 | 1.000 | 0.774 | 0.231 | `{}` |
| 11 | thumb_index_middle_strong__lift_plus | thumb_index_middle_strong | 125.74 | 2/2 | 0.10278 | 1.000 | 0.719 | 0.250 | `{}` |
| 12 | thumb_index_middle_strong__firmer_close | thumb_index_middle_strong | 125.44 | 2/2 | 0.10031 | 1.000 | 0.715 | 0.256 | `{}` |
| 13 | thumb_index_middle_strong__base | thumb_index_middle_strong | 125.25 | 2/2 | 0.09947 | 1.000 | 0.707 | 0.261 | `{}` |
| 14 | thumb_index_middle__low_firm | thumb_index_middle | 125.21 | 2/2 | 0.09838 | 1.000 | 0.718 | 0.257 | `{}` |
| 15 | thumb_index_middle__lower_approach | thumb_index_middle | 125.13 | 2/2 | 0.09781 | 1.000 | 0.700 | 0.251 | `{}` |
| 16 | thumb_index_middle__gentler_close | thumb_index_middle | 125.12 | 2/2 | 0.09531 | 1.000 | 0.785 | 0.255 | `{}` |
| 17 | thumb_index_middle_strong__gentler_close | thumb_index_middle_strong | 124.90 | 2/2 | 0.09870 | 1.000 | 0.716 | 0.291 | `{}` |
| 18 | thumb_index_middle_strong__low_firm | thumb_index_middle_strong | 124.66 | 2/2 | 0.09780 | 1.000 | 0.661 | 0.277 | `{}` |

## Validation Ranking

| rank | candidate | family | score | success | true lift mean | hold pinch | purity | hold slip max | failures |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | tripod_support__higher_approach | tripod_support | 125.73 | 3/3 | 0.10232 | 1.000 | 0.827 | 0.295 | `{}` |
| 2 | thumb_index_middle_strong__higher_approach | thumb_index_middle_strong | 125.71 | 3/3 | 0.09998 | 1.000 | 0.797 | 0.258 | `{}` |
| 3 | thumb_index_middle__higher_approach | thumb_index_middle | 124.71 | 3/3 | 0.09888 | 1.000 | 0.768 | 0.333 | `{}` |
| 4 | thumb_index_light__higher_approach | thumb_index_light | 88.24 | 2/3 | 0.09310 | 1.000 | 0.643 | 0.356 | `{'hold_slip_score_high': 1}` |

## Final Ranking

| rank | candidate | family | score | success | true lift mean | hold pinch | purity | hold slip max | failures |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | thumb_index_middle_strong__higher_approach | thumb_index_middle_strong | 125.78 | 10/10 | 0.10347 | 1.000 | 0.779 | 0.276 | `{}` |
| 2 | tripod_support__higher_approach | tripod_support | 114.76 | 9/10 | 0.10736 | 1.000 | 0.804 | 0.393 | `{'hold_slip_score_high': 1}` |
| 3 | thumb_index_middle__higher_approach | thumb_index_middle | 114.64 | 9/10 | 0.10470 | 1.000 | 0.763 | 0.357 | `{'hold_slip_score_high': 1}` |
| 4 | thumb_index_light__higher_approach | thumb_index_light | 67.34 | 6/10 | 0.07889 | 0.874 | 0.552 | 1.000 | `{'vision_lift_too_small': 1, 'true_lift_too_small': 2, 'hold_slip_score_high': 3, 'egg_still_touching_floor': 2, 'final_vision_failed_or_occluded': 1, 'pinch_not_maintained_in_hold': 1, 'hold_tactile_unstable': 1}` |

## Final Selected Result

- Candidate: `thumb_index_middle_strong__higher_approach`
- Success: `10 / 10`
- Mean true lift: `0.10347 m`
- Mean vision lift: `0.11433 m`
- Hold stable fraction mean: `1.000`
- Hold pinch fraction mean: `1.000`
- Hold pinch purity mean: `0.779`
- Max hold slip: `0.276`
- Max crush risk: `0.143`
- Max penetration: `0.002866 m`
- Failure reasons: `{}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_slip_high': 10}`

## Interpretation

- 如果 final success 是满分，当前 selected candidate 可以作为 Stage3.8B 成功 demo 的默认抓法。
- 如果某些纯二指/二三指方法没通过，它们不会被删除，会保留为失败证据和下一轮修复对象。
- 即使最终成功，`early_contact_in_approach` 或 `transient_slip_high` 仍然是后续优化方向；它们不等于 hold 失败。

## 如果成功

- 使用 demo 命令打开 MuJoCo，展示虚拟视觉、触觉区域、捏持区域和成功抬升。
- 把 selected candidate 作为 Stage3.8B 当前捏持 demo baseline。
- 下一轮可继续修早接触和瞬时滑移，或者挑战更纯的 thumb/index/middle 捏持。

## 如果失败

- 先看 failure_reason_counts：视觉失败、真实抬升失败、触觉捏持失败、hold slip 失败要分开修。
- 如果只有 final vision 失败而真值/触觉成功，优先修验收相机，不先改抓法。
- 如果 true lift 失败，优先修 approach_z_bias_delta、thumb 角度和 active finger 闭合角度。
