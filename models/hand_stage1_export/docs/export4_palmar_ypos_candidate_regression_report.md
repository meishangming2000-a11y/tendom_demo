# Export4 Regression Test Report

Generated: 2026-05-26T10:14:51

- Label: `palmar_ypos_candidate`
- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml`
- Ball position: `[0.0, 0.08, 0.21]`
- Overall: **PASS**
- PASS / FAIL / SKIPPED: `7 / 0 / 0`
- Can enter dataset collection v0: `True`

## Tests

| test | result | status/excerpt |
|---|---|---|
| `model_load_test` | **PASS** | `{'scene': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\mjcf\\scene_ball_export4_palmar_ypos_collision_candidate.xml', 'nbody': 26, 'njnt': 23, 'nu': 22, 'ngeom': 55, 'nsite': 5}` |
| `joint_smoke_test` | **PASS** | `` |
| `wrist_2_test` | **PASS** | `{'status': 'PASS'}` |
| `collision_open_static_test` | **PASS** | `{'contact_count': 0, 'max_penetration': 0.0, 'ball_hand_contact_count': 0, 'ball_hand_max_penetration': 0.0, 'source_counts': {}}` |
| `adapter_unit_test` | **PASS** | `{'status': 'PASS'}` |
| `scripted_grasp_task_smoke` | **PASS** | `{'status': 'PASS'}` |
| `replay_smoke_dataset` | **PASS** | `` |

## Blocking Failure

- If `scripted_grasp_task_smoke` is FAIL, the selected ball side/collision proxy is not ready for dataset collection v0.
- If all tests pass, the selected experimental branch can be used for a tiny dataset-v0 dry run, but still not for training.

## Next Fix Before Dataset v0

1. Inspect visual frames for the selected scene and ball side.
2. Confirm the selected ball side is the actual palm side.
3. Keep training disabled until dataset quality checks are added.
