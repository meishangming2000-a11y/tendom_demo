# Export4 Training Adapter Design

Generated: 2026-05-25 01:50:00

## Scope

This document defines the pre-training data contract for `hand_stage1_export4_current_baseline`.
It is a design scaffold, not a training run.

## Current Baseline

- Model: `mjcf\hand_stage1_export4_current_baseline.xml`
- Scene: `mjcf\scene_export4_current_baseline.xml`
- Action interface: 22D MuJoCo position actuator target.
- Current status: diagnostic baseline, not training-ready.

## Canonical Actuator Order

1. `wrist_1_joint_pos`
2. `wrist_2_joint_pos`
3. `index_mcp_flex_joint_pos`
4. `index_mcp_abd_joint_pos`
5. `index_pip_joint_pos`
6. `index_dip_joint_pos`
7. `middle_mcp_flex_joint_pos`
8. `middle_mcp_abd_joint_pos`
9. `middle_pip_joint_pos`
10. `middle_dip_joint_pos`
11. `ring_mcp_flex_joint_pos`
12. `ring_mcp_abd_joint_pos`
13. `ring_pip_joint_pos`
14. `ring_dip_joint_pos`
15. `little_mcp_flex_joint_pos`
16. `little_mcp_abd_joint_pos`
17. `little_pip_joint_pos`
18. `little_dip_joint_pos`
19. `thumb_cmc_abd_joint_pos`
20. `thumb_cmc_joint_pos`
21. `thumb_mcp_joint_pos`
22. `thumb_ip_joint_pos`

## Scripted Close Targets

Long fingers use negative close directions in the current export4 coordinate convention.

Thumb visual target:

- `thumb_cmc_abd_joint_pos = -0.30`
- `thumb_cmc_joint_pos = 0.00`
- `thumb_mcp_joint_pos = 0.25`
- `thumb_ip_joint_pos = -0.25`

## Observation Schema V0

Minimum simulation observation for scripted / BC pre-training:

- `qpos`: MuJoCo generalized positions.
- `qvel`: MuJoCo generalized velocities.
- `actuator_ctrl`: current 22D position targets.
- `tip_positions_world`: 5 fingertip sites.
- `palm_pose_world`: palm body position and orientation.
- `contact_summary`: contact count, max penetration, optional contact pairs.
- `task_phase`: enum string such as `open`, `preshape`, `close`, `hold`.
- `source`: one of `scripted`, `video_mapping`, `shadow_reference`.

## Action Schema V0

Use one canonical 22D action vector:

```text
export4_position_control_v1[22] = actuator target positions in canonical actuator order
```

Do not train directly on raw joint ranges without this adapter layer. The adapter is where sign conventions, thumb target choices, and future axis corrections are isolated.

## Video Mapping Adapter

Current deterministic bridge:

```text
hand_open_close_feature_v1[35] -> export4_position_control_v1[22]
```

Interpretation:

- feature value `0`: open / neutral actuator target.
- feature value `1`: current tuned close target.
- long-finger curl maps to negative MCP/PIP/DIP targets.
- thumb opposition maps toward the visual thumb target.

## Training Gate Checklist

Training should wait until these are stable:

- joint direction audit passes on current baseline;
- thumb audit accepts current CMC/MCP/IP target signs;
- collision proxy audit accepts contact geometry for the intended task;
- scripted grasp-state metrics are defined;
- reset distribution is defined;
- success metrics are independent of visual-only mesh;
- Shadow comparison uses the same adapter schema.

## Recommended Short-Term Training Path

1. Keep `export4_position_control_v1` as the action space.
2. Generate scripted open/preshape/close/hold rollouts with metrics.
3. Add video-mapped rollouts as diagnostic data, not expert labels yet.
4. Use Shadow comparison only as a structural/behavioral reference, not as ground truth equivalence.
5. Train BC only after the action/state schema and collision proxy are signed off.

## TODO

- Add a versioned dataset writer: `export4_dataset_v0`.
- Add adapter unit tests to verify open features produce near-zero controls and close features produce tuned close controls.
- Add task-specific reward/metric definitions before RL or BC.
