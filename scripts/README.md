# Scripts Overview

This directory contains runnable entrypoints for the `simulations/` subproject.

## Canonical Mainline Scripts

For the current official mainline, use:

- `collect_expert_data.py`
- `analyze_pre_grasp_dataset.py`
- `train_bc.py`
- `eval_bc.py`

These four scripts form the maintained `pre_grasp` loop:

`expert -> dataset -> BC train -> eval -> report`

Recommended command sequence:

```bash
python scripts/collect_expert_data.py --task pre_grasp --episodes 40 --max-steps 200 --placement-mode demo --placement-jitters 0.02,0.04 --pre-grasp-gain-scale 1.0 --pre-grasp-clip-scale 1.0 --pre-grasp-start-bias 0.01,0.0,-0.005 --pre-grasp-target-offset 0.008,0.0165,0.0 --output data/expert_pre_grasp_mixed_v2.npz --report reports/expert_pre_grasp_mixed_v2.json
python scripts/analyze_pre_grasp_dataset.py --data data/expert_pre_grasp_mixed_v2.npz --report reports/pre_grasp_dataset_analysis_v2.json
python scripts/train_bc.py --task pre_grasp --data data/expert_pre_grasp_mixed_v2.npz --success-only --epochs 20 --batch-size 128 --hidden-dim 128 --output models/bc_pre_grasp_v2.pth
python scripts/eval_bc.py --model models/bc_pre_grasp_v2.pth --episodes 20 --no-viewer --placement-mode demo --placement-jitter 0.02 --report reports/bc_pre_grasp_v2_eval_j002.json
python scripts/eval_bc.py --model models/bc_pre_grasp_v2.pth --episodes 20 --no-viewer --placement-mode demo --placement-jitter 0.04 --report reports/bc_pre_grasp_v2_eval_j004.json
```

## Script Roles

- `collect_expert_data.py`
  Canonical expert-trajectory collection entry.
- `analyze_pre_grasp_dataset.py`
  Canonical dataset inspection entry for the current maintained task.
- `train_bc.py`
  Canonical BC training entry.
- `eval_bc.py`
  Canonical BC evaluation entry.

## Reference Or Legacy Scripts

The following scripts are still kept, but they are not the recommended starting point for new mainline work:

- `demo_grasp.py`
  Reference controller demo and debugging entry.
- `demo_bc.py`
  Reference viewer demo for older BC showcase flows.
- `demo_catch_bc.py`
  Reference wrapper around the older catch-task BC demo.
- `run_catch_baseline.py`
  Historical catch baseline pipeline.
- `diagnostics/`
  Utilities for targeted checks and validation.
- `data_tools/`
  Support utilities for inspection, inventory, merging, and visualization.
- `archive/`
  Historical debugging and experiment scripts kept for reference.

## Compatibility Note

Some scripts still keep generic legacy defaults such as:

- `data/expert_data.npz`
- `models/bc_model.pth`

Those defaults exist for compatibility only. New work should use task-qualified names such as `expert_pre_grasp_*` and `bc_pre_grasp_*`.

## Naming Note

Use these patterns for new experiment assets:

- Datasets: `expert_<task>_<tag>.npz`
- Dataset reports: `expert_<task>_<tag>.json`
- Dataset analyses: `<task>_dataset_analysis_<tag>.json`
- Checkpoints: `bc_<task>_<tag>.pth`
- Eval reports: `bc_<task>_<tag>_eval_<condition>.json`

Prefer:

- `vN` for promoted baselines
- `smoke` for disposable validation artifacts
- explicit condition tags such as `j002` or `j004`

## Minimal Protocol Smoke Path

For the current `stable_grasp` protocol layer, the lowest-cost diagnostic entry is:

```bash
python scripts/diagnostics/smoke_task_contracts.py
```

This is a structure smoke test for:

- `pre_grasp` transition input
- transition readiness output
- `stable_grasp` official-vs-debug evaluation payload

It is not a training or benchmark script.

## Minimal Structured Rollout Path

For the current episode-level structured evaluation path, use:

```bash
python scripts/diagnostics/structured_rollout_eval.py
```

The diagnostic rollout now supports:

```bash
python scripts/diagnostics/structured_rollout_eval.py --stable-grasp-phase-mode scripted_controller
python scripts/diagnostics/structured_rollout_eval.py --stable-grasp-phase-mode zero_action
```

This diagnostic path demonstrates:

- `pre_grasp` transition input generation
- transition readiness output
- stable_grasp entry snapshot creation
- stable_grasp episode-level summary generation
- official JSON report payload generation

By default, debug metrics are excluded from the saved report payload.
This path may use diagnostic-only state preparation to build a minimal transition-ready entry. It is not a trained policy evaluation path and not the official batch-eval entry.

## Minimal Batch Eval Harness

For the current `stable_grasp` batch-eval harness, use:

```bash
python scripts/diagnostics/batch_eval_stable_grasp.py --eval-mode environment_only --stable-grasp-phase-mode scripted_controller
```

This path is:

- environment-driven
- batch-oriented
- able to emit per-episode summaries plus an aggregated official batch report
- able to emit a separate behavior-audit artifact for scripted-controller diagnosis

It still is not a trained-policy benchmark baseline.

Optional output paths:

- `--report`
  save the combined official-report plus behavior-audit artifact
- `--official-report`
  save the official report only
- `--audit-report`
  save the behavior-audit artifact only

Diagnostic seeded variant:

```bash
python scripts/diagnostics/batch_eval_stable_grasp.py --eval-mode diagnostic_seeded --stable-grasp-phase-mode scripted_controller
```

Use the seeded variant only for protocol verification and report-chain checks.

Compatibility mode:

```bash
python scripts/diagnostics/batch_eval_stable_grasp.py --eval-mode environment_only --stable-grasp-phase-mode zero_action
```

`scripted_controller` is now the recommended phase mode. `zero_action` remains for compatibility only.

Current output boundary:

- `official_report`
  official task metrics and terminal fields only
- `behavior_audit`
  analysis-only controller audit, failure attribution, and temporary collection readiness
- `debug`
  optional rollout traces only when explicitly requested

## Entry Snapshot Ownership

Current `stable_grasp` entry snapshot ownership is:

- canonical owner
  rollout evaluator / pipeline handoff layer
- fallback owner
  `stable_grasp` checker

`structured_rollout_eval.py` and `batch_eval_stable_grasp.py` both consume the same canonical creation helper. `entry_source` in the report payload records whether the snapshot came from transition-time handoff or checker fallback.

## Stable Grasp Scripted Controller

Current location:

- `common/grasp_workflow.py`

Current role:

- temporary Shadow backend scripted controller for `stable_grasp`
- minimal joint-level close-and-stabilize continuation
- intended to replace zero-action continuation in rollout validation

It is explicitly not a learned policy, not a benchmark policy, and not a real-hand controller.

Current audit note:

- the scripted controller is paired with a temporary collection gate in the batch-eval audit layer
- episodes that pass the gate are only provisional temporary data-source candidates
- the controller is still not a promoted stable_grasp expert baseline
- the gate applies only to `stable_grasp_phase_mode=scripted_controller`; `zero_action` stays comparison-only

## Read Next

- `../README.md`
- `../reports/README.md`
- `../../docs/current_status.md`
