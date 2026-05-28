# Clean Mesh Export2 Visual Check Report

## Inputs

- Source export package: `D:\tendon_project\hardwares\hand\hand_export2\hand_export`
- Source URDF: `D:\tendon_project\hardwares\hand\hand_export2\hand_export\urdf\hand_export.urdf`
- Source meshes: `D:\tendon_project\hardwares\hand\hand_export2\hand_export\meshes`
- Clean test directory: `D:\tendon_project\simulations\models\hand_stage1_export\clean_mesh_test_export2`
- Clean mesh directory: `D:\tendon_project\simulations\models\hand_stage1_export\meshes_clean_export2`
- MJCF draft: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_export2_draft.xml`
- Render directory: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export2`

## Mesh Integrity

- STL count: 23
- Expected logical links present: 23 / 23
- Missing expected links: 0
- Exact hash duplicate groups: 0
- Unique file size count: 18
- Unique triangle count: 18
- Oversized bbox over 300 mm: 0
- `thumb_root_connector_link`: single clean STL file in this export
- Mesh scale used in MJCF: `1 1 1`

The export2 STL bounding boxes are already meter-scale. Example: `palm_link.STL` has a max span near 0.106 m, so the old `0.001` mesh scale would make the hand 1000x too small. Export2 uses `scale="1 1 1"`.

## MuJoCo Load

- `hand_stage1_clean_mesh_export2_draft.xml`: loads successfully
  - Bodies: 24
  - Hand joints: 21
  - Geoms: 99
  - Meshes: 23
- `scene_ball_clean_mesh_export2_draft.xml`: loads successfully
  - Bodies: 25
  - Joints: 22 including ball freejoint
  - Geoms: 101
  - Meshes: 23
  - Cameras: 8

## Screenshots

- `front_view.png`
- `side_view.png`
- `top_view.png`
- `palm_view.png`
- `finger_root_closeup.png`
- `thumb_root_closeup.png`
- `index_finger_closeup.png`
- `full_hand_with_ball.png`

## Visual Result

**PASS for static clean mesh alignment.**

Observed:

- Palm is present and located at the expected palm/root area.
- Wrist and hand base are visible and connected below the palm.
- Four long fingers attach to the palm instead of floating away.
- Thumb is visible on the side of the palm and stays connected through the thumb root area.
- No repeated whole-hand mesh is visible.
- No large detached CAD chunks are visible.
- No scale explosion or 1000x shrink is visible after using `scale="1 1 1"`.
- The ball appears in front of the palm as expected for the demo scene.

Remaining TODO:

- Run targeted joint-motion visual audit before treating all joint axes/origins as mechanically correct.
- Keep primitive collision geoms for now; do not switch to complex mesh collision yet.
- `mcp_flex` / `mcp_abd` semantic reversal is still unresolved and should be checked by joint motion, not renamed tonight.

## Joint / Demo Smoke

- Export2 clean mesh joint smoke test: **PASS**
  - 21 hinge joints tested
  - finite body and clean geom poses
  - no numeric fly-away detected
- Export2 scripted grasp demo: **runs and renders**
  - Stages rendered under `docs\visual_checks_export2\grasp_demo`
  - The close pose visually wraps the ball with the long fingers.
  - Thumb closure is visible, but grasp quality still depends on future joint-axis tuning and collision/control work.

## Conclusion

This export is much better than the previous clean mesh batch. It appears to be body-local or close enough to body-local for the current stage1 clean visual draft. Use `hand_stage1_clean_mesh_export2_draft.xml` as the preferred clean mesh draft going forward, while keeping the primitive model as the collision/kinematic reference.
