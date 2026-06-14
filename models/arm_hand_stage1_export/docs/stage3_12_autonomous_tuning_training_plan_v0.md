# Stage3.12 Autonomous Tuning and Training Plan v0

Generated: `2026-06-13`

## Decision

Stage3.12 will proceed as autonomous batch tuning plus bounded training research. The user should see stage results, not one confirmation request per micro-adjustment.

This lane stays MuJoCo-only. It does not promote hardware runtime, real camera, real tactile, ultrasound, direct force control, or full-action 26-actuator ACT/DP.

## Current Anchors

- Robust rollback baseline: Stage3.10E mixed-control safety baseline.
- Small-ball diagnostic/demo anchor: Stage3.11D-I static geometry true-pinch-release candidate.
- D-I current evidence: `136 / 150` multiseed success, `143 / 150` contact gate, `136 / 150` lift gate, `136 / 150` true pinch, `149 / 150` release.
- D-I remaining failure pool: 7 contact-gate failures and 7 lift-gate failures.
- D-I visual evidence: thumb-side hold frame shows `true2tip=True`, `tip=1.00`, `non_tip=0.00`, `wrap=False`.

## Autonomy Rule

The agent may run, reject, and rerun small parameter/training probes without asking for per-candidate approval when all of these stay true:

- The controller surface remains bounded to Stage3 MuJoCo scripts.
- Stage3.10E remains untouched as rollback baseline.
- D-I remains frozen as the current diagnostic/demo anchor.
- Thresholds are not silently relaxed.
- No result is promoted without matched closed-loop metrics and visual evidence when morphology matters.

The agent must stop and report instead of continuing local tuning when either condition is met:

- Two consecutive batches fail to beat or complement D-I on the selected gate.
- A candidate improves success by adding wrap, non-tip contact, floor contact, crush, or unsafe force/current proxy.

## Batch Structure

### Batch 0: Smoke scoreboard

Goal: create a fast, repeatable scoreboard around D-I.

Candidate families:

- `baseline`: D-I exact geometry.
- `contact_entry`: small grasp height and approach/contact geometry variants.
- `lift_continuation`: lift timing and minimum lift gate variants.
- `morphology_clean`: tip separation and active-finger joint variants that may reduce non-tip contact.
- `force_feedback_observation`: simulated force/current telemetry is logged and analyzed, but not used as direct force control.

Gate:

- Same random seed per candidate.
- Small smoke trial count first.
- Rank by full success, then true-pinch success, lift success, contact success, release success, low wrap/non-tip, and safe current proxy.

Output:

- `run_stage3_12_autonomous_tuning_batch_v0.py`
- `data/stage3_12_autotune_batch0_summary_v0.csv`
- `metadata/stage3_12_autotune_batch0_v0.json`
- `docs/stage3_12_autotune_batch0_v0_report.md`

### Batch 1: Final validation

Only the best smoke candidates advance.

Gate:

- At least one 50-trial final run.
- If a candidate clearly beats D-I or offers a cleaner morphology tradeoff, run multiseed validation up to 150 trials.
- Visual check is required before any demo-quality claim.

Promotion target:

- Beat D-I `136 / 150`, or keep near-D-I success while reducing failures or improving visual morphology.
- No regression in true-tip morphology, wrap, non-tip contact, floor contact, crush, penetration, or release.

### Batch 2: Training branch

Only after Batch 0/1 identify a stable target signal.

Training direction:

- Keep `scripted_arm/wrist + learned hand/finger or bounded residual`.
- Use Stage3.11D-D dense sensor-fusion data and LiftQualityHead outputs as quality labels.
- Add morphology labels: true-tip, non-tip, wrap, contact gate, lift gate, release gate.
- Train only a bounded residual or gain/quality head first. Do not promote direct full-action control.

### PID+AI Side Branch

PID+AI stays side-branch only unless it beats the shared gate without morphology or safety regression.

Allowed first step:

- Offline signal analysis over simulated motor force-feedback packets and dense Stage3.11D-D traces.

Allowed controller step after analysis:

- Fixed PD/PID wrapper around the active thumb/finger pair only, with saturation, rate limits, and anti-windup.
- AI gain scheduler may choose bounded gain buckets, but must not directly emit full actuator actions.

## If Successful

Promote only a bounded Stage3.12 candidate that beats or clearly complements D-I under the same evaluation setup, with report, metadata, and visual evidence.

## If Failed

Keep Stage3.10E as robust baseline and D-I as frozen diagnostic/demo anchor. Stop local tuning and move to one of: contact geometry model update, morphology label redesign, or bounded residual/data improvement.
