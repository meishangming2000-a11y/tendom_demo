# Stage3.11D-D Lift Quality Head v0 Train Report

Generated: `2026-06-12T02:24:27`

## Boundary

- Offline MuJoCo-only classifier training from dense sensor-fusion traces.
- Predicts lift/grasp quality labels, not full hand actions.
- No closed-loop controller or demo-gallery promotion is made here.

## Outputs

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_11d_d_dense_sensor_fusion_dataset_v0.npz`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_11d_d_lift_quality_head_v0.pth`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_11d_d_lift_quality_head_v0_train.json`

## Main Result

- Rows total/train/val: `112875` / `89284` / `23591`
- Input dim: `139`
- Best epoch: `4`
- Primary val F1 (`lift_quality_now`): `0.9998`

| label | val accuracy | val precision | val recall | val F1 | val AUC |
|---|---:|---:|---:|---:|---:|
| `lift_quality_now` | 0.9998 | 1.0000 | 0.9997 | 0.9998 | 1.0000 |
| `adjust_needed_now` | 0.9995 | 0.9984 | 1.0000 | 0.9992 | 1.0000 |
| `hold_safe_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Ablations

| config | input dim | lift-quality val F1 |
|---|---:|---:|
| `all_sensors` | 139 | 0.9998 |
| `no_force` | 124 | 1.0000 |
| `no_tactile` | 130 | 0.9967 |
| `no_vision` | 130 | 0.9969 |
| `no_proprio` | 48 | 1.0000 |

## Next

- Use this head as a shadow evaluator in Stage3.11D-E before any control-loop intervention.
- If all-sensor beats ablations, add a bounded residual micro-adjust teacher around low-quality windows.
