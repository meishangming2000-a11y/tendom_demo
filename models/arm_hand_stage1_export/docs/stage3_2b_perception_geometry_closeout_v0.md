# Stage3.2b Perception Geometry Closeout V0

Generated: 2026-06-04

## Status

Stage3.2b perception geometry is functionally validated under clean MuJoCo
segmentation, a fixed perception camera, and the first dynamic occlusion/control
window gate.

This does not claim real-camera or hardware integration. Stage3 remains
MuJoCo-only.

## Organizing Pattern Used

This closeout follows the Stage2.5 evidence pattern:

1. define the gate before broad testing
2. probe narrowly before running a wider sweep
3. compare against an oracle/control baseline
4. record report, metadata, visual checks, and handoff
5. write repair/lesson memory immediately if it changes future behavior

Records that informed this pattern:

```text
models/arm_hand_stage1_export/docs/stage2_5_pick_place_training_workflow_after_gate2.md
models/arm_hand_stage1_export/docs/arm_hand_stage1_training_run_standard.md
models/arm_hand_stage1_export/docs/stage2_5_gate5_stage3_readiness.md
```

## What Was Built

Tool folder:

```text
models/arm_hand_stage1_export/external_sensors/
```

Core tools:

- `mujoco_egg_pose_sensor.py`
- `mujoco_hand_relative_pose.py`
- `run_stage3_egg_pose_sensor_experiment.py`
- `run_stage3_hand_relative_perception_test.py`
- `run_stage3_visual_guided_grasp_sweep.py`
- `run_stage3_dynamic_occlusion_perception_test.py`
- `video_hand_shape_tool_index.md`

## Evidence Summary

### 1. Egg Position Sensor

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_egg_pose_sensor_accuracy_v0.md
```

Result:

- camera: `stage3_egg_closeup`
- samples: `11`
- status: `PASS`
- mean position error: `0.00005723 m`
- max position error: `0.00005858 m`

Camera probe finding:

- `stage3_egg_closeup` works as the first perception camera
- `stage3_egg_overview` is visual QA only for now; it produced zero egg mask
  pixels in the probe

### 2. Hand-Relative Integration

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_hand_relative_perception_v0.md
```

Result:

- samples: `15`
- hand states: `open_default`, `preshape_hand`, `close_preview_hand`
- status: `PASS`
- max egg position error: `0.00005795 m`
- max object-in-palm-frame error: `0.00005795 m`
- max fingertip vector error: `0.00005795 m`

### 3. Visual-Guided Grasp Sweep

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_visual_guided_grasp_sweep_v0.md
```

Result:

- trial groups: `10`
- paired episodes: `20`
- visual-guided success: `10 / 10`
- oracle success: `10 / 10`
- visual functional hits within `15 mm`: `10 / 10`
- visual precision hits within `8 mm`: `3 / 10`
- visual mean final lift: `0.100897 m`
- oracle mean final lift: `0.098912 m`
- visual max approach true error: `0.012652 m`
- oracle max approach true error: `0.012781 m`
- visual failure reasons: `{}`
- oracle failure reasons: `{}`

### 4. Dynamic Occlusion / Last-Good Tracking

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_dynamic_occlusion_perception_v0.md
```

Result:

- trial groups: `10`
- visual dynamic success: `10 / 10`
- oracle success: `10 / 10`
- perception samples: `90`
- accepted pose updates: `51`
- frozen last-good updates: `39`
- low-visibility samples: `25`
- false confident bad estimates: `0`
- max accepted pose error: `0.008542 m`
- max last-good error before lift/control handoff: `0.020267 m`

## Lessons Captured

### Separate Visual QA From Perception

Demo cameras are not automatically perception cameras. The overview camera was
useful for human viewing but failed the mask probe. Perception cameras must pass
numeric visibility/mask gates.

### Always Use An Oracle Pair

The visual-guided sweep only became meaningful because every visual episode had
a matched oracle episode. If both fail, perception is probably not the limiting
factor. If visual fails while oracle passes, investigate perception, visibility,
or calibration first.

### Avoid Broad Sweeps Before A Probe

The first sweep exposed two bookkeeping/control issues:

- the base egg position was read before `mj_forward`, which made IK target the
  wrong location
- the initial success criterion used an `8 mm` precision hit as a functional
  grasp gate

Both were repaired before trusting the final sweep.

### Use Two Hit Thresholds

For this egg object, a single strict hit threshold hides useful behavior.

- `8 mm` precision hit: useful for pre-contact alignment quality
- `15 mm` functional hit: useful for grasp/lift pass/fail

The current functional result is strong, but precision alignment still has room
to improve.

### Freeze Vision Updates During Closure

The dynamic test shows a useful phase split:

- `initial_acquire`, `pre_approach`, `approach`, and `preshape` are good visual
  update phases
- `close_thumb`, `close_hold`, `lift`, and `hold_lift` often need last-good
  freezing or a handoff to contact/tactile/slip signals

Do not blindly keep updating camera pose estimates after the fingers occlude
the egg. Use a runtime confidence such as:

```text
tracking_confidence = raw_confidence * relative_mask_retention
```

and freeze updates when the confidence/mask gate drops.

## Current Gate Interpretation

Stage3.2b can proceed past the clean perception-geometry gate:

```text
RGB-D/segmentation -> egg center -> hand-relative pose -> visual-guided lift
-> dynamic occlusion-aware last-good tracking
```

under these assumptions:

- clean MuJoCo segmentation
- fixed perception camera: `stage3_egg_closeup`
- known upright egg ellipsoid model
- static acquisition before approach plus phase-boundary re-rendering
- last-good freeze during low-confidence closure/lift phases
- scripted/IK-guided grasp-lift control

## Next Gate

The next Stage3.2b gate should test noisier perception:

1. inject synthetic mask noise, missing depth, and false positives
2. add deliberate occluders or camera perturbations
3. compare clean segmentation against the noisy provider
4. keep the same oracle pairing and last-good tracking gate
5. decide when to retry, freeze, or abort before Stage4 camera work

Suggested acceptance:

- no false confident estimate under noisy masks
- clean/noisy visual-guided lift still matches oracle on the same cases
- last-good control-window error stays below the current `25 mm` gate
- failure reasons are split into perception, grasp/contact, and control

Post-closeout update:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_noisy_virtual_camera_perception_v0.md
```

Stage3.2c completed this noisy virtual-camera gate with `PASS`, `80` total
samples, `40` accepted updates, `40` frozen unsafe updates, and `0` false
confident bad estimates.

## Handoff

Start the next perception conversation from:

```text
models/arm_hand_stage1_export/docs/stage3_perception_geometry_v0.md
models/arm_hand_stage1_export/docs/stage3_2b_perception_geometry_closeout_v0.md
models/arm_hand_stage1_export/external_sensors/reports/stage3_visual_guided_grasp_sweep_v0.md
models/arm_hand_stage1_export/external_sensors/reports/stage3_dynamic_occlusion_perception_v0.md
```

Do not jump to FoundationPose, MegaPose, SAM, or real cameras until the noisy
mask / synthetic occluder gate is defined and probed in MuJoCo.

Stage3 remains MuJoCo-only. Real-camera probes and calibration belong to
Stage4, after the hardware/camera path exists.
