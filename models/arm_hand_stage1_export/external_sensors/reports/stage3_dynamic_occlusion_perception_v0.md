# Stage3 Dynamic Occlusion Perception V0

Generated: 2026-06-04T09:27:09

## Scope

This MuJoCo-only Stage3 test checks perception during the actual approach, closure, lift, and hold phases. It re-renders from the perception camera at each phase boundary, applies a last-good tracking decision, and compares the resulting sensor output against MuJoCo truth for evaluation only.

## Gate

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Perception camera: `stage3_egg_closeup`
- Trial groups: `10`
- Visual dynamic episodes: `10`
- Oracle episodes: `10`
- Runtime tracking confidence: `raw_confidence * relative_mask_retention`
- Accepted update threshold: confidence >= `0.550`, mask pixels >= `500`
- Bad accepted estimate threshold: `0.015 m`
- Last-good control-window threshold: `0.025 m`

## Overall Result

- Visual dynamic success: `10` / `10`
- Oracle success: `10` / `10`
- Perception samples: `90`
- Accepted pose updates: `51`
- Frozen last-good updates: `39`
- Low-visibility samples: `25`
- False confident bad estimates: `0`
- Max accepted pose error: `0.008542 m`
- Max last-good error before lift/control handoff: `0.020267 m`

## Trial Results

| trial | visual | oracle | visual lift m | oracle lift m | low-vis | frozen | max accepted err m | max last-good control err m | final last-good err m | visual failure | oracle failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| center_nominal | 1 | 1 | 0.09718 | 0.09837 | 1 | 4 | 0.006073 | 0.009372 | 0.098008 | `[]` | `[]` |
| left_low_nominal | 1 | 1 | 0.09938 | 0.09936 | 3 | 5 | 0.006771 | 0.019677 | 0.104878 | `[]` | `[]` |
| right_high_nominal | 1 | 1 | 0.09530 | 0.09525 | 4 | 4 | 0.007440 | 0.020267 | 0.096582 | `[]` | `[]` |
| left_high_zplus | 1 | 1 | 0.10576 | 0.10574 | 4 | 4 | 0.007729 | 0.013305 | 0.106249 | `[]` | `[]` |
| right_low_zminus | 1 | 1 | 0.09983 | 0.09981 | 1 | 4 | 0.007194 | 0.011061 | 0.102122 | `[]` | `[]` |
| front_small_lift | 1 | 1 | 0.08417 | 0.08437 | 2 | 4 | 0.007153 | 0.016000 | 0.085691 | `[]` | `[]` |
| back_large_lift | 1 | 1 | 0.11511 | 0.10492 | 4 | 4 | 0.007352 | 0.011046 | 0.116469 | `[]` | `[]` |
| lifted_center | 1 | 1 | 0.09480 | 0.09504 | 0 | 3 | 0.008542 | 0.007379 | 0.008736 | `[]` | `[]` |
| lifted_diag | 1 | 1 | 0.10727 | 0.09615 | 2 | 3 | 0.008168 | 0.012139 | 0.117803 | `[]` | `[]` |
| wide_diag | 1 | 1 | 0.11017 | 0.11011 | 4 | 4 | 0.007707 | 0.011913 | 0.115857 | `[]` | `[]` |

## Phase Visibility Summary

| stage | samples | accepted | low-vis | min mask retention | max pose err m |
|---|---:|---:|---:|---:|---:|
| initial_acquire | 10 | 10 | 0 | 1.000 | 0.000059 |
| pre_approach | 10 | 10 | 0 | 1.000 | 0.000059 |
| approach | 10 | 10 | 0 | 0.855 | 0.003077 |
| preshape | 10 | 10 | 0 | 0.736 | 0.006771 |
| close_fingers | 10 | 9 | 1 | 0.688 | 0.010993 |
| close_thumb | 10 | 1 | 6 | 0.612 | 0.012483 |
| close_hold | 10 | 0 | 8 | 0.565 | 0.014208 |
| lift | 10 | 1 | 5 | 0.522 | 0.015117 |
| hold_lift | 10 | 0 | 5 | 0.506 | 0.015260 |

## Interpretation

- Dynamic perception passed the current control-window gate: no accepted estimate was badly wrong, and the visual-guided grasp/lift still matched the oracle success rate.
- Low-visibility samples occurred, and the tracker used last-good freezing rather than blindly accepting every rendered pose.
- The final last-good error after lift is diagnostic only. Once the egg is in hand, control should increasingly rely on contact/tactile/slip abstractions rather than camera-only pose tracking.
- This is not a real-camera or hardware integration test.

Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\metadata\stage3_dynamic_occlusion_perception_v0.json`
Visual checks: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\visual_checks\stage3_dynamic_occlusion_perception_v0`
