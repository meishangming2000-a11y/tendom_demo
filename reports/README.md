# Reports And Experiment Assets

This folder stores JSON evaluation outputs, dataset summaries, and handoff notes for the `simulations/` subproject.

## Purpose

Use `reports/` for:

- machine-readable JSON outputs from collection and evaluation scripts
- promoted summary documents and inventories
- handoff notes that explain which assets are current and which are comparison-only

Do not treat every file here as a current baseline. Some files are:

- promoted references
- comparison artifacts
- historical showcase outputs

## Current Promoted Pre-Grasp Baseline

As of 2026-03-20, the current promoted `pre_grasp` reference set is:

- Dataset: `data/expert_pre_grasp_mixed_v2.npz`
- Collection report: `reports/expert_pre_grasp_mixed_v2.json`
- Dataset analysis: `reports/pre_grasp_dataset_analysis_v2.json`
- Checkpoint: `models/bc_pre_grasp_v2.pth`
- Eval reports:
  - `reports/bc_pre_grasp_v2_eval_j002.json`
  - `reports/bc_pre_grasp_v2_eval_j004.json`

Comparison-only controller tuning artifacts currently include:

- `*_g11_c11.*`

These are useful for reference but are not yet promoted over `v2`.

## Secondary Historical References

Still useful, but not the current mainline:

- Static showcase:
  - `data/expert_showcase_v5_50x400.npz`
  - `models/bc_showcase_v5_success400_phase_h128_80ep.pth`
  - `reports/bc_showcase_v5_success400_demo_20_ramp160.json`
- Catch baseline:
  - `data/expert_catch_v2_j002_f030_50x300.npz`
  - `models/bc_catch_v2_j002_f030_40ep_h128.pth`
  - `reports/bc_catch_v2_j002_f030_40ep_h128_eval_20x300.json`

## Naming Convention

Keep future artifact names consistent across `data/`, `models/`, and `reports/`.

- Datasets: `expert_<task>_<tag>.npz`
- Dataset reports: `expert_<task>_<tag>.json`
- Dataset analyses: `<task>_dataset_analysis_<tag>.json`
- Checkpoints: `bc_<task>_<tag>.pth`
- Eval reports: `bc_<task>_<tag>_eval_<condition>.json`

Recommended tag meanings:

- `vN`
  Promoted baseline version.
- `smoke`
  Temporary or lightweight validation run.
- `j002`, `j004`
  Condition-specific jitter shorthand for `0.02`, `0.04`.
- `g11_c11`
  Controller-tuning comparison tag, not a promoted baseline by itself.

## Archive Policy

- If an artifact is superseded but still worth preserving, move or conceptually treat it as archival.
- Keep promoted assets near the top level of `data/`, `models/`, and `reports/`.
- Prefer `archive/` for historical experiments rather than deleting them immediately.

See `reports/slimming_manifest_2026-03-14.md` for the earlier keep/archive decision, but note that the current `pre_grasp` baseline post-dates that manifest.

## Inventories And Handoff

- `reports/dataset_inventory.md`
  Generated dataset summary. Useful, but not the sole source of truth for promoted baselines.
- `reports/next_steps_handoff_2026-03-20.md`
  Current handoff note and project cleanup guidance.
