# Motor Bay Preflight: Base Scene Check

Generated: 2026-06-25

Scope: preflight / integration contract only. This does not create the final
motor bay MJCF scene and does not modify any active MJCF file.

## Recommendation

Recommended base scene:

`simulations/models/hand_stage1_export/mjcf/scene_export4_connected_to_body_corrected_v10.xml`

## Why This Scene

- It is the latest body-connected experiment scene in `hand_stage1_export`.
- It preserves the v9 accepted body/arm/hand pose and changes only Isaac-facing
  material / disabled proxy visualization.
- It loads in MuJoCo with `nbody=33`, `njnt=27`, `nu=26`, `ngeom=69`.
- It contains the full body -> arm -> hand chain:
  `rough_body_support_link / base_link / link_1 / link_2 / link_3 / ee_mount / hand_base_link`.
- It contains the existing `wrist_2_joint` as a hinge/revolute joint with
  `axis="0 0 -1"` and `range="-0.8 0.8"`.
- It has Isaac visual reproduction evidence through
  `isaac_simulation/reports/body_connected_v10_isaac_repro_v0.json`.

## Candidate Comparison

| candidate | status for motor bay preflight | reason |
|---|---|---|
| `scene_export4_current_baseline.xml` | not recommended | Frozen hand-only reference. It does not contain body/arm links. |
| `scene_ball_export4_palmar_ypos_collision_candidate.xml` | not recommended as direct base | Best export4 grasp-smoke hand candidate, but hand-only with no rough body / arm tree. |
| `scene_ball_export4_wrist2_collision_tuned.xml` | not recommended as direct base | Useful wrist diagnostic branch, but not body-connected and default `-Y` scripted grasp was documented as failing. |
| `scene_export4_connected_to_body_proxy.xml` | useful regression reference | Body-connected proxy scene with pinned-ball grasp smoke PASS, but it predates v8/v9/v10 orientation and Isaac cleanup. |
| `scene_export4_connected_to_body_corrected_v10.xml` | recommended | Latest body-connected scene with corrected body/arm side, support column parenting, Isaac render pass, and retained 26-action tree. |

## Direct Answers

1. Recommended base scene path:
   `simulations/models/hand_stage1_export/mjcf/scene_export4_connected_to_body_corrected_v10.xml`

2. Why selected:
   latest body-connected scene; includes rough body, arm, hand, wrist hinge
   correction, support-column evidence, MuJoCo load pass, and Isaac visual pass.

3. Does it already include rough body:
   YES. It contains `rough_body_support_link`.

4. Does it already include the `wrist_2_joint` revolute fix:
   YES. MuJoCo reports `wrist_2_joint` as `mjJNT_HINGE`, axis `[0, 0, -1]`,
   range `[-0.8, 0.8]`.

5. Has it passed grasp smoke:
   PARTIAL / INDIRECT. The earlier body-connected proxy scene
   `scene_export4_connected_to_body_proxy.xml` passed pinned-ball grasp smoke
   with `body_proxy_interfered=false`. A direct v10 grasp smoke report was not
   found in the current preflight scan, so the direct v10 answer is UNKNOWN.

6. Can it be used as the motor bay integration baseline:
   YES for preflight and likely formal fixed-body integration, after the user
   confirms the parent link and mount coordinate system. Do not write the final
   motor bay MJCF until those inputs exist.

## Evidence

- `docs/body_connection_isaac_material_cleanup_v10_report.md`
- `metadata/body_connection_isaac_material_cleanup_v10.json`
- `docs/body_connected_grasp_smoke_report.md`
- `metadata/body_connected_grasp_smoke.json`
- `docs/export4_wrist2_joint_fix_report.md`
- `docs/export4_active_file_index.md`
