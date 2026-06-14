# Stage3.12B Morphology Quality Head v0 Closeout

Generated: `2026-06-13`

## Boundary

- MuJoCo-only data/model/shadow evaluation.
- Uses virtual vision, synthetic contact/tactile morphology, simulated motor force feedback, proprioception, action, and phase labels.
- Morphology truth is supervision/evaluation signal in simulation, not a real hardware sensor claim.
- No controller action changes, bounded residual promotion, demo-gallery promotion, full-action ACT/DP success, real camera, real tactile, ultrasound, or hardware-runtime integration is claimed.

## What Changed

Stage3.12B moved beyond single-parameter D-I tuning by adding a current-state morphology-quality data and model loop:

```text
simulations/models/arm_hand_stage1_export/export_stage3_12b_morphology_quality_dataset_v0.py
simulations/models/arm_hand_stage1_export/train_stage3_12b_morphology_quality_head_v0.py
simulations/models/arm_hand_stage1_export/run_stage3_12b_morphology_quality_shadow_v0.py
```

The target is not to directly control the hand. The target is to reliably identify clean true-pinch morphology and low-quality windows so a later bounded residual teacher can be tested without trading lift failures for morphology failures.

## Dataset

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\export_stage3_12b_morphology_quality_dataset_v0.py --episodes-per-candidate 30 --seed 20260616 --candidate baseline_di --candidate lift_ls460
```

Result:

- Candidates: `baseline_di`, `lift_ls460`
- Episodes: `60`
- Dense rows: `94586`
- Success: `50 / 60`
- Terminal reasons: `50` success, `6` contact gate failed, `2` lift gate failed, `2` true-pinch morphology gate failed

Candidate breakdown:

| candidate | episodes | rows | success | contact | lift | true pinch | release | hold two-tip | hold non-tip | hold wrap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_di` | 30 | 48000 | 25 | 28 | 27 | 25 | 30 | 0.838 | 0.050 | 0.000 |
| `lift_ls460` | 30 | 46586 | 25 | 26 | 25 | 25 | 29 | 0.833 | 0.090 | 0.000 |

Artifacts:

```text
simulations/models/arm_hand_stage1_export/data/stage3_12b_morphology_quality_dataset_v0.npz
simulations/models/arm_hand_stage1_export/data/stage3_12b_morphology_quality_dataset_v0.jsonl
simulations/models/arm_hand_stage1_export/metadata/stage3_12b_morphology_quality_dataset_v0.json
simulations/models/arm_hand_stage1_export/docs/stage3_12b_morphology_quality_dataset_v0_report.md
```

## Offline Training

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_12b_morphology_quality_head_v0.py --dataset .\simulations\models\arm_hand_stage1_export\data\stage3_12b_morphology_quality_dataset_v0.npz --epochs 18 --batch-size 1024 --ablation-suite
```

Training scope:

- Grasp-evidence rows: `29726`
- Train / validation rows: `24147 / 5579`
- Input dimension: `139`
- Primary target: `morphology_clean_now`
- Checkpoint: `checkpoints/stage3_12b_morphology_quality_head_v0.pth`

Validation result:

| label | val F1 | note |
|---|---:|---|
| `morphology_clean_now` | 1.0000 | primary target |
| `good_two_tip_now` | 1.0000 | clean tip-contact label |
| `low_non_tip_now` | 0.9999 | non-tip contact below gate threshold |
| `wrap_now` | 0.9995 | support/wrap risk |
| `floor_contact_now` | 1.0000 | floor contact state |
| `lift_quality_now` | 1.0000 | current lift-quality label |
| `future_success` | 0.9400 | episode outcome is harder but usable |
| `penetration_risk_now` | 0.0000 | no validation positives; do not use as primary trigger |

Ablation result:

| config | input dim | morphology-clean val F1 |
|---|---:|---:|
| `all_sensors` | 139 | 1.0000 |
| `no_tactile` | 130 | 0.9961 |
| `no_force` | 124 | 1.0000 |
| `no_vision` | 130 | 1.0000 |
| `no_proprio` | 48 | 1.0000 |

Interpretation: the current morphology boundary is highly rule-separable. This is useful for shadow scoring and residual-window selection, but it is not evidence that a learned action policy is solved.

## Fresh Shadow Evaluation

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_12b_morphology_quality_shadow_v0.py --trials-per-candidate 12 --seed 20260617 --candidate baseline_di --candidate lift_ls460
```

Result:

- Episodes: `24`
- Success: `18 / 24`
- Terminal reasons: `18` success, `5` contact gate failed, `1` true-pinch morphology gate failed
- Shadow evidence frames: `10801`

Shadow metrics:

| label | F1 | fp | fn |
|---|---:|---:|---:|
| `morphology_clean_now` | 0.9999 | 0 | 1 |
| `good_two_tip_now` | 0.9996 | 3 | 4 |
| `low_non_tip_now` | 0.9995 | 0 | 8 |
| `wrap_now` | 0.9983 | 7 | 0 |
| `floor_contact_now` | 1.0000 | 0 | 0 |
| `lift_quality_now` | 0.9991 | 11 | 2 |
| `future_success` | 0.9466 | 456 | 518 |
| `penetration_risk_now` | 0.0000 | 80 | 71 |

Candidate slices:

| candidate | episodes | success | morphology-clean F1 | future-success F1 |
|---|---:|---:|---:|---:|
| `baseline_di` | 12 | 8 | 1.0000 | 0.9130 |
| `lift_ls460` | 12 | 10 | 0.9999 | 0.9734 |

## Decision

Promote Stage3.12B as a diagnostic/shadow quality asset, not as a control policy.

Use `morphology_clean_now`, `good_two_tip_now`, `low_non_tip_now`, `wrap_now`, `floor_contact_now`, and `lift_quality_now` as high-confidence shadow signals. Do not use `penetration_risk_now` as a primary trigger until more positive examples exist.

Do not promote `lift_ls460` from this result. It remains a diagnostic candidate only; the earlier Stage3.12A multiseed gate still blocks it because it introduced morphology failures.

## Next

Stage3.12C should design a bounded residual teacher using high-confidence low-quality windows from the Stage3.12B shadow head:

- first run shadow-window mining on D-I and `lift_ls460`;
- propose 2-4 residual teacher variants only where the head predicts low morphology quality;
- run a small smoke gate before any 50-trial validation;
- promote only if the same multiseed gate beats frozen D-I without increasing true-pinch morphology failures.

If the residual teacher only shifts failures between lift/contact/morphology, keep D-I frozen and move to better morphology coverage or contact-geometry modeling instead of continuing parameter tuning.
