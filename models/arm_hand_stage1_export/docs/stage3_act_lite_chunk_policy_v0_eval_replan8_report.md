# Stage3 ACT-lite Chunk Policy v0 Closed-loop Eval Report

- Generated: `2026-06-07T10:01:48`
- Status: `PASS`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v0.pth`
- Execution mode: `scripted_arm_predicted_hand`
- Replan interval: `8`
- Episodes: `6 / 6` success
- Training status: `stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- Boundary: this is a MuJoCo closed-loop eval, not hardware integration.

## Skill Summary

| skill | success | terminal reasons | failures | risks |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 3 / 3 | `{'success_gentle_grasp_hold': 3}` | `{}` | `{'early_contact_in_approach': 3, 'transient_or_hold_slip': 3}` |
| `thumb_index_middle_pinch` | 3 / 3 | `{'success_vision_confirmed_pinch_lift_hold': 3}` | `{}` | `{'early_contact_in_approach': 3, 'transient_slip_high': 3}` |

## Episodes

| ep | skill | trial | status | reason | lift | hold stable | hold slip | max slip | failures |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1002 | 1.000 | 0.162 | 0.628 | `[]` |
| 1 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1026 | 1.000 | 0.159 | 0.560 | `[]` |
| 2 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1115 | 1.000 | 0.191 | 0.629 | `[]` |
| 3 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1028 | 1.000 | 0.209 | 1.000 | `[]` |
| 4 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1020 | 1.000 | 0.252 | 1.000 | `[]` |
| 5 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1145 | 1.000 | 0.212 | 1.000 | `[]` |

## Interpretation

- `full_action` tests whether the learned chunk policy can directly control all actuators.
- `scripted_arm_predicted_hand` keeps the visual-guided arm/wrist scaffold and tests learned chunk control over the hand/fingers.
- Promotion requires matching or beating scripted SkillZoo baselines on success, slip, crush, penetration, and floor contact.

## 如果成功

Run more trials and compare against Stage3.7D / Stage3.8B scripted baselines before promoting the policy.

## 如果失败

Inspect whether failure comes from approach alignment, contact acquisition, hand closure, lift/hold slip, or final vision. Then decide between hybrid execution, phase-specific heads, or retraining with a different horizon.
