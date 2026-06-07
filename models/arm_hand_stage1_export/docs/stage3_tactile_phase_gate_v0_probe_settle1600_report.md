# Stage3.7B Tactile Phase Gate V0 Eval Report

Generated: 2026-06-05T05:49:45

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Gate release reasons: `{'stable_window_met': 10}`
- Mean final lift: `0.103451 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.646`
- Max transient slip: `0.941`
- Mean pre-lift max slip: `0.635`
- Mean post-lift max slip: `0.453`
- Max hold slip: `0.263`
- Max crush risk: `0.113`
- Max penetration: `0.002260 m`
- Mean contact-settle steps: `1600.0`
- Mean gate stable window at release: `1381.5`

## Gate Parameters

- min contact-settle steps: `1600`
- max contact-settle steps: `1600`
- stable window steps: `300`
- gate slip threshold: `0.18`
- gate crush threshold: `0.35`
- gate penetration threshold: `0.004`

## Episode Results

| ep | trial | status | gate reason | settle | gate window | max slip | pre-lift slip | lift m | stable | hold slip | crush | pen m | risks |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | PASS | stable_window_met | 1600 | 1270 | 0.585 | 0.043 | 0.09929 | 1.000 | 0.146 | 0.113 | 0.002260 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | stable_window_met | 1600 | 1600 | 0.618 | 0.001 | 0.10214 | 1.000 | 0.263 | 0.087 | 0.001737 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | stable_window_met | 1600 | 1367 | 0.578 | 0.020 | 0.09423 | 1.000 | 0.185 | 0.080 | 0.001602 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | stable_window_met | 1600 | 1411 | 0.792 | 0.025 | 0.10931 | 1.000 | 0.153 | 0.106 | 0.002120 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | stable_window_met | 1600 | 1535 | 0.577 | 0.041 | 0.10236 | 1.000 | 0.160 | 0.092 | 0.001846 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | stable_window_met | 1600 | 759 | 0.479 | 0.031 | 0.08553 | 1.000 | 0.140 | 0.085 | 0.001691 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | stable_window_met | 1600 | 1600 | 0.603 | 0.021 | 0.11918 | 1.000 | 0.170 | 0.112 | 0.002232 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | stable_window_met | 1600 | 1311 | 0.788 | 0.002 | 0.09990 | 1.000 | 0.187 | 0.098 | 0.001964 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | stable_window_met | 1600 | 1532 | 0.498 | 0.004 | 0.11145 | 1.000 | 0.190 | 0.101 | 0.002020 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 9 | wide_diag | PASS | stable_window_met | 1600 | 1430 | 0.941 | 0.026 | 0.11113 | 1.000 | 0.161 | 0.110 | 0.002202 | `['early_contact_in_approach', 'transient_or_hold_slip']` |

## Interpretation

- This is a MuJoCo-only virtual-camera + synthetic-tactile evaluation.
- It preserves the Stage3.6 learned hand policy and adds only lift-permission timing.
- It intentionally does not produce hand-residual training labels.
- `transient_or_hold_slip` is reported as a risk flag even when hold slip remains below the success threshold.
- Early approach contact remains a separate approach-gating problem unless the arm/wrist path is changed.
