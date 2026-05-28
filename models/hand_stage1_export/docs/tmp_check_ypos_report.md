# Export4 Scripted Grasp Task Report

Generated: 2026-05-26T10:28:51

## Scope

Uses `export4_task_api.py` to run a small scripted grasp scaffold. No RL/BC/training, CAD edit, STL edit, joint-tree edit, joint rename, or tendon routing is performed.

## Setup

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml`
- Episodes: `1`
- Ball position: `[0.0, 0.08, 0.21]`
- Ball pinned: `True`
- Four-tip threshold: `0.08`
- Success count: `1`
- Status: **PASS**

## Episode Results

| ep | label | success | contacts | ball-hand | max pen | ball disp | four-tip avg | thumb-ball |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | success_smoke | True | 2 | 2 | 0.001042 | 0.000000 | 0.046509 | 0.043258 |

## Interpretation

- Failure here is expected while the canonical palm/ball side remains unresolved.
- The scaffold is still useful because it exercises reset, action application, staged control, observation, contact metrics, and rollout saving.
- `thumb_ball_distance` is recorded but not required for success yet.
