# Export3 Grasp Ball Position-Control Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Load success: yes
- Ball position: `[0.0, -0.1, 0.21]`
- Gravity enabled: False
- Ball pinned: True
- Actuator count: 21
- Missing actuators: None
- Thumb target source: D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_thumb_opposition_candidates.json
- Thumb close target: `{'thumb_cmc_abd_joint': -0.8, 'thumb_cmc_flex_joint': 0.4, 'thumb_mcp_joint': 0.0, 'thumb_ip_joint': 1.2}`

## Stage Summary

| Stage | Contacts | Max penetration (m) | Mean 4-tip dist (m) | Thumb-ball (m) | Thumb-index (m) |
|---|---:|---:|---:|---:|---:|
| open_hand | 0 | 0.000000 | 0.086998 | 0.170287 | 0.142518 |
| approach_pre_shape | 0 | 0.000000 | 0.070699 | 0.155478 | 0.130861 |
| close_four_fingers | 4 | 0.009477 | 0.032670 | 0.152515 | 0.146996 |
| close_thumb | 3 | 0.007154 | 0.035655 | 0.096380 | 0.086095 |
| hold | 3 | 0.006959 | 0.035720 | 0.085809 | 0.075609 |

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\open_hand.png` camera=`full_hand_with_ball` mean_pixel=35.22
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\preshape.png` camera=`full_hand_with_ball` mean_pixel=34.23
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=33.79
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=33.58
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\close_thumb_palm.png` camera=`palm` mean_pixel=60.02
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\hold.png` camera=`full_hand_with_ball` mean_pixel=33.51
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_grasp\hold_palm.png` camera=`palm` mean_pixel=60.23

## Interpretation

- Open hand has no initial ball contact at the requested ball position.
- Hold mean four-fingertip distance is 0.0357 m.
- Hold thumb-ball distance is 0.0858 m.
- Thumb is much closer than the old model and can be used for export3 scripted smoke testing.
- Visual inspection of the saved hold frames shows four fingers wrapping the ball and the thumb moving to the ball-side region; it is improved but still not a final Shadow-like opposition clamp.
- Some exported joint ranges have nonzero lower limits, so an open-hand target of 0 can be clamped by the position actuator ctrlrange; inspect `ctrl_applied` and `qpos_actual` before treating 0 rad as mechanical neutral.
- This remains pinned-ball, zero-gravity scripted position control; it is not training-ready or a stable free-ball grasp.
