# Repository Slimming Manifest

Date: 2026-03-14

Purpose: define which assets remain first-class in the repository, which assets are archived for historical reference, and which temporary files can be safely deleted after smoke validation.

Update note (2026-03-20):

- This manifest predates the current `pre_grasp` baseline.
- Treat the newer `pre_grasp` assets listed below as current keep-list additions rather than contradictions.

## Keep List

### Scripts

Keep as active entrypoints:

- `scripts/collect_expert_data.py`
- `scripts/train_bc.py`
- `scripts/eval_bc.py`
- `scripts/demo_grasp.py`
- `scripts/demo_bc.py`
- `scripts/demo_catch_bc.py`
- `scripts/run_catch_baseline.py`

Keep as active support modules:

- `scripts/common/grasp_workflow.py`
- `scripts/data_tools/check_dataset.py`
- `scripts/data_tools/merge_datasets.py`
- `scripts/data_tools/organize_data.py`
- `scripts/data_tools/visualize_data.py`
- `scripts/diagnostics/check_success_rate.py`
- `scripts/diagnostics/test_catch_task.py`
- `scripts/README.md`

Keep already-archived legacy scripts under:

- `scripts/archive/`

### Data

Keep current pre_grasp baseline data:

- `data/expert_pre_grasp_mixed_v2.npz`

Keep current static baseline data:

- `data/expert_showcase_v5_50x400.npz`

Keep latest catch reference data:

- `data/expert_catch_v2_j002_f030_50x300.npz`

### Models

Keep runtime assets:

- `models/shadow_hand/`
- `models/arm26.xml`
- `models/tendon.xml`

Keep current recommended static model:

- `models/bc_showcase_v5_success400_phase_h128_80ep.pth`

Keep current recommended pre_grasp model:

- `models/bc_pre_grasp_v2.pth`

Keep one historical static baseline for comparison:

- `models/bc_showcase_v3_hold400_phase_h128_80ep.pth`

Keep latest catch reference model:

- `models/bc_catch_v2_j002_f030_40ep_h128.pth`

### Reports

Keep current pre_grasp reports:

- `reports/expert_pre_grasp_mixed_v2.json`
- `reports/pre_grasp_dataset_analysis_v2.json`
- `reports/bc_pre_grasp_v2_eval_j002.json`
- `reports/bc_pre_grasp_v2_eval_j004.json`

Keep current static reports:

- `reports/expert_showcase_v5_50x400.json`
- `reports/bc_showcase_v5_success400_demo_20_ramp160.json`
- `reports/sweep_v5_ramp160_s025.json`
- `reports/bc_showcase_v5_success400_demo_10_no_ramp.json`

Keep catch verification and reference reports:

- `reports/expert_catch_v2_j002_f030_50x300.json`
- `reports/bc_catch_v2_j002_f030_40ep_h128_eval_20x300.json`
- `reports/bc_eval_scene_20_v2.json`

Keep project-level documentation:

- `reports/project_stage_report_2026-03-14.md`
- `reports/dataset_inventory.md`
- `reports/slimming_manifest_2026-03-14.md`

## Archive List

### Data To Archive

- `data/expert_catch_smoke_v1_6x300.npz`
- `data/expert_catch_smoke_v2_6x300.npz`
- `data/expert_catch_v1_j002_f030_20x300.npz`
- `data/expert_mixed_v1_demo600_scene500.npz`
- `data/expert_scene_v1_50x500.npz`
- `data/expert_showcase_v1_50x600.npz`
- `data/expert_showcase_v3_50x600.npz`
- `data/expert_showcase_v4_50x400.npz`
- `data/expert_showcase_v4_smoke_10x400.npz`
- `data/expert_showcase_v5_smoke_10x400.npz`

### Models To Archive

- `models/bc_catch_smoke_v2_20ep.pth`
- `models/bc_catch_v1_j002_f030_30ep.pth`
- `models/bc_catch_v1_j002_f030_h128_30ep.pth`
- `models/bc_mixed_v1_success500_100ep.pth`
- `models/bc_scene_v1_success500_100ep.pth`
- `models/bc_showcase_v2_success500_100ep.pth`
- `models/bc_showcase_v3_hold400_phase50_h128_80ep.pth`
- `models/bc_showcase_v3_success500_phase_h128_100ep.pth`
- `models/bc_showcase_v4_success400_phase_h128_80ep.pth`

### Reports To Archive

- `reports/bc_catch_smoke_v2_eval_3x300.json`
- `reports/bc_catch_v1_j002_f030_eval_10x300.json`
- `reports/bc_catch_v1_j002_f030_eval_on_j000_10x300.json`
- `reports/bc_catch_v1_j002_f030_h128_eval_10x300.json`
- `reports/bc_catch_v1_j002_f030_h128_eval_on_j000_10x300.json`
- `reports/bc_showcase_v2_demo_20_500steps.json`
- `reports/bc_showcase_v3_demo_20_500steps.json`
- `reports/bc_showcase_v3_demo_20_500steps_no_ramp.json`
- `reports/bc_showcase_v3_hold400_demo_10_no_ramp.json`
- `reports/bc_showcase_v3_hold400_demo_20.json`
- `reports/bc_showcase_v3_hold400_phase50_demo_10_no_ramp.json`
- `reports/bc_showcase_v3_hold400_phase50_demo_20.json`
- `reports/bc_showcase_v4_success400_demo_10_no_ramp.json`
- `reports/bc_showcase_v4_success400_demo_20.json`
- `reports/bc_showcase_v4_success400_demo_20_ramp200.json`
- `reports/catch_demo_smoke_3x300.json`
- `reports/demo_catch_bc_headless_single.json`
- `reports/demo_eval_realistic_20.json`
- `reports/expert_catch_smoke_v1_6x300.json`
- `reports/expert_catch_smoke_v2_6x300.json`
- `reports/expert_catch_v1_j002_f030_20x300.json`
- `reports/expert_scene_v1_50x500.json`
- `reports/expert_showcase_v1_50x600.json`
- `reports/expert_showcase_v3_50x600.json`
- `reports/expert_showcase_v4_50x400.json`
- `reports/expert_showcase_v4_smoke_10x400.json`
- `reports/expert_showcase_v5_smoke_10x400.json`
- `reports/matrix_demoonly_on_scene_20x500.json`
- `reports/matrix_mixed_on_demo_20x500.json`
- `reports/matrix_mixed_on_scene_20x500.json`
- `reports/matrix_sceneonly_on_demo_20x500.json`
- `reports/matrix_sceneonly_on_scene_20x500.json`
- `reports/sweep_catch_fallspeed_m020_j002_8x300.json`
- `reports/sweep_catch_fallspeed_m030_j002_8x300.json`
- `reports/sweep_catch_fallspeed_m040_j002_8x300.json`
- `reports/sweep_catch_jitter_000_5x300.json`
- `reports/sweep_catch_jitter_001_5x300.json`
- `reports/sweep_catch_jitter_001_6x300.json`
- `reports/sweep_catch_jitter_002_5x300.json`
- `reports/sweep_catch_jitter_002_6x300.json`
- `reports/sweep_catch_jitter_003_6x300.json`
- `reports/sweep_catch_jitter_004_6x300.json`
- `reports/sweep_catch_jitter_005_6x300.json`
- `reports/sweep_catch_jitter_006_6x300.json`
- `reports/sweep_v4_ramp200_s025.json`
- `reports/sweep_v4_ramp220_s020.json`
- `reports/sweep_v4_ramp240_s020.json`
- `reports/sweep_v5_ramp200_s025.json`

## Delete List After Smoke Validation

Delete only obvious temporary files once the archived layout has been smoke-tested:

- all `__pycache__/` directories
- all `.pyc` files
- temporary smoke datasets, smoke checkpoints, and smoke reports created during validation

Deliberately do not delete historical archived experiment assets in this step.
