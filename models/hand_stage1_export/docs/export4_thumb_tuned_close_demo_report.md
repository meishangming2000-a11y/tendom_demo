# Export4 Thumb-Tuned Close Demo

Generated: 2026-05-25 01:42:23

## Scope

Position-actuator scripted close using the long-finger-tuned export4 model plus the visual thumb target. No CAD, STL, joint tree, joint names, or tendon routing were changed.

## Target Summary

| joint | target |
|---|---:|
| `thumb_cmc_abd_joint` | `-0.3000` |
| `thumb_cmc_joint` | `0.0000` |
| `thumb_mcp_joint` | `0.2500` |
| `thumb_ip_joint` | `-0.2500` |

## Stage Metrics

| stage | contact | max penetration | thumb-index | thumb-middle | thumb-long-centroid |
|---|---:|---:|---:|---:|---:|
| open_hand | 0 | 0.00000 | 0.1307 | 0.1535 | 0.1449 |
| preshape | 0 | 0.00000 | 0.0835 | 0.1040 | 0.1124 |
| four_fingers_closed | 0 | 0.00000 | 0.0398 | 0.0584 | 0.0649 |
| thumb_visual_close | 0 | 0.00000 | 0.0179 | 0.0333 | 0.0330 |
| hold | 0 | 0.00000 | 0.0195 | 0.0332 | 0.0314 |

## Visual Notes

- Screenshots are color-coded for debugging: thumb link orange, thumb tip red, index tip green, middle tip cyan.
- Visual target is preferred over the pure score-best target because it adds mild thumb MCP/IP flexion.
- This is acceptable as a scripted smoke-test target, but not yet a training-ready contact policy.

## Screenshots

- `open_hand`: {'front': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\01_open_hand_front.png', 'top': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\01_open_hand_top.png', 'thumbside': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\01_open_hand_thumbside.png'}
- `preshape`: {'front': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\02_preshape_front.png', 'top': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\02_preshape_top.png', 'thumbside': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\02_preshape_thumbside.png'}
- `four_fingers_closed`: {'front': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\03_four_fingers_closed_front.png', 'top': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\03_four_fingers_closed_top.png', 'thumbside': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\03_four_fingers_closed_thumbside.png'}
- `thumb_visual_close`: {'front': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\04_thumb_visual_close_front.png', 'top': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\04_thumb_visual_close_top.png', 'thumbside': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\04_thumb_visual_close_thumbside.png'}
- `hold`: {'front': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\05_hold_front.png', 'top': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\05_hold_top.png', 'thumbside': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_thumb_tuned_close\\05_hold_thumbside.png'}
