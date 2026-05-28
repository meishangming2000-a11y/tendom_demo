# Arm-Hand Joint Limit And Pose Tuning Report

Generated: 2026-05-27T02:26:16

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_joint_limit_tuned.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_joint_limit_tuned.xml`
- Status: **PASS_LOAD_AND_RENDER**
- Model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 59, 'nsite': 14, 'nmesh': 29, 'nq': 26, 'nv': 26}`

## Scripted Poses

| pose | render | applied target count |
|---|---|---:|
| open_hand | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_joint_limit_tuning\open_hand.png` | 0 |
| preshape | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_joint_limit_tuning\preshape.png` | 16 |
| close_four_fingers | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_joint_limit_tuning\close_four_fingers.png` | 16 |
| close_thumb_smoke | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_joint_limit_tuning\close_thumb_smoke.png` | 20 |

## Semantic Notes

- `+Y` has been confirmed as palm/grasp side.
- Four-finger `*_mcp_flex_joint` is treated as spread/abduction-adduction, despite the current name.
- Four-finger closure uses current `*_mcp_abd_joint`, PIP, and DIP targets.
- Thumb is kept as scripted-smoke only; no further target tuning is claimed here.

## Joint Table

| joint | body | range | note |
|---|---|---|---|
| j1 | link_1 | `-3.142 3.142` |  |
| j2 | link_2 | `-1.571 1.571` |  |
| j3 | link_3 | `-1.571 1.571` |  |
| j4 | ee_mount | `-3.142 3.142` |  |
| wrist_1_joint | wrist_middle_link | `-0.800 0.800` |  |
| wrist_2_joint | palm_link | `-0.800 0.800` |  |
| index_mcp_flex_joint | index_mcp_flex_link | `-0.300 0.180` | User-confirmed spread / abduction-adduction semantic; name kept for compatibility. |
| index_mcp_abd_joint | index_proximal_phalanx_link | `-0.780 0.080` | Used as long-finger flexion/closure target in scripted smoke. |
| index_pip_joint | index_proximal_inter_link | `-1.100 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| index_dip_joint | index_distal_link | `-0.660 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| little_mcp_flex_joint | little_mcp_flex_link | `-0.280 0.160` | User-confirmed spread / abduction-adduction semantic; name kept for compatibility. |
| little_mcp_abd_joint | little_proximal_phalanx_link | `-0.760 0.080` | Used as long-finger flexion/closure target in scripted smoke. |
| little_pip_joint | little_proximal_inter_link | `-1.000 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| little_dip_joint | little_distal_link | `-0.620 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| middle_mcp_flex_joint | middle_mcp_flex_link | `-0.300 0.180` | User-confirmed spread / abduction-adduction semantic; name kept for compatibility. |
| middle_mcp_abd_joint | middle_proximal_phalanx_link | `-0.860 0.080` | Used as long-finger flexion/closure target in scripted smoke. |
| middle_pip_joint | middle_proximal_inter_link | `-1.160 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| middle_dip_joint | middle_distal_link | `-0.700 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| ring_mcp_flex_joint | ring_mcp_flex_link | `-0.300 0.180` | User-confirmed spread / abduction-adduction semantic; name kept for compatibility. |
| ring_mcp_abd_joint | ring_proximal_phalanx_link | `-0.840 0.080` | Used as long-finger flexion/closure target in scripted smoke. |
| ring_pip_joint | ring_proximal_inter_link | `-1.100 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| ring_dip_joint | ring_distal_link | `-0.680 0.040` | Used as long-finger flexion/closure target in scripted smoke. |
| thumb_cmc_abd_joint | thumb_trapezium1_link | `-1.050 1.050` | Thumb scripted-smoke target only; not Shadow-equivalent opposition. |
| thumb_cmc_joint | thumb_metacarpal_link | `-0.950 0.950` | Thumb scripted-smoke target only; not Shadow-equivalent opposition. |
| thumb_mcp_joint | thumb_proximal_link | `-0.100 1.200` | Thumb scripted-smoke target only; not Shadow-equivalent opposition. |
| thumb_ip_joint | thumb_distal_link | `-0.850 0.050` | Thumb scripted-smoke target only; not Shadow-equivalent opposition. |
