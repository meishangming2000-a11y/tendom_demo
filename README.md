# Simulations

`simulations/` is the active runtime workspace for the tendon-driven hand project. If you are working on the current software mainline, treat this directory as the local project root.

## Canonical Mainline

The current official mainline is:

`pre_grasp expert -> dataset -> BC train -> eval -> report`

Current promoted `pre_grasp` baseline assets:

- Dataset: `data/expert_pre_grasp_mixed_v2.npz`
- Collection report: `reports/expert_pre_grasp_mixed_v2.json`
- Dataset analysis: `reports/pre_grasp_dataset_analysis_v2.json`
- Checkpoint: `models/bc_pre_grasp_v2.pth`
- Eval reports:
  - `reports/bc_pre_grasp_v2_eval_j002.json`
  - `reports/bc_pre_grasp_v2_eval_j004.json`

Related but non-promoted assets that still exist:

- earlier `pre_grasp` snapshots such as `expert_pre_grasp*.npz` and `bc_pre_grasp*.pth` without the promoted `v2` tag
- controller-tuning comparison assets tagged `g11_c11`
- smoke-check artifacts tagged `smoke`
- older static-grasp showcase assets tagged `showcase`
- older catch-task assets tagged `catch`

Treat those as `reference`, `comparison`, or `historical` assets unless a newer document explicitly promotes them.

## Recommended Directory Responsibilities

- `src/environments/`
  Runtime environment and MuJoCo integration. `shadow_grasp_env.py` is the environment entry used by current scripts.
- `tasks/`
  Structured task definitions plus task-side check and transition logic. `pre_grasp.py` is maintained; `stable_grasp.py` now contains a first software skeleton; `lift_and_hold.py` is still a placeholder.
- `src/adapters/`
  Hand-agnostic adapter interface and backend-specific implementations. Current runtime only ships a temporary `shadow backend`.
- `src/controllers/`
  Controller implementations and controller-side support logic.
- `scripts/`
  Runnable entrypoints for data collection, training, evaluation, demos, diagnostics, and support utilities.
- `scripts/common/`
  Shared workflow helpers used by collection and evaluation paths.
- `data/`
  Datasets and dataset-side assets.
- `models/`
  Trained checkpoints and simulation XML assets.
- `reports/`
  Collection reports, dataset analyses, evaluation reports, and handoff notes.

## Task Status

- `pre_grasp`
  Closed loop is implemented and is the only maintained training/evaluation baseline.
- `stable_grasp`
  A first software skeleton now exists: task spec/config, an explicit evaluation contract, official-vs-debug metric separation, a `pre_grasp -> stable_grasp` transition contract, and a temporary Shadow backend implementation. It is still not a maintained training baseline.
- `lift_and_hold`
  Task skeleton exists, but it is still a placeholder and is not a maintained baseline.

Do not describe `stable_grasp` or `lift_and_hold` as already completed baselines.

## Stable Grasp v1 Skeleton

The current `stable_grasp` work should be read as software structure, not as a new promoted benchmark path.

What is now in place:

- `tasks/checks.py`
  Reusable task success/failure checker interface with `official_metrics` and `debug_metrics`.
- `tasks/transitions.py`
  First independent transition contract for `pre_grasp -> stable_grasp`, plus reserved placeholders for later transitions.
- `tasks/stable_grasp.py`
  `stable_grasp` task spec/config, evaluation contract, entry snapshot contract, and the first checker-backed task implementation.
- `tasks/episode_evaluation.py`
  Minimal episode-level schema, transition-blocked episode summary, and official batch-report helper for labeling/eval/report output.
- `src/adapters/base_hand_adapter.py`
  Hand-agnostic adapter contract for task logic, including task-level vs backend-derived field semantics.
- `src/adapters/shadow_hand_adapter.py`
  Temporary `shadow backend` implementation for contact, closure, and joint-state access.
- `scripts/diagnostics/smoke_task_contracts.py`
  Minimal protocol smoke path for `pre_grasp info -> transition evaluator -> stable_grasp evaluate_state`.
- `scripts/diagnostics/structured_rollout_eval.py`
  Diagnostic-only structured rollout path for `pre_grasp transition -> stable_grasp entry snapshot -> stable_grasp episode summary -> official report`.
- `scripts/diagnostics/batch_eval_stable_grasp.py`
  Minimal batch evaluation harness for `stable_grasp`, with `environment_only` and `diagnostic_seeded` modes.
- `scripts/common/grasp_workflow.py`
  Temporary scripted action helpers, including the current minimal `stable_grasp` scripted controller.
- `tasks/behavior_audit.py`
  Analysis-only helpers for scripted-controller behavior audit, failure attribution, and temporary collection gating.

Current limitation:

- no promoted `stable_grasp` dataset/checkpoint/eval baseline yet
- no real-hand backend
- no finalized `stable_grasp -> lift_and_hold` transition
- Shadow-specific thresholds and closure/contact approximations are temporary
- the current stable_grasp execution path is a temporary scripted backend, not a learned policy

### Stable Grasp Official Contract

Current official `stable_grasp` contract is intentionally small:

- official success
  - retained workspace
  - abstract contact support ready
  - abstract closure ready
  - hold requirement met
- official failure
  - object on floor
  - retention failure beyond configured limits
- official metrics
  - hold steps
  - support-region summary
  - closure metric
  - palm/object relative relation
  - object displacement/drop from task entry

Current `shadow backend` detail is still debug-only:

- contact body names
- palm/thumb-specific contact flags
- Shadow closure group breakdowns
- joint-name mappings and backend-specific approximations

### Episode-Level Structured Evaluation

`stable_grasp` now also has a minimal episode-level schema intended for later dataset labeling and evaluation:

- `task_name`
- `episode_status`
- `terminal_reason`
- `success`
- `failure`
- `step_count`
- `transition_info`
- `official_metrics`
- `backend_info`
- `entry_snapshot`

Default official report output excludes `debug_metrics` unless explicitly requested.

Batch report aggregation now also includes:

- total episode counts by status
- `terminal_reason_counts`
- aggregated official metrics only
- per-episode summaries

The batch harness now emits two separate artifacts:

- `official_report`
  official task metrics and terminal fields only
- `behavior_audit`
  analysis-only summary for scripted-controller behavior quality, failure modes, and temporary data-source readiness

### Entry Snapshot Contract

`stable_grasp` reference-state metrics now use an explicit entry snapshot:

- canonical owner
  - rollout evaluator / pipeline handoff layer
- preferred entry time
  - capture at `pre_grasp -> stable_grasp` transition ready, before the first `stable_grasp` step
- fallback entry time
  - first `stable_grasp` evaluation step, created by the checker and marked with `fallback_created=true`

This snapshot anchors:

- `object_displacement_from_entry`
- `object_vertical_drop_from_entry`
- `relative_palm_object_distance_at_entry`

Report note:

- `entry_source`
  distinguishes canonical transition-time creation from checker fallback creation

## Canonical Script Entry

Use these scripts for the maintained `pre_grasp` loop:

- `python scripts/collect_expert_data.py --task pre_grasp ...`
- `python scripts/analyze_pre_grasp_dataset.py --data ...`
- `python scripts/train_bc.py --task pre_grasp ...`
- `python scripts/eval_bc.py --model ...`

This is the recommended full command sequence:

```bash
python scripts/collect_expert_data.py --task pre_grasp --episodes 40 --max-steps 200 --placement-mode demo --placement-jitters 0.02,0.04 --pre-grasp-gain-scale 1.0 --pre-grasp-clip-scale 1.0 --pre-grasp-start-bias 0.01,0.0,-0.005 --pre-grasp-target-offset 0.008,0.0165,0.0 --output data/expert_pre_grasp_mixed_v2.npz --report reports/expert_pre_grasp_mixed_v2.json
python scripts/analyze_pre_grasp_dataset.py --data data/expert_pre_grasp_mixed_v2.npz --report reports/pre_grasp_dataset_analysis_v2.json
python scripts/train_bc.py --task pre_grasp --data data/expert_pre_grasp_mixed_v2.npz --success-only --epochs 20 --batch-size 128 --hidden-dim 128 --output models/bc_pre_grasp_v2.pth
python scripts/eval_bc.py --model models/bc_pre_grasp_v2.pth --episodes 20 --no-viewer --placement-mode demo --placement-jitter 0.02 --report reports/bc_pre_grasp_v2_eval_j002.json
python scripts/eval_bc.py --model models/bc_pre_grasp_v2.pth --episodes 20 --no-viewer --placement-mode demo --placement-jitter 0.04 --report reports/bc_pre_grasp_v2_eval_j004.json
```

## Canonical Path vs Legacy Path

Canonical path:

- `pre_grasp`
- task-qualified asset names such as `expert_pre_grasp_*` and `bc_pre_grasp_*`
- `v2` baseline assets unless a newer promoted version is documented
- structured task interfaces under `tasks/` and `src/adapters/`

Legacy, historical, or reference path:

- `demo_grasp.py`
- `demo_bc.py`
- `demo_catch_bc.py`
- `run_catch_baseline.py`
- `analyze_actions.py`
- `check_dataset_quality.py`
- `scripts/archive/`
- `project_state.md`
- `claude_contest.md`

These files are preserved because they still contain useful experiments, demos, or historical context. They are not the recommended starting point for new work on the official mainline.

## Minimal Protocol Smoke Path

To validate the current task protocol without training or viewer rollout:

```bash
python scripts/diagnostics/smoke_task_contracts.py
```

This prints a machine-readable sample covering:

- which `pre_grasp` fields feed the transition contract
- whether the transition evaluator is ready or blocked, and why
- what `stable_grasp` returns as official metrics vs debug metrics

This smoke path validates the protocol layer only. It does not imply a maintained `stable_grasp` policy baseline.

## Minimal Structured Rollout Path

To validate the current episode-level evaluation path without training:

```bash
python scripts/diagnostics/structured_rollout_eval.py
```

Optional compatibility switch:

```bash
python scripts/diagnostics/structured_rollout_eval.py --stable-grasp-phase-mode zero_action
```

This path emits a machine-readable payload covering:

- pre_grasp transition input
- transition decision
- stable_grasp entry snapshot
- stable_grasp episode summary
- official report payload

The default report keeps only official metrics plus terminal fields. Debug metrics remain opt-in.
This is still a diagnostic rollout path and may use diagnostic-only state preparation to create a minimal transition-ready entry. It should not be read as a trained policy evaluation baseline or official batch-eval entry.

## Minimal Batch Evaluation Harness

For the current batch-level `stable_grasp` evaluation path, use:

```bash
python scripts/diagnostics/batch_eval_stable_grasp.py --eval-mode environment_only --stable-grasp-phase-mode scripted_controller
```

This environment-driven harness can produce:

- per-episode `EpisodeEvaluationResult` payloads
- official per-episode report payloads
- aggregated batch report output with official metrics only
- a separate behavior-audit artifact for controller quality diagnosis
- temporary stable_grasp scripted execution after transition handoff

Optional output paths:

- `--report`
  save the combined official-report plus behavior-audit artifact
- `--official-report`
  save the official report only
- `--audit-report`
  save the behavior-audit artifact only

Current output includes:

- config / eval mode / backend metadata
- success / failure / timeout / incomplete counts
- `terminal_reason_counts`
- aggregated official metrics such as hold steps, contact summary, closure summary, displacement/drop, and palm/object relation
- per-episode summaries
- audit-side counts for transition reached vs blocked, stable_grasp entered, failure modes, readiness candidates, and a short controller diagnosis

Diagnostic seeded variant:

```bash
python scripts/diagnostics/batch_eval_stable_grasp.py --eval-mode diagnostic_seeded --stable-grasp-phase-mode scripted_controller
```

This seeded mode is preserved for protocol verification only. Do not treat it as official task-performance evaluation.

Compatibility mode:

```bash
python scripts/diagnostics/batch_eval_stable_grasp.py --eval-mode environment_only --stable-grasp-phase-mode zero_action
```

`zero_action` is kept only for compatibility and comparison. The recommended current phase mode is `scripted_controller`.

Temporary collection note:

- the audit layer may mark some episodes as provisional temporary data-source candidates
- this collection gate is intentionally conservative
- it is not the official stable_grasp success contract and not a benchmark threshold
- it applies only to `stable_grasp_phase_mode=scripted_controller`; `zero_action` remains comparison-only

## Diagnostic Path vs Environment-Driven Path

- `structured_rollout_eval.py`
  diagnostic-only, contract-chain verification, may use transition-seeded state preparation
- `batch_eval_stable_grasp.py --eval-mode diagnostic_seeded`
  batch-form diagnostic verification, still seeded, not official eval
- `batch_eval_stable_grasp.py --eval-mode environment_only`
  minimal environment-driven batch harness using reset-time placement, pre_grasp expert stepping, and temporary stable_grasp scripted execution; this is the current official batch-eval path shape

Even in `environment_only` mode, current results are still software-structuring outputs, not a promoted `stable_grasp` training benchmark.

## Stable Grasp Scripted Controller

Current location:

- `scripts/common/grasp_workflow.py`

Current role:

- temporary Shadow backend scripted controller
- minimal joint-level close-and-stabilize execution helper
- replacement for the old zero-action continuation in stable_grasp rollout validation
- subject to behavior audit before any episode is treated as a temporary collection candidate

Current final status:

- one final minimal refinement attempt was made against `insufficient_sustained_contact`
- the controller remains executable and evaluable
- it still is not data-source-ready under the current temporary collection gate
- no further scripted-controller tuning is planned in the current system-structuring phase

It is not:

- a learned policy
- a benchmark policy
- a real-hand backend
- a promoted stable_grasp expert baseline

## Compatibility Naming Note

Some scripts still keep legacy generic defaults such as:

- `data/expert_data.npz`
- `models/bc_model.pth`

These names remain for compatibility. They are not the recommended canonical naming scheme for new work. Prefer explicit task-qualified names with a version or comparison tag.

## Latest Arm-Hand Stage2 Smoke

The current experimental lift/hold candidate is the v0.4 obs+phase BC checkpoint:

- checkpoint: `models/arm_hand_stage1_export/checkpoints/bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- accepted reset long-hold eval: `87 / 87` on v0.2 recovery resets and `75 / 75` on v0.1 resets
- unseen midpoint holdout: original smoothing `0.5` reached `11 / 12`; selected smoothing `0.2` reached `12 / 12`
- holdout report: `models/arm_hand_stage1_export/docs/arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020_report.md`
- holdout demo video: `models/arm_hand_stage1_export/docs/visual_checks_arm_hand_stage1_v2_bc_v0_4_holdout/holdout_offset_0175_0075_smooth020_demo.mp4`
- pick-place extension: same-platform v3 scripted pure-physics demo reaches `PASS`; it picks the ball, transports it to a nearby target pad, releases it, retreats, and keeps it inside a `0.035 m` target radius
- pick-place report: `models/arm_hand_stage1_export/docs/arm_hand_stage1_v3_pick_place_scripted_demo_report.md`
- pick-place demo video: `models/arm_hand_stage1_export/docs/visual_checks_arm_hand_stage1_v3_pick_place/pick_place_same_platform_scripted_demo.mp4`

This is still experimental smoke validation on collision proxy v2, not a promoted maintained baseline.

## Development Notes

When adding a new task or experiment here:

1. Define observation, action, success criteria, and failure criteria explicitly.
2. Name datasets, checkpoints, and reports with task-qualified filenames.
3. Record which dataset, checkpoint, and eval setting a report belongs to.
4. Save new outputs under new filenames instead of overwriting the promoted baseline.
5. Prefer interface changes that keep future real-to-sim alignment possible.

## Additional Reading

- `../docs/project_overview.md`
- `../docs/task_definition_v1.md`
- `../docs/current_status.md`
- `scripts/README.md`
- `reports/README.md`
