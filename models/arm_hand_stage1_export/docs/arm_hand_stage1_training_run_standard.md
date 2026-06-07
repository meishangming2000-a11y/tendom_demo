# Arm-Hand Stage1 Training Run Standard

Generated: 2026-06-01

This standard defines how new Stage2 training/evaluation runs should be recorded.
It is intended first for `stage2_pick_place_v0_5`, then reusable for later
lift/hold, pick-place, and two-platform variants.

## Status

- Scope: arm-hand Stage1 export workspace
- First target task: `arm_hand_stage1_pick_place_ball`
- First target dataset: `dataset_v0_5`
- Baseline status: experimental smoke only
- Promotion status: not a maintained baseline until dataset replay QA, online
  evaluation, and visual diagnostics pass

## Core Rule

Training outputs should be organized around a run directory. Videos are not the
source of truth. The source of truth is:

- locked config
- exact command log
- git state
- episode metrics
- replayable traces
- summary report
- compact diagnostic visuals

MP4 files are optional selected presentations, not the default evidence for
every episode.

## Run Directory Layout

Use this layout for each new experiment:

```text
runs/
  stage2_pick_place_v0_5/
    20260601_213000_seed000/
      config.lock.yaml
      command.txt
      git_info.txt
      report.md
      logs/
      checkpoints/
      datasets/
      eval/
        summary.json
        episodes.jsonl
        target_sweep.csv
      traces/
        ep000.npz
      visuals/
        contact_sheet.png
        trajectory_topdown.png
        target_sweep_heatmap.png
        demo_best.mp4
        demo_worst.mp4
        failure_epXXX.mp4
```

Large generated files under `runs/` stay local by default. If a run becomes a
promotion candidate, copy the small report/metadata summary to `docs/` and keep
large media/checkpoints under explicit release or artifact handling.

## Required Files

Every run must contain:

- `config.lock.yaml`
  - task name and contract version
  - dataset/checkpoint names
  - scene path
  - action/observation feature mode
  - seed
  - train/eval limits
  - success/failure thresholds
- `command.txt`
  - exact init command
  - later appended collect/train/eval/render commands
- `git_info.txt`
  - outer repo branch/head/status
  - simulations repo branch/head/status
- `report.md`
  - human-readable summary
  - gate results
  - next command suggestions

## Default Visual Outputs

Every completed evaluation run should produce:

- `contact_sheet.png`
  - fixed key moments: approach, close, lift, transport, descend, release,
    retreat, settle
- `trajectory_topdown.png`
  - ball XY path, target center, target radius, important phase boundaries
- `target_sweep_heatmap.png`
  - pass/fail and target XY error over target offsets

These are the default visual check artifacts.

## Optional MP4 Outputs

Do not render every episode to MP4 by default. Render only selected episodes:

- `demo_best.mp4`
  - best successful episode
- `demo_worst.mp4`
  - worst successful episode or borderline pass
- `failure_epXXX.mp4`
  - one or more representative failures

The run report should always include the command needed to regenerate the video
from trace or from a deterministic replay path.

## MuJoCo Viewer Rule

Each run should include a viewer/replay command so the motion can be inspected
interactively. The intended command shape is:

```powershell
cd D:\tendon_project\simulations
python .\models\arm_hand_stage1_export\view_arm_hand_stage1_run.py --run .\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_213000_seed000 --episode best
```

Until the trace replay viewer is implemented, use the task-specific scripted or
policy demo command listed in the run report.

## Gates

### Dataset Gate

Dataset collection may proceed to training only if replay QA passes:

- replay success count is acceptable for the intended dataset type
- no ball-floor contact during transport
- final target distance is within the configured radius after release
- hand contact after release is below the configured threshold
- stable target steps reach the configured requirement

### Training Gate

Training may proceed to online evaluation only if:

- checkpoint and metadata are written under the run
- validation loss is finite
- feature config in the checkpoint matches `config.lock.yaml`

Low offline loss is not a task success result.

### Evaluation Gate

Evaluation must record:

- fixed-target success rate
- narrow target sweep success rate
- target XY distance min/mean/max
- stable target steps min/mean/max
- transport floor contact count
- release hand contact count
- representative failure reasons

## First Pick-Place v0.5 Policy

For `stage2_pick_place_v0_5`, use a conservative first scope:

- same-platform target pad only
- fixed target plus narrow `+/-0.02 m` diagnostics
- no `+/-0.03 m` training until target-conditioned arm transport exists
- no RL promotion until dataset replay QA and reward/termination QA pass

The expected first BC feature mode is:

```text
obs + phase + target
```

The expected first checkpoint name is:

```text
bc_arm_hand_stage1_v3_pick_place_dataset_v0_5_obs_phase_target.pth
```

## Standard First Command

Initialize a run before collecting data:

```powershell
cd D:\tendon_project\simulations
python .\models\arm_hand_stage1_export\init_arm_hand_stage1_run.py --task stage2_pick_place_v0_5 --seed 0 --config .\models\arm_hand_stage1_export\configs\stage2_pick_place_v0_5.yaml
```

## Post-Gate2 Default Workflow

After Gate2, the default Stage2.5 pick-place workflow is no longer "collect a
large grid first and diagnose later." Use the narrower sequence below:

1. Define the gate in config before running:
   target family, holdout family, required success counts, contact limits, and
   policy interpretation.
2. Probe each new target region first:
   center, a few edges/corners, and a few held-out midpoints.
3. Repair the expert/control path by failure type:
   residual hand contact -> `post_release_clear`; descend/transport floor
   contact -> small `hover_z_lift`; release drift -> tune drop/clear/retreat;
   target miss -> add local experts or a region-specific grid.
4. Only after probes pass, run full collection and replay QA.
5. Promote hard-gated nearest-expert phase MoE as the control baseline.
6. Run fixed targets, local exact sweeps, and held-out midpoint sweeps.
7. Compare any smooth/trainable candidate against the hard-gated baseline on
   the same gates before promotion.
8. Record the final repair parameters in source config, run lock, completion
   report, handoff, and skill memory when they change future behavior.

Gate2 reference:

```text
models/arm_hand_stage1_export/docs/stage2_5_pick_place_training_workflow_after_gate2.md
```
