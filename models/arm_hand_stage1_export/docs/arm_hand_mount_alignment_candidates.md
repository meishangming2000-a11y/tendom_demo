# Arm-Hand Mount Alignment Candidates

Generated: 2026-05-26T15:40:04

## Purpose

Diagnose whether the arm `ee_tool_frame` and hand `hand_base_link` origins represent physical mounting faces. Only the fixed child transform of `hand_base_link` under `ee_tool_frame` is changed in these candidates. CAD, STL, joint names, and joint trees are unchanged.

## Key Diagnosis

- The current identity attachment is kinematically valid, but it does not prove flange-face calibration.
- `hand_base_link` is a body origin near the wrist/root geometry, not necessarily the proximal mounting face.
- If the flange disk remains too exposed, the likely fix is a fixed transform offset, not a new joint or training change.

## Candidate Table

| label | hand pos in ee_tool_frame | ee-to-hand-base distance | note |
|---|---:|---:|---|
| `identity` | `[0.0, 0.0, 0.0]` | 0.0000 m | Current first assembly transform. |
| `tool_z_plus_12mm` | `[0.0, 0.0, 0.012]` | 0.0120 m | Move hand outward along ee_tool_frame local +Z. |
| `tool_z_plus_25mm` | `[0.0, 0.0, 0.025]` | 0.0250 m | Move hand outward along ee_tool_frame local +Z by about hand-base half-depth. |
| `tool_z_minus_12mm` | `[0.0, 0.0, -0.012]` | 0.0120 m | Move hand inward along ee_tool_frame local -Z. |
| `tool_z_minus_25mm` | `[0.0, 0.0, -0.025]` | 0.0250 m | Move hand inward along ee_tool_frame local -Z by about hand-base half-depth. |
| `tool_x_plus_15mm` | `[0.015, 0.0, 0.0]` | 0.0150 m | Lateral local +X centering diagnostic. |
| `tool_x_minus_15mm` | `[-0.015, 0.0, 0.0]` | 0.0150 m | Lateral local -X centering diagnostic. |
| `tool_y_plus_15mm` | `[0.0, 0.015, 0.0]` | 0.0150 m | Local +Y diagnostic. |
| `tool_y_minus_15mm` | `[0.0, -0.015, 0.0]` | 0.0150 m | Local -Y diagnostic. |

## Contact Sheets

- flange closeup: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks_mount_alignment\contact_sheet_flange_closeup.png`
- wrist closeup: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks_mount_alignment\contact_sheet_wrist_closeup.png`
- top: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks_mount_alignment\contact_sheet_top.png`

## Current Recommendation

Use the contact sheets for visual selection. Prefer a candidate where the hand wrist/root covers or seats against the visible flange face without burying the palm into the arm body. If none looks right, the next check is whether the arm export has a missing flange-face frame distinct from `ee_tool_frame`.
