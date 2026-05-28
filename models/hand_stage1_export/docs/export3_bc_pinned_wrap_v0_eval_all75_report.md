# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_scripted_pinned_wrap_v0.npz`
- Episode count: 75
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 63, 'PINNED_PARTIAL': 12}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.840
- Mean hold contacts: 3.280
- Mean hold penetration: 0.007314
- Mean four-tip distance: 0.036297
- Mean thumb-ball distance: 0.090997

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
| 30 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 1 | 3 | 0.006971 | 0.033645 | 0.096463 |
| 31 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 2 | 4 | 0.005268 | 0.034135 | 0.095485 |
| 32 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 3 | 3 | 0.011027 | 0.032530 | 0.090260 |
| 33 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 4 | 4 | 0.005487 | 0.034081 | 0.095702 |
| 34 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 5 | 3 | 0.014245 | 0.032143 | 0.094320 |
| 35 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 1 | 4 | 0.001392 | 0.037289 | 0.092256 |
| 36 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 2 | 4 | 0.001441 | 0.037327 | 0.092848 |
| 37 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.002680 | 0.036936 | 0.091119 |
| 38 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 4 | 4 | 0.001602 | 0.037263 | 0.093836 |
| 39 | pinned | PINNED_PARTIAL | `[0.01, -0.1, 0.21]` | 1.00 | 5 | 4 | 0.001620 | 0.036966 | 0.105401 |
| 40 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.003910 | 0.036856 | 0.091287 |
| 41 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.003730 | 0.036842 | 0.092201 |
| 42 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.004729 | 0.036542 | 0.095173 |
| 43 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.004233 | 0.036694 | 0.097693 |
| 44 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.004149 | 0.036838 | 0.095238 |
| 45 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 1 | 3 | 0.010535 | 0.034951 | 0.087993 |
| 46 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 2 | 3 | 0.009945 | 0.035281 | 0.088380 |
| 47 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 3 | 2 | 0.004268 | 0.038255 | 0.087798 |
| 48 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 4 | 3 | 0.009159 | 0.035697 | 0.092753 |
| 49 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.003748 | 0.038805 | 0.092391 |
| 50 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.012826 | 0.035642 | 0.086324 |
| 51 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.014169 | 0.034165 | 0.088504 |
| 52 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.012676 | 0.033843 | 0.086520 |
| 53 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.010952 | 0.034788 | 0.089515 |
| 54 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.013332 | 0.035545 | 0.095597 |
| 55 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.013332 | 0.037181 | 0.087316 |
| 56 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.013337 | 0.036507 | 0.092313 |
| 57 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.011772 | 0.039687 | 0.083247 |
| 58 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.013637 | 0.036673 | 0.091881 |
| 59 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.013632 | 0.037828 | 0.092086 |
| 60 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 1 | 4 | 0.001593 | 0.040297 | 0.081082 |
| 61 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 2 | 4 | 0.001367 | 0.040297 | 0.079660 |
| 62 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 3 | 3 | 0.005712 | 0.037868 | 0.080403 |
| 63 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 4 | 5 | 0.008399 | 0.037689 | 0.098441 |
| 64 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 5 | 4 | 0.005441 | 0.035254 | 0.083829 |
| 65 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 1 | 4 | 0.003384 | 0.039796 | 0.079006 |
| 66 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 2 | 4 | 0.003982 | 0.039710 | 0.080017 |
| 67 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 3 | 4 | 0.002839 | 0.039839 | 0.076895 |
| 68 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 4 | 4 | 0.003189 | 0.039857 | 0.081990 |
| 69 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 5 | 4 | 0.003327 | 0.039870 | 0.087827 |
| 70 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 1 | 4 | 0.005925 | 0.039351 | 0.077774 |
| 71 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 2 | 4 | 0.005862 | 0.039328 | 0.079148 |
| 72 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 3 | 4 | 0.006726 | 0.039047 | 0.080012 |
| 73 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 4 | 4 | 0.006301 | 0.039237 | 0.084599 |
| 74 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 5 | 4 | 0.006077 | 0.039167 | 0.084240 |
