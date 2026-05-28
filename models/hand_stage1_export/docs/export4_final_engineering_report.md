# Export4 Final Engineering Report

Generated: 2026-05-26

## Executive Summary

Tonight's most important result is that export4 now has a passing scripted-smoke candidate:

- `scene_ball_export4_palmar_ypos_collision_candidate.xml`
- ball pose `[0.0, 0.08, 0.21]`
- local fingertip collision spheres with radius `0.015 m`
- regression result `7 PASS / 0 FAIL / 0 SKIPPED`
- 5-episode dry run result `5/5 success_smoke`

This is not a training baseline. It is a clean engineering candidate for the next tiny dataset-v0 dry run after the user confirms that `+Y` is the intended palm/grasp side.

## What Was Completed

### wrist_2_joint

- Verified `wrist_2_joint` as active hinge/revolute in the experimental branch.
- Range: `-0.8 0.8`
- Actuator: `wrist_2_joint_pos`
- Test status: PASS.

### Collision Proxy

Previous tuned branch:

- Static open penetration at default pose was reduced to `0.000000 m`.
- But default `-Y` ball side failed grasp smoke.

New candidate branch:

- Added fingertip collision sphere proxies at the five fingertip sites.
- Radius: `0.015 m`
- Kept clean STL as visual only.
- Did not edit CAD/STL/URDF/joint tree/joint names/current-baseline.
- Candidate open static contact: `0`
- Candidate open static max penetration: `0.000000 m`
- Candidate hold max penetration: about `0.001042 m`

### Scripted Grasp

Default `-Y` tuned branch:

- scripted task runs but fails;
- no ball-hand contact;
- four-finger average tip-ball distance remains too large.

Candidate `+Y` branch:

- scripted task passes;
- hold stage creates 2 ball-hand contacts;
- four-finger average tip-ball distance about `0.0465 m`;
- thumb-ball distance about `0.0433 m`;
- 5-episode dry run passes 5/5.

### Adapter / Task API

Completed:

- `scripts/export4_task_api.py`
- `scripts/run_export4_scripted_grasp_task.py`
- `scripts/replay_export4_smoke_dataset.py`
- `scripts/export4_retargeting_scaffold.py`
- `scripts/run_export4_regression_tests.py`

Task API:

- action dim: `22`
- observation vector dim: `112`
- fields include qpos, qvel, ctrl, fingertip sites, ball position, ball velocity, contact summary, and fingertip-ball distances.

### Smoke Data

Created:

- `data/export4_palmar_ypos_candidate_5ep_smoke_rollout.npz`

This is a small smoke rollout, not a training dataset. It is useful for replay and adapter checks.

## Test Results

### Previous Tuned Branch

Scene:

- `mjcf/scene_ball_export4_wrist2_collision_tuned.xml`

Regression:

- overall: FAIL
- result: `6 PASS / 1 FAIL / 0 SKIPPED`
- failing test: scripted grasp at default `-Y` ball side

### Active Candidate Branch

Scene:

- `mjcf/scene_ball_export4_palmar_ypos_collision_candidate.xml`

Regression:

- overall: PASS
- result: `7 PASS / 0 FAIL / 0 SKIPPED`
- model load: PASS
- joint smoke: PASS
- wrist_2 test: PASS
- collision open static: PASS
- adapter unit test: PASS
- scripted grasp smoke: PASS
- replay smoke dataset: PASS

## Why The Candidate Works Better

The earlier diagnostics showed that the `-Y` ball side was visually and metrically far from the closing fingers, while the mirror `+Y` side was much closer. The candidate therefore tests the `+Y` side and adds local fingertip collision spheres instead of inflating the entire palm or finger collision proxy.

This keeps the fix small:

- no CAD edit;
- no STL edit;
- no joint-tree edit;
- no joint-name change;
- no tendon routing;
- no training.

## Remaining Problems

### BLOCKER Before Full Dataset / Training

- The user confirmed on 2026-05-26 that `+Y` is the palm/grasp side for export4.
- Full dataset collection should still wait until the arm/hand task reset, collision proxy policy, and data schema are frozen.
- Training remains prohibited.

### MAJOR

- Candidate contact depends on fingertip sphere proxies, not high-fidelity collision.
- Thumb and palm contact quality are still smoke-level, not Shadow-equivalent.
- Free-ball grasp is not validated; ball is pinned during scripted smoke.

### MINOR

- `*_mcp_flex_joint` names remain semantically misleading; they are currently treated as spread / abduction-adduction.
- Retargeting scaffold is semantic only; no real video/Shadow retargeting is implemented here.

## Can We Enter Dataset Collection v0?

Tiny dataset-v0 dry run: yes, if the user accepts `+Y` as the canonical palm side.

Full dataset collection: not yet.

Training: no.

## Recommended Next Command

Run the active candidate regression:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\run_export4_regression_tests.py --scene D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml --hand D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_palmar_ypos_collision_candidate.xml --label palmar_ypos_candidate --ball-y 0.08 --dataset D:\tendon_project\simulations\models\hand_stage1_export\data\export4_palmar_ypos_candidate_5ep_smoke_rollout.npz --report D:\tendon_project\simulations\models\hand_stage1_export\docs\export4_palmar_ypos_candidate_regression_report.md --metadata D:\tendon_project\simulations\models\hand_stage1_export\metadata\export4_palmar_ypos_candidate_regression_results.json
```

Then visually inspect:

- `docs/visual_checks_export4_palmar_ypos_candidate_5ep_replay/episode_4_frame_0239_front.png`

## 2026-05-26 Update: +Y Confirmed And Arm-Hand Assembly Started

The user visually confirmed:

> `+Y` is the palm/grasp side for export4.

The `+Y` palmar-side candidate is therefore the active hand-side scripted-smoke candidate. A first arm+hand MuJoCo assembly was also generated:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_palmar_ypos_candidate.xml`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_palmar_ypos_candidate.xml`

Arm+hand smoke result:

- model: `31 bodies / 26 joints / 26 actuators / 59 geoms / 6 sites / 29 meshes`
- joint kinematic smoke: `26 PASS / 0 FAIL / 0 SKIPPED`
- actuator stepping: `PASS`

Conclusion:

- The hand is now a child body under arm `ee_tool_frame`, not a separate point-attached visual.
- The wrist/base visually connects near the arm flange and is good enough for first MuJoCo arm+hand smoke checks.
- It is still not a CAD-certified flange mount. Final flange calibration should tune only the fixed `ee_tool_frame -> hand_base_link` transform in a separate MJCF experiment.
