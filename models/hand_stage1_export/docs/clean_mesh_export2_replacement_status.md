# Clean Mesh Replacement Status

- Clean mesh test passed: yes
- Files copied to `meshes_clean_export2`: 23
- Clean mesh MJCF draft created: yes
- Draft MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- Only clean-test link mesh visuals were added; primitive geoms remain as provisional collision/reference.

## Notes

- Original suspicious STL files were not deleted or overwritten.
- Joint tree and joint names were not changed.
- Clean mesh assets use `scale="1 1 1"` because the export2 STL bounding boxes are already meter-scale and match the MJCF skeleton scale.
- Static visual checks indicate this export is body-local enough to use as the current clean mesh draft; joint-motion checks are still needed before promoting collision/physics quality.
- This draft is a mesh replacement check, not a training or tendon-routing change.
