# Stage3.7B Tactile Phase Gate V0 Eval Report

Generated: 2026-06-05T05:53:51

- Status: **PASS**
- Base checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_phase_hand_policy_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Policy scope: `scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate`
- Episodes: `10`
- Success count: `10 / 10`
- Terminal reasons: `{'success_gentle_grasp_hold': 10}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Gate release reasons: `{'stable_window_met': 10}`
- Mean final lift: `0.103084 m`
- Mean hold stable fraction: `1.000`
- Mean max transient slip: `0.628`
- Max transient slip: `1.000`
- Mean pre-lift max slip: `0.511`
- Mean post-lift max slip: `0.437`
- Max hold slip: `0.263`
- Max crush risk: `0.109`
- Max penetration: `0.002175 m`
- Mean contact-settle steps: `1600.0`
- Mean gate stable window at release: `1445.7`

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
| 0 | center_nominal | PASS | stable_window_met | 1600 | 1308 | 0.416 | 0.021 | 0.09930 | 1.000 | 0.151 | 0.104 | 0.002074 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 1 | left_low_nominal | PASS | stable_window_met | 1600 | 1600 | 0.622 | 0.001 | 0.10213 | 1.000 | 0.263 | 0.090 | 0.001801 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 2 | right_high_nominal | PASS | stable_window_met | 1600 | 1371 | 0.423 | 0.019 | 0.09420 | 1.000 | 0.192 | 0.077 | 0.001541 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 3 | left_high_zplus | PASS | stable_window_met | 1600 | 1421 | 1.000 | 0.018 | 0.10886 | 1.000 | 0.158 | 0.101 | 0.002020 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 4 | right_low_zminus | PASS | stable_window_met | 1600 | 1520 | 0.553 | 0.036 | 0.10256 | 1.000 | 0.159 | 0.087 | 0.001743 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 5 | front_small_lift | PASS | stable_window_met | 1600 | 1344 | 0.397 | 0.022 | 0.08552 | 1.000 | 0.143 | 0.080 | 0.001594 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 6 | back_large_lift | PASS | stable_window_met | 1600 | 1600 | 0.595 | 0.038 | 0.11589 | 1.000 | 0.164 | 0.109 | 0.002175 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 7 | lifted_center | PASS | stable_window_met | 1600 | 1299 | 0.781 | 0.002 | 0.09989 | 1.000 | 0.187 | 0.097 | 0.001930 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 8 | lifted_diag | PASS | stable_window_met | 1600 | 1513 | 0.492 | 0.003 | 0.11147 | 1.000 | 0.190 | 0.101 | 0.002018 | `['early_contact_in_approach', 'transient_or_hold_slip']` |
| 9 | wide_diag | PASS | stable_window_met | 1600 | 1481 | 1.000 | 0.018 | 0.11102 | 1.000 | 0.159 | 0.107 | 0.002132 | `['early_contact_in_approach', 'transient_or_hold_slip']` |

## Interpretation

- This is a MuJoCo-only virtual-camera + synthetic-tactile evaluation.
- It preserves the Stage3.6 learned hand policy and adds only lift-permission timing.
- It intentionally does not produce hand-residual training labels.
- `transient_or_hold_slip` is reported as a risk flag even when hold slip remains below the success threshold.
- Early approach contact remains a separate approach-gating problem unless the arm/wrist path is changed.
