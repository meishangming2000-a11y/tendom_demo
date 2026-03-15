# Scripts Overview

This directory is split by role so the main workflow stays easy to scan.

## Root Entrypoints

- `collect_expert_data.py`
  Collect expert trajectories for behavior cloning.

- `train_bc.py`
  Train a behavior-cloning policy checkpoint.

- `eval_bc.py`
  Evaluate a BC checkpoint headlessly or with the viewer.

- `demo_grasp.py`
  Run the controller demo or batch-evaluate the expert controller.
  `--controller-profile expert_collection` exposes the shorter timing profile used during static expert-data collection.

- `demo_bc.py`
  One-command static-grasp BC showcase demo.

- `demo_catch_bc.py`
  One-command catch-task BC showcase demo.

- `run_catch_baseline.py`
  End-to-end catch baseline collection, training, and evaluation.

## Support Folders

- `common/`
  Shared helpers used by the root entrypoints, including object placement and controller timing.

- `data_tools/`
  Dataset inspection, merging, visualization, and inventory utilities.

- `diagnostics/`
  Quick checks for report summaries and catch-task validation.

- `archive/`
  Older experiments and debugging scripts kept for reference.

## Asset Layout

- Current recommended datasets stay in `data/`.
- Current recommended checkpoints stay in `models/`.
- Current recommended reports stay in `reports/`.
- Historical experiment assets are archived under `data/archive/`, `models/archive/`, and `reports/archive/`.
- The current keep/archive decision is tracked in `reports/slimming_manifest_2026-03-14.md`.

## Success Rules

Static-grasp validation uses:

`palm_and_thumb_plus_3_finger_groups_contact_for_50_steps`

Catch-task validation uses:

`palm_and_thumb_plus_3_finger_groups_contact_for_50_steps_and_object_not_on_floor`

## Recommended Static Workflow

### Expert Data Collection

```bash
python scripts/collect_expert_data.py --episodes 50 --max-steps 400 --placement-mode demo --placement-jitter 0.01 --early-stop-on-stable-grasp --stable-grasp-target-steps 80 --post-success-padding 20 --output data/expert_showcase_v5_50x400.npz --report reports/expert_showcase_v5_50x400.json
```

### BC Training

```bash
python scripts/train_bc.py --data data/expert_showcase_v5_50x400.npz --success-only --truncate-steps 400 --epochs 80 --batch-size 128 --hidden-dim 128 --add-phase-feature --output models/bc_showcase_v5_success400_phase_h128_80ep.pth
```

### BC Evaluation

```bash
python scripts/eval_bc.py --model models/bc_showcase_v5_success400_phase_h128_80ep.pth --episodes 20 --no-viewer --max-steps 400 --placement-mode demo --placement-jitter 0.01 --finger-ramp-steps 160 --finger-ramp-start-scale 0.25 --report reports/bc_showcase_v5_success400_demo_20_ramp160.json
```

### BC Demo

```bash
python scripts/demo_bc.py
```

## Verified Headless Demo Checks

```bash
python scripts/demo_grasp.py --no-viewer
python scripts/demo_bc.py --no-viewer --seed 0
```

## Utility Commands

```bash
python scripts/data_tools/check_dataset.py --data data/expert_showcase_v5_50x400.npz
python scripts/data_tools/merge_datasets.py --inputs data/expert_showcase_v5_50x400.npz data/archive/expert_scene_v1_50x500.npz --output data/expert_merged.npz
python scripts/data_tools/organize_data.py --output reports/dataset_inventory.md
python scripts/data_tools/visualize_data.py --data data/expert_showcase_v5_50x400.npz --all
python scripts/diagnostics/check_success_rate.py --data reports/bc_showcase_v5_success400_demo_20_ramp160.json
python scripts/diagnostics/test_catch_task.py --episodes 5
```
