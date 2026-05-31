# Arm-Hand Stage1 V3 Pick-Place Scripted Demo Report

Generated: 2026-05-31T21:25:42

- Status: **PASS**
- Terminal reason: `success_pick_place_ball`
- Task: `arm_hand_stage1_pick_place_ball`
- Contract: `stage2_pick_place_v0_1`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_demo.xml`
- Mode: `pure_physics_scripted_same_platform`
- Training used: **No**
- Dataset ready: **No**
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v3_pick_place\pick_place_same_platform_scripted_demo.mp4`
- Contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v3_pick_place\pick_place_same_platform_contact_sheet.png`
- Target center: `[0.165, 0.23, -0.06538044]`
- Target radius: `0.035 m`
- Stable target steps: `1169 / 240`
- Transport floor contacts before release: `0`

## Final Metrics

- Ball position: `[0.16190762133740277, 0.23078422736485196, -0.06556456351751812]`
- Ball lift height: `-0.000184 m`
- Target distance XY: `0.003190 m`
- Ball velocity norm: `1.149601`
- Ball-hand contacts: `0`
- Ball-floor contacts: `1`
- Max penetration: `0.000184 m`

## Phase Metrics

| phase | steps | lift m | target xy m | velocity | hand contacts | floor contacts | max pen m |
|---|---:|---:|---:|---:|---:|---:|---:|
| default_hold | 90 | -0.0002 | 0.0492 | 0.0000 | 0 | 1 | 0.000184 |
| move_to_pre_approach | 260 | -0.0002 | 0.0492 | 0.0000 | 0 | 1 | 0.000184 |
| approach_ball | 180 | -0.0006 | 0.0669 | 8.0112 | 2 | 1 | 0.000649 |
| preshape | 120 | -0.0013 | 0.0600 | 0.5176 | 3 | 1 | 0.001557 |
| close_four_fingers | 120 | -0.0013 | 0.0550 | 0.4286 | 4 | 1 | 0.003572 |
| close_thumb | 120 | -0.0014 | 0.0519 | 0.4415 | 7 | 1 | 0.003731 |
| lift | 220 | 0.1619 | 0.0684 | 1.8676 | 7 | 0 | 0.003430 |
| hold_lift | 120 | 0.1584 | 0.0656 | 0.6060 | 7 | 0 | 0.003416 |
| transport | 900 | 0.1688 | 0.0531 | 0.0639 | 7 | 0 | 0.003416 |
| descend_to_target | 500 | 0.0137 | 0.0153 | 0.5206 | 7 | 0 | 0.003414 |
| pre_release_settle | 180 | 0.0108 | 0.0153 | 0.0535 | 7 | 0 | 0.003415 |
| release | 600 | -0.0002 | 0.0129 | 1.1496 | 0 | 1 | 0.000184 |
| retreat | 300 | -0.0002 | 0.0077 | 1.1496 | 0 | 1 | 0.000184 |
| settle_on_target | 600 | -0.0002 | 0.0032 | 1.1496 | 0 | 1 | 0.000184 |

## Interpretation

This is the first same-platform pick-place smoke demo. It proves the v3 task shape can be evaluated end to end, but it is still a scripted pure-physics rollout on collision proxy v2.

The target displacement is intentionally modest. Larger target pads, two-platform transfer, randomized targets, dataset collection, and BC/RL training should remain gated behind additional scripted sweeps.
