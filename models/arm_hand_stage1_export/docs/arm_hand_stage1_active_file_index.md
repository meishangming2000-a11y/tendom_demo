# Arm-Hand Stage1 Active File Index

Generated: 2026-05-28 02:40

## Current Recommendation

Use collision proxy v2 for visual smoke, scripted close, Shadow/video comparison, and the new lift-ball integration demo. Keep the CAD mount candidate as the frozen alignment reference. Keep v1 and older physics-v0 files for regression history and comparison.

Stage1 is closed as a virtual prototype baseline. The next stage should start from task API / dataset v0 / retargeting scaffold, not from CAD alignment.

## Open/View

- Frozen CAD mount reference: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Current model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Current scene without ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- Current scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2_ball.xml`
- Current lift-ball demo scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Previous collision v1 scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v1_ball.xml`
- Previous physics-v0 scene with ball: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`

## Run

- Passive viewer, current v2 scene:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py`
- Scripted close viewer, ball pinned by default:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py`
- Same scripted viewer with raw gravity ball:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_stage1_scripted_demo.py --free-ball`
- Collision v2 smoke:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_collision_proxy_v2.py`
- Previous arm+hand v1 vs Shadow video comparison:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v1_shadow_video_comparison.py --max-keyframes 5`
- Arm+hand v2 vs Shadow video comparison:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_shadow_video_comparison.py --max-keyframes 5`
- Arm+hand lift-ball scripted smoke demo, pure physics:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics`
- Same lift-ball demo with live viewer:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics --viewer`
- Render lift-ball demo to MP4:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\render_arm_hand_lift_ball_video.py`
- Default-posture to lift-ball full demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py`
- Default-posture full demo with live viewer:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py --viewer --no-render-video`
- Previous physics-v0 regression:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_physics_regression.py`
- Previous tiny dataset v0:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_smoke_dataset.py --episodes 5 --steps-per-phase 48`

## Reports

- Stage closeout: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage1_virtual_prototype_closeout.md`
- Current baseline manifest: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\current_baseline_manifest.json`
- Next-stage handoff prompt: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\next_stage_handoff_prompt.md`
- Collision v2 design: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_report.md`
- Collision v2 smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_smoke_report.md`
- Collision v2 visual check: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v2_visual_check_report.md`
- Collision v1 smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_collision_proxy_v1_smoke_report.md`
- Shadow/video comparison v2: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_shadow_video_comparison_report.md`
- Shadow/video comparison v1: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v1_shadow_video_comparison_report.md`
- Lift-ball demo metrics: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_report.md`
- Lift-ball demo visual check: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_visual_check.md`
- Lift-ball MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_pure_physics.mp4`
- Lift-ball contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_contact_sheet.png`
- Default-posture lift demo report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_from_default_report.md`
- Default-posture lift MP4: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_pure_physics.mp4`
- Default-posture lift contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_contact_sheet.png`
- Previous final engineering report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\export4_final_engineering_report.md`
- Morning status: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\morning_status_export4.md`

## Latest Collision V2 Smoke

- Status: `PASS`
- Free ball start contacts: `1`
- Free ball start max penetration: `0.000500 m`
- Free ball displacement after 300 open steps: `0.018294 m`
- Free ball vertical drop after 300 open steps: `0.013383 m`
- Scripted pinned hold contacts: `6`
- Scripted pinned hold max penetration: about `0.0042 m`
- Four-finger average fingertip-ball distance: about `0.0536 m`
- Thumb-ball distance: about `0.0391 m`
- Local ball sweep: `9 / 9` PASS
- Compared with v1, the passive free-ball no longer falls far away during the 300-step open test.

## Latest Shadow Comparison

- Videos processed: `12 / 12`
- Shadow failures: `0`
- Arm+hand v2 failures: `0`
- Shadow mean closure score: `0.3136`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646`
- Visual sheets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\`

## Latest Lift-Ball Demo

- Mode: `pure_physics`
- Status: `PURE_PHYSICS_PASS`
- Final ball lift height: `0.1526 m`
- Final ball-hand contacts: `6`
- Final ball-floor contacts: `0`
- Final max penetration: `0.0031 m`
- Scripted phases: open high, approach ball, preshape, close four fingers, close thumb, lift, hold lift.
- Screenshots: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\`

## Latest Default-Posture Lift Demo

- Mode: `pure_physics`
- Status: `PASS`
- Final ball lift height: `0.1584 m`
- Final ball-hand contacts: `7`
- Final ball-floor contacts: `0`
- Final max penetration: `0.0034 m`
- Scripted phases: default hold, move to pre-approach, approach ball, preshape, close four fingers, close thumb, lift, hold lift.
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_from_default\arm_hand_lift_from_default_pure_physics.mp4`

## Current Limits

- Collision proxy v2 is still a smoke proxy, not final physics.
- Lift-ball is a scripted integration smoke demo on a raised demo floor/table plane; it is not evidence of robust arbitrary object grasp.
- Thumb is usable for smoke, not Shadow-equivalent.
- Training remains blocked.
