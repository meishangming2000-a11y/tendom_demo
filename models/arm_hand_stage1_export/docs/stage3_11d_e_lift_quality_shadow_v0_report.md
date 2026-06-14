# Stage3.11D-E Lift Quality Shadow v0

Generated: `2026-06-12T14:25:18`

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

- Event controller success: `36 / 50` (`0.720`)
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 36, 'lift_gate_failed': 11, 'contact_gate_failed': 3}`
- Trace rows all/evidence: `82154` / `28104`
- Shadow gate passed: `True` (min label F1 `0.995`)

## Evidence-Phase Shadow Metrics

| label | accuracy | precision | recall | F1 | positives | tp | fp | fn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `lift_quality_now` | 0.9989 | 0.9988 | 0.9997 | 0.9992 | 0.6994 | 19650 | 24 | 6 |
| `adjust_needed_now` | 0.9988 | 0.9983 | 0.9978 | 0.9980 | 0.3006 | 8429 | 14 | 19 |
| `hold_safe_now` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0781 | 2196 | 0 | 0 |

## Failure Detection Diagnostics

- Failed episodes: `14`
- Failed episodes with predicted `adjust_needed_now`: `14 / 14`
- Failed episodes without predicted `adjust_needed_now`: `0 / 14`
- Successful episodes with predicted `hold_safe_now`: `36 / 36`

## False Windows

| label | type | phase | terminal reason | windows |
|---|---|---|---|---:|
| `lift_quality_now` | `fp` | `slow_lift` | `lift_gate_failed` | 8 |
| `adjust_needed_now` | `fn` | `slow_lift` | `lift_gate_failed` | 4 |
| `lift_quality_now` | `fn` | `slow_lift` | `lift_gate_failed` | 4 |
| `adjust_needed_now` | `fp` | `slow_lift` | `lift_gate_failed` | 3 |

## Largest False Windows

| episode | label | type | steps | rows | phases | prob mean | terminal reason |
|---:|---|---|---|---:|---|---:|---|
| 47 | `adjust_needed_now` | `fp` | 687-698 | 12 | `slow_lift->slow_lift` | 0.5629 | `lift_gate_failed` |
| 43 | `lift_quality_now` | `fp` | 840-848 | 9 | `slow_lift->slow_lift` | 0.7216 | `lift_gate_failed` |
| 43 | `adjust_needed_now` | `fn` | 841-848 | 8 | `slow_lift->slow_lift` | 0.2688 | `lift_gate_failed` |
| 16 | `lift_quality_now` | `fp` | 976-980 | 5 | `slow_lift->slow_lift` | 0.9952 | `lift_gate_failed` |
| 16 | `adjust_needed_now` | `fn` | 976-980 | 5 | `slow_lift->slow_lift` | 0.0025 | `lift_gate_failed` |
| 43 | `lift_quality_now` | `fp` | 804-808 | 5 | `slow_lift->slow_lift` | 0.6793 | `lift_gate_failed` |
| 43 | `adjust_needed_now` | `fn` | 804-808 | 5 | `slow_lift->slow_lift` | 0.3694 | `lift_gate_failed` |
| 47 | `lift_quality_now` | `fn` | 691-693 | 3 | `slow_lift->slow_lift` | 0.4663 | `lift_gate_failed` |
| 43 | `lift_quality_now` | `fn` | 676-676 | 1 | `slow_lift->slow_lift` | 0.3648 | `lift_gate_failed` |
| 43 | `adjust_needed_now` | `fp` | 676-676 | 1 | `slow_lift->slow_lift` | 0.7090 | `lift_gate_failed` |
| 43 | `lift_quality_now` | `fp` | 680-680 | 1 | `slow_lift->slow_lift` | 0.6396 | `lift_gate_failed` |
| 43 | `adjust_needed_now` | `fn` | 680-680 | 1 | `slow_lift->slow_lift` | 0.3679 | `lift_gate_failed` |

## Next

- If this shadow pass is clean, use the same online frames to build a bounded residual micro-adjust teacher.
- If false windows cluster in one phase, fix labels/features or add targeted data before allowing the head to affect control.
