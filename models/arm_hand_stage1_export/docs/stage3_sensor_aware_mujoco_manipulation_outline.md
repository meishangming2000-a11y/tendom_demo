# Stage3 Sensor-Aware MuJoCo Manipulation Outline

Generated: 2026-06-03

## Stage Boundary

Stage3 is **not** the hardware-interface stage.

The hardware is not available yet, so the next major project stage should stay inside MuJoCo. Stage3 should prepare the project for future real manipulation by adding realistic task structure, visual abstraction, tactile/slip abstraction, robustness gates, and fragile-object evaluation before any real hardware deployment.

Use this stage split:

```text
Stage2.5: MuJoCo training maturity
Stage3:   Sensor-aware MuJoCo manipulation
Stage4:   Hardware interface and real-hand integration
```

## Future Anchor Task

The long-term real-world anchor is:

```text
gently grasp, lift, and hold an egg-like fragile object
```

This is not because the final product is only an egg gripper. It is because the egg task forces the project to solve the right manipulation ingredients:

- gentle contact
- stable grasp without crushing
- slip detection
- object pose uncertainty
- phase-gated control
- recovery or abort logic
- sensor fusion between vision and local tactile cues

## Necessary Conditions For Real Egg Grasping

A real egg-grasp attempt needs these capabilities before it is safe or meaningful:

1. **Object localization**
   - Estimate egg position, approximate orientation, and confidence.
   - Handle noise, partial occlusion, and camera calibration error.

2. **Gentle contact and force proxy**
   - Avoid crushing or excessive penetration/contact force.
   - Track contact state per finger or per contact region.

3. **Slip awareness**
   - Detect whether the object is slipping during lift or hold.
   - Attribute slip to a finger or contact side when possible.

4. **Phase-gated control**
   - Use a state machine such as `approach -> gentle close -> contact check -> lift -> hold -> adjust/release`.
   - Do not drive the real hand with one unconstrained end-to-end policy.

5. **Robustness**
   - Work under pose noise, friction variation, object size variation, actuator delay, and imperfect closing.

6. **Recovery**
   - Retry, loosen, re-close, or abort when contact/slip checks fail.

## What We Can Do Now Without Hardware

Stage3 work can begin entirely in MuJoCo:

1. **Egg-like object benchmark**
   - Add an ellipsoid or egg-like collision object.
   - Define success as lift/hold with no slip and no crush.
   - Define failure as excessive contact, excessive penetration, drop, unstable hold, or uncontrolled roll.

2. **Vision abstraction interface**
   - Do not require a real camera yet.
   - Provide a simulated perception output:

```text
object_pose_xyz
object_orientation_or_axis
object_radius_or_shape_params
confidence
visibility_or_occlusion
noise_level
```

   - Train policies on noisy perception-style observations instead of perfect MuJoCo object state.

3. **Tactile/slip abstraction interface**
   - Do not claim ultrasound/tactile hardware is integrated.
   - Generate synthetic tactile signals from MuJoCo contact state:

```text
contact_present
contact_finger_id
normal_contact_proxy
relative_tangential_motion
slip_score
grip_stable
crush_risk
```

   - Later map these fields to a small tactile sensor set and the ultrasound slip detector when those hardware lanes mature.

4. **Gentle grasp/lift/hold task**
   - Start simpler than pick-place:

```text
approach egg -> gentle grasp -> lift 5 cm -> hold 3 s -> no slip -> no crush
```

   - This directly targets the real egg prerequisite.

5. **Robust training**
   - Randomize object pose, size, friction, mass, contact parameters, visual noise, action delay, and actuator noise.
   - Gate success with numeric eval before rendering demo videos.

6. **Recovery policies**
   - Add retry/abort actions.
   - Train or script slip response: hold, close slightly, lift slower, or release.

## Stage2.5 Still Matters

Stage2.5 should not be discarded. It is the bridge from the current pick-place work to Stage3.

Current Stage2.5 status after Gate2:

- v0.9 Gate2 hard-gated nearest-expert phase MoE: fixed 7 targets, exact local 5x5 around `-165`, `-135`, and `-105`, and held-out midpoint 4x4 around all three regions passed.
- This is a staged-control / nearest-expert baseline, not a smooth continuous target-interpolation policy.
- Main limitation: local target regions are now covered, but inter-region holdouts and perturbation robustness are still incomplete.
- Gate4 policy-structure maturity is complete: Stage3 should inherit phase-gated / phase-specific control. Early approach/grasp/lift stays conservative and should not be fully live-observation BC. Sensor-aware learned modules are best introduced first as phase-specific residuals for transport, descend, release, slip recovery, or abort logic.
- Gate5 Stage3 readiness is complete: Stage2.5 now has the dataset/replay/eval/report template, control framework, failure taxonomy, synthetic tactile/slip phase map, and vision abstraction replacement map needed to start Stage3.0.

Gate5 documents:

- `stage2_5_gate5_stage3_readiness.md`
- `stage3_task_contract_starter_v0.md`

Stage2.5 should continue until the MuJoCo training workflow is mature enough to support Stage3:

- local target interpolation repair
- held-out target eval
- domain randomization
- standardized dataset/replay/train/eval/demo/report loop
- phase-specific policy patterns
- failure-mode taxonomy

## How The Previous Pick-Place Training Helps Stage3

The pick-place work is not wasted. It gives Stage3 several reusable assets:

1. **Training pipeline**
   - Dataset collection.
   - Replay QA.
   - BC / regression training.
   - Online MuJoCo evaluation.
   - Numeric gate before demo.
   - Final report and handoff.

2. **Phase-gated architecture**
   - The project learned that monolithic live-observation BC is unstable during early grasp/lift.
   - Stage3 should keep early approach/grasp conservative and phase-gated.

3. **Failure taxonomy**
   - Early push/roll.
   - Transport drop.
   - Release contact remaining.
   - Target miss.
   - Closed-loop drift.

   Stage3 can reuse this pattern for:

   - crush risk
   - slip during lift
   - unstable hold
   - bad approach due to vision error
   - failed contact acquisition

4. **Target generalization lesson**
   - v0.7.3 fixed targets passed, but local sweep was partial.
   - Stage3 should not trust fixed-case success; it must use noisy pose and holdout eval from the start.

5. **Sensor task context**
   - Pick-place showed exactly where tactile/slip matters:
     - secure grasp check before lift
     - slip monitoring during transport/hold
     - contact-cleared check during release

   Stage3 should formalize these as synthetic tactile labels first.

## Stage3 Proposed Milestones

## Current Stage3.2c-3.5 Status

Updated: 2026-06-04

The active Stage3 line now uses this narrower implementation split:

```text
Stage3.2c: noisy MuJoCo virtual-camera perception gate
Stage3.3:  virtual-camera observation integration into the task API
Stage3.4:  MuJoCo contact-derived tactile/slip sensor
Stage3.5:  sensor-aware gentle grasp/lift/hold expert
```

Current result:

- Stage3.2c noisy virtual-camera gate: `PASS`
- Stage3.3 observation integration gate: `PASS`
- Stage3.4 tactile/slip sensor gate: `PASS`
- Stage3.5 10-trial sensor-aware expert gate: `PASS`

The current Stage3.5 expert is still scripted/IK-guided, not a learned policy.
It uses the virtual camera for pre-contact egg localization and contact-derived
tactile/slip checks for contact, lift, and hold. It does not claim real-camera,
real tactile, motor, or hardware integration.

Current learning-track entry:

```text
models/arm_hand_stage1_export/docs/stage3_learning_track_v0.md
```

## Stage3 Visual QA And Perception Convention

Future Stage3 demos should not rely only on the two named MuJoCo cameras. Those
views are useful seed views, but they are not enough to inspect occlusion,
contact, fingertip alignment, or image-derived hand-object relative pose.

Visual QA should save a phase-aware multi-view contact sheet:

- `stage3_egg_overview` for whole-task motion
- `stage3_egg_closeup` for object/contact detail
- top-down view for object-to-palm alignment
- side/profile view for approach height and lift/hold clearance
- perception-camera debug view with RGB/depth/mask/pose overlay

The perception camera set is separate from demo cameras. Perception outputs must
export camera intrinsics/extrinsics, RGB/depth/segmentation, object pose in
camera/world frame, and object pose relative to palm/fingertips. Demo renders
are visual QA only; they do not replace numeric task success checks.

Current camera rig record:

```text
models/arm_hand_stage1_export/docs/stage3_camera_rig_v0_report.md
```

Current perception literature record:

```text
models/arm_hand_stage1_export/docs/stage3_vision_perception_literature_v0.md
```

### Stage3.0: Task Contract

Create an egg-like grasp/lift/hold task contract:

- object geometry and material assumptions
- observation schema
- action schema
- success/failure metrics
- crush/slip thresholds
- replay QA requirements

Gate:

- task contract and scripted smoke demo exist

Start from:

```text
models/arm_hand_stage1_export/docs/stage3_task_contract_starter_v0.md
```

### Stage3.1: Sensor Requirements

Define the sensor requirements before implementing sensor outputs:

- task-to-sensor coverage
- phase-to-sensor coverage
- policy-visible fields vs ground-truth eval fields
- future Stage4 hardware mapping
- sensor-specific acceptance gates

Gate:

- every success/failure condition has a policy-visible sensor path
- every success/failure condition has a ground-truth evaluation path
- policy input boundary excludes perfect object pose and raw contact dumps
- future hardware mapping exists without claiming hardware integration

Current starter:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_requirements_v0.md
```

### Stage3.2: Sensor Abstractions

Add simulated sensor outputs:

- noisy visual object pose
- synthetic contact state
- synthetic slip score
- crush-risk proxy

Gate:

- sensor fields are logged in dataset rows
- noise parameters are configurable
- fixed seeds reproduce the same sensor sequence during replay QA

Current validation artifact:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_abstraction_v0_report.md
```

### Stage3.2b: Perception Geometry

Convert rendered images into the pose fields required by the sensor abstraction:

- render RGB, depth, segmentation, and camera calibration from MuJoCo
- unproject object-mask depth pixels into a camera-frame point cloud
- estimate object pose in camera and world frames
- use qpos plus forward kinematics for palm/fingertip world poses
- compute object pose and object-to-hand vectors in palm/fingertip frames
- evaluate image-derived estimates against MuJoCo ground truth

Gate:

- image-derived object position error is below threshold on fixed poses
- object-to-palm and object-to-fingertip vector errors are below threshold
- confidence/visibility drops under occlusion or too-small masks
- same seed/step produces replay-safe perception output
- policy-visible fields do not use MuJoCo ground truth directly

Current literature artifact:

```text
models/arm_hand_stage1_export/docs/stage3_vision_perception_literature_v0.md
```

Current geometry validation artifact:

```text
models/arm_hand_stage1_export/docs/stage3_perception_geometry_v0.md
```

Current hand-relative integration artifact:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_hand_relative_perception_v0.md
```

Current visual-guided grasp sweep artifact:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_visual_guided_grasp_sweep_v0.md
```

Current dynamic occlusion / last-good tracking artifact:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_dynamic_occlusion_perception_v0.md
```

Current Stage3.2b closeout:

```text
models/arm_hand_stage1_export/docs/stage3_2b_perception_geometry_closeout_v0.md
```

### Stage3.2c: Noisy Virtual-Camera Perception

Stress the MuJoCo virtual-camera path before trusting it inside the manipulation
loop:

- synthetic mask dropout
- synthetic occluders
- false-positive blobs
- depth noise
- calibration bias
- last-good freeze when the confidence/mask gate fails

Gate:

- no false confident bad estimate under noisy masks
- unsafe estimates are frozen instead of accepted
- accepted updates stay within the functional pose-error gate

Current result:

```text
PASS
```

Current artifact:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_noisy_virtual_camera_perception_v0.md
```

### Stage3.3: Virtual-Camera Observation Integration

Wire external virtual-camera estimates into the Stage3 task API so policy-visible
observations can come from the sensor path instead of perfect MuJoCo object
state:

- `object_pose_xyz_est`
- `object_axis_est`
- `object_shape_params_est`
- `goal_pose_xyz_est`
- `object_to_goal_est`
- `confidence`
- `occlusion`
- `latency_steps`
- `noise_std`
- virtual-camera status/debug fields

Gate:

- replay-safe ground-truth abstraction path still works
- virtual-camera override path exposes the same policy-visible contract
- MuJoCo truth remains evaluation/debug only

Current result:

```text
PASS
```

Current artifact:

```text
models/arm_hand_stage1_export/docs/stage3_virtual_camera_observation_integration_v0.md
```

### Stage3.4: Contact-Derived Tactile/Slip Sensor

Convert MuJoCo contacts into the tactile/slip abstraction needed after visual
occlusion:

- contact present
- contact regions
- contact persistence
- normal contact proxy
- slip score
- grip stability
- crush risk
- penetration

Gate:

- sensor emits valid fields before/after contact
- stable grip is detected before lift
- lift and hold remain stable without excessive crush or penetration
- early contact and transient lift slip are surfaced as risk flags, not hidden

Current result:

```text
PASS
```

Current artifact:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_slip_sensor_v0_report.md
```

Diagnostic slow-lift probe:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_slip_sensor_slow_lift_probe.md
```

### Stage3.5: Sensor-Aware Gentle Expert

Create a conservative scripted/IK-guided expert:

- approach
- gentle close
- contact settle
- lift
- hold
- release/abort

Gate:

- virtual camera acquires the initial egg pose
- IK approach stays within the functional hit gate
- tactile contact is acquired
- stable grip exists before lift
- lift height is at least `0.05 m`
- hold duration is at least `3 s`
- hold stable fraction is at least `0.80`
- hold slip, crush risk, and penetration stay below thresholds
- no floor contact remains after hold

Current result:

```text
PASS
```

Current artifact:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_aware_gentle_grasp_expert_v0_report.md
```

Interactive visualization:

```text
models/arm_hand_stage1_export/demo_stage3_sensor_fusion_viewer.py
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_viewer_demo_v0.md
```

Important finding:

- 10 / 10 fixed trial groups passed.
- The current scripted expert still has early approach contact and transient
  non-hold slip risk flags in all trials.
- Hold itself is stable, but the next controller refinement should make the
  approach cleaner and reduce lift-transition slip.

### After Stage3.5: Learned Policy, Robustness, And Recovery

The next main work after this closeout should not jump to hardware. It should
build on the Stage3.5 expert:

- keep early approach/grasp conservative
- train a phase-gated policy or residual around the expert
- add pose, friction, mass, contact, latency, and action-noise randomization
- add slip response, retry, loosen/re-close, release, or abort logic

Current dataset/replay foundation:

```text
models/arm_hand_stage1_export/data/stage3_sensor_fusion_expert_dataset_v0.npz
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_expert_dataset_v0_report.md
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_expert_dataset_v0_replay_report.md
```

Gates:

- fixed pose eval passes
- noisy pose eval passes
- no-crush and no-slip gates pass

### Stage3.6: Stage4 Sensor Handoff

Prepare the hardware-interface handoff:

- map Stage3 fields to real sensor candidates
- record sampling rate, latency, precision, and mounting requirements
- separate required sensors from optional research sensors
- identify calibration and safety risks

Gate:

- Stage4 hardware requirements are traceable to Stage3 task failures
- no Stage3 result claims real sensor integration

## Stage4 Definition

Stage4 is the hardware-interface stage:

- real motor command interface
- sensor data interface
- camera calibration
- tactile/ultrasound integration when available
- hardware-safe state machine
- small staged real-hand tests

Stage4 should not be started as the main line until Stage3 has produced a stable sensor-aware MuJoCo manipulation baseline.

## Non-Goals For Stage3

- Do not claim real tactile or ultrasound integration.
- Do not require hardware to run Stage3.
- Do not start active ultrasound / FPGA / B-mode work in the main hand runtime.
- Do not deploy an unconstrained neural policy to hardware.
- Do not abandon Stage2.5 target-generalization lessons.

## One-Sentence Memory

Stage3 is the MuJoCo stage for sensor-aware, gentle, robust manipulation: use simulated vision and tactile/slip abstractions to prepare for fragile real-object grasping, while Stage4 is reserved for hardware interfaces.
