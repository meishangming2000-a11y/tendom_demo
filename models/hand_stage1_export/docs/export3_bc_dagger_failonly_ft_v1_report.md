# Export3 BC Pinned-Wrap v0 Report

Status: diagnostic offline BC smoke test, not a promoted stable_grasp baseline.

- Dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_dagger_failonly_pinned_wrap_v1.npz`
- Checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_dagger_failonly_ft_v1.pth`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_bc_dagger_failonly_ft_v1.json`
- Init checkpoint: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Normalization source: `D:\tendon_project\simulations\models\hand_stage1_export\checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Class filter: `PINNED_WRAP_PASS,DAGGER_CORRECTION`
- Train samples: 4930
- Val samples: 1210
- Observation dim: 109
- Action dim: 21
- Hidden dim: 192
- Depth: 3
- Epochs: 30
- Final train MSE normalized: 0.00184031
- Final val MSE normalized: 0.00554864
- Val action RMSE raw units: 0.01668531

## Interpretation

- This only checks whether the scripted export3 pinned-wrap target mapping is learnable offline.
- It does not prove rollout stability, free-object retention, gravity grasp, or sim-to-real readiness.
- Next required step is online rollout evaluation against `scene_ball_export3.xml`.

## Loss Curve

| Epoch | Train MSE | Val MSE |
|---:|---:|---:|
| 1 | 0.05496499 | 0.03350286 |
| 2 | 0.04506306 | 0.02985035 |
| 3 | 0.03899490 | 0.02759940 |
| 4 | 0.03411587 | 0.02380646 |
| 5 | 0.03019955 | 0.02227327 |
| 6 | 0.02677475 | 0.02038002 |
| 7 | 0.02364746 | 0.01868165 |
| 8 | 0.02035221 | 0.01644034 |
| 9 | 0.01739265 | 0.01547916 |
| 10 | 0.01487666 | 0.01415977 |
| 11 | 0.01270655 | 0.01312535 |
| 12 | 0.01089173 | 0.01272872 |
| 13 | 0.00955624 | 0.01204659 |
| 14 | 0.00808330 | 0.01086241 |
| 15 | 0.00690118 | 0.00990995 |
| 16 | 0.00595158 | 0.00924873 |
| 17 | 0.00512714 | 0.00878890 |
| 18 | 0.00449235 | 0.00836965 |
| 19 | 0.00405814 | 0.00792031 |
| 20 | 0.00367885 | 0.00745300 |
| 21 | 0.00334494 | 0.00732478 |
| 22 | 0.00307680 | 0.00717871 |
| 23 | 0.00280190 | 0.00700315 |
| 24 | 0.00262903 | 0.00651602 |
| 25 | 0.00243596 | 0.00639602 |
| 26 | 0.00229946 | 0.00619193 |
| 27 | 0.00215308 | 0.00595553 |
| 28 | 0.00204031 | 0.00585200 |
| 29 | 0.00192864 | 0.00573031 |
| 30 | 0.00184031 | 0.00554864 |
