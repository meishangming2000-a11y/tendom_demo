# Stage3.2c To Stage3.5 Sensor-Aware Expert Closeout V0

Generated: 2026-06-04

## Status

Stage3.2c through Stage3.5 are complete for the current MuJoCo-only gate.

This does not claim real-camera, real tactile, motor, or hardware integration.
Stage3 remains simulation-side; Stage4 owns real hardware interfaces.

## Goal In Plain Terms

The goal of this block was to stop giving the hand perfect object state and
instead test a realistic Stage3 loop:

```text
MuJoCo virtual camera estimates the egg pose
-> the hand uses that estimate to approach
-> MuJoCo contact state becomes tactile/slip feedback
-> the hand gently closes, lifts, and holds the egg
-> ground truth is used only to score the result
```

## What Was Completed

### Stage3.2c: Noisy Virtual-Camera Perception

Script:

```text
models/arm_hand_stage1_export/external_sensors/run_stage3_noisy_virtual_camera_perception_test.py
```

Result:

- status: `PASS`
- total samples: `80`
- accepted pose updates: `40`
- frozen unsafe updates: `40`
- false confident bad estimates: `0`
- max accepted pose error: `0.013718 m`

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_noisy_virtual_camera_perception_v0.md
```

### Stage3.3: Virtual-Camera Observation Integration

Files:

```text
models/arm_hand_stage1_export/stage3_sensor_aware_gentle_grasp_hold_task_api.py
models/arm_hand_stage1_export/validate_stage3_virtual_camera_observation_integration.py
```

Result:

- status: `PASS`
- virtual-camera estimates can now be passed into the task observation
- policy-visible fields keep the Stage3 sensor abstraction boundary
- MuJoCo truth remains for evaluation/debug, not policy input

Report:

```text
models/arm_hand_stage1_export/docs/stage3_virtual_camera_observation_integration_v0.md
```

### Stage3.4: Contact-Derived Tactile/Slip Sensor

Files:

```text
models/arm_hand_stage1_export/external_sensors/mujoco_tactile_slip_sensor.py
models/arm_hand_stage1_export/validate_stage3_tactile_slip_sensor.py
```

Result:

- status: `PASS`
- contact regions, contact persistence, slip score, grip stability, crush risk,
  and penetration are generated from MuJoCo contact state
- slip uses egg motion relative to `palm_link`, so normal lifting is not
  mislabeled as world-frame slip

Report:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_slip_sensor_v0_report.md
```

Diagnostic slow-lift probe:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_slip_sensor_slow_lift_probe.md
```

### Stage3.5: Sensor-Aware Gentle Grasp Expert

Script:

```text
models/arm_hand_stage1_export/run_stage3_sensor_aware_gentle_grasp_expert.py
```

Result:

- status: `PASS`
- trial groups: `10`
- successes: `10 / 10`
- mean final lift: `0.103056 m`
- mean hold stable fraction: `1.000`
- max hold slip score: `0.262`
- max crush risk: `0.113`
- max penetration: `0.002259 m`
- failure reasons: `{}`

Report:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_aware_gentle_grasp_expert_v0_report.md
```

Metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_sensor_aware_gentle_grasp_expert_v0.json
```

Visual checks:

```text
models/arm_hand_stage1_export/docs/visual_checks_stage3_sensor_aware_gentle_grasp_expert_v0/
```

Interactive sensor-fusion viewer:

```text
models/arm_hand_stage1_export/demo_stage3_sensor_fusion_viewer.py
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_viewer_demo_v0.md
```

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py
```

## What We Learned

- `stage3_egg_closeup` is the current perception camera.
- `stage3_egg_overview` is visual QA only until it passes a mask/visibility
  probe.
- Camera-only tracking should update during acquire/approach/preshape, then
  freeze or hand off once fingers occlude the egg.
- The noisy virtual-camera gate must reject bad masks instead of pretending
  every estimate is usable.
- The tactile/slip sensor is useful after contact because it can monitor stable
  hold without relying on a visible egg mask.
- The current expert succeeds, but it is not a polished controller.

## Remaining Issues

The Stage3.5 expert passed but surfaced two control risks in every trial:

- `early_contact_in_approach`: the palm lightly contacts the egg near the end
  of the approach phase.
- `transient_nonhold_slip`: the lift transition can create a short slip spike.

These are not hidden failures because the egg still lifts, clears the floor,
holds for 3 seconds, and stays below crush/penetration thresholds. They should
be the first cleanup targets before training or broad robustness randomization.

## Recommended Next Step

Keep Stage3 in MuJoCo and refine the controller before hardware work:

1. reduce early approach contact by improving approach height/hand preshape
2. reduce lift-transition slip with slower lift, staged lift, or grip adjustment
3. add randomized pose/friction/mass/contact/latency tests
4. train a phase-gated residual or policy only after the scripted expert is a
   clean baseline
5. keep real cameras and real tactile hardware in Stage4

## Learning Track Update

The first simulation-learning dataset/replay foundation has been started:

```text
models/arm_hand_stage1_export/docs/stage3_learning_track_v0.md
models/arm_hand_stage1_export/data/stage3_sensor_fusion_expert_dataset_v0.npz
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_expert_dataset_v0_report.md
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_expert_dataset_v0_replay_report.md
```

Status:

- dataset collection: `10 / 10` expert episodes succeeded
- rows: `31000`
- replay QA: `PASS`
- max replay obs/object error: `0`

This makes the next model step possible: train a small BC or residual baseline
from sensor abstraction observations to expert actions, then evaluate it
closed-loop against the scripted expert.
