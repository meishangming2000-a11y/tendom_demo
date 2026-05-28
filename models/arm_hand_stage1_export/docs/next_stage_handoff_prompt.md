# Next Stage Handoff Prompt

Continue `tendon_project` from the closed Stage1 arm-hand virtual prototype baseline.

Current baseline:

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Lift scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Closeout report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage1_virtual_prototype_closeout.md`
- Baseline manifest: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\current_baseline_manifest.json`
- Default-posture lift demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py`

Latest known result:

- default-posture lift demo status: `PASS`
- pure physics final lift: about `0.158 m`
- ball-hand contacts: `7`
- max penetration: about `0.0034 m`

Guardrails:

- Do not modify CAD/STL.
- Do not overwrite the Stage1 baseline unless explicitly promoted.
- Do not train yet.
- Do not add tendon routing yet.
- Treat collision proxy v2 as smoke-test geometry, not final physics.

Recommended Stage2 start:

1. build task API around current baseline;
2. run small ball-pose sweep for success region;
3. define observation/action/reward schema;
4. collect tiny scripted dataset v0;
5. keep Shadow/video comparison as regression;
6. only then discuss BC/RL training.
