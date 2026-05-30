# Arm-Hand Stage1 V2 BC V0.4 Obs+Phase Training Report

Generated: 2026-05-30

- Scope: continue obs+phase BC training after v0.3 by targeting the transition-band timeout cluster.
- Status: **PASS on v0.1 and v0.2 reset sets, experimental smoke only**.
- Selected checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Training dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Selected feature mode: `obs_phase`
- Selected rollout setting: action smoothing `0.5`
- Training ready: **No, experimental BC smoke only**

## Training

- Epochs: `120`
- Hidden dim/depth: `256 / 3`
- Normalized obs noise std: `0.12`
- Obs dropout prob: `0.20`
- Upper-right sample region: `x >= 0.018`, `y >= 0.015`, weight `6.0`
- Transition-band sample region: `0.008 <= x <= 0.012`, `0.008 <= y <= 0.012`, weight `6.0`
- Upper-right train samples: `6007`
- Transition-band train samples: `3016`
- Final train normalized MSE: `9.336687e-05`
- Final val normalized MSE: `6.606528e-05`
- Val action RMSE raw units: `0.00400155`

## Online Eval

| eval set | success | terminal reasons | mean lift m | report |
|---|---:|---|---:|---|
| v0.2 recovery set | `87 / 87` | `{'success_lift_ball': 87}` | `0.080421` | `docs/arm_hand_stage1_v2_bc_v0_4_obs_phase_weighted_upperright_transition_on_v0_2_smooth050_eval_report.md` |
| v0.1 reset set | `75 / 75` | `{'success_lift_ball': 75}` | `0.080432` | `docs/arm_hand_stage1_v2_bc_v0_4_obs_phase_weighted_upperright_transition_on_v0_1_smooth050_eval_report.md` |

Compared with v0.3, the selected v0.4 policy improves:

- v0.2 recovery set: `84 / 87` -> `87 / 87`
- v0.1 reset set: `72 / 75` -> `75 / 75`

## Demo

Recovered demo from the v0.3 transition-band failure:

- Dataset: v0.1
- Episode: `18`
- Offset: `[0.01, 0.01, 0.0]`
- Result: `success_lift_ball`
- Frames: `262`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_obs_phase\obs_phase_weighted_transition_recovered_ep18_demo.mp4`

## Interpretation

This is the strongest BC smoke result so far on the current accepted reset sets. It should still not be promoted to a maintained baseline until it passes an unseen reset sweep and visual spot checks across boundary cases. RL remains blocked until that broader validation is accepted.

## Next Step

Run a small unseen holdout sweep around the accepted region, especially between `x=0.01..0.02` and `y=0.005..0.02`. If the holdout passes, this checkpoint can become the candidate warm-start for later RL smoke work.
