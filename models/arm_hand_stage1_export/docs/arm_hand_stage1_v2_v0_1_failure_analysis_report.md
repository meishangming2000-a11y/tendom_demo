# Arm-Hand Stage1 V2 V0.1 Failure Analysis

Generated: 2026-05-30T01:32:39

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Eval metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_bc_v0_1_obs_phase_strongreg_smooth_eval.json`
- Eval success count: `69 / 75`
- Failed episodes: `6`
- Failed reasons: `{'timeout': 6}`
- Failed profile counts: `{'clean_nominal': 2, 'mild_fast_jitter': 2, 'mild_slow_jitter': 2}`
- Dataset terminal reason counts: `{'success_lift_ball': 68, 'timeout': 7}`
- Training ready: **No, diagnostic only**

## Failed Offsets

| offset xyz | count | profiles | episodes | reasons |
|---|---:|---|---|---|
| `[0.02, -0.01, 0.0]` | 3 | clean_nominal, mild_fast_jitter, mild_slow_jitter | [9, 34, 59] | {'timeout': 3} |
| `[0.02, 0.02, 0.0]` | 3 | clean_nominal, mild_fast_jitter, mild_slow_jitter | [24, 49, 74] | {'timeout': 3} |

## Failed Episodes

| ep | profile | offset xyz | eval reason | dataset reason | steps | lift m | hand contacts | floor contacts | max pen m |
|---:|---|---|---|---|---:|---:|---:|---:|---:|
| 9 | clean_nominal | `[0.02, -0.01, 0.0]` | timeout | success_lift_ball | 1300 | -0.000184 | 0 | 1 | 0.000184 |
| 24 | clean_nominal | `[0.02, 0.02, 0.0]` | timeout | timeout | 1300 | -0.000184 | 0 | 1 | 0.000184 |
| 34 | mild_fast_jitter | `[0.02, -0.01, 0.0]` | timeout | success_lift_ball | 1300 | -0.000184 | 0 | 1 | 0.000184 |
| 49 | mild_fast_jitter | `[0.02, 0.02, 0.0]` | timeout | timeout | 1300 | -0.000184 | 0 | 1 | 0.000184 |
| 59 | mild_slow_jitter | `[0.02, -0.01, 0.0]` | timeout | timeout | 1300 | -0.000184 | 0 | 1 | 0.000184 |
| 74 | mild_slow_jitter | `[0.02, 0.02, 0.0]` | timeout | success_lift_ball | 1300 | -0.000184 | 0 | 1 | 0.000184 |

## Diagnosis

The retained obs+phase v0.1 failures cluster on the right-edge ball offsets. Final states show near-zero lift and zero ball-hand contacts, so the main gap is approach/closure coverage at the right boundary rather than lift-after-contact stability.

## Recommended V0.2 Recovery Offsets

- `[0.02, -0.01, 0.0]`
- `[0.02, 0.02, 0.0]`
- `[0.02, -0.015, 0.0]`
- `[0.02, -0.005, 0.0]`
- `[0.02, 0.015, 0.0]`
- `[0.02, 0.025, 0.0]`
