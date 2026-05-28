# Clean Mesh Visual Check Report

## Inputs

- MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_draft.xml`
- Hand draft: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_draft.xml`
- Screenshot directory: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks`
- Clean mesh source: `D:\tendon_project\hardwares\hand\STL`

## Screenshot Files

- `front_view.png`
- `side_view.png`
- `top_view.png`
- `palm_view.png`
- `finger_root_closeup.png`
- `thumb_root_closeup.png`
- `index_finger_closeup.png`
- `full_hand_with_ball.png`

## Overall Visual Conclusion

**FAIL for clean mesh replacement.**

The model loads and the primitive skeleton remains visible, but the clean STL visual geoms are not aligned closely enough to the joint tree. This is a clean-mesh visual BLOCKER, not a URDF/joint-tree blocker. The most likely cause is that the hand-exported clean STL vertices still carry SolidWorks assembly/world coordinates and/or assembly-frame orientation instead of each link's body-local mesh frame.

## Per-View Observations

- `front_view.png`: primitive root/wrist/palm/fingers are visible, but many white CAD mesh parts float above or beside the hand. Palm mesh exists but is offset from the primitive palm. Several finger phalanx meshes are detached from the colored primitive links.
- `side_view.png`: the large clean palm shell is visible to the side of the primitive palm/finger bundle. It does not coincide with the primitive palm body. Floating finger segments are visible above/right.
- `top_view.png`: clean finger segments are scattered around the hand instead of forming one continuous per-finger chain. No single STL appears to contain the whole hand, but the per-link local placement is not correct.
- `palm_view.png`: root/wrist primitive chain is intact. Clean connector/palm-related parts appear around the base but are not consistently attached to their corresponding primitive bodies.
- `finger_root_closeup.png`: MCP root area is not visually reliable because primitive capsules and clean meshes occupy different frames. The clean phalanx parts do not sit on the joint centers.
- `thumb_root_closeup.png`: thumb-root STL parts exist and are visible, but they do not form a clearly connected palm-to-thumb bridge. The three root connector parts are not yet visually validated as a coherent body-local assembly.
- `index_finger_closeup.png`: index-related clean pieces are visible, but several segments float away from the primitive index chain. PIP/DIP locations cannot be trusted from this clean mesh view.
- `full_hand_with_ball.png`: primitive hand and ball are visible. Clean mesh components are scattered, so this view is not acceptable for clean-mesh grasp demo validation.

## Issues

- BLOCKER: Clean mesh geoms are not body-local/aligned with the primitive joint tree.
- BLOCKER: Clean mesh ball demo should not be visually accepted until per-link mesh origins/orientations are fixed.
- MAJOR: Palm mesh is present but offset from the primitive palm.
- MAJOR: Multiple finger phalanx meshes float away from the finger chains.
- MAJOR: Thumb root connector multi-STL mapping loads, but its visual placement does not yet prove correct palm-to-thumb connection.
- MINOR: `meshes_clean` contains ASCII-safe aliases for thumb-root STL filenames so MuJoCo can load them; source STL filenames were not changed.

## What Is Not The Problem

- Not a scale explosion: clean mesh assets use `scale="0.001 0.001 0.001"` and no rendered link is >1 m.
- Not a hash-duplicate export: 25 STL files, 0 exact hash duplicate groups.
- Not an obvious whole-hand-as-one-link export: no single clean STL bbox is suspiciously huge.
- Not missing thumb files: `thumb_metacarpal_link`, `thumb_proximal_link`, and `thumb_distal_link` are present.

## Recommendations

- Do continue using the primitive model for joint tree, joint axis, limits, and scripted grasp logic.
- Do keep `hand_stage1_clean_mesh_draft.xml` only as a diagnostic mesh-placement draft.
- Do not promote clean mesh visuals to the main demo yet.
- Do not run clean mesh ball demo as a visual acceptance demo while this BLOCKER remains.

## SolidWorks / Export TODO

- Re-export or post-process per-link STL so each mesh is in the corresponding link-local frame, or provide the exact CAD-to-URDF link transforms needed to convert assembly-coordinate STL into body-local meshes.
- Confirm whether SolidWorks export is "selected body in assembly coordinates" versus "selected body in part/link local coordinates".
- Keep `thumb_root_connector_link` as three separate STL parts unless CAD rigid-body grouping says otherwise.
- Recheck these first after export-frame correction: `palm_link`, all long-finger phalanx links, and the three `thumb_root_connector_link` component STL files.
