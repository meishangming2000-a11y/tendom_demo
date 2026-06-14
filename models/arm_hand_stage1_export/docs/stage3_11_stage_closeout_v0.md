# Stage3.11 Stage Closeout v0

Generated: `2026-06-13`

## Decision

Stage3.11 is closed for now. Do not keep optimizing the same small-ball pinch demo unless a future task explicitly reopens this lane.

The stage produced useful system assets, but it did not promote a new full-action controller or a hardware-facing runtime:

- Stage3.10E remains the robust mixed-control safety baseline.
- Stage3.11B/C/D outputs are kept as safety, label, force-feedback telemetry, and true-pinch diagnostic assets.
- Stage3.11D-I is frozen as the current MuJoCo-only demo-quality small-ball true-pinch-release diagnostic candidate.
- The remaining D-I contact/lift failures are backlog items, not the next mainline.

## What Stage3.11 Was For

Stage3.11 was not meant to be an endless parameter search. Its plan was to take the Stage3.10E mixed-control baseline and make the system more trainable and inspectable:

1. Connect the safety head online in shadow mode.
2. Export frame-level noisy-vision, occlusion, tactile-handoff, repair, and risk labels.
3. Add simulated motor force-feedback telemetry from MuJoCo actuator loads.
4. Audit whether the visible grasp is a real fingertip pinch or a wrapping clamp.
5. Try residual-policy directions only when they beat the baseline under shared gates.

## Accepted Results

| item | result | status |
|---|---|---|
| Stage3.11B online safety-head shadow | D-B v1 `100 / 100`, stress `13 / 14`, unsafe hold-safe prediction `0` | keep as shadow evaluator |
| Stage3.11C frame labels | `164` episodes, `2663` trace frames, `17` labels | keep as label dataset |
| Stage3.11D motor force feedback | simulated actuator-load / tendon-tension telemetry connected | keep as observation/label signal |
| Stage3.11D-D LiftQualityHead | dense capture `200` episodes / `329075` rows; val F1 about `0.9998 / 0.9992 / 1.0000` | keep as quality head, not controller |
| Stage3.11D-E online LiftQualityHead | 50-trial shadow evidence-phase F1 `0.9992 / 0.9980 / 1.0000` | keep as shadow telemetry |
| Stage3.11D-F residual probes | blind wait/close/x-retarget residuals did not improve robustness | rejected |
| Stage3.11D-I demo-quality geometry | `136 / 150`, clean thumb-side visual: `tip=1.00`, `non_tip=0.00`, `wrap=False` | freeze as diagnostic demo candidate |

## Non-Promotions

- No full-action 26-actuator ACT/DP success is claimed.
- No real camera, real tactile, ultrasound, or hardware runtime integration is claimed.
- No direct force-control promotion is claimed. Motor force feedback remains simulated telemetry.
- D-I is not a robust production baseline. It is a clean visual diagnostic candidate with known remaining failures.

## Frozen D-I Candidate

```text
grasp_offset_x = -0.0014 m
grasp_offset_z = 0.0022 m
lift_steps = 480
tip_pair_separation = 0.060 m
active_finger = middle
```

Multiseed result:

```text
success:    136 / 150
contact:    143 / 150
lift:       136 / 150
true pinch: 136 / 150
release:    149 / 150
```

Primary D-I evidence:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_i_demo_quality_static_geometry_v0_closeout.md
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_i_demo_quality_static_geometry_selected_v0.json
simulations/models/arm_hand_stage1_export/docs/stage3_11d_i_static_geometry_visual_side_v0_report.md
```

## Backlog, Not Current Mainline

These are useful later, but not worth blocking the project on now:

- Build a D-I thumb-side viewer/demo alias.
- Try contact-conditioned repair for the remaining D-I failures.
- Expand force-feedback labels into a better residual-policy training target.
- Revisit fingertip proxy geometry if future hardware contact geometry requires it.

## Next Mainline

Move on from Stage3.11. The next higher-value work should be one of:

1. Stage4/readiness: define the real motor, current/torque, tendon-tension, encoder, tactile, and safety data contract.
2. Real-to-sim bridge: map the simulated force-feedback/tactile labels onto measurable hardware signals.
3. Next model-training stage: use the closed Stage3.11 label and telemetry assets to design a bounded, sensor-conditioned residual policy, with a clear promotion gate before any controller claim.

如果成功:

- The next stage should produce a hardware-facing or data-contract artifact that makes real force feedback and tactile control trainable.

如果失败:

- Keep Stage3.10E as the robust MuJoCo baseline and Stage3.11 as the diagnostic/data package; do not return to open-ended D-I parameter tuning without a new gate.
