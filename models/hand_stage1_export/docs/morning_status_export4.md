# Morning Status Export4

Generated: 2026-05-26

## Update: +Y Palmar Candidate

After the first regression report, a new experimental candidate was built:

- `mjcf/hand_stage1_export4_palmar_ypos_collision_candidate.xml`
- `mjcf/scene_ball_export4_palmar_ypos_collision_candidate.xml`

This candidate keeps the frozen/current baseline untouched. It adds only local fingertip collision sphere proxies at the five fingertip sites and uses the `+Y` ball side:

- ball pose: `[0.0, 0.08, 0.21]`
- fingertip sphere radius: `0.015 m`
- clean STL remains visual-only

Candidate results:

- regression: `7 PASS / 0 FAIL / 0 SKIPPED`
- scripted grasp smoke: PASS
- 5-episode smoke dry run: `5/5 success_smoke`
- hold contacts: `2`
- hold max penetration: about `0.001042 m`
- four-finger average tip-ball distance: about `0.0465 m`
- thumb-ball distance: about `0.0433 m`

New key files:

- `docs/export4_active_file_index.md`
- `docs/export4_final_engineering_report.md`
- `docs/export4_palmar_ypos_candidate_regression_report.md`
- `metadata/export4_palmar_ypos_candidate_regression_results.json`
- `data/export4_palmar_ypos_candidate_5ep_smoke_rollout.npz`

Current decision:

- Tiny dataset-v0 dry run: allowed only if user confirms `+Y` is the real palm/grasp side.
- Full dataset collection: not yet.
- Training: still forbidden.

## 1. Starting Point

At the beginning of this pass, export4 had:

- frozen current-baseline files that must not be overwritten;
- a wrist2/collision-tuned experimental branch from the previous step;
- `wrist_2_joint` expected to be active;
- collision proxy static penetration improved but not fully task-validated;
- adapter unit tests passing;
- a tiny smoke dataset generated for pipeline validation only;
- a known major issue: the default `-Y` ball side appears to be the wrong grasp side and scripted grasp creates no ball-hand contact.

## 2. Files Completed

New or updated scripts:

- `scripts/export4_task_api.py`
- `scripts/run_export4_scripted_grasp_task.py`
- `scripts/replay_export4_smoke_dataset.py`
- `scripts/export4_retargeting_scaffold.py`
- `scripts/run_export4_regression_tests.py`
- `scripts/export4_wrist2_common.py`
- `scripts/test_wrist2_joint_export4.py`
- `scripts/diagnose_collision_proxy_penetration.py`
- `scripts/demo_grasp_ball_export4_wrist2_collision_tuned.py`
- `scripts/test_export4_adapter_mapping.py`
- `scripts/collect_export4_scripted_smoke_dataset.py`

New or updated reports and metadata:

- `docs/export4_task_api_report.md`
- `docs/export4_scripted_grasp_task_report.md`
- `metadata/export4_scripted_grasp_task_results.json`
- `metadata/export4_scripted_grasp_task_rollout.npz`
- `docs/export4_replay_report.md`
- `docs/export4_retargeting_scaffold.md`
- `metadata/export4_semantic_joint_aliases.json`
- `docs/export4_shadow_style_task_gap_checklist.md`
- `docs/export4_regression_test_report.md`
- `metadata/export4_regression_test_results.json`
- `docs/morning_status_export4.md`

Existing supporting outputs from the previous step remain active:

- `mjcf/hand_stage1_export4_wrist2_collision_tuned.xml`
- `mjcf/scene_ball_export4_wrist2_collision_tuned.xml`
- `data/export4_scripted_smoke_dataset.npz`
- `docs/export4_wrist2_joint_fix_report.md`
- `docs/collision_proxy_tuning_report.md`
- `docs/export4_adapter_unit_test_report.md`
- `docs/export4_scripted_smoke_dataset_report.md`

## 3. PASS Tests

Regression runner result: `6 PASS / 1 FAIL / 0 SKIPPED`.

PASS:

- model load test
- joint smoke test
- wrist_2 test
- collision penetration diagnosis for open-static threshold
- adapter unit test
- replay smoke dataset

## 4. FAIL / SKIPPED Tests

FAIL:

- `scripted_grasp_task_smoke`

Reason:

- the default `-Y` ball side remains far from the closing fingers;
- hold stage creates `0` ball-hand contacts;
- regression runner intentionally marks this as failure instead of hiding it behind a successful script exit code.

SKIPPED:

- none

## 5. wrist_2_joint

`wrist_2_joint` is fixed in the experimental branch:

- type: `hinge`
- parent: `wrist_middle_link`
- child: `palm_link`
- range: `-0.8 0.8`
- actuator: `wrist_2_joint_pos`
- test: PASS

The palm position does not translate much because the joint rotates near its origin, but relative orientation changes by about `0.3 rad` for both test directions.

## 6. Collision Proxy Penetration

The previous static penetration issue is improved for the tested open pose:

- tuned open-hand default ball pose `[0.0, -0.1, 0.21]`: max penetration `0.000000 m`
- wrist2 single-joint negative test: max penetration about `0.004361 m`

This is under the 5 mm target for the tested cases. However, the proxy is still not task-complete because the default ball side creates no meaningful contact.

## 7. Adapter Unit Tests

Adapter unit tests: PASS.

- action dim: `22`
- observation dim in the legacy adapter test: `86`
- `wrist_2_joint_pos` is included in action mapping
- fingertip sites are present

The newer `export4_task_api.py` observation vector is `112` dim because it additionally includes actuator ctrl, ball velocity, and fingertip distance fields.

## 8. Smoke Dataset

Tiny smoke dataset generated:

- `data/export4_scripted_smoke_dataset.npz`
- obs shape: `[750, 86]`
- action shape: `[750, 22]`
- labels:
  - `fail_far_from_ball`: 2
  - `visual_close_no_contact`: 3

This dataset is for adapter/replay/data-shape checks only. It is not training data.

## 9. Task API

Generated:

- `scripts/export4_task_api.py`
- `docs/export4_task_api_report.md`

The API includes:

- `load_model(scene_path)`
- `reset_hand_open()`
- `set_ball_pose(x, y, z)`
- `get_joint_names()`
- `get_actuator_names()`
- `get_action_dim()`
- `apply_action(action)`
- `get_observation()`
- `get_fingertip_positions()`
- `get_ball_pose()`
- `get_contact_summary()`
- `compute_fingertip_ball_distances()`
- `step(n=1)`
- `render_or_save_frame_if_available()`

## 10. Scripted Grasp Scaffold

Generated:

- `scripts/run_export4_scripted_grasp_task.py`
- `docs/export4_scripted_grasp_task_report.md`
- `metadata/export4_scripted_grasp_task_results.json`

It runs, but default smoke success fails:

- episodes: 3
- success count: 0
- failure reason: default ball side / target side creates no contact

## 11. Replay Viewer

Generated:

- `scripts/replay_export4_smoke_dataset.py`
- `docs/export4_replay_report.md`
- `docs/visual_checks_export4_replay/`

Replay status: PASS.

Important detail:

- dataset action dim matches current model action dim;
- dataset obs dim does not match the newer task API obs dim, because the task API has additional fields;
- replay still works by using the qpos/qvel prefix and action arrays.

## 12. Retargeting Scaffold

Generated:

- `scripts/export4_retargeting_scaffold.py`
- `docs/export4_retargeting_scaffold.md`
- `metadata/export4_semantic_joint_aliases.json`

It defines:

- palm reference
- five fingertip sites
- wrist action group
- four-finger spread group
- four-finger flex group
- thumb group
- semantic alias table

Important semantic note:

- four-finger `*_mcp_flex_joint` is currently treated as spread / abduction-adduction;
- four-finger `*_mcp_abd_joint` is likely current primary MCP flexion;
- no joint names were changed.

## 13. Dataset Collection v0

Current decision: do not enter dataset collection v0 yet.

Reason:

- regression overall is FAIL due to scripted grasp task smoke;
- canonical palm side / ball side remains unresolved;
- contact proxy still needs final fingertip tuning after side convention is fixed.

## 14. Training

Training remains forbidden for now.

Do not start RL, BC, or neural policy training until:

1. canonical palm side is fixed;
2. scripted grasp task smoke passes;
3. collision proxy creates meaningful contact without excessive penetration;
4. dataset labels pass quality checks.

## 15. User Manual Checks

Tomorrow's manual check list:

1. Confirm export4 palm side and world-coordinate sign convention.
2. Decide whether the canonical task ball side should be `+Y` rather than `-Y`.
3. Confirm how video/Shadow retargeting coordinates define palm-forward and grasp-side.
4. After side is fixed, let Codex tune distal/fingertip collision proxy radius and position.

## 16. Recommended Next Codex Command

Recommended next task:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\run_export4_scripted_grasp_task.py --ball-y 0.1 --save-rollout
```

Then compare it against:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\run_export4_regression_tests.py
```

If the `+Y` side is accepted as canonical, update the task default and rerun collision proxy fingertip tuning.
