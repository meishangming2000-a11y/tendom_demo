# Stage3.6 Phase Hand Policy V0 Closeout

Generated: 2026-06-05

## Purpose

Stage3.6 formalizes the useful result from the earlier hybrid BC test:

```text
scripted arm/wrist approach
+ learned hand/finger control during contact/lift/hold phases
```

This stays MuJoCo-only. It uses virtual-camera pose abstraction and
contact-derived tactile/slip abstraction. It does not use real cameras or
hardware.

## Why This Exists

The previous full-action BC baseline learned all `26` actuators and failed
closed-loop `0 / 10`, even when overfit. The failure came from the
high-sensitivity arm/wrist approach. Small approach errors moved the hand away
from the egg, so later finger commands could not recover.

Stage3.6 keeps that sensitive part scripted and trains only the hand/finger
slice.

## Artifacts

Training script:

```text
models/arm_hand_stage1_export/train_stage3_phase_hand_policy_v0.py
```

Evaluation script:

```text
models/arm_hand_stage1_export/eval_stage3_phase_hand_policy_v0.py
```

Checkpoint:

```text
models/arm_hand_stage1_export/checkpoints/stage3_phase_hand_policy_v0.pth
```

Reports:

```text
models/arm_hand_stage1_export/docs/stage3_phase_hand_policy_v0_train_report.md
models/arm_hand_stage1_export/docs/stage3_phase_hand_policy_v0_eval_report.md
```

Metadata:

```text
models/arm_hand_stage1_export/metadata/stage3_phase_hand_policy_v0_train.json
models/arm_hand_stage1_export/metadata/stage3_phase_hand_policy_v0_eval.json
```

## Training

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_phase_hand_policy_v0.py --epochs 120 --batch-size 1024
```

Training scope:

- input: `obs`
- target: hand/finger slice of `expert_actions`
- hand action dim: `20`
- arm/wrist actuators excluded from model target
- learned phases:
  - `gentle_close_fingers`
  - `gentle_close_thumb`
  - `contact_settle`
  - `slow_lift`
  - `hold`

Result:

- train samples: `21920`
- val samples: `5480`
- final train normalized MSE: `0.00000416`
- final val normalized MSE: `0.00463073`
- train hand-action RMSE raw: `0.00036781`
- val hand-action RMSE raw: `0.00510821`

## Closed-Loop MuJoCo Eval

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\eval_stage3_phase_hand_policy_v0.py
```

Evaluation behavior:

- arm/wrist: scripted expert in all phases
- hand/fingers: learned policy only in configured learned phases
- approach/preshape outside learned phases: full scripted expert action

Result:

- status: `PASS`
- success count: `10 / 10`
- terminal reasons: `{'success_gentle_grasp_hold': 10}`
- mean final lift: `0.103050 m`
- mean hold stable fraction: `1.000`
- max hold slip: `0.262`
- max crush risk: `0.113`
- max penetration: `0.002260 m`
- learned-control steps per episode: `2740`

Known risk flags remain:

- `early_contact_in_approach`: `10 / 10`
- `transient_or_hold_slip`: `10 / 10`

These are inherited from the current scripted expert envelope and are not fixed
by the hand imitation policy.

## Decision

Stage3.6 passes the fixed 10-trial gate as the formal hand-only learned policy
baseline.

Promote this as the next control structure for Stage3 model work:

```text
scripted vision-guided arm/wrist
+ learned phase-specific hand/finger policy
```

Do not promote monolithic full-action BC.

## Next Gate

Start Stage3.7 tactile residual correction.

The residual policy should try to reduce the two known risks without reducing
the fixed 10-trial success rate:

- early contact in approach
- transient non-hold slip

Suggested structure:

```text
base action = scripted arm/wrist + Stage3.6 learned hand policy
residual = small tactile/slip correction on hand/finger targets
final action = base action + residual
```

Promotion criteria:

- fixed 10-trial success remains `10 / 10`
- hold stable fraction remains near `1.000`
- max penetration stays within the expert envelope
- at least one risk metric improves before claiming the residual policy improves
  the expert
