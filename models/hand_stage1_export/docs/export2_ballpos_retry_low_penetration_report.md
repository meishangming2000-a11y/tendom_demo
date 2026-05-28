# Export2 Ball Position Retry Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_export2_retry.xml`
- Source scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_export2_draft.xml`
- Ball position: `[0.0, -0.1, 0.195]`
- Axis handling: kept original export2 axes; rejected all-axis flip because fingertip distance became worse.
- Collision note: clean STL geoms are visual-only; contacts below are from primitive collision geoms.

## Stage Contact And Distance Summary

| Stage | Ball contacts | Max penetration (m) | Mean 4-tip distance (m) | Thumb distance (m) |
|---|---:|---:|---:|---:|
| open_hand | 0 | 0.000000 | 0.105781 | 0.170603 |
| approach_pre_shape | 0 | 0.000000 | 0.092632 | 0.171181 |
| close_four_fingers | 2 | 0.005000 | 0.034357 | 0.171181 |
| close_thumb | 2 | 0.005000 | 0.034357 | 0.170784 |
| hold | 2 | 0.005000 | 0.034357 | 0.170784 |

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\open_hand.png` camera=`full_hand_with_ball` mean_pixel=31.83
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\preshape.png` camera=`full_hand_with_ball` mean_pixel=31.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=31.18
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=31.19
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold.png` camera=`full_hand_with_ball` mean_pixel=31.19
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold_front.png` camera=`front` mean_pixel=34.58
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold_side.png` camera=`side` mean_pixel=32.24
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold_top.png` camera=`top` mean_pixel=96.83
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold_palm.png` camera=`palm` mean_pixel=71.22
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold_thumb_root_closeup.png` camera=`thumb_root_closeup` mean_pixel=73.13
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\low_penetration\hold_index_finger_closeup.png` camera=`index_finger_closeup` mean_pixel=28.12

## Interpretation

- Initial open-hand contact should be zero or near zero; otherwise the ball is starting inside the hand/collision shell.
- Hold-stage penetration is expected to be approximate because the script teleports qpos targets and does not run a contact-aware controller.
- TODO: tune thumb opposition after joint-axis semantics are confirmed.
