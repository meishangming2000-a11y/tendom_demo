# Arm-Hand Stage1 V2 BC V0.1 Obs+Phase Repair Report

Generated: 2026-05-30

- Scope: expand dataset v0.1 and retry observation+phase BC.
- Status: **PARTIAL, improved to phase-only reference ceiling**
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Dataset report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_report.md`
- Dataset replay QA: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_replay_report.md`
- Final obs+phase checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth`
- Final obs+phase eval: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_1_obs_phase_strongreg_smooth_eval_report.md`
- Final demo video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_1_obs_phase\obs_phase_strongreg_policy_demo.mp4`

## Dataset V0.1

- Episodes: `75`
- Rows: `77154`
- Observation dim: `124`
- Action dim: `26`
- Ball offsets: x/y `[-0.02, -0.01, 0.0, 0.01, 0.02]`, z `[0.0]`
- Behavior profiles: `clean_nominal`, `mild_fast_jitter`, `mild_slow_jitter`
- Dataset behavior success: `68 / 75`
- Terminal reasons: `{'success_lift_ball': 68, 'timeout': 7}`
- Replay QA: `PASS`, max obs/next_obs/reward error `0`

Rows preserve two action fields:

- `actions`: behavior action actually applied in MuJoCo, used for replay QA.
- `expert_actions`: scripted recovery target, used as the BC label.

## Obs+Phase Attempts

| attempt | feature mode | training target | repair | online result |
|---|---|---|---|
| v0.1 raw | `obs_phase` | `expert_actions` | none | `18 / 75` |
| v0.1 regularized | `obs_phase` | `expert_actions` | obs noise `0.15`, obs dropout `0.25` | `51 / 75` |
| v0.1 strongreg + smoothing | `obs_phase` | `expert_actions` | obs noise `0.30`, obs dropout `0.60`, online smoothing `0.2` | `69 / 75` |
| v0 phase-only reference on v0.1 resets | `phase_only` | previous v0 checkpoint | reference only | `69 / 75` |

## Final Result

- Final selected policy: obs+phase strong regularization with online action smoothing.
- Feature mode: `obs_phase`
- Training target: `expert_actions`
- Final val MSE normalized: about `1.42e-4`
- Raw val action RMSE: about `0.00659`
- Online eval: `69 / 75` success
- Remaining failures: `6` timeout cases
- Lift range: about `-0.00018 m` to `0.08052 m`
- Demo episode 12: success, lift about `0.08050 m`, video rendered.

## Interpretation

- Dataset v0.1 materially improves obs+phase BC: v0 first attempt was `0 / 9`; v0.1 raw obs+phase reached `18 / 75`; strong regularization plus smoothing reached `69 / 75`.
- The remaining `6 / 75` failures match the phase-only reference on the same v0.1 reset set, suggesting the residual limit is now mostly the scripted trajectory and wide-offset task boundary rather than obs+phase policy collapse.
- This is still an experimental smoke policy, not a promoted manipulation baseline.

## Next Step

For v0.2, do not just add more BC epochs. Improve the data/task boundary: either narrow the accepted training reset region to the 69/75 success subset, or add recovery demonstrations for the 6 timeout offsets before attempting promotion.
