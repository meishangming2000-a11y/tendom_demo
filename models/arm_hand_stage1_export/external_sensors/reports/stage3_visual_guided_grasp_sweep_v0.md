# Stage3 Visual-Guided Grasp Sweep V0

Generated: 2026-06-04T01:16:51

## Scope

This MuJoCo-only Stage3 test checks whether image-derived egg position can guide the mechanical hand to approach, close on, and lift the egg. Each trial has a paired oracle run that uses MuJoCo egg truth for IK while keeping the same control phases.

## Inputs

- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Perception camera: `stage3_egg_closeup`
- Trial groups: `10`
- Episodes: `20`
- Success lift threshold: `0.050 m`
- Precision hit threshold: `0.008 m`
- Functional hit threshold: `0.015 m`
- Max success penetration: `0.012 m`

## Overall Result

- Visual episodes: `10` / `10` success
- Oracle episodes: `10` / `10` success
- Visual precision hits: `3` / `10`
- Visual functional hits: `10` / `10`
- Visual mean final lift: `0.100897 m`
- Oracle mean final lift: `0.098912 m`
- Visual max approach true error: `0.012652 m`
- Oracle max approach true error: `0.012781 m`

## Paired Trial Results

| trial | visual | oracle | visual lift m | oracle lift m | lift delta m | visual hit 8/15mm | oracle hit 8/15mm | visual approach err m | oracle approach err m | visual failure | oracle failure |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---|---|
| center_nominal | 1 | 1 | 0.09718 | 0.09837 | -0.001188 | 0/1 | 0/1 | 0.011205 | 0.011213 | `[]` | `[]` |
| left_low_nominal | 1 | 1 | 0.09938 | 0.09936 | 0.000017 | 0/1 | 0/1 | 0.009105 | 0.009094 | `[]` | `[]` |
| right_high_nominal | 1 | 1 | 0.09530 | 0.09525 | 0.000049 | 0/1 | 0/1 | 0.012652 | 0.012682 | `[]` | `[]` |
| left_high_zplus | 1 | 1 | 0.10576 | 0.10574 | 0.000021 | 0/1 | 0/1 | 0.010248 | 0.010248 | `[]` | `[]` |
| right_low_zminus | 1 | 1 | 0.09983 | 0.09981 | 0.000016 | 0/1 | 0/1 | 0.011677 | 0.011703 | `[]` | `[]` |
| front_small_lift | 1 | 1 | 0.08417 | 0.08437 | -0.000199 | 0/1 | 0/1 | 0.010203 | 0.010824 | `[]` | `[]` |
| back_large_lift | 1 | 1 | 0.11511 | 0.10492 | 0.010190 | 0/1 | 0/1 | 0.010902 | 0.012781 | `[]` | `[]` |
| lifted_center | 1 | 1 | 0.09480 | 0.09504 | -0.000232 | 1/1 | 1/1 | 0.007565 | 0.007545 | `[]` | `[]` |
| lifted_diag | 1 | 1 | 0.10727 | 0.09615 | 0.011124 | 1/1 | 1/1 | 0.006912 | 0.007512 | `[]` | `[]` |
| wide_diag | 1 | 1 | 0.11017 | 0.11011 | 0.000053 | 1/1 | 1/1 | 0.007558 | 0.007556 | `[]` | `[]` |

## Failure Aggregates

- Visual failure reasons: `{}`
- Oracle failure reasons: `{}`

## Interpretation

- Visual-guided grasp/lift passed every tested group under this clean MuJoCo segmentation setup.
- This is not a real-camera test and does not validate Stage4 hardware integration.
- The next risk is dynamic occlusion during approach/closure and replacing exact MuJoCo segmentation with a noisier mask provider.

Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\metadata\stage3_visual_guided_grasp_sweep_v0.json`
Visual checks: `D:\tendon_project\simulations\models\arm_hand_stage1_export\external_sensors\visual_checks\stage3_visual_guided_grasp_sweep_v0`
