# Fingertip Ball Distance Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_primitive.xml`
- Load success: yes
- Ball position: `[0.01, -0.045, 0.215]`
- Ball radius: 0.025 m
- Missing sites: None

## Stage Distances

### open_hand

- Ball center: `[0.01, -0.045, 0.215]`
- Min fingertip distance: 0.06267 m
- `index_tip_site`: distance=0.07493 m, clearance=0.04993 m
- `little_tip_site`: distance=0.06267 m, clearance=0.03767 m
- `middle_tip_site`: distance=0.07926 m, clearance=0.05426 m
- `ring_tip_site`: distance=0.06365 m, clearance=0.03865 m
- `thumb_tip_site`: distance=0.12280 m, clearance=0.09780 m

### approach_pre_shape

- Ball center: `[0.01, -0.045, 0.215]`
- Min fingertip distance: 0.05654 m
- `index_tip_site`: distance=0.06963 m, clearance=0.04463 m
- `little_tip_site`: distance=0.05654 m, clearance=0.03154 m
- `middle_tip_site`: distance=0.07590 m, clearance=0.05090 m
- `ring_tip_site`: distance=0.06045 m, clearance=0.03545 m
- `thumb_tip_site`: distance=0.12033 m, clearance=0.09533 m

### close_four_fingers

- Ball center: `[0.01, -0.045, 0.215]`
- Min fingertip distance: 0.05800 m
- `index_tip_site`: distance=0.05897 m, clearance=0.03397 m
- `little_tip_site`: distance=0.05800 m, clearance=0.03300 m
- `middle_tip_site`: distance=0.06729 m, clearance=0.04229 m
- `ring_tip_site`: distance=0.06082 m, clearance=0.03582 m
- `thumb_tip_site`: distance=0.12033 m, clearance=0.09533 m

### close_thumb

- Ball center: `[0.01, -0.045, 0.215]`
- Min fingertip distance: 0.05800 m
- `index_tip_site`: distance=0.05897 m, clearance=0.03397 m
- `little_tip_site`: distance=0.05800 m, clearance=0.03300 m
- `middle_tip_site`: distance=0.06729 m, clearance=0.04229 m
- `ring_tip_site`: distance=0.06082 m, clearance=0.03582 m
- `thumb_tip_site`: distance=0.11758 m, clearance=0.09258 m

### hold

- Ball center: `[0.01, -0.045, 0.215]`
- Min fingertip distance: 0.05800 m
- `index_tip_site`: distance=0.05897 m, clearance=0.03397 m
- `little_tip_site`: distance=0.05800 m, clearance=0.03300 m
- `middle_tip_site`: distance=0.06729 m, clearance=0.04229 m
- `ring_tip_site`: distance=0.06082 m, clearance=0.03582 m
- `thumb_tip_site`: distance=0.11758 m, clearance=0.09258 m

## Notes

- Distances are computed on primitive fingertip sites, not CAD fingertip geometry.
- Negative clearance means the site is inside the ideal ball radius; this is allowed for this qpos-only scripted smoke test.
- TODO: use these numbers to tune ball position and scripted target signs after visual inspection.
