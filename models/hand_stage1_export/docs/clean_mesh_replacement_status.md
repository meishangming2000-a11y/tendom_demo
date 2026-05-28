# Clean Mesh Replacement Status

- Clean mesh test passed: yes
- Files copied to `meshes_clean`: 25
- Clean mesh MJCF draft created: yes
- Draft MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_draft.xml`
- Only clean-test link mesh visuals were added; primitive geoms remain as provisional collision/reference.

## Notes

- Original suspicious STL files were not deleted or overwritten.
- Joint tree and joint names were not changed.
- Non-ASCII or space-containing STL filenames are copied into `meshes_clean` with deterministic ASCII-safe MJCF filenames; original source/test filenames are not changed.
- Clean mesh assets use `scale="0.001 0.001 0.001"` because the manually exported STL bounding boxes are in millimeter-like dimensions while the MJCF skeleton is in meters.
- Mesh local-frame alignment is still a draft item; verify per-link origin/orientation visually before promoting these mesh geoms beyond replacement testing.
- This draft is a mesh replacement check, not a training or tendon-routing change.
