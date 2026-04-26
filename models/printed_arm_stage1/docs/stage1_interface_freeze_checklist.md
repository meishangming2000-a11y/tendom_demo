# Stage 1 Interface Freeze Checklist

Purpose: freeze the minimum coordinate, interface, and naming assumptions needed to carry `printed_arm_stage1` from visual validation into later real-to-sim work.

Scope:

- doc-only freeze checklist
- no `robot.xml` / joint tree / env / adapter / training changes
- no new STL import in this pass

## Priority Checklist

| Priority | Check item | Freeze condition | Why it matters |
| --- | --- | --- | --- |
| P0 | `pa_base` reference frame | Confirm Stage 1 base origin, axis directions, and whether future hardware calibration will continue to use this frame as the root reference. | This is the root for downstream mount alignment, actuator axes, tendon routing, and any future calibration offsets. |
| P0 | `pa_ee_mount` interface frame | Confirm whether `pa_ee_mount_site` already represents the real mating frame or only the current Stage 1 visual center; freeze its origin and axis meaning. | This directly affects end-effector attachment, wrapper weld assumptions, and later tool-frame consistency. |
| P0 | `j5` fixed-side vs rotating-side semantic boundary | Freeze that `pa_j5_fixed_support` is the fixed-side main visual and `pa_j5_rotating_output_candidate` is only a rotating-side reference visual; explicitly record which side is expected to own the future output axis. | This prevents later mixing of support geometry, rotating output semantics, and actuator/transmission ownership. |
| P1 | `pa_j4_link` assembly-level meaning | Freeze that `pa_j4_link` is currently a three-part main visual assembly and does not require a one-STL-to-one-body interpretation. | This avoids unnecessary refactors while still keeping the visual chain stable enough for Stage 1 validation. |
| P1 | future naming namespace review | Reserve or review future `body`, `joint`, `site`, `actuator`, `tendon`, and `transmission` names to avoid collisions with current legacy terms such as `pa_j5_fixed`. | Naming drift here will create avoidable adapter and config churn once actuation is modeled. |
| P1 | output-axis ownership by layer | Confirm which layer will own the mechanically meaningful output axis for `j3`, `j4`, and `j5`, even if visual candidates remain assembly-level. | This is a prerequisite for actuator gearing, tendon path definition, and pulley / spool ownership. |
| P2 | `pa_j2_carriage` placeholder boundary | Keep `pa_j2_carriage` as a logic-layer placeholder unless a discrete CAD part is clearly confirmed; do not infer geometry from neighboring parts. | This does not block Stage 1 loading, but it does affect later mechanism closure and tendon-routing fidelity. |
| P2 | visual vs collision divergence record | Note which bodies still rely on primitive collision that does not yet correspond tightly to imported visuals. | This matters later for contact realism, cable clearance, and validation beyond the current visual stage. |

## Must Confirm vs Can Defer

| Must confirm now | Can defer for later |
| --- | --- |
| `pa_base` root frame origin and axis directions | replacing `pa_j2_carriage` placeholder with a real STL |
| `pa_ee_mount_site` origin, normal, and axis meaning | merging `pa_j4_link` visual pieces into a cleaner export |
| `pa_j5_fixed_support` vs `pa_j5_rotating_output_candidate` ownership rule | renaming legacy mesh filenames on disk |
| future output-axis ownership for `j3` / `j4` / `j5` | collision mesh refinement or decimation |
| future naming registry for `body` / `joint` / `site` / `actuator` / `tendon` / `transmission` | cosmetic README cleanup beyond the current freeze notes |

## Minimum Additional Information Needed Next

- one explicit note or screenshot defining the `pa_base` assembly frame: origin, `+X`, `+Y`, `+Z`, and home-facing direction
- one explicit note for `pa_ee_mount_site`: whether it matches the real flange mating frame, and what physical feature defines its origin
- one explicit rule for `j5`: which candidate is fixed-side, which candidate is rotating-side, and which one should own the future output axis
- one naming reservation list for future `joint`, `actuator`, `tendon`, `transmission`, and critical `site` names
- one short layer-by-layer map of motor output ownership or transmission handoff from `j3` through `j5`
- optional but useful: a brief statement that `pa_j2_carriage` remains intentionally unresolved until a discrete part export exists

## Freeze Guidance

- if the three P0 items are confirmed, Stage 1 is stable enough to start coordinate/interface stabilization work for real-to-sim
- if any P0 item is still ambiguous, do not spend the next round importing more STL; close the semantic and frame definitions first
