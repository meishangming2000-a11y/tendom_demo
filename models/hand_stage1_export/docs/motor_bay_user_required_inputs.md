# Motor Bay Preflight: User Required Inputs

Generated: 2026-06-25

Minimum user / SolidWorks inputs required before formal MJCF integration.

## Required Export Folder

Expected folder:

`D:/tendon_project/hardwares/hand&arm_final/body&forearm_output/motor_bay/motor_bay_fixed_v0/`

It should contain at least:

```text
motor_bay_fixed_v0/
  urdf/
    motor_bay_fixed_v0.urdf
  meshes/
    motor_bay_link.STL
  docs_or_export_notes/
    screenshot_overview.png
    screenshot_mount_csys.png
    README_or_export_notes.md
```

Optional but strongly useful:

```text
  meshes/
    motor_bay_link_collision_simple.STL
  coordinate_systems.csv
  mass_properties.csv
```

## Direct Answers

1. URDF export directory should include:
   - `urdf/motor_bay_fixed_v0.urdf`
   - `meshes/motor_bay_link.STL`
   - optional simplified collision mesh:
     `meshes/motor_bay_link_collision_simple.STL`
   - export note naming the parent link and mount frame
   - screenshots showing the assembly and mount CSYS axes

2. Root link should be named:
   `motor_bay_link`

3. Mount coordinate system should be named:
   `motor_bay_mount_csys`

4. Is `motor_bay_wrist_mount_csys` mandatory:
   NO for a purely body-fixed motor bay. YES/strongly recommended if the motor
   bay touches the wrist side, aligns to `ee_mount`, or may later sit between
   arm and wrist/hand. If uncertain, provide it.

5. Is a dummy link needed:
   Not required if the exporter preserves `motor_bay_mount_csys` or the user can
   provide the transform explicitly. A dummy/reference link is acceptable only
   if SW2URDF cannot export the coordinate system name and a named frame must be
   carried through the URDF.

6. How to judge STL unit:
   Provide one known physical measurement from SolidWorks, for example motor bay
   length/width/height in mm. The integration script will compare STL bounding
   box size against that measurement. Do not rely on filename or exporter
   defaults. Current body STL was meter-scale; motor bay unit is UNKNOWN until
   checked.

7. If URDF Exporter does not export CSYS names:
   Provide the transform manually:
   - confirmed parent link name;
   - `parent_link -> motor_bay_mount_csys` translation in meters;
   - rotation as `rpy` radians or quaternion `wxyz`;
   - screenshot with parent frame and motor bay frame axes;
   - note whether the transform is in SolidWorks assembly coordinates or parent
     link local coordinates.

## Still UNKNOWN

- final parent link;
- `motor_bay_mount_csys` transform;
- STL unit;
- whether motor bay has a wrist-side reference frame;
- whether collision should be mesh-based or simplified primitive for the first
  pass.
