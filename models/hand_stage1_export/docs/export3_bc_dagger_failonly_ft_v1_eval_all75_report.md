# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_dagger_failonly_ft_v1.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_dagger_failonly_pinned_wrap_v1.npz`
- Episode count: 75
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 56, 'PINNED_PARTIAL': 19}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.747
- Mean hold contacts: 2.867
- Mean hold penetration: 0.007867
- Mean four-tip distance: 0.037314
- Mean thumb-ball distance: 0.089473

## Interpretation

- This checks whether the offline BC policy can reproduce the scripted pinned-wrap target pattern in MuJoCo rollout.
- The ball is still pinned during closing, so this is not free-object stable grasp.
- If pass rate is low, the dataset needs stage identity or more episodes before RL.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 2 | 0.003987 | 0.035620 | 0.085933 |
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 2 | 0.003725 | 0.035955 | 0.087300 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 2 | 0.003837 | 0.035969 | 0.086326 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 2 | 0.003876 | 0.035513 | 0.089929 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.003534 | 0.035992 | 0.092246 |
| 5 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 4 | 0.023464 | 0.032902 | 0.086186 |
| 6 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 5 | 0.023419 | 0.033459 | 0.086611 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 4 | 0.007512 | 0.035658 | 0.087307 |
| 8 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 4 | 0.022899 | 0.033681 | 0.088260 |
| 9 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.018809 | 0.034890 | 0.092085 |
| 10 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 4 | 0.021811 | 0.035302 | 0.093590 |
| 11 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 4 | 0.021638 | 0.035399 | 0.091752 |
| 12 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 4 | 0.021832 | 0.035294 | 0.093025 |
| 13 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 4 | 0.021871 | 0.035188 | 0.095105 |
| 14 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.021875 | 0.035237 | 0.098045 |
| 15 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 0 | 0.000000 | 0.047227 | 0.104200 |
| 16 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 0 | 0.000000 | 0.049248 | 0.108158 |
| 17 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 0 | 0.000000 | 0.054315 | 0.115861 |
| 18 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 0 | 0.000000 | 0.047556 | 0.106406 |
| 19 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 0 | 0.000000 | 0.046126 | 0.103222 |
| 20 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 1 | 0.002374 | 0.038716 | 0.095624 |
| 21 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 2 | 0.003762 | 0.036817 | 0.092948 |
| 22 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 1 | 0.000241 | 0.041631 | 0.100038 |
| 23 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 2 | 0.003841 | 0.036634 | 0.095409 |
| 24 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 1 | 0.002883 | 0.038023 | 0.100139 |
| 25 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 4 | 0.002348 | 0.035997 | 0.091597 |
| 26 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 4 | 0.002283 | 0.036137 | 0.093214 |
| 27 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 2 | 0.008059 | 0.032422 | 0.089471 |
| 28 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 4 | 0.002225 | 0.036371 | 0.096016 |
| 29 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 4 | 0.002220 | 0.036411 | 0.099995 |
| 30 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 1 | 3 | 0.014070 | 0.032105 | 0.090144 |
| 31 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 2 | 3 | 0.014322 | 0.032081 | 0.090237 |
| 32 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 3 | 3 | 0.014382 | 0.032138 | 0.090502 |
| 33 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 4 | 2 | 0.013829 | 0.032204 | 0.091550 |
| 34 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 5 | 2 | 0.014568 | 0.032257 | 0.094065 |
| 35 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 1 | 4 | 0.005276 | 0.035317 | 0.090054 |
| 36 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.006099 | 0.034914 | 0.090489 |
| 37 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.007256 | 0.033662 | 0.090025 |
| 38 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.006949 | 0.034086 | 0.091932 |
| 39 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.007056 | 0.033972 | 0.094111 |
| 40 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.003613 | 0.036844 | 0.090463 |
| 41 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.003686 | 0.036872 | 0.090349 |
| 42 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.003441 | 0.036787 | 0.092591 |
| 43 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.003739 | 0.036884 | 0.091797 |
| 44 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.003896 | 0.036816 | 0.094063 |
| 45 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 1 | 2 | 0.004978 | 0.037954 | 0.082794 |
| 46 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 2 | 2 | 0.004053 | 0.038554 | 0.085495 |
| 47 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 0.85 | 3 | 2 | 0.005165 | 0.037905 | 0.083725 |
| 48 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 4 | 1 | 0.002103 | 0.039872 | 0.089665 |
| 49 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 5 | 1 | 0.001000 | 0.040526 | 0.091420 |
| 50 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 1 | 3 | 0.014523 | 0.033676 | 0.083923 |
| 51 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 2 | 3 | 0.014751 | 0.033629 | 0.085343 |
| 52 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 3 | 3 | 0.011547 | 0.034432 | 0.083477 |
| 53 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 4 | 3 | 0.011621 | 0.034366 | 0.089780 |
| 54 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 5 | 3 | 0.013642 | 0.033848 | 0.091415 |
| 55 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 1 | 3 | 0.012868 | 0.039860 | 0.084503 |
| 56 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 2 | 3 | 0.012588 | 0.040235 | 0.085237 |
| 57 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 3 | 3 | 0.011430 | 0.040391 | 0.083932 |
| 58 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 4 | 3 | 0.012659 | 0.040363 | 0.087950 |
| 59 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 5 | 3 | 0.013243 | 0.038060 | 0.092114 |
| 60 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 1 | 3 | 0.004837 | 0.036726 | 0.077157 |
| 61 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 2 | 4 | 0.004377 | 0.036216 | 0.078275 |
| 62 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 3 | 4 | 0.004693 | 0.036688 | 0.076464 |
| 63 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 4 | 4 | 0.004424 | 0.035810 | 0.080509 |
| 64 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 5 | 3 | 0.003839 | 0.036639 | 0.083563 |
| 65 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 1 | 4 | 0.003899 | 0.039691 | 0.077309 |
| 66 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 2 | 4 | 0.003813 | 0.039700 | 0.078348 |
| 67 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 3 | 5 | 0.002682 | 0.039890 | 0.077439 |
| 68 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 4 | 4 | 0.002904 | 0.039857 | 0.080836 |
| 69 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 5 | 5 | 0.002622 | 0.039904 | 0.083557 |
| 70 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 1 | 3 | 0.005572 | 0.039583 | 0.077288 |
| 71 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 2 | 4 | 0.005634 | 0.039484 | 0.078334 |
| 72 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 3 | 4 | 0.006443 | 0.039120 | 0.077906 |
| 73 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 4 | 4 | 0.005784 | 0.039490 | 0.080782 |
| 74 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 5 | 4 | 0.005846 | 0.039487 | 0.083571 |
