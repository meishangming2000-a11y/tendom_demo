# Export4 Regression Test Report

Generated: 2026-05-26T02:09:11

- Overall: **FAIL**
- PASS / FAIL / SKIPPED: `6 / 1 / 0`
- Can enter dataset collection v0: `False`

## Tests

| test | result | status/excerpt |
|---|---|---|
| `model_load_test` | **PASS** | `{'scene': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\mjcf\\scene_ball_export4_wrist2_collision_tuned.xml', 'nbody': 26, 'njnt': 23, 'nu': 22, 'ngeom': 50, 'nsite': 5}` |
| `joint_smoke_test` | **PASS** | `` |
| `wrist_2_test` | **PASS** | `{'status': 'PASS'}` |
| `collision_penetration_diagnosis` | **PASS** | `{'conclusion': 'PARTIAL_DEFAULT_SIDE_FAILS_MIRROR_SIDE_BETTER', 'open_static_penetration_status': 'PASS_UNDER_5MM', 'default_grasp_status': 'FAIL_GRASP_SIDE_OR_TARGET_NEEDS_REVIEW', 'mirror_grasp_status': 'PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE'}` |
| `adapter_unit_test` | **PASS** | `{'status': 'PASS'}` |
| `scripted_grasp_task_smoke` | **FAIL** | `{'status': 'FAIL_EXPECTED_UNTIL_GRASP_SIDE_FIXED'}` |
| `replay_smoke_dataset` | **PASS** | `` |

## Blocking Failure

- `scripted_grasp_task_smoke` fails because the default `-Y` ball side remains far from the closing fingers and creates no ball-hand contact.
- This is intentionally not hidden by the regression runner.

## Next Fix Before Dataset v0

1. Finalize canonical palm side / ball side for export4.
2. Re-run scripted grasp task with that side.
3. Only then refine fingertip collision proxy for reliable contact.
