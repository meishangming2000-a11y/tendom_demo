# Clean Mesh Aligned Visual Check Report

## Inputs

- Primitive reference: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_primitive.xml`
- Original clean draft: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_draft.xml`
- Aligned draft: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_aligned_draft.xml`
- Aligned scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_clean_mesh_aligned.xml`
- Render directory: `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_aligned\`

## Rendered Screenshots

- `front_view.png`
- `side_view.png`
- `top_view.png`
- `palm_view.png`
- `finger_root_closeup.png`
- `thumb_root_closeup.png`
- `index_finger_closeup.png`
- `full_hand_with_ball.png`

## Overall Result

**PARTIAL**

The MJCF-only translation correction substantially improves the clean mesh placement. The palm, wrist, hand base, five fingers, and thumb are now visible as one connected hand instead of separated assembly-position fragments. The original clean draft visual failure is therefore improved enough to keep using this aligned draft for visual debugging.

This is not a final CAD-quality mesh alignment. The automatic pass only added per-body `geom pos` translations and did not solve unknown per-link CAD-to-body rotations. For final clean CAD visuals, SolidWorks should still export body-local per-link STL or provide an explicit link frame transform for each mesh.

## View Observations

| View | Observation |
|---|---|
| `front_view.png` | Full hand is visible. Palm, wrist/base, four long fingers, thumb, and ball appear in one coherent area. No large mesh fragment is floating far away. |
| `side_view.png` | Palm and wrist are connected, and fingers are attached near the palm top. Thumb is on the side and no longer detached. |
| `top_view.png` | Five digits are visible around the ball. Long fingers are roughly ordered and no repeated whole-hand mesh is visible. |
| `palm_view.png` | Palm mesh has returned to the expected palm body region. Finger root hardware/mesh is close to the palm top but still visually crowded and should not be treated as final mechanical proof. |
| `finger_root_closeup.png` | MCP root region is much closer to the palm. Some root/finger clean mesh details overlap primitive reference geoms, so exact joint-center correctness remains TODO. |
| `thumb_root_closeup.png` | Thumb root connector is now adjacent to the palm and thumb chain. Multi-part connector looks plausible enough for inspection, but exact part orientation remains unverified. |
| `index_finger_closeup.png` | Index/neighbor finger mesh follows the finger chain region, but the camera crop makes individual phalanx orientation hard to prove. More targeted joint-motion renders are recommended before using this as a final mesh. |
| `full_hand_with_ball.png` | The ball is in front of the palm and the hand reads as a complete hand. This is acceptable for the next scripted visual demo check, not for final CAD release. |

## Issues

| Severity | Issue | Notes |
|---|---|---|
| MAJOR | Unknown per-link mesh rotation remains unresolved | The aligned draft only fixes assembly/world translation offsets. If any STL was exported with assembly orientation that differs from the MuJoCo body frame, MJCF `pos` alone cannot fully correct it. |
| MAJOR | Exact joint-center alignment is not proven | The mesh is visually close to the primitive skeleton, but MCP/PIP/DIP centers need joint-motion screenshots to confirm there is no rotation around an incorrect point. |
| MINOR | Closeup cameras need refinement | `index_finger_closeup.png` is useful but cropped; a later camera pass can make individual phalanx checks easier. |
| MINOR | Primitive collision/reference geoms are still visible through transparent clean visuals | This is intentional for debugging, but screenshots are visually busy. |

## Decision

- Sample-link alignment result: **improved** for hand base, wrist, palm, index examples, and thumb examples.
- Full-hand extension: **applied** to all 23 logical clean mesh links found in the draft.
- Continue with aligned draft for visual debugging: **yes**.
- Treat as final clean CAD mesh: **no**.
- Return to SolidWorks body-local STL export still recommended for final CAD-quality alignment: **yes**.

## SolidWorks Body-Local Export Recommendation

For final replacement, each link should be exported with vertices in that link's local coordinate frame, not the assembly/world frame:

1. Open the hand assembly and isolate exactly one link's parts.
2. Create or select the link-local coordinate system that matches the URDF/MJCF body frame.
3. Export STL using that coordinate system as the output frame when possible.
4. Keep units consistent with millimeters and retain `scale="0.001 0.001 0.001"` in MJCF.
5. Repeat per link, including multi-part `thumb_root_connector_link` without merging unless the parts share the same link-local frame.
6. Re-run clean mesh validation and visual alignment checks.
