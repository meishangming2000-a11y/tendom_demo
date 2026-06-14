# Stage3.11D-I Demo-Quality Static Geometry Closeout v0

Generated: `2026-06-12`

## Boundary

- MuJoCo-only diagnostic candidate for the 18 mm small-ball true-pinch-release lane.
- Uses the existing event/contact-gated controller and simulated motor force-feedback telemetry.
- Not hardware runtime, real camera, real tactile, ultrasound, demo-gallery promotion, or full-action ACT/DP.

## Selected Candidate

D-I selects the visually cleaner geometry:

```text
grasp_offset_x = -0.0014 m
grasp_offset_z = 0.0022 m
lift_steps = 480
tip_pair_separation = 0.060 m
active_finger = middle
```

Selected metadata:

```text
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_i_demo_quality_static_geometry_selected_v0.json
```

## Why This Beats The Previous Center

| candidate | purpose | success |
|---|---|---:|
| Stage3.11D-C `gx=-0.0008,gz=0.0020,ls520` | old selected center | `115 / 150` |
| Stage3.11D-G `gx=-0.0014,gz=0.0020,ls520` | first static x repair | `128 / 150` |
| Stage3.11D-H `gx=-0.0014,gz=0.0025,ls480` | max robustness | `137 / 150` |
| Stage3.11D-I `gx=-0.0014,gz=0.0022,ls480` | demo-quality selected | `136 / 150` |

D-H is still the best raw multiseed count by 1 trial, but its inspected hold frame had `tip=0.67` and `non_tip=0.33`. D-I gives up one success in `150` trials while restoring a cleaner visual pinch: inspected hold frame had `tip=1.00`, `non_tip=0.00`, and `wrap=False`.

## Multiseed Result

| seed | success | contact | lift | true pinch | release | failures |
|---:|---:|---:|---:|---:|---:|---|
| `20260612` | `44 / 50` | `47 / 50` | `44 / 50` | `44 / 50` | `50 / 50` | 3 lift, 3 contact |
| `20265612` | `46 / 50` | `48 / 50` | `46 / 50` | `46 / 50` | `50 / 50` | 2 lift, 2 contact |
| `20265613` | `46 / 50` | `48 / 50` | `46 / 50` | `46 / 50` | `49 / 50` | 2 lift, 2 contact |
| total | `136 / 150` | `143 / 150` | `136 / 150` | `136 / 150` | `149 / 150` | 7 lift, 7 contact |

Reports:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_i_gx_m0014_gz_p0022_ls480_50_ddseed_report.md
simulations/models/arm_hand_stage1_export/docs/stage3_11d_i_gx_m0014_gz_p0022_ls480_50_dcfinalseed_report.md
simulations/models/arm_hand_stage1_export/docs/stage3_11d_i_gx_m0014_gz_p0022_ls480_50_seed20265613_report.md
```

## Visual Check

Visual evidence:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_i_static_geometry_side_vis/event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0014_gyp0p0000_gzp0p0022_lj2m0p950_ls480_hs100_ml0p100_contact_sheet.png
```

Observed in the inspected `04_hold_thumb_side` frame:

- `lift=0.1122`
- `hand=2`
- `floor=0`
- `regions=middle,thumb`
- `true2tip=True`
- `tip=1.00`
- `non_tip=0.00`
- `wrap=False`

The visible behavior is a thumb+middle fingertip pinch of the small ball, followed by finger opening and release. The thumb-side/oblique view should be the default camera for the next viewer/demo polish pass.

## Decision

- Promote D-I as the current demo-quality diagnostic candidate.
- Keep D-H as a comparison candidate when the only target is maximum raw multiseed count.
- Keep D-F residuals rejected unless the next repair is contact-conditioned and directional.

## Next

- Build a short D-I viewer/demo wrapper or alias with the thumb-side camera.
- Target the remaining 14/150 failures with contact-conditioned repair: 7 contact-gate failures and 7 lift-gate failures.
- Keep force feedback as simulated observation/label telemetry until it beats D-I in a shared closed-loop gate.
