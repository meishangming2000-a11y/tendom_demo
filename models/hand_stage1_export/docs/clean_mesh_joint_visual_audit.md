# Clean Mesh Joint Visual Audit

## Inputs

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_draft.xml`
- Render directory: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks\joint_motion`
- Positive test angle: `+0.2 rad`, clamped by each joint limit.

## Rendered Joints

- `wrist_1_joint`
- `wrist_2_joint`
- `index_mcp_flex_joint`
- `index_mcp_abd_joint`
- `index_pip_joint`
- `index_dip_joint`
- `middle_mcp_flex_joint`
- `ring_mcp_flex_joint`
- `little_mcp_flex_joint`
- `thumb_cmc_joint`
- `thumb_mcp_joint`
- `thumb_ip_joint`

Each joint directory contains:

- `before.png`
- `after_positive_angle.png`

## Overall Conclusion

**FAIL for clean mesh joint-motion visual validation.**

The joints move numerically and the primitive skeleton follows the expected kinematic chain, but the clean mesh visual geoms are already offset from the joint tree in the neutral pose. Because of that, axis direction and hinge placement cannot be reliably judged from the clean STL visuals.

## Observations

- `index_mcp_abd_joint`: before/after images show motion in the corresponding kinematic chain, but clean mesh finger parts are detached from the primitive index chain. The clean mesh cannot be used to validate MCP axis semantics yet.
- `thumb_cmc_joint`: the primitive thumb moves, but thumb-root clean STL parts do not form a trustworthy continuous palm-to-thumb visual chain. Thumb opposition direction remains TODO.
- `wrist_1_joint` / `wrist_2_joint`: whole hand kinematics remain finite, but floating clean mesh pieces make visual rotation hard to interpret.
- Long-finger MCP samples: some clean mesh parts move with their body, but their neutral offsets are large enough that the motion looks like detached CAD chunks moving near the hand rather than link-local phalanx geometry.

## Issue Severity

- BLOCKER: Clean mesh geoms are not aligned to body-local link frames, so clean mesh joint visual audit is not valid.
- MAJOR: `mcp_flex` / `mcp_abd` semantic review cannot be resolved using the current clean mesh visuals.
- MAJOR: Thumb CMC/MCP/IP visual direction cannot be accepted using current clean STL placement.
- MINOR: Numeric joint smoke test still passes and remains useful for kinematic sanity.

## Recommendation

- Keep using primitive screenshots and numeric joint smoke tests for tonight's scripted grasp logic.
- Re-run this visual audit after CAD/export correction or after a verified assembly-to-body-local mesh transform is applied.
- Do not rename `mcp_flex` / `mcp_abd` based on current clean mesh screenshots.
