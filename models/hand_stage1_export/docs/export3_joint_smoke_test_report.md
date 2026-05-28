# Export3 Joint Smoke Test Report

- XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export3.xml`
- Load success: yes
- Bodies / joints / hinges / actuators / geoms / sites / meshes: 25 / 21 / 21 / 21 / 53 / 5 / 24
- All hinge joints moved numerically: yes
- `thumb_cmc_abd_joint` present: yes
- `thumb_cmc_flex_joint` present: yes
- Old `thumb_cmc_joint` present: no
- `wrist_2_joint` present as hinge: no
- Missing expected controlled joints: None

## Per Joint

| Joint | Range | Target | Actual | Moved |
|---|---|---:|---:|---|
| `wrist_1_joint` | `[-0.8, 0.8]` | 0.200000 | 0.200000 | yes |
| `index_mcp_flex_joint` | `[-0.5, 0.5]` | 0.200000 | 0.200000 | yes |
| `index_mcp_abd_joint` | `[0.2, 1.2]` | 0.200000 | 0.200000 | yes |
| `index_pip_joint` | `[0.0, 1.57]` | 0.200000 | 0.200000 | yes |
| `index_dip_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |
| `middle_mcp_flex_joint` | `[-0.5, 0.5]` | 0.200000 | 0.200000 | yes |
| `middle_mcp_abd_joint` | `[0.2, 1.2]` | 0.200000 | 0.200000 | yes |
| `middle_pip_joint` | `[0.0, 1.57]` | 0.200000 | 0.200000 | yes |
| `middle_dip_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |
| `ring_mcp_flex_joint` | `[-0.5, 0.5]` | 0.200000 | 0.200000 | yes |
| `ring_mcp_abd_joint` | `[-0.2, 1.2]` | 0.200000 | 0.200000 | yes |
| `ring_pip_joint` | `[0.0, 1.57]` | 0.200000 | 0.200000 | yes |
| `ring_dip_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |
| `little_mcp_flex_joint` | `[-0.5, 0.5]` | 0.200000 | 0.200000 | yes |
| `little_mcp_abd_joint` | `[-0.2, 1.2]` | 0.200000 | 0.200000 | yes |
| `little_pip_joint` | `[0.0, 1.57]` | 0.200000 | 0.200000 | yes |
| `little_dip_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |
| `thumb_cmc_abd_joint` | `[-0.8, 0.8]` | 0.200000 | 0.200000 | yes |
| `thumb_cmc_flex_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |
| `thumb_mcp_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |
| `thumb_ip_joint` | `[0.0, 1.2]` | 0.200000 | 0.200000 | yes |

## Notes

- This smoke test directly sets qpos for small positive hinge motion only.
- It verifies numerical mobility, not visual correctness or physical contact stability.
- export3 URDF has wrist_2_joint as fixed, so it is not expected in the hinge list unless the CAD export changes.
