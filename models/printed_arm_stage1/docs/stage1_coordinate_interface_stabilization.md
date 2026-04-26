# Stage 1 Coordinate / Interface Stabilization

Purpose: record the minimum coordinate, interface, handoff, and naming definitions that are stable enough to support the next real-to-sim pass without changing the current `robot.xml` structure.

Scope:

- doc-only stabilization pass
- no `robot.xml` / joint tree / env / adapter / training changes
- no new STL import
- no deletion of legacy assets or legacy names

Status legend:

- `CONFIRMED`: stable enough to freeze at the current Stage 1 semantic/interface level
- `PENDING`: still missing required mechanical confirmation before structure updates
- `INFERRED`: current best freeze derived from existing structure and metadata, with explicit risk

## 1. Five Minimum Freeze Definitions

### 1.1 `pa_base` root frame definition

- Status: `INFERRED`
- Minimum freeze definition:
  - In current Stage 1, the root reference frame is the frame of `pa_root` / `pa_base_origin`.
  - `+X` is the current chain-forward direction from `pa_root` toward `pa_j1_link` and along the `pa_J2` slide axis.
  - `+Z` is the current `pa_J1` hinge axis.
  - `+Y` is defined by the right-hand rule from the current Stage 1 body tree.
  - This freeze only defines the Stage 1 simulation root frame; it does not yet prove that the same frame is the final hardware calibration datum.
- Evidence:
  - `robot.xml`: `pa_base_origin` is placed at the root body origin.
  - `robot.xml`: `pa_j1_link` is offset along `+X`, `pa_J2` uses axis `1 0 0`, and `pa_J1` uses axis `0 0 1`.
  - `mesh_manifest.yaml`: `pa_base` is marked as orientation-preserved from the imported assembly-frame visual.
- Missing point:
  - No explicit CAD note yet confirms that the current Stage 1 root frame is the final physical base datum used for calibration or measurement.
- Risk:
  - If the physical base datum differs from the current Stage 1 root frame, later mount transforms, output-axis sites, and actuator alignment will all inherit a global offset or rotation correction.

### 1.2 `pa_ee_mount_site` interface definition

- Status: `INFERRED`
- Minimum freeze definition:
  - `pa_ee_mount_site` is the current Stage 1 interface anchor used for mount alignment and later wrapper-level attachment logic.
  - `pa_ee_axis_x`, `pa_ee_axis_y`, and `pa_ee_axis_z` define the current local interface axes for that anchor.
  - The current imported `pa_ee_mount` visual is intentionally centered on this site for Stage 1 validation.
  - This does not yet freeze `pa_ee_mount_site` as the final production flange-hole origin or fully calibrated mechanical mating frame.
- Evidence:
  - `mount_metadata.yaml`: `mount_body`, `mount_site`, and `mount_axes_sites` explicitly define the interface anchor and local axis markers.
  - `mount_metadata.yaml`: `ee_mount_geom_origin_to_mount_site_error_m` is near zero.
  - `robot.xml`: the mount body and axis sites are explicitly present, and the comment states the frame is chosen to match the Shadow root home pose.
  - `mount_metadata.yaml`: notes explicitly state that hole-pattern origin calibration is still pending.
- Missing point:
  - No confirmed mechanical statement yet says that the current site origin equals the real flange mating origin or hole-pattern reference.
- Risk:
  - If the real mount interface origin differs from the current Stage 1 site, future welds, tool transforms, and end-effector calibration will need structural updates.

### 1.3 `j5` fixed / rotating ownership rule

- Status: `CONFIRMED`
- Minimum freeze definition:
  - `pa_j5_fixed_support` is the current Stage 1 fixed-side main visual for the `j5` layer.
  - `pa_j5_rotating_output_candidate` is retained only as a rotating-side reference visual.
  - The legacy on-disk filename `assets/meshes/visual/pa_j5_fixed.stl` remains preserved, but its current semantics are rotating-side reference only and not fixed-side primary meaning.
  - The final mechanical body split and final naming can still evolve later without changing this Stage 1 semantic boundary.
- Evidence:
  - `mesh_manifest.yaml`: `pa_j5_fixed_support_visual` is listed as `formal_main_visual`.
  - `mesh_manifest.yaml`: `pa_j5_rotating_output_candidate_visual` is listed as `reference_candidate_visual`.
  - `README.md`: the `j5` layer is explicitly split into fixed-side main visual and rotating-side reference visual.
  - `mount_metadata.yaml`: the rotating-side candidate is kept centered on `pa_ee_mount_site`, while the fixed-side support uses the current assembly offset.
- Missing point:
  - The final mechanically authoritative output-axis owner for the future `J5` stage is not yet frozen in structure.
- Risk:
  - The biggest remaining risk is semantic confusion from legacy names such as `pa_j5_fixed` in filenames and body labels if future structure changes happen before the naming registry is accepted.

### 1.4 `j3 -> j5` output-axis / transmission handoff

- Status: `PENDING`
- Minimum freeze definition:
  - The current structure-level articulated axes that are explicitly modeled stop at `pa_J4`.
  - `pa_J3` is currently the `0 1 0` hinge on `pa_j3_link`.
  - `pa_J4` is currently the `0 0 1` hinge on `pa_j4_link`.
  - The current `j5` layer is visual-semantic only: there is no explicit `J5` joint, actuator, tendon, or transmission object yet.
  - Until a real `j5` output-axis owner is confirmed, no future tendon, transmission, spool, or pulley definition should assume a finalized `j5` axis location from the current visual candidates alone.
- Evidence:
  - `robot.xml`: actuated joints and actuators currently exist for `J1` through `J4` only.
  - `robot.xml`: `pa_j5_fixed` and `pa_ee_mount` are fixed child bodies with no `J5` joint.
  - `mesh_manifest.yaml`: `pa_j4_link` is assembly-level visual semantics, and `pa_j5` is split into fixed-side main visual plus rotating-side reference visual.
- Missing point:
  - No confirmed mechanical handoff document yet defines where torque/output ownership transitions from the `j4` stage into the future `j5` rotating side.
  - No confirmed tendon or transmission path has been defined from `j3` through `j5`.
- Risk:
  - Prematurely binding tendons, transmissions, or actuator gearing to current visual centers would likely create avoidable rework once the real output-axis owner is confirmed.

### 1.5 Future naming registry

- Status: `INFERRED`
- Minimum freeze definition:
  - Existing structure names remain frozen for Stage 1 compatibility: current `body`, `joint`, `site`, and `actuator` names should not be repurposed to mean something different before a structure update pass.
  - The following future names are reserved for the next structure-layer pass if corresponding entities are added:
    - `body`: `pa_j5_fixed_side_body`, `pa_j5_rotating_side_body`
    - `joint`: `pa_J5`
    - `site`: `pa_base_frame_site`, `pa_j3_output_axis_site`, `pa_j4_output_axis_site`, `pa_j5_output_axis_site`, `pa_tool_mount_frame_site`
    - `actuator`: `pa_A_J5`
    - `tendon`: prefix `pa_T_`
    - `transmission`: prefix `pa_TR_`
  - Until the structure pass begins, these names are reserved only as registry guidance and are not yet implementation commitments.
- Evidence:
  - `robot.xml`: current implemented names already use the `pa_*`, `pa_J*`, and `pa_A_*` conventions.
  - `README.md` and `mesh_manifest.yaml`: legacy semantic drift around `pa_j5_fixed` is already documented and motivates an explicit future naming guardrail.
- Missing point:
  - The registry has not yet been accepted by an actual structure update pass, so no new names have been instantiated.
- Risk:
  - If future updates introduce ad hoc names before this registry is accepted, there is a high chance of semantic drift between body names, actuator names, and later transmission/tendon labels.

## 2. Evidence Summary and Missing Information

| Freeze item | Main evidence source | Main missing point |
| --- | --- | --- |
| `pa_base` root frame | `robot.xml`, `mesh_manifest.yaml` | physical base datum confirmation from CAD or measurement |
| `pa_ee_mount_site` interface | `mount_metadata.yaml`, `robot.xml` | real flange mating origin / hole-pattern reference |
| `j5` fixed / rotating rule | `mesh_manifest.yaml`, `README.md`, `mount_metadata.yaml` | final output-axis ownership for future structural `J5` modeling |
| `j3 -> j5` handoff | `robot.xml`, `mesh_manifest.yaml` | actual output-axis handoff and transmission ownership after `J4` |
| future naming registry | current naming in `robot.xml`, semantic drift notes in docs/metadata | acceptance during a future structure-layer pass |

## 3. Risk Notes

- `pa_base` and `pa_ee_mount_site` are the two highest-leverage frame risks. If either is redefined later, most downstream real-to-sim transforms will move with them.
- `j5` currently has enough semantic separation for Stage 1 review, but not enough structural certainty for a final `J5` joint or transmission definition.
- `j4` is stable enough as an assembly-level visual meaning, but not yet a mechanically frozen transmission boundary.
- `pa_j2_carriage` remaining as a placeholder does not block the current stabilization pass, provided no one infers a transmission or tendon anchor from it.
- Legacy names are intentionally preserved today; the main protection against later confusion is the naming registry, not filename cleanup.

## 4. Gate To Enter Structure-Layer Updates

The project can move from doc-only stabilization into `robot.xml` structure updates once all of the following are true:

1. `pa_base` frame is explicitly confirmed as either the final hardware datum or an approved intermediate datum with a documented conversion.
2. `pa_ee_mount_site` is explicitly confirmed as either the true mechanical interface frame or a documented surrogate frame with a known offset to the real flange origin.
3. The `j5` ownership rule is extended from semantic split into a confirmed mechanical rule: which side owns the future `J5` output axis, and which body should host any future `J5` joint/site.
4. A minimal `j3 -> j5` handoff statement exists that says where output-axis responsibility changes and which future element will own tendon / transmission routing at each stage.
5. The future naming registry is accepted so that any added `body`, `joint`, `site`, `actuator`, `tendon`, or `transmission` names do not collide with current legacy semantics.

If any one of these five gate items remains open, the recommended next step is still documentation or calibration clarification, not structure editing.
