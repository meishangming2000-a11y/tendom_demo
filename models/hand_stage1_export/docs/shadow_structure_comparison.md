# Shadow Structure Comparison

- hand_stage1 model: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_visual_clean_collision_proxy.xml`
- hand_stage1 scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Local Shadow model found: yes
- Shadow model: `D:\tendon_project\simulations\models\shadow_hand\right_hand.xml`

## Counts

| Item | hand_stage1 | Shadow right_hand |
|---|---:|---:|
| Bodies/links excluding world | 23 | 25 |
| Joints | 21 | 24 |
| Hinge joints | 21 | 24 |
| Actuators | 21 | 24 |
| Sites | 5 | 1 |
| Fingertip-like sites | 5 | 0 |
| Geoms | 99 | 62 |
| Collision geoms | 28 | 30 |
| Mesh assets | 23 | 15 |
| Tendons | 0 | 0 |

## Design Comparison

- hand_stage1 visual: clean SolidWorks STL meshes from export2, visual-only.
- hand_stage1 collision: simplified primitive proxy geoms, not STL mesh collision.
- hand_stage1 actuation: 21 MuJoCo position actuators added for smoke tests.
- Shadow visual/collision: local MJCF uses mesh visuals plus many curated primitive/mesh collision geoms with collision masks.
- Shadow actuation: local MJCF uses position actuators from defaults/classes.
- Tendon routing: no MuJoCo tendon elements are present in either current hand_stage1 or the local Shadow right_hand XML.

## Grasp Ball Readiness

- hand_stage1 can run a scripted position-control ball smoke test with the low-penetration ball position.
- hand_stage1 four long fingers close toward the ball; thumb opposition remains a TODO.
- Shadow right_hand has enough actuators/collisions for scripted grasp experiments, but this report did not run a Shadow ball demo.

## Gap

- hand_stage1 is a stage1 kinematic + clean visual + simplified collision proxy prototype, not a Shadow Hand equivalent.
- hand_stage1 now has 21 position actuators and 5 fingertip sites, enough for scripted smoke tests.
- The local Shadow MJCF has more joints/actuators and a mature collision setup, but no MuJoCo tendon elements in this local XML.
- hand_stage1 thumb opposition remains unresolved and should be confirmed in SolidWorks/URDF before Shadow-style grasp tasks are promoted.

## Notes

- Shadow sites: `grasp_site`.
- Shadow scene path: `D:\tendon_project\simulations\models\shadow_hand\scene_right.xml`.
