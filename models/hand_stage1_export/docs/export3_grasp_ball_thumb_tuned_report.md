# Export3 Thumb-Tuned Grasp Ball Report

Status: scripted position-control smoke test with experimental thumb limits. Not a training baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_thumb_limit_tuned.xml`
- Load success: yes
- Ball position: `[0.0, -0.1, 0.21]`
- Gravity enabled: False
- Ball pinned: True
- Thumb target source: D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_thumb_limit_tuning_candidates.json
- Thumb target: `{'thumb_cmc_abd_joint': -1.2, 'thumb_cmc_flex_joint': 0.6, 'thumb_mcp_joint': -0.2, 'thumb_ip_joint': 1.2}`
- Missing actuators: None

## Stage Summary

| Stage | Contacts | Max penetration (m) | Mean 4-tip dist (m) | Thumb-ball (m) | Thumb-index (m) |
|---|---:|---:|---:|---:|---:|
| open_hand | 0 | 0.000000 | 0.086999 | 0.170286 | 0.142518 |
| approach_pre_shape | 0 | 0.000000 | 0.069265 | 0.144942 | 0.118447 |
| close_four_fingers | 4 | 0.006641 | 0.035018 | 0.143585 | 0.135993 |
| close_thumb | 3 | 0.006607 | 0.035860 | 0.041089 | 0.033527 |
| hold | 3 | 0.006608 | 0.035860 | 0.034260 | 0.029600 |

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\open_hand.png` camera=`full_hand_with_ball` mean_pixel=35.17
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\preshape.png` camera=`full_hand_with_ball` mean_pixel=34.09
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=33.53
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=33.39
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\close_thumb_top.png` camera=`top` mean_pixel=99.16
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\close_thumb_palm.png` camera=`palm` mean_pixel=60.30
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\hold.png` camera=`full_hand_with_ball` mean_pixel=33.40
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\hold_top.png` camera=`top` mean_pixel=99.17
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_tuned_grasp\hold_palm.png` camera=`palm` mean_pixel=60.31

## Interpretation

- Open hand has no initial ball contact at the default tuned ball position.
- Hold thumb-ball distance is 0.0343 m.
- Hold thumb-index distance is 0.0296 m.
- Hold mean four-fingertip distance is 0.0359 m.
- Tuned thumb pose enters the 0.06 m thumb-ball target region.
- The tuned thumb target is suitable for scripted Shadow-style scaffold experiments, but not yet for training promotion.
