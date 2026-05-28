# Export3 Thumb Separation Diagnosis

## Observation

The viewer screenshot shows the thumb root / thumb segments visually separated from the palm-side root area. This is not expected for a continuous thumb chain.

## Short Conclusion

This is a transform/origin problem, not a mesh hash/size problem.

The export3 link tree contains the expected 2-DoF CMC thumb chain, but two thumb child-body origins are much too large:

- `thumb_cmc_flex_joint`: `thumb_trapezium1_link -> thumb_metacarpal_link`
- `thumb_mcp_joint`: `thumb_metacarpal_link -> thumb_proximal_link`

Those origins make the downstream thumb bodies appear suspended away from their parent joints.

## World-Position Distances

Measured from `scene_ball_export3_palm_side_fixed.xml` at neutral/open pose:

| Segment | Distance |
|---|---:|
| `palm_link -> thumb_root_connector_link` | `0.026175 m` |
| `thumb_root_connector_link -> thumb_trapezium1_link` | `0.011587 m` |
| `thumb_trapezium1_link -> thumb_metacarpal_link` | `0.150613 m` |
| `thumb_metacarpal_link -> thumb_proximal_link` | `0.132965 m` |
| `thumb_proximal_link -> thumb_distal_link` | `0.032000 m` |

The first, second, and last values are plausible. The middle two are not plausible for adjacent thumb bones.

## URDF Joint Origins

These large offsets already exist in the export3 URDF:

```text
thumb_cmc_flex_joint origin xyz = 0.022854 0.085965 0.12154
thumb_mcp_joint      origin xyz = -0.11064 0.054899 0.049241
```

Approximate origin lengths:

- `thumb_cmc_flex_joint`: `0.1506 m`
- `thumb_mcp_joint`: `0.1330 m`

## Mesh Size Cross-Check

The STL mesh sizes are plausible and do not explain the separation:

| Mesh | BBox size |
|---|---:|
| `thumb_trapezium1_link.STL` | `0.0171, 0.0107, 0.0109 m` |
| `thumb_metacarpal_link.STL` | `0.0525, 0.0497, 0.0336 m` |
| `thumb_proximal_link.STL` | `0.0173, 0.0458, 0.0208 m` |
| `thumb_distal_link.STL` | `0.0161, 0.0411, 0.0200 m` |

So the STL files are likely still clean, but the joint/body origin transforms for the thumb chain are wrong.

## Likely Cause

Most likely SolidWorks / URDF Exporter exported the origins of `thumb_cmc_flex_joint` and `thumb_mcp_joint` in an assembly/world-like coordinate frame, or the corresponding CSYS origins were not placed at the real parent-child joint center in the parent link frame.

This is why the thumb appears disconnected even though the tree is present.

## What Is Not The Cause

- Not caused by the palm-side ball fix.
- Not caused by the visual camera.
- Not caused by duplicate STL files.
- Not caused by a missing `thumb_trapezium1_link`; that link exists.
- Not caused by MuJoCo deleting the fixed root joint. MuJoCo compiles fixed joints away, but the fixed child body still exists.

## Recommended SolidWorks Check

For export4, inspect these CSYS/origin definitions first:

1. `thumb_cmc_flex_joint` origin should sit at the real connection between `Trapezium1` and `Os metacarpale I`.
2. `thumb_cmc_flex_joint` origin must be expressed relative to `thumb_trapezium1_link`, not an assembly/world reference.
3. `thumb_mcp_joint` origin should sit at the real connection between `Os metacarpale I` and `Proximal phalanx of thumb`.
4. `thumb_mcp_joint` origin must be expressed relative to `thumb_metacarpal_link`.
5. Re-export and verify that adjacent thumb body distances are on the order of millimeters to a few centimeters, not `0.13-0.15 m`.

## Sim-Side Recommendation

Do not continue thumb opposition tuning on this export3 chain until these origins are fixed or an explicit temporary MJCF-only thumb-origin repair is created and marked experimental.
