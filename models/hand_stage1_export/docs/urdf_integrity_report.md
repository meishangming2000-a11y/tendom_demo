# URDF Integrity Report

- URDF: `D:\tendon_project\simulations\models\hand_stage1_export\robot.urdf`
- Robot name: `hand_export`
- Links: 23
- Joints: 22
- Revolute joints: 21
- Fixed joints: 1
- Mesh files in `meshes/`: 23
- Mesh references in URDF: 46
- Contains `Empty_Link`: no

## Checks

- Unique link names: yes
- Unique joint names: yes
- All mesh files exist: yes
- All revolute joints have limits: yes
- All joints have parent: yes
- All joints have child: yes
- Unresolved `package://` paths: none

## Notes

- `package://hand_export/meshes/...` paths were normalized in `robot.urdf` to local `meshes/...`; the pre-edit URDF is backed up under `archive/`.
- CAD/URDF current names `mcp_flex` and `mcp_abd` may need later review against actual motion-axis semantics.
- Tip coordinate systems are not represented as URDF links or joints in this export.
