# Scripted Grasp Ball Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball.xml`
- Load success: yes
- Ball position: `[0.01, -0.045, 0.215]`
- Ball radius: 0.025 m
- Visual grasp status: approximate_wrap_visible_in_primitive_skeleton_renders

## Applied Joint Targets

- `index_dip_joint`: 0.35 rad
- `index_mcp_abd_joint`: 0.45 rad
- `index_mcp_flex_joint`: -0.08 rad
- `index_pip_joint`: 0.65 rad
- `little_dip_joint`: 0.35 rad
- `little_mcp_abd_joint`: 0.45 rad
- `little_mcp_flex_joint`: 0.08 rad
- `little_pip_joint`: 0.65 rad
- `middle_dip_joint`: 0.38 rad
- `middle_mcp_abd_joint`: 0.5 rad
- `middle_mcp_flex_joint`: 0 rad
- `middle_pip_joint`: 0.7 rad
- `ring_dip_joint`: 0.38 rad
- `ring_mcp_abd_joint`: 0.5 rad
- `ring_mcp_flex_joint`: 0.04 rad
- `ring_pip_joint`: 0.7 rad
- `thumb_cmc_joint`: 0.25 rad
- `thumb_ip_joint`: 0.35 rad
- `thumb_mcp_joint`: 0.45 rad

## Possible Direction/Axis Issues

- TODO: visually confirm whether MCP flex/abd signs are correct; current names may not match actual motion semantics.
- TODO: visually confirm whether any PIP/DIP axes are reversed.
- TODO: visually confirm whether any link origin/scale causes penetration or offset around the ball.

## Notes

- No RL, tendon routing, or actuator controller is used; the demo directly interpolates qpos.
- The pose uses small MCP side-motion values and moderate PIP/DIP closure to avoid explosive motion.
- Default scene uses primitive skeleton geoms because the exported STL meshes appear unsuitable as clean per-link visuals.
- See docs/renders/scripted_close_front.png, scripted_close_side.png, and scripted_close_top.png for fixed-camera checks.
- CAD/URDF current names mcp_flex and mcp_abd may need later review against actual motion-axis semantics.
- TODO: confirm whether any target signs should be flipped after visual inspection.
- TODO: tune ball position after viewing real palm/finger alignment.
