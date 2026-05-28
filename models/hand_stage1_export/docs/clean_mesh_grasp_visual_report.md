# Clean Mesh Grasp Visual Report

## Status

**Skipped as visual acceptance demo due to clean mesh alignment BLOCKER.**

The script `D:\tendon_project\simulations\models\hand_stage1_export\scripts\demo_grasp_ball_clean_mesh.py` has been created and can reuse the primitive staged qpos logic, but it was not promoted/run as a visual acceptance demo because `clean_mesh_visual_check_report.md` found detached and floating clean STL geoms.

## Reason

- Primitive hand and ball are visible and still usable.
- Clean mesh MJCF loads successfully.
- Clean mesh STL files are credible by size/triangles/bbox/hash.
- However, clean mesh visual placement is wrong: palm/finger/thumb mesh parts are not reliably attached to their corresponding primitive body frames.

Running the grasp demo now would only prove that the primitive qpos targets still execute. It would not validate clean mesh grasp geometry, fingertip contact, palm support, or thumb opposition.

## Current Ball Demo Recommendation

- Continue using `scripts\demo_grasp_ball_primitive.py` for scripted grasp logic.
- Keep `scripts\demo_grasp_ball_clean_mesh.py` as a ready-to-run draft after mesh-frame correction.
- Re-run clean mesh grasp screenshots only after clean STL local-frame alignment is fixed.

## Expected Future Screenshots

When clean mesh visual alignment is fixed, save:

- `docs\visual_checks\grasp_demo\open_hand.png`
- `docs\visual_checks\grasp_demo\preshape.png`
- `docs\visual_checks\grasp_demo\four_fingers_closed.png`
- `docs\visual_checks\grasp_demo\thumb_closed.png`
- `docs\visual_checks\grasp_demo\hold.png`

## TODO

- Re-export per-link STL in body-local/link-local frames, or provide exact per-link mesh transform offsets.
- Confirm thumb root connector rigid grouping and visual bridge from palm to thumb.
- Re-run `render_clean_mesh_visual_checks.py`.
- If visual result becomes PASS/PARTIAL with no BLOCKER, run `demo_grasp_ball_clean_mesh.py`.
