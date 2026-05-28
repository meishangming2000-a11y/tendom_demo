# Export4 Retargeting Scaffold

Generated: 2026-05-26T02:03:55

## Scope

This is only a semantic mapping scaffold for future human/Shadow -> export4 retargeting. It does not consume video/glove data, optimize targets, train a model, or rename joints.

## Export4 Keypoints

| semantic keypoint | model object | note |
|---|---|---|
| `palm_reference` | `palm_link` | Use palm_link pose as the current palm reference. TODO: finalize palmar/dorsal side convention. |
| `index_tip` | `index_tip_site` |  |
| `middle_tip` | `middle_tip_site` |  |
| `ring_tip` | `ring_tip_site` |  |
| `little_tip` | `little_tip_site` |  |
| `thumb_tip` | `thumb_tip_site` |  |

## Action Groups

- `wrist_joints`: `['wrist_1_joint', 'wrist_2_joint']`
- `four_finger_spread_joints_currently_named_mcp_flex`: `['index_mcp_flex_joint', 'middle_mcp_flex_joint', 'ring_mcp_flex_joint', 'little_mcp_flex_joint']`
- `four_finger_flex_joints`: `['index_mcp_abd_joint', 'index_pip_joint', 'index_dip_joint', 'middle_mcp_abd_joint', 'middle_pip_joint', 'middle_dip_joint', 'ring_mcp_abd_joint', 'ring_pip_joint', 'ring_dip_joint', 'little_mcp_abd_joint', 'little_pip_joint', 'little_dip_joint']`
- `thumb_joints`: `['thumb_cmc_abd_joint', 'thumb_cmc_joint', 'thumb_mcp_joint', 'thumb_ip_joint']`

## Semantic Joint Alias Table

| semantic name | current joint name | actual motion semantics | exists | note |
|---|---|---|---:|---|
| `wrist_yaw_or_roll_1` | `wrist_1_joint` | wrist root DOF, exact anatomical meaning TBD | True | Keep as explicit wrist group for Shadow/human alignment. |
| `wrist_yaw_or_roll_2` | `wrist_2_joint` | wrist/palm active hinge, confirmed should be revolute | True | Included in action mapping after wrist2 experiment. |
| `index_spread` | `index_mcp_flex_joint` | spread / abduction-adduction | True | Name is misleading; do not rename yet. Semantic alias used for retargeting. |
| `index_mcp_flexion` | `index_mcp_abd_joint` | likely primary MCP flexion for current export4 | True | Name may be semantically reversed relative to CAD labels; verify with visual audit before training. |
| `index_pip_flexion` | `index_pip_joint` | PIP flexion | True | Current scripted close uses negative target sign. |
| `index_dip_flexion` | `index_dip_joint` | DIP flexion | True | Current scripted close uses negative target sign. |
| `middle_spread` | `middle_mcp_flex_joint` | spread / abduction-adduction | True | Name is misleading; do not rename yet. Semantic alias used for retargeting. |
| `middle_mcp_flexion` | `middle_mcp_abd_joint` | likely primary MCP flexion for current export4 | True | Name may be semantically reversed relative to CAD labels; verify with visual audit before training. |
| `middle_pip_flexion` | `middle_pip_joint` | PIP flexion | True | Current scripted close uses negative target sign. |
| `middle_dip_flexion` | `middle_dip_joint` | DIP flexion | True | Current scripted close uses negative target sign. |
| `ring_spread` | `ring_mcp_flex_joint` | spread / abduction-adduction | True | Name is misleading; do not rename yet. Semantic alias used for retargeting. |
| `ring_mcp_flexion` | `ring_mcp_abd_joint` | likely primary MCP flexion for current export4 | True | Name may be semantically reversed relative to CAD labels; verify with visual audit before training. |
| `ring_pip_flexion` | `ring_pip_joint` | PIP flexion | True | Current scripted close uses negative target sign. |
| `ring_dip_flexion` | `ring_dip_joint` | DIP flexion | True | Current scripted close uses negative target sign. |
| `little_spread` | `little_mcp_flex_joint` | spread / abduction-adduction | True | Name is misleading; do not rename yet. Semantic alias used for retargeting. |
| `little_mcp_flexion` | `little_mcp_abd_joint` | likely primary MCP flexion for current export4 | True | Name may be semantically reversed relative to CAD labels; verify with visual audit before training. |
| `little_pip_flexion` | `little_pip_joint` | PIP flexion | True | Current scripted close uses negative target sign. |
| `little_dip_flexion` | `little_dip_joint` | DIP flexion | True | Current scripted close uses negative target sign. |
| `thumb_cmc_abduction` | `thumb_cmc_abd_joint` | thumb first CMC DOF; axis confirmed through center in SolidWorks | True | Sign selected by scripted target; do not flip axis automatically. |
| `thumb_cmc_flexion` | `thumb_cmc_joint` | thumb second CMC/flexion DOF in export4 naming | True | Export3/4 naming kept as `thumb_cmc_joint`; semantic alias records actual role. |
| `thumb_mcp_flexion` | `thumb_mcp_joint` | thumb MCP flexion | True | Axis previously confirmed by user as mechanically credible. |
| `thumb_ip_flexion` | `thumb_ip_joint` | thumb IP flexion | True | Target sign remains scripted/audited. |

## TODO Before Real Retargeting

1. Finalize canonical palmar side and ball-side convention.
2. Decide whether Shadow/video coordinates map to fingertip positions, joint angles, or a hybrid objective.
3. Add quality checks for physically impossible poses, joint-limit clipping, and self-collision.
4. Keep this as semantic aliasing; do not rename export4 joints until CAD/URDF naming is deliberately revised.
