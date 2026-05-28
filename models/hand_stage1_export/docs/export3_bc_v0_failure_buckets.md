# Export3 BC v0 Failure Buckets

Status: diagnostic pinned-wrap failure analysis, not a promoted stable_grasp baseline.

- Eval metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_bc_pinned_wrap_v0_eval_all75.json`
- Episodes: 75
- Pass: 63
- Partial/fail: 12
- Pass rate: 0.840

## Partial Episodes

| Episode | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball | Thumb-index |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 11 | `[0.000, -0.100, 0.210]` | 1.15 | 1 | 4 | 0.022898 | 0.033600 | 0.087062 | 0.075320 |
| 12 | `[0.000, -0.100, 0.210]` | 1.15 | 2 | 5 | 0.023205 | 0.033239 | 0.090739 | 0.079094 |
| 13 | `[0.000, -0.100, 0.210]` | 1.15 | 3 | 3 | 0.023180 | 0.033736 | 0.087373 | 0.080597 |
| 14 | `[0.000, -0.100, 0.210]` | 1.15 | 4 | 4 | 0.023090 | 0.032120 | 0.093214 | 0.082020 |
| 15 | `[0.000, -0.100, 0.210]` | 1.15 | 5 | 3 | 0.019431 | 0.034388 | 0.096934 | 0.084650 |
| 17 | `[0.000, -0.100, 0.195]` | 0.85 | 2 | 1 | 0.003433 | 0.037333 | 0.097184 | 0.080785 |
| 19 | `[0.000, -0.100, 0.195]` | 0.85 | 4 | 2 | 0.003573 | 0.036838 | 0.100278 | 0.085105 |
| 20 | `[0.000, -0.100, 0.195]` | 0.85 | 5 | 1 | 0.000987 | 0.040538 | 0.100270 | 0.078302 |
| 23 | `[0.000, -0.100, 0.195]` | 1.00 | 3 | 3 | 0.005226 | 0.033601 | 0.100300 | 0.092514 |
| 25 | `[0.000, -0.100, 0.195]` | 1.00 | 5 | 4 | 0.004524 | 0.034762 | 0.103784 | 0.089792 |
| 30 | `[0.000, -0.100, 0.195]` | 1.15 | 5 | 4 | 0.002141 | 0.036543 | 0.101687 | 0.088318 |
| 40 | `[0.010, -0.100, 0.210]` | 1.00 | 5 | 4 | 0.001620 | 0.036966 | 0.105401 | 0.094883 |

## By Ball Position

| Bucket | Total | Partial | Partial rate | Mean contacts | Mean penetration | Mean four-tip | Mean thumb-ball |
|---|---:|---:|---:|---:|---:|---:|---:|
| `[-0.010, -0.100, 0.210]` | 15 | 0 | 0.000 | 2.87 | 0.011155 | 0.036323 | 0.089508 |
| `[0.000, -0.090, 0.210]` | 15 | 0 | 0.000 | 4.00 | 0.004675 | 0.039107 | 0.082328 |
| `[0.000, -0.100, 0.195]` | 15 | 6 | 0.400 | 2.80 | 0.003511 | 0.036017 | 0.097810 |
| `[0.000, -0.100, 0.210]` | 15 | 5 | 0.333 | 3.33 | 0.012399 | 0.034301 | 0.090719 |
| `[0.010, -0.100, 0.210]` | 15 | 1 | 0.067 | 3.40 | 0.004832 | 0.035739 | 0.094619 |

## By Finger Scale

| Bucket | Total | Partial | Partial rate | Mean contacts | Mean penetration | Mean four-tip | Mean thumb-ball |
|---|---:|---:|---:|---:|---:|---:|---:|
| `0.85` | 25 | 3 | 0.120 | 2.88 | 0.005558 | 0.036235 | 0.091647 |
| `1.00` | 25 | 3 | 0.120 | 3.40 | 0.006786 | 0.035970 | 0.090892 |
| `1.15` | 25 | 6 | 0.240 | 3.56 | 0.009599 | 0.036688 | 0.090451 |

## By Thumb Rank

| Bucket | Total | Partial | Partial rate | Mean contacts | Mean penetration | Mean four-tip | Mean thumb-ball |
|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | 15 | 1 | 0.067 | 3.33 | 0.007370 | 0.036368 | 0.088515 |
| `2` | 15 | 2 | 0.133 | 3.33 | 0.007219 | 0.036284 | 0.090055 |
| `3` | 15 | 2 | 0.133 | 3.07 | 0.007534 | 0.036171 | 0.088417 |
| `4` | 15 | 2 | 0.133 | 3.40 | 0.007146 | 0.036204 | 0.093347 |
| `5` | 15 | 5 | 0.333 | 3.27 | 0.007303 | 0.036461 | 0.094648 |

## Takeaways

- BC v0 is still the best current diagnostic policy, but its failures are not uniformly distributed.
- The next dataset should target the highest partial-rate buckets instead of broad DAgger aggregation.
- Keep this analysis scoped to pinned-wrap; it does not prove free-object retention or gravity grasp.

## Recommended Next Collection

- Add scripted successful samples near `ball_position=[0.000, -0.100, 0.195]` (partial rate 0.400, partial 6/15).
- Add scripted successful samples near `ball_position=[0.000, -0.100, 0.210]` (partial rate 0.333, partial 5/15).
- Add scripted successful samples near `thumb_rank=5` (partial rate 0.333, partial 5/15).
- Add scripted successful samples near `finger_scale=1.15` (partial rate 0.240, partial 6/25).
- Add scripted successful samples near `thumb_rank=2` (partial rate 0.133, partial 2/15).
- Add scripted successful samples near `thumb_rank=3` (partial rate 0.133, partial 2/15).
- Add scripted successful samples near `thumb_rank=4` (partial rate 0.133, partial 2/15).
- Add scripted successful samples near `finger_scale=0.85` (partial rate 0.120, partial 3/25).
