# Stage3.2c Noisy Virtual-Camera Perception V0

Generated: 2026-06-04T18:33:42

## Scope

This MuJoCo-only test stresses the virtual perception camera by corrupting the rendered egg mask, depth, and calibration path. It checks whether the perception gate accepts good estimates and freezes unreliable ones instead of producing false confident bad pose updates.

## Result

- Status: `PASS`
- Camera: `stage3_egg_closeup`
- Trial groups: `10`
- Scenarios: `8`
- Samples: `80`
- Accepted updates: `40`
- Frozen updates: `40`
- False confident bad estimates: `0`
- Max accepted error: `0.013718 m`
- Max sensor-ok error: `49.915555 m`

## Scenario Summary

| scenario | samples | ok | accepted | frozen | false-conf bad | mean conf | max accepted err m | max err m |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| clean_reference | 10 | 10 | 10 | 0 | 0 | 0.803 | 0.000059 | 0.000059 |
| mask_dropout_30 | 10 | 10 | 10 | 0 | 0 | 0.802 | 0.000060 | 0.000060 |
| mask_dropout_55 | 10 | 10 | 0 | 10 | 0 | 0.517 | 0.000000 | 0.000059 |
| synthetic_occluder_45 | 10 | 10 | 10 | 0 | 0 | 0.655 | 0.000156 | 0.000156 |
| depth_noise_5mm | 10 | 10 | 0 | 10 | 0 | 0.000 | 0.000000 | 0.007802 |
| false_positive_blob | 10 | 10 | 0 | 10 | 0 | 0.000 | 0.000000 | 4.462671 |
| combined_hard | 10 | 10 | 0 | 10 | 0 | 0.000 | 0.000000 | 49.915555 |
| calibration_bias_12mm | 10 | 10 | 10 | 0 | 0 | 0.803 | 0.013718 | 0.013718 |

## Interpretation

- The noisy virtual-camera gate passed: no corrupted input produced an accepted pose update above the bad-estimate threshold.
- This is still MuJoCo virtual-camera work. It does not use or require real hardware.
- Frozen updates mean the controller should reuse last-good pose and rely more on contact/tactile/slip signals after approach.

Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\metadata\stage3_noisy_virtual_camera_perception_v0.json`
Visual checks: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\visual_checks\stage3_noisy_virtual_camera_perception_v0`
