# Export2 Ball Position Retry Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_export2_retry.xml`
- Source scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_export2_draft.xml`
- Ball position: `[0.01, -0.085, 0.205]`
- Axis handling: kept original export2 axes; rejected all-axis flip because fingertip distance became worse.
- Collision note: clean STL geoms are visual-only; contacts below are from primitive collision geoms.

## Stage Contact And Distance Summary

| Stage | Ball contacts | Max penetration (m) | Mean 4-tip distance (m) | Thumb distance (m) |
|---|---:|---:|---:|---:|
| open_hand | 0 | 0.000000 | 0.089017 | 0.159101 |
| approach_pre_shape | 0 | 0.000000 | 0.076808 | 0.158292 |
| close_four_fingers | 4 | 0.015776 | 0.031317 | 0.158292 |
| close_thumb | 4 | 0.015776 | 0.031317 | 0.156393 |
| hold | 4 | 0.015776 | 0.031317 | 0.156393 |

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\open_hand.png` camera=`full_hand_with_ball` mean_pixel=31.95
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\preshape.png` camera=`full_hand_with_ball` mean_pixel=31.46
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\four_fingers_closed.png` camera=`full_hand_with_ball` mean_pixel=31.19
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\thumb_closed.png` camera=`full_hand_with_ball` mean_pixel=31.21
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold.png` camera=`full_hand_with_ball` mean_pixel=31.21
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold_front.png` camera=`front` mean_pixel=34.56
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold_side.png` camera=`side` mean_pixel=32.00
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold_top.png` camera=`top` mean_pixel=96.52
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold_palm.png` camera=`palm` mean_pixel=69.43
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold_thumb_root_closeup.png` camera=`thumb_root_closeup` mean_pixel=73.13
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2_retry\balanced_thumb\hold_index_finger_closeup.png` camera=`index_finger_closeup` mean_pixel=28.12

## Interpretation

- Initial open-hand contact should be zero or near zero; otherwise the ball is starting inside the hand/collision shell.
- Hold-stage penetration is expected to be approximate because the script teleports qpos targets and does not run a contact-aware controller.
- TODO: tune thumb opposition after joint-axis semantics are confirmed.
