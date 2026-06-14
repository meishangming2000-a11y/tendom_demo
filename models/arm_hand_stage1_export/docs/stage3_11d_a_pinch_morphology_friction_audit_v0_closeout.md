# Stage3.11D-A Pinch Morphology Friction Audit v0

Generated: `2026-06-11T01:31:45`

Status: **diagnostic PASS** if the script ran and produced morphology labels. This does not promote a new controller.

## Purpose

The current Stage3.8B pinch demo can look like a three-finger clamp or enclosure. This audit measures that morphology under an egg-friction sweep before Stage3.11D trains any safety-conditioned hand/residual policy.

## Boundary

- MuJoCo-only.
- No real camera, tactile hardware, ultrasound, or hardware runtime.
- No full-action ACT/DP promotion.
- The current controller is not changed.

## Summary

- Episodes: `8`
- Success: `8 / 8`
- Terminal reasons: `{'success_vision_confirmed_pinch_lift_hold': 8}`
- Risk flags: `{'early_contact_in_approach': 8, 'transient_slip_high': 8, 'pinch_morphology_wrap_or_enclosure': 8, 'low_true_two_finger_tip_pinch': 8, 'non_tip_contact_dominates': 8, 'three_digit_clamp_dominates': 6}`

## Friction Sweep

| friction case | success | lift mean | hold slip max | two-finger tip pinch | three-digit clamp | wrap frames | tip contact | non-tip contact | wrap score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| egg_only_egg_mu_0.45 | 1/1 | 0.10190 | 0.198 | 0.000 | 0.226 | 1.000 | 0.229 | 0.771 | 0.558 |
| egg_only_egg_mu_0.75 | 1/1 | 0.10190 | 0.198 | 0.000 | 0.226 | 1.000 | 0.229 | 0.771 | 0.558 |
| egg_only_egg_mu_1.15 | 1/1 | 0.10138 | 0.185 | 0.000 | 0.540 | 1.000 | 0.224 | 0.776 | 0.596 |
| egg_only_egg_mu_1.60 | 1/1 | 0.09996 | 0.195 | 0.000 | 1.000 | 1.000 | 0.261 | 0.739 | 0.658 |
| matched_hand_egg_mu_0.45 | 1/1 | 0.09996 | 0.191 | 0.000 | 1.000 | 1.000 | 0.286 | 0.714 | 0.690 |
| matched_hand_egg_mu_0.75 | 1/1 | 0.09891 | 0.228 | 0.000 | 0.918 | 1.000 | 0.373 | 0.627 | 0.604 |
| matched_hand_egg_mu_1.15 | 1/1 | 0.10117 | 0.183 | 0.000 | 0.533 | 1.000 | 0.226 | 0.774 | 0.594 |
| matched_hand_egg_mu_1.60 | 1/1 | 0.09996 | 0.195 | 0.000 | 1.000 | 1.000 | 0.261 | 0.739 | 0.658 |

## Interpretation

- If three-digit clamp and wrap frames remain high across friction cases, morphology is mainly a controller/objective issue, not only an egg-surface friction issue.
- If success or slip changes sharply with egg friction, the material model should become a first-class Stage3.11D/Stage4 design variable.
- A future true-pinch gate should require a higher two-finger fingertip-pinch fraction and penalize non-tip/palm/support contacts instead of only checking lift and low hold slip.

## Episode Details

| ep | friction | status | lift | hold slip | two-finger tip | three-digit clamp | wrap frames | regions | risks |
|---:|---|---|---:|---:|---:|---:|---:|---|---|
| 0 | egg_only_egg_mu_0.45 | PASS | 0.10190 | 0.198 | 0.000 | 0.226 | 1.000 | `{'index': 203, 'middle': 900, 'palm': 900, 'thumb': 900, 'ring': 186}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'non_tip_contact_dominates']` |
| 1 | egg_only_egg_mu_0.75 | PASS | 0.10190 | 0.198 | 0.000 | 0.226 | 1.000 | `{'index': 203, 'middle': 900, 'palm': 900, 'thumb': 900, 'ring': 186}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'non_tip_contact_dominates']` |
| 2 | egg_only_egg_mu_1.15 | PASS | 0.10138 | 0.185 | 0.000 | 0.540 | 1.000 | `{'index': 486, 'middle': 900, 'palm': 900, 'thumb': 900}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'three_digit_clamp_dominates', 'non_tip_contact_dominates']` |
| 3 | egg_only_egg_mu_1.60 | PASS | 0.09996 | 0.195 | 0.000 | 1.000 | 1.000 | `{'index': 900, 'middle': 900, 'palm': 900, 'thumb': 900}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'three_digit_clamp_dominates', 'non_tip_contact_dominates']` |
| 4 | matched_hand_egg_mu_0.45 | PASS | 0.09996 | 0.191 | 0.000 | 1.000 | 1.000 | `{'index': 900, 'middle': 900, 'palm': 900, 'thumb': 900}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'three_digit_clamp_dominates', 'non_tip_contact_dominates']` |
| 5 | matched_hand_egg_mu_0.75 | PASS | 0.09891 | 0.228 | 0.000 | 0.918 | 1.000 | `{'index': 826, 'middle': 900, 'palm': 900, 'thumb': 900}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'three_digit_clamp_dominates', 'non_tip_contact_dominates']` |
| 6 | matched_hand_egg_mu_1.15 | PASS | 0.10117 | 0.183 | 0.000 | 0.533 | 1.000 | `{'index': 480, 'middle': 900, 'palm': 900, 'thumb': 900}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'three_digit_clamp_dominates', 'non_tip_contact_dominates']` |
| 7 | matched_hand_egg_mu_1.60 | PASS | 0.09996 | 0.195 | 0.000 | 1.000 | 1.000 | `{'index': 900, 'middle': 900, 'palm': 900, 'thumb': 900}` | `['early_contact_in_approach', 'transient_slip_high', 'pinch_morphology_wrap_or_enclosure', 'low_true_two_finger_tip_pinch', 'three_digit_clamp_dominates', 'non_tip_contact_dominates']` |

## Next

Stage3.11D should add morphology-conditioned residual/policy work only after this diagnostic is reviewed. If dense obs/action labels are needed for morphology conditioning, do Stage3.11C2-style dense capture rather than pretending trace-frame labels are dense policy data.
