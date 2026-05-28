# Export4 Current Baseline Thumb Audit

Generated: 2026-05-25 14:57:12

Model: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_current_baseline.xml`

Visual sheet: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_current_baseline_audit\thumb\thumb_audit_sheet.png`

Conclusion: `PASS_FOR_SCRIPTED_SMOKE`

## Thumb Chain

| joint | expected parent | actual parent | expected child | actual child | axis / representation | range |
|---|---|---|---|---|---|---|
| `thumb_root_connector_fixed_joint` | `palm_link` | `palm_link` | `thumb_root_connector_link` | `thumb_root_connector_link` | `MJCF fixed body nesting` | `fixed` |
| `thumb_cmc_abd_joint` | `thumb_root_connector_link` | `thumb_root_connector_link` | `thumb_trapezium1_link` | `thumb_trapezium1_link` | `0 0 -1` | `-1.05 1.05` |
| `thumb_cmc_joint` | `thumb_trapezium1_link` | `thumb_trapezium1_link` | `thumb_metacarpal_link` | `thumb_metacarpal_link` | `0 0 -1` | `-0.95 0.95` |
| `thumb_mcp_joint` | `thumb_metacarpal_link` | `thumb_metacarpal_link` | `thumb_proximal_link` | `thumb_proximal_link` | `0 0 -1` | `-0.1 1.2` |
| `thumb_ip_joint` | `thumb_proximal_link` | `thumb_proximal_link` | `thumb_distal_link` | `thumb_distal_link` | `0 0 1` | `-0.85 0.05` |

## Thumb Opposition Metrics

- open thumb-index distance: `0.1304 m`
- close thumb-index distance: `0.0196 m`
- open thumb-middle distance: `0.1531 m`
- close thumb-middle distance: `0.0333 m`
- close thumb-palm distance: `0.0980 m`

## Individual Thumb Joint Sign Probe

| joint | range | +Y delta at +angle | +Y delta at -angle | note |
|---|---:|---:|---:|---|
| `thumb_cmc_abd_joint` | `-1.050 1.050` | 0.02013 | -0.02335 | TODO: confirm mechanical meaning in SolidWorks |
| `thumb_cmc_joint` | `-0.950 0.950` | 0.00675 | -0.01030 | TODO: confirm mechanical meaning in SolidWorks |
| `thumb_mcp_joint` | `-0.100 1.200` | 0.00266 | -0.00165 | TODO: confirm mechanical meaning in SolidWorks |
| `thumb_ip_joint` | `-0.850 0.050` | -0.00033 | 0.00106 | TODO: confirm mechanical meaning in SolidWorks |

## Interpretation

- In MJCF, fixed joints are commonly represented as direct body nesting rather than an explicit `<joint>` element.
- The chain topology matches the export4 intended 2-DoF CMC chain if all rows show expected parent/child.
- Current scripted target closes the thumb near index/middle and is acceptable for smoke tests.
- This does not prove the CMC axes are anatomically final; SolidWorks should still confirm axis origins/directions.
