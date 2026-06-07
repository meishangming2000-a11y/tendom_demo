# Stage3 Sensor Fusion BC Baseline V0 Model Result

Generated: 2026-06-05

## Purpose

This experiment tested whether the Stage3 sensor abstraction can support a
learned controller before hardware is available.

Scope:

- MuJoCo only
- virtual-camera pose abstraction
- contact-derived tactile/slip abstraction
- no real camera
- no hardware interface

The key question was not "can the model fit the dataset offline?", but:

```text
Can a learned policy close the loop in MuJoCo and gently lift the egg?
```

## Artifacts

Dataset:

```text
models/arm_hand_stage1_export/data/stage3_sensor_fusion_expert_dataset_v0.npz
```

Training script:

```text
models/arm_hand_stage1_export/train_stage3_sensor_fusion_bc_baseline.py
```

Evaluation script:

```text
models/arm_hand_stage1_export/eval_stage3_sensor_fusion_bc_baseline.py
```

Primary checkpoint:

```text
models/arm_hand_stage1_export/checkpoints/stage3_sensor_fusion_bc_baseline_v0.pth
```

Overfit sanity checkpoint:

```text
models/arm_hand_stage1_export/checkpoints/stage3_sensor_fusion_bc_baseline_v0_overfit.pth
```

## Training Result

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_sensor_fusion_bc_baseline.py --epochs 120 --batch-size 1024
```

Result:

- feature mode: `obs_only`
- feature dim: `130`
- action dim: `26`
- train episodes: `[0, 1, 2, 3, 5, 6, 7, 9]`
- val episodes: `[4, 8]`
- final train normalized MSE: `0.00004627`
- final val normalized MSE: `0.00673794`
- train action RMSE raw: `0.00234676`
- val action RMSE raw: `0.01273346`

The largest validation errors are in the arm and wrist actuators. The finger
actuator errors are much smaller, which foreshadowed the closed-loop result:
the hand portion is easier to imitate than the whole arm-hand trajectory.

## Closed-Loop Matrix

| controller | checkpoint | arm/wrist | hand/fingers | success | mean final lift | hold stable | max hold slip | max crush | max penetration | report |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| scripted expert | n/a | expert | expert | `10 / 10` | `0.103056 m` | `1.000` | `0.262` | `0.113` | `0.002259 m` | `stage3_sensor_aware_gentle_grasp_expert_v0_report.md` |
| full BC | normal split | BC | BC | `0 / 10` | `-0.009690 m` | `0.000` | `1.000` | `0.476` | `0.009521 m` | `stage3_sensor_fusion_bc_baseline_v0_eval_report.md` |
| full BC | overfit sanity | BC | BC | `0 / 10` | `-0.010207 m` | `0.000` | `0.000` | `0.360` | `0.007197 m` | `stage3_sensor_fusion_bc_baseline_v0_overfit_eval_report.md` |
| hybrid | normal split | expert | BC | `10 / 10` | `0.103356 m` | `1.000` | `0.262` | `0.110` | `0.002199 m` | `stage3_sensor_fusion_bc_baseline_v0_hybrid_eval_report.md` |
| hybrid | overfit sanity | expert | BC | `10 / 10` | `0.103294 m` | `1.000` | `0.262` | `0.114` | `0.002276 m` | `stage3_sensor_fusion_bc_baseline_v0_overfit_hybrid_eval_report.md` |

Hybrid mode used:

```text
--hybrid-control expert_arm_bc_hand
--expert-prefix-actuators 6
```

That means the first six actuators, corresponding to arm and wrist control,
came from the scripted expert; the remaining hand/finger actuators came from
the BC model.

## Interpretation

The normal-split BC model fits the offline dataset well enough to be useful,
but full-action closed-loop BC fails. Even an overfit sanity model fails when it
controls all 26 actuators. That points to a policy-structure problem rather
than a simple train/validation split problem.

The arm/wrist approach trajectory is high sensitivity. Small actuator errors
early in approach and preshape shift the hand away from the true egg pose, so
the later finger commands cannot recover. This shows why low offline loss is
not a promotion gate for this task.

The hand/finger part is learnable. When the arm/wrist remain scripted and the
BC model controls the hand/fingers, the policy passes the same fixed 10-trial
closed-loop MuJoCo gate.

## Decision

Do not promote monolithic full-action BC for Stage3.

Promote the following learning direction instead:

```text
vision-guided scripted arm/wrist approach
+ learned hand/finger closure and hold
+ learned residual corrections for slip/crush during contact phases
```

This matches the evidence:

- vision is already useful for estimating where the egg is
- tactile/slip is most useful after contact begins
- scripted arm/wrist approach is currently more reliable than full BC
- learned hand/finger control can match the expert on the fixed gate

## Next Gate

The next model gate should train and evaluate a phase-specific or residual
policy:

1. keep acquire/approach/preshape arm and wrist control deterministic
2. learn hand/finger actions during close/lift/hold
3. optionally learn residual corrections that reduce known risks:
   - early contact in approach
   - transient non-hold slip
   - crush risk
   - penetration
4. require closed-loop MuJoCo evaluation before promotion
5. only after fixed 10-trial success, add randomized object offsets, noisy
   virtual-camera settings, and timing variation

Promotion criteria for the next learned module:

- fixed Stage3 gate success: `10 / 10`
- mean hold stable fraction near `1.000`
- max penetration no worse than the scripted expert envelope
- no new failure mode compared with the scripted expert
- improvement on at least one known risk metric before claiming it improves the
  expert
