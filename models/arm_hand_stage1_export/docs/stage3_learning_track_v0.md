# Stage3 Learning Track V0

Generated: 2026-06-05

## Purpose

Hardware is not available yet, so the useful next research lane is simulation
learning:

```text
scripted sensor-aware expert
-> sensor-fusion dataset
-> replay QA
-> BC or residual baseline
-> noisy/randomized evaluation
```

This stays MuJoCo-only. It uses virtual-camera vision and contact-derived
tactile/slip signals.

## Live Progress Mind Map

Stage3 progress can be reviewed through a live local mind-map viewer:

```text
models/arm_hand_stage1_export/stage3_progress_mindmap_viewer.py
models/arm_hand_stage1_export/docs/stage3_progress_mindmap.json
```

Run:

```powershell
python .\simulations\models\arm_hand_stage1_export\stage3_progress_mindmap_viewer.py
```

The browser view refreshes from `stage3_progress_mindmap.json` every few
seconds. Update that JSON after each major Stage3 repair or promotion so future
alignment checks can start from the map instead of re-reading every closeout.

## Current Dataset

Dataset:

```text
models/arm_hand_stage1_export/data/stage3_sensor_fusion_expert_dataset_v0.npz
```

Collection script:

```text
models/arm_hand_stage1_export/collect_stage3_sensor_fusion_expert_dataset_v0.py
```

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\collect_stage3_sensor_fusion_expert_dataset_v0.py --episodes 10
```

Result:

- episodes: `10`
- total rows: `31000`
- obs shape: `[31000, 130]`
- action shape: `[31000, 26]`
- success count: `10 / 10`
- terminal reasons: `{'success_gentle_grasp_hold': 10}`
- risk flags: `early_contact_in_approach` and `transient_nonhold_slip` in all
  10 episodes

Report:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_expert_dataset_v0_report.md
```

Metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_sensor_fusion_expert_dataset_v0.json
```

## Replay QA

Replay script:

```text
models/arm_hand_stage1_export/replay_stage3_sensor_fusion_dataset.py
```

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\replay_stage3_sensor_fusion_dataset.py
```

Result:

- status: `PASS`
- episodes checked: `10`
- success replay count: `10 / 10`
- max obs error: `0.000e+00`
- max next obs error: `0.000e+00`
- max object position error: `0.000e+00`
- training ready: `True`

Report:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_expert_dataset_v0_replay_report.md
```

Metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_sensor_fusion_expert_dataset_v0_replay.json
```

## Dataset Fields

Main training fields:

- `obs`: Stage3 sensor abstraction vector
- `actions`: behavior actions actually applied in MuJoCo
- `expert_actions`: clean expert action labels for BC
- `next_obs`
- `rewards`
- `dones`
- `successes`
- `failures`

Sensor/logging fields:

- `vision_pose_estimates`
- `vision_scalars`
- `tactile_scalars`
- `tactile_region_masks`

Evaluation-only fields:

- `gt_object_positions`
- `gt_object_lift_heights`
- `initial_object_positions`

Policy boundary:

```text
Use obs for learning by default.
Use ground-truth fields only for labels, QA, metrics, and debugging.
```

## Next Model Step

The first model baseline has now been run. The useful model is still not
end-to-end image-to-action. The tested first step was:

```text
phase + sensor abstraction obs -> expert action
```

Implemented first baseline:

```text
models/arm_hand_stage1_export/train_stage3_sensor_fusion_bc_baseline.py
models/arm_hand_stage1_export/eval_stage3_sensor_fusion_bc_baseline.py
```

Primary result:

- offline training worked: val action RMSE raw `0.01273346`
- full-action BC failed closed-loop: `0 / 10`
- overfit full-action BC also failed closed-loop: `0 / 10`
- hybrid expert-arm + BC-hand passed closed-loop: `10 / 10`

Result doc:

```text
models/arm_hand_stage1_export/docs/stage3_sensor_fusion_bc_baseline_v0_model_result.md
```

Interpretation:

```text
Full-action BC is too fragile for arm/wrist approach.
Hand/finger BC is viable when arm/wrist approach stays scripted.
```

Recommended second baseline:

```text
scripted vision-guided arm/wrist approach
+ learned hand/finger closure/hold
+ learned residual correction during tactile/slip phases
```

The first half of this second baseline is now implemented as Stage3.6:

```text
models/arm_hand_stage1_export/train_stage3_phase_hand_policy_v0.py
models/arm_hand_stage1_export/eval_stage3_phase_hand_policy_v0.py
```

Stage3.6 result:

- hand-only policy target dim: `20`
- learned phases: `gentle_close_fingers`, `gentle_close_thumb`,
  `contact_settle`, `slow_lift`, `hold`
- closed-loop fixed trial result: `10 / 10`
- mean final lift: `0.103050 m`
- mean hold stable fraction: `1.000`
- max hold slip: `0.262`
- max crush risk: `0.113`
- max penetration: `0.002260 m`

Result doc:

```text
models/arm_hand_stage1_export/docs/stage3_phase_hand_policy_v0_closeout.md
```

The residual policy remains the next useful step. It is safer for this project
because the expert already works and the model can focus on reducing the two
known risks instead of relearning the whole grasp.

## Stage3.7A Tactile Teacher Probe

Stage3.7A tested hand/finger residuals and tactile phase timing.

Script:

```text
models/arm_hand_stage1_export/eval_stage3_tactile_residual_teacher_v0.py
```

Closeout:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_residual_teacher_v0_closeout.md
```

Result:

- hand close residuals did not help; stronger close made transient slip worse
- mild relax-on-slip helped only slightly
- slow lift improved hold slip but not transient max slip
- longer tactile contact-settle timing was the best direction
- recommended phase-timing teacher kept success `10 / 10`
- mean max transient slip improved from `0.816` to `0.659`
- max transient slip improved from `1.000` to `0.941`
- crush and penetration stayed inside the Stage3.6 envelope
- randomized 30-trial probe also passed `30 / 30`
- randomized mean max slip improved from `0.882` to `0.707`
- randomized max hold slip increased from `0.263` to `0.330`, still below the
  `0.35` threshold

Decision:

```text
Do not train a learned hand residual from the current hand-residual teacher.
Continue with tactile-gated phase timing / lift permission.
```

## Stage3.7B Tactile Phase Gate

Stage3.7B formalized the useful Stage3.7A direction as a clean evaluation
script without hand residuals.

Script:

```text
models/arm_hand_stage1_export/eval_stage3_tactile_phase_gate_v0.py
```

Closeout:

```text
models/arm_hand_stage1_export/docs/stage3_tactile_phase_gate_v0_closeout.md
```

Selected default:

- approach steps: `320`
- contact-settle gate: `2000` min / `2000` max steps
- stable window: `300` steps
- gate slip threshold: `0.18`
- gate crush threshold: `0.35`
- gate penetration threshold: `0.004 m`

Fixed 10-trial result:

- success: `10 / 10`
- gate release reason: `stable_window_met` in all `10` episodes
- mean max transient slip improved to `0.598`
- max transient slip remained `0.941`
- max hold slip: `0.263`
- max crush risk: `0.111`
- max penetration: `0.002223 m`

Randomized 30-trial result with `random_offset_std = 0.005 m`:

- success: `30 / 30`
- gate release reason: `stable_window_met` in all `30` episodes
- mean max transient slip improved to `0.625`
- max transient slip remained `1.000`
- max hold slip: `0.318`
- max crush risk: `0.127`
- max penetration: `0.002542 m`

Interpretation:

```text
Stage3.7B is the current best Stage3 learned-control baseline.
It improves mean transient slip while preserving success, hold stability, crush,
and penetration margins.
```

Remaining risk:

```text
The worst slip peaks are now contact-transition peaks around contact_settle,
gentle_close_thumb, and slow_lift, not a simple lift-permission timing problem.
The early_contact_in_approach risk flag also remains and should be handled by
an approach/contact gate.
```

Recommended next step:

```text
Stage3.7C approach/contact gate:
detect early tactile contact during approach or thumb close, pause/retreat or
re-align, then re-test the same fixed 10 and randomized 30 gates.
```

## Stage3.7C Contact Transition Gate

Stage3.7C tested contact-transition pauses on top of Stage3.7B.

Script:

```text
models/arm_hand_stage1_export/eval_stage3_contact_transition_gate_v0.py
```

Closeout:

```text
models/arm_hand_stage1_export/docs/stage3_contact_transition_gate_v0_closeout.md
```

Selected default:

- stop approach on contact: `False`
- transition gate phases: `slow_lift`
- transition slip threshold: `0.28`
- max transition hold steps per phase: `150`
- contact-settle gate: `2000` min / `2000` max steps

Fixed 10-trial result:

- success: `10 / 10`
- mean max transient slip improved to `0.564`
- max transient slip remained `0.941`
- max hold slip: `0.264`
- max crush risk: `0.111`
- max penetration: `0.002223 m`

Randomized 30-trial result with `random_offset_std = 0.005 m`:

- success: `30 / 30`
- mean max transient slip improved to `0.602`
- max transient slip remained `1.000`
- max hold slip: `0.315`
- max crush risk: `0.127`
- max penetration: `0.002542 m`

Interpretation:

```text
Stage3.7C is the current best Stage3 learned-control baseline.
The useful repair is a bounded slow_lift pause, not approach-stop or broad
thumb-close pause.
```

Remaining risk:

```text
transition_gate_budget_exhausted remains common, so the pause is only a
mitigation. The next repair should be an explicit contact-transition recovery
micro-phase that can slightly lower lift, hold, and retry without raising hold
slip above 0.35.
```

Do not promote a model from offline loss alone. Promotion requires closed-loop
MuJoCo success against the same fixed Stage3 trials, then randomized/noisy
virtual-camera trials.
