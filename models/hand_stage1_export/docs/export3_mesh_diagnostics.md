# Export3 Mesh Diagnostics

- Mesh directory: `D:\tendon_project\simulations\models\hand_stage1_export\export3\meshes`
- STL count: 24
- Unique file size count: 19
- Unique triangle count: 19
- Exact duplicate hash groups: 0
- All size/triangle identical: no
- More credible than suspicious mesh: yes
- Overall pass: yes
- MJCF mesh scale selected: `1 1 1`

## Special Checks

- `palm_link` present: True, bbox span `[0.035356984473764896, 0.10583710134960711, 0.08224114775657654]`
- `index_distal_link` present: True, bbox span `[0.025308015756309032, 0.030957377050071955, 0.01818703208118677]`
- `index_distal_link` smaller than `palm_link` by max span: True
- `index_distal_link` smaller than `palm_link` by volume: True
- `hand_base_link` present: True, bbox span `[0.04891063645482063, 0.039948564022779465, 0.01999999955296517]`
- `hand_base_link` not identical to `palm_link`: True
- `thumb_trapezium1_link` present: True
- `thumb_root_connector_link` present: True
- `thumb_metacarpal_link` present: True
- `thumb_proximal_link` present: True
- `thumb_distal_link` present: True

## Per Mesh

| File | Size bytes | Triangles | BBox span xyz | SHA-256 prefix | Duplicate group |
|---|---:|---:|---|---|---|
| `hand_base_link.STL` | 143484 | 2868 | `0.0489106, 0.0399486, 0.02` | `b19f6fe0bcfce304` | no |
| `index_distal_link.STL` | 252584 | 5050 | `0.025308, 0.0309574, 0.018187` | `2d00873921edcc94` | no |
| `index_mcp_flex_link.STL` | 72284 | 1444 | `0.0185931, 0.019768, 0.0145335` | `b7b8a93d8c886079` | no |
| `index_proximal_inter_link.STL` | 108584 | 2170 | `0.024304, 0.042192, 0.0176963` | `31dd92c74c8e44e9` | no |
| `index_proximal_phalanx_link.STL` | 120184 | 2402 | `0.0165929, 0.0489992, 0.0179605` | `1ee5ce4cfb4d123e` | no |
| `little_distal_link.STL` | 252084 | 5040 | `0.032877, 0.0199002, 0.0179976` | `ddf44064a69cd921` | no |
| `little_mcp_flex_link.STL` | 72284 | 1444 | `0.0198742, 0.0205096, 0.0145335` | `137785a87ee37f8d` | no |
| `little_proximal_inter_link.STL` | 101184 | 2022 | `0.0166349, 0.0389814, 0.0176084` | `c551cbe29649ffeb` | no |
| `little_proximal_phalanx_link.STL` | 119684 | 2392 | `0.04898, 0.0173413, 0.0179605` | `55b2a600f4add9ad` | no |
| `middle_distal_link.STL` | 252584 | 5050 | `0.0332639, 0.0186581, 0.0179976` | `a1ffb944483be102` | no |
| `middle_mcp_flex_link.STL` | 72284 | 1444 | `0.0187298, 0.0198498, 0.0145335` | `aae059f7612fc835` | no |
| `middle_proximal_inter_link.STL` | 103584 | 2070 | `0.0489727, 0.0170826, 0.0176669` | `779009bae937a73f` | no |
| `middle_proximal_phalanx_link.STL` | 110784 | 2214 | `0.0589021, 0.0187383, 0.0177113` | `533963988a85908e` | no |
| `palm_link.STL` | 977984 | 19558 | `0.035357, 0.105837, 0.0822411` | `2e5ec970631df7de` | no |
| `ring_distal_link.STL` | 257784 | 5154 | `0.0326149, 0.0206092, 0.0179976` | `4df63def79856851` | no |
| `ring_mcp_flex_link.STL` | 72284 | 1444 | `0.0189712, 0.0199906, 0.0145335` | `049ae24007bb8502` | no |
| `ring_proximal_inter_link.STL` | 107384 | 2146 | `0.0189558, 0.0437306, 0.017732` | `cf413a7f89957068` | no |
| `ring_proximal_phalanx_link.STL` | 111884 | 2236 | `0.0539178, 0.0182035, 0.0175963` | `4315d1bdd067cf47` | no |
| `thumb_distal_link.STL` | 193484 | 3868 | `0.0160657, 0.0411037, 0.02` | `15c357ec2405c50e` | no |
| `thumb_metacarpal_link.STL` | 116784 | 2334 | `0.0525043, 0.049676, 0.03358` | `5136bc9d505c7d12` | no |
| `thumb_proximal_link.STL` | 103584 | 2070 | `0.0172834, 0.0458099, 0.0208134` | `669db0611c4bcea1` | no |
| `thumb_root_connector_link.STL` | 163184 | 3262 | `0.018, 0.018, 0.0154` | `5618dfb3d49302a8` | no |
| `thumb_trapezium1_link.STL` | 38484 | 768 | `0.0170512, 0.0106708, 0.0109` | `f971a148f99f27c1` | no |
| `wrist_middle_link.STL` | 32684 | 652 | `0.056, 0.0257639, 0.03` | `0aaaf079579cd1e7` | no |

## Notes

- Export3 meshes are copied to `meshes_export3` only when this diagnostics pass is credible.
- No old suspicious mesh directory is used.
