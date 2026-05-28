# Arm + Export4 Hand Mount Alignment Report

Generated: 2026-05-26

## Goal

Attach the current export4 hand candidate to the previous arm_stage1 MuJoCo model so the arm flange connects to the hand wrist/root region, avoiding the earlier Shadow+arm failure mode where the two models appeared to meet only at a single point.

## Inputs

- Arm source: `D:\tendon_project\simulations\models\arm_stage1_export\robot.xml`
- Hand source: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_palmar_ypos_collision_candidate.xml`

## Outputs

- Combined MJCF: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_palmar_ypos_candidate.xml`
- Combined scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_palmar_ypos_candidate.xml`
- Viewer: `D:\tendon_project\simulations\models\arm_hand_stage1_export\view_arm_hand_export4.py`
- Joint smoke: `D:\tendon_project\simulations\models\arm_hand_stage1_export\test_arm_hand_export4_joints.py`

## Attachment

- Parent body/frame: `ee_tool_frame`
- Child body: `hand_base_link`
- Local hand root pos: `[0, 0, 0]`
- Local hand root quat: `[1, 0, 0, 0]`

Measured in the combined model:

- `ee_tool_frame_site -> hand_base_link`: `0.000000 m`
- `ee_tool_frame body -> hand_base_link`: `0.000000 m`
- `hand_base_link -> wrist_middle_link`: `0.015000 m`
- `wrist_middle_link -> palm_link`: `0.020292 m`

## Visual Check

Rendered views:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_overview.png`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_side.png`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_top.png`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_wrist_closeup.png`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_flange_axis.png`

Conclusion: **PASS as first MuJoCo assembly candidate / PARTIAL as final mechanical flange calibration**.

The hand is now in the arm kinematic tree and visually attached at the flange/wrist region. It no longer looks like two separately rendered bodies connected by only one point. The wrist/base sits near the arm flange and the hand extends outward from the end effector.

Remaining TODO: final flange calibration may still need a small fixed transform adjustment if the desired physical interface is a specific flange face, bolt pattern, or wrist mounting plane. Do not change CAD/STL for this; first tune only the fixed `ee_tool_frame -> hand_base_link` transform in a new MJCF experiment.

## Joint Smoke

Report:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_export4_joint_smoke_report.md`

Result:

- Overall: **PASS**
- Model: `31 bodies / 26 joints / 26 actuators / 59 geoms / 6 sites / 29 meshes`
- Joint kinematic smoke: `26 PASS / 0 FAIL / 0 SKIPPED`
- Actuator stepping: `PASS`

## Current Recommendation

Use the CAD mount candidate for visual and adapter-level arm+hand smoke checks:

- `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_cad_mount_candidate.xml`
- `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`

## 2026-05-26 Flange Diagnosis Update

The identity attachment was not a good flange-face convention. Axis debugging showed:

- the visible bolt/flange plate is on the `ee_mount` local `+Y` side;
- `ee_tool_frame` is located at local `y=0.01956` inside `ee_mount`;
- the `ee_mount` mesh `+Y` boundary is about `y=0.0341`;
- the missing offset is therefore about `14.5 mm`;
- this maps almost exactly to `ee_tool_frame` local `+Z`.

The selected candidate sets:

- `hand_base_link pos="0 0 0.01455"` under `ee_tool_frame`
- `hand_base_link quat="1 0 0 0"`

This moves the hand root toward the visible flange face without changing CAD, STL, joint names, or the joint tree.

Important caveat: a visible flange rim or bolt pattern can still remain because the hand wrist/root mesh is smaller than the arm flange and there is no explicit CAD wrist-adapter plate in the model. If the goal is a physically exact bolted interface, SolidWorks should expose two explicit frames later:

- arm `flange_mount_csys` on the actual external flange mounting plane;
- hand `wrist_mount_csys` on the proximal wrist/adapter mounting plane.

## 2026-05-27 CAD Mount CSV Update

The user exported exact SolidWorks mount frames and bridge frames:

- arm: `arm_flange_mount_csys`, `csys_j4`
- hand: `hand_wrist_mount_csys`, `hand_base_csys`

The CAD-frame candidate computes:

`T_ee_mount_to_hand_base = T_csys_j4_to_arm_flange_mount * inverse(T_hand_base_to_hand_wrist_mount)`

Result:

- `hand_base_link` parent: `ee_mount`
- hand base pos in `ee_mount`: `[-0.02088772184, 0.02424258807, 0.0550479998]`
- hand base quat in `ee_mount`: `[0.2527988274, 0.239537304, -0.6652983388, -0.6603731922]`
- CAD mount origin alignment error: `0 m`

This supersedes the earlier guessed identity/flange-seated candidates. If the new candidate still looks visually wrong, the next correction should be made by changing the SolidWorks mount CSYS axis directions or clocking, not by guessing another MuJoCo offset.
