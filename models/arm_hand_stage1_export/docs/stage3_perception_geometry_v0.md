# Stage3 Perception Geometry V0

Generated: 2026-06-04

## Scope

This is the first Stage3.2b perception-geometry experiment. It tests whether an
external sensor tool can estimate the egg position from MuJoCo-rendered depth
and segmentation.

Stage3 remains MuJoCo-only. MuJoCo ground truth is used only for evaluation, not
as the sensor output.

## Tool Folder

```text
models/arm_hand_stage1_export/external_sensors/
```

Current files:

- `mujoco_egg_pose_sensor.py`
- `run_stage3_egg_pose_sensor_experiment.py`
- `video_hand_shape_tool_index.md`

## Experiment Design

For each fixed egg pose:

1. set the egg freejoint to a known position
2. render RGB, depth, and segmentation from the candidate camera
3. isolate `egg_geom` with the MuJoCo segmentation image
4. unproject masked depth pixels into a world-frame point cloud
5. fit a known upright ellipsoid center
6. compare the estimated center against MuJoCo body `xpos`

Acceptance:

- max center error <= `0.002 m`
- no failed samples for the designated perception camera
- debug images show the mask covers the egg

## Result

Designated perception camera:

```text
stage3_egg_closeup
```

Result:

```text
PASS
```

Summary:

- samples: `11`
- mean position error: `0.00005723 m`
- max position error: `0.00005858 m`
- RMS position error: `0.00005724 m`
- minimum mask pixels: `12946`

Primary report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_egg_pose_sensor_accuracy_v0.md
```

Machine-readable metadata:

```text
models/arm_hand_stage1_export/external_sensors/metadata/stage3_egg_pose_sensor_accuracy_v0.json
```

Visual checks:

```text
models/arm_hand_stage1_export/external_sensors/visual_checks/stage3_egg_pose_sensor_accuracy_v0/
```

## Camera Probe Finding

The two existing Stage3 demo cameras are not both valid perception cameras.

`stage3_egg_closeup` can identify the egg mask and recover the egg center with
sub-millimeter error in this fixed-pose test.

`stage3_egg_overview` produced zero egg mask pixels in the camera probe. The
overview image is useful for human visual QA, but it should not be used as the
current perception camera.

Camera probe report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_egg_pose_sensor_camera_probe_v0.md
```

## Interpretation

This validates the first narrow piece of Stage3.2b:

```text
rendered RGB-D/segmentation -> egg center position
```

It does not yet validate:

- occlusion during grasp
- moving-object tracking
- real camera images
- FoundationPose or MegaPose integration

The next Stage3.2b step is:

```text
egg center estimate + qpos/FK palm/fingertip poses -> hand-object relative vectors
```

## Hand-Relative Integration Test

Follow-up test:

```text
models/arm_hand_stage1_export/external_sensors/run_stage3_hand_relative_perception_test.py
```

This compares:

```text
image-derived egg position + hand qpos/FK
vs
MuJoCo egg truth + same hand qpos/FK
```

Hand anchors:

- palm body: `palm_link`
- fingertip sites: `index_tip_site`, `middle_tip_site`, `ring_tip_site`,
  `little_tip_site`, `thumb_tip_site`

Result:

```text
PASS
```

Summary:

- hand poses: `open_default`, `preshape_hand`, `close_preview_hand`
- samples: `15`
- max egg position error: `0.00005795 m`
- max object-in-palm-frame error: `0.00005795 m`
- max fingertip vector error: `0.00005795 m`
- pass threshold: `0.002 m`

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_hand_relative_perception_v0.md
```

Metadata:

```text
models/arm_hand_stage1_export/external_sensors/metadata/stage3_hand_relative_perception_v0.json
```

Visual checks:

```text
models/arm_hand_stage1_export/external_sensors/visual_checks/stage3_hand_relative_perception_v0/
```

Current interpretation:

```text
rendered RGB-D/segmentation -> egg center estimate -> hand-relative pose
```

is validated for fixed egg poses and static hand-shape states.

Still not validated:

- occlusion during actual approach/contact phases
- moving-object tracking
- real camera images
- FoundationPose or MegaPose integration

## Visual-Guided Grasp Sweep

Follow-up test:

```text
models/arm_hand_stage1_export/external_sensors/run_stage3_visual_guided_grasp_sweep.py
```

This test runs paired episodes:

```text
visual: image-derived egg position -> arm IK -> grasp/lift
oracle: MuJoCo egg truth -> same arm IK -> grasp/lift
```

Result:

```text
PASS_FUNCTIONAL
```

Summary:

- trial groups: `10`
- paired episodes: `20`
- visual-guided grasp/lift success: `10 / 10`
- oracle grasp/lift success: `10 / 10`
- visual functional hits within `15 mm`: `10 / 10`
- visual precision hits within `8 mm`: `3 / 10`
- visual mean final lift: `0.100897 m`
- oracle mean final lift: `0.098912 m`
- visual max approach true error: `0.012652 m`
- oracle max approach true error: `0.012781 m`
- visual failure reasons: `{}`
- oracle failure reasons: `{}`

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_visual_guided_grasp_sweep_v0.md
```

Metadata:

```text
models/arm_hand_stage1_export/external_sensors/metadata/stage3_visual_guided_grasp_sweep_v0.json
```

Visual checks:

```text
models/arm_hand_stage1_export/external_sensors/visual_checks/stage3_visual_guided_grasp_sweep_v0/
```

Interpretation:

- Under clean MuJoCo segmentation and a fixed perception camera, the image-based
  egg position is accurate enough to guide arm IK, hand closure, and lift.
- Visual and oracle outcomes match across all 10 trial groups, so perception is
  not the limiting factor in this sweep.
- The strict `8 mm` precision-hit rate is only `3 / 10`; this is the next
  alignment tuning target if the project needs tighter pre-contact centering.
- The next risk remains dynamic occlusion and replacing exact MuJoCo
  segmentation with a noisier mask provider.

## Dynamic Occlusion Perception Test

Follow-up test:

```text
models/arm_hand_stage1_export/external_sensors/run_stage3_dynamic_occlusion_perception_test.py
```

This test re-renders the perception camera at each phase boundary:

```text
initial_acquire -> pre_approach -> approach -> preshape
-> close_fingers -> close_thumb -> close_hold -> lift -> hold_lift
```

Runtime decision:

```text
tracking_confidence = raw_confidence * relative_mask_retention
```

If the confidence/mask gate fails, the tracker freezes the last-good egg pose
instead of accepting the new estimate. MuJoCo truth is used only for evaluation.

Result:

```text
PASS_DYNAMIC_CONTROL_WINDOW
```

Summary:

- trial groups: `10`
- visual dynamic grasp/lift success: `10 / 10`
- oracle grasp/lift success: `10 / 10`
- perception samples: `90`
- accepted pose updates: `51`
- frozen last-good updates: `39`
- low-visibility samples: `25`
- false confident bad estimates: `0`
- max accepted pose error: `0.008542 m`
- max last-good error before lift/control handoff: `0.020267 m`

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_dynamic_occlusion_perception_v0.md
```

Metadata:

```text
models/arm_hand_stage1_export/external_sensors/metadata/stage3_dynamic_occlusion_perception_v0.json
```

Visual checks:

```text
models/arm_hand_stage1_export/external_sensors/visual_checks/stage3_dynamic_occlusion_perception_v0/
```

Interpretation:

- During approach and preshape the perception estimate is still safe to update.
- During close/lift/hold the camera path becomes less reliable, so the Stage3
  controller should freeze vision updates and hand off more authority to
  contact/tactile/slip abstractions.
- This still uses clean MuJoCo segmentation. The next perception stress test is
  synthetic noisy masks or deliberate occluders, not Stage4 real cameras yet.

## Stage3.2c Noisy Virtual Camera Perception Test

Follow-up test:

```text
models/arm_hand_stage1_export/external_sensors/run_stage3_noisy_virtual_camera_perception_test.py
```

This test keeps perception inside MuJoCo, but deliberately corrupts the virtual
camera output before the pose estimator sees it:

```text
clean_reference
mask_dropout_30
mask_dropout_55
synthetic_occluder_45
depth_noise_5mm
false_positive_blob
combined_hard
calibration_bias_12mm
```

Runtime decision:

```text
accept clean enough updates; otherwise freeze last-good pose
```

Result:

```text
PASS
```

Summary:

- trial groups: `10`
- scenarios per group: `8`
- total samples: `80`
- accepted pose updates: `40`
- frozen unsafe updates: `40`
- false confident bad estimates: `0`
- max accepted pose error: `0.013718 m`
- max sensor-ok error: `49.915 m` in deliberately frozen hard-corruption cases

Report:

```text
models/arm_hand_stage1_export/external_sensors/reports/stage3_noisy_virtual_camera_perception_v0.md
```

Metadata:

```text
models/arm_hand_stage1_export/external_sensors/metadata/stage3_noisy_virtual_camera_perception_v0.json
```

Visual checks:

```text
models/arm_hand_stage1_export/external_sensors/visual_checks/stage3_noisy_virtual_camera_perception_v0/
```

Interpretation:

- The current virtual-camera tracker should not blindly accept every rendered
  estimate.
- The acceptance gate correctly rejects or freezes severe synthetic corruption.
- This is still not a real-camera test. It validates the Stage3.2c noisy
  MuJoCo virtual-camera path before any Stage4 camera work.
