# Stage3.11D-B gx -0.0008 Lift Timing Expansion v0 Closeout

Generated: `2026-06-12`

## Boundary

- MuJoCo-only Stage3 diagnostic work.
- No real hardware, real camera, real tactile, ultrasound, or motor-driver data.
- Not a demo-gallery promotion.
- Not full-action ACT/DP closed-loop success.

## What Changed

1. Added `grasp_offset_x_values` and `grasp_offset_y_values` to the event
   contact-gated refine runner so local search can sweep the grasp center
   directly.
2. Increased event-runner name precision for small `gx/gy/gz` offsets.
3. Added robustness-runner override flags for candidate and case parameters:
   thumb abduction/MCP, active-finger abduction/PIP, grasp offsets, tip-pair
   separation, lift joint, lift steps, hold steps, and min lift height.
4. Ran a robustness-aware candidate selection pass after local refine showed
   nominal score can overfit the center pose.

## Search Results

Local refine around `gx -0.0008`:

- Cases evaluated: `80`
- Nominal full true-pinch-release pass: `52 / 80`
- Failure pattern: `28` contact-gate failures
- Nominal selected candidate:
  - `gx = -0.0006`
  - `gz = 0.0015`
  - `active_mcp_abd = -0.46`
  - `lift_steps = 520`
- Randomized 50-trial result for this nominal selected candidate: `15 / 50`
- Conclusion: nominal local score overfit the center pose; do not promote it.

Robustness-aware 24-trial candidate probes:

| Candidate | 24-trial result | Main issue |
| --- | ---: | --- |
| `active_abd=-0.48, gx=-0.0010, gz=0.0020` | `14 / 24` | Contact fragility |
| `active_abd=-0.46, gx=-0.0008, gz=0.0015` | `7 / 24` | Contact fragility |
| `thumb_abd=-0.33, active_abd=-0.46, gx=-0.0008, gz=0.0020` | `12 / 24` | Contact fragility |
| `active_abd=-0.48, gx=-0.0008, gz=0.0020` | `15 / 24` | Contact/lift failures |
| `base hand, gx=-0.0008, lift_j2=-0.93` | `17 / 24` | Better lift, same failure structure |
| `base hand, gx=-0.0008, lift_j2=-0.91` | `17 / 24` | Better lift, same failure structure |
| `base hand, gx=-0.0008, lift_steps=480` | `17 / 24` | Best clean lift-timing probe |
| `base hand, gx=-0.0008, lift_j2=-0.91, lift_steps=480` | `17 / 24` | Added one morphology failure |

## New Best Diagnostic Candidate

The best verified candidate from this pass keeps the original hand geometry and
uses:

- `grasp_offset_x = -0.0008`
- `grasp_offset_z = 0.0020`
- `lift_steps = 480`
- `lift_j2 = -0.95`
- `active_mcp_abd = -0.50`
- `active_pip = -0.70`
- `thumb_cmc_abd = -0.35`
- `thumb_mcp = 0.28`

50-trial randomized robustness:

- Success: `36 / 50`
- Contact gate: `47 / 50`
- Lift gate: `36 / 50`
- True-pinch gate: `36 / 50`
- Release: `49 / 50`
- Terminal reasons:
  - `36` success
  - `11` lift-gate failures
  - `3` contact-gate failures
- Success hold-lift mean: `0.11471 m`
- Success hold-lift max: `0.11729 m`
- Mean slow-lift active-pair tension proxy: `7.5235 N`
- Mean hold active-pair tension proxy: `4.3188 N`
- Saturation trial fraction: `0.000`

Previous reference:

- 50-trial baseline: `29 / 50`
- 50-trial `gx -0.0008`: `34 / 50`
- New `gx -0.0008 + lift_steps=480`: `36 / 50`

## Visual Check

Selected candidate contact sheet:

```text
simulations/models/arm_hand_stage1_export/docs/v11db_gxm0008_ls480_vis/event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gxm0p0008_gyp0p0000_gzp0p0020_lj2m0p950_ls480_hs100_ml0p100_contact_sheet.png
```

Visual interpretation:

- The ball is lifted and released cleanly in the selected run.
- It is not the earlier three-finger enclosure pattern.
- The default view still partially hides the thumb-side contact, so this is not
  demo-gallery promotion evidence by itself.
- Morphology gates remain the main truth source for this pass: hold true
  two-tip `1.000`, wrap `0.000`, non-tip ratio `0.000`, release true.

## Interpretation

The local hand-geometry search did not beat the prior robust geometry. It
mostly made the contact gate more fragile under randomized object/grasp
perturbations.

The useful improvement came from lift timing: shortening the slow-lift schedule
from `520` to `480` steps while keeping the already validated `gx -0.0008`
geometry improved 50-trial robustness from `34 / 50` to `36 / 50` and raised
the successful hold-lift mean.

Force feedback remains useful as observation, gate, and label signal. It did
not need to directly alter the controller in this pass, but the active-pair
tension metrics increased with the improved lift-timing candidate.

## Artifacts

Selected candidate:

- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_gxm0008_ls480_selected_v0.json`

Reports:

- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_refine_gxm0008_local_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_50_gxm0006_local_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_50_gxm0008_ls480_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_refine_gxm0008_ls480_selected_v0_report.md`

Metadata:

- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_gxm0008_local_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_gxm0008_local_selected_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_50_gxm0006_local_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_50_gxm0008_ls480_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_gxm0008_ls480_selected_run_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_gxm0008_ls480_selected_v0.json`

## Next

1. Treat `gx -0.0008 + lift_steps=480` as the current best diagnostic search
   center, not a robust baseline.
2. Run the next robustness-aware search around lift timing:
   - `lift_steps = 440, 460, 480, 500`
   - optionally `lift_j2 = -0.95, -0.93, -0.91`
   - keep original hand geometry unless a candidate survives randomized checks.
3. Add close-up/multiview visual evidence for the new selected candidate.
4. Use force-feedback pair tension/balance as labels for lift-failure taxonomy
   and later residual micro-adjust design.
5. Do not promote until robustness and visual clarity both improve.
