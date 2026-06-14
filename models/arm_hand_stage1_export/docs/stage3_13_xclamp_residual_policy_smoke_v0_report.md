# Stage3.13 X-Clamp Residual Policy v0

Generated: `2026-06-14T01:51:12`

## Boundary

- MuJoCo-only teacher distillation from Stage3.12C x-clamp.
- Action surface is a bounded grasp-x residual before IK, not full-action control.
- The learned policy is evaluated with a safety clamp around the Stage3.12C corridor.
- No hardware runtime, real camera, real tactile, demo-gallery, or full-action ACT/DP promotion.

## Dataset

- Episodes: `32`
- Residual-active labels: `9` (`0.281`)
- Mean/max |target residual|: `0.000112` / `0.000883 m`

## Training

- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_13_xclamp_residual_policy_smoke_v0.pth`
- Val MAE: `0.00007332 m`
- Val max abs error: `0.00015917 m`

## Closed-Loop Gate

| mode | success | contact | lift | true pinch | release | hold non-tip | wrap | residual active | clip fraction | reasons |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline_di` | 8/8 | 8 | 8 | 8 | 8 | 0.163 | 0.000 | 0.000 | 0.000 | `{'success_event_contact_gated_true_pinch_release_ball': 8}` |
| `teacher_xclamp` | 8/8 | 8 | 8 | 8 | 8 | 0.096 | 0.000 | 0.375 | 0.000 | `{'success_event_contact_gated_true_pinch_release_ball': 8}` |
| `learned_xresidual_safe` | 8/8 | 8 | 8 | 8 | 8 | 0.099 | 0.000 | 1.000 | 0.250 | `{'success_event_contact_gated_true_pinch_release_ball': 8}` |

## Decision

- Status: `advance_distilled_policy_candidate`
- The learned bounded residual policy matched or beat the Stage3.12C teacher on the matched gate without adding true-pinch morphology failures.
- Learned vs D-I success delta: `0`
- Learned vs teacher success delta: `0`
- True-pinch morphology failures added vs teacher: `0`

## Next

- If success: use this as Stage3.13A distilled residual-policy candidate and broaden to contact/lift windows only after preserving this matched gate.
- If failure: keep Stage3.12C teacher primary, inspect residual prediction errors, and avoid returning to open-ended D-I parameter tuning.

## Artifacts

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_13_xclamp_residual_policy_smoke_v0.npz`
- JSONL: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_13_xclamp_residual_policy_smoke_v0.jsonl`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_13_xclamp_residual_policy_smoke_v0.pth`
- Summary CSV: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_13_xclamp_residual_policy_smoke_v0_summary.csv`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_13_xclamp_residual_policy_smoke_v0.json`
