# Video Hand Shape Tool Index

This folder now owns the external-sensor/tooling index, but the existing
video-to-hand-shape diagnostic scripts are intentionally kept in their original
locations to avoid breaking previous reports.

## Existing Tools

- Arm+hand v2 comparison wrapper:

```text
models/arm_hand_stage1_export/run_arm_hand_stage1_v2_shadow_video_comparison.py
```

- Hand-only Shadow/export4 comparison source:

```text
models/hand_stage1_export/scripts/run_export4_shadow_video_comparison.py
```

## What The Tool Does

The diagnostic maps recorded open/close video features to both a Shadow Hand
reference model and the current arm+hand export4 assembly. It is useful as a
hand-shape/open-close regression check.

## What It Does Not Prove

- It does not estimate the Stage3 egg pose.
- It does not prove stable object grasp.
- It does not represent Stage4 real camera integration.

For Stage3 egg-relative manipulation, use `mujoco_egg_pose_sensor.py` first.
