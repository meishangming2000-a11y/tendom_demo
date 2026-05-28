# SolidWorks Mount CSYS Export Instructions

Goal: export exact transforms for the arm flange mount frame and hand wrist mount frame so MuJoCo can align the hand to the arm without guessing offsets.

## Coordinate System Names

Use these canonical names if possible:

- Arm assembly flange frame: `arm_flange_mount_csys`
- Hand assembly wrist frame: `hand_wrist_mount_csys`

The current screenshots show the arm-side feature may be named `hand_wrist_mount_cysc`. That is okay for this export macro because it checks that typo too, but please rename the arm-side coordinate system to `arm_flange_mount_csys` when convenient.

## Macro

Macro file:

`D:\tendon_project\simulations\models\arm_hand_stage1_export\solidworks\export_mount_csys_transforms.bas`

## Run Procedure

1. Open the mechanical arm assembly in SolidWorks.
2. Run the macro.
3. It will export a CSV next to the active assembly, named like:

   `<arm-assembly-name>_mount_csys_export.csv`

4. Open the hand assembly in SolidWorks.
5. Run the same macro again.
6. It will export another CSV next to the hand assembly, named like:

   `<hand-assembly-name>_mount_csys_export.csv`

## What The CSV Contains

Each row includes:

- coordinate-system name;
- status: `FOUND`, `MISSING`, or `ERROR`;
- origin in meters;
- X/Y/Z axis unit vectors in the active assembly frame;
- origin in mm for easier human reading;
- raw SolidWorks transform entries.

## Send Back

Copy both CSV files into:

`D:\tendon_project\simulations\models\arm_hand_stage1_export\mount_csys_exports\`

Then Codex can compute the fixed `ee_tool_frame -> hand_base_link` transform from actual CAD mount frames.
