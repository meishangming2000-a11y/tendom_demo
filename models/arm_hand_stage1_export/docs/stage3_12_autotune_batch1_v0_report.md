# Stage3.12 Autonomous Tuning stage3_12_autotune_batch1 Report

Generated: `2026-06-13T11:38:47`

## Boundary

- MuJoCo-only smoke scoreboard around Stage3.11D-I.
- Uses existing Stage3.11D-B event/contact-gated runner.
- Simulated motor force feedback is logged as observation telemetry only.
- No hardware runtime, real camera, direct force control, demo-gallery promotion, or full-action ACT/DP promotion.

## Gate

- Trials per candidate: `50`
- Shared seed: `20260614`
- Ranking priority: full success, true-pinch, lift, contact, release, clean hold morphology, safe force/current proxy.

## Ranked Results

| rank | candidate | family | success | contact | lift | true pinch | release | hold true-tip | hold non-tip | hold wrap | decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `lift_ls460` | `lift_continuation` | 43/50 | 46 | 43 | 43 | 48 | 0.860 | 0.069 | 0.000 | advance_to_final_validation |
| 2 | `robust_gz0025_watch_nontip` | `contact_entry` | 42/50 | 46 | 43 | 42 | 49 | 0.832 | 0.067 | 0.000 | advance_to_final_validation |
| 3 | `baseline_di` | `baseline` | 41/50 | 46 | 42 | 41 | 48 | 0.821 | 0.061 | 0.000 | reject_or_hold |

## Next Action

Advance `lift_ls460`, `robust_gz0025_watch_nontip` to multiseed validation only if the morphology risk is acceptable, then run visual thumb-side/oblique inspection before any demo-quality claim.

## Artifacts

- Summary CSV: `simulations\models\arm_hand_stage1_export\data\stage3_12_autotune_batch1_summary_v0.csv`
- Metadata: `simulations\models\arm_hand_stage1_export\metadata\stage3_12_autotune_batch1_v0.json`
