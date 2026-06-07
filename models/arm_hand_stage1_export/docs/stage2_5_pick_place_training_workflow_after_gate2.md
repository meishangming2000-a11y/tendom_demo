# Stage2.5 Pick-Place Training Workflow After Gate2

Generated: 2026-06-03

## Current Gate Status

Gate2 is complete for the hard-gated nearest-expert phase MoE baseline:

- dataset collection: `79 / 79 PASS`
- replay QA: `79 / 79 PASS`
- fixed 7 targets: `7 / 7 PASS`
- local exact 5x5 around `-165`, `-135`, `-105`: `25 / 25 PASS` for each region
- local held-out midpoint 4x4 around `-165`, `-135`, `-105`: `16 / 16 PASS` for each region
- transport floor contacts: `0`
- final hand contacts max: `0`

Primary report:

```text
models/arm_hand_stage1_export/runs/stage2_pick_place_v0_9_gate2_multiregion_hard_moe/20260603_020000_seed072/eval/gate2_v0_9_hard_moe_completion_report.md
```

## What The Previous Flow Actually Did

The effective flow became:

1. build a scripted expert and task contract
2. collect target-conditioned trajectories
3. run replay QA
4. train or construct a policy candidate
5. run online fixed-target eval
6. run local sweep eval
7. inspect failures
8. repair expert/data/control parameters
9. regenerate dataset and policy evidence
10. record demo/report/handoff

This was the right high-level loop, but it was applied too broadly at first.

## Problems Found

- Full dataset collection was used too early. Gate2 first collected 79 targets and only then revealed a `64 / 79` result.
- Policy search was too wide before the staged baseline was fully mapped. RBF regression, soft MoE, and keypoint variants consumed time but did not beat hard-gated staged control.
- Offline fit was a weak signal. Several candidates fit data but failed online from early closed-loop drift, transport drops, or release instability.
- Failure repair was initially reactive. The useful categories only became clear after reading episode reports: residual hand contact, transport/descend floor contact, target drift, and timeout.
- Videos were useful for presentation, but numeric gates and contact-sheet inspection are the real pass/fail evidence.
- Repair parameters were easy to lose unless written into config/run locks after the successful rerun.

## Optimized Default Workflow

Use this order for Gate3 and later Stage2.5 work.

### 1. Define The Gate Before Running

Write the gate in the config before collecting data:

- target family and holdout family
- required success counts
- contact requirements
- allowed policy interpretation
- stop condition for repair

Do not run a broad collection without knowing what will count as pass/fail.

### 2. Probe New Regions Before Full Collection

For every new target region:

- run the center target
- run 4-8 edge/corner probes
- run 2-4 held-out midpoint probes
- only then collect the full grid

If a new region fails the probe, repair the expert first. Do not add the failed region to the full dataset yet.

### 3. Use A Failure Decision Tree

Map failure to the smallest repair:

| Symptom | Likely cause | First repair |
|---|---|---|
| target XY inside radius but stable steps stay zero | residual hand contact after release | add/increase `post_release_clear_steps` |
| floor contact during `transport` or `descend_to_target` before release | carried ball too low during descent | add small `hover_z_lift`; do not globally lower place pose |
| ball rolls away after release | release push or excessive clear motion | reduce hover lift, tune `pre_release_z_drop`, check release/retreat |
| target miss with no hand contact | wrong nearest expert or sparse region | add local experts or make a region-specific probe grid |
| offline loss low but online fails | closed-loop OOD or phase mixing | fall back to staged hard-gated baseline |

### 4. Promote Baselines In Layers

Use this order:

1. scripted expert success
2. replay QA success
3. hard-gated nearest-expert baseline success
4. local exact sweep success
5. held-out midpoint sweep success
6. perturbation/robustness success
7. only then trainable/smooth policy candidate

Hard-gated MoE is the control baseline. A smoother candidate must beat it on the same gates before promotion.

### 5. Keep Evidence Compact

For every promoted run, keep:

- `config.lock.yaml`
- collection summary
- replay QA summary
- eval JSON and CSV
- completion report
- one representative MP4
- one contact sheet
- handoff update

Do not render every episode unless debugging a specific failure.

### 6. Write Repair Memory Immediately

After a successful repair, update:

- the source config
- `config.lock.yaml` or run report
- completion report
- handoff
- skill memory if the lesson changes future behavior

Gate2 example:

- first collection: `64 / 79 PASS`
- final fix: `post_release_clear_steps=700`
- `-105` region: `pre_release_z_drop=0.012`, `hover_z_lift=0.012`
- final collection/replay/eval: PASS

## Recommended Next Gate

Gate3 should not collect more exact local cells by default.

Recommended Gate3 scope:

- inter-region holdout targets around `-150`, `-120`, and possibly `-97.5`
- small target/initial-ball perturbations
- hard-gated MoE as the control baseline
- success/failure heatmap over target regions
- no smooth-policy claim unless it beats hard-gated MoE on the same holdouts

## One-Sentence Rule

Probe narrowly, repair by failure type, then run the full gate; never use a large dataset run as the first diagnostic for a new target region.
