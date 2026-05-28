# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_scripted_pinned_wrap_v0.npz`
- Episode count: 30
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 19, 'PINNED_PARTIAL': 11}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.633
- Mean hold contacts: 3.067
- Mean hold penetration: 0.007955
- Mean four-tip distance: 0.035159
- Mean thumb-ball distance: 0.094264

## Interpretation

- This checks whether the offline BC policy can reproduce the scripted pinned-wrap target pattern in MuJoCo rollout.
- The ball is still pinned during closing, so this is not free-object stable grasp.
- If pass rate is low, the dataset needs stage identity or more episodes before RL.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 3 | 0.004596 | 0.035774 | 0.089437 |
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 3 | 0.003827 | 0.035897 | 0.089980 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 2 | 0.001777 | 0.036462 | 0.086595 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 3 | 0.000630 | 0.037469 | 0.094267 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 3 | 0.007464 | 0.033593 | 0.092846 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.012581 | 0.033360 | 0.086634 |
| 6 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.012524 | 0.032491 | 0.094445 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 4 | 0.012445 | 0.033377 | 0.086420 |
| 8 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.008911 | 0.034339 | 0.091559 |
| 9 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 4 | 0.009428 | 0.034668 | 0.093276 |
| 10 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 4 | 0.022898 | 0.033600 | 0.087062 |
| 11 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 5 | 0.023205 | 0.033239 | 0.090739 |
| 12 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.023180 | 0.033736 | 0.087373 |
| 13 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 4 | 0.023090 | 0.032120 | 0.093214 |
| 14 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.019431 | 0.034388 | 0.096934 |
| 15 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 2 | 0.004129 | 0.036286 | 0.098222 |
| 16 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 1 | 0.003433 | 0.037333 | 0.097184 |
| 17 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 2 | 0.005375 | 0.034756 | 0.097148 |
| 18 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 2 | 0.003573 | 0.036838 | 0.100278 |
| 19 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 1 | 0.000987 | 0.040538 | 0.100270 |
| 20 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 3 | 0.004347 | 0.034976 | 0.094561 |
| 21 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 2 | 0.004177 | 0.035156 | 0.095694 |
| 22 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 3 | 0.005226 | 0.033601 | 0.100300 |
| 23 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 2 | 0.006075 | 0.033674 | 0.097970 |
| 24 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 4 | 0.004524 | 0.034762 | 0.103784 |
| 25 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 4 | 0.002125 | 0.036518 | 0.092313 |
| 26 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 4 | 0.002019 | 0.036549 | 0.094228 |
| 27 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 4 | 0.002583 | 0.036083 | 0.096996 |
| 28 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 4 | 0.001954 | 0.036642 | 0.096512 |
| 29 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 4 | 0.002141 | 0.036543 | 0.101687 |
