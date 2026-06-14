# Stage3.12B Morphology Quality Head v0 Train Report

Generated: `2026-06-13T12:52:04`

## Boundary

- Offline MuJoCo-only classifier training from dense morphology-quality traces.
- Predicts morphology/quality labels, not hand or arm actions.
- No closed-loop controller, demo-gallery, full-action ACT/DP, or hardware-runtime promotion is made here.

## Outputs

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_12b_morphology_quality_dataset_v0.npz`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_12b_morphology_quality_head_v0.pth`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_12b_morphology_quality_head_v0_train.json`

## Main Result

- Rows total/train/val: `29726` / `24147` / `5579`
- Input dim: `139`
- Best epoch: `18`
- Primary val F1 (`morphology_clean_now`): `1.0000`

| label | val accuracy | val precision | val recall | val F1 | val AUC | positive fraction |
|---|---:|---:|---:|---:|---:|---:|
| `morphology_clean_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.7440 |
| `good_two_tip_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8096 |
| `low_non_tip_now` | 0.9998 | 1.0000 | 0.9998 | 0.9999 | 1.0000 | 0.8267 |
| `wrap_now` | 0.9998 | 0.9990 | 1.0000 | 0.9995 | 1.0000 | 0.1733 |
| `floor_contact_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.1140 |
| `penetration_risk_now` | 1.0000 | 0.0000 | 0.0000 | 0.0000 | nan | 0.0000 |
| `lift_quality_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.7440 |
| `future_success` | 0.8998 | 0.9204 | 0.9605 | 0.9400 | 0.9486 | 0.8177 |

## Candidate Validation Slice

| candidate | morphology-clean F1 | good-two-tip F1 | lift-quality F1 | future-success F1 |
|---|---:|---:|---:|---:|
| `baseline_di` | 1.0000 | 1.0000 | 1.0000 | 0.8941 |
| `lift_ls460` | 1.0000 | 1.0000 | 1.0000 | 0.9809 |

## Ablations

| config | input dim | morphology-clean val F1 |
|---|---:|---:|
| `all_sensors` | 139 | 1.0000 |
| `no_tactile` | 130 | 0.9961 |
| `no_force` | 124 | 1.0000 |
| `no_vision` | 130 | 1.0000 |
| `no_proprio` | 48 | 1.0000 |

## Interpretation

- This is a current-state morphology/quality scorer. It can be used for shadow ranking and residual-window selection.
- It is not yet an action policy. Promotion still requires closed-loop multiseed evidence against frozen D-I.

## Next

- Run the head in shadow on fresh D-I/lift candidates and log false positive/false negative windows.
- Use only high-confidence low-quality windows to design a bounded residual teacher; reject any branch that trades lift failures for morphology failures.
