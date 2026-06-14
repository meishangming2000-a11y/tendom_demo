# Stage3.12 Autotune Lift-Timing Closeout v0

Generated: `2026-06-13`

## Boundary

- MuJoCo-only Stage3 diagnostic and tuning work.
- Uses existing Stage3.11D-B event/contact-gated runner.
- Simulated motor force feedback is logged as telemetry only.
- No hardware runtime, real camera, direct force control, demo-gallery promotion, or full-action ACT/DP promotion.

## What Changed

Stage3.12 now has an autonomous batch runner:

```text
simulations/models/arm_hand_stage1_export/run_stage3_12_autonomous_tuning_batch_v0.py
```

It runs bounded candidate batches without asking for per-parameter confirmation, ranks them against D-I, and writes per-candidate reports, summary CSVs, and metadata.

## Baseline Anchor

Stage3.11D-I remains the frozen diagnostic/demo anchor:

```text
gx = -0.0014 m
gz = 0.0022 m
lift_steps = 480
```

Existing D-I multiseed result:

| seed | success | contact | lift | true pinch | release | failures |
|---:|---:|---:|---:|---:|---:|---|
| `20260612` | `44 / 50` | `47 / 50` | `44 / 50` | `44 / 50` | `50 / 50` | 3 lift, 3 contact |
| `20265612` | `46 / 50` | `48 / 50` | `46 / 50` | `46 / 50` | `50 / 50` | 2 lift, 2 contact |
| `20265613` | `46 / 50` | `48 / 50` | `46 / 50` | `46 / 50` | `49 / 50` | 2 lift, 2 contact |
| total | `136 / 150` | `143 / 150` | `136 / 150` | `136 / 150` | `149 / 150` | 7 lift, 7 contact |

## Batch 0 Smoke

Batch 0 ran 8 candidates, `12` trials each, seed `20260614`.

Top smoke results:

| candidate | family | success | contact | lift | true pinch | release | note |
|---|---|---:|---:|---:|---:|---:|---|
| `lift_ls460` | lift continuation | `11 / 12` | 11 | 11 | 11 | 12 | best smoke rank |
| `robust_gz0025_watch_nontip` | contact entry | `11 / 12` | 11 | 11 | 11 | 12 | morphology watch item |
| `baseline_di` | baseline | `10 / 12` | 11 | 11 | 10 | 12 | same smoke seed |

Artifacts:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_12_autotune_batch0_v0_report.md
simulations/models/arm_hand_stage1_export/metadata/stage3_12_autotune_batch0_v0.json
simulations/models/arm_hand_stage1_export/data/stage3_12_autotune_batch0_summary_v0.csv
```

## Batch 1 50-Trial Validation

Batch 1 validated D-I, `lift_ls460`, and `robust_gz0025_watch_nontip`, `50` trials each, seed `20260614`.

| candidate | success | contact | lift | true pinch | release | terminal reasons |
|---|---:|---:|---:|---:|---:|---|
| `lift_ls460` | `43 / 50` | 46 | 43 | 43 | 48 | 4 contact, 3 lift |
| `robust_gz0025_watch_nontip` | `42 / 50` | 46 | 43 | 42 | 49 | 4 contact, 3 lift, 1 morphology |
| `baseline_di` | `41 / 50` | 46 | 42 | 41 | 48 | 4 contact, 4 lift, 1 morphology |

Interpretation:

- `lift_ls460` gave the cleanest 50-trial signal: +2 successes over the same-seed D-I baseline.
- The change primarily helps lift continuation.
- It does not solve contact entry.

Artifacts:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_12_autotune_batch1_v0_report.md
simulations/models/arm_hand_stage1_export/metadata/stage3_12_autotune_batch1_v0.json
simulations/models/arm_hand_stage1_export/data/stage3_12_autotune_batch1_summary_v0.csv
```

## Batch 2 Multiseed Lift Timing

Batch 2 scaled only `lift_ls460` across the three D-I comparison seeds.

| seed | success | contact | lift | true pinch | release | failures |
|---:|---:|---:|---:|---:|---:|---|
| `20260612` | `44 / 50` | 47 | 45 | 44 | 50 | 3 contact, 2 lift, 1 morphology |
| `20265612` | `46 / 50` | 48 | 48 | 46 | 50 | 2 contact, 2 morphology |
| `20265613` | `47 / 50` | 48 | 47 | 47 | 49 | 2 contact, 1 lift |
| total | `137 / 150` | `143 / 150` | `140 / 150` | `137 / 150` | `149 / 150` | 7 contact, 3 lift, 3 morphology |

Comparison against D-I:

| candidate | success | contact | lift | true pinch | release | contact failures | lift failures | morphology failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| D-I `ls480` | `136 / 150` | 143 | 136 | 136 | 149 | 7 | 7 | 0 |
| `lift_ls460` | `137 / 150` | 143 | 140 | 137 | 149 | 7 | 3 | 3 |

Interpretation:

- `lift_ls460` is a real but small improvement: +1 full success and +4 lift successes.
- The improvement is not clean enough for promotion because it introduces 3 morphology-gate failures.
- It is useful as a lift-timing diagnostic and possible ingredient for a later morphology-conditioned controller.

## Batch 3 Combo Smoke

Batch 3 combined `lift_ls460` with separation, active-finger abduction, and small contact-height offsets, `12` trials each, seed `20260615`.

Result:

- Most combos tied D-I at `11 / 12`.
- `ls460_active_abd_m048` regressed to `10 / 12`.
- No combo clearly beat D-I on the smoke gate.
- Tie candidates are retained as diagnostics only; they should not be auto-scaled.

Artifacts:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_12_autotune_batch3_v0_report.md
simulations/models/arm_hand_stage1_export/metadata/stage3_12_autotune_batch3_v0.json
simulations/models/arm_hand_stage1_export/data/stage3_12_autotune_batch3_summary_v0.csv
```

## Decision

Do not promote `lift_ls460` as the new Stage3.11D-I replacement.

Keep it as a Stage3.12 diagnostic candidate:

```text
classification = lift_timing_diagnostic_candidate
gx = -0.0014 m
gz = 0.0022 m
lift_steps = 460
```

Reason:

- It improves lift continuation.
- It does not improve contact entry.
- It introduces morphology failures, which is exactly the failure mode we do not want to hide behind higher raw success.

## Next

Stop local single-parameter tuning for now.

The next useful Stage3.12 work is training/data oriented:

1. Use the new batch runner as the scoreboard for future candidates.
2. Export or derive per-step morphology/quality labels for the D-I and `lift_ls460` failure windows.
3. Train or tune a bounded quality/residual branch that distinguishes:
   - contact-entry failure
   - lift-continuation failure
   - true-tip morphology failure
   - safe release
4. Keep PID+AI as offline side-branch signal analysis until it can improve the same gate without morphology regression.

## If Successful

Promote only a future bounded candidate that beats D-I on multiseed success while preserving clean true-tip morphology and visual evidence.

## If Failed

Keep Stage3.11D-I frozen as the demo-quality diagnostic anchor and move the next effort to contact geometry or morphology-label/residual data, not more blind parameter tuning.
