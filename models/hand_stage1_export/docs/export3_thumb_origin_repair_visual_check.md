# Export3 Thumb Origin Repair Visual Check

## Question

Can the separated thumb be pulled back in MuJoCo, or must it be re-exported from SolidWorks?

## Result

Partial MJCF-only repair is possible, but it is not a trustworthy final fix.

The repaired MJCF pulls the thumb body chain back into a continuous kinematic chain:

| Segment | Repaired distance |
|---|---:|
| `palm_link -> thumb_root_connector_link` | `0.026175 m` |
| `thumb_root_connector_link -> thumb_trapezium1_link` | `0.011587 m` |
| `thumb_trapezium1_link -> thumb_metacarpal_link` | `0.018001 m` |
| `thumb_metacarpal_link -> thumb_proximal_link` | `0.052000 m` |
| `thumb_proximal_link -> thumb_distal_link` | `0.032000 m` |

However, visual inspection still shows thumb mesh pieces not fully attached. This means the issue is not only the body/joint origin. At least one thumb STL visual mesh, especially `thumb_metacarpal_link.STL`, also carries a local/assembly offset that does not match the repaired body frame.

## Generated Experimental Files

- `mjcf/hand_stage1_export3_thumb_origin_repaired.xml`
- `mjcf/scene_ball_export3_thumb_origin_repaired.xml`
- `scripts/build_export3_thumb_origin_repaired.py`
- `docs/export3_thumb_origin_repair_report.md`

## Interpretation

The MuJoCo model can be made kinematically usable for a rough smoke test by repairing body origins and relying more on primitive collision proxies.

But the clean visual STL thumb chain is not reliable enough to promote as final. The correct fix is to return to SolidWorks and re-export with correct body-local origins and mesh-local coordinates.

## SolidWorks Export4 Priority Fix

1. `thumb_cmc_flex_joint` CSYS origin must be at the real `Trapezium1 -> Os metacarpale I` joint center.
2. `thumb_mcp_joint` CSYS origin must be at the real `Os metacarpale I -> Proximal phalanx` joint center.
3. Each thumb STL should be exported in its own link-local coordinates, not assembly/world coordinates.
4. After export4, verify that adjacent thumb body distances are plausible before running grasp demos.

## Recommendation

- For tonight's rough scripted-grasp debugging: use the repaired/proxy model only as an experimental scaffold.
- For any serious visual/MJCF hand model: re-export from SolidWorks.
