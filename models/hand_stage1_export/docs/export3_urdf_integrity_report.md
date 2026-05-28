# Export3 URDF Integrity Report

- URDF: `D:\tendon_project\simulations\models\hand_stage1_export\export3\urdf\hand_export3.urdf`
- Robot name: `hand_export3`
- Links: 24
- Joints: 23
- Revolute joints: 21
- Fixed joints: 2
- Empty_Link: no
- Duplicate links: None
- Duplicate joints: None
- Missing parent/child joints: None
- Revolute joints missing limit: None
- Missing mesh refs: 0
- Unresolved package refs: 0
- Old `thumb_cmc_joint` present: no
- Expected export3 thumb chain OK: yes
- Overall pass: yes

## Export3 Thumb Chain Check

| Joint | Expected | Actual | Type | OK |
|---|---|---|---|---|
| `thumb_root_connector_fixed_joint` | `palm_link -> thumb_root_connector_link` | `palm_link -> thumb_root_connector_link` | `fixed` | yes |
| `thumb_cmc_abd_joint` | `thumb_root_connector_link -> thumb_trapezium1_link` | `thumb_root_connector_link -> thumb_trapezium1_link` | `revolute` | yes |
| `thumb_cmc_flex_joint` | `thumb_trapezium1_link -> thumb_metacarpal_link` | `thumb_trapezium1_link -> thumb_metacarpal_link` | `revolute` | yes |
| `thumb_mcp_joint` | `thumb_metacarpal_link -> thumb_proximal_link` | `thumb_metacarpal_link -> thumb_proximal_link` | `revolute` | yes |
| `thumb_ip_joint` | `thumb_proximal_link -> thumb_distal_link` | `thumb_proximal_link -> thumb_distal_link` | `revolute` | yes |

## Notes

- `wrist_2_joint` is recorded exactly as exported. If it is fixed in export3, this report does not change it.
- If a name differs from the target chain, this report records the actual name and does not force a rename.
- TODO: manually confirm MCP flex/abd semantics against actual axes.
