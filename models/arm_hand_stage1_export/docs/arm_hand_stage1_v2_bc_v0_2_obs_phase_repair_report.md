# Arm-Hand Stage1 V2 BC V0.2 Obs+Phase Recovery Report

Generated: 2026-05-30

- Scope: targeted right-edge recovery after dataset v0.1 obs+phase timeouts.
- Status: **PARTIAL, improved on the v0.1 reset set but not promoted**.
- Selected checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth`
- Selected dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Selected rollout setting: `obs_phase`, `expert_actions`, action smoothing `0.4`, CPU.
- Training ready: **No, experimental BC smoke only**.

## Failure Diagnosis

The v0.1 selected obs+phase policy had `69 / 75` online success. The six failures clustered on right-edge offsets and finished as timeout with near-zero lift and zero ball-hand contacts. The diagnostic report is:

`D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_v0_1_failure_analysis_report.md`

## Dataset V0.2

- Collection script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_2.py`
- Episodes: `87`
- Rows: `87773`
- Behavior success: `87 / 87`
- Terminal reasons: `{'success_lift_ball': 87}`
- Replay QA: `PASS`
- Max replay errors: obs `0.0`, next_obs `0.0`, reward `0.0`
- Training readiness: `PASS`
- Recovery mode counts: `{'nominal': 63, 'right_edge_mid_y': 15, 'right_edge_high_y': 6, 'right_edge_upper_y': 3}`

V0.2 keeps the v0.1 5x5 reset grid and adds a small right-edge recovery neighborhood around `x=0.02`. The recovery modes adjust the scripted arm approach only for the timeout cluster; `actions` remain the applied replay actions and `expert_actions` remain the BC labels.

## Training And Eval

Selected training:

- Feature mode: `obs_phase`
- Action field: `expert_actions`
- Hidden dim/depth: `256 / 3`
- Epochs: `120`
- Normalized obs noise std: `0.12`
- Obs dropout prob: `0.20`
- Final train normalized MSE: `5.084956e-05`
- Final val normalized MSE: `3.500831e-05`
- Val action RMSE raw units: `0.00325758`

Selected online eval:

| eval set | success | terminal reasons | mean lift m | report |
|---|---:|---|---:|---|
| v0.2 recovery set | `81 / 87` | `{'success_lift_ball': 81, 'timeout': 6}` | `0.074824` | `docs/arm_hand_stage1_v2_bc_v0_2_obs_phase_moderatereg_smooth040_eval_report.md` |
| v0.1 reset set | `72 / 75` | `{'success_lift_ball': 72, 'timeout': 3}` | `0.077147` | `docs/arm_hand_stage1_v2_bc_v0_2_obs_phase_moderatereg_on_v0_1_smooth040_eval_report.md` |

The v0.1 reset score improved from `69 / 75` to `72 / 75`. The v0.2 score is lower because it includes the added upper-right recovery offsets.

## Attempt Notes

- Strong regularization reproduced worse online behavior on v0.2 (`54 / 87`) and caused many `floor_contact_after_lift` failures.
- Low regularization overfit the recovery branch and regressed the old reset set.
- A wider moderate model matched the selected score (`81 / 87` on v0.2 and `72 / 75` on v0.1) but was larger, so the smaller moderate checkpoint was retained.

Only selected artifacts are retained in the repo; intermediate attempt checkpoints/reports were removed to avoid artifact clutter.

## Demo

Recovered demo from an old v0.1 failure case:

- Dataset: v0.1
- Episode: `9`
- Offset: `[0.02, -0.01, 0.0]`
- Result: `success_lift_ball`
- Frames: `263`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_2_obs_phase\obs_phase_moderatereg_recovered_ep09_demo.mp4`

## Remaining Gap

The remaining selected failures are still cleanly localized:

- v0.1 remaining failures: `[0.02, 0.02, 0.0]` across all three behavior profiles.
- v0.2 remaining failures: `[0.02, 0.02, 0.0]` and `[0.02, 0.025, 0.0]` across all three behavior profiles.

These failures again end as timeout with zero ball-hand contacts, so the next fix should target the upper-right approach/closure branch rather than lift stability.

## Next Step

For v0.3, either:

1. add heavier upper-right recovery coverage and/or weighted sampling for `[0.02, 0.02..0.025, 0.0]`, or
2. add explicit reset-offset/initial-ball features to the policy input so obs+phase can separate the right-edge recovery branch more reliably.

Keep RL blocked until this upper-right reset cluster is either solved or explicitly excluded from the accepted reset region.
