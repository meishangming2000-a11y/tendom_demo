# Manual Per-Link Mesh Export Checklist

## Purpose

The current STL meshes are marked `suspicious_export_mesh` because all 23 STL files have identical file size and triangle count. Tomorrow's SolidWorks pass should re-export clean per-link meshes.

For each link below:

1. Open the SolidWorks assembly.
2. Show only the parts that belong to the current link rigid body.
3. Hide or suppress all other hand parts.
4. Export exactly that visible geometry as the STL for the current link.
5. Re-open the STL by itself and confirm it contains only the intended link geometry.
6. After all links are exported, check that STL file sizes and triangle counts are not all identical.

Do not rename original STEP files and do not rebuild CAD reference geometry during this pass.

## Root And Wrist

- `hand_base_link`
  - Should show: base/root hardware only.
  - Should not show: wrist middle, palm, fingers, thumb.

- `wrist_middle_link`
  - Should show: the intermediate wrist rigid body between `wrist_1_joint` and `wrist_2_joint`.
  - Should not show: hand base, palm, fingers, thumb.

- `palm_link`
  - Should show: palm rigid body and only geometry rigidly attached to the palm.
  - Should not show: separate MCP flex links, finger phalanges, thumb moving links, wrist links.

## Index Finger

- `index_mcp_flex_link`
  - Should show: index MCP flex intermediate/root link only.
  - Should not show: index proximal phalanx, inter phalanx, distal phalanx, palm, other fingers.

- `index_proximal_phalanx_link`
  - Should show: index proximal phalanx rigid body only.
  - Should not show: index MCP flex link, index proximal inter link, index distal link, other fingers.

- `index_proximal_inter_link`
  - Should show: index intermediate/proximal-inter rigid body only.
  - Should not show: index proximal phalanx or distal link.

- `index_distal_link`
  - Should show: index distal phalanx/fingertip rigid body only.
  - Should not show: any other index segment or palm.

## Middle Finger

- `middle_mcp_flex_link`
  - Should show: middle MCP flex intermediate/root link only.
  - Should not show: middle proximal phalanx, inter phalanx, distal phalanx, palm, other fingers.

- `middle_proximal_phalanx_link`
  - Should show: middle proximal phalanx rigid body only.
  - Should not show: middle MCP flex link, middle proximal inter link, middle distal link, other fingers.

- `middle_proximal_inter_link`
  - Should show: middle intermediate/proximal-inter rigid body only.
  - Should not show: middle proximal phalanx or distal link.

- `middle_distal_link`
  - Should show: middle distal phalanx/fingertip rigid body only.
  - Should not show: any other middle segment or palm.

## Ring Finger

- `ring_mcp_flex_link`
  - Should show: ring MCP flex intermediate/root link only.
  - Should not show: ring proximal phalanx, inter phalanx, distal phalanx, palm, other fingers.

- `ring_proximal_phalanx_link`
  - Should show: ring proximal phalanx rigid body only.
  - Should not show: ring MCP flex link, ring proximal inter link, ring distal link, other fingers.

- `ring_proximal_inter_link`
  - Should show: ring intermediate/proximal-inter rigid body only.
  - Should not show: ring proximal phalanx or distal link.

- `ring_distal_link`
  - Should show: ring distal phalanx/fingertip rigid body only.
  - Should not show: any other ring segment or palm.

## Little Finger

- `little_mcp_flex_link`
  - Should show: little MCP flex intermediate/root link only.
  - Should not show: little proximal phalanx, inter phalanx, distal phalanx, palm, other fingers.

- `little_proximal_phalanx_link`
  - Should show: little proximal phalanx rigid body only.
  - Should not show: little MCP flex link, little proximal inter link, little distal link, other fingers.

- `little_proximal_inter_link`
  - Should show: little intermediate/proximal-inter rigid body only.
  - Should not show: little proximal phalanx or distal link.

- `little_distal_link`
  - Should show: little distal phalanx/fingertip rigid body only.
  - Should not show: any other little segment or palm.

## Thumb

- `thumb_root_connector_link`
  - Should show: fixed thumb root connector rigid body only.
  - Should not show: palm, thumb metacarpal, thumb proximal, thumb distal.

- `thumb_metacarpal_link`
  - Should show: thumb metacarpal rigid body only.
  - Should not show: root connector, proximal, distal, palm.

- `thumb_proximal_link`
  - Should show: thumb proximal rigid body only.
  - Should not show: metacarpal, distal, palm.

- `thumb_distal_link`
  - Should show: thumb distal/fingertip rigid body only.
  - Should not show: proximal, metacarpal, palm.

## Post-Export Sanity Checks

- `palm_link.STL` should visibly contain a palm and no full fingers.
- `index_distal_link.STL` should visibly contain only one small distal index segment.
- `hand_base_link.STL` should visibly contain only the root/base.
- STL file sizes should differ across large and small links.
- Triangle counts should differ across large and small links.
- If all STL files still have identical file size or identical triangle count, stop and review the export workflow before trying MuJoCo again.

## Expected Output Names

Keep the URDF link-name based filenames:

- `hand_base_link.STL`
- `wrist_middle_link.STL`
- `palm_link.STL`
- `index_mcp_flex_link.STL`
- `index_proximal_phalanx_link.STL`
- `index_proximal_inter_link.STL`
- `index_distal_link.STL`
- `middle_mcp_flex_link.STL`
- `middle_proximal_phalanx_link.STL`
- `middle_proximal_inter_link.STL`
- `middle_distal_link.STL`
- `ring_mcp_flex_link.STL`
- `ring_proximal_phalanx_link.STL`
- `ring_proximal_inter_link.STL`
- `ring_distal_link.STL`
- `little_mcp_flex_link.STL`
- `little_proximal_phalanx_link.STL`
- `little_proximal_inter_link.STL`
- `little_distal_link.STL`
- `thumb_root_connector_link.STL`
- `thumb_metacarpal_link.STL`
- `thumb_proximal_link.STL`
- `thumb_distal_link.STL`
