# Stage3 Task Contract Starter V0

Generated: 2026-06-03

## Contract Name

```text
stage3_sensor_aware_gentle_grasp_hold_v0
```

## Purpose

Create the first Stage3 MuJoCo task contract for sensor-aware fragile-object manipulation.

Stage3 stays in MuJoCo. It uses simulated vision and synthetic tactile/slip abstractions. It does not claim real camera, tactile, ultrasound, or hardware integration.

## Anchor Task

```text
approach egg-like object -> gentle grasp -> lift 5 cm -> hold 3 s -> no slip -> no crush
```

## Object Definition

Initial object should be simple but fragile-task meaningful:

- shape: egg-like ellipsoid or ellipsoid/capsule approximation
- pose: randomized on support surface within a small workspace
- orientation: at least one dominant axis estimate
- material parameters: mass, friction, contact softness, penetration threshold
- fragile threshold: crush-risk proxy from contact/penetration/normal proxy

Do not tune object physics to make the demo easy without recording the assumptions.

## Phase Contract

| Phase | Goal | Control default | Sensor abstraction |
|---|---|---|---|
| `default_hold` | reset/stabilize | fixed open hand | none |
| `vision_acquire` | estimate object pose/shape/confidence | no contact motion | vision active |
| `approach` | move near object without pushing | phase-gated/scripted | vision pose estimate |
| `pre_contact_align` | align fingers around object | phase-gated/scripted | vision + proprioception |
| `gentle_close` | acquire first contact | conservative close | tactile contact fields active |
| `contact_settle` | check contact quality | phase-specific | tactile/crush/slip fields |
| `grasp_secure_check` | decide lift/abort | rule/check gate | tactile grip_stable |
| `lift` | lift 5 cm | phase-specific | tactile slip/crush active |
| `hold` | hold 3 s | phase-specific/residual allowed | tactile slip/crush active |
| `slip_recover_or_abort` | respond to slip/crush risk | explicit state transition | tactile slip/crush active |
| `release_or_reset` | release safely | rule-based initially | release_contact_clear |

Early approach/grasp/lift must not be fully live-observation BC. Learned modules should start as phase-specific residuals after this contract is stable.

## Observation Schema

Policy observation should include:

```text
proprio.qpos
proprio.qvel
proprio.ctrl
phase.id
phase.progress
vision.object_pose_xyz_est
vision.object_axis_est
vision.object_shape_params_est
vision.goal_pose_xyz_est
vision.object_to_goal_est
vision.confidence
vision.occlusion
vision.latency_steps
tactile.contact_present
tactile.contact_regions
tactile.normal_contact_proxy
tactile.contact_persistence
tactile.relative_tangential_motion
tactile.slip_score
tactile.grip_stable
tactile.crush_risk
```

Ground truth MuJoCo object pose/contact may be logged as:

```text
gt.object_pose
gt.object_velocity
gt.contact_summary
gt.penetration
gt.eval_metrics
```

Ground truth fields are for labels, replay QA, and eval. They should not be the default learned-policy input once sensor abstraction is enabled.

## Action Schema

Start with the existing arm-hand actuator action dimension.

Allowed policy forms:

- scripted phase action
- hard-gated expert action schedule
- phase-specific learned residual added to a safe base action
- phase-specific learned module for hold/slip response after smoke success

Blocked by default:

- unconstrained end-to-end policy over all phases
- fully live-observation BC for approach / first close / early lift
- RL before task contract, replay QA, and reward/termination QA pass

## Success Criteria

An episode succeeds when all are true:

- object is lifted at least `0.05 m` above support
- hold duration reaches `3 s`
- object remains within allowed pose drift during hold
- `slip_score` remains below threshold
- `crush_risk` remains below threshold
- contact/penetration remains below failure threshold
- state remains finite

## Failure Reasons

Use these terminal reasons first:

```text
running
success_gentle_grasp_hold
non_finite_state
premature_object_push
no_contact_timeout
grasp_not_secure
slip_detected
object_dropped
crush_risk_exceeded
excessive_penetration
bad_vision_confidence
unstable_hold
timeout
```

## Dataset Fields

Stage3 dataset rows should include:

```text
obs
next_obs
proprio_obs
vision_obs
tactile_obs
gt_eval_state
actions
expert_actions
residual_actions_optional
phase_ids
phase_step_ids
episode_ids
rewards
dones
successes
failures
terminal_reason_ids
sensor_noise_params
object_params
```

## Replay QA

Replay QA should verify:

- deterministic replay of actions
- deterministic reconstruction of vision/tactile abstractions for fixed seed
- shape/schema match
- terminal reason match
- success/failure metric match
- max obs/next_obs/reward error within threshold

## First Smoke Gate

Stage3.0 smoke gate:

- task contract exists
- egg-like object scene exists
- scripted expert passes at least one fixed pose
- dataset collection succeeds for fixed pose
- replay QA passes
- report and contact sheet exist

## First Robustness Gate

Stage3.1/3.2 should add:

- noisy object pose estimate
- contact/tactile synthetic fields
- slip/crush proxy fields
- 3-5 fixed/randomized poses
- failure taxonomy report

## Overclaim Boundary

Do not claim:

- real egg grasping
- real camera integration
- real tactile/ultrasound integration
- hardware readiness
- end-to-end learned manipulation

Until Stage4 hardware interfaces exist, Stage3 claims are MuJoCo sensor-abstraction claims only.
