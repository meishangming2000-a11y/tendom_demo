# Stage3.11D-B Pinch Demo Visual Review v0

Generated from the current Stage3.8B pinch viewer path:

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_pinch_grasp_viewer.py --candidate-config .\simulations\models\arm_hand_stage1_export\metadata\stage3_pinch_grasp_training_v0_selected.json
```

## Boundary

- MuJoCo-only visual review.
- No controller change.
- No hardware, real camera, tactile hardware, ultrasound, or full-action ACT/DP promotion.

## Visual Evidence

Rendered frames and contact sheet:

```text
simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_11d_pinch_demo_visual_review_v0/pinch_demo_visual_review_contact_sheet.png
simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_11d_pinch_demo_visual_review_v0/visual_review_summary.json
```

## Answer: Did It Lift?

Yes. The egg is visually and numerically lifted in the current demo.

Key final-hold metrics:

| metric | value |
|---|---:|
| candidate | `thumb_index_middle_strong__higher_approach` |
| active fingers | `thumb,index,middle` |
| final true lift | `0.101382 m` |
| success lift threshold | `0.050000 m` |
| final floor contacts | `0` |
| observed hold stable fraction | `1.000` |
| observed hold pinch fraction | `1.000` |
| observed hold purity mean | `0.790910` |

## Main Visual Problems

1. The motion is a successful lift, but not a clean fingertip pinch.
   - The final hold is supported by `middle,palm,thumb`, with the egg sitting near the palm-side pocket.
   - Final frame morphology: `tip_contact_ratio=0.25`, `non_tip_contact_ratio=0.75`, `wrap=True`, `two_finger_tip_pinch=False`.

2. The close phase pushes the egg through a support-contact moment before lift.
   - At `pinch_close_end`: `lift=-0.0026 m`, `floor_contacts=1`, regions `index,middle,palm,support,thumb`.
   - The demo recovers and lifts afterward, but the approach/close trajectory is not clean.

3. The current success gate over-rewards stable lifting and under-specifies grasp shape.
   - Current active fingers are `thumb,index,middle`, so a three-digit clamp is expected by design.
   - The success gate accepts `thumb + active finger` contact and lift, but does not require fingertip-to-fingertip opposition.
   - `pinch purity` can remain high even when palm/non-tip contacts dominate, because desired regions include both index and middle.

4. The friction/material model is not the sole cause.
   - The Stage3.11D-A friction audit kept success across friction settings while wrap/non-tip morphology persisted.
   - Material design still matters, but the immediate blocker is objective/gate/controller morphology.

## Next Plan

### Stage3.11D-B1: Add a True-Pinch Visual/Morphology Gate

Create a diagnostic gate that separates:

- `lift_success`: egg is off the table and stable.
- `true_pinch_success`: lift succeeds with fingertip-dominant opposition and limited non-tip/palm support.

Initial proposed criteria:

| metric | first target |
|---|---:|
| final true lift | `>= 0.050 m` |
| final floor contacts | `0` |
| hold stable fraction | `>= 0.90` |
| two-finger fingertip pinch fraction | `>= 0.50` |
| wrap frame fraction | `<= 0.30` |
| non-tip contact ratio | `<= 0.45` |
| support/palm contact in hold | reject or heavy penalty |

### Stage3.11D-B2: Run Morphology Ablations Before Training

Before training a residual policy, run a small MuJoCo parameter search with the new gate:

- `thumb + index only`
- `thumb + index + middle` with middle as light stabilizer only
- reduced palm/wrist support acceptance
- approach height and lateral offset variants
- close timing variants that avoid support contact during `pinch_close`

Promotion rule: do not promote a candidate just because it lifts. It must improve morphology without relaxing slip/crush/penetration/final-vision safety gates.

### Stage3.11D-B3: Only Then Train Morphology-Conditioned Residuals

If B2 finds any morphology-improving candidate:

- export dense obs/action/contact/morphology labels,
- train a hand/residual policy conditioned on safety plus morphology labels,
- evaluate against two ablations:
  - safety conditioning only,
  - morphology conditioning only.

If B2 cannot find a candidate:

- treat the current hand proxy geometry/contact surfaces as a limiting factor,
- design a Stage3 material/geometry branch before spending more training effort.

## Next Success And Failure Branch

If successful:

Promote a `true_pinch_candidate_v0` only after it passes both lift and morphology gates on fixed plus randomized pose trials.

If failed:

Keep the current demo as `lift_by_three_digit_enclosure`, not as a true pinch baseline, and shift the next work to contact geometry/material design plus approach/close trajectory redesign.
