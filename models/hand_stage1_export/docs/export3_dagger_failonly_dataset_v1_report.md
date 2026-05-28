# Export3 DAgger Dataset v1 Report

Status: diagnostic DAgger correction dataset, not a promoted stable_grasp baseline.

- Base dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_scripted_pinned_wrap_v0.npz`
- Policy used for on-policy states: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Output dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_dagger_failonly_pinned_wrap_v1.npz`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_dagger_failonly_dataset_v1.json`
- Base samples retained: 4640
- DAgger correction samples: 1500
- DAgger rollout episodes collected: 75
- DAgger rollout episodes kept as corrections: 12
- Observation dim: 109
- Action dim: 21
- DAgger rollout classification counts: `{'PINNED_WRAP_PASS': 63, 'PINNED_PARTIAL': 12}`
- Kept correction classification counts: `{'PINNED_PARTIAL': 12}`
- Execute expert mix: 0.0
- Keep rollout classes: `['PINNED_PARTIAL']`

## Semantics

- Base samples are successful scripted pinned-wrap samples.
- DAgger samples are observations visited by the current BC policy; labels are scripted expert actuator targets at the same stage/fraction.
- The ball is pinned during closing. This remains pinned-wrap training, not free-object stable grasp.

## DAgger Episodes

| Episode | Kept | Class under policy rollout | Ball | Finger scale | Thumb rank | Samples | Hold contacts | Penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 125 | 3 | 0.004596 | 0.035774 | 0.089437 |
| 1 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 125 | 3 | 0.003827 | 0.035897 | 0.089980 |
| 2 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 125 | 2 | 0.001777 | 0.036462 | 0.086595 |
| 3 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 125 | 3 | 0.000630 | 0.037469 | 0.094267 |
| 4 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 125 | 3 | 0.007464 | 0.033593 | 0.092846 |
| 5 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 125 | 3 | 0.012581 | 0.033360 | 0.086634 |
| 6 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 125 | 3 | 0.012524 | 0.032491 | 0.094445 |
| 7 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 125 | 4 | 0.012445 | 0.033377 | 0.086420 |
| 8 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 125 | 3 | 0.008911 | 0.034339 | 0.091559 |
| 9 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 125 | 4 | 0.009428 | 0.034668 | 0.093276 |
| 10 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 125 | 4 | 0.022898 | 0.033600 | 0.087062 |
| 11 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 125 | 5 | 0.023205 | 0.033239 | 0.090739 |
| 12 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 125 | 3 | 0.023180 | 0.033736 | 0.087373 |
| 13 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 125 | 4 | 0.023090 | 0.032120 | 0.093214 |
| 14 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 125 | 3 | 0.019431 | 0.034388 | 0.096934 |
| 15 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 125 | 2 | 0.004129 | 0.036286 | 0.098222 |
| 16 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 125 | 1 | 0.003433 | 0.037333 | 0.097184 |
| 17 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 125 | 2 | 0.005375 | 0.034756 | 0.097148 |
| 18 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 125 | 2 | 0.003573 | 0.036838 | 0.100278 |
| 19 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 125 | 1 | 0.000987 | 0.040538 | 0.100270 |
| 20 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 125 | 3 | 0.004347 | 0.034976 | 0.094561 |
| 21 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 125 | 2 | 0.004177 | 0.035156 | 0.095694 |
| 22 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 125 | 3 | 0.005226 | 0.033601 | 0.100300 |
| 23 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 125 | 2 | 0.006075 | 0.033674 | 0.097970 |
| 24 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 125 | 4 | 0.004524 | 0.034762 | 0.103784 |
| 25 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 125 | 4 | 0.002125 | 0.036518 | 0.092313 |
| 26 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 125 | 4 | 0.002019 | 0.036549 | 0.094228 |
| 27 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 125 | 4 | 0.002583 | 0.036083 | 0.096996 |
| 28 | False | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 125 | 4 | 0.001954 | 0.036642 | 0.096512 |
| 29 | True | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 125 | 4 | 0.002141 | 0.036543 | 0.101687 |
| 30 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 1 | 125 | 3 | 0.006971 | 0.033645 | 0.096463 |
| 31 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 2 | 125 | 4 | 0.005268 | 0.034135 | 0.095485 |
| 32 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 3 | 125 | 3 | 0.011027 | 0.032530 | 0.090260 |
| 33 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 4 | 125 | 4 | 0.005487 | 0.034081 | 0.095702 |
| 34 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 5 | 125 | 3 | 0.014245 | 0.032143 | 0.094320 |
| 35 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 1 | 125 | 4 | 0.001392 | 0.037289 | 0.092256 |
| 36 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 2 | 125 | 4 | 0.001441 | 0.037327 | 0.092848 |
| 37 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 3 | 125 | 3 | 0.002680 | 0.036936 | 0.091119 |
| 38 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 4 | 125 | 4 | 0.001602 | 0.037263 | 0.093836 |
| 39 | True | PINNED_PARTIAL | `[0.01, -0.1, 0.21]` | 1.00 | 5 | 125 | 4 | 0.001620 | 0.036966 | 0.105401 |
| 40 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 1 | 125 | 3 | 0.003910 | 0.036856 | 0.091287 |
| 41 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 2 | 125 | 3 | 0.003730 | 0.036842 | 0.092201 |
| 42 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 3 | 125 | 3 | 0.004729 | 0.036542 | 0.095173 |
| 43 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 4 | 125 | 3 | 0.004233 | 0.036694 | 0.097693 |
| 44 | False | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 5 | 125 | 3 | 0.004149 | 0.036838 | 0.095238 |
| 45 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 1 | 125 | 3 | 0.010535 | 0.034951 | 0.087993 |
| 46 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 2 | 125 | 3 | 0.009945 | 0.035281 | 0.088380 |
| 47 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 3 | 125 | 2 | 0.004268 | 0.038255 | 0.087798 |
| 48 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 4 | 125 | 3 | 0.009159 | 0.035697 | 0.092753 |
| 49 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 5 | 125 | 2 | 0.003748 | 0.038805 | 0.092391 |
| 50 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 1 | 125 | 3 | 0.012826 | 0.035642 | 0.086324 |
| 51 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 2 | 125 | 3 | 0.014169 | 0.034165 | 0.088504 |
| 52 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 3 | 125 | 3 | 0.012676 | 0.033843 | 0.086520 |
| 53 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 4 | 125 | 3 | 0.010952 | 0.034788 | 0.089515 |
| 54 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 5 | 125 | 3 | 0.013332 | 0.035545 | 0.095597 |
| 55 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 1 | 125 | 3 | 0.013332 | 0.037181 | 0.087316 |
| 56 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 2 | 125 | 3 | 0.013337 | 0.036507 | 0.092313 |
| 57 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 3 | 125 | 3 | 0.011772 | 0.039687 | 0.083247 |
| 58 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 4 | 125 | 3 | 0.013637 | 0.036673 | 0.091881 |
| 59 | False | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 5 | 125 | 3 | 0.013632 | 0.037828 | 0.092086 |
| 60 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 1 | 125 | 4 | 0.001593 | 0.040297 | 0.081082 |
| 61 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 2 | 125 | 4 | 0.001367 | 0.040297 | 0.079660 |
| 62 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 3 | 125 | 3 | 0.005712 | 0.037868 | 0.080403 |
| 63 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 4 | 125 | 5 | 0.008399 | 0.037689 | 0.098441 |
| 64 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 5 | 125 | 4 | 0.005441 | 0.035254 | 0.083829 |
| 65 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 1 | 125 | 4 | 0.003384 | 0.039796 | 0.079006 |
| 66 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 2 | 125 | 4 | 0.003982 | 0.039710 | 0.080017 |
| 67 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 3 | 125 | 4 | 0.002839 | 0.039839 | 0.076895 |
| 68 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 4 | 125 | 4 | 0.003189 | 0.039857 | 0.081990 |
| 69 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 5 | 125 | 4 | 0.003327 | 0.039870 | 0.087827 |
| 70 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 1 | 125 | 4 | 0.005925 | 0.039351 | 0.077774 |
| 71 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 2 | 125 | 4 | 0.005862 | 0.039328 | 0.079148 |
| 72 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 3 | 125 | 4 | 0.006726 | 0.039047 | 0.080012 |
| 73 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 4 | 125 | 4 | 0.006301 | 0.039237 | 0.084599 |
| 74 | False | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 5 | 125 | 4 | 0.006077 | 0.039167 | 0.084240 |
