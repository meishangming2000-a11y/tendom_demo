# Stage3.12 Autonomous Tuning Batch 0 Report

Generated: `2026-06-13T11:32:19`

## Boundary

- MuJoCo-only smoke scoreboard around Stage3.11D-I.
- Uses existing Stage3.11D-B event/contact-gated runner.
- Simulated motor force feedback is logged as observation telemetry only.
- No hardware runtime, real camera, direct force control, demo-gallery promotion, or full-action ACT/DP promotion.

## Gate

- Trials per candidate: `12`
- Shared seed: `20260614`
- Ranking priority: full success, true-pinch, lift, contact, release, clean hold morphology, safe force/current proxy.

## Ranked Smoke Results

| rank | candidate | family | success | contact | lift | true pinch | release | hold true-tip | hold non-tip | hold wrap | decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `lift_ls460` | `lift_continuation` | 11/12 | 11 | 11 | 11 | 12 | 0.917 | 0.038 | 0.000 | advance_to_final_validation |
| 2 | `robust_gz0025_watch_nontip` | `contact_entry` | 11/12 | 11 | 11 | 11 | 12 | 0.879 | 0.036 | 0.000 | advance_to_final_validation |
| 3 | `contact_gz0023` | `contact_entry` | 10/12 | 11 | 11 | 10 | 12 | 0.842 | 0.053 | 0.000 | keep_as_tie_candidate |
| 4 | `baseline_di` | `baseline` | 10/12 | 11 | 11 | 10 | 12 | 0.838 | 0.024 | 0.000 | reject_or_hold |
| 5 | `sep058` | `morphology_clean` | 10/12 | 11 | 11 | 10 | 12 | 0.838 | 0.024 | 0.000 | keep_as_tie_candidate |
| 6 | `sep062` | `morphology_clean` | 10/12 | 11 | 11 | 10 | 12 | 0.838 | 0.024 | 0.000 | keep_as_tie_candidate |
| 7 | `active_abd_m048` | `morphology_clean` | 10/12 | 10 | 10 | 10 | 12 | 0.833 | 0.030 | 0.000 | keep_as_tie_candidate |
| 8 | `lift_ls500` | `lift_continuation` | 9/12 | 11 | 10 | 9 | 12 | 0.758 | 0.017 | 0.000 | reject_or_hold |

## Next Action

Advance `lift_ls460`, `robust_gz0025_watch_nontip`, `contact_gz0023` to 50-trial validation against the same D-I anchor, then require visual morphology check.

## Artifacts

- Summary CSV: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_12_autotune_batch0_summary_v0.csv`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_12_autotune_batch0_v0.json`
