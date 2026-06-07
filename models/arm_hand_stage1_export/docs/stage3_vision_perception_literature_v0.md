# Stage3 Vision Perception Literature V0

Generated: 2026-06-04

## Question

For Stage3, we need visual perception that can support:

```text
camera image/depth/mask -> object pose -> hand-object relative pose -> approach/alignment control
```

The target is not just a nice demo render. The perception stack must eventually
estimate where the egg-like object is relative to the palm and fingertips.

Stage3 remains MuJoCo-only. Real cameras, electronics, calibration rigs, and
hardware integration remain Stage4.

## Stage3-Specific Requirement

The useful output is not only:

```text
vision.object_pose_xyz_est
```

We also need:

```text
vision.object_pose_camera_frame
vision.object_pose_world_frame
vision.object_pose_in_palm_frame
vision.object_to_palm_xyz_est
vision.object_to_fingertips_xyz_est
vision.visibility
vision.confidence
```

For the hand side, the mainline should use:

```text
proprio.qpos -> forward kinematics -> palm/fingertip world poses
```

Do not try to visually detect the robotic hand first. The hand is controlled and
its joint state is available; using FK is simpler, more accurate, and closer to
what a real robot would do with encoders.

## Main Finding

There are two different problems:

1. **Visual QA**
   - renders for humans to inspect whether a demo makes sense
   - needs many views and phase snapshots
   - does not feed the policy

2. **Perception**
   - camera/depth/mask/intrinsics/extrinsics used to compute object pose
   - feeds `vision.*` fields
   - must be replay-safe and numerically evaluated

The two named cameras currently created for Stage3 are useful only for visual QA.
They are not enough to define a perception pipeline by themselves.

## Candidate Project Review

| Project | What it does | Inputs | Direct reuse for us | Fit |
|---|---|---|---|---|
| MuJoCo renderer + OpenCV/Open3D geometry | Render RGB/depth/segmentation, unproject depth, compute object pose, optionally refine with point cloud registration | MuJoCo camera, depth, segmentation, known object geometry | Immediate Stage3.2b mainline | Best first step |
| FoundationPose | 6D pose estimation/tracking for novel objects; works with CAD model or reference images | RGB-D, object model or references, mask/initialization | Strong candidate once we export object mesh, RGB-D, camera intrinsics, mask | Best external 6D pose candidate |
| MegaPose | 6D pose for novel objects by render-and-compare | RGB, optional depth, intrinsics, object mesh, bounding box | Good baseline for known object mesh | Good external baseline |
| SAM 2 | Promptable image/video segmentation and tracking | image/video plus prompt | Useful mask provider for real/sim RGB, not a pose estimator | Segmentation helper only |
| Grounded-SAM | Text/object detection + SAM segmentation | text prompt + image | Useful for automatic masks, not pose | Segmentation helper only |
| BundleSDF | 6D tracking and reconstruction of unknown rigid objects from RGB-D video | RGB-D video, first-frame segmentation | Useful if no CAD/model; heavy for current stage | Optional research backup |
| OnePose / OnePose++ | CAD-free object pose from object scan / SfM-style model | RGB scan/query images | Less suitable for plain/low-texture egg-like object | Backup only |
| DOPE | RGB-only 6D pose of known objects | trained model for object | Requires training for our object; older ROS path | Not mainline |
| DenseFusion / PVN3D | RGB-D 6D pose networks | RGB-D, segmentation, trained models | Strong literature, but requires training/adaptation | Not first reuse |
| CosyPose | Consistent multi-view multi-object 6D pose | RGB, bboxes, object model | Multi-view idea is useful; code older | Reference |
| BOP toolkit | Standard 6D pose evaluation toolkit | predicted/GT poses, datasets | Useful for evaluation metrics/file format | Evaluation helper |
| MediaPipe Hands / DexYCB | Human hand landmarks / hand-object benchmarks | human hand images/datasets | Not directly useful for robotic hand pose; use FK instead | Reference only |

## Recommended Stage3 Route

### Route A: Immediate Mainline

Build Stage3.2b using MuJoCo + OpenCV/Open3D-style geometry:

1. Render from perception camera:
   - RGB
   - depth
   - segmentation/object mask
   - camera intrinsics/extrinsics

2. Estimate object pose:
   - mask pixels -> depth points
   - depth unprojection -> camera-frame point cloud
   - camera-frame -> world-frame transform
   - ellipsoid/mesh fit or centroid + axis estimate

3. Estimate hand-object relation:
   - qpos -> FK -> palm/fingertip world poses
   - object world pose -> palm frame
   - compute object-to-palm and object-to-fingertip vectors

4. Evaluate:
   - compare image-derived object pose to MuJoCo GT
   - compare relative pose to GT-derived relative pose
   - check failure under occlusion/low visibility

This should be built before the scripted gentle expert.

### Route B: Direct External Reuse

Try FoundationPose as the first external 6D pose baseline.

Why:

- it supports novel objects
- it can work with a CAD/object model or reference images
- it estimates and tracks 6D pose
- it is recent and officially released by NVIDIA

What we need to provide:

- RGB-D frames
- object mask or prompt/initialization
- object mesh for the egg-like object
- camera intrinsics
- transform from camera frame to MuJoCo world

Risks:

- CUDA/PyTorch3D/NVDiffRast setup can be heavy
- our current object is an ellipsoid MJCF geom, so we may need a simple mesh export
- success on a texture-poor egg-like object depends on depth/mask quality

### Route C: Lightweight External Baseline

Try MegaPose if FoundationPose setup is too heavy.

Why:

- it estimates 6D pose of novel objects
- it accepts object mesh, camera intrinsics, RGB image, optional depth, and 2D box
- it provides inference examples

Risks:

- older stack than FoundationPose
- may be less convenient than our geometry path for a simple ellipsoid

### Route D: Mask Provider Only

Use SAM 2 or Grounded-SAM only as a mask provider, not as the full pose system.

For MuJoCo Stage3, native segmentation should be preferred because it is exact
and replay-safe. SAM-style segmentation becomes useful when testing more
realistic rendered images or preparing Stage4.

## What Not To Do First

Do not start with:

- end-to-end image-to-action policy
- visual hand pose estimation of the robotic hand
- RGB-only 6D pose for a plain egg-like object
- training a custom DenseFusion/PVN3D/DOPE model before the geometry baseline
- treating visual QA cameras as perception cameras

## Open-Source Projects To Reuse

### FoundationPose

- Repo: https://github.com/NVlabs/FoundationPose
- Paper: https://arxiv.org/abs/2312.08344
- Use case: external 6D pose estimator/tracker for novel object
- Reuse level: high, after RGB-D/mask/mesh export

### MegaPose

- Repo: https://github.com/megapose6d/megapose6d
- Project: https://megapose6d.github.io/
- Paper: https://arxiv.org/abs/2212.06870
- Use case: external 6D pose baseline from RGB/RGB-D plus mesh and bounding box
- Reuse level: medium-high

### SAM 2

- Project: https://ai.meta.com/research/sam2/
- Repo: https://github.com/facebookresearch/sam2
- Paper: https://arxiv.org/abs/2408.00714
- Use case: promptable object segmentation/tracking
- Reuse level: medium as mask provider, not pose estimator

### Grounded-SAM

- Repo: https://github.com/IDEA-Research/Grounded-Segment-Anything
- Use case: text/object detection plus mask generation
- Reuse level: medium as automatic mask provider

### Open3D

- Project: https://www.open3d.org/
- ICP docs: https://www.open3d.org/docs/latest/tutorial/pipelines/icp_registration.html
- Use case: point cloud processing and pose refinement
- Reuse level: high for geometry baseline

### OpenCV ArUco / Calibration Utilities

- Docs: https://docs.opencv.org/3.4/d9/d6a/group__aruco.html
- Use case: camera calibration / marker pose sanity tests
- Reuse level: medium; more relevant for Stage4 or calibration validation

### BOP Toolkit

- Repo: https://github.com/thodan/bop_toolkit
- Benchmark paper: https://arxiv.org/abs/1808.08319
- Use case: 6D pose evaluation conventions
- Reuse level: medium for eval/reporting

### BundleSDF

- Repo: https://github.com/NVlabs/BundleSDF
- Paper: https://arxiv.org/abs/2303.14158
- Use case: unknown-object RGB-D tracking/reconstruction
- Reuse level: backup, heavy

### OnePose / OnePose++

- OnePose: https://zju3dv.github.io/onepose/
- OnePose++: https://zju3dv.github.io/onepose_plus_plus/
- Use case: CAD-free pose estimation after object scan
- Reuse level: backup only for Stage3, because egg-like objects are low-texture

## Proposed Revised Milestone

Add this stage before scripted expert:

```text
Stage3.2b: Perception Geometry
```

Deliverables:

- `stage3_perception_geometry_v0.md`
- perception camera set, separate from demo cameras
- RGB/depth/segmentation render script
- camera intrinsics/extrinsics export
- object mask/depth unprojection
- object pose estimate in camera/world frame
- palm/fingertip FK pose extraction
- object pose in palm frame
- relative pose QA report

Acceptance:

- fixed-pose image-derived object position error under threshold
- object-to-palm vector error under threshold
- object-to-fingertip vector error under threshold
- visibility/confidence drops under occlusion
- same seed/step perception output is replay-safe
- no policy field uses MuJoCo GT directly

## Decision

Use the geometry baseline first.

Then test FoundationPose as the first reusable external project once Stage3 can
export RGB-D, mask, object mesh, and camera calibration. MegaPose is the fallback
if FoundationPose setup is too heavy.
