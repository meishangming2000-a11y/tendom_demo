# Export4 Wrist2 Collision-Tuned Grasp Report

Generated: 2026-05-26T01:47:30

## Scope

Scripted position-control smoke test for the experimental export4 wrist2/collision-tuned scene. The hand is controlled through MuJoCo position actuators; the script does not write hand qpos directly.

## Setup

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Ball position: `[0.0, -0.1, 0.21]`
- Ball pinned: `True`
- Status: **FAIL_GRASP_SIDE_OR_TARGET_NEEDS_REVIEW**
- Bodies/joints/actuators/geoms/sites: `{'nbody': 26, 'njnt': 23, 'nu': 22, 'ngeom': 50, 'nsite': 5}`

## Stage Metrics

| stage | contacts | ball-hand contacts | max penetration | ball displacement | four-tip avg | thumb-ball | thumb-index |
|---|---:|---:|---:|---:|---:|---:|---:|
| open_hand | 0 | 0 | 0.000000 | 0.000000 | 0.093999 | 0.170167 | 0.130735 |
| preshape | 0 | 0 | 0.000000 | 0.000000 | 0.124444 | 0.170358 | 0.083454 |
| close_four_fingers | 0 | 0 | 0.000000 | 0.000000 | 0.153400 | 0.170598 | 0.039820 |
| close_thumb | 0 | 0 | 0.000000 | 0.000000 | 0.154583 | 0.145366 | 0.017917 |
| hold | 0 | 0 | 0.000000 | 0.000000 | 0.154572 | 0.142052 | 0.019539 |

## Target Angles

Only non-zero stage target angles are listed.

### open_hand

- all actuator targets zero

### preshape

- `index_mcp_flex_joint`: `-0.0350`
- `middle_mcp_flex_joint`: `-0.0350`
- `ring_mcp_flex_joint`: `-0.0200`
- `little_mcp_flex_joint`: `-0.0150`
- `index_mcp_abd_joint`: `-0.3400`
- `middle_mcp_abd_joint`: `-0.3800`
- `ring_mcp_abd_joint`: `-0.2000`
- `little_mcp_abd_joint`: `-0.1500`
- `index_pip_joint`: `-0.4800`
- `middle_pip_joint`: `-0.5200`
- `ring_pip_joint`: `-0.2000`
- `little_pip_joint`: `-0.1600`
- `index_dip_joint`: `-0.2200`
- `middle_dip_joint`: `-0.2400`
- `ring_dip_joint`: `-0.1000`
- `little_dip_joint`: `-0.0800`

### close_four_fingers

- `index_mcp_flex_joint`: `-0.0600`
- `middle_mcp_flex_joint`: `-0.0600`
- `ring_mcp_flex_joint`: `-0.0500`
- `little_mcp_flex_joint`: `-0.0400`
- `index_mcp_abd_joint`: `-0.5800`
- `middle_mcp_abd_joint`: `-0.6400`
- `ring_mcp_abd_joint`: `-0.6200`
- `little_mcp_abd_joint`: `-0.5400`
- `index_pip_joint`: `-0.8200`
- `middle_pip_joint`: `-0.8800`
- `ring_pip_joint`: `-0.8400`
- `little_pip_joint`: `-0.7600`
- `index_dip_joint`: `-0.4200`
- `middle_dip_joint`: `-0.4600`
- `ring_dip_joint`: `-0.4400`
- `little_dip_joint`: `-0.4000`

### close_thumb

- `index_mcp_flex_joint`: `-0.0600`
- `middle_mcp_flex_joint`: `-0.0600`
- `ring_mcp_flex_joint`: `-0.0500`
- `little_mcp_flex_joint`: `-0.0400`
- `index_mcp_abd_joint`: `-0.5800`
- `middle_mcp_abd_joint`: `-0.6400`
- `ring_mcp_abd_joint`: `-0.6200`
- `little_mcp_abd_joint`: `-0.5400`
- `index_pip_joint`: `-0.8200`
- `middle_pip_joint`: `-0.8800`
- `ring_pip_joint`: `-0.8400`
- `little_pip_joint`: `-0.7600`
- `index_dip_joint`: `-0.4200`
- `middle_dip_joint`: `-0.4600`
- `ring_dip_joint`: `-0.4400`
- `little_dip_joint`: `-0.4000`
- `thumb_cmc_abd_joint`: `-0.3000`
- `thumb_mcp_joint`: `0.2500`
- `thumb_ip_joint`: `-0.2500`

### hold

- `index_mcp_flex_joint`: `-0.0600`
- `middle_mcp_flex_joint`: `-0.0600`
- `ring_mcp_flex_joint`: `-0.0500`
- `little_mcp_flex_joint`: `-0.0400`
- `index_mcp_abd_joint`: `-0.5800`
- `middle_mcp_abd_joint`: `-0.6400`
- `ring_mcp_abd_joint`: `-0.6200`
- `little_mcp_abd_joint`: `-0.5400`
- `index_pip_joint`: `-0.8200`
- `middle_pip_joint`: `-0.8800`
- `ring_pip_joint`: `-0.8400`
- `little_pip_joint`: `-0.7600`
- `index_dip_joint`: `-0.4200`
- `middle_dip_joint`: `-0.4600`
- `ring_dip_joint`: `-0.4400`
- `little_dip_joint`: `-0.4000`
- `thumb_cmc_abd_joint`: `-0.3000`
- `thumb_mcp_joint`: `0.2500`
- `thumb_ip_joint`: `-0.2500`

## Interpretation

- `PASS_FOR_SCRIPTED_SMOKE` means the branch can be used for scripted inspection, not training.
- `PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE` means the closure shape is useful, but collision/ball placement still needs tuning.
- The current `*_mcp_flex_joint` names are retained, but these joints are treated as lateral spread / abduction-adduction in the report.

## Screenshots

- `open_hand`: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\open_hand_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 32.64914525462963, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\open_hand_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 33.78048755787037, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\open_hand_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 86.1858587962963, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\open_hand_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 46.61648148148148, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- `preshape`: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\preshape_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 33.867774016203704, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\preshape_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 36.849650752314815, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\preshape_top.png', 'shape': [900, 1280, 3], 'min_pixel': 2, 'max_pixel': 255, 'mean_pixel': 84.96544097222223, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\preshape_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 49.87230584490741, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- `close_four_fingers`: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_four_fingers_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 36.74979745370371, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_four_fingers_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 35.910432291666666, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_four_fingers_top.png', 'shape': [900, 1280, 3], 'min_pixel': 3, 'max_pixel': 255, 'mean_pixel': 89.340296875, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_four_fingers_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 45.50398929398148, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- `close_thumb`: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_thumb_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 36.471531828703704, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_thumb_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 34.47249739583334, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_thumb_top.png', 'shape': [900, 1280, 3], 'min_pixel': 3, 'max_pixel': 255, 'mean_pixel': 89.6395552662037, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\close_thumb_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 44.08371296296296, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
- `hold`: `{'front': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\hold_front.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 36.47008449074074, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 145, 'elevation': -25}, 'side': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\hold_side.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 34.46755989583333, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.34, 'azimuth': 90, 'elevation': -20}, 'top': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\hold_top.png', 'shape': [900, 1280, 3], 'min_pixel': 3, 'max_pixel': 255, 'mean_pixel': 89.62113715277778, 'lookat': [0.0, 0.045, 0.2], 'distance': 0.3, 'azimuth': 180, 'elevation': -78}, 'thumb': {'file': 'D:\\tendon_project\\simulations\\models\\hand_stage1_export\\docs\\visual_checks_export4_wrist2_collision_tuned_grasp\\hold_thumb.png', 'shape': [900, 1280, 3], 'min_pixel': 0, 'max_pixel': 255, 'mean_pixel': 43.91919589120371, 'lookat': [-0.015, 0.035, 0.19], 'distance': 0.26, 'azimuth': 75, 'elevation': -18}}`
