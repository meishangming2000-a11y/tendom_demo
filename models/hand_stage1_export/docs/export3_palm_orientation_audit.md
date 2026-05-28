# Export3 Palm Orientation Audit

Status: direction/orientation diagnostic only. No CAD/STL/tree/training changes.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Marker debug scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_palm_orientation_debug.xml`
- Current ball position: `[0.0, -0.1, 0.21]`
- Palm world position: `[0.0005711446680750725, -0.0006589003018724648, 0.08527305568729812]`

## Palm Local Axes In World

| Axis | World direction |
|---|---|
| palm local `x` | `[-0.07648039777530402, 0.9806672150279276, 0.1801181893243981]` |
| palm local `y` | `[3.607102949665375e-10, -0.18064728983487102, 0.9835479432520391]` |
| palm local `z` | `[0.9970710851068401, 0.07522213799596855, 0.013815976229864801]` |

## Inferred Anatomical / Task Directions

- Finger extension direction: `[0.1053236235551359, -0.24668766701495662, 0.963354622796784]`
- Thumb side direction: `[-0.5753504804244425, 0.19727842694540818, 0.7937588090454861]`
- Scripted four-finger close direction: `[0.0029334061036954, -0.6422417282189723, -0.7664965477175605]`
- Palm normal from finger/thumb cross: `[-0.5108856638152867, -0.8445498643046677, -0.160409990994892]`
- Palm normal / close alignment: `0.663860`
- Inferred palmar side: `[-0.5108856638152867, -0.8445498643046677, -0.160409990994892]`
- Inferred dorsal side: `[0.5108856638152867, 0.8445498643046677, 0.160409990994892]`

## Ball Side

- Ball vector from palm: `[-0.0005711446680750725, -0.09934109969812754, 0.12472694431270187]`
- Projection on inferred palmar axis: `0.064183 m`
- Ball is on inferred palmar side: `True`

## MCP / Thumb / Tip Positions

- MCP base positions: `{'index': [-0.02404923894269346, -0.02205578740816377, 0.1833585745520407], 'middle': [-0.004107817341262879, -0.020050978398722916, 0.1809106118375438], 'ring': [0.015833604458208132, -0.01735816423530059, 0.1747167526887979], 'little': [0.03577502615722817, -0.014292815625357206, 0.16649460129913718]}`
- Proximal base positions: `{'index': [-0.02351358979469934, -0.02403830700428789, 0.19289909656939785], 'middle': [-0.0034467551663750692, -0.022022683904373796, 0.19044550762798731], 'ring': [0.016723258161215775, -0.01930939960455902, 0.18423726003430824], 'little': [0.03759894295493783, -0.01615006044941702, 0.17590006955188844]}`
- Fingertip positions: `{'index': [-0.01889905274706996, -0.037339012541697525, 0.2837029145703529], 'middle': [0.00490658083103945, -0.05071274636339239, 0.29389366841833214], 'ring': [0.026971659456861127, -0.05028542813987437, 0.2761208255202925], 'little': [0.05492513092003695, -0.0395372170847805, 0.2583552629361778]}`
- Thumb base positions: `{'thumb_root_connector_link': [-0.01629372836873276, 0.0009575554889412472, 0.1052251744411096], 'thumb_trapezium1_link': [-0.02055248065934455, 0.006584051112547681, 0.11441540327036856]}`

## Marker Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_orientation\palm_side_debug_front.png` camera=`front` mean_pixel=17.36
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_orientation\palm_side_debug_side.png` camera=`side` mean_pixel=14.06
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_orientation\ball_current_side.png` camera=`top` mean_pixel=42.67
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_palm_orientation\ball_mirrored_side.png` camera=`top` mean_pixel=42.53

## Interpretation

- The inferred palmar side is the finger-forward x thumb-side palm-plane normal, with sign chosen to align with the current scripted four-finger close motion.
- Current ball `[0.0, -0.1, 0.21]` has palmar projection 0.0642 m.
- Mirrored ball `[0.0, 0.1, 0.21]` has palmar projection -0.1047 m.
- By the current scripted-close inference, the existing negative-Y ball position is on the palm-closing side.

## Visual Judgment

- In the marker views, the green palmar-side marker lies on the same side family as the current negative-Y ball placement; the purple dorsal marker lies on the opposite side.
- The mirrored positive-Y ball appears far from the four-finger closing side in the top view.
- This does not support a simple "mirror ball Y" fix.
- The palm local axes are non-intuitive: palm local `x` is mostly world +Y, local `y` is mostly world +Z, and local `z` is mostly world +X. If SolidWorks expects a specific palm-normal CSYS convention, the exported palm frame should be checked.
- The user's "hand looks palm-backwards" observation may therefore be caused by palm mesh/frame orientation or camera/anatomical labeling mismatch, not by the current ball coordinate alone.
