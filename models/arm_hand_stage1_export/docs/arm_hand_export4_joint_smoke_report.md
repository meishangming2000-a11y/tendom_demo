# Arm + Export4 Hand Joint Smoke Report

Generated: 2026-05-27T01:58:13

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Overall status: **PASS**
- Model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 59, 'nsite': 14, 'nmesh': 29}`
- Joint kinematic smoke: `{'total': 26, 'pass': 26, 'fail': 0, 'skipped': 0}`
- Actuator smoke: `PASS` after `250` steps
- Open render: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_joint_smoke_open.png`
- Actuated render: `D:\tendon_project\simulations\models\arm_hand_stage1_export\visual_checks\arm_hand_joint_smoke_actuated.png`

## Notes

- The hand is attached as a child body under the arm `ee_tool_frame`.
- This smoke test checks loadability, finite kinematics, and finite position-actuator stepping only. It is not a collision or grasp-quality proof.

## Joint Results

| joint | body | target rad | status | pos_delta | rot_delta |
|---|---|---:|---|---:|---:|
| j1 | link_1 | 0.1200 | PASS | 0.000000 | 0.169604 |
| j2 | link_2 | 0.1200 | PASS | 0.000000 | 0.169604 |
| j3 | link_3 | 0.1200 | PASS | 0.000000 | 0.169604 |
| j4 | ee_mount | 0.1200 | PASS | 0.000000 | 0.169604 |
| wrist_1_joint | wrist_middle_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| wrist_2_joint | palm_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| index_mcp_flex_joint | index_mcp_flex_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| index_mcp_abd_joint | index_proximal_phalanx_link | 0.0800 | PASS | 0.000000 | 0.113107 |
| index_pip_joint | index_proximal_inter_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| index_dip_joint | index_distal_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| little_mcp_flex_joint | little_mcp_flex_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| little_mcp_abd_joint | little_proximal_phalanx_link | 0.0800 | PASS | 0.000000 | 0.113107 |
| little_pip_joint | little_proximal_inter_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| little_dip_joint | little_distal_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| middle_mcp_flex_joint | middle_mcp_flex_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| middle_mcp_abd_joint | middle_proximal_phalanx_link | 0.0800 | PASS | 0.000000 | 0.113107 |
| middle_pip_joint | middle_proximal_inter_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| middle_dip_joint | middle_distal_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| ring_mcp_flex_joint | ring_mcp_flex_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| ring_mcp_abd_joint | ring_proximal_phalanx_link | 0.0800 | PASS | 0.000000 | 0.113107 |
| ring_pip_joint | ring_proximal_inter_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| ring_dip_joint | ring_distal_link | 0.0400 | PASS | 0.000000 | 0.056565 |
| thumb_cmc_abd_joint | thumb_trapezium1_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| thumb_cmc_joint | thumb_metacarpal_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| thumb_mcp_joint | thumb_proximal_link | 0.1200 | PASS | 0.000000 | 0.169604 |
| thumb_ip_joint | thumb_distal_link | 0.0500 | PASS | 0.000000 | 0.070703 |
