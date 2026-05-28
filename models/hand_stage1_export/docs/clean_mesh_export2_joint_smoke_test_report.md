# Clean Mesh Joint Smoke Test Report

- XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- Load success: yes
- Model summary: `{"nbody": 24, "njnt": 21, "nq": 21, "nv": 21, "ngeom": 99, "nsite": 5, "nmesh": 23, "nu": 0, "ncam": 0}`
- Hinge joints tested: 21
- Overall status: ok

## Per-Joint Qpos Smoke

- `wrist_1_joint` target=0.12, range=[-0.8, 0.8], finite=True, max_abs_body_pos=0.2667, max_abs_clean_geom_pos=0.2759, status=ok
- `wrist_2_joint` target=0.12, range=[-0.8, 0.8], finite=True, max_abs_body_pos=0.2716, max_abs_clean_geom_pos=0.2813, status=ok
- `index_mcp_flex_joint` target=0.12, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `index_mcp_abd_joint` target=0.12, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `index_pip_joint` target=0.12, range=[0, 1.57], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `index_dip_joint` target=0.12, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `middle_mcp_flex_joint` target=0.12, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `middle_mcp_abd_joint` target=0.12, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2655, max_abs_clean_geom_pos=0.2741, status=ok
- `middle_pip_joint` target=0.12, range=[0, 1.57], finite=True, max_abs_body_pos=0.2671, max_abs_clean_geom_pos=0.2757, status=ok
- `middle_dip_joint` target=0.12, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2769, status=ok
- `ring_mcp_flex_joint` target=0.12, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `ring_mcp_abd_joint` target=0.12, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `ring_pip_joint` target=0.12, range=[0, 1.57], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `ring_dip_joint` target=0.12, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `little_mcp_flex_joint` target=0.12, range=[-0.5, 0.5], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `little_mcp_abd_joint` target=0.12, range=[-0.2, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `little_pip_joint` target=0.12, range=[0, 1.57], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `little_dip_joint` target=0.12, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `thumb_cmc_joint` target=0.12, range=[-0.8, 0.8], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `thumb_mcp_joint` target=0.12, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok
- `thumb_ip_joint` target=0.12, range=[0, 1.2], finite=True, max_abs_body_pos=0.2682, max_abs_clean_geom_pos=0.2774, status=ok

## Notes

- This smoke test sets qpos directly and checks numeric sanity for clean mesh geoms.
- It does not prove mesh origin/orientation correctness; screenshot-based visual audit is required.
- Collision remains primitive/provisional; clean mesh geoms are visual-only.
