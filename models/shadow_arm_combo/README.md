# shadow_arm_combo

Stage 1 combo wrapper for:

- `printed_arm_stage1`
- the existing `shadow_hand` scene

Current scope:

- loadable combo scene
- explicit wrapper-side mount relationship
- explicit wrapper-side Shadow wrist lock behavior
- mountable Shadow root with a freejoint so the arm is not welded back to the world frame
- metadata placeholders for mount calibration and future combined action layout

Current non-goals:

- no new environment
- no new adapter
- no training logic
- no Shadow source-model rewrite

Wrapper strategy:

- keep the original Shadow files untouched
- load a combo-local `shadow_right_hand_mountable.xml` wrapper
- give `rh_forearm` a wrapper-local freejoint and weld it to `pa_ee_mount`
- add wrapper-side lock actuators for `rh_WRJ1` and `rh_WRJ2`

Debug note:

- the combo can now be joint-driven for visual inspection
- load `scene.xml` through an absolute resolved path, or run from this directory, so nested includes and mesh paths resolve consistently
- it is still not a promoted training environment or finalized dynamics model
