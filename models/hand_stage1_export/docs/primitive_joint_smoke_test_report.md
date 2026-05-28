# Primitive Joint Smoke Test Report

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_primitive.xml`
- Load success: yes
- Model summary: `{"nbody": 25, "njnt": 22, "nq": 28, "nv": 27, "ngeom": 78, "nsite": 5, "nmesh": 0, "nu": 0}`
- Hinge joints tested: 21
- Overall status: ok

## Fingertip Sites

- `index_tip_site`
- `middle_tip_site`
- `ring_tip_site`
- `little_tip_site`
- `thumb_tip_site`

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

- Primitive smoke test does not use suspicious STL meshes.
- This test sets qpos directly and validates kinematic/numeric sanity only.
- Axis signs and mechanical semantics still need viewer/manual confirmation.
