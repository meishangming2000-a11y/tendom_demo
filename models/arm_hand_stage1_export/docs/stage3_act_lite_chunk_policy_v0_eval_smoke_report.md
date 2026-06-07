# Stage3 ACT-lite Chunk Policy v0 Closed-loop Eval Report

- Generated: `2026-06-07T09:59:43`
- Status: `PASS`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v0.pth`
- Execution mode: `scripted_arm_predicted_hand`
- Replan interval: `1`
- Episodes: `2 / 2` success
- Training status: `stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- Boundary: this is a MuJoCo closed-loop eval, not hardware integration.

## Skill Summary

| skill | success | terminal reasons | failures | risks |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 1 / 1 | `{'success_gentle_grasp_hold': 1}` | `{}` | `{'early_contact_in_approach': 1, 'transient_or_hold_slip': 1}` |
| `thumb_index_middle_pinch` | 1 / 1 | `{'success_vision_confirmed_pinch_lift_hold': 1}` | `{}` | `{'early_contact_in_approach': 1, 'transient_slip_high': 1}` |

## Episodes

| ep | skill | trial | status | reason | lift | hold stable | hold slip | max slip | failures |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0995 | 1.000 | 0.141 | 1.000 | `[]` |
| 1 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1016 | 1.000 | 0.161 | 1.000 | `[]` |

## Interpretation

- `full_action` tests whether the learned chunk policy can directly control all actuators.
- `scripted_arm_predicted_hand` keeps the visual-guided arm/wrist scaffold and tests learned chunk control over the hand/fingers.
- Promotion requires matching or beating scripted SkillZoo baselines on success, slip, crush, penetration, and floor contact.

## 如果成功

Run more trials and compare against Stage3.7D / Stage3.8B scripted baselines before promoting the policy.

## 如果失败

Inspect whether failure comes from approach alignment, contact acquisition, hand closure, lift/hold slip, or final vision. Then decide between hybrid execution, phase-specific heads, or retraining with a different horizon.
