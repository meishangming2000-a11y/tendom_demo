# Stage3.7B Tactile Phase Gate V0 Eval Report

Generated: 2026-06-05T05:51:33

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Gate release reasons: `{'stable_window_met': 10}`
- Mean final lift: `0.103097 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.601`
- Max transient slip: `0.941`
- Mean pre-lift max slip: `0.490`
- Mean post-lift max slip: `0.438`
- Max hold slip: `0.263`
- Max crush risk: `0.111`
- Max penetration: `0.002223 m`
- Mean contact-settle steps: `1600.0`
- Mean gate stable window at release: `1428.2`

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
| 0 | center_nominal | PASS | stable_window_met | 1600 | 1261 | 0.414 | 0.063 | 0.09930 | 1.000 | 0.151 | 0.109 | 0.002188 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | stable_window_met | 1600 | 1600 | 0.619 | 0.001 | 0.10214 | 1.000 | 0.263 | 0.089 | 0.001781 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | stable_window_met | 1600 | 1367 | 0.405 | 0.020 | 0.09421 | 1.000 | 0.190 | 0.079 | 0.001582 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | stable_window_met | 1600 | 1404 | 0.789 | 0.022 | 0.10907 | 1.000 | 0.153 | 0.106 | 0.002122 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | stable_window_met | 1600 | 1517 | 0.554 | 0.037 | 0.10254 | 1.000 | 0.158 | 0.090 | 0.001798 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | stable_window_met | 1600 | 1331 | 0.361 | 0.035 | 0.08552 | 1.000 | 0.141 | 0.083 | 0.001667 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | stable_window_met | 1600 | 1600 | 0.565 | 0.037 | 0.11562 | 1.000 | 0.173 | 0.111 | 0.002212 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | stable_window_met | 1600 | 1292 | 0.769 | 0.002 | 0.09991 | 1.000 | 0.187 | 0.096 | 0.001923 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | stable_window_met | 1600 | 1514 | 0.592 | 0.002 | 0.11150 | 1.000 | 0.190 | 0.101 | 0.002024 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 9 | wide_diag | PASS | stable_window_met | 1600 | 1396 | 0.941 | 0.026 | 0.11116 | 1.000 | 0.162 | 0.111 | 0.002223 | `['early_contact_in_approach', 'transient_or_hold_slip']` |

## Interpretation

- This is a MuJoCo-only virtual-camera + synthetic-tactile evaluation.
- It preserves the Stage3.6 learned hand policy and adds only lift-permission timing.
- It intentionally does not produce hand-residual training labels.
- `transient_or_hold_slip` is reported as a risk flag even when hold slip remains below the success threshold.
- Early approach contact remains a separate approach-gating problem unless the arm/wrist path is changed.
