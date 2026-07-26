# Body Connection Isaac Material Cleanup V10

- Status: `ISAAC_REPRO_RENDER_PASS`
- Source scene: `simulations/models/hand_stage1_export/mjcf/scene_export4_connected_to_body_corrected_v10.xml`
- Pose standard: unchanged from v9
- Isaac asset id: `body_connected_v10_mujoco_scene`

## What Changed

V10 keeps the v9 body, arm, hand, mount quaternion, support-column parenting, and joint structure unchanged.

The only MJCF-side visual cleanup is:

- `rough_body_support_link_visual` alpha was made opaque gray for more stable Isaac inspection.
- `rough_body_support_collision_proxy_bbox_disabled` was removed. It was already disabled (`contype=0`, `conaffinity=0`) and acted only as a misleading orange visual/proxy in Isaac.

## Checks

- MuJoCo load check: `nbody=33`, `njnt=27`, `ngeom=69`, `nu=26`
- Isaac conversion/render: `isaac_simulation/reports/body_connected_v10_isaac_repro_v0.json`
- MuJoCo/Isaac comparison: `isaac_simulation/reports/body_connected_v10_mujoco_isaac_compare_v0.json`
- Contact sheet: `isaac_simulation/figures/body_connected_v10_mujoco_isaac_compare_v0/body_connected_v10_mujoco_scene_mujoco_vs_isaac_contact_sheet.png`

## Ground Diagnosis

The Isaac fixed-camera renderer now records the inspection floor placement:

- asset minimum z: `-0.1629999876 m`
- inspection floor top z: `-0.2429999876 m`
- clearance: `0.08 m`

So the visible inspection floor is not cutting through the imported asset. The previous "half buried" impression came from the visual floor/camera angle plus the orange disabled body bbox proxy, not from the body root being below the inspection ground.

## Remaining Risks

- V10 is still a simulation-side cleanup, not a fresh CAD export.
- The body is still a single-link visual/support body with no forearm joints.
- The support column is still a temporary visual placeholder, not final CAD/contact geometry.
- Isaac material rendering is cleaner now, but production USD material authoring is still TBD.
