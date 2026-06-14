# Stage3.11D-E Lift Quality Shadow v0

Generated: `2026-06-12T14:35:43`

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
- Trials: `50`
- Dense trace sample every: `1`

## Online Trial Summary

- Event controller success: `43 / 50` (`0.860`)
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 43, 'lift_gate_failed': 5, 'true_pinch_morphology_gate_failed': 1, 'contact_gate_failed': 1}`
- Trace rows all/evidence: `81545` / `27495`
- Shadow gate passed: `False` (min label F1 `0.995`)

## Evidence-Phase Shadow Metrics

| label | accuracy | precision | recall | F1 | positives | tp | fp | fn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `lift_quality_now` | 0.9987 | 0.9985 | 0.9999 | 0.9992 | 0.7918 | 21767 | 32 | 3 |
| `adjust_needed_now` | 0.9987 | 0.9993 | 0.9944 | 0.9968 | 0.2082 | 5693 | 4 | 32 |
| `hold_safe_now` | 0.9987 | 0.9863 | 1.0000 | 0.9931 | 0.0943 | 2593 | 36 | 0 |

## Failure Detection Diagnostics

- Failed episodes: `7`
- Failed episodes with predicted `adjust_needed_now`: `7 / 7`
- Failed episodes without predicted `adjust_needed_now`: `0 / 7`
- Successful episodes with predicted `hold_safe_now`: `43 / 43`

## False Windows

| label | type | phase | terminal reason | windows |
|---|---|---|---|---:|
| `lift_quality_now` | `fp` | `hold` | `success_event_contact_gated_true_pinch_release_ball` | 5 |
| `adjust_needed_now` | `fn` | `hold` | `success_event_contact_gated_true_pinch_release_ball` | 5 |
| `adjust_needed_now` | `fp` | `hold` | `success_event_contact_gated_true_pinch_release_ball` | 4 |
| `lift_quality_now` | `fn` | `hold` | `success_event_contact_gated_true_pinch_release_ball` | 3 |
| `hold_safe_now` | `fp` | `hold` | `success_event_contact_gated_true_pinch_release_ball` | 2 |

## Largest False Windows

| episode | label | type | steps | rows | phases | prob mean | terminal reason |
|---:|---|---|---|---:|---|---:|---|
| 28 | `lift_quality_now` | `fp` | 968-987 | 20 | `hold->hold` | 0.7645 | `success_event_contact_gated_true_pinch_release_ball` |
| 28 | `adjust_needed_now` | `fn` | 968-987 | 20 | `hold->hold` | 0.2222 | `success_event_contact_gated_true_pinch_release_ball` |
| 28 | `hold_safe_now` | `fp` | 968-987 | 20 | `hold->hold` | 0.9857 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `hold_safe_now` | `fp` | 1038-1053 | 16 | `hold->hold` | 0.9711 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `lift_quality_now` | `fp` | 1038-1045 | 8 | `hold->hold` | 0.7106 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `adjust_needed_now` | `fn` | 1038-1045 | 8 | `hold->hold` | 0.2941 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `lift_quality_now` | `fp` | 1050-1051 | 2 | `hold->hold` | 0.5736 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `adjust_needed_now` | `fn` | 1050-1051 | 2 | `hold->hold` | 0.4544 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `lift_quality_now` | `fp` | 1047-1047 | 1 | `hold->hold` | 0.5640 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `adjust_needed_now` | `fn` | 1047-1047 | 1 | `hold->hold` | 0.4576 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `lift_quality_now` | `fp` | 1053-1053 | 1 | `hold->hold` | 0.5785 | `success_event_contact_gated_true_pinch_release_ball` |
| 16 | `adjust_needed_now` | `fn` | 1053-1053 | 1 | `hold->hold` | 0.4515 | `success_event_contact_gated_true_pinch_release_ball` |

## Next

- If this shadow pass is clean, use the same online frames to build a bounded residual micro-adjust teacher.
- If false windows cluster in one phase, fix labels/features or add targeted data before allowing the head to affect control.
