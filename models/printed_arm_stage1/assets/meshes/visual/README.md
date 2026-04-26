# Visual Mesh Assets

These assets now include formal Stage 1 main visuals, retained reference candidates, and a remaining placeholder logic asset.

Current files:

- `unit_box.obj`
- `pa_base.stl`
- `pa_j1_link.stl`
- `pa_j3_link.stl`
- `pa_j4_link_main.stl`
- `pa_j4_link_aux.stl`
- `pa_j4_link_cover.stl`
- `pa_j5_fixed.stl`
- `pa_j5_fixed_support.stl`
- `pa_ee_mount.stl`

Current semantic grouping:

- main-chain visuals: `pa_base.stl`, `pa_j1_link.stl`, `pa_j3_link.stl`, `pa_j4_link_main.stl`, `pa_j4_link_aux.stl`, `pa_j4_link_cover.stl`, `pa_j5_fixed_support.stl`, `pa_ee_mount.stl`
- reference candidate visual: `pa_j5_fixed.stl`, kept on disk with its legacy filename but currently interpreted as `pa_j5_rotating_output_candidate`
- placeholder logic asset: `unit_box.obj`, still used for `pa_j2_carriage`

Planned replacement path:

- export cleaned CAD-derived visual meshes from the printed assembly
- keep filenames ASCII-safe
- update `robot.xml` asset names in place instead of renaming bodies or joints
- preserve assembly-frame exports by recording any visual-only compensation in model metadata
- `pa_j4_link_main.stl`, `pa_j4_link_aux.stl`, and `pa_j4_link_cover.stl` are currently treated together as the main Stage 1 `pa_j4_link` visual assembly
- `pa_j3_link.stl` is currently treated as the part directly coupled to the motor inside the lowest fixed support
- `pa_j5_fixed.stl` is a preserved legacy import whose current semantics are closer to `pa_j5_rotating_output_candidate`
- `pa_j5_fixed_support.stl` is the current Stage 1 fixed-side support / bracket main visual copied from the latest hardware export
