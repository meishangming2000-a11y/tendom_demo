# Export3 MuJoCo Load Report

- Raw hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3_raw_mesh.xml`
- Export3 hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3.xml`
- Scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Mesh scale: `1 1 1`
- Mesh geoms are visual-only; simplified primitive geoms provide collision proxy.
- No suspicious STL is used.

## Load Summary

| Model | Load | Bodies | Joints | Actuators | Geoms | Sites | Meshes |
|---|---|---:|---:|---:|---:|---:|---:|
| hand | yes | 25 | 21 | 21 | 53 | 5 | 24 |
| scene | yes | 26 | 22 | 21 | 55 | 5 | 24 |
| raw | yes | 25 | 21 | 21 | 53 | 5 | 24 |

## Actuators

- `wrist_1_joint_pos` -> `wrist_1_joint` kp=5.0 ctrlrange=`['-0.8', '0.8']`
- `index_mcp_flex_joint_pos` -> `index_mcp_flex_joint` kp=3.0 ctrlrange=`['-0.5', '0.5']`
- `index_mcp_abd_joint_pos` -> `index_mcp_abd_joint` kp=3.0 ctrlrange=`['0.2', '1.2']`
- `index_pip_joint_pos` -> `index_pip_joint` kp=2.0 ctrlrange=`['0', '1.57']`
- `index_dip_joint_pos` -> `index_dip_joint` kp=2.0 ctrlrange=`['0', '1.2']`
- `middle_mcp_flex_joint_pos` -> `middle_mcp_flex_joint` kp=3.0 ctrlrange=`['-0.5', '0.5']`
- `middle_mcp_abd_joint_pos` -> `middle_mcp_abd_joint` kp=3.0 ctrlrange=`['0.2', '1.2']`
- `middle_pip_joint_pos` -> `middle_pip_joint` kp=2.0 ctrlrange=`['0', '1.57']`
- `middle_dip_joint_pos` -> `middle_dip_joint` kp=2.0 ctrlrange=`['0', '1.2']`
- `ring_mcp_flex_joint_pos` -> `ring_mcp_flex_joint` kp=3.0 ctrlrange=`['-0.5', '0.5']`
- `ring_mcp_abd_joint_pos` -> `ring_mcp_abd_joint` kp=3.0 ctrlrange=`['-0.2', '1.2']`
- `ring_pip_joint_pos` -> `ring_pip_joint` kp=2.0 ctrlrange=`['0', '1.57']`
- `ring_dip_joint_pos` -> `ring_dip_joint` kp=2.0 ctrlrange=`['0', '1.2']`
- `little_mcp_flex_joint_pos` -> `little_mcp_flex_joint` kp=3.0 ctrlrange=`['-0.5', '0.5']`
- `little_mcp_abd_joint_pos` -> `little_mcp_abd_joint` kp=3.0 ctrlrange=`['-0.2', '1.2']`
- `little_pip_joint_pos` -> `little_pip_joint` kp=2.0 ctrlrange=`['0', '1.57']`
- `little_dip_joint_pos` -> `little_dip_joint` kp=2.0 ctrlrange=`['0', '1.2']`
- `thumb_cmc_abd_joint_pos` -> `thumb_cmc_abd_joint` kp=2.0 ctrlrange=`['-0.8', '0.8']`
- `thumb_cmc_flex_joint_pos` -> `thumb_cmc_flex_joint` kp=2.0 ctrlrange=`['0', '1.2']`
- `thumb_mcp_joint_pos` -> `thumb_mcp_joint` kp=3.0 ctrlrange=`['0', '1.2']`
- `thumb_ip_joint_pos` -> `thumb_ip_joint` kp=2.0 ctrlrange=`['0', '1.2']`

## Notes

- `wrist_2_joint` is fixed in export3 if it appears that way in the URDF; no actuator is added for fixed joints.
- `thumb_cmc_abd_joint` and `thumb_cmc_flex_joint` are included as position actuated hinge joints when present in the URDF.
- Raw and main export3 MJCF currently use the same mesh/body transform path. If visual inspection shows assembly/world-coordinate offsets, generate an aligned draft later and document it.
