# Morning Status Export4

Generated: 2026-05-27 02:30

Updated: 2026-05-28 02:15 after collision proxy v2 and arm+hand Shadow/video comparison.

## Starting Point

- Export4 hand and arm could load as a visual/kinematic assembly.
- CAD mount alignment was uncertain until the user exported SolidWorks mount coordinate systems.
- The user then confirmed the CAD-frame mount looked correct.
- Main remaining goals were joint range sanity, full arm+hand collision proxy, and project closeout.

## Completed

- Froze the user-approved CAD mount as the current virtual-space reference.
- Generated joint pose/range experiment files.
- Added v0 arm collision proxies for `base_link`, `link_1`, `link_2`, `link_3`, and `ee_mount`.
- Kept clean STL meshes visual-only.
- Generated a palm-side ball scene using confirmed `+Y` palm side.
- Tuned ball default to avoid open-hand overlap:
  - radius: `0.028 m`
  - palm local offset: `[0.04, 0.12, -0.02]`
- Ran physics regression and got PASS.
- Updated README and active file indexes.
- Added a minimal `ArmHandStage1TaskAPI`.
- Collected a tiny scripted smoke dataset v0.
- Replayed dataset episode 0 and saved keyframes.
- Added and ran a scripted task scaffold with randomized small ball offsets.
- Added collision proxy v1 with a palm-side contact pad and smaller fingertip spheres.
- Added collision proxy v2 with a shallow local `-Z` palm rail for better free-ball retention.
- Added a dedicated scripted viewer that pins the ball and visibly drives the staged close.
- Ran the full 12-video Shadow vs arm+hand v2 open/close comparison.

## Key Files

- Open this model now:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Watch the scripted close now:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py`
- Frozen mount reference:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Regression report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_physics_regression_report.md`
- Engineering report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\export4_final_engineering_report.md`
- Active file index:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\export4_active_file_index.md`
- Dataset v0 closeout:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_dataset_v0_closeout.md`
- Collision v1 smoke:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v1_smoke_report.md`
- Collision v2 smoke:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_smoke_report.md`
- Shadow/video comparison:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_shadow_video_comparison_report.md`

## Tests

| test | result |
|---|---|
| model load | PASS |
| joint kinematic smoke | PASS |
| open static contact | PASS |
| scripted ball-contact smoke | PASS |
| task API shape check | PASS |
| tiny smoke dataset v0 | PASS |
| replay v0 | PASS |
| scripted task scaffold | PASS |
| collision proxy v1 smoke | PASS |
| collision proxy v2 smoke | PASS |
| arm+hand v2 vs Shadow video comparison | PASS |

Regression details:

- Model summary: `32 bodies / 27 joints / 26 actuators / 65 geoms / 14 sites / 29 meshes`
- Joint smoke: `26 PASS / 0 FAIL / 1 SKIPPED`
- Open contact count: `0`
- Open max penetration: `0.000000 m`
- Hold contact count: `7`
- Hold max penetration: `0.003885 m`
- Task API: action dim `26`, obs dim `124`
- Dataset v0: `5 episodes / 1200 steps`
- Dataset labels: `5 / 5 contact_smoke_pass`
- Replay keyframes saved under `docs\visual_checks_arm_hand_stage1_replay\`
- Scripted task scaffold: `3 / 3` episodes PASS
- Scripted task rollout: `data\arm_hand_stage1_scripted_task_rollout_v0.npz`
- Collision v1: free ball start ball-hand contact `1`, start penetration `0.000500 m`
- Collision v1 scripted hold: ball-hand contacts `6`, max penetration about `0.0040 m`
- Collision v2: free-ball displacement after 300 open steps `0.018294 m`, vertical drop `0.013383 m`
- Collision v2 scripted hold: ball-hand contacts `6`, max penetration about `0.0042 m`
- Collision v2 local ball sweep: `9 / 9` PASS
- Shadow/video comparison v2: `12 / 12` videos processed, `0` arm+hand failures
- Shadow mean closure score: `0.3136`
- Arm+hand v1 mean closure score: `0.2202`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646`

## Current Conclusion

This is a real milestone: the arm and hand now have a reproducible CAD-frame mount and a first full-body MuJoCo physics smoke model.

It is ready for:

- tiny smoke dataset v0;
- scripted task scaffold;
- Shadow-style structural/task comparison;
- collision proxy refinement.
- Shadow/video open-close comparison using the assembled arm+hand model.

It is not ready for:

- RL/BC training;
- large-scale dataset collection;
- high-confidence grasp physics;
- tendon/coupling work.

## Tomorrow's Manual Checks

- Visually inspect the wrist/flange region with collision proxy group visible.
- Decide whether the `ee_mount` proxy should be split into flange plate and wrist adapter pieces.
- Continue thumb and fingertip proxy refinement only after flange/wrist collision looks stable.
- Keep `*_mcp_flex_joint` names unchanged, but use semantic aliases in adapters.
- For free-ball behavior, remember the ball falls/slides in passive simulation; use the scripted pinned demo for closure inspection.

## Recommended Next Codex Command

Continue from `arm_hand_stage1_export`, run `view_arm_hand_stage1_scripted_demo.py` for visual inspection, then decide whether collision proxy v2 is good enough to become the next smoke baseline. Do not train yet.
