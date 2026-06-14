# Stage3.11D-D Dense Sensor Fusion + Lift Quality Head v0 Closeout

Generated: `2026-06-12`

## Boundary

- MuJoCo-only dense capture and offline classifier training.
- No real hardware, real camera, real tactile hardware, ultrasound, or hardware runtime integration.
- Not a demo-gallery promotion.
- Not full-action ACT/DP closed-loop success.
- The trained head predicts grasp/lift quality labels only; it does not output hand actions.

## What Changed

Stage3.11D-D added dense sensor-fusion capture from the Stage3.11D-C selected true-pinch center:

```text
simulations/models/arm_hand_stage1_export/export_stage3_11d_d_dense_sensor_fusion_dataset_v0.py
```

It also added an offline lift-quality classifier:

```text
simulations/models/arm_hand_stage1_export/train_stage3_11d_d_lift_quality_head_v0.py
```

The event-gated runner now has a default-off dense trace hook:

```text
--capture-dense-sensor-trace
--dense-trace-sample-every
```

The hook records virtual vision, synthetic contact/tactile morphology, simulated motor force feedback, proprioception, current scripted control, phase, and labels while preserving old behavior when disabled.

## Dense Dataset

Command:

```powershell
python -u .\simulations\models\arm_hand_stage1_export\export_stage3_11d_d_dense_sensor_fusion_dataset_v0.py --episodes 200 --dense-trace-sample-every 1
```

Result:

- Episodes: `200`
- Dense rows: `329075`
- Grasp-evidence rows used for lift-quality training: `112875`
- Episode success: `148 / 200`
- Terminal reasons:
  - `148` success
  - `41` lift_gate_failed
  - `8` contact_gate_failed
  - `3` true_pinch_morphology_gate_failed

Dataset shape:

- `obs`: `[329075, 139]`
- `vision_features`: `[329075, 9]`
- `tactile_features`: `[329075, 9]`
- `force_features`: `[329075, 15]`
- `context_features`: `[329075, 4]`
- `proprio_features`: `[329075, 91]`
- `actions`: `[329075, 26]`
- `safety_labels`: `[329075, 12]`

Sensor blocks:

- Virtual vision: ball relative pose, lift, goal-normalized lift, virtual confidence/visibility.
- Synthetic tactile/contact: contact counts, tip/non-tip ratio, two-tip pinch, wrap/support, penetration.
- Simulated motor force feedback: active thumb + active-finger pair tension/balance/Iq/saturation and group tension summaries.
- Proprioception: qpos, qvel, ctrl.
- Morphology truth is exported as training/evaluation supervision, not future hardware runtime truth.

Artifacts:

```text
simulations/models/arm_hand_stage1_export/data/stage3_11d_d_dense_sensor_fusion_dataset_v0.npz
simulations/models/arm_hand_stage1_export/data/stage3_11d_d_dense_sensor_fusion_dataset_v0.jsonl
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_d_dense_sensor_fusion_dataset_v0.json
simulations/models/arm_hand_stage1_export/docs/stage3_11d_d_dense_sensor_fusion_dataset_v0_report.md
```

## Lift Quality Head

Command:

```powershell
python -u .\simulations\models\arm_hand_stage1_export\train_stage3_11d_d_lift_quality_head_v0.py --dataset .\simulations\models\arm_hand_stage1_export\data\stage3_11d_d_dense_sensor_fusion_dataset_v0.npz --epochs 24 --batch-size 1024 --ablation-suite
```

Training scope:

- Rows total/train/val: `112875 / 89284 / 23591`
- Episode split: `160` train episodes, `40` val episodes
- Target labels: `lift_quality_now`, `adjust_needed_now`, `hold_safe_now`
- Status: `stage3_11d_d_lift_quality_head_v0_offline_trained_not_closed_loop_promoted`

Main validation result:

| label | accuracy | precision | recall | F1 | AUC |
|---|---:|---:|---:|---:|---:|
| `lift_quality_now` | 0.9998 | 1.0000 | 0.9997 | 0.9998 | 1.0000 |
| `adjust_needed_now` | 0.9995 | 0.9984 | 1.0000 | 0.9992 | 1.0000 |
| `hold_safe_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Ablation:

| config | input dim | lift-quality val F1 |
|---|---:|---:|
| `all_sensors` | 139 | 0.9998 |
| `no_force` | 124 | 1.0000 |
| `no_tactile` | 130 | 0.9967 |
| `no_vision` | 130 | 0.9969 |
| `no_proprio` | 48 | 1.0000 |

Artifacts:

```text
simulations/models/arm_hand_stage1_export/checkpoints/stage3_11d_d_lift_quality_head_v0.pth
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_d_lift_quality_head_v0_train.json
simulations/models/arm_hand_stage1_export/docs/stage3_11d_d_lift_quality_head_v0_train_report.md
```

## Interpretation

The classifier learns the current rule-labeled quality boundary almost perfectly. The high ablation scores mean the labels are still largely sensor-consistency/rule-separable rather than a hard learned manipulation policy problem. This is good for a shadow safety/quality monitor, but it is not enough evidence to let the head directly control the hand.

The dataset is useful because it now gives Stage3 a synchronized per-step table of:

```text
virtual vision + tactile/contact + motor force feedback + proprioception + action + phase + outcome labels
```

That is the missing bridge between scripted event control and a future residual micro-adjust policy.

## Next

Stage3.11D-E should use the checkpoint as a shadow evaluator inside the MuJoCo event runner:

- compare predicted `lift_quality_now` / `adjust_needed_now` against live rule labels,
- report false positive/false negative windows by phase,
- do not alter actions on the first pass,
- then add a bounded residual micro-adjust teacher only around low-quality slow-lift/hold windows.

Promotion gates remain:

- no closed-loop action intervention until the shadow evaluator passes,
- no demo-gallery promotion until visual cleanliness and randomized robustness both pass,
- no hardware claims; motor force feedback remains simulated from MuJoCo actuator loads.
