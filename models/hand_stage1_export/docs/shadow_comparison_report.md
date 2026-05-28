# Shadow Comparison Report

- Local Shadow model found: yes
- Shadow model path: `D:\tendon_project\simulations\models\shadow_hand\right_hand.xml`

## Structure Counts

| Item | hand_stage1 | Shadow Hand |
|---|---:|---:|
| Links/bodies | 23 | 25 |
| Joints | 21 | 24 |
| Hinge/revolute joints | 21 | 24 |
| Sites | 0 | 1 |
| Fingertip sites | 0 | 0 |
| Actuators | 0 | 24 |
| Tendons | 0 | 0 |
| Collision geoms | 23 | 25 |
| Mesh assets | 0 | 15 |

## Grasp Ball Demo Readiness

- hand_stage1: can load in MuJoCo as a primitive stage1 skeleton, can run joint smoke tests, and can show a scripted visual ball-wrap pose.
- hand_stage1 raw mesh debug: loads, but exported STL visuals are not clean per-link meshes and produce duplicated geometry during articulation.
- Shadow Hand: local model has actuators and collision geoms and is closer to a real grasp-task baseline.

## Gap Summary

- hand_stage1 is currently a stage1 geometry/kinematics skeleton, not a Shadow Hand equivalent.
- Default hand_stage1 MJCF uses primitive geoms for inspection because raw exported STL link meshes are not suitable for clean per-link visualization.
- Shadow has position actuators and a mature collision setup; hand_stage1 has no actuators, no tendons, and no fingertip sites yet.
- The current hand_stage1 scene can run a visual scripted ball-wrap demo, but it is not a stable grasp task.

## Required Next Steps

1. Fix or re-export per-link mesh geometry from SolidWorks/SW2URDF.
2. Review joint axes and limits, especially possible mcp_flex/mcp_abd semantic reversal.
3. Add fingertip sites.
4. Add clean collision geoms.
5. Add actuators and a simple controller.
6. Only then consider imitating Shadow-style grasp tasks.

## Notes

- Shadow site names: grasp_site. Fingertip-like sites: none named with `tip`.
- Local Shadow XML uses actuators; no explicit MuJoCo tendon elements were found in the compiled model.
