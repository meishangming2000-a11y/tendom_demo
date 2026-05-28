# Hand Stage1 MuJoCo Status

## Latest Arm+Hand Virtual-Space Milestone

Updated: 2026-05-28 02:15

The hand has now been assembled with the mechanical arm using the SolidWorks-exported mount coordinate systems. The current active arm+hand workspace is:

`D:\tendon_project\simulations\models\arm_hand_stage1_export\`

Current arm+hand collision candidate:

- Model: `mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Ball scene: `mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Scripted viewer: `view_arm_hand_stage1_scripted_demo.py`
- Collision smoke report: `docs\arm_hand_collision_proxy_v2_smoke_report.md`
- Shadow/video comparison report: `docs\arm_hand_stage1_v2_shadow_video_comparison_report.md`

Latest arm+hand v2 results:

- Collision v2 smoke: PASS
- Free ball start ball-hand contacts: `1`
- Free ball start penetration: `0.000500 m`
- Free-ball displacement after 300 open steps: `0.018294 m`
- Free-ball vertical drop after 300 open steps: `0.013383 m`
- Scripted pinned hold ball-hand contacts: `6`
- Scripted pinned hold max penetration: about `0.0042 m`
- Local ball sweep: `9 / 9` PASS
- Shadow/video comparison: `12 / 12` videos processed, `0` arm+hand failures
- Shadow mean closure score: `0.3136`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646`

Important interpretation:

- The passive viewer lets the ball fall under gravity and does not send hand-closing controls.
- Use `view_arm_hand_stage1_scripted_demo.py` to visually confirm staged closure.
- The comparison run removes the ball and validates video-to-control closure behavior, not stable free-object grasp.
- Training remains blocked until collision proxy, task labels, and free-object behavior are better validated.

## Latest Export4 +Y Palmar Collision Candidate

Generated on 2026-05-26 as a new experimental branch. Current-baseline remains frozen and was not overwritten.

Active candidate:

- Hand MJCF: `mjcf/hand_stage1_export4_palmar_ypos_collision_candidate.xml`
- Scene MJCF: `mjcf/scene_ball_export4_palmar_ypos_collision_candidate.xml`
- Ball pose: `[0.0, 0.08, 0.21]`
- Added collision proxy: fingertip sphere geoms at the five fingertip sites
- Fingertip sphere radius: `0.015 m`
- Clean STL remains visual-only

Why this candidate exists:

- The previous `wrist2_collision_tuned` branch fixed/verified wrist_2 and reduced static penetration, but the default `-Y` ball side still failed scripted grasp.
- Visual and metric diagnostics showed that `+Y` is much closer to the closing fingertips.
- The candidate tests `+Y` and adds only local fingertip collision, instead of inflating the palm or whole fingers.

Candidate results:

- Regression: `7 PASS / 0 FAIL / 0 SKIPPED`
- Model load: PASS
- Joint smoke: PASS
- wrist_2 test: PASS
- Open static collision: PASS
- Adapter unit test: PASS
- Scripted grasp smoke: PASS
- Replay smoke dataset: PASS
- 5-episode dry run: `5/5 success_smoke`

Candidate hold metrics:

- contacts: `2`
- ball-hand contacts: `2`
- max penetration: about `0.001042 m`
- four-finger average tip-ball distance: about `0.0465 m`
- thumb-ball distance: about `0.0433 m`

New reports and data:

- `docs/export4_active_file_index.md`
- `docs/export4_final_engineering_report.md`
- `docs/export4_palmar_ypos_candidate_regression_report.md`
- `metadata/export4_palmar_ypos_candidate_regression_results.json`
- `docs/export4_palmar_ypos_candidate_5ep_smoke_report.md`
- `metadata/export4_palmar_ypos_candidate_5ep_smoke_results.json`
- `data/export4_palmar_ypos_candidate_5ep_smoke_rollout.npz`
- `docs/export4_palmar_ypos_candidate_5ep_replay_report.md`
- `docs/visual_checks_export4_palmar_ypos_candidate_5ep_replay/`

Current decision:

- Tiny dataset-v0 dry run: allowed only after user confirms `+Y` is the canonical palm/grasp side.
- Full dataset collection: not yet.
- RL/BC/training: still forbidden.

Tomorrow's first human decision:

- Confirm whether export4 task scenes should treat `+Y` as the palm/grasp side.
- If yes, promote this candidate to the next experiment baseline.
- If no, keep it as diagnostic only and return to palm-frame orientation audit.

## Latest Export4 Task API / Regression Scaffold

Generated on 2026-05-26 after the wrist2/collision-tuned experiment.

New scaffold files:

- `scripts/export4_task_api.py`
- `scripts/run_export4_scripted_grasp_task.py`
- `scripts/replay_export4_smoke_dataset.py`
- `scripts/export4_retargeting_scaffold.py`
- `scripts/run_export4_regression_tests.py`
- `docs/export4_task_api_report.md`
- `docs/export4_scripted_grasp_task_report.md`
- `docs/export4_replay_report.md`
- `docs/export4_retargeting_scaffold.md`
- `docs/export4_shadow_style_task_gap_checklist.md`
- `docs/export4_regression_test_report.md`
- `docs/morning_status_export4.md`
- `metadata/export4_scripted_grasp_task_results.json`
- `metadata/export4_scripted_grasp_task_rollout.npz`
- `metadata/export4_semantic_joint_aliases.json`
- `metadata/export4_regression_test_results.json`

Task API status:

- Loads `scene_ball_export4_wrist2_collision_tuned.xml`.
- Action dim: `22`.
- Observation vector dim: `112`.
- Includes qpos, qvel, ctrl, fingertip sites, ball position, ball velocity, contact summary, and fingertip-ball distances.
- This is a scaffold, not a Gym environment and not a training setup.

Scripted grasp task status:

- Runs through `export4_task_api.py`.
- Default ball `[0.0, -0.1, 0.21]` fails smoke success.
- 3/3 default episodes fail with no ball-hand contact.
- This failure is expected until palm side / ball side is finalized.

Replay status:

- `replay_export4_smoke_dataset.py` can replay `data/export4_scripted_smoke_dataset.npz`.
- Dataset action dim matches the current model.
- Dataset obs dim differs from the newer task API because the API adds ctrl, ball velocity, and distance fields.
- Replay uses the qpos/qvel prefix plus action arrays and passes.

Retargeting scaffold status:

- Semantic keypoints and action groups are defined.
- Four-finger `*_mcp_flex_joint` is aliased as spread / abduction-adduction.
- Four-finger `*_mcp_abd_joint` is treated as likely current MCP flexion.
- No joint names were changed.

Regression result:

- Overall: **FAIL**
- PASS / FAIL / SKIPPED: `6 / 1 / 0`
- PASS:
  - model load
  - joint smoke
  - wrist_2 test
  - collision open-static penetration threshold
  - adapter unit test
  - replay smoke dataset
- FAIL:
  - scripted grasp task smoke at default `-Y` ball side

Dataset collection v0:

- Current decision: **not ready**.
- Reason: default scripted grasp smoke fails and canonical palm/ball side remains unresolved.

Training:

- Current decision: **still forbidden**.
- Do not start RL, BC, or neural training until scripted grasp task smoke and contact proxy are meaningful.

Next recommended fix:

1. Decide whether export4 canonical palm-side ball placement should use `+Y`.
2. Re-run scripted grasp task with the accepted canonical side.
3. Tune fingertip/distal collision proxy after side convention is fixed.
4. Re-run `scripts/run_export4_regression_tests.py`.

## Latest Export4 Wrist2 / Collision-Proxy Experiment

Generated on 2026-05-26 under the experimental branch:

- `mjcf\hand_stage1_export4_wrist2_collision_tuned.xml`
- `mjcf\scene_ball_export4_wrist2_collision_tuned.xml`

The current export4 baseline remains frozen and was not overwritten. See:

- `docs\export4_current_baseline_freeze.md`

### Baseline Freeze

- `hand_stage1_export4_current_baseline.xml` remains the current frozen baseline.
- All wrist2/collision work was copied into the experimental files listed above.
- Known baseline issues are now documented:
  - `wrist_2_joint` was user-confirmed to be an active joint. The frozen MJCF already contains it as `hinge`; the experimental branch verifies and preserves this.
  - collision proxy still needs side/contact tuning before training.
  - four-finger `*_mcp_flex_joint` names are semantically misleading: these joints are currently treated as lateral spread / abduction-adduction, not palm flexion.
  - thumb CMC axes were confirmed in SolidWorks; target sign is still handled in scripted control.

### Wrist 2 Result

- `wrist_2_joint` in the experimental branch is `hinge` / revolute with range `-0.8 0.8`.
- `wrist_2_joint_pos` actuator exists with action mapping.
- Single-joint test at `-0.3` and `+0.3` rad passed.
- Palm position barely translates because the joint rotates near the same origin, but palm orientation relative to `wrist_middle_link` changes by about `0.3` rad in both directions.
- Report:
  - `docs\export4_wrist2_joint_fix_report.md`
  - `metadata\export4_wrist2_joint_fix.json`

### Collision Proxy Result

- Static open-hand penetration at default tested ball pose `[0.0, -0.1, 0.21]`: `0.000000 m`.
- This resolves the earlier static-penetration problem for the tested open pose; the old about-13 mm penetration is not reproduced in the tuned branch.
- However, the default `-Y` ball side is visually and metrically far from the closed fingers.
- Mirror-side diagnostic `[0.0, 0.1, 0.21]` is much closer to fingertips and thumb, but still does not produce collision contact with the conservative proxy.
- I did not inflate collision geoms to force contact across a large air gap, because that would hide the grasp-side / target-side issue.
- Reports:
  - `docs\collision_proxy_penetration_diagnosis.md`
  - `metadata\collision_proxy_penetration_diagnosis.json`
  - `docs\collision_proxy_tuning_report.md`
  - `metadata\collision_proxy_tuning_results.json`

### Position-Control Grasp Smoke

- Script:
  - `scripts\demo_grasp_ball_export4_wrist2_collision_tuned.py`
- Default ball `[0.0, -0.1, 0.21]` status: `FAIL_GRASP_SIDE_OR_TARGET_NEEDS_REVIEW`.
- Mirror diagnostic ball `[0.0, 0.1, 0.21]` status: `PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE`.
- Default hold metrics:
  - contacts: `0`
  - max penetration: `0.000000 m`
  - four-finger avg tip-ball distance: about `0.1546 m`
  - thumb-ball distance: about `0.1421 m`
- Mirror hold metrics:
  - contacts: `0`
  - max penetration: `0.000000 m`
  - four-finger avg tip-ball distance: about `0.0608 m`
  - thumb-ball distance: about `0.0616 m`
- Conclusion: wrist2 and actuator flow are usable, but grasp-side / canonical ball placement must be settled before calling this a successful grasp contact demo.

### Adapter And Smoke Dataset

- Adapter unit tests passed.
- `action_dim = 22`; `wrist_2_joint_pos` is included in the action mapping.
- Observation vector includes qpos, qvel, five fingertip site positions, ball pose, and contact summary.
- Report:
  - `docs\export4_adapter_unit_test_report.md`
  - `metadata\export4_adapter_unit_test.json`

Tiny scripted smoke dataset was generated for pipeline validation only:

- `data\export4_scripted_smoke_dataset.npz`
- obs shape: `[750, 86]`
- action shape: `[750, 22]`
- labels:
  - `fail_far_from_ball`: 2 episodes
  - `visual_close_no_contact`: 3 episodes
- Report:
  - `docs\export4_scripted_smoke_dataset_report.md`
  - `metadata\export4_scripted_smoke_dataset_summary.json`

This dataset is not training-ready. It is only for adapter, logging, replay, and data-shape smoke tests.

### Current Blocking / Issue List

- BLOCKER for training: canonical palmar-side ball placement and grasp target signs are not finalized.
- MAJOR: default `-Y` ball side fails the scripted grasp-side check; mirror `+Y` is closer but still no contact with conservative proxy.
- MAJOR: collision proxy needs final fingertip/distal refinement after the correct grasp side is fixed.
- MINOR: `*_mcp_flex_joint` naming remains semantically confusing but should not be renamed yet.

### Next Step Recommendation

1. Decide the canonical palm side in export4 from visual markers and video-retargeting coordinates.
2. Re-run position-control grasp with the canonical side, not both sides mixed.
3. Add small fingertip collision spheres or slightly tune distal proxy radii only after the side is fixed.
4. Keep using the adapter and tiny smoke dataset for pipeline tests.
5. Do not start RL/BC training until grasp-side, contact proxy, and dataset labels are stable.

## Latest Export2 Result

- New source package tested: `D:\tendon_project\hardwares\hand\hand_export2\hand_export`
- Source URDF: `D:\tendon_project\hardwares\hand\hand_export2\hand_export\urdf\hand_export.urdf`
- Source mesh folder: `D:\tendon_project\hardwares\hand\hand_export2\hand_export\meshes`
- Working clean test folder: `D:\tendon_project\simulations\models\hand_stage1_export\clean_mesh_test_export2`
- Working clean mesh folder: `D:\tendon_project\simulations\models\hand_stage1_export\meshes_clean_export2`
- Result: **PASS for static clean mesh alignment**

Export2 is now the preferred clean mesh visual draft. It uses:

- `mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- `mjcf\scene_ball_clean_mesh_export2_draft.xml`
- `scale="1 1 1"` because the export2 STL vertex coordinates are already meter-scale

Export2 checks:

- STL count: 23
- Expected logical links present: 23 / 23
- Missing expected links: 0
- Hash duplicate groups: 0
- Unique file size count: 18
- Unique triangle count: 18
- Oversized bbox over 300 mm: 0
- `thumb_root_connector_link`: 1 STL file, not the previous 3-part manual split
- MuJoCo load:
  - `hand_stage1_clean_mesh_export2_draft.xml`: 24 bodies / 21 joints / 99 geoms / 23 meshes
  - `scene_ball_clean_mesh_export2_draft.xml`: 25 bodies / 22 joints / 101 geoms / 23 meshes / 8 cameras
- Joint smoke test: 21 hinge joints passed numeric qpos sanity
- Scripted clean mesh ball demo: runs and renders staged screenshots

Visual conclusion:

- Palm exists and is in the correct palm/root region.
- Wrist/base, palm, four long fingers, and thumb are visible as one connected hand.
- Finger meshes are attached to the palm region instead of floating away.
- Thumb root and thumb links are attached on the palm side.
- No repeated whole-hand mesh or far-away CAD fragment is visible.
- This looks like a body-local or sufficiently body-local export for the current stage1 visual draft.

Remaining TODO:

- Run a more targeted joint-motion visual audit before treating all joint axes/origins as mechanically final.
- Keep primitive collision geoms for now; do not switch to mesh collision yet.
- Keep `mcp_flex` / `mcp_abd` names unchanged until actual axis semantics are confirmed.

Export2 reports and renders:

- `docs\clean_mesh_export2_test_report.md`
- `metadata\clean_mesh_export2_test_summary.json`
- `docs\clean_mesh_export2_replacement_status.md`
- `docs\clean_mesh_export2_visual_check_report.md`
- `docs\clean_mesh_export2_joint_smoke_test_report.md`
- `metadata\clean_mesh_export2_joint_smoke_test.json`
- `docs\clean_mesh_export2_grasp_visual_report.md`
- `metadata\clean_mesh_export2_grasp_demo.json`
- `docs\visual_checks_export2\`
- `docs\visual_checks_export2\grasp_demo\`

## Clean STL Intake

- Clean STL source copied from: `D:\tendon_project\hardwares\hand\STL`
- Clean test directory: `D:\tendon_project\simulations\models\hand_stage1_export\clean_mesh_test`
- Clean MuJoCo mesh directory: `D:\tendon_project\simulations\models\hand_stage1_export\meshes_clean`
- Scanned STL count: 25
- Expected logical link count: 23
- Present logical links: 23
- Missing expected links: 0
- Exact hash duplicate groups: 0
- Unique file size count: 20
- Unique triangle count: 20
- BBox over 300 mm count: 0
- Result: clean STL validation passed and is more credible than `suspicious_export_mesh`.

Per-file size, triangle count, bbox, hash prefix, logical link mapping, and MJCF filename are in:

- `docs\clean_mesh_test_report.md`
- `metadata\clean_mesh_test_summary.json`

## Thumb Mesh Mapping

- `thumb_metacarpal_link.STL`: present in source, `clean_mesh_test`, and `meshes_clean`.
- `thumb_proximal_link.STL`: present in source, `clean_mesh_test`, and `meshes_clean`.
- `thumb_distal_link.STL`: present in source, `clean_mesh_test`, and `meshes_clean`.
- `thumb_root_connector_link` is represented by 3 STL files:
  - `D18d12H4`
  - `Trapezium1`
  - `Trapezium3`
- These 3 files are mapped as separate mesh geoms on the same `thumb_root_connector_link` body.
- Non-ASCII/space-containing STL names are copied into `meshes_clean` with deterministic ASCII-safe aliases for MJCF loading. Source files were not renamed or deleted.

Details:

- `docs\thumb_mesh_mapping_fix_report.md`

## Generated / Updated Files

- `scripts\validate_clean_mesh_test.py`
- `scripts\check_thumb_mesh_mapping.py`
- `scripts\view_clean_mesh_hand.py`
- `scripts\inspect_clean_mesh_alignment.py`
- `scripts\smoke_test_clean_mesh_joints.py`
- `scripts\render_clean_mesh_visual_checks.py`
- `scripts\render_clean_mesh_joint_motion.py`
- `scripts\demo_grasp_ball_clean_mesh.py`
- `scripts\build_clean_mesh_aligned_draft.py`
- `scripts\render_clean_mesh_aligned_visual_checks.py`
- `mjcf\hand_stage1_clean_mesh_draft.xml`
- `mjcf\scene_ball_clean_mesh_draft.xml`
- `mjcf\hand_stage1_clean_mesh_aligned_draft.xml`
- `mjcf\scene_ball_clean_mesh_aligned.xml`
- `docs\clean_mesh_alignment_report.md`
- `docs\clean_mesh_joint_smoke_test_report.md`
- `docs\clean_mesh_visual_check_report.md`
- `docs\clean_mesh_joint_visual_audit.md`
- `docs\clean_mesh_grasp_visual_report.md`
- `docs\mesh_body_transform_analysis.md`
- `metadata\mesh_body_transform_analysis.json`
- `docs\clean_mesh_aligned_visual_check_report.md`
- `metadata\clean_mesh_aligned_visual_render_summary.json`

## MuJoCo Load Status

- `hand_stage1_clean_mesh_draft.xml`: loads successfully.
  - Bodies: 24
  - Hand hinge joints: 21
  - Geoms: 101
  - Mesh assets: 25
- `scene_ball_clean_mesh_draft.xml`: loads successfully.
  - Bodies: 25
  - Joints: 22 including ball freejoint
  - Geoms: 103
  - Mesh assets: 25
  - Cameras: 8
- `hand_stage1_clean_mesh_aligned_draft.xml`: loads successfully.
  - Bodies: 24
  - Hand hinge joints: 21
  - Geoms: 101
  - Mesh assets: 25
- `scene_ball_clean_mesh_aligned.xml`: loads successfully.
  - Bodies: 25
  - Joints: 22 including ball freejoint
  - Geoms: 103
  - Mesh assets: 25
  - Cameras: 8
- Mesh assets use `scale="0.001 0.001 0.001"` because the STL bbox dimensions are millimeter-like while the MJCF model is meter-scale.
- The suspicious SolidWorks/SW2URDF auto-exported STL set is still isolated and not used.

## Checks Run

- Clean mesh validation: passed.
- Thumb mesh mapping report: generated.
- Viewer load summary: passed with `view_clean_mesh_hand.py --no-viewer`.
- Numeric clean mesh alignment check: passed for scale/path/outlier thresholds.
- Clean mesh joint smoke test: 21 hinge joints passed numeric qpos sanity.
- Multi-view visual screenshots: generated under `docs\visual_checks`.
- Clean mesh joint motion screenshots: generated under `docs\visual_checks\joint_motion`.
- Mesh-to-body transform analysis: generated under `docs\mesh_body_transform_analysis.md` and `metadata\mesh_body_transform_analysis.json`.
- Aligned multi-view visual screenshots: generated under `docs\visual_checks_aligned`.

## Visual Findings

### Original Clean Mesh Draft

- Primitive root/wrist/palm/five-finger kinematic skeleton is still visible and usable.
- Clean CAD `palm_link` mesh exists, and the thumb STL files are no longer missing.
- No single clean STL looks like an entire hand mesh by size/hash/bbox.
- No scale explosion is visible after applying `0.001` scale.
- However, clean STL geoms are not aligned with the primitive joint tree:
  - palm mesh is offset from the primitive palm;
  - many finger phalanx meshes float away from their colored primitive links;
  - thumb root connector parts are visible but do not yet form a clearly connected palm-to-thumb bridge;
  - several clean parts appear as detached CAD chunks around the hand.

Visual conclusion:

- Clean mesh file credibility: PASS
- Clean mesh MuJoCo loading: PASS
- Original clean mesh visual alignment: FAIL / BLOCKER
- Original clean mesh joint visual audit: FAIL / BLOCKER
- Original clean mesh ball demo visual acceptance: SKIPPED

### Aligned Clean Mesh Draft

An MJCF-only translation correction was applied in `hand_stage1_clean_mesh_aligned_draft.xml`. The correction:

- keeps the same joint tree and joint names as the primitive skeleton;
- keeps `scale="0.001 0.001 0.001"`;
- does not edit CAD or STL files;
- adds per-body clean visual `geom pos` offsets to move each clean mesh group center onto that body's primitive reference geometry center;
- applies to all 23 logical clean mesh links, including the 3-part `thumb_root_connector_link` group.

Aligned visual result:

- Palm/root/wrist returned to the expected hand region.
- Five fingers are now attached near the palm instead of floating away.
- Thumb root and thumb links are now adjacent to the palm side.
- No repeated full-hand mesh or large far-away clean mesh fragment is visible.
- Exact joint-center alignment and per-link CAD orientation remain unproven because this pass did not apply unknown rotations.

Aligned visual conclusion:

- Aligned draft generation: PASS
- Aligned MuJoCo loading: PASS
- Aligned visual improvement: PASS
- Aligned final CAD-quality replacement: PARTIAL, not final
- Need SolidWorks/body-local STL confirmation for final clean mesh: YES

## Current Diagnosis

The likely issue is not the old suspicious mesh export. The new STL files are per-link credible by size, triangle count, bbox, and hash. The original visible failure is more consistent with clean STL files being exported in SolidWorks assembly/world coordinates and/or assembly-frame orientation, while MuJoCo expects mesh vertices in each link body's local frame.

The aligned draft confirms that a large part of the problem was translational assembly/world offset: centering each STL group onto the matching primitive body greatly improves the view. It does not prove that mesh rotations are correct. The final fix should still be one of:

- export each link mesh in the link-local/body-local coordinate frame; or
- provide/apply exact per-link mesh transforms from CAD assembly coordinates to URDF/MJCF body-local coordinates.

Do not guess rotational transforms without CAD confirmation.

## Demo Status

- Primitive scripted grasp ball demo remains the valid demo for tonight.
- `demo_grasp_ball_clean_mesh.py` was created, but the original clean mesh draft was not promoted because its visual alignment had a BLOCKER.
- The aligned clean mesh draft is now reasonable enough for a follow-up visual demo/joint-motion audit, but it should still be labeled diagnostic until body-local STL/export-frame confirmation is done.
- Continue scripted grasp work on the primitive skeleton for kinematic truth; use the aligned clean mesh draft only for CAD visual debugging.

## Can This Enter The Next Stage?

Partial:

- Yes for joint tree, joint limits, primitive kinematic checks, and primitive scripted grasp logic.
- Yes for diagnostic clean mesh visualization using `hand_stage1_clean_mesh_aligned_draft.xml`.
- No for final real clean CAD visual replacement, clean mesh collision, or final clean mesh ball-grasp visual acceptance until body-local STL/export-frame alignment is confirmed.

## Manual Work For Tomorrow

1. In SolidWorks, confirm whether manual per-link STL exports are emitted in assembly/world coordinates or part/link-local coordinates.
2. Re-export or transform clean STL so each file is body-local to its corresponding URDF/MJCF link.
3. If SolidWorks allows export coordinate-system selection, export each STL using the link-local coordinate system matching the URDF/MJCF body frame.
4. If link-local STL export is not practical, export or document the exact CAD assembly-to-link transform for each mesh so MJCF `pos`/`quat` can be set explicitly.
5. Recheck first: `palm_link`, all long-finger phalanx links, `thumb_metacarpal_link`, `thumb_proximal_link`, `thumb_distal_link`, and the 3 `thumb_root_connector_link` part STL files.
6. Confirm the rigid-body grouping for `thumb_root_connector_link` before merging or changing the three-part mapping.
7. Keep `mcp_flex` / `mcp_abd` names unchanged until the actual motion axes are confirmed.
8. After corrected mesh frames are available, rerun:
   - `python scripts\validate_clean_mesh_test.py`
   - `python scripts\render_clean_mesh_visual_checks.py`
   - `python scripts\smoke_test_clean_mesh_joints.py`
   - `python scripts\render_clean_mesh_joint_motion.py`
   - then `python scripts\demo_grasp_ball_clean_mesh.py` only if visual alignment is PASS/PARTIAL with no BLOCKER.

## Next Step Recommendation

Keep `hand_stage1_primitive.xml` and `scene_ball_primitive.xml` as the current runnable stage1 skeleton. Use `hand_stage1_clean_mesh_aligned_draft.xml` as the current diagnostic clean visual draft. Treat `hand_stage1_clean_mesh_draft.xml` as the unaligned baseline, and do not promote either clean mesh version to final CAD visual status until SolidWorks body-local mesh export or exact per-link transforms are confirmed.

## Export2 Retry Update - 2026-05-20

New SolidWorks export tested:

- Source: `D:\tendon_project\hardwares\hand\hand_export2\hand_export`
- Clean mesh directory: `meshes_clean_export2`
- Main clean mesh MJCF: `mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- Ball scene: `mjcf\scene_ball_clean_mesh_export2_draft.xml`

Current export2 status:

- Export2 clean STL set is credible for visual use: 23 meshes, no hash duplicates, reasonable bbox sizes.
- Export2 MJCF loads successfully.
- Export2 clean mesh uses `scale="1 1 1"` because these STL files are already meter-scale.
- Static clean mesh visual alignment is much better than the earlier manual STL set.

Latest ball-grasp retry:

- Added `scripts\run_export2_ballpos_retry.py`.
- Added `scripts\demo_grasp_ball_export2_retry.py`.
- Added retry scene `mjcf\scene_ball_clean_mesh_export2_retry.xml`.
- Added report `docs\export2_collision_and_ballpos_retry_report.md`.
- Rendered screenshots under:
  - `docs\visual_checks_export2_retry\low_penetration`
  - `docs\visual_checks_export2_retry\balanced_thumb`
  - `docs\visual_checks_export2_retry\live_demo`

Collision and overlap conclusion:

- Clean STL geoms are visual-only (`contype="0"`, `conaffinity="0"`), so they do not collide with the ball yet.
- Collision currently comes from primitive collision geoms.
- The earlier ball position `[0.01, -0.045, 0.215]` started inside the hand collision shell:
  - open hand: 4 ball contacts, min contact distance `-0.012230 m`;
  - hold: 6 ball contacts, min contact distance `-0.022275 m`.
- The conservative retry ball position `[0.0, -0.1, 0.195]` removes initial overlap:
  - open hand: 0 ball contacts;
  - hold: 2 ball contacts, max penetration about `0.005000 m`;
  - four-fingertip mean distance at hold: about `0.034357 m`.

Direction conclusion:

- Globally flipping the closing axes was tested and rejected because fingertip-to-ball distance got worse.
- Four long fingers now close toward the retry ball position and visually wrap the ball.
- Thumb opposition is still not correct. Flipping only thumb CMC/MCP/IP axes did not bring the thumb tip across to the ball.
- TODO: confirm thumb CMC/MCP/IP joint frames and axes in SolidWorks/URDF before trying to "fix" thumb semantics in MJCF.

Recommended current command:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\demo_grasp_ball_export2_retry.py --viewer
```

This is still a visual/kinematic smoke test, not a final physical grasp. To move toward physical grasp, the next step is simplified collision proxies plus position actuators/controllers, not RL or tendon routing.

## Collision Proxy + Position Control Update - 2026-05-20

Generated new visual-clean + collision-proxy model:

- `mjcf\hand_stage1_visual_clean_collision_proxy.xml`
- `mjcf\scene_ball_visual_clean_collision_proxy.xml`
- `docs\collision_proxy_design_report.md`
- `docs\actuator_setup_report.md`
- `metadata\visual_clean_collision_proxy_summary.json`

Model status:

- Clean STL meshes are still visual-only and do not collide.
- Collision uses simplified primitive proxy geoms only.
- No suspicious STL is used.
- Joint tree and joint names are unchanged.
- Fingertip sites retained: 5.
- Compiled hand model:
  - Bodies excluding world: 23
  - Hinge joints: 21
  - Position actuators: 21
  - Mesh assets: 23
  - Collision proxy geoms: 28 in the hand model, 30 in the ball scene including ball/ground

Collision-mask fix:

- Initial proxy pass caused hand-hand self-collision and moved fingers even when open target was zero.
- Fixed by setting hand proxy geoms to `contype=1`, `conaffinity=2`.
- Ball geom is `contype=2`, `conaffinity=1`.
- Ground is `contype=1`, `conaffinity=3`.
- Result: hand proxies collide with ball/ground but not with other hand proxy geoms.

Position-control grasp demo:

- Script: `scripts\demo_grasp_ball_position_control.py`
- Scene: `mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Report: `docs\position_control_grasp_ball_report.md`
- Metadata: `metadata\position_control_grasp_ball.json`
- Screenshots: `docs\visual_checks_position_control_grasp`

Position-control result with low-penetration ball position `[0.0, -0.1, 0.195]`:

- Hand joints are controlled with `data.ctrl` through position actuators.
- Hand `qpos` is not directly written during the demo.
- Runtime gravity is zero by default for this ball-placement smoke test.
- `--pin-ball` run was used for the saved report because the free ball is pushed away before a stable grasp controller exists.
- Open hand:
  - Ball contacts: 0
  - Max penetration: 0
  - Hand qpos targets/actuals remain at zero after collision mask fix
- Hold:
  - Ball contacts: 2
  - Max penetration: about `0.00394 m`
  - Mean four-fingertip distance: about `0.03520 m`
  - Thumb-to-ball distance: about `0.17048 m`

Interpretation:

- Four long fingers are usable for scripted collision-proxy grasp smoke tests.
- The ball no longer starts overlapped with the open hand.
- Collision proxy is now good enough for scripted contact checking.
- This is not yet a stable physical grasp because the ball must be pinned for visual/contact smoke testing; a real free-ball grasp needs better thumb opposition, palm support/contact tuning, and controller work.

Thumb opposition audit:

- Script: `scripts\thumb_opposition_audit.py`
- Report: `docs\thumb_opposition_audit.md`
- Metadata: `metadata\thumb_opposition_candidates.json`
- Screenshots: `docs\visual_checks_thumb_opposition`

Audit result:

- Baseline thumb-to-ball distance: about `0.1706 m`.
- Best scanned pose among CMC/MCP/IP combinations:
  - `thumb_cmc_joint=-0.8`
  - `thumb_mcp_joint=1.2`
  - `thumb_ip_joint=0.0`
  - thumb-to-ball distance: about `0.1549 m`
- Single-axis trends:
  - `thumb_cmc_joint`: negative direction is slightly better than positive, but not enough.
  - `thumb_mcp_joint`: positive flexion helps most, best at `1.2`.
  - `thumb_ip_joint`: positive flexion helps slightly, best at `1.2`.
- Even the best scanned pose leaves the thumb far from the ball; thumb opposition is not solved by simply flipping an axis or tuning scripted angles.

Thumb TODO:

- Manually inspect `thumb_cmc_axis`, `thumb_mcp_axis`, and `thumb_ip_axis` in SolidWorks/URDF.
- Confirm thumb CMC body frame orientation and whether the modeled CMC has the required opposition DOF.
- Do not rename or flip thumb axes automatically until CAD/URDF semantics are confirmed.

Shadow structure comparison:

- Report: `docs\shadow_structure_comparison.md`
- Metadata: `metadata\shadow_structure_comparison.json`
- Local Shadow model found: `D:\tendon_project\simulations\models\shadow_hand\right_hand.xml`

Structure summary:

- hand_stage1 current model:
  - Bodies excluding world: 23
  - Joints: 21
  - Actuators: 21
  - Fingertip-like sites: 5
  - Tendons: 0
- Local Shadow right_hand:
  - Bodies excluding world: 25
  - Joints: 24
  - Actuators: 24
  - Fingertip-like sites by name: 0
  - Tendons in this local MJCF: 0

Current go/no-go:

- Continue Shadow structure-level comparison: yes.
- Continue scripted grasp smoke tests: yes, with collision proxy and position actuators.
- Start RL or imitation training: no.
- Promote as Shadow-equivalent hand: no.
- Promote as final physical grasp model: no.

Next manual checks:

1. Confirm thumb CMC/MCP/IP axes and body frames in SolidWorks/URDF.
2. Confirm whether thumb CMC should have another opposition DOF or a different axis orientation.
3. Confirm final body-local STL export convention even though export2 visual alignment is currently usable.
4. Tune collision proxy sizes around palm/thumb after mechanical axes are confirmed.
5. Add a real free-ball controller only after thumb opposition and collision proxies are more reliable.

## Next Validation Update - 2026-05-20

This stage is not a failure. The stage1 MuJoCo line has now run through the intended prototype ladder:

- clean visual model loads;
- collision proxy model loads;
- 21 position actuators load;
- four-finger position-control ball smoke test is usable;
- thumb opposition is the current largest blocker.

New outputs:

- `scripts\analyze_thumb_mechanical_semantics.py`
- `scripts\sweep_four_finger_grasp_ball.py`
- `docs\thumb_mechanical_semantics_report.md`
- `metadata\thumb_mechanical_semantics.json`
- `docs\solidworks_thumb_axis_checklist.md`
- `docs\four_finger_grasp_sweep_report.md`
- `metadata\four_finger_grasp_sweep.json`
- `docs\collision_proxy_refinement_report.md`
- `docs\shadow_stage1_gap_report.md`

Thumb mechanical semantics:

- Thumb chain parent/child structure is present and reasonable:
  - `palm_link`
  - `thumb_root_connector_fixed_joint`
  - `thumb_root_connector_link`
  - `thumb_cmc_joint`
  - `thumb_metacarpal_link`
  - `thumb_mcp_joint`
  - `thumb_proximal_link`
  - `thumb_ip_joint`
  - `thumb_distal_link`
- `thumb_cmc_joint`, `thumb_mcp_joint`, and `thumb_ip_joint` all exist in the current MJCF/URDF-derived model.
- Positive single-joint motion does not meaningfully move `thumb_tip_site` toward the ball.
- `thumb_cmc_joint` positive motion slightly increases thumb-to-ball distance in the tested zero pose; negative motion helps only slightly.
- Best previous scanned combination remains far from a useful opposition pose:
  - `thumb_cmc_joint=-0.8`
  - `thumb_mcp_joint=1.2`
  - `thumb_ip_joint=0.0`
  - thumb-to-ball distance about `0.1549 m`
- Most likely first manual check: `thumb_cmc_joint` axis/body frame and the intended CMC opposition DOF.
- Do not automatically flip or rename thumb axes until SolidWorks CSYS/axis semantics are confirmed.

SolidWorks thumb checklist:

- Highest priority for tomorrow is checking `thumb_cmc_axis`, `thumb_mcp_axis`, `thumb_ip_axis`.
- Also check `thumb_cmc_csys`, `thumb_mcp_csys`, and `thumb_ip_csys`, especially whether local Z is the intended exported hinge axis.
- Confirm whether `thumb_root_connector_link` should be fixed to palm and whether D18d12H4 / Trapezium / Os metacarpale parts are assigned to the correct thumb/root bodies.

Four-finger grasp sweep:

- Script: `scripts\sweep_four_finger_grasp_ball.py`
- Report: `docs\four_finger_grasp_sweep_report.md`
- Metadata: `metadata\four_finger_grasp_sweep.json`
- Scene: `mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Sweep grid:
  - x: `[-0.02, 0, 0.02]`
  - y: `[-0.08, -0.10, -0.12]`
  - z: `[0.18, 0.195, 0.21]`
- Thumb policy: thumb joints held open at `0 rad`.
- Gravity: disabled.
- Ball: pinned for smoke testing.
- Results:
  - PASS: 15
  - PARTIAL: 10
  - FAIL: 2
  - open-hand contact count: 0 for all 27 positions
  - best position: `[0.0, -0.1, 0.21]`
  - best hold contacts: 3
  - best hold max penetration: about `0.00674 m`
  - best hold mean four-fingertip distance: about `0.03571 m`
- Interpretation: four long fingers are good enough for continued scripted smoke testing, but this is not a stable free-object grasp.

Collision proxy refinement:

- Current palm proxy is not causing open-hand ball overlap in the tested grid.
- Current finger capsules are usable for four-finger smoke testing.
- Some side/far positions show too much hold penetration, up to about `0.02237 m`.
- Dedicated fingertip collision spheres are not yet present; distal capsules are acting as the current fingertip contact approximation.
- Thumb proxy should not be tuned to hide the thumb kinematic issue; repair thumb axis/csys first.

Shadow stage1 gap:

- Continue Shadow structure-level comparison: yes.
- Continue scripted grasp task scaffolding: yes.
- Current hand_stage1 remains a stage1 kinematic + clean visual + collision-proxy prototype.
- It is not Shadow-equivalent.
- Shadow-style task API work can continue after keeping this distinction explicit.

Current go/no-go:

- Continue four-finger scripted grasp smoke tests: GO.
- Continue Shadow structure-level comparison: GO.
- Continue primitive/collision proxy refinement: GO.
- Start RL/BC/training: NO-GO.
- Promote as final physical grasp model: NO-GO.
- Promote as Shadow-equivalent hand: NO-GO.

Tomorrow's highest-priority manual checks:

1. Verify `thumb_cmc_axis` passes through the real CMC rotation center and has the intended opposition direction.
2. Verify `thumb_cmc_csys` local Z axis matches the exporter hinge axis.
3. Verify `thumb_mcp_axis` and `thumb_ip_axis` are flexion axes, not accidental lateral/assembly-frame axes.
4. Confirm whether the modeled CMC has enough DOF for opposition or whether the current stage1 thumb base is missing a required motion.
5. Only after thumb axis/csys confirmation, retest `thumb_opposition_audit.py` and position-control grasp.

## Export3 Validation Update - 2026-05-21

Export3 source:

- `D:\tendon_project\hardwares\hand\hand_export3`

Generated export3 workspace:

- `export3\`
- `meshes_export3\`
- `mjcf\hand_stage1_export3_raw_mesh.xml`
- `mjcf\hand_stage1_export3.xml`
- `mjcf\scene_ball_export3.xml`

Generated scripts:

- `scripts\process_export3.py`
- `scripts\view_export3_hand.py`
- `scripts\smoke_test_export3_joints.py`
- `scripts\thumb_export3_opposition_audit.py`
- `scripts\demo_grasp_ball_export3_position_control.py`

Generated reports:

- `docs\export3_import_report.md`
- `docs\export3_urdf_integrity_report.md`
- `metadata\export3_urdf_summary.json`
- `docs\export3_link_joint_tree.md`
- `metadata\export3_link_joint_tree.json`
- `docs\export3_mesh_diagnostics.md`
- `metadata\export3_mesh_manifest.json`
- `docs\export3_mujoco_load_report.md`
- `docs\export3_joint_smoke_test_report.md`
- `metadata\export3_joint_smoke_test.json`
- `docs\export3_thumb_opposition_audit.md`
- `metadata\export3_thumb_opposition_candidates.json`
- `docs\export3_grasp_ball_report.md`
- `metadata\export3_grasp_ball_position_control.json`
- `docs\visual_checks_export3_thumb\`
- `docs\visual_checks_export3_grasp\`

Import result:

- Export3 successfully imported from the source directory.
- URDF found: `export3\urdf\hand_export3.urdf`
- Package file found: `export3\package.xml`
- Mesh directory found: `export3\meshes`
- Mesh file count: 24
- Multiple URDF: no
- Empty_Link: no

URDF / tree result:

- Links: 24
- Joints: 23
- Revolute joints: 21
- Fixed joints: 2
- Duplicate links: none
- Duplicate joints: none
- Missing parent/child: none
- Revolute joints missing limits: none
- Mesh paths unresolved/missing: none
- `wrist_2_joint` is fixed in export3.
- Old `thumb_cmc_joint` is not present.

Export3 thumb chain:

```text
palm_link
-> thumb_root_connector_fixed_joint
-> thumb_root_connector_link
-> thumb_cmc_abd_joint
-> thumb_trapezium1_link
-> thumb_cmc_flex_joint
-> thumb_metacarpal_link
-> thumb_mcp_joint
-> thumb_proximal_link
-> thumb_ip_joint
-> thumb_distal_link
```

Status: PASS. The exported thumb chain now has the intended 2-DoF CMC structure.

Mesh result:

- STL count: 24
- Hash duplicate groups: 0
- Unique file size count: 19
- Unique triangle count: 19
- All STL size/triangle identical: no
- `palm_link` present and large relative to fingertip links.
- `index_distal_link` is smaller than `palm_link`.
- `hand_base_link` is not identical to `palm_link` or index distal.
- `thumb_trapezium1_link`, `thumb_root_connector_link`, `thumb_metacarpal_link`, `thumb_proximal_link`, and `thumb_distal_link` are present.
- Mesh scale selected for MJCF: `1 1 1`
- Result: clean/credible for current visual-only use.

MuJoCo load:

- `hand_stage1_export3.xml`: loads.
  - Bodies including world: 25
  - Hinge joints: 21
  - Position actuators: 21
  - Geoms: 53
  - Sites: 5
  - Meshes: 24
- `scene_ball_export3.xml`: loads.
  - Bodies including world: 26
  - Joints including ball freejoint: 22
  - Position actuators: 21
  - Geoms: 55
  - Sites: 5
  - Meshes: 24
- Clean export3 STL meshes are visual-only.
- Collision remains simplified primitive proxy.
- No suspicious mesh is used.

Joint smoke test:

- 21 hinge joints moved numerically.
- `thumb_cmc_abd_joint`: present and movable.
- `thumb_cmc_flex_joint`: present and movable.
- Old `thumb_cmc_joint`: absent.
- `wrist_2_joint`: not a hinge because export3 exported it as fixed.

Thumb opposition:

- Audit script: `scripts\thumb_export3_opposition_audit.py`
- Best metric candidate:
  - `thumb_cmc_abd_joint=-0.8`
  - `thumb_cmc_flex_joint=0.4`
  - `thumb_mcp_joint=0.0`
  - `thumb_ip_joint=1.2`
- Best thumb-ball distance: about `0.08582 m`
- Best thumb-index distance: about `0.05354 m`
- Improvement vs old thumb reference around `0.1549 m`: about `0.06908 m`
- Visual judgment: improved and usable for export3 scripted smoke tests, but still not a final Shadow-like opposition clamp.
- Note: requested negative `thumb_cmc_flex_joint` samples are clamped by the exported joint limit because its range starts at 0.

Export3 grasp smoke test:

- Script: `scripts\demo_grasp_ball_export3_position_control.py`
- Scene: `mjcf\scene_ball_export3.xml`
- Default ball position: `[0.0, -0.1, 0.21]`
- Control: position actuators through `data.ctrl`
- Ball: pinned
- Gravity: disabled
- Open hand:
  - Ball contacts: 0
  - Max penetration: 0
- Hold:
  - Ball contacts: 3
  - Max penetration: about `0.00696 m`
  - Mean four-fingertip distance: about `0.03572 m`
  - Thumb-ball distance: about `0.08581 m`
  - Thumb-index distance: about `0.07561 m`
- Visual result: four fingers still wrap the ball, and the thumb now approaches the ball-side region. This is better than export2, but still smoke-test quality.

Current go/no-go after export3:

- Continue Shadow structure-level comparison: GO.
- Continue Shadow-style scripted grasp scaffolding: GO.
- Continue collision proxy refinement: GO.
- Promote export3 as better than previous thumb model: GO, with caveat.
- Start RL/BC/training: NO-GO.
- Claim Shadow equivalence: NO-GO.
- Treat as stable free-object grasp: NO-GO.

Issue levels:

- BLOCKER: none for continuing scripted smoke tests.
- MAJOR: thumb opposition is improved but not mechanically final; collision proxy is still coarse; ball remains pinned in the demo.
- MAJOR: several open-hand targets are clamped by exported lower limits, so `0 rad` should not be assumed to mean mechanical neutral for every joint.
- MINOR: `wrist_2_joint` changed to fixed in export3; this may be intended, but should be confirmed against the stage1 root-wrist design.

Tomorrow's manual checks:

1. Confirm whether `wrist_2_joint` being fixed in export3 is intended.
2. Confirm `thumb_cmc_abd_joint` and `thumb_cmc_flex_joint` axes/CSYS in SolidWorks.
3. Confirm `thumb_cmc_flex_joint` lower limit of 0 and whether negative flex values should be physically allowed.
4. Confirm whether the best metric thumb pose also looks mechanically plausible in SolidWorks.
5. Tune fingertip and palm collision proxies only after the thumb axis/limit semantics are accepted.
6. Move from pinned-ball smoke test to free-ball zero-gravity test only after collision proxy tuning.

## Shadow-Style Scripted Task Update - 2026-05-22

Goal:

- Test how far export3 can go as a Shadow-style scripted grasp scaffold without training, tendon routing, CAD edits, STL edits, or joint tree/name changes.

Generated:

- `scripts\run_export3_shadow_style_scripted_task.py`
- `docs\export3_shadow_style_scripted_report.md`
- `metadata\export3_shadow_style_scripted_trials.json`
- `docs\visual_checks_export3_shadow_style\`

Sweep result:

- Trials: 225
- Modes: `pinned`, `free_zero_g`, `free_gravity`
- Capability best level: `pinned_wrap`
- Classification counts:
  - `PINNED_WRAP_PASS`: 58
  - `PINNED_PARTIAL`: 17
  - `WRAP_BEFORE_RELEASE_ONLY`: 118
  - `PARTIAL_OR_FAIL`: 32

Best pinned wrap:

- Ball position: `[0.0, -0.09, 0.21]`
- Finger scale: `1.0`
- Thumb pose:
  - `thumb_cmc_abd_joint=-0.8`
  - `thumb_cmc_flex_joint=0.0`
  - `thumb_mcp_joint=0.0`
  - `thumb_ip_joint=0.4`
- Hold contacts: `5`
- Max penetration: about `0.00233 m`
- Mean four-fingertip distance: about `0.03992 m`
- Thumb-ball distance: about `0.07693 m`

Release tests:

- Zero-gravity release retention: not achieved.
- Best zero-gravity checked case had a similar pre-release wrap but drifted about `0.08102 m` after release.
- Gravity release retention: not achieved.
- Best gravity checked case had a pre-release wrap but the ball drifted/fell about `0.19088 m` after release.
- Visual checks confirm the ball leaves the hand after release.

Current interpretation:

- This is not a failure of stage1. Export3 can run a Shadow-style scripted task shell and can do pinned-ball wrap/contact smoke tests.
- The current maximum demonstrated capability is not stable free-object grasp.
- The model should not be used for RL/BC/training yet.
- The next blockers are collision proxy fidelity, contact/friction tuning, actuator gain tuning, and final thumb axis/limit semantics.

Go / no-go:

- Continue Shadow-style scripted scaffolding: GO.
- Continue collision/contact tuning: GO.
- Continue structure-level Shadow comparison: GO.
- Claim stable object grasp: NO-GO.
- Start training: NO-GO.

## Diagnostic Training Update - 2026-05-23

Training status:

- A diagnostic export3 training scaffold has been created.
- This is not a promoted `stable_grasp` baseline.
- This does not change the conclusion that free-object stable grasp is not solved.

Generated:

- `scripts\collect_export3_scripted_dataset.py`
- `scripts\train_export3_bc.py`
- `scripts\eval_export3_bc.py`
- `data\export3_scripted_pinned_wrap_v0.npz`
- `checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- `docs\export3_diagnostic_training_status.md`
- `docs\export3_scripted_dataset_v0_report.md`
- `docs\export3_bc_pinned_wrap_v0_report.md`
- `docs\export3_bc_pinned_wrap_v0_eval_report.md`

Dataset:

- Mode: pinned export3 scripted wrap.
- Episodes: 75.
- Samples: 6000.
- Observation dimension: 109.
- Action dimension: 21.
- Observation now includes stage one-hot and thumb target pose. These were needed because the first BC rollout failed from stage ambiguity and thumb-pose averaging.

BC result:

- Model: state-based MLP BC.
- Trained on `PINNED_WRAP_PASS` samples.
- Final normalized validation MSE: about `0.000187`.
- Raw action validation RMSE: about `0.00405`.

Online rollout result:

- Eval episodes: 30.
- Default eval speed: `2.5`.
- Action smoothing: `0.0`.
- `PINNED_WRAP_PASS`: 19.
- `PINNED_PARTIAL`: 11.
- Pinned-wrap pass rate: about `0.633`.
- Mean hold contacts: about `3.07`.
- Mean hold penetration: about `0.00796 m`.

Findings:

- Offline BC fit alone was not sufficient; online rollout exposed distribution shift.
- Adding stage one-hot, thumb target pose, and training-action-envelope clipping was necessary.
- Action smoothing `0.15` degraded rollout performance; direct clipped actuator targets worked better for this diagnostic model.

Current go/no-go:

- Continue diagnostic BC/DAgger scaffold: GO.
- Treat BC pinned-wrap as useful engineering signal: GO.
- Start free-object stable-grasp training baseline: NO-GO.
- Start PPO/DAPG benchmark training: NO-GO until zero-g release and collision proxy are more stable.

## DAgger Diagnostic Update - 2026-05-23

Scope:

- Continued the export3 diagnostic training line only.
- No CAD, STL, joint tree, joint name, tendon routing, or RL changes.
- This remains pinned-wrap training, not stable free-object grasp.

Generated / updated:

- `scripts\collect_export3_dagger_dataset.py`
- `scripts\train_export3_bc.py`
- `data\export3_dagger_pinned_wrap_v1.npz`
- `data\export3_dagger_failonly_pinned_wrap_v1.npz`
- `checkpoints\bc_hand_stage1_export3_dagger_v1.pth`
- `checkpoints\bc_hand_stage1_export3_dagger_failonly_v1.pth`
- `checkpoints\bc_hand_stage1_export3_dagger_failonly_ft_v1.pth`
- `docs\export3_dagger_dataset_v1_report.md`
- `docs\export3_dagger_failonly_dataset_v1_report.md`
- `docs\export3_bc_dagger_v1_eval_all75_report.md`
- `docs\export3_bc_dagger_failonly_v1_eval_all75_report.md`
- `docs\export3_bc_dagger_failonly_ft_v1_eval_all75_report.md`
- `docs\export3_bc_v0_failure_buckets.md`

75-episode comparison:

| Model | Pass / 75 | Pass rate | Mean hold contacts | Mean hold penetration |
|---|---:|---:|---:|---:|
| BC v0 | 63 | 0.840 | 3.28 | 0.00731 m |
| DAgger all-states v1 | 58 | 0.773 | 2.91 | 0.00699 m |
| DAgger fail-only v1 | 58 | 0.773 | 3.01 | 0.00732 m |
| DAgger fail-only fine-tune v1 | 56 | 0.747 | 2.87 | 0.00787 m |

Conclusion:

- BC v0 remains the best current diagnostic pinned-wrap checkpoint.
- Naive DAgger aggregation did not improve rollout.
- Fail-only DAgger repaired 2 previous partial cases but regressed 7 previous pass cases.
- The current DAgger v1 checkpoints should be kept as diagnostic artifacts, not promoted.
- BC v0 partial cases are concentrated around ball `[0.000, -0.100, 0.195]`, ball `[0.000, -0.100, 0.210]`, thumb rank `5`, and finger scale `1.15`.

Current go/no-go:

- Continue scripted task and structure-level Shadow work: GO.
- Continue targeted dataset/debug work: GO.
- Promote DAgger v1: NO-GO.
- Start stable free-object RL training: NO-GO.

Next recommended training work:

1. Bucket the 12 BC v0 partial cases by ball position, finger scale, and thumb rank.
2. Collect more successful scripted data around those exact buckets instead of broad DAgger aggregation.
3. Add zero-g release labels/eval only after pinned-wrap exceeds 90 percent.
4. Revisit RL/DAPG/PPO only after collision/contact and release behavior are stable enough to define a meaningful reward.

## Export3 Thumb Limit Tuning Update - 2026-05-23

Scope:

- Returned to SolidWorks-informed thumb mechanical semantics.
- No CAD, STL, link tree, joint name, tendon routing, or training changes.
- Generated an experimental MJCF variant instead of overwriting the main export3 model.

User-confirmed SolidWorks semantics:

- `D18d12H4.STEP` and `Trapezium3.STEP` are fixed root parts and belong under `thumb_root_connector_link`.
- `Trapezium1.STEP` is the first moving CMC-abduction link and belongs to `thumb_trapezium1_link`.
- `Os metacarpale I 3.STEP` is after the second CMC joint and belongs to `thumb_metacarpal_link`.
- `thumb_cmc_abd_joint` negative direction is useful for opposition and must be allowed.
- `thumb_mcp_axis` has been checked in SolidWorks and is mechanically credible.

Generated:

- `mjcf\hand_stage1_export3_thumb_limit_tuned.xml`
- `mjcf\scene_ball_export3_thumb_limit_tuned.xml`
- `scripts\build_export3_thumb_limit_tuned.py`
- `scripts\thumb_export3_limit_tuning_audit.py`
- `scripts\demo_grasp_ball_export3_thumb_tuned.py`
- `docs\export3_thumb_limit_tuned_model_report.md`
- `docs\export3_thumb_limit_tuning_audit.md`
- `metadata\export3_thumb_limit_tuning_candidates.json`
- `docs\visual_checks_export3_thumb_limit_tuning\`
- `docs\export3_grasp_ball_thumb_tuned_report.md`
- `metadata\export3_grasp_ball_thumb_tuned.json`
- `docs\visual_checks_export3_thumb_tuned_grasp\`

Experimental thumb limits used:

| Joint | Experimental range |
|---|---:|
| `thumb_cmc_abd_joint` | `-1.2 1.2` |
| `thumb_cmc_flex_joint` | `-1.2 1.2` |
| `thumb_mcp_joint` | `-0.2 1.4` |
| `thumb_ip_joint` | `-0.2 1.2` |

Grid search result:

- Candidate count: 2430.
- Best scripted thumb pose:
  - `thumb_cmc_abd_joint = -1.2`
  - `thumb_cmc_flex_joint = 0.6`
  - `thumb_mcp_joint = -0.2`
  - `thumb_ip_joint = 1.2`
- Static audit thumb-ball distance: about `0.0343 m`.
- Static audit thumb-index distance: about `0.0290 m`.
- Old export3 best thumb-ball reference: about `0.0858 m`.
- The tuned pose enters the `0.06 m` thumb-ball target region.

Thumb-tuned scripted grasp result:

- Scene: `scene_ball_export3_thumb_limit_tuned.xml`.
- Default ball position: `[0.0, -0.1, 0.21]`.
- Open hand starts with `0` contacts.
- Hold thumb-ball distance: about `0.0343 m`.
- Hold thumb-index distance: about `0.0296 m`.
- Hold mean four-fingertip distance: about `0.0359 m`.
- Hold contact count: `3`.
- Hold max penetration: about `0.0066 m`.
- Visual check: the thumb now moves to the opposite side of the ball and forms a visibly better pinch/wrap with the long fingers.

Interpretation:

- Thumb opposition improved significantly for scripted smoke testing.
- The best target uses the expanded limit boundaries, especially `thumb_cmc_abd=-1.2`, `thumb_mcp=-0.2`, and `thumb_ip=1.2`; these are experimental until mechanically accepted.
- No obvious thumb fly-away or severe visual flip is visible in the saved screenshots.
- This remains pinned-ball scripted position control with primitive collision proxy, not stable free-object grasp.

Current go/no-go:

- Continue Shadow-style scripted grasp scaffold: GO.
- Use tuned thumb pose for scripted smoke tests: GO.
- Promote tuned limits to final mechanical limits: WAIT FOR SOLIDWORKS REVIEW.
- Start RL/BC training from tuned pose: NO-GO until zero-g/free-ball behavior and collision/contact fidelity are stronger.

Next checks:

1. In SolidWorks, confirm whether `thumb_cmc_abd=-1.2`, `thumb_mcp=-0.2`, and `thumb_ip=1.2` are physically acceptable extremes.
2. If those extremes are acceptable, use this tuned thumb pose as the scripted grasp target.
3. If the extremes are not acceptable, rerun `thumb_export3_limit_tuning_audit.py` with narrower ranges.
4. Refine collision proxy around index/middle distal links because contact penetration is now the next visible limitation.

## Thumb Missing-Joint / Axis Re-Audit - 2026-05-23

Reason:

- User visual feedback: thumb joints still look reversed and the thumb root appears to be missing a joint.
- Response: stopped target tuning and audited the actual export3 URDF/MJCF thumb chain.

Generated:

- `scripts\audit_export3_thumb_missing_joint_and_axis.py`
- `docs\export3_thumb_missing_joint_axis_audit.md`
- `metadata\export3_thumb_missing_joint_axis_audit.json`
- `docs\visual_checks_export3_thumb_axis_audit\`
- `docs\solidworks_export4_thumb_root_joint_fix_plan.md`

Actual export3 thumb chain:

```text
palm_link
-> thumb_root_connector_fixed_joint [fixed]
-> thumb_root_connector_link
-> thumb_cmc_abd_joint [revolute]
-> thumb_trapezium1_link
-> thumb_cmc_flex_joint [revolute]
-> thumb_metacarpal_link
-> thumb_mcp_joint [revolute]
-> thumb_proximal_link
-> thumb_ip_joint [revolute]
-> thumb_distal_link
```

Finding:

- Export3 contains only four active thumb joints: `thumb_cmc_abd_joint`, `thumb_cmc_flex_joint`, `thumb_mcp_joint`, `thumb_ip_joint`.
- If the real thumb root should have another active opposition/root/twist joint, that joint is not present in export3 URDF/MJCF.
- There is no intermediate exported link between `thumb_root_connector_link` and `thumb_trapezium1_link` other than `thumb_cmc_abd_joint`.
- `thumb_cmc_abd_joint` is reversed relative to intuitive positive-opposition semantics: `+0.6 rad` moves thumb farther from ball/index, while `-0.6 rad` moves toward ball/index.

Updated interpretation:

- The previous thumb limit tuning was a numeric workaround, not a mechanical correction.
- Do not promote the tuned thumb limits until export4 fixes or explicitly accepts the missing joint/sign convention.
- Best next step is SolidWorks/export4 correction, not more MuJoCo target search.

Export4 request:

1. Confirm whether an additional active thumb root joint should exist between `thumb_root_connector_link` and `thumb_trapezium1_link`, or between `palm_link` and `thumb_root_connector_link`.
2. If yes, add/export a distinct intermediate link and joint; URDF needs a serial link between two revolute joints.
3. Flip `thumb_cmc_abd_joint` axis/CSYS if positive angle is intended to mean opposition toward palm/index.
4. Re-export as `hand_export4` without overwriting export3.

## Palm-Side / Grasp-Side Orientation Audit - 2026-05-24

Reason:

- User observed that the current grasp demo looks like the hand is grasping with the wrong side / palm flipped.
- Thumb target tuning is paused until palm side, ball side, and four-finger closure direction are understood.

Generated:

- `scripts\audit_export3_palm_orientation_and_grasp_side.py`
- `mjcf\scene_ball_export3_palm_orientation_debug.xml`
- `docs\export3_palm_orientation_audit.md`
- `metadata\export3_palm_orientation_audit.json`
- `docs\export3_ball_side_mirror_test.md`
- `docs\export3_four_finger_flex_direction_audit.md`
- `docs\visual_checks_export3_palm_orientation\`
- `docs\visual_checks_export3_finger_direction\`

Palm orientation findings:

- Finger extension direction is approximately `[0.105, -0.247, 0.963]`.
- Thumb side direction is approximately `[-0.575, 0.197, 0.794]`.
- Inferred palmar normal from `finger_forward x thumb_side`, signed to align with scripted close, is approximately `[-0.511, -0.845, -0.160]`.
- Current ball `[0.0, -0.1, 0.21]` lies on that inferred palm-closing side.
- Mirrored ball `[0.0, 0.1, 0.21]` lies on the opposite/dorsal/far side.

Ball mirror test:

| Ball position | Hold contacts | Mean hold four-tip distance | Side conclusion |
|---|---:|---:|---|
| `[0.0, -0.1, 0.21]` | 5 | about `0.0331 m` | current scripted closing side |
| `[0.0, 0.1, 0.21]` | 0 | about `0.2021 m` | far/opposite side |
| `[0.0, -0.08, 0.21]` | 5 | about `0.0397 m` | current scripted closing side |
| `[0.0, 0.08, 0.21]` | 0 | about `0.1824 m` | far/opposite side |

Four-finger direction findings:

- Single-joint positive tests for index/middle/ring/little MCP/PIP/DIP all move more toward the inferred palm-closing side than negative tests.
- Negative PIP/DIP tests visibly bend away/backward in top-view renders.
- A global sign flip for the four long fingers is not supported by this audit.

Updated interpretation:

- The odd "palm reversed" visual is not explained by the ball simply being on the wrong Y side.
- The current negative-Y ball placement is the only tested side that four long fingers can approach.
- The likely issue is a mismatch between exported palm CSYS / anatomical palm-dorsal labeling / CAD visual orientation and the user's expected view, not just scripted target signs.
- Palm local axes are non-intuitive in world coordinates: local `x` is mostly world +Y, local `y` is mostly world +Z, local `z` is mostly world +X.

Current go/no-go:

- Continue thumb target tuning: PAUSED.
- Mirror ball side to positive Y: NO-GO based on this audit.
- Globally flip four-finger close signs: NO-GO based on this audit.
- Check SolidWorks palm CSYS / palm normal / dorsal visual orientation: GO.
- Check whether the hand mesh is displayed from dorsal side while the task assumes palmar side: GO.

Next recommended SolidWorks checks:

1. Mark palm surface normal and dorsal surface normal explicitly in the CAD assembly.
2. Confirm which SolidWorks CSYS axis should represent palm normal.
3. Confirm whether `palm_link` visual mesh is oriented with the anatomical palm facing the same side as MuJoCo inferred palm normal.
4. If needed, add explicit `palm_palmar_csys`, `palm_dorsal_csys`, and `grasp_ball_csys` reference frames for export4.
5. Re-export export4 and rerun `audit_export3_palm_orientation_and_grasp_side.py` adapted to export4 before returning to thumb tuning.

## Palm-Side Fixed Experimental Demo - 2026-05-24

User visual correction:

- User confirmed the previous ball placement was visibly on the dorsal/back side of the hand.
- The earlier automatic palm-side inference is therefore treated as a frame-labeling failure, not as source of truth.
- Thumb target tuning remains paused.

Generated experimental files:

- `scripts\build_export3_palm_side_fixed.py`
- `mjcf\hand_stage1_export3_palm_side_fixed.xml`
- `mjcf\scene_ball_export3_palm_side_fixed.xml`
- `scripts\demo_grasp_ball_export3_palm_side_fixed.py`
- `docs\export3_palm_side_fix_report.md`
- `docs\export3_palm_side_fixed_grasp_report.md`
- `metadata\export3_palm_side_fixed_grasp.json`
- `docs\visual_checks_export3_palm_side_fixed_grasp\`

What changed:

- Original export3 files were not overwritten.
- CAD, STL files, link tree, and joint names were not changed.
- The corrected scene places the ball on the visually identified palm side at `[0.0, 0.045, 0.22]`.
- The full mirror point `[0.0, 0.1, 0.21]` was too far from the long-finger closure envelope, so it was not used as the working default.
- In the experimental hand MJCF only, long-finger closure joint axes were negated for:
  `*_mcp_abd_joint`, `*_pip_joint`, and `*_dip_joint`.
- `*_mcp_flex_joint` was left unchanged because the current scripted policy uses it as lateral/spread control.

Validation result:

- `scene_ball_export3_palm_side_fixed.xml` loads.
- 21 position actuators are present and usable.
- Open hand has 0 initial ball contacts.
- Hold stage has 4 ball contacts.
- Hold max penetration is about `0.00370 m`.
- Hold mean four-fingertip distance is about `0.0314 m`.
- Hold thumb-ball distance is about `0.0357 m`.
- Saved renders are nonblack and show the ball on the corrected visual palm side with the long fingers closing around it.

Current interpretation:

- The user was right that the old demo looked wrong because the ball side was visually inconsistent with the anatomical palm.
- The fix that works for the current export3 demo is: ball on positive-Y visual palm side, closer to the hand than the full mirror point, plus reversed long-finger closure axes in an experimental MJCF.
- This is a simulation-side orientation fix only; it should be promoted back into CAD/export semantics only after SolidWorks palm/dorsal CSYS is explicitly labeled.

Current go/no-go:

- Use `scene_ball_export3_palm_side_fixed.xml` for the next visual scripted grasp checks: GO.
- Continue using old `scene_ball_export3.xml` as the grasp demo default: NO-GO.
- Treat the previous palm-side audit as superseded by user visual correction: GO.
- Resume thumb target tuning before confirming the palm-side fixed demo in viewer: NO-GO.

## Thumb Separation Diagnosis - 2026-05-24

Reason:

- User observed that the thumb/root appears separated and suspended in the viewer.

Generated:

- `docs\export3_thumb_separation_diagnosis.md`

Finding:

- This is a thumb transform/origin issue, not a mesh duplication issue.
- The export3 tree contains the expected 2-DoF CMC chain, but two adjacent thumb body offsets are much too large.

Measured neutral/open distances:

| Segment | Distance |
|---|---:|
| `palm_link -> thumb_root_connector_link` | `0.026175 m` |
| `thumb_root_connector_link -> thumb_trapezium1_link` | `0.011587 m` |
| `thumb_trapezium1_link -> thumb_metacarpal_link` | `0.150613 m` |
| `thumb_metacarpal_link -> thumb_proximal_link` | `0.132965 m` |
| `thumb_proximal_link -> thumb_distal_link` | `0.032000 m` |

Interpretation:

- `thumb_cmc_flex_joint` and `thumb_mcp_joint` origins are likely exported in the wrong frame or placed at the wrong CSYS origin.
- The problematic URDF origins are already present in export3:
  `thumb_cmc_flex_joint xyz=0.022854 0.085965 0.12154`,
  `thumb_mcp_joint xyz=-0.11064 0.054899 0.049241`.
- Do not continue thumb opposition tuning until these origins are fixed in SolidWorks/export4 or a clearly marked MJCF-only temporary repair is made.

## Thumb Origin Temporary Repair Attempt - 2026-05-24

Generated:

- `scripts\build_export3_thumb_origin_repaired.py`
- `mjcf\hand_stage1_export3_thumb_origin_repaired.xml`
- `mjcf\scene_ball_export3_thumb_origin_repaired.xml`
- `docs\export3_thumb_origin_repair_report.md`
- `docs\export3_thumb_origin_repair_visual_check.md`

Result:

- A MJCF-only body-origin repair can pull the thumb kinematic chain back into plausible adjacent-body distances.
- Repaired distances:
  `thumb_trapezium1_link -> thumb_metacarpal_link ~= 0.018 m`,
  `thumb_metacarpal_link -> thumb_proximal_link ~= 0.052 m`,
  `thumb_proximal_link -> thumb_distal_link ~= 0.032 m`.
- The repaired scene loads and the long-finger ball smoke test still runs.

Limitation:

- Visual inspection still shows thumb STL pieces partially separated.
- This means at least one thumb visual STL, especially `thumb_metacarpal_link.STL`, still carries a mesh-local / assembly-coordinate mismatch relative to the repaired body frame.
- Therefore this is only a temporary simulation scaffold, not a final CAD mesh solution.

Recommendation:

- For quick scripted-grasp debugging, use the repaired/proxy model with caution.
- For final clean visual hand and reliable thumb opposition, re-export export4 from SolidWorks with corrected thumb joint CSYS origins and link-local STL coordinates.

## Export4 Thumb Separation Check - 2026-05-24

Source:

- `D:\tendon_project\hardwares\hand\hand_export4`

Generated:

- `export4\`
- `meshes_export4\`
- `scripts\process_export4_quick_check.py`
- `mjcf\hand_stage1_export4.xml`
- `mjcf\scene_ball_export4.xml`
- `docs\export4_thumb_fix_check_report.md`
- `metadata\export4_thumb_fix_check.json`
- `docs\visual_checks_export4_thumb\`

Thumb chain in export4:

- `palm_link -> thumb_root_connector_fixed_joint -> thumb_root_connector_link`
- `thumb_root_connector_link -> thumb_cmc_abd_joint -> thumb_trapezium1_link`
- `thumb_trapezium1_link -> thumb_cmc_joint -> thumb_metacarpal_link`
- `thumb_metacarpal_link -> thumb_mcp_joint -> thumb_proximal_link`
- `thumb_proximal_link -> thumb_ip_joint -> thumb_distal_link`

Important naming change:

- Export4 has the second CMC joint as `thumb_cmc_joint`.
- It does not use the earlier expected name `thumb_cmc_flex_joint`.
- Downstream export3 scripts must be updated or mapped before running thumb/grasp automation on export4.

Measured thumb distances in generated MuJoCo scene:

| Segment | Distance |
|---|---:|
| `palm_link -> thumb_root_connector_link` | `0.026175 m` |
| `thumb_root_connector_link -> thumb_trapezium1_link` | `0.011587 m` |
| `thumb_trapezium1_link -> thumb_metacarpal_link` | `0.000000 m` |
| `thumb_metacarpal_link -> thumb_proximal_link` | `0.052000 m` |
| `thumb_proximal_link -> thumb_distal_link` | `0.032000 m` |

Result:

- Export4 fixes the previous export3 blocker where thumb adjacent body distances were about `0.13-0.15 m`.
- MuJoCo load succeeds: `26 bodies / 23 joints / 22 actuators / 50 geoms / 5 sites / 24 meshes`.
- Visual renders show the thumb root and downstream thumb visual mesh are attached well enough to continue simulation checks.
- A small thumb motion render also stays continuous; the thumb no longer splits into distant floating parts.

Remaining caution:

- `thumb_cmc_joint` has zero translation from `thumb_trapezium1_link` to `thumb_metacarpal_link`. This may be intended, but should be manually confirmed in SolidWorks.
- The palm-side / ball-side scripted grasp correction still needs to be ported to export4; do not reuse export3 scripts blindly because the thumb joint name changed.

## Export4 vs Shadow Video Open/Close Comparison - 2026-05-24

Goal:

- Use the previously collected local videos as the common motion source.
- Replay the same video-derived open/close motion on both Shadow Hand and hand_stage1 export4.
- Remove the ball from this comparison and quantify closure state instead of object grasp success.

Generated:

- `mjcf\scene_export4_no_ball_compare.xml`
- `..\shadow_hand\scene_right_no_object_compare.xml`
- `scripts\run_export4_shadow_video_comparison.py`
- `docs\export4_shadow_video_comparison_report.md`
- `metadata\export4_shadow_video_comparison.json`
- `docs\visual_checks_export4_shadow_video_compare\`

Result:

- Processed `12 / 12` local videos from the open/close manifest.
- Shadow replay failures: `0`.
- export4 replay failures: `0`.
- Rendered Shadow/export4 keyframe comparison sheets for all 12 videos.
- Mean Shadow diagnostic closure score: `0.3136`.
- Mean hand_stage1 export4 diagnostic closure score: `0.1965`.
- Shadow/export4 closure-score correlation across videos: `0.7981`.

Conclusion:

- `PIPELINE PASS / FUNCTIONAL COMPARISON PARTIAL`.
- hand_stage1 export4 can now be driven by the same video-derived open/close semantics as Shadow without MuJoCo load or replay failure.
- The export4 closure trend follows Shadow across the video set, but the absolute closure score is lower.
- This validates the comparison pipeline and basic export4 hand operation, not Shadow-equivalent dexterous grasping.

Remaining caution:

- The export4 adapter is deterministic and diagnostic, not an IK solver or trained policy.
- Thumb opposition and MCP flex/abd sign semantics still need final manual verification.
- The ball was intentionally removed, so this does not prove stable object grasp.
- Training should still wait until hand semantics, collision proxy, and task targets are signed off.

## Export4 Flexion Sign / Limit Audit - 2026-05-25

Reason:

- User observed that fingers appear to bend toward the dorsal side.
- User suspected many SolidWorks/URDF limit values were filled with the wrong sign.

Generated:

- `scripts\audit_fix_export4_flexion_signs.py`
- `scripts\demo_export4_flexion_sign_fixed_close.py`
- `mjcf\hand_stage1_export4_flexion_sign_fixed.xml`
- `mjcf\scene_export4_flexion_sign_fixed.xml`
- `mjcf\scene_ball_export4_flexion_sign_fixed.xml`
- `docs\export4_flexion_sign_audit.md`
- `metadata\export4_flexion_sign_audit.json`
- `docs\visual_checks_export4_flexion_sign\export4_flexion_sign_summary.png`

Finding:

- Previous ball-side audit established world `+Y` as the export4 palmar side.
- For the four long fingers, small negative angles move fingertips toward world `+Y`.
- The current exported limits for most long-finger flexion joints are positive-only or positive-dominant, so the old scripted positive close can bend toward the dorsal side.

Experimental MJCF-only fixes:

- Flipped long-finger MCP-abd/PIP/DIP ranges to negative ranges ending at zero:
  `index/middle/ring/little *_mcp_abd_joint`, `*_pip_joint`, `*_dip_joint`.
- Also flipped `thumb_ip_joint` based on the same audit; thumb CMC joints remain audit-only and should not be auto-flipped.
- `mcp_flex` joints remain audit-only because MCP flex/abd naming may still be semantically reversed.

Result:

- Fixed experimental scene loads successfully.
- Visual summary shows `fixed_observed_close` curls the long fingers toward the palm side more plausibly than the original positive-close pose.

Important:

- This is not a CAD change and not a replacement for SolidWorks cleanup.
- If the fixed scene looks correct in viewer, mirror these sign conventions back into SolidWorks/URDF limits:
  long-finger flexion should use negative ranges for the current export4 coordinate convention.

## Export4 Long Finger Joint Tuning - 2026-05-25

Reason:

- After sign correction, the next step was to make index/middle/ring/little bend naturally toward the palm without excessive folding or obvious interpenetration.
- Thumb was intentionally left neutral for this pass.

Generated:

- `scripts\tune_export4_long_finger_joints.py`
- `scripts\demo_export4_long_finger_tuned_close.py`
- `mjcf\hand_stage1_export4_long_finger_tuned.xml`
- `mjcf\scene_export4_long_finger_tuned.xml`
- `mjcf\scene_ball_export4_long_finger_tuned.xml`
- `docs\export4_long_finger_joint_tuning_report.md`
- `metadata\export4_long_finger_joint_tuning.json`
- `docs\visual_checks_export4_long_finger_tuning\`

Result:

- Tuned long-finger ranges are narrower and more conservative than the full sign-fixed ranges.
- Recommended scripted `natural_close` targets keep MCP-abd/PIP/DIP in negative closing direction.
- Visual sheets include full, side, top, and per-finger single-joint checks.
- Current visual pass shows four long fingers closing toward the palm side, with no obvious palm stabbing or severe self-intersection in fixed camera renders.
- `full_but_safe` is kept as a stress pose, not as the default scripted target.

Important:

- `mcp_flex` joints are kept small because they may represent spread/side motion despite also moving the fingertip palmar in this coordinate convention.
- Thumb tuning remains TODO.
- This is an experimental MJCF baseline for visual debugging; do not overwrite the raw export4 model yet.

## Export4 Thumb Tuning And Current Baseline - 2026-05-25

Reason:

- After long-finger sign/range tuning, the remaining local issue was thumb opposition.
- The previous pure distance scoring could select a thumb target that was close numerically but visually hard to judge because the thumb was hidden under the four fingers.

Generated:

- `scripts\tune_export4_thumb_joints.py`
- `scripts\demo_export4_thumb_tuned_close.py`
- `mjcf\hand_stage1_export4_thumb_tuned.xml`
- `mjcf\scene_export4_thumb_tuned.xml`
- `mjcf\scene_ball_export4_thumb_tuned.xml`
- `mjcf\hand_stage1_export4_current_baseline.xml`
- `mjcf\scene_export4_current_baseline.xml`
- `mjcf\scene_ball_export4_current_baseline.xml`
- `docs\export4_thumb_joint_tuning_report.md`
- `docs\export4_thumb_tuned_close_demo_report.md`
- `docs\export4_current_baseline_status.md`
- `metadata\export4_thumb_joint_tuning.json`
- `metadata\export4_thumb_tuned_close_demo.json`
- `metadata\export4_current_baseline_manifest.json`
- `docs\visual_checks_export4_thumb_tuning\`
- `docs\visual_checks_export4_thumb_tuned_close\`

Thumb tuning result:

- Score-best target:
  `thumb_cmc_abd_joint=-0.3`, `thumb_cmc_joint=0.25`, `thumb_mcp_joint=0.0`, `thumb_ip_joint=0.0`.
- Visual recommended target:
  `thumb_cmc_abd_joint=-0.3`, `thumb_cmc_joint=0.0`, `thumb_mcp_joint=0.25`, `thumb_ip_joint=-0.25`.
- The visual recommended target is used for the current baseline because it adds mild MCP/IP flexion and looks more like natural opposition in color-coded focus renders.

Load check:

- `hand_stage1_export4_current_baseline.xml`: `25 bodies / 22 joints / 22 actuators / 48 geoms / 5 sites`.
- `scene_export4_current_baseline.xml`: `25 bodies / 22 joints / 22 actuators / 49 geoms / 5 sites`.
- `scene_ball_export4_current_baseline.xml`: `26 bodies / 23 joints / 22 actuators / 50 geoms / 5 sites`.

Thumb close demo hold metrics:

- thumb-index distance: `0.0195 m`.
- thumb-middle distance: `0.0332 m`.
- thumb-long-tip-centroid distance: `0.0314 m`.
- contact count: `0`.
- max penetration: `0.00000 m`.

Conclusion:

- Export4 is now organized as the current diagnostic baseline.
- The thumb is no longer treated as solved by random target tuning; it has a reproducible visual-audit target and quantitative close-state metrics.
- This is good enough to continue joint direction audit, thumb audit, collision audit, Shadow/video mapping comparison, scripted grasp-state quantification, and pre-training adapter/data-schema design.
- It is still not training-ready. Collision proxy, action adapter, reward/metric definitions, and task reset semantics need to be stabilized first.

Remaining caution:

- Thumb CMC axis/origin semantics still need final SolidWorks confirmation if future visual tasks expose unnatural motion.
- Collision remains simplified proxy geometry.
- Do not overwrite raw export4 or CAD/STL with this experimental baseline.

## Export4 Pre-Training Adapter Design - 2026-05-25

Generated:

- `docs\export4_training_adapter_design.md`
- `metadata\export4_training_adapter_schema.json`

Decision:

- Use `export4_position_control_v1` as the canonical 22D action interface.
- Keep all sign conventions and target scaling inside adapters, not inside raw training data.
- The video-mapping adapter now maps `0=open` and `1=current tuned close target`, instead of interpolating across raw joint ranges.

Training status:

- Not training-ready yet.
- Next gates are current-baseline joint direction audit, thumb audit, collision audit, scripted grasp-state metrics, reset distribution, and adapter unit tests.

## Export4 Current-Baseline Shadow/Video Smoke - 2026-05-25

Generated:

- `docs\export4_current_baseline_shadow_video_comparison_report.md`
- `metadata\export4_current_baseline_shadow_video_comparison.json`
- `docs\visual_checks_export4_current_baseline_shadow_video_compare\`

Result:

- Ran a 1-video / 5-keyframe smoke test on the current baseline.
- Shadow failures: `0`.
- export4 failures: `0`.
- Mean Shadow closure score: `0.0737`.
- Mean export4 closure score: `0.0543`.

Interpretation:

- The current baseline and updated `hand_open_close_feature_v1 -> export4_position_control_v1` adapter load and replay without failure.
- This is only a smoke run, not the full 12-video regression.
- Full Shadow/video comparison should be rerun after joint/thumb/collision audits are refreshed on the current baseline.

## Export4 Current-Baseline Audits - 2026-05-25

Generated:

- `scripts\audit_export4_current_baseline.py`
- `docs\export4_current_baseline_joint_direction_audit.md`
- `docs\export4_current_baseline_thumb_audit.md`
- `docs\export4_current_baseline_collision_audit.md`
- `docs\solidworks_export4_followup_checklist.md`
- `metadata\export4_current_baseline_audit.json`
- `docs\visual_checks_export4_current_baseline_audit\`

Joint direction audit:

- `12` long-finger MCP-abd/PIP/DIP closure joints passed the current sign convention.
- `10` joints are audit-only: wrist, MCP-flex side/spread candidates, and thumb joints.
- No long-finger `NEEDS_SW_CHECK` rows were found.

Thumb audit:

- Thumb chain topology matches export4 intended 2-DoF CMC chain.
- `thumb_root_connector_fixed_joint` is represented in MJCF as fixed body nesting, which is expected.
- Close thumb-index distance: `0.0196 m`.
- Close thumb-middle distance: `0.0333 m`.
- Conclusion: `PASS_FOR_SCRIPTED_SMOKE`.
- Remaining manual confirmation: CMC axis origins/directions should still be checked in SolidWorks.

Collision audit:

- Clean STL remains visual-only.
- Collision proxy geom count: `24`.
- Collision-enabled mesh geom count: `0`.
- Visual geoms accidentally collision-enabled: `0`.
- Static ball close reaches contact, but max hand-ball penetration is about `0.013 m`.
- Conclusion: `PASS_FOR_SMOKE_NEEDS_TRAINING_PROXY_TUNING`.

SolidWorks follow-up:

- No current blocker found.
- Main human-check item is `thumb_cmc_abd_joint / thumb_cmc_joint`: confirm axes pass through intended CMC centers and positive/negative directions match intended abd/flex semantics.

Training implication:

- Current baseline can continue scripted/Shadow/video diagnostics.
- Do not start contact-rich training until collision proxy/ball placement is tuned below the current 13 mm penetration level.

## Export4 Current-Baseline Full Shadow/Video Regression - 2026-05-25

Generated:

- `docs\export4_current_baseline_shadow_video_comparison_report.md`
- `metadata\export4_current_baseline_shadow_video_comparison.json`
- `docs\visual_checks_export4_current_baseline_shadow_video_compare\`

Result:

- Processed videos: `12 / 12`.
- Shadow failures: `0`.
- export4 failures: `0`.
- Mean Shadow closure score: `0.3136`.
- Mean export4 closure score: `0.2204`.
- Shadow/export4 closure-score correlation: `0.8647`.

Conclusion:

- `PIPELINE PASS / FUNCTIONAL COMPARISON PARTIAL`.
- The current baseline can replay all local video-derived open/close sequences through the export4 adapter.
- This validates the comparison pipeline and closure-state trend, not Shadow-equivalent dexterous grasp or training readiness.

## Export4 +Y Palm Side Confirmation And Arm-Hand Assembly - 2026-05-26

User confirmation:

- `+Y` is the palm/grasp side for export4.
- The active scripted-smoke hand candidate remains `mjcf/hand_stage1_export4_palmar_ypos_collision_candidate.xml`.
- Current smoke-test ball pose remains `[0.0, 0.08, 0.21]`.

Arm+hand assembly generated:

- Workspace: `D:\tendon_project\simulations\models\arm_hand_stage1_export\`
- Combined MJCF: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_cad_mount_candidate.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Viewer: `D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py`
- Joint smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_export4_joints.py`

Result:

- The hand is attached as a real child body under arm `ee_tool_frame`.
- The initial identity mount showed that `ee_tool_frame` is an internal/tool origin, not the visible flange mounting face.
- The user then exported exact CAD mount frames and bridge frames.
- Current CAD mount candidate aligns `arm_flange_mount_csys == hand_wrist_mount_csys`.
- Current CAD mount candidate attaches `hand_base_link` directly under `ee_mount`.
- CAD mount origin alignment error is `0 m`.
- Combined model loads with `31 bodies / 26 joints / 26 actuators / 59 geoms / 6 sites / 29 meshes`.
- Joint smoke result: `26 PASS / 0 FAIL / 0 SKIPPED`; actuator stepping: `PASS`.

Current interpretation:

- This is a good first MuJoCo arm+hand smoke assembly.
- If visual orientation still looks wrong, the next correction is SolidWorks mount CSYS axis direction/clocking, not another MuJoCo guessed offset.
- Training remains prohibited.

## Export4 Arm-Hand Physics V0 Closeout - 2026-05-27

Workspace:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\`

Active arm+hand files:

- Frozen CAD mount reference: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Active physics-v0 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_collision_proxy.xml`
- Active physics-v0 ball scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`

Result:

- CAD mount alignment is accepted as the current virtual-space entry point.
- `wrist_2_joint` is active as a hinge in the arm+hand model.
- Arm collision proxy boxes were added for `base_link`, `link_1`, `link_2`, `link_3`, and `ee_mount`.
- Clean STL remains visual-only; collision uses primitive proxies.
- Default ball is on the confirmed palm `+Y` side, radius `0.028 m`, palm local offset `[0.04, 0.12, -0.02]`.
- Physics regression PASS:
  - model load PASS;
  - joint smoke `26 PASS / 0 FAIL / 1 SKIPPED`;
  - open static contact `0`;
  - hold contact count `7`;
  - hold max penetration `0.003885 m`.

Current interpretation:

- This is ready for tiny smoke dataset v0 and scripted task scaffold work.
- This is still not ready for RL/BC training or contact-rich large-scale collection.
- Main next engineering task is collision proxy refinement, especially flange/wrist and thumb/fingertip contact fidelity.

## Export4 Arm-Hand Tiny Dataset V0 - 2026-05-27

Generated in arm-hand workspace:

- Task API: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py`
- Dataset collector: `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_smoke_dataset.py`
- Replay checker: `D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_smoke_dataset.py`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_scripted_smoke_dataset_v0.npz`

Result:

- Task API loads active physics-v0 scene.
- Action dim: `26`.
- Observation dim: `124`.
- Dataset: `5 episodes / 1200 steps`.
- qpos shape: `[1200, 33]`.
- qvel shape: `[1200, 32]`.
- ctrl/action shape: `[1200, 26]`.
- obs shape: `[1200, 124]`.
- Replay: `PASS`.
- Visual keyframes show palm-side open, close-four-fingers, and hold stages.

Interpretation:

- This validates adapter/data/replay plumbing for arm+hand stage1.
- This is still pinned-ball scripted smoke, not free-object grasp and not training data.
- Training remains prohibited until collision proxy and free-object behavior are improved.

## Export4 Arm-Hand Scripted Task Scaffold - 2026-05-27

Generated in arm-hand workspace:

- Script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_scripted_task.py`
- Report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_scripted_task_report.md`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_scripted_task.json`
- Rollout: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_scripted_task_rollout_v0.npz`

Result:

- Episodes: `3`.
- Success: `3 / 3`.
- Hold contacts: `6-8`.
- Hold max penetration range: about `0.0037-0.0049 m`.
- Four-finger average fingertip-ball distance range: about `0.051-0.055 m`.
- Thumb-ball distance: about `0.043 m`.

Interpretation:

- The scaffold is ready for Shadow-style scripted comparison plumbing.
- It is still pinned-ball smoke, not free-object stable grasp.
- Training remains blocked.
