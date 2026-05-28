# Joint Smoke Test Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball.xml`
- Load success: yes
- Model summary: `{"nbody": 25, "njnt": 22, "nq": 28, "nv": 27, "ngeom": 78, "nmesh": 0, "nu": 0}`
- Hinge joints tested: 21
- Overall status: ok

## Joint Names

- `wrist_1_joint`
- `wrist_2_joint`
- `index_mcp_flex_joint`
- `index_mcp_abd_joint`
- `index_pip_joint`
- `index_dip_joint`
- `middle_mcp_flex_joint`
- `middle_mcp_abd_joint`
- `middle_pip_joint`
- `middle_dip_joint`
- `ring_mcp_flex_joint`
- `ring_mcp_abd_joint`
- `ring_pip_joint`
- `ring_dip_joint`
- `little_mcp_flex_joint`
- `little_mcp_abd_joint`
- `little_pip_joint`
- `little_dip_joint`
- `thumb_cmc_joint`
- `thumb_mcp_joint`
- `thumb_ip_joint`
- `ball_freejoint`

## Per-Joint Qpos Smoke

- `wrist_1_joint` target=0.1, range=[-0.8, 0.8], finite=True, max_abs_body_pos=0.2671, status=ok
- `wrist_2_joint` target=0.1, range=[-0.8, 0.8], finite=True, max_abs_body_pos=0.2712, status=ok
- `index_mcp_flex_joint` target=0.1, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, status=ok
- `index_mcp_abd_joint` target=0.1, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `index_pip_joint` target=0.1, range=[0, 1.57], finite=True, max_abs_body_pos=0.2682, status=ok
- `index_dip_joint` target=0.1, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `middle_mcp_flex_joint` target=0.1, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2683, status=ok
- `middle_mcp_abd_joint` target=0.1, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.266, status=ok
- `middle_pip_joint` target=0.1, range=[0, 1.57], finite=True, max_abs_body_pos=0.2673, status=ok
- `middle_dip_joint` target=0.1, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `ring_mcp_flex_joint` target=0.1, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, status=ok
- `ring_mcp_abd_joint` target=0.1, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `ring_pip_joint` target=0.1, range=[0, 1.57], finite=True, max_abs_body_pos=0.2682, status=ok
- `ring_dip_joint` target=0.1, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `little_mcp_flex_joint` target=0.1, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, status=ok
- `little_mcp_abd_joint` target=0.1, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `little_pip_joint` target=0.1, range=[0, 1.57], finite=True, max_abs_body_pos=0.2682, status=ok
- `little_dip_joint` target=0.1, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `thumb_cmc_joint` target=0.1, range=[-0.8, 0.8], finite=True, max_abs_body_pos=0.2682, status=ok
- `thumb_mcp_joint` target=0.1, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok
- `thumb_ip_joint` target=0.1, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, status=ok

## Notes

- This smoke test sets qpos directly; no actuator or controller is implied.
- No severe numeric explosion was detected if max_abs_body_pos stays below 2 m.
- Joint axis direction, mesh fly-away, and penetration still need human visual confirmation in the viewer.
- CAD/URDF current names mcp_flex and mcp_abd may need later review against actual motion-axis semantics.
