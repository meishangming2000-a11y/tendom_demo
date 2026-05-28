# Joint Direction Audit

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_primitive.xml`
- Load success: yes
- Positive test angle: 0.2 rad
- Ball position: `[0.01, -0.045, 0.215]`

## Results

| Joint | Site | Displacement norm | Ball distance delta | Classification |
|---|---|---:|---:|---|
| `wrist_1_joint` | `all_tip_sites` | 0.04570 | N/A | moves_body_no_single_fingertip_site |
| `wrist_2_joint` | `all_tip_sites` | 0.04284 | N/A | moves_body_no_single_fingertip_site |
| `index_mcp_flex_joint` | `index_tip_site` | 0.02029 | 0.00877 | moves_tip_needs_mcp_semantic_review |
| `index_mcp_abd_joint` | `index_tip_site` | 0.01835 | -0.00435 | moves_tip_needs_mcp_semantic_review |
| `index_pip_joint` | `index_tip_site` | 0.01136 | -0.00305 | positive_angle_moves_tip_toward_ball |
| `index_dip_joint` | `index_tip_site` | 0.00559 | -0.00214 | positive_angle_moves_tip_toward_ball |
| `middle_mcp_flex_joint` | `middle_tip_site` | 0.02335 | 0.00396 | moves_tip_needs_mcp_semantic_review |
| `middle_mcp_abd_joint` | `middle_tip_site` | 0.02150 | -0.00366 | moves_tip_needs_mcp_semantic_review |
| `middle_pip_joint` | `middle_tip_site` | 0.01252 | -0.00313 | positive_angle_moves_tip_toward_ball |
| `middle_dip_joint` | `middle_tip_site` | 0.00559 | -0.00219 | positive_angle_moves_tip_toward_ball |
| `ring_mcp_flex_joint` | `ring_tip_site` | 0.02140 | -0.00292 | moves_tip_needs_mcp_semantic_review |
| `ring_mcp_abd_joint` | `ring_tip_site` | 0.01947 | -0.00317 | moves_tip_needs_mcp_semantic_review |
| `ring_pip_joint` | `ring_tip_site` | 0.01154 | -0.00332 | positive_angle_moves_tip_toward_ball |
| `ring_dip_joint` | `ring_tip_site` | 0.00559 | -0.00231 | positive_angle_moves_tip_toward_ball |
| `little_mcp_flex_joint` | `little_tip_site` | 0.01931 | -0.01083 | moves_tip_needs_mcp_semantic_review |
| `little_mcp_abd_joint` | `little_tip_site` | 0.01746 | -0.00314 | moves_tip_needs_mcp_semantic_review |
| `little_pip_joint` | `little_tip_site` | 0.01050 | -0.00288 | positive_angle_moves_tip_toward_ball |
| `little_dip_joint` | `little_tip_site` | 0.00559 | -0.00221 | positive_angle_moves_tip_toward_ball |
| `thumb_cmc_joint` | `thumb_tip_site` | 0.02217 | -0.00272 | moves_thumb_tip_needs_opposition_review |
| `thumb_mcp_joint` | `thumb_tip_site` | 0.01197 | -0.00264 | moves_thumb_tip_needs_opposition_review |
| `thumb_ip_joint` | `thumb_tip_site` | 0.00559 | 0.00120 | moves_thumb_tip_needs_opposition_review |

## Notes

- This audit applies a positive qpos offset to one hinge joint at a time in the primitive model.
- Classifications are heuristics for inspection, not mechanical truth.
- mcp_flex/mcp_abd names are intentionally not changed; semantic review remains TODO.
- A positive angle moving a fingertip away from the ball may be correct if the ball pose or open pose is not aligned with that joint axis.
