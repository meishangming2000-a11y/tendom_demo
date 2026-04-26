# Next Steps And Handoff

Date: 2026-03-20

## Current Truth

The current maintained learning pipeline is:

`pre_grasp expert -> dataset -> BC -> eval -> report`

Promoted reference assets:

- `data/expert_pre_grasp_mixed_v2.npz`
- `reports/expert_pre_grasp_mixed_v2.json`
- `reports/pre_grasp_dataset_analysis_v2.json`
- `models/bc_pre_grasp_v2.pth`
- `reports/bc_pre_grasp_v2_eval_j002.json`
- `reports/bc_pre_grasp_v2_eval_j004.json`

Interpretation:

- The `pre_grasp` expert is no longer a zero-action placeholder.
- The data is non-degenerate and learnable.
- BC learns non-zero reach-like behavior.
- Robustness at `placement_jitter=0.04` is still limited, so the project should not jump to `stable_grasp` yet.

## What Is Core vs Historical

Core for active work:

- `src/environments/shadow_grasp_env.py`
- `src/controllers/`
- `tasks/`
- `observations/`
- `scripts/collect_expert_data.py`
- `scripts/analyze_pre_grasp_dataset.py`
- `scripts/train_bc.py`
- `scripts/eval_bc.py`
- `scripts/common/grasp_workflow.py`

Historical or secondary:

- static showcase assets (`showcase_v*`)
- catch baseline assets (`catch_v*`)
- `project_state.md`
- `claude_contest.md`
- root-level one-off utilities like `analyze_actions.py` and `check_dataset_quality.py`
- `scripts/archive/`

## Current Engineering Issues

1. Documentation is split between an older static-showcase story and the newer `pre_grasp` mainline.
2. Some scripts still use generic legacy default names such as `expert_data.npz` and `bc_model.pth` for compatibility.
3. Root-level utility scripts overlap with maintained tools under `scripts/`.
4. Naming is mostly consistent for new `pre_grasp` assets, but not yet uniformly documented across the project.
5. The keep/archive manifest predates the new `pre_grasp` baseline and should be interpreted carefully.

## Minimal Cleanup Policy

Do:

- keep the current folder structure
- keep legacy CLI defaults for backward compatibility
- document the promoted `pre_grasp` baseline clearly
- steer new work toward task-qualified names
- keep future extensions inside the existing task/observation/script seams

Do not do yet:

- large directory moves
- deleting historical reports in bulk
- collapsing static, catch, and pre_grasp flows into one framework
- changing BC algorithm or task scope

## Extension Interfaces To Preserve

For new controllers:

- extend `scripts/common/grasp_workflow.py`
- keep controller parameters recorded in dataset metadata

For new data filtering:

- add a dedicated stage between dataset analysis and `train_bc.py`
- avoid baking filtering logic irreversibly into collection

For new policies:

- keep checkpoint metadata explicit:
  - `structured_task_name`
  - `task_name`
  - `task_kwargs`
  - `observation_mode`
  - dataset provenance fields

For real-to-sim / sim-to-real:

- extend `observations/` first
- keep task logic in `tasks/`
- avoid rewriting the environment public API unless absolutely necessary

## Recommended Naming Going Forward

- Dataset: `expert_<task>_<tag>.npz`
- Dataset report: `expert_<task>_<tag>.json`
- Dataset analysis: `<task>_dataset_analysis_<tag>.json`
- Model: `bc_<task>_<tag>.pth`
- Eval report: `bc_<task>_<tag>_eval_<condition>.json`

Tag guidance:

- `vN` for promoted baselines
- `smoke` for disposable validation
- `g.._c..` for controller tuning comparisons
- `filter_<name>` for data-selection comparisons
- `policy_<name>` only when a new policy family is actually introduced

## Recommended Next Steps

1. Keep `pre_grasp` as the only maintained learning task until robustness is clearer.
2. If the next experiment is algorithm-free, prefer data-selection work over more tiny controller sweeps.
3. Refresh generated inventories after new promoted datasets or checkpoints are accepted.
4. If a new baseline surpasses `v2`, promote it by naming it `v3` and keep comparison artifacts alongside it for traceability.
