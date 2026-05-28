# Arm-Hand Collision Proxy V0 Report

Generated: 2026-05-27T02:26:19

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_collision_proxy.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy.xml`
- Ball scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml`
- Status: **PASS_LOAD_AND_SMOKE**
- Model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 64, 'nsite': 14, 'nmesh': 29, 'nq': 26, 'nv': 26}`
- Open static contacts without ball: `0`
- Open static max penetration without ball: `0.000000 m`
- Default ball position: `[0.021334, 0.145571, 0.518815]`
- Default ball radius: `0.028 m`
- Default ball local offset in palm frame: `[0.04, 0.12, -0.02]`
- Ball smoke status: `PASS`
- Ball displacement during pinned smoke: `0.000000 m`
- Hold contacts: `7`; hold max penetration: `0.003898 m`

## Added Arm Proxies

| body | proxy size | bbox extent | status |
|---|---|---|---|
| base_link | `0.0268150251 0.0541228689 0.0539611652` | `0.0654025003 0.132007003 0.131612599` | ADDED |
| link_1 | `0.0294324197 0.0438568369 0.0517794713` | `0.0717863888 0.106967896 0.126291394` | ADDED |
| link_2 | `0.0352628678 0.0396192297 0.0695821196` | `0.086006999 0.096632272 0.169712484` | ADDED |
| link_3 | `0.0370307341 0.0369158015 0.0684083179` | `0.0903188661 0.090038538 0.166849554` | ADDED |
| ee_mount | `0.0214219075 0.025186738 0.0369422249` | `0.0595052987 0.0699631572 0.102617286` | ADDED |

## Visual Checks

| pose | render |
|---|---|
| open_hand | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy\open_hand.png` |
| preshape | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy\preshape.png` |
| close_four_fingers | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy\close_four_fingers.png` |
| close_thumb_smoke | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_collision_proxy\close_thumb_smoke.png` |

## Limitations

- These are simplified primitive proxies. They make the full arm+hand physically present to external objects, but are not final contact geometry.
- Adjacent-link self-collision remains intentionally conservative/disabled in places.
- This is still not training-ready.
