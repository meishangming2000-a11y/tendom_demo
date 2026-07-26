# Body Mesh Diagnostics

Generated: 2026-06-23T02:05:55

| file | size bytes | triangles | bbox min | bbox max | bbox size | centroid | sha256 prefix | unit guess | looks like body |
|---|---:|---:|---|---|---|---|---|---|---|
| `rough_body_support_link.STL` | 149684 | 2992 | `[-7.000000e-02 -8.700000e-02 -1.490116e-09]` | `[0.07  0.343 0.2  ]` | `[0.14 0.43 0.2 ]` | `[-0.001282  0.066511  0.099628]` | `74373705a2826f5e` | `meters` | `True` |

## Unit Decision

- Recommended MuJoCo mesh scale: `1 1 1`.
- The largest dimension is below 1 m and the inertial COM in URDF is around `z=0.1`, so this export is treated as meter-scale, not millimeter-scale.

## Geometry Check

- Suspected wrong geometry or full assembly export: `False`.
- The mesh appears to be the rough body/base support only, not the full arm-hand assembly.
