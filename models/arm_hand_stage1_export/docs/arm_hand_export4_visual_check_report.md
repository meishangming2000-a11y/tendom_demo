# Arm + Export4 Hand Visual Check Report

Generated: 2026-05-27T01:58:14

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 59, 'nsite': 14, 'nmesh': 29}`

- Visual conclusion: `PASS_FIRST_ASSEMBLY_CANDIDATE`

## Mount Metrics

- ee_tool_frame_site to hand_base_link: `0.042921 m`
- ee_tool_frame body to hand_base_link: `0.042921 m`
- hand_base_link to wrist_middle_link: `0.015000 m`
- wrist_middle_link to palm_link: `0.020292 m`

## Renders

- `overview`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_overview.png`
- `side`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_side.png`
- `top`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_top.png`
- `wrist_closeup`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_wrist_closeup.png`
- `flange_axis`: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_flange_axis.png`

## Notes

- This is a first attachment candidate, not final flange calibration.
- The wrist/root is attached near the arm flange and no longer has the old one-point separate-model look.
- If exact flange face or bolt-pattern alignment is needed, adjust only the fixed hand root transform in a new experiment file.
