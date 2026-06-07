# Stage3 External Sensor Tools

This folder holds sensor/perception tools that sit outside the core MuJoCo task
API. Stage3 still stays MuJoCo-only; these tools emulate or test external
perception streams before Stage4 real hardware integration.

## Current Tools

- `mujoco_egg_pose_sensor.py`
  - Estimates the Stage3 egg center from MuJoCo RGB/depth/segmentation.
  - Uses the object mask plus a known upright ellipsoid shape fit.
  - Does not use MuJoCo ground truth as the sensor output.

- `run_stage3_egg_pose_sensor_experiment.py`
  - Runs fixed-position accuracy tests.
  - Compares image-derived egg position against MuJoCo ground truth for
    evaluation only.
  - Writes reports, metadata, and visual debug images under this folder.

- `mujoco_hand_relative_pose.py`
  - Uses mechanical-hand FK anchors (`palm_link` and fingertip sites) to compute
    hand-relative object pose from an object position.

- `run_stage3_hand_relative_perception_test.py`
  - Compares the perception path against the direct ground-truth path:

```text
image-derived egg position + hand FK
vs
MuJoCo egg truth + same hand FK
```

- `run_stage3_visual_guided_grasp_sweep.py`
  - Runs paired visual/oracle grasp-lift attempts across multiple egg positions
    and small grasp-parameter variations.
  - Checks whether image-derived egg pose can guide arm IK, hand closure, and
    lift in MuJoCo.

- `run_stage3_dynamic_occlusion_perception_test.py`
  - Re-renders the perception camera at each approach/close/lift phase boundary.
  - Applies a last-good tracker using `raw_confidence * relative_mask_retention`.
  - Freezes vision pose updates when the mask/confidence gate drops, then
    compares the result against MuJoCo truth for evaluation only.

- `run_stage3_noisy_virtual_camera_perception_test.py`
  - Corrupts the MuJoCo virtual-camera mask/depth/calibration path with mask
    dropout, synthetic occluders, false-positive blobs, depth noise, and
    calibration bias.
  - Checks that the tracker accepts clean enough estimates, freezes unsafe
    updates, and produces no false confident bad estimates.

- `mujoco_tactile_slip_sensor.py`
  - Converts MuJoCo egg/hand contacts into policy-visible tactile fields:
    contact regions, persistence, normal contact proxy, slip score, grip
    stability, crush risk, and penetration.
  - Uses object motion relative to `palm_link` so slip during lift is not
    confused with normal world-frame lifting motion.

- `video_hand_shape_tool_index.md`
  - Index for the existing video-to-hand-shape/open-close diagnostic tools.
  - The older scripts remain at their original paths so historical reports and
    imports do not break.

## Boundary

Stage3 external sensors are simulation-side perception tools:

```text
MuJoCo render / video feature input -> estimated sensor fields -> Stage3 policy/eval
```

Real cameras, electronics, live calibration rigs, and hardware runtime
interfaces remain Stage4 work.

## Operating Pattern

Use the Stage2.5-style evidence loop:

1. define the gate before running
2. run a narrow probe first
3. compare visual/perception output against an oracle path
4. save report, metadata, and a compact visual check
5. write the lesson into the Stage3 handoff docs when it changes future work

For visual-guided grasp, keep both hit metrics:

- `8 mm` precision hit for alignment quality
- `15 mm` functional hit for grasp/lift pass-fail

For dynamic perception during closure/lift:

- accept visual pose updates during `initial_acquire`, `pre_approach`,
  `approach`, and `preshape` when confidence/mask gates pass
- freeze last-good pose during low-confidence closure/lift phases
- treat final camera-only last-good error after lift as diagnostic; once the
  egg is in hand, Stage3 should increasingly use contact/tactile/slip
  abstractions

For the current Stage3 mainline, real cameras are out of scope. Stage3 uses
MuJoCo virtual cameras and contact-derived tactile/slip signals only; real
camera calibration and hardware interfaces belong to Stage4.
