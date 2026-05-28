# Export4 Scripted Grasp Task Report

Generated: 2026-05-26T02:09:11

## Scope

Uses `export4_task_api.py` to run a small scripted grasp scaffold. No RL/BC/training, CAD edit, STL edit, joint-tree edit, joint rename, or tendon routing is performed.

## Setup

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Episodes: `3`
- Ball position: `[0.0, -0.1, 0.21]`
- Ball pinned: `True`
- Four-tip threshold: `0.08`
- Success count: `0`
- Status: **FAIL_EXPECTED_UNTIL_GRASP_SIDE_FIXED**

## Episode Results

| ep | label | success | contacts | ball-hand | max pen | ball disp | four-tip avg | thumb-ball |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | fail_far_or_wrong_side | False | 0 | 0 | 0.000000 | 0.000000 | 0.154570 | 0.142076 |
| 1 | fail_far_or_wrong_side | False | 0 | 0 | 0.000000 | 0.000000 | 0.154570 | 0.142076 |
| 2 | fail_far_or_wrong_side | False | 0 | 0 | 0.000000 | 0.000000 | 0.154570 | 0.142076 |

## Interpretation

- Failure here is expected while the canonical palm/ball side remains unresolved.
- The scaffold is still useful because it exercises reset, action application, staged control, observation, contact metrics, and rollout saving.
- `thumb_ball_distance` is recorded but not required for success yet.
