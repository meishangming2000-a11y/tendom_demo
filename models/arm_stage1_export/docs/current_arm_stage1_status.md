# Current Arm Stage1 Status

## 1. Completed

- SolidWorks export package was audited and reduced to the frozen arm chain:
  - `base_link -> link_1 -> link_2 -> link_3 -> ee_mount`
- Active joints are frozen as:
  - `j1`
  - `j2`
  - `j3`
  - `j4`
- `ee_tool_frame` has been added as a fixed child frame under `ee_mount`
- Source URDF package remains available at:
  - `D:\tendon_project\hardwares\arm_stage1_export`
- MuJoCo working copy now has a loadable model and scene at:
  - `D:\tendon_project\simulations\models\arm_stage1_export\robot.xml`
  - `D:\tendon_project\simulations\models\arm_stage1_export\scene.xml`
- MuJoCo visualization is available from:
  - `D:\tendon_project\simulations\models\arm_stage1_export\view_model.py`

## 2. Frozen Structure

- Main chain:
  - `base_link -> link_1 -> link_2 -> link_3 -> ee_mount`
- Active joints:
  - `j1 / j2 / j3 / j4`
- End-effector reference:
  - `ee_tool_frame` is a fixed child frame of `ee_mount`
- Explicitly not used:
  - `j5`
  - `link_4`
  - `candidate_link_4`
- `axis_ee_mount` is flange/reference geometry only and must not be treated as a joint axis

## 3. Directory Roles

- Source export package:
  - `D:\tendon_project\hardwares\arm_stage1_export`
  - Role: keep the SolidWorks-to-URDF export result, meshes, ROS package files, and export audit history
  - Source entry file:
    - `D:\tendon_project\hardwares\arm_stage1_export\urdf\arm_stage1_export.urdf`
- MuJoCo working copy:
  - `D:\tendon_project\simulations\models\arm_stage1_export`
  - Role: hold the MuJoCo-ready copy, current runtime scene, and local visualization utilities

## 4. Canonical Entry Points

- Current canonical MuJoCo working directory:
  - `D:\tendon_project\simulations\models\arm_stage1_export`
- Current canonical model:
  - `D:\tendon_project\simulations\models\arm_stage1_export\robot.xml`
- Current canonical scene:
  - `D:\tendon_project\simulations\models\arm_stage1_export\scene.xml`
- Recommended directory for continued development:
  - `D:\tendon_project\simulations\models\arm_stage1_export`
- Minimal control entry kept in the root directory:
  - `D:\tendon_project\simulations\models\arm_stage1_export\control_smoketest.py`

Reference bridge files that should not be confused with the canonical runtime scene:

- `D:\tendon_project\simulations\models\arm_stage1_export\robot.urdf`
- `D:\tendon_project\simulations\models\arm_stage1_export\build_from_urdf.py`

## 5. Not Yet Established

- Final collision model for MuJoCo
- Refined inertia and dynamics validation against hardware intent
- Committed actuator architecture for long-term simulation use
- Tendon routing and tendon-driven transmission
- Controller stack beyond basic visualization and inspection utilities

## 6. Next Reasonable Directions

1. Minimal joint control
2. Joint limit and damping refinement
3. End-effector hand attachment
