# Stage3.11D-C Geometry + Force-Feedback Refine v0 Closeout

Generated: `2026-06-12`

## Boundary

- MuJoCo-only Stage3 diagnostic training/search.
- No real hardware, real camera, real tactile hardware, ultrasound, or hardware
  runtime integration.
- Not a demo-gallery promotion.
- Not full-action ACT/DP closed-loop success.
- Neural-network training has not started in this stage; this stage selects the
  next dense-capture center.

## What Changed

Stage3.11D-C added:

```text
simulations/models/arm_hand_stage1_export/train_stage3_11d_c_geometry_force_refine_v0.py
```

The runner:

- loads the Stage3.11D-B high-lift selected case,
- centers local search around `gx = -0.0008 m`,
- sweeps small geometry/control parameters,
- keeps simulated active-pair motor force feedback enabled as an observation,
- runs local event-gated evaluation,
- runs randomized smoke robustness on top candidates,
- reruns final candidates with a shared final seed,
- includes the `gx = -0.0008 m` center control in final evaluation,
- writes report, metadata, selected case, and visual contact sheet.

## Result

Local search:

- Cases evaluated: `36`
- Local event true-pinch-release success: `33 / 36`
- Contact gate: `36 / 36`
- Lift gate: `34 / 36`
- True-pinch gate: `33 / 36`
- Release: `36 / 36`
- Failures: `2` lift failures, `1` true-pinch morphology failure

Final selected candidate:

```text
s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700
```

Selected geometry:

- `grasp_offset_x = -0.0008 m`
- `grasp_offset_z = 0.0020 m`
- `tip_pair_separation_target = 0.060 m`
- `thumb_mcp = 0.28`
- `active_mcp_abd = -0.50`
- `active_pip = -0.70`

Final 50-trial robustness:

- Full success: `43 / 50`
- Contact gate: `49 / 50`
- Lift gate: `44 / 50`
- True-pinch gate: `43 / 50`
- Release: `50 / 50`
- Terminal reasons:
  - `43` success
  - `5` lift_gate_failed
  - `1` true_pinch_morphology_gate_failed
  - `1` contact_gate_failed
- Successful hold-lift mean/min/max: `0.11276 / 0.11093 / 0.11452 m`
- Mean slow-lift active-pair tension proxy: `7.8862 N`
- Mean hold active-pair tension proxy: `4.3746 N`
- Saturation trial fraction: `0.000`

This improves over the previous recorded 50-trial `gx -0.0008 m` result
(`34 / 50`) and over the 50-trial baseline (`29 / 50`) under the currently
selected Stage3.11D-C evaluation setup.

## Artifacts

Report:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_c_geometry_force_refine_v0_report.md
```

Metadata:

```text
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_c_geometry_force_refine_v0.json
```

Selected case:

```text
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_c_geometry_force_refine_selected_v0.json
```

Visual contact sheet:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_c_geometry_force_refine_vis/s311dc_thumb_middle_gxm0p0008_gzp0p0020_sep0p060_tmcpp0p280_aabdm0p500_apipm0p700_contact_sheet.png
```

## Interpretation

The best candidate is the original `gx -0.0008 m` geometry center, not one of
the neighboring hand-angle variants. The local sweep was still useful because
it showed:

- active-finger abduction at `-0.53` is risky,
- lowering `gz` to `0.0015 m` can increase lift count but hurts true-pinch
  morphology,
- `sep = 0.056` with higher thumb MCP looked good in smoke but did not survive
  the 50-trial final gate,
- the center geometry has the best balance of contact, lift, true-pinch, and
  release under the final shared seed.

Force feedback remains an observation/gate/label signal. Direct preload is not
the default controller.

## Next

Stage3.11D-D should be dense capture from this selected center:

- per-step observation,
- action targets,
- active-pair motor force feedback,
- morphology labels,
- phase labels,
- terminal/failure labels,
- and residual micro-adjust labels.

The first trainable targets should be:

1. `LiftQualityHead`: predict whether slow-lift/hold is safe to continue.
2. `ResidualMicroAdjustPolicy`: small bounded corrections, not full-action
   actuator control.

Do not promote this to demo gallery until close-up visual review confirms that
the ball is visibly pinched, lifted, held, and released cleanly.
