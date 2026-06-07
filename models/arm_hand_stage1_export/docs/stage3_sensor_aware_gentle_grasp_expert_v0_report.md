# Stage3.5 Sensor-Aware Gentle Grasp Expert V0

Generated: 2026-06-04T18:17:23

## Scope

This MuJoCo-only expert uses virtual-camera pose acquisition and contact-derived tactile/slip checks to gently grasp, slowly lift, and hold the egg-like object for 3 seconds.

## Result

- Status: `PASS`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Virtual camera: `stage3_egg_closeup`
- Episodes: `10`
- Successes: `10` / `10`
- Mean final lift: `0.103056 m`
- Mean hold stable fraction: `1.000`
- Max hold slip score: `0.262`
- Max crush risk: `0.113`
- Max penetration: `0.002259 m`
- Failure reasons: `{}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_nonhold_slip': 10}`

## Trial Summary

| trial | success | lift m | hold stable | hold max slip | crush | penetration m | first contact | risks | failures |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| center_nominal | 1 | 0.09927 | 1.000 | 0.161 | 0.113 | 0.002259 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| left_low_nominal | 1 | 0.10199 | 1.000 | 0.262 | 0.088 | 0.001751 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| right_high_nominal | 1 | 0.09483 | 1.000 | 0.221 | 0.081 | 0.001617 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| left_high_zplus | 1 | 0.10840 | 1.000 | 0.174 | 0.107 | 0.002134 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| right_low_zminus | 1 | 0.10220 | 1.000 | 0.185 | 0.093 | 0.001861 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| front_small_lift | 1 | 0.08565 | 1.000 | 0.161 | 0.085 | 0.001701 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| back_large_lift | 1 | 0.11653 | 1.000 | 0.161 | 0.112 | 0.002246 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| lifted_center | 1 | 0.09948 | 1.000 | 0.179 | 0.098 | 0.001959 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| lifted_diag | 1 | 0.11095 | 1.000 | 0.191 | 0.101 | 0.002017 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |
| wide_diag | 1 | 0.11127 | 1.000 | 0.178 | 0.111 | 0.002213 | `approach` | `['early_contact_in_approach', 'transient_nonhold_slip']` | `[]` |

## Interpretation

- The Stage3.5 scripted expert passed the fixed 10-trial MuJoCo gate.
- Visual pose is used for pre-contact localization; tactile/slip is used for post-contact stability and hold checks.
- Early approach contact and transient non-hold slip are reported as risk flags for later control refinement, not hidden.
- This does not claim real hardware or real-camera integration.

Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_sensor_aware_gentle_grasp_expert_v0.json`
Visual checks: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_stage3_sensor_aware_gentle_grasp_expert_v0`
