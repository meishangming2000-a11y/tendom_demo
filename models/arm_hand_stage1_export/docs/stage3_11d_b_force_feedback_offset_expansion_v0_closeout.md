# Stage3.11D-B Force Feedback And Offset Expansion v0 Closeout

Generated: `2026-06-11`

## Boundary

- MuJoCo-only Stage3 diagnostic work.
- No real motor, real encoder, real tactile, ultrasound, camera, or hardware runtime integration.
- Not a demo-gallery promotion and not a robust baseline promotion.
- Not full-action ACT/DP closed-loop success.

## What Changed

1. Extended the simulated motor force-feedback proxy from global/hand totals to
   thumb + active-finger pair summaries:
   - per-finger group tension, current, torque, saturation, and top actuator
   - active-pair total tendon-tension proxy
   - active-pair balance ratio
   - active-pair max `Iq` and saturation count
   - per-phase pair summaries for contact, preload, slow-lift, hold, release

2. Added force-feedback lift/hold gate plumbing to the event-gated runner:
   - v0 preload mode can increase thumb + active-finger closure.
   - v0b conservative mode pauses slow-lift progress when pair force is below
     threshold, without changing grasp geometry by default.
   - preload is now opt-in via `--force-feedback-enable-preload`.

3. Added robustness runner base-offset probes:
   - `--base-grasp-offset-x-delta`
   - `--base-grasp-offset-y-delta`
   - `--base-grasp-offset-z-delta`
   - `--base-ball-offset-x-delta`
   - `--base-ball-offset-y-delta`

## Key Results

| Probe | Result | Main failure pattern | Note |
| --- | ---: | --- | --- |
| 24-trial baseline | `13 / 24` | `11` lift failures | Existing reference. |
| 24-trial force-gate v0 with preload | `9 / 24` | `13` lift failures, `2` true-pinch morphology failures | Raised pair tension but harmed geometry. Do not use by default. |
| 24-trial force-gate v0b wait-only | `13 / 24` | `11` lift failures | No regression, but no rescue; force signal is diagnostic/label quality first. |
| 24-trial `gx -0.0004 m` | `15 / 24` | `8` lift failures, `1` morphology failure | Better than baseline. |
| 24-trial `gx -0.0008 m` | `16 / 24` | `5` lift failures, `2` contact failures, `1` morphology failure | Best 24-trial probe. |
| 24-trial `gx -0.0012 m` | `15 / 24` | `5` lift failures, `4` contact failures | Overshoots contact window. |
| 50-trial baseline | `29 / 50` | `20` lift failures, `1` contact failure | 50-trial reference. |
| 50-trial `gx -0.0008 m` | `34 / 50` | `12` lift failures, `3` contact failures, `1` morphology failure | Best verified expansion point. |

Best 50-trial offset result:

- Success: `34 / 50`
- Contact gate: `47 / 50`
- Lift gate: `35 / 50`
- True-pinch gate: `34 / 50`
- Release: `49 / 50`
- Success hold-lift mean: `0.11279 m`
- Mean slow-lift active-pair tension proxy: `7.2922 N`
- Mean hold active-pair tension proxy: `4.0126 N`
- Saturation trial fraction: `0.000`

## Interpretation

The first force-feedback preload controller was too aggressive. It increased
the thumb + active-finger tension proxy, but it disturbed the two-tip geometry
and reduced success from `13 / 24` to `9 / 24`.

The conservative wait-only gate avoided regression but did not rescue the lift
failures. The low-force wait counter showed that many failures are not brief
force dips; the grasp geometry is already outside the stable two-tip lift
window.

The useful improvement in this round came from base grasp geometry. A small
negative x shift, `--base-grasp-offset-x-delta -0.0008`, moved more randomized
cases into the stable lift window: `29 / 50` -> `34 / 50`. It also introduced
a small contact-gate cost: `1` -> `3` contact failures.

Therefore, force feedback is now validated as:

- an observation surface,
- a lift/hold quality gate,
- a failure-labeling signal,
- and a future residual-controller input.

It is not yet validated as a direct "close harder" controller.

## Artifacts

Reports:

- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_pair_baseline_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_forcegate_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_gxm0004_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_gxm0008_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_gxm0012_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_gxm0008_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_50_baseline_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_50_gxm0008_v0_report.md`

Metadata:

- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_pair_baseline_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_forcegate_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_gxm0004_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_gxm0008_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_forcegate_wait_gxm0012_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_gxm0008_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_50_baseline_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_50_gxm0008_v0.json`

## Next Plan

1. Promote `gx -0.0008 m` only as the next search center, not as a final
   baseline.
2. Run a local refine around:
   - `grasp_offset_x` near `-0.0006 .. -0.0010`
   - `grasp_offset_z`
   - `tip_pair_separation_target`
   - thumb CMC abduction / thumb MCP
   - active MCP abduction / active PIP
3. Keep force feedback in the observation vector and success gates:
   - active-pair hold tension proxy
   - active-pair tension balance
   - hand-side saturation and current limit margin
4. Add a residual-style correction action later:
   use force feedback to choose small pose/closure corrections rather than
   blindly increasing preload.
5. Repeat 50-trial robustness and close-up visual review before any demo
   promotion.
