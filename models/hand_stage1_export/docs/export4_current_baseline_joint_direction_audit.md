# Export4 Current Baseline Joint Direction Audit

Generated: 2026-05-25 14:57:12

Model: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_current_baseline.xml`

Visual sheet: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_current_baseline_audit\joint_direction\joint_direction_positive_negative_sheet.png`

## Status Counts

- `AUDIT_ONLY`: 10
- `PASS`: 12

## Joint Direction Table

| joint | status | range | +Y delta at +angle | +Y delta at -angle | expectation |
|---|---|---:|---:|---:|---|
| `wrist_1_joint` | AUDIT_ONLY | `-0.800 0.800` | -0.00342 | 0.00342 | not signed |
| `wrist_2_joint` | AUDIT_ONLY | `-0.800 0.800` | 0.04232 | -0.04031 | not signed |
| `index_mcp_flex_joint` | AUDIT_ONLY | `-0.300 0.180` | -0.00125 | 0.00207 | not signed |
| `index_mcp_abd_joint` | PASS | `-0.780 0.080` | -0.00720 | 0.01826 | negative should move fingertip toward palmar +Y |
| `index_pip_joint` | PASS | `-1.100 0.040` | -0.00224 | 0.01132 | negative should move fingertip toward palmar +Y |
| `index_dip_joint` | PASS | `-0.660 0.040` | -0.00108 | 0.00546 | negative should move fingertip toward palmar +Y |
| `little_mcp_flex_joint` | AUDIT_ONLY | `-0.280 0.160` | -0.00147 | 0.00240 | not signed |
| `little_mcp_abd_joint` | PASS | `-0.760 0.080` | -0.00661 | 0.01710 | negative should move fingertip toward palmar +Y |
| `little_pip_joint` | PASS | `-1.000 0.040` | -0.00197 | 0.01018 | negative should move fingertip toward palmar +Y |
| `little_dip_joint` | PASS | `-0.620 0.040` | -0.00100 | 0.00524 | negative should move fingertip toward palmar +Y |
| `middle_mcp_flex_joint` | AUDIT_ONLY | `-0.300 0.180` | -0.00151 | 0.00245 | not signed |
| `middle_mcp_abd_joint` | PASS | `-0.860 0.080` | -0.00817 | 0.02110 | negative should move fingertip toward palmar +Y |
| `middle_pip_joint` | PASS | `-1.160 0.040` | -0.00238 | 0.01224 | negative should move fingertip toward palmar +Y |
| `middle_dip_joint` | PASS | `-0.700 0.040` | -0.00102 | 0.00532 | negative should move fingertip toward palmar +Y |
| `ring_mcp_flex_joint` | AUDIT_ONLY | `-0.300 0.180` | -0.01764 | 0.02083 | not signed |
| `ring_mcp_abd_joint` | PASS | `-0.840 0.080` | -0.00725 | 0.01890 | negative should move fingertip toward palmar +Y |
| `ring_pip_joint` | PASS | `-1.100 0.040` | -0.00211 | 0.01101 | negative should move fingertip toward palmar +Y |
| `ring_dip_joint` | PASS | `-0.680 0.040` | -0.00098 | 0.00518 | negative should move fingertip toward palmar +Y |
| `thumb_cmc_abd_joint` | AUDIT_ONLY | `-1.050 1.050` | 0.01643 | -0.01849 | not signed |
| `thumb_cmc_joint` | AUDIT_ONLY | `-0.950 0.950` | 0.00571 | -0.00798 | not signed |
| `thumb_mcp_joint` | AUDIT_ONLY | `-0.100 1.200` | 0.00230 | -0.00165 | not signed |
| `thumb_ip_joint` | AUDIT_ONLY | `-0.850 0.050` | -0.00033 | 0.00093 | not signed |

## Interpretation

- Long-finger MCP-abd/PIP/DIP are expected to close toward the current palmar side on negative commands.
- MCP-flex, wrist, and thumb joints are marked audit-only because their mechanical semantics are not one-dimensional palm closure.
- Any `NEEDS_SW_CHECK` row should be checked in SolidWorks for joint axis direction, csys Z axis, and limit sign.
