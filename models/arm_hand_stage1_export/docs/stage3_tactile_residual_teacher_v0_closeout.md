# Stage3.7A Tactile Residual Teacher V0 Closeout

Generated: 2026-06-05

## Purpose

Stage3.7A tested whether tactile/slip signals can reduce the known Stage3
risk:

```text
transient_nonhold_slip
```

The base controller was the Stage3.6 formal learned-control baseline:

```text
scripted arm/wrist
+ learned phase-specific hand/finger policy
```

This work stayed MuJoCo-only. It did not use real cameras or hardware.

## Baseline

Stage3.6 fixed-trial baseline:

- success: `10 / 10`
- mean final lift: `0.103050 m`
- hold stable fraction: `1.000`
- mean max transient slip: `0.816`
- max transient slip: `1.000`
- max hold slip: `0.262`
- max crush risk: `0.113`
- max penetration: `0.002260 m`
- risk flags: `early_contact_in_approach` and `transient_or_hold_slip` in all
  10 trials

Important interpretation:

```text
Hold is already stable.
The slip problem is a transient peak during thumb close / contact settle / lift
transition, not a steady hold problem.
```

## New Script

Teacher/evaluation script:

```text
models/arm_hand_stage1_export/eval_stage3_tactile_residual_teacher_v0.py
```

It can test:

- hand/finger residuals driven by tactile slip/crush fields
- lift-start hand bias
- adaptive contact-settle timing based on tactile stability
- fixed or adaptive contact-settle duration probes

Primary recommended Stage3.7A timing-teacher report:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_phase_timing_teacher_v0_eval_report.md
```

Metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_tactile_phase_timing_teacher_v0_eval.json
```

Randomized 30-trial report:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_phase_timing_teacher_v0_randomized30_report.md
```

Randomized 30-trial metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_tactile_phase_timing_teacher_v0_randomized30.json
```

## Probe Matrix

| probe | success | mean max slip | max slip | max hold slip | max crush | max penetration | mean settle steps | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Stage3.6 base | `10 / 10` | `0.816` | `1.000` | `0.262` | `0.113` | `0.002260` | n/a | baseline |
| hand close residual | `10 / 10` | `0.821` | `1.000` | `0.261` | `0.113` | `0.002260` | n/a | no improvement |
| strong hand close residual | `10 / 10` | `0.846` | `1.000` | `0.261` | `0.113` | `0.002260` | n/a | worse |
| mild relax-on-slip residual | `10 / 10` | `0.812` | `1.000` | `0.262` | `0.113` | `0.002260` | n/a | tiny improvement |
| strong relax-on-slip residual | `10 / 10` | `1.000` | `1.000` | `0.268` | `0.113` | `0.002260` | n/a | worse |
| slow lift 1000 | `10 / 10` | `0.815` | `1.000` | `0.183` | `0.113` | `0.002260` | n/a | improves hold slip only |
| very slow lift 1500 | `10 / 10` | `0.817` | `1.000` | `0.121` | `0.113` | `0.002260` | n/a | improves hold slip only |
| contact settle 500 | `10 / 10` | `0.726` | `1.000` | `0.262` | `0.113` | `0.002260` | n/a | meaningful transient improvement |
| contact settle 800 | `10 / 10` | `0.694` | `0.941` | `0.263` | `0.113` | `0.002260` | n/a | better |
| contact settle 1200 | `10 / 10` | `0.659` | `0.941` | `0.263` | `0.113` | `0.002260` | n/a | best fixed probe |
| slow thumb close 500 | `10 / 10` | `0.761` | `1.000` | `0.262` | `0.113` | `0.002260` | n/a | not enough |
| slow thumb close 500 + settle 1200 | `10 / 10` | `0.683` | `1.000` | `0.263` | `0.113` | `0.002260` | n/a | worse than settle alone |
| adaptive settle early | `10 / 10` | `0.746` | `1.000` | `0.262` | `0.113` | `0.002260` | `462.5` | stopped too early |
| adaptive settle min 800 | `10 / 10` | `0.694` | `0.941` | `0.263` | `0.113` | `0.002260` | `800.0` | matches fixed 800 |
| recommended phase timing teacher | `10 / 10` | `0.659` | `0.941` | `0.263` | `0.113` | `0.002260` | `1200.0` | best Stage3.7A result |

## Main Finding

Hand/finger residuals are not the right first fix.

The slip peak is not mainly caused by under-gripping. Stronger close residuals
made transient slip worse. Strong relax residuals also made it worse. A tiny
relax-on-slip residual helped only slightly and did not remove the risk flag.

The best improvement came from tactile phase timing:

```text
wait longer in contact_settle before lift
```

This reduced mean max transient slip from `0.816` to `0.659` while preserving:

- success: `10 / 10`
- hold stable fraction: `1.000`
- max crush risk: `0.113`
- max penetration: `0.002260 m`

The same direction also helped on a 30-trial randomized pose probe:

| controller | random offset std | success | mean max slip | max slip | max hold slip | max crush | max penetration |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage3.6 phase hand policy | `0.005 m` | `30 / 30` | `0.882` | `1.000` | `0.263` | `0.129` | `0.002573 m` |
| Stage3.7A phase timing teacher | `0.005 m` | `30 / 30` | `0.707` | `1.000` | `0.330` | `0.129` | `0.002574 m` |

The randomized probe shows a real transient-slip improvement, but also a
tradeoff: max hold slip increased from `0.263` to `0.330`. This is still below
the `0.35` success threshold, but it should be watched before promotion.

## Decision

Do not train a learned hand residual policy from the current hand-residual
teacher labels. The teacher does not improve the task enough to be worth
imitating.

Promote the next Stage3.7 direction as:

```text
tactile-gated phase timing / lift permission
```

instead of:

```text
larger hand/finger close residual
```

## Remaining Risks

`transient_nonhold_slip` still appears in all 10 trials because the max slip
threshold is `0.35` and the best current max slip is still `0.941`.

`early_contact_in_approach` also remains in all 10 trials. This is not solved by
hand residuals. It is an approach/path/timing issue and probably needs:

- safer approach clearance
- earlier vision-to-contact handoff
- approach speed or proxy-position gating
- tactile stop/retreat behavior when contact appears during approach

## Recommended Stage3.7B

Build a tactile phase gate, not a hand residual policy:

1. keep Stage3.6 hand policy as the base controller
2. add a contact-settle gate driven by tactile stability:
   - contact present
   - grip stable
   - slip below threshold for a sustained window
   - minimum settle duration before lift
3. add a lift-permission gate:
   - do not start lift immediately after thumb close
   - only lift after tactile stability is sustained
4. run fixed 10-trial eval
5. then test randomized poses and noisy virtual-camera settings

Promotion criteria:

- fixed success remains `10 / 10`
- mean max transient slip improves beyond `0.659`
- max transient slip moves below `0.941`
- no increase in crush or penetration
- randomized `30 / 30` success remains intact
- max hold slip stays below `0.35`
- early approach contact is either reduced or explicitly moved to a separate
  Stage3.7C approach-gating task
