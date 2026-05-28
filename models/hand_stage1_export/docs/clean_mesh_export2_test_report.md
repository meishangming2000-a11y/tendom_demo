# Clean Mesh Test Report

- Clean mesh test directory: `D:\tendon_project\simulations\models\hand_stage1_export\clean_mesh_test_export2`
- STL count: 23
- Unique file size count: 18
- Unique triangle count: 18
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
- `thumb_root_connector_link` STL part count: 1

Thumb root connector files mapped to `thumb_root_connector_link` body:

- `thumb_root_connector_link.STL`

## Oversize / Whole-Hand Checks

- BBox over 300 mm count: 0
- BBox over 300 mm files: []

## Per-File Diagnostics

| File | MJCF file | Logical link | Size bytes | Triangles | BBox span xyz | SHA-256 prefix | Exact duplicate group |
|---|---|---|---:|---:|---|---|---|
| `hand_base_link.STL` | `hand_base_link.STL` | `hand_base_link` | 143484 | 2868 | `0.0489106, 0.0399486, 0.02` | `b19f6fe0bcfce304` | no |
| `index_distal_link.STL` | `index_distal_link.STL` | `index_distal_link` | 252584 | 5050 | `0.025308, 0.0309574, 0.018187` | `2d00873921edcc94` | no |
| `index_mcp_flex_link.STL` | `index_mcp_flex_link.STL` | `index_mcp_flex_link` | 72284 | 1444 | `0.0185931, 0.019768, 0.0145335` | `b7b8a93d8c886079` | no |
| `index_proximal_inter_link.STL` | `index_proximal_inter_link.STL` | `index_proximal_inter_link` | 108584 | 2170 | `0.024304, 0.042192, 0.0176963` | `31dd92c74c8e44e9` | no |
| `index_proximal_phalanx_link.STL` | `index_proximal_phalanx_link.STL` | `index_proximal_phalanx_link` | 120184 | 2402 | `0.0165929, 0.0489992, 0.0179605` | `1ee5ce4cfb4d123e` | no |
| `little_distal_link.STL` | `little_distal_link.STL` | `little_distal_link` | 252084 | 5040 | `0.032877, 0.0199002, 0.0179976` | `ddf44064a69cd921` | no |
| `little_mcp_flex_link.STL` | `little_mcp_flex_link.STL` | `little_mcp_flex_link` | 72284 | 1444 | `0.0198742, 0.0205096, 0.0145335` | `137785a87ee37f8d` | no |
| `little_proximal_inter_link.STL` | `little_proximal_inter_link.STL` | `little_proximal_inter_link` | 101184 | 2022 | `0.0166349, 0.0389814, 0.0176084` | `c551cbe29649ffeb` | no |
| `little_proximal_phalanx_link.STL` | `little_proximal_phalanx_link.STL` | `little_proximal_phalanx_link` | 119684 | 2392 | `0.04898, 0.0173413, 0.0179605` | `55b2a600f4add9ad` | no |
| `middle_distal_link.STL` | `middle_distal_link.STL` | `middle_distal_link` | 252584 | 5050 | `0.0332639, 0.0186581, 0.0179976` | `a1ffb944483be102` | no |
| `middle_mcp_flex_link.STL` | `middle_mcp_flex_link.STL` | `middle_mcp_flex_link` | 72284 | 1444 | `0.0187298, 0.0198498, 0.0145335` | `aae059f7612fc835` | no |
| `middle_proximal_inter_link.STL` | `middle_proximal_inter_link.STL` | `middle_proximal_inter_link` | 103584 | 2070 | `0.0489727, 0.0170826, 0.0176669` | `779009bae937a73f` | no |
| `middle_proximal_phalanx_link.STL` | `middle_proximal_phalanx_link.STL` | `middle_proximal_phalanx_link` | 110784 | 2214 | `0.0589021, 0.0187383, 0.0177113` | `533963988a85908e` | no |
| `palm_link.STL` | `palm_link.STL` | `palm_link` | 977984 | 19558 | `0.035357, 0.105837, 0.0822411` | `2e5ec970631df7de` | no |
| `ring_distal_link.STL` | `ring_distal_link.STL` | `ring_distal_link` | 257784 | 5154 | `0.0326149, 0.0206092, 0.0179976` | `4df63def79856851` | no |
| `ring_mcp_flex_link.STL` | `ring_mcp_flex_link.STL` | `ring_mcp_flex_link` | 72284 | 1444 | `0.0189712, 0.0199906, 0.0145335` | `049ae24007bb8502` | no |
| `ring_proximal_inter_link.STL` | `ring_proximal_inter_link.STL` | `ring_proximal_inter_link` | 107384 | 2146 | `0.0189558, 0.0437306, 0.017732` | `cf413a7f89957068` | no |
| `ring_proximal_phalanx_link.STL` | `ring_proximal_phalanx_link.STL` | `ring_proximal_phalanx_link` | 111884 | 2236 | `0.0539178, 0.0182035, 0.0175963` | `4315d1bdd067cf47` | no |
| `thumb_distal_link.STL` | `thumb_distal_link.STL` | `thumb_distal_link` | 193484 | 3868 | `0.0160657, 0.0411037, 0.02` | `15c357ec2405c50e` | no |
| `thumb_metacarpal_link.STL` | `thumb_metacarpal_link.STL` | `thumb_metacarpal_link` | 116784 | 2334 | `0.0312277, 0.0584031, 0.0205455` | `9136379967852696` | no |
| `thumb_proximal_link.STL` | `thumb_proximal_link.STL` | `thumb_proximal_link` | 103584 | 2070 | `0.0172834, 0.0458099, 0.0208134` | `669db0611c4bcea1` | no |
| `thumb_root_connector_link.STL` | `thumb_root_connector_link.STL` | `thumb_root_connector_link` | 201584 | 4030 | `0.018, 0.018, 0.0165341` | `22a8d4e3fc041422` | no |
| `wrist_middle_link.STL` | `wrist_middle_link.STL` | `wrist_middle_link` | 32684 | 652 | `0.056, 0.0257639, 0.03` | `0aaaf079579cd1e7` | no |

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
- thumb_root_connector_link_part_count: 1
- thumb_root_connector_link_files: ['thumb_root_connector_link.STL']
- oversized_bbox_over_300mm_count: 0
- oversized_bbox_over_300mm_files: []

## Interpretation

- A clean per-link export should have different file sizes, triangle counts, and bounding boxes across large and small links.
- `palm_link` should be palm-sized; `index_distal_link` should be much smaller than `palm_link`; `hand_base_link` should not look identical to either.
- Current suspicious exports are still not used by the primitive model.
