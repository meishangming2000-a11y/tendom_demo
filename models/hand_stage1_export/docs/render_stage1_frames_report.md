# Render Stage1 Frames Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_primitive.xml`

## Rendered Frames

- `neutral_front.png` camera=`front` mean_pixel=31.94
- `neutral_side.png` camera=`side` mean_pixel=26.97
- `neutral_top.png` camera=`top` mean_pixel=90.97
- `scripted_close_front.png` camera=`front` mean_pixel=31.64
- `scripted_close_side.png` camera=`side` mean_pixel=27.56
- `scripted_close_top.png` camera=`top` mean_pixel=94.78

## Observed

- Neutral primitive skeleton renders show root, wrist, palm, fingers, thumb, and ball without using suspicious STL meshes.
- Scripted close renders use the enhanced primitive staged target close_thumb pose.
- Palm is represented by a visible ellipsoid plus MCP spokes and joint markers.
- Fingertip sites are rendered as blue site markers in the primitive model.
- Thumb direction remains TODO for manual semantic review; it does not yet provide a Shadow-like opposition grasp.

## Notes

- Rendered frames are fixed-camera visual checks for neutral and scripted close poses.
- They are not a substitute for interactive axis/sign inspection in the MuJoCo viewer.
