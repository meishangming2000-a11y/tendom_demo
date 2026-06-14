# Stage3.12 Autonomous Tuning stage3_12_autotune_batch3 Report

Generated: `2026-06-13T11:43:32`

## Boundary

- MuJoCo-only smoke scoreboard around Stage3.11D-I.
- Uses existing Stage3.11D-B event/contact-gated runner.
- Simulated motor force feedback is logged as observation telemetry only.
- No hardware runtime, real camera, direct force control, demo-gallery promotion, or full-action ACT/DP promotion.

## Gate

- Trials per candidate: `12`
- Shared seed: `20260615`
- Ranking priority: full success, true-pinch, lift, contact, release, clean hold morphology, safe force/current proxy.

## Ranked Results

| rank | candidate | family | success | contact | lift | true pinch | release | hold true-tip | hold non-tip | hold wrap | decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `ls460_gz0021` | `lift_contact_combo` | 11/12 | 12 | 11 | 11 | 12 | 0.917 | 0.139 | 0.000 | keep_as_tie_candidate |
| 2 | `ls460_sep058` | `lift_morphology_combo` | 11/12 | 12 | 11 | 11 | 12 | 0.917 | 0.143 | 0.000 | keep_as_tie_candidate |
| 3 | `ls460_sep062` | `lift_morphology_combo` | 11/12 | 12 | 11 | 11 | 12 | 0.917 | 0.143 | 0.000 | keep_as_tie_candidate |
| 4 | `baseline_di` | `baseline` | 11/12 | 12 | 11 | 11 | 12 | 0.917 | 0.156 | 0.000 | reject_or_hold |
| 5 | `ls460_gz0023` | `lift_contact_combo` | 11/12 | 12 | 11 | 11 | 12 | 0.917 | 0.171 | 0.000 | keep_as_tie_candidate |
| 6 | `lift_ls460` | `lift_continuation` | 11/12 | 12 | 11 | 11 | 12 | 0.917 | 0.171 | 0.000 | keep_as_tie_candidate |
| 7 | `ls460_active_abd_m048` | `lift_morphology_combo` | 10/12 | 10 | 10 | 10 | 12 | 0.833 | 0.160 | 0.000 | reject_or_hold |

## Next Action

No candidate clearly beat the D-I anchor in this batch. Keep tie candidates as diagnostics, but do not automatically scale them; move to closeout, visual/morphology diagnosis, or label/residual data work.

## Artifacts

- Summary CSV: `simulations\models\arm_hand_stage1_export\data\stage3_12_autotune_batch3_summary_v0.csv`
- Metadata: `simulations\models\arm_hand_stage1_export\metadata\stage3_12_autotune_batch3_v0.json`
