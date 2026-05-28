# Mesh Export Diagnostics

## What Was Observed

- The default MuJoCo demo previously showed a large palm cube. That cube was not from SolidWorks; it was a temporary primitive `palm_link` box added in the first MJCF skeleton draft.
- The palm cube has been removed from `mjcf/hand_stage1.xml`.
- The default skeleton now uses thin palm spokes, small joint markers, and capsule phalanxes.

## STL Mesh Evidence

The exported STL files under `meshes/` show a strong warning sign:

- STL file count: 23.
- Every STL file has the same byte size: 3,955,184 bytes.
- Every STL file has the same triangle count: 79,102 triangles.
- Many files have large spans on the order of the whole hand, not just a small local part.

That is not expected for clean per-link meshes. A distal phalanx, palm, wrist link, and MCP connector should not all have exactly the same triangle count and file size.

## Current Interpretation

This strongly suggests a SolidWorks/SW2URDF export-side mesh problem: the STL files appear to carry full or broad assembly geometry in different frames, instead of clean local geometry for each URDF link.

The URDF kinematic tree itself is parseable and usable for a skeleton model, but the raw STL visuals should not be trusted as the default articulated MuJoCo visual until re-exported or fixed.

## What Was Fixed In MuJoCo

- `mjcf/hand_stage1.xml` now uses primitive geoms for a readable stage1 skeleton.
- `mjcf/hand_stage1_mesh_debug.xml` keeps the raw STL mesh version for debugging only.
- `mjcf/scene_ball.xml` includes the cleaned primitive skeleton and ball scene.

## Remaining TODO

1. In SolidWorks/SW2URDF, confirm exporter settings for per-link visual meshes.
2. Verify whether each link mesh is exported in its link-local frame, not as a full assembly snapshot.
3. Re-export a small test with only `palm_link` and one finger link to confirm STL triangle counts differ.
4. Keep `hand_stage1_mesh_debug.xml` only as a diagnostic model until clean meshes exist.
