# Arm + Export4 CAD Mount Candidate

Generated: 2026-05-27T01:53:04

## Scope

Experimental MuJoCo assembly only. CAD, STL, joint tree, and joint names were not modified.

## CSV Inputs

- Arm CSV: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mount_csys_exports\打印装配体_mount_csys_export.csv`
- Hand CSV: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mount_csys_exports\hand_export_mount_csys_export.csv`

## Formula

`T_ee_mount_to_hand_base = T_csys_j4_to_arm_flange_mount * inverse(T_hand_base_to_hand_wrist_mount)`

## Resulting Fixed Transform

- Parent body: `ee_mount`
- Child body: `hand_base_link`
- hand_base pos in ee_mount: `[-0.02088772183937338, 0.02424258807052312, 0.055047999796798974]`
- hand_base quat in ee_mount: `[0.2527988265351695, 0.23953730430403544, -0.665298338978001, -0.6603731924467483]`
- alignment translation error: `0 m`
- alignment rotation Frobenius error: `0`

## Outputs

- MJCF: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_cad_mount_candidate.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`

## Notes

- The hand is attached directly under `ee_mount`, not under the earlier manually inserted `ee_tool_frame`.
- Debug sites were added for the arm flange mount frame and hand wrist mount frame. If alignment is correct, their origins and axes overlap in the rendered model.
- This assumes SolidWorks exported `csys_j4` corresponds to the MuJoCo `ee_mount` body frame and `hand_base_csys` corresponds to the MuJoCo `hand_base_link` body frame.
