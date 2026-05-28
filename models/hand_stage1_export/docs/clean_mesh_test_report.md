# Clean Mesh Test Report

- Clean mesh test directory: `D:\tendon_project\simulations\models\hand_stage1_export\clean_mesh_test`
- STL count: 25
- Unique file size count: 20
- Unique triangle count: 20
- Duplicate exact STL groups: 0
- More credible than `suspicious_export_mesh`: yes
- Overall pass: yes

## Expected Link Coverage

- Expected clean per-link STL count: 23
- Present expected links: 23
- Missing expected links: 0

## Thumb Mesh Mapping

- `thumb_metacarpal_link` present: True
- `thumb_proximal_link` present: True
- `thumb_distal_link` present: True
- `thumb_root_connector_link` STL part count: 3

Thumb root connector files mapped to `thumb_root_connector_link` body:

- `thumb_root_connector_link - hand 装配(1).STEP-1 D18d12H4.STEP-1.STL`
- `thumb_root_connector_link - hand 装配(1).STEP-1 Trapezium1.STEP-1.STL`
- `thumb_root_connector_link - hand 装配(1).STEP-1 Trapezium3.STEP-1.STL`

## Oversize / Whole-Hand Checks

- BBox over 300 mm count: 0
- BBox over 300 mm files: []

## Per-File Diagnostics

| File | MJCF file | Logical link | Size bytes | Triangles | BBox span xyz | SHA-256 prefix | Exact duplicate group |
|---|---|---|---:|---:|---|---|---|
| `hand_base_link.STL` | `hand_base_link.STL` | `hand_base_link` | 143484 | 2868 | `48.9426, 24.7744, 39.3461` | `a65d10279446ef51` | no |
| `index_distal_link.STL` | `index_distal_link.STL` | `index_distal_link` | 252584 | 5050 | `17.9718, 34.3988, 14.7605` | `238b49f685859ddf` | no |
| `index_mcp_flex_link.STL` | `index_mcp_flex_link.STL` | `index_mcp_flex_link` | 72284 | 1444 | `18.5931, 19.768, 14.5335` | `0edf8f31ae0a82de` | no |
| `index_proximal_inter_link.STL` | `index_proximal_inter_link.STL` | `index_proximal_inter_link` | 108584 | 2170 | `18.9092, 43.5212, 18.3298` | `81b4981541d0e1f6` | no |
| `index_proximal_phalanx_link.STL` | `index_proximal_phalanx_link.STL` | `index_proximal_phalanx_link` | 120184 | 2402 | `19.389, 49.7186, 16.5929` | `c04ee967e90d32a6` | no |
| `little_distal_link.STL` | `little_distal_link.STL` | `little_distal_link` | 252084 | 5040 | `18.8476, 33.5083, 19.9002` | `e5e36943b587d09b` | no |
| `little_mcp_flex_link.STL` | `little_mcp_flex_link.STL` | `little_mcp_flex_link` | 72284 | 1444 | `19.8742, 20.5097, 14.5335` | `3c04adc6977db8d3` | no |
| `little_proximal_inter_link.STL` | `little_proximal_inter_link.STL` | `little_proximal_inter_link` | 101184 | 2022 | `21.677, 41.0319, 16.6349` | `dfbd152a60a7bf40` | no |
| `little_proximal_phalanx_link.STL` | `little_proximal_phalanx_link.STL` | `little_proximal_phalanx_link` | 119684 | 2392 | `23.7284, 50.8864, 17.3413` | `89d4008196e7f7f1` | no |
| `middle_distal_link.STL` | `middle_distal_link.STL` | `middle_distal_link` | 252584 | 5050 | `17.9642, 33.6002, 18.6581` | `8f23eb753bf72d9f` | no |
| `middle_mcp_flex_link.STL` | `middle_mcp_flex_link.STL` | `middle_mcp_flex_link` | 72284 | 1444 | `18.7298, 19.8499, 14.5335` | `e68f49ec9ca3eaa8` | no |
| `middle_proximal_inter_link.STL` | `middle_proximal_inter_link.STL` | `middle_proximal_inter_link` | 103584 | 2070 | `19.6532, 49.8368, 17.0826` | `9bad4562b029edd6` | no |
| `middle_proximal_phalanx_link.STL` | `middle_proximal_phalanx_link.STL` | `middle_proximal_phalanx_link` | 110784 | 2214 | `20.3643, 59.743, 18.7383` | `9bd35a43bf1ea2dc` | no |
| `palm_link.STL` | `palm_link.STL` | `palm_link` | 977984 | 19558 | `82.2411, 105.837, 35.357` | `6ea0aad9f47df722` | no |
| `ring_distal_link.STL` | `ring_distal_link.STL` | `ring_distal_link` | 257784 | 5154 | `17.943, 33.0367, 20.6092` | `fa15302e158bfbbb` | no |
| `ring_mcp_flex_link.STL` | `ring_mcp_flex_link.STL` | `ring_mcp_flex_link` | 72284 | 1444 | `18.9712, 19.9906, 14.5335` | `16b25a86f0e67109` | no |
| `ring_proximal_inter_link.STL` | `ring_proximal_inter_link.STL` | `ring_proximal_inter_link` | 107384 | 2146 | `20.0028, 44.8658, 18.9558` | `84732bf610607621` | no |
| `ring_proximal_phalanx_link.STL` | `ring_proximal_phalanx_link.STL` | `ring_proximal_phalanx_link` | 111884 | 2236 | `20.8548, 55.0142, 18.2035` | `cc90277a41156ea1` | no |
| `thumb_distal_link.STL` | `thumb_distal_link.STL` | `thumb_distal_link` | 193484 | 3868 | `16.2612, 35.1982, 34.5889` | `fad34f036d58e677` | no |
| `thumb_metacarpal_link.STL` | `thumb_metacarpal_link.STL` | `thumb_metacarpal_link` | 116784 | 2334 | `30.9984, 54.0631, 49.676` | `0d5e5bc3e6f54054` | no |
| `thumb_proximal_link.STL` | `thumb_proximal_link.STL` | `thumb_proximal_link` | 103584 | 2070 | `18.8891, 44.3824, 43.1467` | `c2b3751ad131eb82` | no |
| `thumb_root_connector_link - hand 装配(1).STEP-1 D18d12H4.STEP-1.STL` | `thumb_root_connector_link_707ff91f.STL` | `thumb_root_connector_link` | 41684 | 832 | `18.035, 14.9617, 15.6982` | `707ff91f1939809a` | no |
| `thumb_root_connector_link - hand 装配(1).STEP-1 Trapezium1.STEP-1.STL` | `thumb_root_connector_link_b6051f81.STL` | `thumb_root_connector_link` | 38484 | 768 | `17.0465, 12.9443, 15.2038` | `b6051f8180a437a6` | no |
| `thumb_root_connector_link - hand 装配(1).STEP-1 Trapezium3.STEP-1.STL` | `thumb_root_connector_link_36a50eba.STL` | `thumb_root_connector_link` | 121584 | 2430 | `17.235, 16.6481, 16.9742` | `36a50eba5f344f78` | no |
| `wrist_middle_link.STL` | `wrist_middle_link.STL` | `wrist_middle_link` | 32684 | 652 | `56, 28.0445, 32.1578` | `664f7388a8b0de16` | no |

## Special Checks

- palm_link_present: True
- index_distal_link_present: True
- hand_base_link_present: True
- index_distal_smaller_than_palm_by_volume: True
- index_distal_smaller_than_palm_by_max_span: True
- hand_base_not_identical_to_palm: True
- hand_base_not_identical_to_index_distal: True
- thumb_metacarpal_link_present: True
- thumb_proximal_link_present: True
- thumb_distal_link_present: True
- thumb_root_connector_link_part_count: 3
- thumb_root_connector_link_files: ['thumb_root_connector_link - hand 装配(1).STEP-1 D18d12H4.STEP-1.STL', 'thumb_root_connector_link - hand 装配(1).STEP-1 Trapezium1.STEP-1.STL', 'thumb_root_connector_link - hand 装配(1).STEP-1 Trapezium3.STEP-1.STL']
- oversized_bbox_over_300mm_count: 0
- oversized_bbox_over_300mm_files: []

## Interpretation

- A clean per-link export should have different file sizes, triangle counts, and bounding boxes across large and small links.
- `palm_link` should be palm-sized; `index_distal_link` should be much smaller than `palm_link`; `hand_base_link` should not look identical to either.
- Current suspicious exports are still not used by the primitive model.
