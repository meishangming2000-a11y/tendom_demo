# Export4 Shadow-Style Task Gap Checklist

Generated: 2026-05-26

## Scope

This checklist compares the current export4 smoke hand against the kind of scaffold needed for Shadow-style scripted tasks. It does not claim Shadow equivalence, and it does not start RL/BC/training.

## Current Capabilities

- Visual clean mesh is available for export4 and is used as visual geometry.
- Simplified collision proxy exists and is used instead of STL mesh collision.
- Position actuators exist for the controllable hand joints.
- Five fingertip sites exist:
  - `index_tip_site`
  - `middle_tip_site`
  - `ring_tip_site`
  - `little_tip_site`
  - `thumb_tip_site`
- Scripted grasp smoke scripts exist.
- `wrist_2_joint` is verified as an active hinge in the experimental branch.
- Adapter unit tests pass with `action_dim = 22`.
- Minimal task API scaffold exists:
  - `scripts/export4_task_api.py`
- Scripted grasp task scaffold exists:
  - `scripts/run_export4_scripted_grasp_task.py`
- Replay scaffold exists:
  - `scripts/replay_export4_smoke_dataset.py`
- Retargeting semantic scaffold exists:
  - `scripts/export4_retargeting_scaffold.py`

## Remaining Gaps

- Robust collision proxy:
  - current proxy avoids static penetration in the tested open pose;
  - it is still conservative and does not create contact in the scripted grasp at the current default ball side.
- Stable free-ball grasp:
  - current scaffold pins the ball by default for diagnosis;
  - free-object grasp is not validated.
- Contact-aware controller:
  - current controller is scripted position target only;
  - no feedback controller adapts to contact.
- Tendon/coupling model:
  - no tendon routing or joint coupling has been added.
- Retargeting objective:
  - only semantic aliases and keypoints are defined;
  - no human/Shadow trajectory optimization is implemented.
- Dataset quality checks:
  - tiny smoke dataset exists only for shape/replay;
  - no dataset v0 quality gate is ready.
- Real-to-sim calibration:
  - CAD geometry, collision proxy, actuator gains, and mass/contact parameters are not calibrated.
- Thumb opposition final tuning:
  - thumb can participate in scripted smoke;
  - final contact-quality opposition remains unresolved.
- Palm/ball-side convention:
  - default `-Y` ball side fails the scripted grasp-side check;
  - mirror `+Y` is closer but still lacks contact.

## Staged Route

### Stage 1.0: Current Export4 Smoke Hand

- Keep export4 current-baseline frozen.
- Use the wrist2/collision-tuned experimental branch for tests.
- Treat results as diagnostic only.

### Stage 1.1: Collision Proxy Tuned + Task API

- Finalize canonical palm side and ball side.
- Tune fingertip/distal collision proxy after side convention is fixed.
- Keep task API stable enough for small scripted tests.

### Stage 1.2: Scripted Grasp Scaffold

- Run scripted tasks through `export4_task_api.py`.
- Require explicit success/failure labels.
- Do not hide grasp-side failures by inflating collision geoms.

### Stage 1.3: Smoke Dataset + Replay

- Use tiny smoke datasets for replay and adapter checks.
- Add quality checks before any dataset v0 expansion.
- Keep training disabled until labels and contact behavior are meaningful.

### Stage 1.4: Retargeting Scaffold

- Use semantic aliases for export4 joints.
- Map video/Shadow keypoints to export4 keypoints only after palm-side convention is fixed.
- Preserve current joint names until CAD/URDF naming is intentionally revised.

### Stage 2.0: Tendon/Coupling And Real-To-Sim

- Add tendon/coupling only after kinematic, collision, and task scaffolds are stable.
- Add real-to-sim calibration and contact model validation before training claims.

## Current Decision

- Continue Shadow-style scripted task API work: yes.
- Start dataset collection v0: not yet.
- Start RL/BC training: no.
