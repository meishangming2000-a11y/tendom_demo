# Mesh Body Transform Analysis

- Primitive XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_primitive.xml`
- Source clean draft XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_draft.xml`
- Aligned draft XML: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_aligned_draft.xml`
- Method: center-align each clean visual mesh group to the matching primitive body's main local geometry center
- Scale preserved: `0.001 0.001 0.001`
- Joint tree changed: False
- Joint names changed: False
- STL files modified: False

## Interpretation

- The previous clean mesh draft treated STL vertices as body-local coordinates.
- The large visual offsets suggest many STL vertex clouds still contain CAD assembly/world position components.
- This pass adds per-body MJCF `geom pos` translations so each clean mesh group center is moved to that body's primitive reference center.
- No automatic rotation is applied because the required CAD-to-body rotations are not confirmed.

## Per-Link Translation Analysis

| Body | Sample | Error before m | Delta local applied | Target primitive geom | Assembly-coordinate-like |
|---|---|---:|---|---|---|
| `hand_base_link` | True | 0.04802 | `[-0.02531, -0.02795, -0.02973]` | `hand_base_link_primitive` | False |
| `index_distal_link` | True | 0.22476 | `[-0.00623, -0.22453, -0.00816]` | `index_distal_link_primitive` | True |
| `index_mcp_flex_link` | True | 0.15690 | `[-0.01053, -0.1563, -0.00892]` | `index_mcp_flex_link_primitive` | True |
| `index_proximal_inter_link` | False | 0.20072 | `[-0.0048, -0.20036, -0.011]` | `index_proximal_inter_link_primitive` | True |
| `index_proximal_phalanx_link` | True | 0.16537 | `[-0.01247, -0.16465, -0.00921]` | `index_proximal_phalanx_link_primitive` | True |
| `little_distal_link` | False | 0.22643 | `[-0.06355, -0.21695, -0.01286]` | `little_distal_link_primitive` | True |
| `little_mcp_flex_link` | False | 0.15297 | `[-0.06419, -0.13856, -0.00906]` | `little_mcp_flex_link_primitive` | True |
| `little_proximal_inter_link` | False | 0.19533 | `[-0.07341, -0.18071, -0.01036]` | `little_proximal_inter_link_primitive` | True |
| `little_proximal_phalanx_link` | False | 0.17226 | `[-0.0506, -0.16436, -0.01009]` | `little_proximal_phalanx_link_primitive` | True |
| `middle_distal_link` | False | 0.25396 | `[-0.01532, -0.25308, -0.01469]` | `middle_distal_link_primitive` | True |
| `middle_mcp_flex_link` | False | 0.15545 | `[-0.02254, -0.15355, -0.00893]` | `middle_mcp_flex_link_primitive` | True |
| `middle_proximal_inter_link` | False | 0.22528 | `[-0.01059, -0.22471, -0.01196]` | `middle_proximal_inter_link_primitive` | True |
| `middle_proximal_phalanx_link` | False | 0.18602 | `[-0.00281, -0.18566, -0.01117]` | `middle_proximal_phalanx_link_primitive` | True |
| `palm_link` | True | 0.09102 | `[-0.05514, -0.05145, -0.05097]` | `palm_link_ellipsoid` | True |
| `ring_distal_link` | False | 0.24033 | `[-0.03694, -0.23679, -0.01794]` | `ring_distal_link_primitive` | True |
| `ring_mcp_flex_link` | False | 0.15340 | `[-0.04285, -0.14702, -0.00895]` | `ring_mcp_flex_link_primitive` | True |
| `ring_proximal_inter_link` | False | 0.20104 | `[-0.04711, -0.19502, -0.01277]` | `ring_proximal_inter_link_primitive` | True |
| `ring_proximal_phalanx_link` | False | 0.17853 | `[-0.02577, -0.17632, -0.01085]` | `ring_proximal_phalanx_link_primitive` | True |
| `thumb_distal_link` | True | 0.16644 | `[-0.00939, -0.16445, -0.0239]` | `thumb_distal_link_primitive` | True |
| `thumb_metacarpal_link` | True | 0.08856 | `[-0.03163, -0.07624, -0.03209]` | `thumb_metacarpal_link_primitive` | True |
| `thumb_proximal_link` | False | 0.11967 | `[-0.01495, -0.11562, -0.02699]` | `thumb_proximal_link_primitive` | True |
| `thumb_root_connector_link` | False | 0.08100 | `[-0.01197, -0.0776, -0.01989]` | `thumb_root_connector_link_primitive` | True |
| `wrist_middle_link` | True | 0.05552 | `[-0.02866, -0.04404, -0.01794]` | `wrist_middle_link_primitive` | True |

## TODO / Limits

- This is an MJCF-only translation attempt. It does not edit CAD or STL files.
- The method can fix assembly/world translation offsets but cannot prove or repair unknown per-link rotations.
- If screenshots still show detached/rotated clean parts, SolidWorks body-local STL export is recommended.
