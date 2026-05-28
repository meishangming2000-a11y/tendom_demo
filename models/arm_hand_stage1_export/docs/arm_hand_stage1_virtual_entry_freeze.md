# Arm-Hand Stage1 Virtual Entry Freeze

Generated: 2026-05-27T02:26:14

## Freeze Decision

The CAD-frame-mounted arm + export4 hand assembly is frozen as the current virtual-space entry point.

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_export4_cad_mount_candidate.xml`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\scene_arm_hand_export4_cad_mount_candidate.xml`
- Status: **FROZEN_VIRTUAL_ENTRY_POINT**
- Model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 59, 'nsite': 14, 'nmesh': 29, 'nq': 26, 'nv': 26}`
- Joint count: `26`
- Actuator count: `26`
- `wrist_2_joint`: `hinge`
- Freeze render: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_joint_limit_tuning\phase0_frozen_cad_mount_open.png`

## Known Issues Kept Out Of The Frozen Baseline

- Full arm collision proxy is not complete in the frozen baseline.
- The hand collision proxy is a smoke proxy, not final contact geometry.
- Four-finger `*_mcp_flex_joint` names currently represent spread/abduction-adduction semantics; names are not changed.
- No training or tendon routing is included.
