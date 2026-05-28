# Arm-Hand Stage1 Physics Regression Report

Generated: 2026-05-27T02:26:28

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Overall status: **PASS**
- Model summary: `{'nbody': 32, 'njnt': 27, 'nu': 26, 'ngeom': 65, 'nsite': 14, 'nmesh': 29, 'nq': 33, 'nv': 32}`
- Training ready: **No**
- Dataset v0 ready: **Yes, tiny smoke only**
- Open render: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_physics_regression\regression_open.png`
- Hold render: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_physics_regression\regression_hold.png`

## Test Results

| test | status | detail |
|---|---|---|
| model_load | PASS | `{"nbody": 32, "njnt": 27, "nu": 26, "ngeom": 65, "nsite": 14, "nmesh": 29, "nq": 33, "nv": 32}` |
| joint_kinematic_smoke | PASS | `{"total": 27, "pass": 26, "fail": 0, "skipped": 1}` |
| open_static_contact | PASS | `{"count": 0, "max_penetration": 0.0}` |
| scripted_ball_contact_smoke | PASS | `{"finite": true, "hold_contacts": 7, "hold_max_penetration": 0.003885329801188645, "ball_displacement": 0.0, "four_finger_avg_tip_ball_distance": 0.05276908148359338, "thumb_ball_distance": 0.0427909946471727}` |

## Notes

- This checks model load, hinge kinematics, static contact, and a pinned-ball scripted contact smoke.
- The collision proxy is still v0 and should not be treated as final physics or training geometry.
- If this report is PARTIAL, inspect the failing rows before collecting more data.
