# Export3 BC Pinned-Wrap v0 Online Eval Report

Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_dagger_v1.pth`
- Dataset reference: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_dagger_pinned_wrap_v1.npz`
- Episode count: 30
- Modes: `['pinned']`
- Classification counts: `{'PINNED_WRAP_PASS': 18, 'PINNED_PARTIAL': 12}`
- Action smoothing: 0.0

## Summary

- Pinned wrap pass rate: 0.600
- Mean hold contacts: 2.500
- Mean hold penetration: 0.007015
- Mean four-tip distance: 0.036739
- Mean thumb-ball distance: 0.092288

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
