# Stage3 Sensor Requirements V0

Generated: 2026-06-03

## Purpose

Define the sensor requirements for:

```text
stage3_sensor_aware_gentle_grasp_hold_v0
```

The anchor task is:

```text
approach egg-like object -> gentle grasp -> lift 5 cm -> hold 3 s -> no slip -> no crush
```

This document is the first Stage3 sensor-design deliverable. It defines the
required sensor semantics, their phase usage, MuJoCo abstraction source, future
hardware mapping, and acceptance gates.

Stage3 remains MuJoCo-only. This document does not claim real camera, tactile,
ultrasound, electronics, firmware, or real-hand integration. Those belong to
Stage4.

## Boundary

Stage3 sensor work means:

- define what the policy is allowed to sense
- replace perfect MuJoCo object state with simulated sensor-style fields
- generate tactile, slip, and crush proxies from MuJoCo state
- keep ground truth available for labels, replay QA, and evaluation only
- prepare a clean handoff to future Stage4 hardware design

Stage3 sensor work does not mean:

- selecting final camera or tactile hardware
- designing PCB, ADC, MCU, power, or wiring
- integrating ultrasound hardware into the hand runtime
- claiming real egg grasping or hardware readiness

## Sensor Requirement Summary

| Sensor family | Main question answered | Policy use | Eval use | Stage3 source | Stage4 hardware candidate |
|---|---|---|---|---|---|
| Vision object pose | Where is the object? | yes | yes | noisy MuJoCo pose estimate | RGB/depth camera or external tracking |
| Vision object axis/shape | How should fingers align? | yes | yes | noisy MuJoCo orientation/shape estimate | calibrated camera + shape fitting |
| Vision confidence/occlusion | Is approach safe? | yes | yes | configurable noise/visibility model | camera confidence, tracking score |
| Proprioception | Where is the hand/arm? | yes | yes | qpos/qvel/ctrl | joint encoders, motor state |
| Contact presence | Did contact begin? | yes | yes | MuJoCo contact proxy | fingertip contact/pressure/tactile pads |
| Contact region | Which finger/side is involved? | yes | yes | contact-body region map | distributed tactile regions |
| Normal contact proxy | How hard are we pressing? | yes | yes | penetration/normal proxy | force/tactile/pressure estimate |
| Contact persistence | Is contact stable over time? | yes | yes | contact history counter | filtered tactile/contact state |
| Slip score | Is object slipping? | yes | yes | relative tangential motion + contact | tactile slip, acoustic/ultrasound slip, vision drift |
| Grip stable | Is it safe to lift? | yes | yes | contact + slip + crush gate | tactile fusion result |
| Crush risk | Are we damaging the object? | yes | yes | penetration/normal proxy | force/tactile proxy, current/tendon tension proxy |
| Release clear | Is hand contact cleared? | yes | yes | post-release contact proxy | tactile contact clear signal |

## Phase-Sensor Map

| Phase | Required sensor semantics | Abort or slow-down trigger |
|---|---|---|
| `default_hold` | proprioception only | non-finite state |
| `vision_acquire` | object pose, axis, shape, confidence, occlusion | low confidence or high occlusion |
| `approach` | object pose estimate, object-to-goal estimate, proprioception | premature object motion, low confidence |
| `pre_contact_align` | object axis, shape estimate, proprioception | poor alignment or low confidence |
| `gentle_close` | contact present, contact region, normal proxy | no contact timeout, rising crush risk |
| `contact_settle` | contact persistence, slip score, crush risk | unstable contact, slip, crush risk |
| `grasp_secure_check` | grip stable, contact persistence, normal proxy | grasp not secure |
| `lift` | slip score, crush risk, contact persistence, object lift estimate | slip, drop, crush risk |
| `hold` | slip score, object pose drift, contact persistence, crush risk | unstable hold, slip, crush risk |
| `slip_recover_or_abort` | slip score, grip margin, crush risk | repeated slip or high crush risk |
| `release_or_reset` | release contact clear, object pose, support contact | contact not cleared |

## Success And Failure Coverage

Every success or failure condition must have one policy-visible sensor path and
one ground-truth evaluation path.

| Condition | Policy-visible sensor path | Ground-truth eval path | Notes |
|---|---|---|---|
| Lift at least 5 cm | vision object pose estimate + phase state | MuJoCo object pose | policy should not receive perfect pose by default |
| Hold 3 s | phase timer + tactile persistence | simulator step count/time | deterministic replay must match |
| Pose drift bounded | vision pose delta estimate | MuJoCo pose drift | used during hold and recovery |
| No slip | tactile slip score | relative object/contact motion | slip proxy must be configurable |
| No crush | tactile crush risk | penetration/contact proxy | threshold is task-level, not hardware-calibrated yet |
| Contact secure | contact persistence + grip stable | contact summary | required before lift |
| Premature push | vision pose delta before contact | MuJoCo object displacement | approach gate |
| Object dropped | tactile contact loss + vision/drop estimate | floor/support contact + object height | lift/hold gate |
| Bad vision confidence | vision confidence/occlusion | configured sensor state | can abort before contact |
| Release clear | tactile release contact clear | final hand/object contacts | release/reset gate |

## Policy Input Boundary

Allowed policy inputs:

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
vision.noise_std
tactile.contact_present
tactile.contact_regions
tactile.normal_contact_proxy
tactile.contact_persistence
tactile.relative_tangential_motion
tactile.slip_score
tactile.grip_stable
tactile.crush_risk
tactile.release_contact_clear
```

Ground-truth fields allowed for logging, labeling, replay QA, and eval only:

```text
gt.object_pose
gt.object_velocity
gt.contact_summary
gt.penetration
gt.eval_metrics
```

Blocked by default:

- perfect object pose as learned-policy input
- raw MuJoCo contact body lists as learned-policy input
- raw penetration/contact internals presented as real tactile data
- end-to-end image or omniscient-state policy over all phases

## Stage3 Simulation Source Requirements

Vision abstraction requirements:

- pose noise must be configurable
- axis/shape noise must be configurable
- confidence and occlusion must be logged
- latency steps must be represented, even if initially fixed
- fixed seed must reproduce the same sensor sequence during replay QA

Tactile/slip abstraction requirements:

- contact regions must be stable symbolic names, not backend-only body dumps
- normal contact proxy must be normalized or thresholded consistently
- contact persistence must be a history-derived field
- slip score must combine relative tangential motion and contact state
- crush risk must come from contact/penetration/normal proxy
- release contact clear must be explicit for release/reset phases

## Future Hardware Mapping

This is a Stage4 handoff map, not final hardware selection.

| Stage3 field | Future hardware meaning | Candidate physical source | Stage4 risk |
|---|---|---|---|
| `vision.object_pose_xyz_est` | object center estimate | camera/tracker | calibration, occlusion, lighting |
| `vision.object_axis_est` | dominant object axis | camera shape fit | symmetry and partial visibility |
| `vision.object_shape_params_est` | approximate size/shape | camera/depth/known class prior | fragile object variation |
| `vision.confidence` | tracking reliability | perception score | confidence calibration |
| `tactile.contact_present` | finger/object contact | fingertip contact/tactile sensor | mounting and sensitivity |
| `tactile.contact_regions` | contact distribution | multi-region tactile layout | routing and durability |
| `tactile.normal_contact_proxy` | pressure/force proxy | tactile pressure, force proxy, tendon load | calibration to real force |
| `tactile.contact_persistence` | stable contact duration | filtered contact state | debounce and latency |
| `tactile.relative_tangential_motion` | slip precursor | tactile flow, acoustic/ultrasound, vision drift | signal quality |
| `tactile.slip_score` | slip probability/proxy | tactile/acoustic/ultrasound fusion | false positives |
| `tactile.grip_stable` | lift permission signal | sensor fusion result | conservative thresholding |
| `tactile.crush_risk` | excessive force risk | force/tactile/current/tendon tension proxy | egg-specific calibration |
| `tactile.release_contact_clear` | safe release | tactile contact clear | residual light contact |

## Stage3.1 Acceptance Gate

Stage3.1 passes when all are true:

- sensor requirements document exists and is linked to the Stage3 task contract
- every success/failure condition has a policy-visible sensor path
- every success/failure condition has a ground-truth evaluation path
- phase-sensor map covers all Stage3 phases
- policy input boundary excludes default perfect object pose and raw contact dumps
- future hardware mapping is documented without claiming hardware integration
- TBD items are explicitly listed

## TBD / Risks

- Exact tactile region names need to be matched to stable hand geometry names.
- Slip score formula is still a MuJoCo proxy and must be validated against failure cases.
- Crush risk threshold is not hardware-calibrated.
- Vision latency is currently an abstraction, not a camera pipeline.
- Future ultrasound slip mapping remains a Stage4 handoff item, not a Stage3 runtime dependency.

## Next Step

Stage3.2 should implement or refine the sensor abstraction API against this
document:

- deterministic noisy vision sequence
- deterministic tactile/slip/crush proxy sequence
- replay-safe sensor noise parameters
- numeric checks for field ranges
- sensor report emitted with dataset/eval outputs
