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

## Vision Palm Trace Add-On

The vision palm-trace path is a bridge for bringing camera-derived hand/palm landmarks into the existing BC dataset format. It does not replace the canonical oracle-observation baseline yet.

Convert recorded 21-landmark frames, or collect with MediaPipe if `opencv-python` and `mediapipe` are installed:

```bash
python scripts/vision/collect_palm_trace.py --input-json data/raw_palm_frames.json --output data/vision_palm_trace_latest.npz --report reports/vision_palm_trace_latest.json
```

For newer MediaPipe Tasks builds, pass a downloaded `hand_landmarker.task` model:

```bash
python scripts/vision/collect_palm_trace.py --source path/to/hand_video.mp4 --hand-landmarker-model path/to/hand_landmarker.task --output data/vision_palm_trace_latest.npz --report reports/vision_palm_trace_latest.json
```

For batch videos, use `--max-source-frames` to cap how many raw video frames
are scanned, and `--max-frames` to cap how many detected hand frames are kept.

Attach the palm features to an existing expert dataset:

```bash
python scripts/vision/attach_palm_trace_to_dataset.py --dataset data/expert_pre_grasp_mixed_v2.npz --palm-trace data/vision_palm_trace_latest.npz --output data/expert_pre_grasp_mixed_v2_vision.npz
```

Train on the fused observation field:

```bash
python scripts/train_bc.py --task pre_grasp --data data/expert_pre_grasp_mixed_v2_vision.npz --observation-field fused_observations --epochs 20 --output models/bc_pre_grasp_v2_vision.pth
```

Retarget the same 21-landmark trace into the current Shadow Hand action layout
for a diagnostic MuJoCo replay:

```bash
python scripts/vision/retarget_palm_trace_to_shadow.py --palm-trace data/vision_palm_trace_latest.npz --output data/vision_shadow_retarget_latest.npz --rollout-output data/vision_shadow_retarget_replay_latest.npz --report reports/vision_shadow_retarget_latest.json
```

Use `--start-frame`, `--end-frame`, and `--stride` to keep only a coherent
gesture segment before replaying it as one diagnostic rollout.

Visualize the retargeted trace, action curves, optional rollout metrics, and
fixed-camera Shadow keyframes:

```bash
python scripts/vision/visualize_shadow_retarget.py --retarget data/vision_shadow_retarget_latest.npz --rollout data/vision_shadow_retarget_replay_latest.npz --output-dir artifacts/vision_shadow_retarget_latest --render-mujoco
```

Run the organized real-hand video through extraction, Shadow retarget, MuJoCo
replay, and a full-vs-segment visual comparison in one command:

```bash
python scripts/vision/run_real_hand_video_compare.py --force --open
```

By default this uses
`../artifacts/vision_real_hand/hand_example_20260429/source/hand-example_video.mp4`
and writes the comparison sheet to
`../artifacts/vision_real_hand/hand_example_20260429/one_command_compare/comparison_overview.png`.
It also writes synchronized MP4 comparisons under
`../artifacts/vision_real_hand/hand_example_20260429/one_command_compare/videos/`.
Each MP4 shows the source video frame, the intermediate 21-point hand graph,
and the Shadow MuJoCo replay side by side.
Use `--video path/to/hand_video.mp4` for a different recording, and
`--segment-start`, `--segment-end`, and `--segment-stride` to choose the
coherent gesture window shown beside the full-video replay.
The one-command runner defaults to `--retarget-time-scale 3`, which slows fast
real-hand motion by inserting interpolated MuJoCo action steps between visual
frames. Increase it when the Shadow fingers visibly lag behind the gesture.
Use `--video-frame-stride 1` for smoother MP4 output, or keep the default
stride of 2 for faster diagnostic videos.

Build a trainable dataset from the diagnostic Shadow retarget output:

```bash
python scripts/vision/build_shadow_retarget_bc_dataset.py --retarget ../artifacts/vision_real_hand/hand_example_20260429/one_command_compare/data/segment_shadow_retarget.npz --rollout ../artifacts/vision_real_hand/hand_example_20260429/one_command_compare/data/segment_shadow_retarget_replay.npz --output ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_bc_dataset.npz --report ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_bc_dataset.json
```

Train a diagnostic visual-to-Shadow imitation model on the 76D palm feature
field:

```bash
python scripts/train_bc.py --data ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_bc_dataset.npz --output ../artifacts/vision_real_hand/hand_example_20260429/training/bc_vision_shadow_segment_phase_h256.pth --epochs 200 --batch-size 128 --hidden-dim 256 --add-phase-feature
```

Evaluate that model on the same retarget trace by predicting Shadow actions
from palm features and replaying the prediction in MuJoCo:

```bash
python scripts/vision/eval_shadow_retarget_bc.py --model ../artifacts/vision_real_hand/hand_example_20260429/training/bc_vision_shadow_segment_phase_h256.pth --retarget ../artifacts/vision_real_hand/hand_example_20260429/one_command_compare/data/segment_shadow_retarget.npz --output ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_phase_model_prediction.npz --rollout-output ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_phase_model_prediction_replay.npz --report ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_phase_model_prediction_report.json --visualization-dir ../artifacts/vision_real_hand/hand_example_20260429/training/segment_shadow_retarget_phase_model_prediction_visualization --render-mujoco
```

Experimental sequence model branch:

```bash
python scripts/vision/train_sequence_shadow_bc.py --data ../artifacts/vision_web_hand/commons_hand_20260430/training/commons_shadow_retarget_bc_dataset.npz --output ../artifacts/vision_web_hand/commons_hand_20260430/sequence_experiment/seq_tcn_gru_h32_c8_vphase_h256.pth --report ../artifacts/vision_web_hand/commons_hand_20260430/sequence_experiment/seq_tcn_gru_h32_c8_vphase_h256_report.json --history 32 --chunk 8 --sample-stride 2 --add-velocity --add-phase-feature --epochs 80 --batch-size 256 --hidden-dim 256 --eval-retarget ../artifacts/vision_real_hand/hand_example_20260429/one_command_compare/data/segment_shadow_retarget.npz --prediction-output ../artifacts/vision_web_hand/commons_hand_20260430/sequence_experiment/user_segment_seq_prediction.npz --rollout-output ../artifacts/vision_web_hand/commons_hand_20260430/sequence_experiment/user_segment_seq_prediction_replay.npz --visualization-dir ../artifacts/vision_web_hand/commons_hand_20260430/sequence_experiment/user_segment_seq_prediction_visualization --render-mujoco
```

This trains a small TCN + GRU model on history windows and predicts an action
chunk. It is diagnostic-only and should be judged by episode-level held-out
metrics plus MuJoCo replay, not by training loss alone.

Train from a local folder of hand open/close videos:

```bash
python scripts/vision/run_video_folder_training.py --video-dir ../videos --output-root ../artifacts/vision_real_hand/video_folder_20260504
```

This wrapper runs MediaPipe extraction, Shadow retargeting, dataset building,
single-frame BC training, and sequence-model training. Raw videos and generated
artifacts remain outside Git by default.

Build the device-independent open/close manifest and intermediate-feature
dataset from the processed video folder:

```bash
python scripts/vision/build_open_close_manifest.py --video-dir ../videos --trace-dir ../artifacts/vision_real_hand/video_folder_20260504/data --retarget-dir ../artifacts/vision_real_hand/video_folder_20260504/retarget --reports-dir ../artifacts/vision_real_hand/video_folder_20260504/reports --output ../artifacts/vision_real_hand/open_close_v1/open_close_manifest.json
python scripts/vision/build_open_close_bc_dataset.py --manifest ../artifacts/vision_real_hand/open_close_v1/open_close_manifest.json --output ../artifacts/vision_real_hand/open_close_v1/training/open_close_shadow_retarget_bc_dataset.npz --report ../artifacts/vision_real_hand/open_close_v1/training/open_close_shadow_retarget_bc_dataset.json
python scripts/train_bc.py --data ../artifacts/vision_real_hand/open_close_v1/training/open_close_shadow_retarget_bc_dataset.npz --output ../artifacts/vision_real_hand/open_close_v1/training/bc_open_close_shadow_retarget_phase_h128.pth --epochs 120 --batch-size 256 --hidden-dim 128 --add-phase-feature
```

This path uses `vision/hand_open_close.py` to convert 21 landmarks into a
35D semantic vector with per-finger curl, spread, palm normal, and global
open/close fields. It is the preferred bridge for future custom-hand mapping,
because it separates visual hand understanding from the temporary Shadow action
layout.

Current boundary: this is a data and training workflow integration only. Evaluation still needs a runtime observation provider before a fused-vision policy can be treated as a deployable baseline.
The Shadow retarget path is also diagnostic-only: it maps landmark geometry to
the temporary 24D Shadow normalized action interface, without camera
calibration, IK, object alignment, or custom tendon-hand semantics.

## Stage-1 Arm + Shadow Mount Demo

The arm-plus-Shadow combo has a structural inspection demo for checking mount direction, scale, and actuator ordering while the custom tendon-hand model is still being built:

```bash
python scripts/demo_arm_stage1_shadow.py
```

Headless smoke check:

```bash
python scripts/demo_arm_stage1_shadow.py --no-viewer --steps 200
```

This demo drives gentle arm motion and a temporary Shadow hand open-close cycle. It is not a promoted training environment.
By default, the demo hides the temporary Shadow forearm shell, aligns `rh_wrist` to `ee_tool_frame_site` with a small forward offset, and re-projects that visual mount each step. This avoids reading the Shadow forearm shell as a real mechanical adapter while the custom tendon-hand model is still missing.

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
