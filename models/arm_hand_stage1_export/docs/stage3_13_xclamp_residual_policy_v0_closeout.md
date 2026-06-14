# Stage3.13 X-Clamp Residual Policy v0 Closeout

Generated: `2026-06-14`

## Boundary

- MuJoCo-only teacher distillation from the Stage3.12C directional x-clamp teacher.
- Action surface is a bounded `grasp_offset_x` residual before IK.
- This is not full-action ACT/DP, not hardware runtime, not real camera/tactile integration, and not demo-gallery promotion.
- Stage3.10E remains the robust mixed-control baseline; Stage3.11D-I remains the frozen demo-quality diagnostic candidate.

## What Changed

Stage3.13A converts the Stage3.12C rule teacher into a learned residual policy:

```text
randomized planning context -> bounded grasp-x residual -> safety clamp -> IK -> existing event controller
```

The teacher target is the difference between the raw randomized `grasp_offset_x`
and the Stage3.12C clamp corridor `[-0.0025, 0.0000]`.

## Dataset And Training

- Dataset: `data/stage3_13_xclamp_residual_policy_dataset_v0.npz`
- Episodes: `300`
- Residual-active labels: `115 / 300` (`0.383`)
- Mean/max absolute target residual: `0.000149 / 0.000883 m`
- Checkpoint: `checkpoints/stage3_13_xclamp_residual_policy_v0.pth`
- Validation MAE: `0.00001579 m`
- Validation max absolute error: `0.00008205 m`

## Matched Closed-Loop Gate

Shared gate: three 50-trial seeds `20260612`, `20265612`, and `20265613`.

| mode | success | contact | lift | true pinch | release | hold non-tip | floor | wrap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| frozen D-I | 136 / 150 | 143 | 136 | 136 | 149 | 0.0677 | 0.0280 | 0.0000 |
| Stage3.12C teacher x-clamp | 143 / 150 | 146 | 143 | 143 | 149 | 0.0569 | 0.0120 | 0.0000 |
| Stage3.13 learned residual safe | 143 / 150 | 146 | 143 | 143 | 149 | 0.0573 | 0.0123 | 0.0000 |

Terminal reasons for learned residual safe:

```text
success_event_contact_gated_true_pinch_release_ball: 143
lift_gate_failed: 3
contact_gate_failed: 4
```

## Decision

Advance Stage3.13A as a distilled residual-policy candidate because it:

- matches the Stage3.12C teacher on the same multiseed gate,
- beats frozen D-I by `+7 / 150`,
- does not add true-pinch morphology failures,
- keeps wrap at `0.0`.

This does not mean the learned policy is stronger than the 12C teacher yet. It
means the hand-written x-corridor repair has been converted into a trainable
residual policy surface.

## Residual Behavior Note

The learned safe policy predicted a small nonzero residual on every eval trial,
then the safety clamp clipped `43 / 150` trials. This is acceptable for the
first distillation gate, but the next model pass should add deadband/calibration
or an active-gate head so the policy does not become unnecessarily always-on.

## Visual Check

Rendered sample: seed `20265613`, trial `0`, learned-safe policy.

- Status: `PASS`
- Contact/lift/true-pinch/release: `true / true / true / true`
- Hold lift max: `0.11406 m`
- Hold true two-tip fraction: `1.000`
- Hold tip contact ratio: `1.000`
- Hold non-tip contact ratio: `0.000`
- Hold wrap fraction: `0.000`

Observed: the hold frame shows thumb + middle pinching the ball from opposite
sides without visible wrap or palm/support contact; release opens the hand and
the ball settles on the floor.

## Next

If success:

```text
Stage3.13B should keep the same 143 / 150 matched gate while adding residual
deadband/active gating, then test whether contact/lift failures can be reduced
without increasing non-tip/floor contact.
```

If failure:

```text
Keep Stage3.12C as the selected teacher and move to contact-geometry modeling
instead of returning to open-ended D-I parameter tuning.
```

## Artifacts

- Runner: `run_stage3_13_xclamp_residual_policy_v0.py`
- Report: `docs/stage3_13_xclamp_residual_policy_v0_report.md`
- Metadata: `metadata/stage3_13_xclamp_residual_policy_v0.json`
- Selected metadata: `metadata/stage3_13_xclamp_residual_policy_selected_v0.json`
- Dataset: `data/stage3_13_xclamp_residual_policy_dataset_v0.npz`
- Dataset summaries: `data/stage3_13_xclamp_residual_policy_dataset_v0.jsonl`
- Checkpoint: `checkpoints/stage3_13_xclamp_residual_policy_v0.pth`
- Summary CSV: `data/stage3_13_xclamp_residual_policy_v0_summary.csv`
- Visual contact sheet: `docs/stage3_13_xclamp_residual_policy_visual_v0/trial0_seed20265613_learned_safe_contact_sheet.png`
- Visual summary: `docs/stage3_13_xclamp_residual_policy_visual_v0/trial0_seed20265613_learned_safe_summary.json`
