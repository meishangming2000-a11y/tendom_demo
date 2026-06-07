# Export4 Final Engineering Report

Generated: 2026-05-27 02:30

Updated: 2026-05-28 02:15 with collision proxy v2 and arm+hand Shadow/video comparison.

## Summary

Tonight's arm+hand stage closed the virtual-space entry problem and advanced the model to a reproducible physics-v0 experiment.

The important change is that the hand is no longer attached by a guessed point. It is attached using the SolidWorks-exported mount coordinate systems:

- arm mount frame: `arm_flange_mount_csys`
- hand mount frame: `hand_wrist_mount_csys`
- attachment rule: `arm_flange_mount_csys == hand_wrist_mount_csys`

The CAD mount candidate is kept frozen. Physics changes are saved under `mjcf/` as experiment files.

## Active Files

- Frozen mount reference: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Current collision v2 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Current collision v2 scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- Current collision v2 ball scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Previous physics-v0 model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_collision_proxy.xml`

## Phase Results

| phase | result | notes |
|---|---|---|
| Phase 0 freeze | PASS | CAD mount candidate frozen as virtual entry point. |
| Phase 1 joint ranges/poses | PASS | Existing export4 tuned ranges retained; staged poses rendered. |
| Phase 2 collision proxy | PASS | Arm primitive collision proxies added; clean STL remains visual-only. |
| Phase 3 regression | PASS | Load, joint smoke, static contact, and scripted ball smoke pass. |
| Phase 4 closeout | PASS | Active file index, README, reports, and metadata updated. |
| Dataset v0 | PASS | Minimal task API, 5 scripted episodes, and replay check completed. |
| Scripted task scaffold | PASS | 3 randomized small-offset episodes passed smoke criteria. |
| Collision v1 | PASS | Added palm-side pad, reduced fingertip spheres, and reran free-ball/scripted smoke. |
| Shadow/video comparison | PASS | Ran 12-video Shadow vs arm+hand v1 open/close diagnostic. |
| Collision v2 | PASS | Added shallow palm rail and reran free-ball/scripted/sweep smoke. |
| Shadow/video comparison v2 | PASS | Ran 12-video Shadow vs arm+hand v2 open/close diagnostic. |

## Collision Proxy V2 Update

Collision proxy v2 starts from v1 and adds one shallow local `-Z` palm rail based on the measured free-ball slide direction. It is saved as a separate experiment and does not overwrite CAD, STL, joint names, or joint tree.

Files:

- `mjcf\arm_hand_export4_collision_proxy_v2.xml`
- `mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- `mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- `build_arm_hand_collision_proxy_v2.py`
- `test_arm_hand_collision_proxy_v2.py`

Smoke metrics:

- Model: `32 bodies / 27 joints / 26 actuators / 67 geoms / 14 sites / 29 meshes`
- Free ball start ball-hand contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free-ball displacement after 300 open steps: `0.018294 m`
- Free-ball vertical drop after 300 open steps: `0.013383 m`
- Scripted pinned hold contacts: `6`
- Scripted pinned hold max penetration: about `0.0042 m`
- Local ball sweep: `9 / 9` PASS

Compared with v1, v2 substantially improves passive ball retention near the palm while keeping penetration in the smoke-test target range.

## Collision Proxy V1 Update

Collision proxy v1 adds a small palm-side contact pad and reduces the fingertip spheres. It is saved as a separate experiment and does not overwrite the frozen CAD mount or the previous physics-v0 scene.

Files:

- `mjcf\arm_hand_export4_collision_proxy_v1.xml`
- `mjcf\scene_arm_hand_export4_collision_proxy_v1.xml`
- `mjcf\scene_arm_hand_export4_collision_proxy_v1_ball.xml`
- `view_arm_hand_stage1_scripted_demo.py`
- `test_arm_hand_collision_proxy_v1.py`

Smoke metrics:

- Model: `32 bodies / 27 joints / 26 actuators / 66 geoms / 14 sites / 29 meshes`
- Free ball start ball-hand contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free ball still slides/falls in passive simulation because the palm is tilted and gravity is active.
- Scripted pinned hold contacts: `6`
- Scripted pinned hold max penetration: about `0.0040 m`
- Four-finger average fingertip-ball distance: about `0.0539 m`
- Thumb-ball distance: about `0.0388 m`

The new `view_arm_hand_stage1_scripted_demo.py` is the recommended visual demo when the goal is to watch the hand close. The older passive viewer does not apply actuator targets and does not hold the ball.

## Shadow/Video Comparison Update

The previous hand-only comparison was extended to the assembled arm+hand model. It has now been rerun with collision proxy v2:

- Script: `run_arm_hand_stage1_v2_shadow_video_comparison.py`
- Report: `docs\arm_hand_stage1_v2_shadow_video_comparison_report.md`
- Metadata: `metadata\arm_hand_stage1_v2_shadow_video_comparison.json`
- Visual sheets: `docs\archive\visual_evidence_20260608\visual_checks_arm_hand_stage1_v2_shadow_video_compare\`

Results:

- Videos processed: `12 / 12`
- Shadow failures: `0`
- Arm+hand v2 failures: `0`
- Shadow mean closure score: `0.3136`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646`

Interpretation: the video-to-control path can now drive both the Shadow reference and the assembled arm+hand model through comparable open/close motion. This is still a diagnostic without a ball; it does not prove stable free-object grasp.

## Regression Metrics

From `arm_hand_stage1_physics_regression_report.md`:

- Model: `32 bodies / 27 joints / 26 actuators / 65 geoms / 14 sites / 29 meshes`
- Joint smoke: `26 PASS / 0 FAIL / 1 SKIPPED` (`ball_freejoint` skipped)
- Open static contact: `0`
- Open static max penetration: `0.000000 m`
- Scripted hold contacts: `7`
- Scripted hold max penetration: `0.003885 m`
- Four-finger average fingertip-ball distance: `0.052769 m`
- Thumb-ball distance: `0.042791 m`

Dataset v0:

- Task API action dim: `26`
- Task API obs dim: `124`
- Dataset: `5 episodes / 1200 steps`
- qpos shape: `[1200, 33]`
- qvel shape: `[1200, 32]`
- ctrl/action shape: `[1200, 26]`
- obs shape: `[1200, 124]`
- Replay: PASS
- Scripted task: `3 / 3` episodes PASS
- Scripted task rollout: `data\arm_hand_stage1_scripted_task_rollout_v0.npz`

## Collision Proxy Design

Added arm proxy boxes:

- `base_link`
- `link_1`
- `link_2`
- `link_3`
- `ee_mount`

Design choices:

- STL meshes are visual-only.
- Primitive proxies are used for contact.
- Adjacent-link self-collision is intentionally conservative in v0 to avoid false positive collisions near the wrist/flange stack.
- The ball scene uses palm-side placement from the confirmed `+Y` side.

## Remaining Issues

- MAJOR: collision proxy v2 is usable for smoke tests, not final contact-rich training.
- MAJOR: thumb is good enough for scripted smoke, but not yet Shadow-equivalent opposition.
- MAJOR: arm collision proxies are bbox-derived and need hand tuning around the flange/wrist.
- MINOR: current four-finger `*_mcp_flex_joint` names actually represent spread/abduction-adduction semantics; keep semantic aliases instead of renaming.

## Training Decision

Do not start RL/BC training yet.

What is allowed next:

- tiny dataset collection v0 for smoke/replay only;
- Shadow-style scripted task API;
- adapter and retargeting scaffolds;
- collision proxy refinement;
- Shadow/video diagnostic comparison.

What is still blocked:

- large-scale dataset collection;
- RL/BC training;
- tendon routing;
- claims of Shadow-equivalent dexterity.

## Next Recommended Command

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_physics_regression.py
```

Then visually inspect:

- `docs\visual_checks_arm_hand_physics_regression\regression_open.png`
- `docs\visual_checks_arm_hand_physics_regression\regression_hold.png`

For the current v2 visual close demo, run:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py
```

For the current Shadow/video comparison, run:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_shadow_video_comparison.py --max-keyframes 5
```
