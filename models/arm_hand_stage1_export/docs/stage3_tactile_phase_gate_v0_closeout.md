# Stage3.7B Tactile Phase Gate V0 Closeout

Generated: 2026-06-05

## Purpose

Stage3.7B formalized the useful Stage3.7A finding:

```text
use tactile phase timing / lift permission instead of hand residuals
```

The controller remains MuJoCo-only:

```text
virtual camera pose
+ scripted arm/wrist
+ Stage3.6 learned hand/finger policy
+ tactile-gated phase timing before lift
```

No real camera or hardware interface is used.

## New Script

Evaluation script:

```text
models/arm_hand_stage1_export/eval_stage3_tactile_phase_gate_v0.py
```

Default Stage3.7B parameters:

- approach steps: `320`
- min contact-settle steps: `2000`
- max contact-settle steps: `2000`
- stable window steps: `300`
- gate slip threshold: `0.18`
- gate crush threshold: `0.35`
- gate penetration threshold: `0.004 m`

The gate opens only after tactile stability is sustained. The report records
whether each episode was released by `stable_window_met` or forced by the max
step limit.

Primary fixed-trial report:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_phase_gate_v0_eval_report.md
```

Primary fixed-trial metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_tactile_phase_gate_v0_eval.json
```

Randomized 30-trial report:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_phase_gate_v0_randomized30_report.md
```

Randomized 30-trial metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_tactile_phase_gate_v0_randomized30.json
```

## Fixed 10-Trial Result

Stage3.7B passed the fixed gate:

- success: `10 / 10`
- gate release reasons: `stable_window_met` in all `10` episodes
- mean final lift: `0.103110 m`
- hold stable fraction: `1.000`
- mean max transient slip: `0.598`
- max transient slip: `0.941`
- max hold slip: `0.263`
- max crush risk: `0.111`
- max penetration: `0.002223 m`

Comparison:

| controller | success | mean max slip | max slip | max hold slip | max crush | max penetration |
|---|---:|---:|---:|---:|---:|---:|
| Stage3.6 phase hand policy | `10 / 10` | `0.816` | `1.000` | `0.262` | `0.113` | `0.002260 m` |
| Stage3.7A timing teacher | `10 / 10` | `0.659` | `0.941` | `0.263` | `0.113` | `0.002260 m` |
| Stage3.7B phase gate | `10 / 10` | `0.598` | `0.941` | `0.263` | `0.111` | `0.002223 m` |

Interpretation:

```text
Stage3.7B improves mean transient slip and preserves success, hold stability,
crush margin, and penetration margin.
```

It does not eliminate the worst transient peak. After the selected timing
change, the fixed 10-trial peak phases were:

- `contact_settle`: `4`
- `gentle_close_thumb`: `2`
- `slow_lift`: `4`

That means the remaining risk is no longer a simple "lift starts too early"
problem. It is a contact-transition problem around close, settle, and lift.

## Probe Matrix

| probe | success | mean max slip | max slip | max hold slip | interpretation |
|---|---:|---:|---:|---:|---|
| settle 1600 | `10 / 10` | `0.646` | `0.941` | `0.263` | improves Stage3.7A, not enough |
| approach 320 + settle 1600 | `10 / 10` | `0.601` | `0.941` | `0.263` | approach timing helps |
| approach 400 + settle 1600 | `10 / 10` | `0.628` | `1.000` | `0.263` | too slow/worse |
| thumb 300 + settle 1600 | `10 / 10` | `0.671` | `1.000` | `0.263` | slower thumb close is worse |
| approach 320 + settle 2000 | `10 / 10` | `0.598` | `0.941` | `0.263` | selected default |

## Randomized 30-Trial Result

Random pose perturbation:

```text
random_offset_std = 0.005 m
```

Stage3.7B randomized result:

- success: `30 / 30`
- gate release reasons: `stable_window_met` in all `30` episodes
- mean final lift: `0.103031 m`
- hold stable fraction: `1.000`
- mean max transient slip: `0.625`
- max transient slip: `1.000`
- max hold slip: `0.318`
- max crush risk: `0.127`
- max penetration: `0.002542 m`

Comparison:

| controller | random offset std | success | mean max slip | max slip | max hold slip | max crush | max penetration |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage3.6 phase hand policy | `0.005 m` | `30 / 30` | `0.882` | `1.000` | `0.263` | `0.129` | `0.002573 m` |
| Stage3.7A timing teacher | `0.005 m` | `30 / 30` | `0.707` | `1.000` | `0.330` | `0.129` | `0.002574 m` |
| Stage3.7B phase gate | `0.005 m` | `30 / 30` | `0.625` | `1.000` | `0.318` | `0.127` | `0.002542 m` |

Stage3.7B is therefore better than Stage3.7A on randomized mean max slip and
has a lower max hold slip while preserving `30 / 30` success.

## Decision

Promote Stage3.7B as the current Stage3 learned-control baseline:

```text
scripted arm/wrist
+ Stage3.6 learned hand/finger policy
+ conservative tactile-gated phase timing
```

Do not train from the Stage3.7A hand-residual teacher dataset. Those labels came
from a diagnostic direction that did not improve the task.

## Remaining Risks

`transient_or_hold_slip` remains in every fixed and randomized episode because
the full-episode max slip still exceeds `0.35`.

The remaining worst peaks are not solved by waiting longer before lift. In the
randomized 30-trial run, the top-slip phases were:

- `slow_lift`: `15`
- `contact_settle`: `8`
- `gentle_close_thumb`: `7`

`early_contact_in_approach` also remains as a separate risk flag, even though
the selected slower approach reduced approach-phase peak slip.

Recommended next task:

```text
Stage3.7C approach/contact gate:
detect early tactile contact during approach or thumb close, pause/retreat or
re-align before continuing, then re-test the same fixed and randomized gates.
```
