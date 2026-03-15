# MuJoCo Tendon Demo Core

Shadow Hand grasping project built around a full MuJoCo behavior-cloning pipeline:

`expert controller -> dataset collection -> BC training -> BC evaluation -> showcase demo`

The current repository is strongest as a static-grasp showcase. It includes a runnable expert demo, a runnable learned-policy demo, the scripts used to collect and train the baseline, and reports for the current recommended setup.

## Highlights

- End-to-end static pipeline is runnable from expert control to learned-policy demo.
- Static success is evaluated with a stricter grasp rule instead of palm-only support.
- Catch-task object placement now preserves falling velocity after `reset()`.
- The script tree is organized around entrypoints, shared helpers, data tools, and diagnostics.
- Current static BC baseline uses cleaned expert data, a phase feature, and a finger-action ramp during inference.

## Current Result Snapshot

Static expert dataset:

- Dataset: `data/expert_showcase_v5_50x400.npz`
- Stable-grasp success: `47/50` (`94.0%`)
- Terminal success: `25/50` (`50.0%`)

Static BC evaluation:

- Model: `models/bc_showcase_v5_success400_phase_h128_80ep.pth`
- Report: `reports/bc_showcase_v5_success400_demo_20_ramp160.json`
- Success rate: `10/20` (`50.0%`)

Important limitation:

- The static BC policy is demo-ready, but still not a robust benchmark-level policy.
- The catch-task environment bug is fixed, but the catch learning result still needs a fresh retrain.

## Success Rules

Static grasp:

`palm_and_thumb_plus_3_finger_groups_contact_for_50_steps`

Catch and hold:

`palm_and_thumb_plus_3_finger_groups_contact_for_50_steps_and_object_not_on_floor`

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

If your PyTorch install needs a CUDA-specific wheel, install `torch` from the official PyTorch channel first, then run the command above.

Verified headless demo commands:

```bash
python scripts/demo_grasp.py --no-viewer
python scripts/demo_bc.py --no-viewer --seed 0
```

The second command was verified locally with the current default static model and succeeded under the strict rule. The first command was verified with the current expert-controller defaults and reached a successful hold-phase grasp.

Optional note:

- `--controller-profile expert_collection` exposes the shorter timing profile used during static expert-data collection.
- It is useful for inspecting controller timing in shorter episodes, but the verified strict-rule expert demo command remains `python scripts/demo_grasp.py --no-viewer`.

## Main Entrypoints

- `python scripts/demo_grasp.py`
  Run the expert-controller grasp demo.
- `python scripts/demo_bc.py`
  Run the learned-policy showcase demo.
- `python scripts/collect_expert_data.py ...`
  Collect expert trajectories for BC.
- `python scripts/train_bc.py ...`
  Train a behavior-cloning checkpoint.
- `python scripts/eval_bc.py ...`
  Evaluate a BC checkpoint.

See `scripts/README.md` for the per-folder script overview.

## Recommended Static Workflow

Collect expert data:

```bash
python scripts/collect_expert_data.py --episodes 50 --max-steps 400 --placement-mode demo --placement-jitter 0.01 --early-stop-on-stable-grasp --stable-grasp-target-steps 80 --post-success-padding 20 --output data/expert_showcase_v5_50x400.npz --report reports/expert_showcase_v5_50x400.json
```

Train BC:

```bash
python scripts/train_bc.py --data data/expert_showcase_v5_50x400.npz --success-only --truncate-steps 400 --epochs 80 --batch-size 128 --hidden-dim 128 --add-phase-feature --output models/bc_showcase_v5_success400_phase_h128_80ep.pth
```

Evaluate BC:

```bash
python scripts/eval_bc.py --model models/bc_showcase_v5_success400_phase_h128_80ep.pth --episodes 20 --no-viewer --max-steps 400 --placement-mode demo --placement-jitter 0.01 --finger-ramp-steps 160 --finger-ramp-start-scale 0.25 --report reports/bc_showcase_v5_success400_demo_20_ramp160.json
```

## Repository Layout

- `src/`
  Environment and controller implementations.
- `scripts/`
  Main runnable entrypoints plus helper folders.
- `data/`
  Current recommended datasets plus archived experiments.
- `models/`
  Runtime assets and current checkpoints.
- `reports/`
  Evaluation reports, project summaries, and inventories.

The current keep/archive decision is documented in `reports/slimming_manifest_2026-03-14.md`.

## Diagnostics

```bash
python scripts/data_tools/check_dataset.py --data data/expert_showcase_v5_50x400.npz
python scripts/data_tools/organize_data.py --output reports/dataset_inventory.md
python scripts/diagnostics/check_success_rate.py --data reports/bc_showcase_v5_success400_demo_20_ramp160.json
python scripts/diagnostics/test_catch_task.py --episodes 5
```

## Project Stage

The repository is currently at a pipeline-validation and showcase stage:

- Static expert and BC demos are presentable.
- Evaluation is stricter and more physically meaningful than earlier revisions.
- Static robustness and scene generalization are still limited.
- Catch learning still needs refreshed training under the corrected falling-object physics.
