# Arm-Hand Lift Ball Demo Visual Check

Generated: 2026-05-28

## Scope

This report checks the current scripted arm+hand lift-ball demo visually. It does not modify CAD, STL, joint tree, joint names, tendon routing, or training code.

## Files

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Script: `D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py`
- Metrics report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_lift_ball_demo_report.md`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_lift_ball_demo.json`
- Screenshots: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\`
- Contact sheet: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_contact_sheet.png`
- Keyframe GIF: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_keyframes.gif`
- MP4 video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_lift_ball_demo\arm_hand_lift_ball_demo_pure_physics.mp4`

## Run

Command:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics
```

Live viewer command:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_scripted.py --pure-physics --viewer
```

MP4 render command:

```powershell
python D:\tendon_project\simulations\models\arm_hand_stage1_export\render_arm_hand_lift_ball_video.py
```

The latest run used `lift_demo_side`, a free camera tracking the palm/ball area from the side. This is clearer than the earlier named MJCF cameras because the arm base no longer hides the hand-ball interaction.

## Result

Overall visual result: **PASS for scripted smoke demo**

- `00_open_high.png`: ball starts near the palm-side work area on the demo floor/table; hand is open and visible.
- `02_preshape.png`: four fingers begin moving toward the ball; ball remains on the floor/table.
- `03_close_four_fingers.png`: long fingers visibly wrap around the ball.
- `04_close_thumb.png`: thumb participates from the opposite side, though this is still a smoke-test grasp rather than a tuned dexterous opposition.
- `05_lift.png`: ball is visibly lifted off the floor/table.
- `06_hold_lift.png`: ball remains held while the wrist/arm lifts.

## Quantitative Check

Latest pure-physics metrics:

- Status: `PURE_PHYSICS_PASS`
- Final ball lift height: `0.152621 m`
- Final ball-hand contacts: `6`
- Final ball-floor contacts: `0`
- Final max penetration: `0.003056 m`
- Final four-finger average tip-ball distance: `0.052516 m`
- Final thumb-ball distance: `0.038009 m`

## Important Caveats

- The demo uses the current `collision_proxy_v2` simplified collision model, not high-fidelity STL collision.
- The floor/table plane in this scene is intentionally raised to match the reachable workspace for this scripted demo.
- This is still scripted position control, not a learned policy and not proof of robust arbitrary-object grasping.
- The result is suitable as an integration milestone: arm mount, wrist, hand, collision proxy, position actuators, ball contact, and lift sequence are all connected in MuJoCo.

## Recommendation

Keep this demo as the current presentation-quality smoke test for "arm + hand grasps and lifts a ball." Next engineering work should focus on:

- collision proxy robustness across nearby ball positions;
- producing a video/GIF from these frames;
- adding a small workspace sweep for lift success rate;
- later replacing scripted targets with task API / dataset collection once the proxy is stable.
