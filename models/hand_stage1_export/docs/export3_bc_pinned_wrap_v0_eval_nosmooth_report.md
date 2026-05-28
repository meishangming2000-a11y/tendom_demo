# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_scripted_pinned_wrap_v0.npz`
- Episode count: 30
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 13, 'PINNED_PARTIAL': 17}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.433
- Mean hold contacts: 3.233
- Mean hold penetration: 0.008956
- Mean four-tip distance: 0.035026
- Mean thumb-ball distance: 0.102092

## Interpretation

- This checks whether the offline BC policy can reproduce the scripted pinned-wrap target pattern in MuJoCo rollout.
- The ball is still pinned during closing, so this is not free-object stable grasp.
- If pass rate is low, the dataset needs stage identity or more episodes before RL.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 4 | 0.010503 | 0.032279 | 0.095300 |
| 1 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 5 | 0.009519 | 0.033729 | 0.134458 |
| 2 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 5 | 0.009983 | 0.034525 | 0.116168 |
| 3 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 3 | 0.005601 | 0.036798 | 0.108422 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.006453 | 0.034212 | 0.092978 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 4 | 0.012584 | 0.033883 | 0.086376 |
| 6 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 4 | 0.011842 | 0.034130 | 0.089297 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 4 | 0.012999 | 0.034248 | 0.092527 |
| 8 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 4 | 0.010590 | 0.034562 | 0.090700 |
| 9 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 4 | 0.011870 | 0.034244 | 0.092610 |
| 10 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.018087 | 0.034947 | 0.105692 |
| 11 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 4 | 0.021945 | 0.034684 | 0.102205 |
| 12 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 4 | 0.021691 | 0.034537 | 0.102145 |
| 13 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.022127 | 0.033109 | 0.108339 |
| 14 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 4 | 0.019300 | 0.034037 | 0.095173 |
| 15 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 1 | 0.000217 | 0.041391 | 0.094407 |
| 16 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 2 | 0.004237 | 0.036651 | 0.108890 |
| 17 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 2 | 0.004301 | 0.035811 | 0.105242 |
| 18 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 2 | 0.004106 | 0.036759 | 0.113181 |
| 19 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 1 | 0.002345 | 0.038931 | 0.112679 |
| 20 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 2 | 0.004804 | 0.034790 | 0.091795 |
| 21 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 2 | 0.004647 | 0.034831 | 0.094831 |
| 22 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 4 | 0.011589 | 0.031526 | 0.111994 |
| 23 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 2 | 0.007215 | 0.032712 | 0.112087 |
| 24 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 2 | 0.006601 | 0.033276 | 0.110888 |
| 25 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 4 | 0.002279 | 0.036302 | 0.091774 |
| 26 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 4 | 0.002270 | 0.036303 | 0.093890 |
| 27 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 4 | 0.002868 | 0.036070 | 0.096554 |
| 28 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 4 | 0.002142 | 0.036312 | 0.096403 |
| 29 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 4 | 0.003963 | 0.035176 | 0.115746 |
