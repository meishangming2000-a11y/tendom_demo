# Stage3.12 Autonomous Tuning stage3_12_autotune_batch2_lift_ls460_seed20260612 Report

Generated: `2026-06-13T11:39:57`

## Boundary

- MuJoCo-only smoke scoreboard around Stage3.11D-I.
- Uses existing Stage3.11D-B event/contact-gated runner.
- Simulated motor force feedback is logged as observation telemetry only.
- No hardware runtime, real camera, direct force control, demo-gallery promotion, or full-action ACT/DP promotion.

## Gate

- Trials per candidate: `50`
- Shared seed: `20260612`
- Ranking priority: full success, true-pinch, lift, contact, release, clean hold morphology, safe force/current proxy.

## Ranked Results

| rank | candidate | family | success | contact | lift | true pinch | release | hold true-tip | hold non-tip | hold wrap | decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `lift_ls460` | `lift_continuation` | 44/50 | 47 | 45 | 44 | 50 | 0.881 | 0.093 | 0.000 | advance_to_final_validation |

## Next Action

Advance `lift_ls460` to multiseed validation only if the morphology risk is acceptable, then run visual thumb-side/oblique inspection before any demo-quality claim.

## Artifacts

- Summary CSV: `simulations\models\arm_hand_stage1_export\data\stage3_12_autotune_batch2_lift_ls460_seed20260612_summary_v0.csv`
- Metadata: `simulations\models\arm_hand_stage1_export\metadata\stage3_12_autotune_batch2_lift_ls460_seed20260612_v0.json`
