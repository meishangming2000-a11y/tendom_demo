# Export3 Diagnostic Training Status

Status: diagnostic training scaffold, not a promoted stable_grasp baseline.

## Generated Files

- `scripts\collect_export3_scripted_dataset.py`
- `scripts\train_export3_bc.py`
- `scripts\eval_export3_bc.py`
- `data\export3_scripted_pinned_wrap_v0.npz`
- `metadata\export3_scripted_dataset_v0.json`
- `metadata\export3_bc_pinned_wrap_v0.json`
- `metadata\export3_bc_pinned_wrap_v0_eval.json`
- `docs\export3_scripted_dataset_v0_report.md`
- `docs\export3_bc_pinned_wrap_v0_report.md`
- `docs\export3_bc_pinned_wrap_v0_eval_report.md`
- `checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`

## Dataset v0

- Scene: `mjcf\scene_ball_export3.xml`
- Collection mode: pinned scripted export3 wrap
- Episode count: 75
- Sample count: 6000
- Observation dim: 109
- Action dim: 21
- Action semantics: MuJoCo position actuator targets
- Labels:
  - `PINNED_WRAP_PASS`
  - `PINNED_PARTIAL`

Observation includes:

- controlled joint qpos/qvel
- ball pose/velocity
- fingertip site positions
- fingertip-ball distances
- contact count and max penetration
- previous actuator target
- stage fraction
- stage one-hot
- finger scale
- thumb rank
- thumb target pose
- target ball position

## BC Training

- Checkpoint: `checkpoints\bc_hand_stage1_export3_pinned_wrap_v0.pth`
- Model: state-based MLP BC
- Hidden dim: 192
- Depth: 3
- Epochs: 80
- Class filter: `PINNED_WRAP_PASS`
- Final normalized val MSE: about `0.000187`
- Val action RMSE in raw actuator units: about `0.00405`

The offline fit is good enough for a first diagnostic BC model. It does not prove rollout stability by itself.

## Online Eval

Default eval settings after debugging:

- Speed: `2.5`
- Action smoothing: `0.0`
- Main comparison episodes: 75

Best current result remains the original BC v0:

- `PINNED_WRAP_PASS`: 63 / 75
- `PINNED_PARTIAL`: 12 / 75
- Pinned-wrap pass rate: `0.840`
- Mean hold contacts: about `3.28`
- Mean hold penetration: about `0.00731 m`

The earlier 30-episode smoke eval produced 19 / 30 pass. The 75-episode sweep is now the more useful comparison set.

Earlier failed settings:

- With action smoothing `0.15`, rollout degraded badly.
- The policy output needed training-action-envelope clipping to avoid actuator-limit saturation.
- Stage one-hot and thumb target pose were required in observation; otherwise BC suffered severe closed-loop ambiguity.

## DAgger v1 Check

Goal:

- Use the BC v0 policy to visit on-policy states.
- Relabel those states with the scripted expert target at the same stage/fraction.
- Test whether DAgger-style corrections improve pinned-wrap rollout.

Generated:

- `scripts\collect_export3_dagger_dataset.py`
- `data\export3_dagger_pinned_wrap_v1.npz`
- `data\export3_dagger_failonly_pinned_wrap_v1.npz`
- `checkpoints\bc_hand_stage1_export3_dagger_v1.pth`
- `checkpoints\bc_hand_stage1_export3_dagger_failonly_v1.pth`
- `checkpoints\bc_hand_stage1_export3_dagger_failonly_ft_v1.pth`
- `docs\export3_dagger_dataset_v1_report.md`
- `docs\export3_dagger_failonly_dataset_v1_report.md`
- `docs\export3_bc_dagger_v1_eval_all75_report.md`
- `docs\export3_bc_dagger_failonly_v1_eval_all75_report.md`
- `docs\export3_bc_dagger_failonly_ft_v1_eval_all75_report.md`
- `scripts\analyze_export3_bc_failure_buckets.py`
- `docs\export3_bc_v0_failure_buckets.md`
- `metadata\export3_bc_v0_failure_buckets.json`

75-episode rollout comparison:

| Model | Dataset / training mode | Pass | Partial | Pass rate | Mean hold contacts | Mean hold penetration |
|---|---|---:|---:|---:|---:|---:|
| BC v0 | Successful scripted pinned-wrap only | 63 | 12 | 0.840 | 3.28 | 0.00731 m |
| DAgger v1 | All on-policy rollout states corrected | 58 | 17 | 0.773 | 2.91 | 0.00699 m |
| DAgger fail-only v1 | Only v0 partial rollout states corrected | 58 | 17 | 0.773 | 3.01 | 0.00732 m |
| DAgger fail-only fine-tune v1 | v0 checkpoint low-lr fine-tune on fail-only correction set | 56 | 19 | 0.747 | 2.87 | 0.00787 m |

Diff against BC v0 for fail-only v1:

- Fixed 2 previous partial cases.
- Regressed 7 previous pass cases.
- Net effect was negative, so DAgger v1 is not promoted.

Interpretation:

- The current scripted expert is not yet a strong enough oracle for blind DAgger aggregation.
- The correction labels appear to perturb useful v0 behavior instead of only repairing the partial cases.
- The best checkpoint to keep using for diagnostic pinned-wrap is still `bc_hand_stage1_export3_pinned_wrap_v0.pth`.
- Next learning work should use better targeted correction data or a sequence/phase-conditioned policy, not simply aggregate all DAgger samples.

## Failure Buckets

BC v0 partial cases are concentrated rather than random:

- Ball `[0.000, -0.100, 0.195]`: 6 partial / 15, partial rate `0.400`.
- Ball `[0.000, -0.100, 0.210]`: 5 partial / 15, partial rate `0.333`.
- Thumb rank `5`: 5 partial / 15, partial rate `0.333`.
- Finger scale `1.15`: 6 partial / 25, partial rate `0.240`.

Report:

- `docs\export3_bc_v0_failure_buckets.md`
- `metadata\export3_bc_v0_failure_buckets.json`

## Interpretation

This confirms that export3 can now support the first diagnostic training loop:

```text
scripted export3 data -> state-based BC -> MuJoCo rollout eval -> report
```

This is still not stable free-object grasp:

- ball is pinned during the collected/evaluated close phase
- free zero-g release was not trained here
- gravity release was not trained here
- collision remains primitive proxy
- STL remains visual-only
- thumb and wrist mechanical semantics still require confirmation

## Next Steps

1. Keep BC v0 as the current best diagnostic pinned-wrap checkpoint.
2. Improve data quality before more DAgger: collect more successful cases around the failure regions, especially low finger-scale and offset-ball configurations.
3. Add per-config evaluation plots and targeted failure buckets before training another model.
4. Add a zero-g release dataset/eval mode only after pinned BC is reliably above 90 percent pass.
5. Tune collision proxy and thumb pose before demo-augmented RL.
6. Do not start PPO/DAPG as a benchmark line until zero-g release and contact metrics are more stable.
