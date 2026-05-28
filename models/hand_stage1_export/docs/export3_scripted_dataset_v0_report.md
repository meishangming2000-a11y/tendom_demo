# Export3 Scripted Dataset v0 Report

Status: diagnostic training asset, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_scripted_pinned_wrap_v0.npz`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_scripted_dataset_v0.json`
- Backup directory: `D:\tendon_project\simulations\models\hand_stage1_export\archive\export3_dataset_backup_20260523_103859`
- Episode count: 75
- Sample count: 6000
- Observation dim: 109
- Action dim: 21
- Modes: `{'pinned': 75}`
- Classification counts: `{'PINNED_WRAP_PASS': 58, 'PINNED_PARTIAL': 17}`
- Step stride: 3
- Speed: 4.0

## Dataset Semantics

- `observations`: state vector built from controlled joint qpos/qvel, ball pose/velocity, fingertip site positions, fingertip-ball distances, contact summary, previous ctrl, stage fraction, finger scale, thumb rank, and target ball position.
- `actions`: 21-D MuJoCo position actuator target vector after actuator ctrlrange clipping.
- `episode_class` / `sample_class`: scripted-trial diagnostic classification labels.
- This dataset is meant for first-pass BC/DAgger scaffolding over export3 scripted behavior.

## Limits

- The ball is pinned during scripted closing for collected `pinned` episodes.
- Successful pinned wrap is not equivalent to stable free-object grasp.
- Collision is still primitive proxy; clean STL remains visual-only.
- Thumb/wrist mechanical semantics still need manual confirmation before final task training.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Samples | Hold contacts | Hold penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 80 | 2 | 0.006550 | 0.034106 | 0.086441 |
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 80 | 2 | 0.006549 | 0.034107 | 0.087914 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 80 | 2 | 0.006544 | 0.034098 | 0.086647 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 80 | 2 | 0.006549 | 0.034108 | 0.090291 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 80 | 2 | 0.006553 | 0.034126 | 0.092714 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 80 | 4 | 0.010827 | 0.034098 | 0.086239 |
| 6 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 2 | 80 | 4 | 0.010839 | 0.034097 | 0.087776 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 3 | 80 | 4 | 0.010560 | 0.034205 | 0.086493 |
| 8 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 4 | 80 | 5 | 0.010939 | 0.033989 | 0.090222 |
| 9 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 5 | 80 | 5 | 0.011196 | 0.033891 | 0.092626 |
| 10 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 1 | 80 | 5 | 0.022051 | 0.035099 | 0.086614 |
| 11 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 2 | 80 | 5 | 0.022052 | 0.035097 | 0.088030 |
| 12 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 3 | 80 | 5 | 0.022071 | 0.035090 | 0.086790 |
| 13 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 4 | 80 | 5 | 0.022051 | 0.035098 | 0.090346 |
| 14 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.21]` | 1.15 | 5 | 80 | 5 | 0.022059 | 0.035089 | 0.092773 |
| 15 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 1 | 80 | 0 | 0.000000 | 0.043099 | 0.091685 |
| 16 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 2 | 80 | 0 | 0.000000 | 0.043100 | 0.093872 |
| 17 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 3 | 80 | 0 | 0.000000 | 0.043090 | 0.090048 |
| 18 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 4 | 80 | 0 | 0.000000 | 0.043100 | 0.096240 |
| 19 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 0.85 | 5 | 80 | 0 | 0.000000 | 0.043117 | 0.100409 |
| 20 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 1 | 80 | 2 | 0.004911 | 0.034428 | 0.091677 |
| 21 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 2 | 80 | 2 | 0.004909 | 0.034428 | 0.093869 |
| 22 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 3 | 80 | 2 | 0.004929 | 0.034420 | 0.090040 |
| 23 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.00 | 4 | 80 | 2 | 0.004908 | 0.034429 | 0.096243 |
| 24 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.00 | 5 | 80 | 2 | 0.004874 | 0.034441 | 0.100413 |
| 25 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 1 | 80 | 4 | 0.002384 | 0.036458 | 0.091623 |
| 26 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 2 | 80 | 4 | 0.002390 | 0.036455 | 0.093829 |
| 27 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 3 | 80 | 4 | 0.002349 | 0.036465 | 0.090002 |
| 28 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 4 | 80 | 4 | 0.002397 | 0.036453 | 0.096217 |
| 29 | pinned | PINNED_PARTIAL | `[0.0, -0.1, 0.195]` | 1.15 | 5 | 80 | 4 | 0.002470 | 0.036434 | 0.100383 |
| 30 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 1 | 80 | 3 | 0.013865 | 0.032226 | 0.090439 |
| 31 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 2 | 80 | 3 | 0.013863 | 0.032225 | 0.090862 |
| 32 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 3 | 80 | 3 | 0.013894 | 0.032217 | 0.090147 |
| 33 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 4 | 80 | 3 | 0.013861 | 0.032226 | 0.092114 |
| 34 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 0.85 | 5 | 80 | 3 | 0.013809 | 0.032206 | 0.094491 |
| 35 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 1 | 80 | 4 | 0.005045 | 0.035674 | 0.090556 |
| 36 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 2 | 80 | 4 | 0.005043 | 0.035674 | 0.090951 |
| 37 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 3 | 80 | 4 | 0.005086 | 0.035650 | 0.090246 |
| 38 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 4 | 80 | 3 | 0.005038 | 0.035696 | 0.092171 |
| 39 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.00 | 5 | 80 | 3 | 0.004963 | 0.035739 | 0.094546 |
| 40 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 1 | 80 | 3 | 0.004129 | 0.036821 | 0.090583 |
| 41 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 2 | 80 | 3 | 0.004127 | 0.036822 | 0.090973 |
| 42 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 3 | 80 | 3 | 0.004120 | 0.036827 | 0.090273 |
| 43 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 4 | 80 | 3 | 0.004124 | 0.036822 | 0.092188 |
| 44 | pinned | PINNED_WRAP_PASS | `[0.01, -0.1, 0.21]` | 1.15 | 5 | 80 | 3 | 0.004141 | 0.036818 | 0.094564 |
| 45 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 1 | 80 | 1 | 0.002277 | 0.039739 | 0.083283 |
| 46 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 2 | 80 | 1 | 0.002276 | 0.039740 | 0.085899 |
| 47 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 3 | 80 | 1 | 0.002292 | 0.039723 | 0.084052 |
| 48 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 4 | 80 | 1 | 0.002275 | 0.039741 | 0.089463 |
| 49 | pinned | PINNED_PARTIAL | `[-0.01, -0.1, 0.21]` | 0.85 | 5 | 80 | 1 | 0.002250 | 0.039768 | 0.091897 |
| 50 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 1 | 80 | 3 | 0.011220 | 0.034601 | 0.083274 |
| 51 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 2 | 80 | 3 | 0.011219 | 0.034602 | 0.085895 |
| 52 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 3 | 80 | 3 | 0.011243 | 0.034585 | 0.084046 |
| 53 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 4 | 80 | 3 | 0.011218 | 0.034603 | 0.089465 |
| 54 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.00 | 5 | 80 | 3 | 0.011175 | 0.034635 | 0.091899 |
| 55 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 1 | 80 | 3 | 0.013772 | 0.040654 | 0.083580 |
| 56 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 2 | 80 | 3 | 0.013775 | 0.040654 | 0.086119 |
| 57 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 3 | 80 | 3 | 0.013726 | 0.040449 | 0.084278 |
| 58 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 4 | 80 | 3 | 0.013777 | 0.040653 | 0.089600 |
| 59 | pinned | PINNED_WRAP_PASS | `[-0.01, -0.1, 0.21]` | 1.15 | 5 | 80 | 3 | 0.013553 | 0.040503 | 0.092076 |
| 60 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 1 | 80 | 4 | 0.005042 | 0.035430 | 0.077672 |
| 61 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 2 | 80 | 4 | 0.005041 | 0.035431 | 0.078909 |
| 62 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 3 | 80 | 4 | 0.005038 | 0.035422 | 0.077325 |
| 63 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 4 | 80 | 4 | 0.005041 | 0.035432 | 0.081013 |
| 64 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 5 | 80 | 4 | 0.005041 | 0.035450 | 0.084033 |
| 65 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 1 | 80 | 5 | 0.002819 | 0.039764 | 0.077524 |
| 66 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 2 | 80 | 5 | 0.002825 | 0.039761 | 0.078800 |
| 67 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 3 | 80 | 5 | 0.002782 | 0.039774 | 0.077210 |
| 68 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 4 | 80 | 5 | 0.002831 | 0.039759 | 0.080948 |
| 69 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 5 | 80 | 5 | 0.002909 | 0.039732 | 0.083960 |
| 70 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 1 | 80 | 4 | 0.005640 | 0.039599 | 0.077650 |
| 71 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 2 | 80 | 4 | 0.005643 | 0.039598 | 0.078886 |
| 72 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 3 | 80 | 4 | 0.005621 | 0.039609 | 0.077314 |
| 73 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 4 | 80 | 4 | 0.005647 | 0.039597 | 0.080992 |
| 74 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 5 | 80 | 4 | 0.005609 | 0.039597 | 0.084000 |
