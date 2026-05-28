# Export4 Flexion Sign Audit

Generated: 2026-05-25 00:52:14

## Scope

This audit checks whether small positive or negative joint motion brings the relevant fingertip closer to the palm reference. It only generates an experimental MJCF with range/ctrlrange sign changes. CAD, STL, joint names, and joint tree are unchanged.

## Outputs

- Fixed experimental hand: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_flexion_sign_fixed.xml`
- No-ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_export4_flexion_sign_fixed.xml`
- Ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_flexion_sign_fixed.xml`
- Visual summary: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export4_flexion_sign\export4_flexion_sign_summary.png`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export4_flexion_sign_audit.json`

## Summary

- Audited joints: 20
- Planned auto-fixes: 13
- Uncertain signs: 0
- For long fingers, the closing-sign criterion is fingertip displacement toward world `+Y`, which is the current export4 palmar side.
- `mcp_flex` joints were audit-only because current project notes say MCP flex/abd naming may be reversed. Several also move palmar in the negative direction, so target sign may need follow-up.
- Thumb CMC joints were audit-only because opposition is multi-axis and should not be auto-flipped from a single scalar metric.

## Planned Limit / Ctrlrange Changes

| joint | old range | new range | observed closing sign | reason |
|---|---:|---:|---|---|
| `index_mcp_abd_joint` | `0.2 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `index_pip_joint` | `0 1.57` | `-1.57 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `index_dip_joint` | `0 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `middle_mcp_abd_joint` | `0.2 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `middle_pip_joint` | `0 1.57` | `-1.57 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `middle_dip_joint` | `0 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `ring_mcp_abd_joint` | `-0.2 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `ring_pip_joint` | `0 1.57` | `-1.57 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `ring_dip_joint` | `0 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `little_mcp_abd_joint` | `-0.2 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `little_pip_joint` | `0 1.57` | `-1.57 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `little_dip_joint` | `0 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `thumb_ip_joint` | `-0.2 1.2` | `-1.2 0` | negative | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |

## Per-Joint Audit

| joint | finger | old range | +angle delta m | -angle delta m | observed closing sign | planned change | note |
|---|---|---:|---:|---:|---|---|---|
| `index_mcp_flex_joint` | index | `-0.5 0.5` | 0.004542 | -0.008897 | negative | False | mcp_flex_audit_only_possible_spread_joint |
| `index_mcp_abd_joint` | index | `0.2 1.2` | -0.001437 | -0.002940 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `index_pip_joint` | index | `0 1.57` | -0.001359 | -0.002914 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `index_dip_joint` | index | `0 1.2` | -0.001526 | -0.001207 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `middle_mcp_flex_joint` | middle | `-0.5 0.5` | 0.000390 | -0.004621 | negative | False | mcp_flex_audit_only_possible_spread_joint |
| `middle_mcp_abd_joint` | middle | `0.2 1.2` | -0.003180 | -0.001453 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `middle_pip_joint` | middle | `0 1.57` | -0.003400 | -0.001363 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `middle_dip_joint` | middle | `0 1.2` | -0.002872 | 0.000067 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `ring_mcp_flex_joint` | ring | `-0.5 0.5` | -0.003048 | -0.000743 | negative | False | mcp_flex_audit_only_possible_spread_joint |
| `ring_mcp_abd_joint` | ring | `-0.2 1.2` | -0.003535 | -0.000679 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `ring_pip_joint` | ring | `0 1.57` | -0.004298 | -0.000041 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `ring_dip_joint` | ring | `0 1.2` | -0.003227 | 0.000496 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `little_mcp_flex_joint` | little | `-0.5 0.5` | -0.008096 | 0.004428 | negative | False | mcp_flex_audit_only_possible_spread_joint |
| `little_mcp_abd_joint` | little | `-0.2 1.2` | -0.002692 | -0.001101 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `little_pip_joint` | little | `0 1.57` | -0.003335 | -0.000544 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `little_dip_joint` | little | `0 1.2` | -0.003129 | 0.000503 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |
| `thumb_cmc_abd_joint` | thumb | `-1.2 1.2` | 0.008772 | -0.009626 | negative | False | thumb_cmc_audit_only_do_not_autoflip |
| `thumb_cmc_joint` | thumb | `-1.2 1.2` | -0.006154 | 0.006015 | positive | False | thumb_cmc_audit_only_do_not_autoflip |
| `thumb_mcp_joint` | thumb | `-0.2 1.4` | -0.007274 | 0.004012 | positive | False | limit_already_supports_observed_closing_sign |
| `thumb_ip_joint` | thumb | `-0.2 1.2` | 0.001847 | -0.004225 | negative | True | current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar |

## Interpretation

- For long fingers, `observed closing sign` means the sign whose fingertip moved further toward world `+Y`, the corrected palmar side.
- For thumb CMC audit-only joints, the sign remains a distance/opposition diagnostic and is not auto-fixed.
- If a joint was positive-only but negative perturbation closed the finger, the experimental model flips that limit to a negative range ending at zero.
- This is a simulation-side repair for verification. If the result looks correct, the same sign convention should be repaired in SolidWorks/URDF limits later.
