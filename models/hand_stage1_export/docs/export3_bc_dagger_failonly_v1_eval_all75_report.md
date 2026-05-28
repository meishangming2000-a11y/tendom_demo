# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_dagger_failonly_v1.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_dagger_failonly_pinned_wrap_v1.npz`
- Episode count: 75
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 58, 'PINNED_PARTIAL': 17}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.773
- Mean hold contacts: 3.013
- Mean hold penetration: 0.007323
- Mean four-tip distance: 0.037193
- Mean thumb-ball distance: 0.089839

## Interpretation

- This checks whether the offline BC policy can reproduce the scripted pinned-wrap target pattern in MuJoCo rollout.
- The ball is still pinned during closing, so this is not free-object stable grasp.
- If pass rate is low, the dataset needs stage identity or more episodes before RL.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 3 | 0.007780 | 0.033359 | 0.086308 |
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 3 | 0.008905 | 0.032702 | 0.086917 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 3 | 0.009185 | 0.032608 | 0.086149 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 4 | 0.009024 | 0.032519 | 0.089391 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.005411 | 0.034784 | 0.095848 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 4 | 0.009945 | 0.034792 | 0.086308 |
| 6 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.010816 | 0.034696 | 0.087245 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 4 | 0.009475 | 0.034949 | 0.086703 |
| 8 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.011154 | 0.034739 | 0.089883 |
| 9 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 4 | 0.011435 | 0.034347 | 0.092454 |
| 10 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 4 | 0.021915 | 0.035057 | 0.088268 |
| 11 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 4 | 0.021863 | 0.035216 | 0.089224 |
| 12 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 4 | 0.021899 | 0.035165 | 0.091921 |
| 13 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 4 | 0.021835 | 0.035286 | 0.092649 |
| 14 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 4 | 0.021932 | 0.035052 | 0.093487 |
| 15 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 0 | 0.000000 | 0.046559 | 0.102519 |
| 16 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 0 | 0.000000 | 0.047456 | 0.103623 |
| 17 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 0 | 0.000000 | 0.059204 | 0.130429 |
| 18 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 0 | 0.000000 | 0.046409 | 0.104242 |
| 19 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 0 | 0.000000 | 0.045710 | 0.104095 |
| 20 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 2 | 0.005016 | 0.034441 | 0.093519 |
| 21 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 2 | 0.005209 | 0.034040 | 0.093205 |
| 22 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 1 | 0.003391 | 0.037581 | 0.101061 |
| 23 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 2 | 0.005100 | 0.034211 | 0.095484 |
| 24 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 2 | 0.003474 | 0.037254 | 0.103007 |
| 25 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 4 | 0.002074 | 0.036515 | 0.092202 |
| 26 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 4 | 0.002142 | 0.036503 | 0.093260 |
| 27 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 4 | 0.002575 | 0.035752 | 0.094382 |
| 28 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 4 | 0.002126 | 0.036500 | 0.095737 |
| 29 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 4 | 0.002205 | 0.036464 | 0.099995 |
| 30 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 1 | 3 | 0.013911 | 0.032039 | 0.090294 |
| 31 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 2 | 3 | 0.013663 | 0.032080 | 0.090320 |
| 32 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 3 | 3 | 0.013742 | 0.032165 | 0.089966 |
| 33 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 4 | 3 | 0.013870 | 0.032012 | 0.091905 |
| 34 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 5 | 3 | 0.013507 | 0.032074 | 0.094101 |
| 35 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.005197 | 0.035432 | 0.090963 |
| 36 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 2 | 4 | 0.004001 | 0.036240 | 0.090262 |
| 37 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 3 | 4 | 0.004292 | 0.036077 | 0.089891 |
| 38 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.004416 | 0.036045 | 0.091590 |
| 39 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 5 | 4 | 0.004636 | 0.035929 | 0.094125 |
| 40 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.003387 | 0.036825 | 0.093858 |
| 41 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.003871 | 0.036842 | 0.091805 |
| 42 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.003941 | 0.036750 | 0.091477 |
| 43 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.004101 | 0.036852 | 0.091856 |
| 44 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.003981 | 0.036889 | 0.094224 |
| 45 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 1 | 1 | 0.000994 | 0.040531 | 0.087056 |
| 46 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 2 | 1 | 0.000734 | 0.040714 | 0.088396 |
| 47 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 3 | 1 | 0.001881 | 0.039923 | 0.086541 |
| 48 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 4 | 1 | 0.000968 | 0.040566 | 0.092792 |
| 49 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 5 | 0 | 0.000000 | 0.041632 | 0.097088 |
| 50 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.012140 | 0.034203 | 0.082721 |
| 51 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.012463 | 0.034127 | 0.085053 |
| 52 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.012773 | 0.034067 | 0.083381 |
| 53 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.012465 | 0.034135 | 0.089292 |
| 54 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.012766 | 0.034017 | 0.091424 |
| 55 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.012587 | 0.040099 | 0.082713 |
| 56 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.012478 | 0.040227 | 0.084976 |
| 57 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.012618 | 0.039464 | 0.083664 |
| 58 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.012426 | 0.040256 | 0.089053 |
| 59 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.012607 | 0.040383 | 0.091656 |
| 60 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 1 | 4 | 0.005794 | 0.034958 | 0.077169 |
| 61 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 2 | 4 | 0.006177 | 0.034769 | 0.077970 |
| 62 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 3 | 4 | 0.006587 | 0.034557 | 0.077034 |
| 63 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 4 | 4 | 0.006080 | 0.034826 | 0.080086 |
| 64 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 5 | 4 | 0.005262 | 0.035224 | 0.087144 |
| 65 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 1 | 5 | 0.002618 | 0.039911 | 0.077400 |
| 66 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 2 | 4 | 0.003000 | 0.039863 | 0.078691 |
| 67 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 3 | 4 | 0.003000 | 0.039852 | 0.078189 |
| 68 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 4 | 4 | 0.002904 | 0.039869 | 0.081197 |
| 69 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 5 | 5 | 0.002629 | 0.039893 | 0.084381 |
| 70 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 1 | 4 | 0.005702 | 0.039550 | 0.077226 |
| 71 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 2 | 4 | 0.005803 | 0.039403 | 0.078356 |
| 72 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 3 | 4 | 0.006050 | 0.039227 | 0.076822 |
| 73 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 4 | 4 | 0.005750 | 0.039438 | 0.080698 |
| 74 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 5 | 4 | 0.005530 | 0.039651 | 0.083568 |
