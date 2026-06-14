# Stage3.11D-E Lift Quality Shadow v0

Generated: `2026-06-12T14:23:24`

## Boundary

- MuJoCo-only online shadow evaluation.
- Loads the Stage3.11D-D LiftQualityHead checkpoint and predicts on dense event-runner trace frames.
- The shadow head does not change actions, timing, force gates, or release logic.
- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.
- No full-action ACT/DP, hardware runtime, or demo-gallery promotion is made here.

## Inputs

- Selected center: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_11d_c_geometry_force_refine_selected_v0.json`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_11d_d_lift_quality_head_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Trials: `8`
- Dense trace sample every: `1`

## Online Trial Summary

- Event controller success: `7 / 8` (`0.875`)
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 7, 'lift_gate_failed': 1}`
- Trace rows all/evidence: `13055` / `4407`
- Shadow gate passed: `True` (min label F1 `0.995`)

## Evidence-Phase Shadow Metrics

| label | accuracy | precision | recall | F1 | positives | tp | fp | fn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `lift_quality_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8021 | 3535 | 0 | 0 |
| `adjust_needed_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.1979 | 872 | 0 | 0 |
| `hold_safe_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0969 | 427 | 0 | 0 |

## Failure Detection Diagnostics

- Failed episodes: `1`
- Failed episodes with predicted `adjust_needed_now`: `1 / 1`
- Failed episodes without predicted `adjust_needed_now`: `0 / 1`
- Successful episodes with predicted `hold_safe_now`: `7 / 7`

## False Windows

- No false-positive or false-negative windows on evidence phases.

## Next

- If this shadow pass is clean, use the same online frames to build a bounded residual micro-adjust teacher.
- If false windows cluster in one phase, fix labels/features or add targeted data before allowing the head to affect control.
