# Stage3.12C Quality-Gated Residual Teacher v0 Closeout

Generated: `2026-06-13`

## Boundary

- MuJoCo-only Stage3 small-ball true-pinch-release work.
- Uses virtual vision, synthetic contact/tactile morphology, and simulated motor force-feedback proxies.
- Adds an optional Stage3.12B quality-head hook to the event runner, but does not promote full-action ACT/DP, real camera, real tactile, ultrasound, or hardware runtime.
- No demo-gallery promotion is made here.

## What Changed

Stage3.12C moved from open-ended parameter microtuning to failure-window-driven teacher design:

```text
simulations/models/arm_hand_stage1_export/run_stage3_12c_quality_gated_residual_teacher_v0.py
```

It also added a non-default quality predictor hook to:

```text
simulations/models/arm_hand_stage1_export/train_stage3_11d_b_event_contact_gated_refine_v0.py
```

Default event-runner behavior is unchanged. The hook is only active when Stage3.12C passes a callable quality predictor into the event runner.

## Failure Window Mining

The formal Stage3.12C run mined frozen D-I evidence windows before intervention:

- Evidence frames: `764`
- Low-quality frames: `189` (`0.247`)
- Low-quality phases: `{'contact_gate': 135, 'slow_lift': 43, 'post_contact_settle': 9, 'hold': 2}`
- Low-quality terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 145, 'contact_gate_failed': 44}`

Interpretation: the main remaining bottleneck is not late contact that can be solved by waiting. It is the contact-entry target corridor, especially noisy `grasp_offset_x` excursions.

## Candidate Result

Selected candidate:

```text
di_directional_gx_clamp_m0025_p0000
```

Teacher rule:

```text
clamp per-trial grasp_offset_x to [-0.0025, 0.0000] before IK
```

This is a bounded vision-directional teacher. It does not change the nominal D-I center and does not add finger-force close residual by default.

## Matched 50-Trial Validation

Command output is in:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_12c_quality_gated_residual_teacher_v0_report.md
simulations/models/arm_hand_stage1_export/metadata/stage3_12c_quality_gated_residual_teacher_v0.json
```

Same seed validation:

| variant | success | contact | lift | true pinch | release | terminal reasons |
|---|---:|---:|---:|---:|---:|---|
| `di_directional_gx_clamp_m0025_p0000` | `49 / 50` | `49` | `49` | `49` | `50` | `{'success_event_contact_gated_true_pinch_release_ball': 49, 'contact_gate_failed': 1}` |
| `baseline_di_off` | `46 / 50` | `48` | `46` | `46` | `50` | `{'success_event_contact_gated_true_pinch_release_ball': 46, 'lift_gate_failed': 2, 'contact_gate_failed': 2}` |

## Multiseed Gate

Matched seeds:

```text
20260612
20265612
20265613
```

Aggregate result:

| variant | success | contact | lift | true pinch | release | terminal reasons |
|---|---:|---:|---:|---:|---:|---|
| `di_directional_gx_clamp_m0025_p0000` | `143 / 150` | `146` | `143` | `143` | `149` | `{'success_event_contact_gated_true_pinch_release_ball': 143, 'lift_gate_failed': 3, 'contact_gate_failed': 4}` |
| frozen `D-I` | `136 / 150` | `143` | `136` | `136` | `149` | `{'success_event_contact_gated_true_pinch_release_ball': 136, 'lift_gate_failed': 7, 'contact_gate_failed': 7}` |

Delta versus D-I:

- Success: `+7 / 150`
- Contact failures: `7 -> 4`
- Lift failures: `7 -> 3`
- True-pinch morphology failures: no increase
- Release: unchanged at `149 / 150`

Morphology aggregate:

| variant | hold non-tip mean | hold wrap mean | hold floor mean | max penetration |
|---|---:|---:|---:|---:|
| `di_directional_gx_clamp_m0025_p0000` | `0.0569` | `0.0000` | `0.0120` | `0.00595 m` |
| frozen `D-I` | `0.0677` | `0.0000` | `0.0280` | `0.00604 m` |

## Visual Check

Clean selected visual sample:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_12c_directional_xclamp_visual_v0/trial0_seed20265613_clean_contact_sheet.png
```

Observed in the rendered clean sample:

- `PASS`
- contact/lift/true-pinch/release all true
- hold `true_two_tip_pinch_fraction = 1.0`
- hold `tip_contact_ratio_mean = 1.0`
- hold `non_tip_contact_ratio_mean = 0.0`
- hold `wrap_frame_fraction = 0.0`
- release opens the fingers and the ball settles back to the floor

An edge corrective sample is retained as diagnostic only:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_12c_directional_xclamp_visual_v0/trial0_seed20260618_clamped_contact_sheet.png
```

That sample fixes a baseline contact failure, but has some non-tip contact (`0.333` mean), so it is not the preferred polished demo image.

## Rejected Or Diagnostic Branches

These did not earn promotion:

- contact-gate extension alone: did not improve the failure structure;
- quality-head wait/close residual: triggered but did not improve success in smoke;
- PID-like force-feedback wait/preload: triggered heavily, but did not beat D-I and showed higher penetration in smoke;
- tighter x clamp `[-0.0023, -0.0002]`: improved lift count in smoke but introduced a morphology failure.

## Decision

Promote `di_directional_gx_clamp_m0025_p0000` as the Stage3.12C selected robustness/teacher candidate.

Do not promote the quality-close or PID-like residual branches to the main controller. They remain diagnostic evidence that the current short-horizon force/close residual is not the winning control surface.

Frozen D-I remains the cleaner historical demo anchor, while Stage3.12C is the stronger robustness candidate and the better teacher for the next data/model step.

## Next

Stage3.12 can now close with a real improvement. The useful next step is not more local hand tuning; it is to turn the directional x-clamp teacher into residual-policy data:

```text
vision/contact state -> bounded grasp-x residual
```

Then Stage3.13 can train a small residual policy and compare it against this teacher and frozen D-I on the same multiseed gate.
