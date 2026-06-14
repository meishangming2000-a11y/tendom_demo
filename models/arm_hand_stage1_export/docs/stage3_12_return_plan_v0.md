# Stage3.12 Return Plan v0

Generated: `2026-06-13`

## Decision

Stage4.0 is paused after F2. The active project lane returns to Stage3 MuJoCo simulation.

Stage3.12 is a planning/evaluation lane, not an immediate controller rewrite. Its job is to define the next Stage3 experiment with clear baselines, candidates, seeds, metrics, failure taxonomy, reports, and metadata before any controller/model code changes.

## Baselines

- Robust control baseline: Stage3.10E mixed-control safety baseline.
- Frozen diagnostic/demo asset: Stage3.11D-I small-ball true-pinch-release candidate.
- Shadow/data assets: Stage3.11D-D dense sensor-fusion dataset and Stage3.11D-E LiftQualityHead shadow evaluation.
- Readiness artifacts only: Stage4.0-F0/F1/F2 force-feedback packet contract/export/replay.

## Do Not Reopen

- Do not restart open-ended Stage3.11D-I parameter microtuning.
- Do not promote direct force control.
- Do not promote full-action 26-actuator ACT/DP.
- Do not claim real hardware, real camera, real tactile, or ultrasound runtime.
- Do not use Stage4 F3/F4/PID+AI as the current lane unless explicitly reopened.

## Candidate Stage3.12 Branches

Choose one branch only after the gate is written:

1. **Stage3.12-A baseline refresh / evidence audit**
   - Re-run or summarize the current Stage3.10E and Stage3.11D-I evidence.
   - Confirm which demo, evaluator, and metadata are the current comparison anchors.

2. **Stage3.12-B sensor-conditioned evaluation gate**
   - Use existing virtual vision, synthetic tactile/slip, force-feedback telemetry, and LiftQualityHead outputs as observation/evaluator signals.
   - Keep controller changes off until the evaluator/report is defined.

3. **Stage3.12-C bounded controller/model branch**
   - Only after A/B are clear.
   - Compare against Stage3.10E on the same scenes.
   - Preserve Stage3.11D-I as frozen diagnostic evidence.

## Required Gate Before Implementation

Any Stage3.12 implementation must define:

- baseline command and artifact
- candidate command and artifact
- seed list
- object/task set
- success metrics
- failure taxonomy
- visual inspection requirement
- output report path
- output metadata path
- rollback condition

Minimum metrics:

- full success rate
- contact gate
- lift gate
- release gate
- true-pinch/contact morphology when testing small ball
- hold slip
- crush risk
- penetration
- floor contact
- visual confidence / final vision evidence where applicable

## If Successful

Promote only the bounded Stage3.12 branch that beats or clearly complements Stage3.10E under the same evaluation setup.

## If Failed

Keep Stage3.10E as robust baseline, keep Stage3.11D-I frozen as diagnostic/demo asset, and revise labels/evaluator/data coverage before changing controller code.
