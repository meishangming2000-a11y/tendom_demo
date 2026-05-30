# Arm-Hand Stage1 V2 BC V0.3 Obs+Phase Training Report

Generated: 2026-05-30

- Scope: continue obs+phase BC training after dataset v0.2.
- Status: **PARTIAL, improved v0.2 recovery-set score but not promoted**.
- Selected checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth`
- Training dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Selected feature mode: `obs_phase`
- Selected weighting: samples with `x >= 0.018` and `y >= 0.015` weighted by `6.0`
- Selected rollout setting: action smoothing `0.5`
- Training ready: **No, experimental BC smoke only**

## Attempts

| attempt | outcome | retained |
|---|---|---:|
| v0.3 dense upper-right dataset | behavior collection was only `129 / 141`; rejected because expert labels were not clean | no |
| `obs_phase_offset` | offline RMSE improved, but online regressed to at best `75 / 87` on v0.2 and `66 / 75` on v0.1 | no |
| weighted right-edge `y >= 0.01` | over-weighted right side and regressed to `66 / 87` on v0.2 and `54 / 75` on v0.1 | no |
| weighted upper-right `y >= 0.015` | improved v0.2 recovery set to `84 / 87` and kept v0.1 at `72 / 75` | yes |

## Selected Training

- Epochs: `120`
- Hidden dim/depth: `256 / 3`
- Normalized obs noise std: `0.12`
- Obs dropout prob: `0.20`
- Upper-right sample weight: `6.0`
- Upper-right train samples: `8037`
- Final train normalized MSE: `6.573866e-05`
- Final val normalized MSE: `4.268441e-05`
- Val action RMSE raw units: `0.00403975`

## Selected Online Eval

| eval set | success | terminal reasons | mean lift m | report |
|---|---:|---|---:|---|
| v0.2 recovery set | `84 / 87` | `{'success_lift_ball': 84, 'timeout': 3}` | `0.077614` | `docs/arm_hand_stage1_v2_bc_v0_3_obs_phase_weighted_upperright_on_v0_2_smooth050_eval_report.md` |
| v0.1 reset set | `72 / 75` | `{'success_lift_ball': 72, 'timeout': 3}` | `0.077179` | `docs/arm_hand_stage1_v2_bc_v0_3_obs_phase_weighted_upperright_on_v0_1_smooth050_eval_report.md` |

Compared with the selected v0.2 policy, v0.3 improves the v0.2 recovery-set score from `81 / 87` to `84 / 87` while preserving the old v0.1 reset-set score at `72 / 75`.

## Demo

Recovered demo from a v0.2-selected failure case:

- Dataset: v0.1
- Episode: `24`
- Offset: `[0.02, 0.02, 0.0]`
- Result: `success_lift_ball`
- Frames: `268`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_3_obs_phase\obs_phase_weighted_upperright_recovered_ep24_demo.mp4`

## Remaining Gap

The selected `0.5` smoothing eval leaves the remaining failures at `[0.01, 0.01, 0.0]` across the three behavior profiles. A `0.4` smoothing check kept the same total success count but left failures at `[0.02, 0.01, 0.0]`. So the right-upper cluster is improved, but the right-side transition band is still thin.

## Next Step

For the next training pass, prefer clean data or sampling around the transition band `[0.01..0.02, 0.01, 0.0]`. Do not move to RL yet; the remaining failures are still no-contact timeout cases, so BC/data coverage is the right next lever.
