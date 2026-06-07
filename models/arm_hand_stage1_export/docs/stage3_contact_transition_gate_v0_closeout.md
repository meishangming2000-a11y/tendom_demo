# Stage3.7C Contact Transition Gate V0 Closeout

Generated: 2026-06-05

## Purpose

Stage3.7C continued the Stage3.7B repair path. Stage3.7B improved mean slip by
waiting for tactile stability before lift, but the remaining slip peaks were
still clustered around:

- `contact_settle`
- `gentle_close_thumb`
- `slow_lift`

Stage3.7C tested whether contact-transition pauses could reduce those peaks
without changing the learned hand policy.

This work is still MuJoCo-only:

```text
virtual camera pose
+ scripted arm/wrist
+ Stage3.6 learned hand/finger policy
+ Stage3.7B tactile lift-permission gate
+ Stage3.7C slow-lift transition pause
```

No real camera or hardware interface is used.

## New Script

Evaluation script:

```text
models/arm_hand_stage1_export/eval_stage3_contact_transition_gate_v0.py
```

Selected default:

- stop approach on contact: `False`
- transition gate phases: `slow_lift`
- transition slip threshold: `0.28`
- max transition hold steps per phase: `150`
- contact-settle gate: `2000` min / `2000` max steps

The transition gate pauses `slow_lift` progress when post-step tactile slip is
high. It does not change hand/finger residuals or retrain the model.

Primary fixed-trial report:

```text
models/arm_hand_stage1_export/docs/stage3_contact_transition_gate_v0_eval_report.md
```

Primary fixed-trial metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_contact_transition_gate_v0_eval.json
```

Randomized 30-trial report:

```text
models/arm_hand_stage1_export/docs/stage3_contact_transition_gate_v0_randomized30_report.md
```

Randomized 30-trial metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_contact_transition_gate_v0_randomized30.json
```

## Fixed 10-Trial Result

Stage3.7C selected default passed the fixed gate:

- success: `10 / 10`
- mean final lift: `0.103126 m`
- hold stable fraction: `1.000`
- mean max transient slip: `0.564`
- max transient slip: `0.941`
- max hold slip: `0.264`
- max crush risk: `0.111`
- max penetration: `0.002223 m`
- mean transition hold steps: `108.3`

Comparison:

| controller | success | mean max slip | max slip | max hold slip | max crush | max penetration |
|---|---:|---:|---:|---:|---:|---:|
| Stage3.6 phase hand policy | `10 / 10` | `0.816` | `1.000` | `0.262` | `0.113` | `0.002260 m` |
| Stage3.7A timing teacher | `10 / 10` | `0.659` | `0.941` | `0.263` | `0.113` | `0.002260 m` |
| Stage3.7B phase gate | `10 / 10` | `0.598` | `0.941` | `0.263` | `0.111` | `0.002223 m` |
| Stage3.7C slow-lift pause | `10 / 10` | `0.564` | `0.941` | `0.264` | `0.111` | `0.002223 m` |

## Probe Matrix

| probe | success | mean max slip | max slip | max hold slip | interpretation |
|---|---:|---:|---:|---:|---|
| post-step pause + approach stop | `10 / 10` | `0.574` | `0.965` | `0.348` | improves mean, hold too close to threshold |
| no approach stop, broad pause | `9 / 10` | `0.584` | `0.986` | `0.373` | failed hold slip |
| hold budget 200 | `10 / 10` | `0.582` | `0.965` | `0.258` | stable hold, worse max slip |
| slip threshold 0.35 | `9 / 10` | `0.572` | `0.965` | `0.388` | failed hold slip |
| slow-lift only, hold 200 | `10 / 10` | `0.582` | `0.965` | `0.258` | stable but worse max slip |
| no approach stop + slow-lift hold 200 | `10 / 10` | `0.569` | `0.941` | `0.326` | better mean, hold tradeoff |
| no approach stop + slow-lift hold 100 | `10 / 10` | `0.566` | `0.941` | `0.261` | good conservative variant |
| no approach stop + slow-lift hold 150 | `10 / 10` | `0.564` | `0.941` | `0.264` | selected default |

Main lesson:

```text
Do not stop approach early by default.
Do not pause thumb close by default.
Pause slow_lift briefly when slip is high.
```

## Randomized 30-Trial Result

Random pose perturbation:

```text
random_offset_std = 0.005 m
```

Stage3.7C randomized result:

- success: `30 / 30`
- mean final lift: `0.103054 m`
- hold stable fraction: `1.000`
- mean max transient slip: `0.602`
- max transient slip: `1.000`
- max hold slip: `0.315`
- max crush risk: `0.127`
- max penetration: `0.002542 m`
- mean transition hold steps: `109.5`

Comparison:

| controller | random offset std | success | mean max slip | max slip | max hold slip | max crush | max penetration |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage3.6 phase hand policy | `0.005 m` | `30 / 30` | `0.882` | `1.000` | `0.263` | `0.129` | `0.002573 m` |
| Stage3.7A timing teacher | `0.005 m` | `30 / 30` | `0.707` | `1.000` | `0.330` | `0.129` | `0.002574 m` |
| Stage3.7B phase gate | `0.005 m` | `30 / 30` | `0.625` | `1.000` | `0.318` | `0.127` | `0.002542 m` |
| Stage3.7C slow-lift pause | `0.005 m` | `30 / 30` | `0.602` | `1.000` | `0.315` | `0.127` | `0.002542 m` |

Stage3.7C therefore improves randomized mean max slip while preserving success
and keeping hold slip below `0.35`.

## Decision

Promote Stage3.7C as the current Stage3 learned-control baseline:

```text
scripted arm/wrist
+ Stage3.6 learned hand/finger policy
+ Stage3.7B tactile lift-permission gate
+ Stage3.7C slow-lift transition pause
```

Do not promote:

- approach stop on contact
- broad transition pause across thumb close and slow lift
- threshold-only variants that push hold slip over `0.35`

## Remaining Risks

`transient_or_hold_slip` remains in every fixed and randomized episode because
the full-episode max slip still exceeds `0.35`.

`transition_gate_budget_exhausted` appears in `6 / 10` fixed episodes and
`19 / 30` randomized episodes. This means the pause budget is useful but not a
complete recovery behavior.

The remaining worst peaks are split across:

- `contact_settle`
- `gentle_close_thumb`
- `slow_lift`

Recommended next task:

```text
Stage3.7D contact-transition recovery:
replace simple slow-lift pause with an explicit recovery micro-phase that can
slightly lower lift, hold, and retry; separately test contact_settle and thumb
transition recovery without pushing hold slip above 0.35.
```
