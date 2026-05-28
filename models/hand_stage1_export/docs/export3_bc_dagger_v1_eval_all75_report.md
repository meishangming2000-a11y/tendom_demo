# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_dagger_v1.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_dagger_pinned_wrap_v1.npz`
- Episode count: 75
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 58, 'PINNED_PARTIAL': 17}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.773
- Mean hold contacts: 2.907
- Mean hold penetration: 0.006986
- Mean four-tip distance: 0.036977
- Mean thumb-ball distance: 0.088433

## Interpretation

- This checks whether the offline BC policy can reproduce the scripted pinned-wrap target pattern in MuJoCo rollout.
- The ball is still pinned during closing, so this is not free-object stable grasp.
- If pass rate is low, the dataset needs stage identity or more episodes before RL.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 2 | 0.006495 | 0.034136 | 0.086708 |
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 2 | 0.006373 | 0.034180 | 0.087583 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 2 | 0.006282 | 0.034220 | 0.087372 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 2 | 0.006435 | 0.034154 | 0.089808 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.006657 | 0.033988 | 0.092307 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.006644 | 0.035820 | 0.086928 |
| 6 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.006689 | 0.035793 | 0.088095 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.006454 | 0.035801 | 0.086724 |
| 8 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.006632 | 0.035789 | 0.090474 |
| 9 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.007249 | 0.035774 | 0.092954 |
| 10 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 4 | 0.021901 | 0.035219 | 0.085908 |
| 11 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 4 | 0.021959 | 0.035136 | 0.087630 |
| 12 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 4 | 0.021876 | 0.035272 | 0.086061 |
| 13 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 4 | 0.021904 | 0.035218 | 0.089631 |
| 14 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 4 | 0.021931 | 0.035178 | 0.092349 |
| 15 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 0 | 0.000000 | 0.044144 | 0.095861 |
| 16 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 0 | 0.000000 | 0.044482 | 0.097454 |
| 17 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 0 | 0.000000 | 0.043472 | 0.095386 |
| 18 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 0 | 0.000000 | 0.044237 | 0.100033 |
| 19 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 0 | 0.000000 | 0.044287 | 0.102808 |
| 20 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 2 | 0.004792 | 0.034829 | 0.092825 |
| 21 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 2 | 0.004848 | 0.034717 | 0.094082 |
| 22 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 2 | 0.004832 | 0.034853 | 0.090658 |
| 23 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 2 | 0.004819 | 0.034771 | 0.096156 |
| 24 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 2 | 0.004851 | 0.034777 | 0.101110 |
| 25 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 4 | 0.002194 | 0.036326 | 0.091668 |
| 26 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 4 | 0.002184 | 0.036367 | 0.094014 |
| 27 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 4 | 0.002159 | 0.036400 | 0.089583 |
| 28 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 4 | 0.002172 | 0.036380 | 0.096037 |
| 29 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 4 | 0.002128 | 0.036444 | 0.100434 |
| 30 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 1 | 2 | 0.014227 | 0.032183 | 0.090957 |
| 31 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 2 | 3 | 0.014302 | 0.032021 | 0.090423 |
| 32 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 3 | 3 | 0.014308 | 0.032074 | 0.090056 |
| 33 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 4 | 3 | 0.014247 | 0.032081 | 0.091662 |
| 34 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.014095 | 0.032061 | 0.094091 |
| 35 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 1 | 4 | 0.005211 | 0.035583 | 0.090497 |
| 36 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 2 | 4 | 0.005118 | 0.035615 | 0.090501 |
| 37 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.005485 | 0.035319 | 0.089758 |
| 38 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.005041 | 0.035693 | 0.091682 |
| 39 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 5 | 4 | 0.004957 | 0.035690 | 0.094099 |
| 40 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.004067 | 0.036873 | 0.090240 |
| 41 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.004059 | 0.036877 | 0.090560 |
| 42 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.004067 | 0.036859 | 0.090077 |
| 43 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.004052 | 0.036871 | 0.091955 |
| 44 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.003999 | 0.036887 | 0.094071 |
| 45 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 1 | 1 | 0.001854 | 0.040031 | 0.083712 |
| 46 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 2 | 1 | 0.001910 | 0.039962 | 0.085534 |
| 47 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 3 | 1 | 0.002096 | 0.039800 | 0.083790 |
| 48 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 4 | 1 | 0.001955 | 0.039940 | 0.089018 |
| 49 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 5 | 1 | 0.002180 | 0.039771 | 0.091491 |
| 50 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.011230 | 0.034544 | 0.083583 |
| 51 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.011312 | 0.034491 | 0.085429 |
| 52 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.011167 | 0.034562 | 0.083895 |
| 53 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.011349 | 0.034463 | 0.088981 |
| 54 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.011278 | 0.034518 | 0.091827 |
| 55 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.012620 | 0.040474 | 0.082687 |
| 56 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.012664 | 0.040463 | 0.085328 |
| 57 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.012649 | 0.040477 | 0.083388 |
| 58 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.012647 | 0.040475 | 0.089241 |
| 59 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.012597 | 0.040519 | 0.091611 |
| 60 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 1 | 4 | 0.005328 | 0.035247 | 0.077679 |
| 61 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 2 | 4 | 0.005293 | 0.035242 | 0.078484 |
| 62 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 3 | 4 | 0.005208 | 0.035271 | 0.077492 |
| 63 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 4 | 4 | 0.005178 | 0.035309 | 0.080501 |
| 64 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 5 | 4 | 0.005442 | 0.035176 | 0.083778 |
| 65 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 1 | 5 | 0.002403 | 0.039943 | 0.077476 |
| 66 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 2 | 5 | 0.002473 | 0.039936 | 0.078739 |
| 67 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 3 | 5 | 0.002225 | 0.039932 | 0.077101 |
| 68 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 4 | 5 | 0.002480 | 0.039939 | 0.080713 |
| 69 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 5 | 4 | 0.002550 | 0.039926 | 0.083940 |
| 70 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 1 | 4 | 0.005690 | 0.039555 | 0.077177 |
| 71 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 2 | 4 | 0.005606 | 0.039635 | 0.078774 |
| 72 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 3 | 3 | 0.005580 | 0.039647 | 0.077110 |
| 73 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 4 | 3 | 0.005586 | 0.039654 | 0.080910 |
| 74 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 5 | 4 | 0.005725 | 0.039553 | 0.083843 |
