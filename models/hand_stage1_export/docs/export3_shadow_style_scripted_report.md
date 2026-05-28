# Export3 Shadow-Style Scripted Task Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Trial count: 225
- Modes: `['pinned', 'free_zero_g', 'free_gravity']`
- Ball sweep: `[[0.0, -0.1, 0.21], [0.0, -0.1, 0.195], [0.01, -0.1, 0.21], [-0.01, -0.1, 0.21], [0.0, -0.09, 0.21]]`
- Finger scales: `[0.85, 1.0, 1.15]`
- Thumb candidates used: 5
- Capability best level: **pinned_wrap**

## Capability Ladder

- Pinned visual/contact wrap: PASS
- Zero-gravity release retained: not achieved
- Gravity release retained: not achieved

## Classification Counts

- PARTIAL_OR_FAIL: 32
- PINNED_PARTIAL: 17
- PINNED_WRAP_PASS: 58
- WRAP_BEFORE_RELEASE_ONLY: 118

## Classification Counts By Mode

- pinned: `{'PINNED_PARTIAL': 17, 'PINNED_WRAP_PASS': 58}`
- free_zero_g: `{'PARTIAL_OR_FAIL': 17, 'WRAP_BEFORE_RELEASE_ONLY': 58}`
- free_gravity: `{'PARTIAL_OR_FAIL': 15, 'WRAP_BEFORE_RELEASE_ONLY': 60}`

## Best By Mode

| Mode | Class | Ball | Finger scale | Thumb pose | Contacts | Penetration | Mean four-tip | Thumb-ball | Release drift |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | `{'thumb_cmc_abd_joint': -0.8, 'thumb_cmc_flex_joint': 0.0, 'thumb_ip_joint': 0.4, 'thumb_mcp_joint': 0.0}` | 5 | 0.002328 | 0.039919 | 0.076934 | 0.000000 |
| free_zero_g | WRAP_BEFORE_RELEASE_ONLY | `[0.0, -0.09, 0.21]` | 1.00 | `{'thumb_cmc_abd_joint': -0.8, 'thumb_cmc_flex_joint': 0.0, 'thumb_ip_joint': 0.4, 'thumb_mcp_joint': 0.0}` | 5 | 0.002328 | 0.039919 | 0.076934 | 0.081021 |
| free_gravity | WRAP_BEFORE_RELEASE_ONLY | `[0.0, -0.09, 0.21]` | 1.00 | `{'thumb_cmc_abd_joint': -0.8, 'thumb_cmc_flex_joint': 0.0, 'thumb_ip_joint': 0.4, 'thumb_mcp_joint': 0.0}` | 4 | 0.002764 | 0.039887 | 0.076540 | 0.190883 |

## Best Overall Trials

| Rank | Mode | Class | Ball | Finger scale | Thumb-ball | Mean four-tip | Penetration | Score |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 0.076934 | 0.039919 | 0.002328 | 0.069571 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 0.077297 | 0.039910 | 0.002340 | 0.069799 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 0.078506 | 0.039910 | 0.002341 | 0.070525 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 0.080611 | 0.039909 | 0.002342 | 0.071789 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 0.076901 | 0.035345 | 0.005113 | 0.073155 |
| 6 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 0.077256 | 0.035340 | 0.005116 | 0.073367 |
| 7 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.00 | 0.083681 | 0.039894 | 0.002366 | 0.073652 |
| 8 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 0.078476 | 0.035340 | 0.005116 | 0.074100 |
| 9 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 0.080595 | 0.035339 | 0.005116 | 0.075370 |
| 10 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 0.85 | 0.083665 | 0.035331 | 0.005121 | 0.077212 |
| 11 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.195]` | 1.15 | 0.089609 | 0.036429 | 0.002243 | 0.077559 |
| 12 | pinned | PINNED_WRAP_PASS | `[0.0, -0.09, 0.21]` | 1.15 | 0.076903 | 0.039247 | 0.005945 | 0.078305 |

## Rendered Best Trials

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_pinned\open_hand.png` camera=`full_hand_with_ball` mean_pixel=35.00
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_pinned\preshape.png` camera=`full_hand_with_ball` mean_pixel=34.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_pinned\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_pinned\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=33.05
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_pinned\hold.png` camera=`full_hand_with_ball` mean_pixel=33.03
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_pinned\hold_palm.png` camera=`palm` mean_pixel=58.64
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\open_hand.png` camera=`full_hand_with_ball` mean_pixel=35.00
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\preshape.png` camera=`full_hand_with_ball` mean_pixel=34.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=33.05
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\hold.png` camera=`full_hand_with_ball` mean_pixel=33.03
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\hold_palm.png` camera=`palm` mean_pixel=58.64
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\release_end.png` camera=`full_hand_with_ball` mean_pixel=32.48
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_zero_g\release_end_palm.png` camera=`palm` mean_pixel=57.78
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\open_hand.png` camera=`full_hand_with_ball` mean_pixel=35.00
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\preshape.png` camera=`full_hand_with_ball` mean_pixel=34.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=33.38
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=33.07
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\hold.png` camera=`full_hand_with_ball` mean_pixel=33.04
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\hold_palm.png` camera=`palm` mean_pixel=58.73
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\release_end.png` camera=`full_hand_with_ball` mean_pixel=33.12
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_shadow_style\best_free_gravity\release_end_palm.png` camera=`palm` mean_pixel=59.73

## Shadow-Style Task API Sketch

- Reset: set hand to exported open/neutral actuator limits and place a ball from a small pose grid.
- Observation: joint qpos, actuator targets, fingertip-to-ball distances, thumb-index distance, ball pose, and ball contact summary.
- Action: 21-D position actuator target vector, currently generated by a staged scripted policy.
- Success metrics: no initial overlap, multi-finger contact, low penetration, thumb close to ball/index, and object retention after release.
- Current status: diagnostic scripted scaffold only; not training-ready.

## Interpretation

- Export3 can achieve a Shadow-style scripted pinned-ball wrap/contact smoke test.
- Zero-gravity release did not satisfy the retention threshold; the grasp is still mainly a pinned-ball smoke test.
- Gravity release retention was not achieved; do not treat this as a stable physical grasp.
- The current ceiling is diagnostic scripted grasp scaffolding, not RL/BC training or final Shadow equivalence.
- Next limiting factors are collision proxy fidelity, actuator gain/contact tuning, and final thumb axis/limit confirmation.
