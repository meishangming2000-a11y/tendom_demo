# Real Mesh Replacement Plan

## Current Policy

- Do not use the current SolidWorks/SW2URDF STL files as real CAD visual meshes.
- Current STL files are classified as `suspicious_export_mesh`.
- `hand_stage1_primitive.xml` remains the default MuJoCo model for kinematic validation.
- `hand_stage1_mesh_debug.xml` is diagnostic only.

## Replacement Target

After clean per-link STL files are re-exported, create a real-mesh MJCF variant without changing the URDF joint tree:

- Keep the same body tree as `hand_stage1_primitive.xml`.
- Keep the same hinge joint names, axes, and limits.
- Replace primitive visual geoms with clean mesh visual geoms.
- Add or keep simple primitive collision geoms until mesh collision quality is verified.
- Keep fingertip sites from the primitive model.

## Primitive Link To Future Clean STL

| Primitive body/link | Future clean STL |
|---|---|
| `hand_base_link` | `meshes/hand_base_link.STL` |
| `wrist_middle_link` | `meshes/wrist_middle_link.STL` |
| `palm_link` | `meshes/palm_link.STL` |
| `index_mcp_flex_link` | `meshes/index_mcp_flex_link.STL` |
| `index_proximal_phalanx_link` | `meshes/index_proximal_phalanx_link.STL` |
| `index_proximal_inter_link` | `meshes/index_proximal_inter_link.STL` |
| `index_distal_link` | `meshes/index_distal_link.STL` |
| `middle_mcp_flex_link` | `meshes/middle_mcp_flex_link.STL` |
| `middle_proximal_phalanx_link` | `meshes/middle_proximal_phalanx_link.STL` |
| `middle_proximal_inter_link` | `meshes/middle_proximal_inter_link.STL` |
| `middle_distal_link` | `meshes/middle_distal_link.STL` |
| `ring_mcp_flex_link` | `meshes/ring_mcp_flex_link.STL` |
| `ring_proximal_phalanx_link` | `meshes/ring_proximal_phalanx_link.STL` |
| `ring_proximal_inter_link` | `meshes/ring_proximal_inter_link.STL` |
| `ring_distal_link` | `meshes/ring_distal_link.STL` |
| `little_mcp_flex_link` | `meshes/little_mcp_flex_link.STL` |
| `little_proximal_phalanx_link` | `meshes/little_proximal_phalanx_link.STL` |
| `little_proximal_inter_link` | `meshes/little_proximal_inter_link.STL` |
| `little_distal_link` | `meshes/little_distal_link.STL` |
| `thumb_root_connector_link` | `meshes/thumb_root_connector_link.STL` |
| `thumb_metacarpal_link` | `meshes/thumb_metacarpal_link.STL` |
| `thumb_proximal_link` | `meshes/thumb_proximal_link.STL` |
| `thumb_distal_link` | `meshes/thumb_distal_link.STL` |

## Manual Re-Export Checklist Reference

Use `docs/manual_per_link_mesh_export_checklist.md`. Each STL should contain only the SolidWorks parts assigned to that link:

- root/base geometry only for `hand_base_link`
- wrist middle geometry only for `wrist_middle_link`
- palm rigid geometry only for `palm_link`
- one rigid segment per finger link
- one rigid segment per thumb link

Hide all unrelated parts before exporting each STL.

## MJCF Replacement Steps

1. Keep `hand_stage1_primitive.xml` unchanged as the working skeleton baseline.
2. Create a new file such as `mjcf/hand_stage1_real_mesh.xml`.
3. Add a compiler mesh directory:

```xml
<compiler angle="radian" meshdir="../meshes" autolimits="true"/>
```

4. Add one mesh asset per clean STL:

```xml
<asset>
  <mesh name="palm_link_mesh" file="palm_link.STL"/>
</asset>
```

5. Under each body, add visual mesh geoms while keeping simple primitive collision geoms:

```xml
<geom name="palm_link_visual" type="mesh" mesh="palm_link_mesh"
      contype="0" conaffinity="0" group="2"/>
```

6. Keep fingertip sites on distal bodies:

```xml
<site name="index_tip_site" .../>
```

7. Load the real-mesh MJCF in MuJoCo and compare against `hand_stage1_primitive.xml`.

## Acceptance Criteria For New STL

- Different link STL files should not all have identical file sizes.
- Different link STL files should not all have identical triangle counts.
- Opening `palm_link.STL` alone should show only palm geometry.
- Opening `index_distal_link.STL` alone should show only the index distal segment.
- Articulating one joint in MuJoCo should move only that link subtree, not duplicate the whole hand.

## TODO

- TODO: confirm final link-local mesh origins after re-export.
- TODO: decide whether clean STL meshes should be visual-only while primitive geoms remain collision.
- TODO: add a side-by-side primitive vs real-mesh visual check once clean per-link meshes exist.
