# Arm-Hand Stage1 V2 BC V0.4 Hold Validation Report

Generated: 2026-05-31

- Scope: extend the v0.4 obs+phase BC smoke rollout from "lift reached" to "lift then hold".
- Status: **PASS on v0.1 and v0.2 reset sets with hold controller, experimental smoke only**.
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Hold controller: after first lift success, allow `180` settle steps, then freeze the best settle-window action and require `900` consecutive hold steps.
- Hold height floor: `0.070 m` during the counted hold window.
- Training ready: **No, experimental BC smoke only**

## Hold Eval

| eval set | success | terminal reasons | final lift range m | report |
|---|---:|---|---:|---|
| v0.2 recovery set | `87 / 87` | `{'success_lift_hold': 87}` | `0.077342` to `0.093798` | `docs/arm_hand_stage1_v2_bc_v0_4_freeze_settle180_hold900_min070_recover_on_v0_2_eval_report.md` |
| v0.1 reset set | `75 / 75` | `{'success_lift_hold': 75}` | `0.077501` to `0.093798` | `docs/arm_hand_stage1_v2_bc_v0_4_freeze_settle180_hold900_min070_recover_on_v0_1_eval_report.md` |

## Demo

- Dataset: v0.2
- Episode: `25`
- Offset: `[0.02, -0.015, 0.0]`
- Result: `success_lift_hold`
- Frames: `537`
- Final lift: `0.079840 m`
- Ball-hand contacts: `7`
- Ball-floor contacts after lift: `0`
- Max penetration after success: `0.002634 m`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_hold\obs_phase_weighted_transition_ep25_freeze_settle180_hold900_demo.mp4`

## Interpretation

The original short eval stopped as soon as the ball reached the lift success threshold, so it did not prove that the ball stayed held. This validation adds a longer post-success hold window and a simple hold controller. The controller avoids continued BC oscillation after lift by freezing the best action seen during a short settling window.

This improves the demo/eval answer to "does it stay held?" on the current accepted reset sets. It still does not promote the checkpoint to a maintained baseline, because collision proxy v2 is smoke geometry and the reset coverage is not yet an unseen holdout distribution.

## Next Step

Run an unseen holdout sweep around `x=0.01..0.02`, `y=0.005..0.02` with the same hold controller. Only consider RL warm-start after that holdout passes.
