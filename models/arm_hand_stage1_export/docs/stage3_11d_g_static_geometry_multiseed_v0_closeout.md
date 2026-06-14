# Stage3.11D-G Static Geometry Multiseed Closeout v0

Generated: `2026-06-12`

## Boundary

- MuJoCo-only diagnostic candidate for the small-ball true-pinch-release lane.
- Uses the existing event/contact-gated controller and simulated motor force feedback telemetry.
- D-G only changes the static `grasp_offset_x` center from the Stage3.11D-C selected geometry.
- Not a hardware runtime, real camera, real tactile, ultrasound, demo-gallery, or full-action ACT/DP promotion.

## Why D-G Exists

Stage3.11D-E proved that the `LiftQualityHead` can detect low-quality lift windows online, but the first Stage3.11D-F residual probes did not improve the controller. The failed D-F variants showed that blind waiting, blind extra close, and uniform x-retargeting do not rescue the failure cluster. Some pre-lift retarget variants actively damaged successful cases.

The useful signal was earlier in the pipeline: failure clustering showed positive `grasp_offset_x` cases tended toward lift failure, while overly negative cases tended toward contact failure. D-G therefore tested static geometry centers before adding more online control.

## Selected Candidate

- Selected offset: `grasp_offset_x = -0.0014 m`
- Other selected geometry remains from Stage3.11D-C:
  - `grasp_offset_z = 0.0020 m`
  - `tip_pair_separation = 0.060 m`
  - `active_finger = middle`
  - `thumb_mcp = 0.28`
  - `active_mcp_abd = -0.50`
  - `active_pip = -0.70`

Selected metadata:

```text
simulations/models/arm_hand_stage1_export/metadata/stage3_11d_g_static_geometry_multiseed_selected_v0.json
```

## Multiseed Result

Known 50-trial seed comparison:

| seed | old gx=-0.0008 | new gx=-0.0014 | delta |
|---:|---:|---:|---:|
| `20260612` | `36 / 50` | `42 / 50` | `+6` |
| `20265612` | `43 / 50` | `46 / 50` | `+3` |
| `20265613` | `36 / 50` | `40 / 50` | `+4` |
| total | `115 / 150` | `128 / 150` | `+13` |

D-G selected aggregate:

- Full event true-pinch-release success: `128 / 150`
- Contact gate: `139 / 150`
- Lift gate: `128 / 150`
- True-pinch morphology gate: `128 / 150`
- Release: `147 / 150`
- Terminal failures: `11` contact-gate, `11` lift-gate

Individual reports:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_g_static_gx_m0014_50_ddseed_report.md
simulations/models/arm_hand_stage1_export/docs/stage3_11d_g_static_gx_m0014_50_dcfinalseed_report.md
simulations/models/arm_hand_stage1_export/docs/stage3_11d_g_static_gx_m0014_50_seed20265613_report.md
```

## Visual Evidence

D-G close-up visual check:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_g_static_geometry_side_vis/event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0014_gyp0p0000_gzp0p0020_lj2m0p950_ls520_hs100_ml0p100_contact_sheet.png
```

Observed:

- The rendered single-case D-G visual run passed `1 / 1`.
- Hold frame metrics: `lift=0.1091`, `floor=0`, `regions=middle,thumb`, `true2tip=True`, `tip=1.00`, `non_tip=0.00`, `wrap=False`.
- The thumb-side close-up frame shows the ball held between thumb and middle fingertips.
- `05_release_open_thumb_side` shows the fingers opened and the ball released to the floor.

Visible issue:

- The default camera and finger-side camera still partially occlude the ball.
- The ball is lifted, but the view is close to the floor reflection, so the demo needs a thumb-side/oblique camera and possibly more visual lift margin before gallery discussion.

Visual report:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_g_static_geometry_visual_side_v0_report.md
```

## D-F Residual Decision

Stage3.11D-F is kept as diagnostic evidence, not a promoted controller:

- Wait-only residual matched baseline on the final seed and did not rescue failures.
- Extra close residuals raised hand-side tension but did not improve success.
- Slow-lift x-retarget residuals did not improve D-D seed robustness.
- Pre-lift x-retarget variants worsened results after the trigger bug was fixed.

Conclusion: the current failure is not solved by unconditional "pinch harder" or uniform x motion. The next residual must be contact-conditioned and directional, or it should not be added.

## Next

If successful:

- Treat `gx=-0.0014` as the next diagnostic center for close-up visual inspection and contact-conditioned repair probes.
- Re-run any new residual against this D-G center, not the older D-C `gx=-0.0008` center.

If failed:

- Repair contact-gate geometry, fingertip proxy/material modeling, or phase timing before training broader neural policies.
- Keep the `LiftQualityHead` as online shadow/label telemetry, not direct control.
