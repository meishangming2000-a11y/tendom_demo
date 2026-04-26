# printed_arm_stage1

Stage 1 placeholder body for the printed arm.

Current scope:

- loadable MuJoCo body with a named link/joint tree
- mixed visual meshes: CAD-derived main-chain visuals for `pa_base`, `pa_j1_link`, `pa_j3_link`, `pa_j4_link`, `pa_j5_fixed_support`, and `pa_ee_mount`, plus the retained `pa_j5` rotating-side reference visual and the remaining `pa_j2_carriage` placeholder
- explicit `pa_ee_mount` body and `pa_ee_mount_site`
- metadata placeholders for CAD export, mount calibration, and future action layout

Current non-goals:

- no full CAD-derived link set yet
- no custom environment wiring yet
- no tendon routing
- no dynamics calibration claim

Recommended entry:

- `scene.xml`
- `docs/stage1_interface_freeze_checklist.md`
- `docs/stage1_coordinate_interface_stabilization.md`

Stage 1 semantic grouping:

- formal main visual chain: `pa_base`, `pa_j1_link`, `pa_j3_link`, the three-part `pa_j4_link` visual assembly, `pa_j5_fixed_support`, and `pa_ee_mount`
- reference/candidate visual: `pa_j5_rotating_output_candidate`, retained as a rotating-side reference visual and not the fixed-side primary meaning
- placeholder logic layer: `pa_j2_carriage`, still represented by `unit_box.obj` until a discrete CAD visual is confirmed
- Stage 1 does not require a strict one-to-one mapping between CAD visual parts and the body tree

Notes:

- `pa_base` now loads from `assets/meshes/visual/pa_base.stl` with `1 mm -> 0.001 m` scaling
- `pa_j1_link` now loads from `assets/meshes/visual/pa_j1_link.stl` with a Stage 1 `Rz(180deg)` visual correction to match the current positive-X chain direction
- `pa_j3_link` now loads from `assets/meshes/visual/pa_j3_link.stl`; it is currently interpreted as the part directly coupled to the motor inside the lowest fixed support
- `pa_j4_link` is now treated as a three-part main visual assembly: `pa_j4_link_main.stl` as the cylindrical motor shell, `pa_j4_link_aux.stl` as the motor-connection disk, and `pa_j4_link_cover.stl` as the removable cover
- the current `pa_j4_link` semantics are assembly-level; Stage 1 does not require a single STL to map one-to-one to that body
- `assets/meshes/visual/pa_j5_fixed.stl` is kept as a legacy imported file, but it now maps semantically to `pa_j5_rotating_output_candidate` and should be read as the end-rotation output / flange candidate
- `pa_j5_visual_geom` now uses `assets/meshes/visual/pa_j5_fixed_support.stl`, copied from `hardwares/打印装配体/realtosim/pa_j5_fixed.STL`, as the current fixed-side support / bracket candidate
- within the current Stage 1 grouping, that fixed-side support visual is the main visual for the `j5` layer
- the old rotating-output candidate is still retained in Stage 1 as `pa_j5_rotating_output_candidate_visual_geom`, but only as a rotating-side reference visual and not as the fixed-side primary semantics
- the final link ownership and final naming inside the `j5` layer are still pending later confirmation
- `pa_ee_mount` now loads from `assets/meshes/visual/pa_ee_mount.stl` with assembly-frame compensation on the visual geom
- `pa_j2_carriage` still uses `assets/meshes/visual/unit_box.obj` as a placeholder, because no one-to-one independent CAD visual piece has been confirmed for it yet
- the adjacent imported real visuals around `pa_j2_carriage` already cover the main visible chain well enough for current Stage 1 loading and structural validation
- if a discrete `pa_j2_carriage` CAD visual is confirmed later, it can be added without changing the current Stage 1 structure or loadability assumptions
- collision still uses simple primitives
- the end-effector mount frame is aligned to the current Shadow forearm root pose so the combo wrapper can weld cleanly at load time
- the mount mesh is visually centered for Stage 1 validation, but the flange-hole origin is not yet production-calibrated

Current Stage 1 closure:

- the main visual chain is now largely complete for Stage 1 loading and structural validation
- `pa_j2_carriage` intentionally remains a placeholder logic layer at this stage
- `j4` and `j5` have completed the current round of semantic splitting into main-chain visuals versus retained reference candidates
- if we continue from here, coordinate/interface stabilization and naming cleanup should take priority over blindly importing more STL files
