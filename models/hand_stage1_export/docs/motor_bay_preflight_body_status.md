# Motor Bay Preflight: Body Status

Generated: 2026-06-25

Scope: body status check before any `motor_bay_fixed_v0` MJCF integration.

## Direct Answers

1. Body URDF imported:
   YES. `body_urdf_export1/urdf/body.urdf` was copied/imported. The report says
   link count `1`, joint count `0`, root link `rough_body_support_link`.

2. `rough_body_support_link` exists in the current recommended scene:
   YES. It exists in
   `mjcf/scene_export4_connected_to_body_corrected_v10.xml`.

3. `body_arm_mount_csys` successfully used for root/global origin:
   PARTIAL. The URDF import report found `body_arm_mount_csys` in the CSV
   coordinate-system column, and the MJCF scene has `body_arm_mount_origin` /
   `body_arm_mount_x` / `body_arm_mount_y` / `body_arm_mount_z` sites under
   `rough_body_support_link`. The v10 body root is at `[0, 0, 0.18]` and
   `base_link` is nested under `rough_body_support_link`. Final mount clocking
   and CAD confirmation are still `needs_user_confirmation`.

4. Body visually aligned:
   PARTIAL. v10 has MuJoCo load/render pass and Isaac visual reproduction pass.
   The latest Isaac diagnosis says the inspection floor does not cut through
   the asset, and the previous "half buried" read was a visual/proxy issue.
   Final production CAD material/contact fidelity is still UNKNOWN.

5. Body affects grasp smoke:
   NO in the available body-connected smoke report. The available pinned-ball
   smoke was run on `scene_export4_connected_to_body_proxy.xml` and reports
   `body_proxy_interfered=false`. Direct v10 grasp smoke is UNKNOWN.

6. Current body integration status:
   PARTIAL.

## Interpretation

The body is stable enough for motor bay preflight and topology planning. It is
not yet a fully frozen production body/contact model:

- body is still a single-link visual/support body;
- body collision proxy/contact is not the final load-bearing geometry;
- support column is a temporary visual placeholder;
- final CAD mount orientation remains `needs_user_confirmation`.

Therefore, do not continue to final motor bay MJCF authoring until the motor bay
parent link and mount coordinate system are supplied. This is a data/contract
blocker, not a MuJoCo load blocker.

## Evidence

- `docs/body_urdf_import_report.md`
- `docs/body_connection_isaac_material_cleanup_v10_report.md`
- `metadata/body_connection_isaac_material_cleanup_v10.json`
- `docs/body_connected_grasp_smoke_report.md`
- `metadata/body_connected_grasp_smoke.json`
