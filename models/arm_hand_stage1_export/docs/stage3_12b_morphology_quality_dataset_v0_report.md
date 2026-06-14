# Stage3.12B Morphology Quality Dataset v0

Generated: `2026-06-13T12:51:34`

## Boundary

- MuJoCo-only dense data capture for morphology/quality labels.
- Captures virtual vision, synthetic contact/tactile morphology, simulated motor force feedback, proprioception, actions, phase, and outcome labels.
- Morphology truth is supervision for simulation training/evaluation, not a real hardware sensor claim.
- No controller, demo-gallery, full-action ACT/DP, or hardware-runtime promotion is made here.

## Outputs

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_12b_morphology_quality_dataset_v0.npz`
- JSONL episode summaries: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_12b_morphology_quality_dataset_v0.jsonl`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_12b_morphology_quality_dataset_v0.json`

## Summary

- Candidates: `['baseline_di', 'lift_ls460']`
- Episodes: `60`
- Success: `50 / 60` (`0.833`)
- Dense rows: `94586`; mean/min/max rows per episode: `1576.4` / `1301` / `1747`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 50, 'true_pinch_morphology_gate_failed': 2, 'contact_gate_failed': 6, 'lift_gate_failed': 2}`

## Candidate Breakdown

| candidate | episodes | rows | success | contact | lift | true pinch | release | hold two-tip | hold non-tip | hold wrap | reasons |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline_di` | 30 | 48000 | 25 | 28 | 27 | 25 | 30 | 0.838 | 0.050 | 0.000 | `{'success_event_contact_gated_true_pinch_release_ball': 25, 'true_pinch_morphology_gate_failed': 2, 'contact_gate_failed': 2, 'lift_gate_failed': 1}` |
| `lift_ls460` | 30 | 46586 | 25 | 26 | 25 | 25 | 29 | 0.833 | 0.090 | 0.000 | `{'success_event_contact_gated_true_pinch_release_ball': 25, 'contact_gate_failed': 4, 'lift_gate_failed': 1}` |

## Label Means

- `lift_quality_now`: `0.2326`
- `future_success`: `0.8459`
- `adjust_needed_now`: `0.0817`
- `good_two_tip_now`: `0.2689`
- `wrap_now`: `0.0528`
- `floor_contact_now`: `0.6585`
- `low_force_now`: `0.4309`
- `force_imbalance_now`: `0.0006`
- `force_saturation_now`: `0.0000`
- `penetration_risk_now`: `0.0012`
- `hold_safe_now`: `0.0322`
- `release_phase_now`: `0.3812`

## Next

- Train the Stage3.12B morphology-quality head on grasp-evidence phases.
- Use the trained head as a shadow quality scorer before any bounded residual intervention.
