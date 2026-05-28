# Arm-Hand Stage1 Physics Workflow

Generated: 2026-05-27

## Goal

Turn the CAD-frame-mounted export4 hand + arm assembly from a visual/kinematic model into a first usable MuJoCo physics prototype.

Current anchor:

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Alignment rule: `arm_flange_mount_csys == hand_wrist_mount_csys`
- Status: CAD-frame mount works; joint smoke passes; physical collision is not yet complete.

## Guardrails

- Do not modify CAD.
- Do not modify STL.
- Do not rename joints.
- Do not overwrite frozen/current hand or arm baselines.
- Do not train.
- Do not add tendon routing.
- New work must be saved as experiment files.
- Any uncertain mechanical semantics must be written as TODO, not guessed into the model.

## Phase 0: Freeze Current Virtual Entry Point

Purpose: mark the CAD-frame-mounted arm+hand model as the current virtual-space entry point before tuning begins.

Actions:

- Keep `arm_hand_export4_cad_mount_candidate.xml` as the reference input.
- Run load and joint smoke once.
- Record current body/joint/actuator counts.
- Save current renders as before-tuning evidence.

Outputs:

- `docs/arm_hand_stage1_virtual_entry_freeze.md`
- `metadata/arm_hand_stage1_virtual_entry_freeze.json`

Pass criteria:

- Scene loads.
- `26/26` joints pass smoke.
- Arm flange mount and hand wrist mount debug origins overlap.

## Phase 1: Joint Range And Pose Tuning

Purpose: define practical joint ranges and scripted poses that look natural and avoid obvious self-intersection before collision proxy tuning.

Inputs:

- CAD mount scene.
- Existing export4 joint direction audits.
- User-confirmed semantics:
  - `+Y` is palm/grasp side.
  - four-finger `*_mcp_flex_joint` is spread/abduction-adduction, not flexion.
  - flexion mainly uses current `*_mcp_abd_joint`, PIP, DIP.

Actions:

- Build a joint semantic table:
  - wrist joints;
  - four-finger spread joints;
  - four-finger flex joints;
  - thumb CMC/MCP/IP joints.
- Render open, half-close, full-close, and preshape poses.
- For each joint group, sweep candidate limits and target values.
- Tune scripted targets first; only narrow MJCF joint limits when motion is clearly impossible or unsafe.
- Keep thumb separate from four-finger tuning.

Outputs:

- `mjcf/arm_hand_export4_joint_limit_tuned.xml`
- `mjcf/scene_arm_hand_export4_joint_limit_tuned.xml`
- `docs/arm_hand_joint_limit_tuning_report.md`
- `metadata/arm_hand_joint_limit_tuning.json`
- `docs/visual_checks_arm_hand_joint_limit_tuning/`

Pass criteria:

- Scene loads.
- `26/26` joint smoke passes.
- Open pose has no severe self-intersection.
- Preshape pose looks anatomically plausible.
- Four fingers close toward palm side.
- Thumb does not flip through palm during scripted close.

Failure handling:

- If a joint only looks correct with a reversed sign, handle it in scripted target mapping first.
- If a joint axis is physically wrong, list it for SolidWorks review.
- Do not rename joints during this phase.

## Phase 2: Collision Proxy V0

Purpose: give the full arm+hand a simplified physical body, without using complex STL meshes as collision geoms.

Inputs:

- Joint-tuned arm+hand scene from Phase 1.

Design rules:

- STL meshes remain visual-only.
- Collision uses primitive proxy geoms.
- Proxies must be conservative but not so inflated that they cause static self-penetration.
- Parent-child contact can be disabled where appropriate.
- Fingertips keep small sphere/capsule proxy geoms for contact.

Proxy targets:

- Arm:
  - `base_link`: cylinder/box proxy.
  - `link_1`, `link_2`, `link_3`: capsule or box proxies.
  - `ee_mount`: cylinder/box proxy around flange and wrist mount region.
- Hand:
  - `hand_base_link`, `wrist_middle_link`: capsule/box proxy.
  - `palm_link`: ellipsoid/box proxy.
  - phalanx links: capsule proxies.
  - fingertips: small spheres.
  - thumb links: separate capsules; do not copy four-finger values blindly.

Outputs:

- `mjcf/arm_hand_export4_joint_limit_collision_proxy.xml`
- `mjcf/scene_arm_hand_export4_joint_limit_collision_proxy.xml`
- `docs/arm_hand_collision_proxy_report.md`
- `metadata/arm_hand_collision_proxy.json`
- `docs/visual_checks_arm_hand_collision_proxy/`

Pass criteria:

- Scene loads.
- Open pose static contacts are explainable and ideally zero for self-collision.
- Max static penetration is below `5 mm`, target below `3 mm`.
- Scripted close does not explode.
- Ball or external object can contact palm/fingers/thumb via proxy geoms.
- Arm links have collision representation, not only visuals.

Failure handling:

- If arm-hand self-collision appears at the flange, tune `contype/conaffinity` or exclude adjacent mount-pair collisions.
- If fingertips cannot contact objects, increase tip proxy slightly before inflating whole fingers.
- If palm causes initial penetration, shrink/shift palm proxy before changing ball placement.

## Phase 3: Physics Smoke Tasks

Purpose: verify that the tuned limits and collision proxy behave in simple scripted tasks.

Tasks:

- Load test.
- Joint smoke.
- Open static collision test.
- Scripted close without ball.
- Scripted ball-contact smoke.
- Optional arm wrist-pose variation smoke.

Outputs:

- `scripts/run_arm_hand_stage1_physics_regression.py`
- `docs/arm_hand_stage1_physics_regression_report.md`
- `metadata/arm_hand_stage1_physics_regression.json`

Pass criteria:

- All load/joint tests pass.
- No NaN / explosion.
- Contacts are present when expected and absent when clearly impossible.
- Penetration stays within smoke threshold.

## Phase 4: Stage Closeout

Purpose: make the current state reproducible and easy to continue.

Actions:

- Promote exactly one active experiment file.
- Write a file index.
- Archive superseded guessed-offset candidates.
- Keep CAD-frame candidate and its CSV provenance.
- Write remaining SolidWorks check list.

Outputs:

- `docs/arm_hand_stage1_active_file_index.md`
- `docs/arm_hand_stage1_phase_closeout_report.md`
- `docs/hand_stage1_mujoco_status.md` update
- `README.md` update

Closeout statement should answer:

- Which model should be opened now?
- Which tests pass?
- Which collision problems remain?
- Is it ready for tiny dataset v0?
- Is it ready for training? The expected answer for this stage is still no.

## Recommended Tonight Scope

Minimum useful completion:

1. Phase 0 freeze.
2. Phase 1 joint range/pose tuning v0.
3. Start Phase 2 collision proxy v0 for the hand and flange region.
4. Write closeout status.

Stretch goal:

- Add arm collision proxies and run full arm+hand physics regression.

Do not attempt tonight:

- Training.
- Tendon routing.
- High-fidelity mesh collision.
- Large dataset collection.

## Decision Gates

Gate A: joint tuning can proceed to collision if open/preshape/close poses are visually plausible.

Gate B: collision proxy can proceed to task scaffold if static penetration is under `5 mm` and scripted close is stable.

Gate C: dataset v0 can proceed only after collision and adapter observations are reproducible.

Gate D: training remains blocked until collision proxy, reset distribution, action limits, reward metrics, and dataset QA are stable.
