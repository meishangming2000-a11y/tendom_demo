# SolidWorks Thumb Axis Checklist

Context: current MuJoCo stage1 hand loads and the four long fingers can perform a useful position-control grasp smoke test. Thumb opposition is still the main blocker. Do not rename joints or rebuild the tree during this check; only verify the SolidWorks reference geometry and exported URDF semantics.

## Thumb Chain To Verify

Expected chain:

```text
palm_link
-> thumb_root_connector_fixed_joint
-> thumb_root_connector_link
-> thumb_cmc_joint
-> thumb_metacarpal_link
-> thumb_mcp_joint
-> thumb_proximal_link
-> thumb_ip_joint
-> thumb_distal_link
```

## Axis Checks

- `thumb_cmc_axis` should pass through the real CMC rotation center.
- Positive `thumb_cmc_axis` rotation should move the thumb toward the palm/index side for opposition, or the intended opposite direction must be explicitly documented.
- `thumb_mcp_axis` should correspond to thumb proximal flexion, not an unintended lateral sweep.
- `thumb_ip_axis` should correspond to distal thumb flexion.
- Confirm whether the current `thumb_cmc_joint` is expected to be the main opposition sweep joint or only one component of a compound CMC motion.
- Check whether any thumb joint axis is mirrored because of right/left hand assembly orientation or exported CSYS handedness.

## CSYS Checks

- `thumb_cmc_csys` Z axis should align with the intended CMC hinge axis if the exporter uses local Z as joint axis.
- `thumb_mcp_csys` Z axis should align with the intended MCP hinge axis.
- `thumb_ip_csys` Z axis should align with the intended IP hinge axis.
- Confirm each CSYS origin is at the physical hinge center, not at a part origin, mate reference, or assembly/world origin.
- Verify CSYS orientation after export by checking URDF joint `axis`, `origin xyz`, and `origin rpy` against the SolidWorks reference.

## Parent/Child And Body Checks

- `thumb_root_connector_fixed_joint` should be fixed from `palm_link` to `thumb_root_connector_link`.
- `thumb_cmc_joint` should parent `thumb_root_connector_link` and child `thumb_metacarpal_link`.
- `thumb_mcp_joint` should parent `thumb_metacarpal_link` and child `thumb_proximal_link`.
- `thumb_ip_joint` should parent `thumb_proximal_link` and child `thumb_distal_link`.
- Confirm `thumb_root_connector_link` is not accidentally carrying movable metacarpal geometry.
- Confirm D18d12H4 / Trapezium / Os metacarpale parts belong to the intended link:
  - D18d12H4: TODO confirm whether this is connector/bushing geometry for `thumb_root_connector_link`.
  - Trapezium parts: TODO confirm whether these should remain fixed to palm/root connector or be part of CMC moving body.
  - Os metacarpale: TODO confirm whether this belongs to `thumb_metacarpal_link`.

## Manual Motion Test In SolidWorks

- Suppress or isolate all non-thumb moving mates except the thumb chain.
- Rotate `thumb_cmc_axis` by a small positive angle and verify thumb tip moves toward palm/index/ball-side direction.
- Rotate `thumb_cmc_axis` by a small negative angle and compare which direction is physically intended.
- Rotate `thumb_mcp_axis` positive and verify proximal thumb flexion.
- Rotate `thumb_ip_axis` positive and verify distal thumb flexion.
- Record the intended positive direction for each joint before re-exporting.

## Re-export Notes

- Keep joint names unchanged for now.
- Do not export assembly/world STL as final per-link mesh; export body-local clean per-link STL if visual meshes are regenerated.
- If axis fixes require CSYS edits, re-export URDF and meshes together so joint origins and visuals stay consistent.
- TODO: after re-export, rerun `thumb_opposition_audit.py` and `analyze_thumb_mechanical_semantics.py`.
