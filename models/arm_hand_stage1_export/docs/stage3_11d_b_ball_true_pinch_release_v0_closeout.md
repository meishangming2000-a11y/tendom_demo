# Stage3.11D-B Ball True-Pinch Release Closeout v0

Generated: `2026-06-11`

## Boundary

- MuJoCo-only.
- Parameter/action-phase search, not neural-network training.
- No hardware, real camera, tactile hardware, ultrasound, or full-action ACT/DP promotion.
- This is a provisional small-ball demo candidate, not a robust released baseline.

## What Changed

Stage3.11D-A showed that the egg demo really lifts the object, but the visible
grasp is a three-finger/palm enclosure rather than a clean two-finger pinch.
Stage3.11D-B switches the diagnostic object to a small ball and separates three
gates:

1. lift gate,
2. true two-tip pinch morphology gate,
3. release gate.

The new search script is:

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_11d_b_ball_true_pinch_release_candidates_v0.py
```

## Best Current Candidate

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_11d_b_ball_true_pinch_release_candidates_v0.py --max-candidates 108 --ball-radius 0.018 --ball-mass 0.010 --tip-pair-separation-target 0.060 --tip-mu 2.8 --ball-mu 1.35 --non-tip-mu 0.10 --lift-j2 -0.95 --lift-steps 520 --hold-steps 100 --morphology-sample-every 5 --no-render-best
```

Result:

- Full true-pinch-release success: `1 / 108`
- Lift gate success: `1 / 108`
- True-pinch morphology gate success: `1 / 108`
- Release gate success: `108 / 108`
- Best candidate: `thumb_middle_tip_mu2p8_abdm0p45_pipm0p70_tabdm0p35_tmcpp0p28`
- Object: ball radius `0.018 m`, mass `0.010 kg`
- Hold lift max: `0.1610 m`
- Hold true two-tip fraction: `0.900`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`

Primary report and metadata:

- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_ball_true_pinch_release_candidates_v0_report.md`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_ball_true_pinch_release_candidates_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_ball_true_pinch_release_selected_v0.json`

## Visual Review

Multiview visual check:

- `simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_11d_b_ball_true_pinch_release_v0/multiview_hold100_thumb_middle_pass/front_default_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_11d_b_ball_true_pinch_release_v0/multiview_hold100_thumb_middle_pass/thumb_side_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_11d_b_ball_true_pinch_release_v0/multiview_hold100_thumb_middle_pass/finger_side_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/visual_checks_stage3_11d_b_ball_true_pinch_release_v0/multiview_hold100_thumb_middle_pass/higher_oblique_contact_sheet.png`

Visual conclusion:

- The candidate does lift the small ball and releases it cleanly.
- The contact morphology is no longer the egg demo's three-finger/palm enclosure.
- The visible contact is still not presentation-ready: the ball sits close to the
  middle-finger side, and the clean two-tip relation is clearer from side views
  than from the default camera.
- The success region is narrow: only `1 / 108` candidates pass in the current
  broad grid.

## Friction Diagnosis

The current evidence does not support "just increase friction" as the answer.
High-friction sweeps did not produce a stable true-pinch demo on the larger
ball. The first full gate pass appeared after changing object scale, hold
duration, and phase timing around a thumb-middle contact window.

Friction remains a first-class design parameter, but the immediate blocker is
contact geometry plus phase timing:

- establish true two-tip contact before lifting,
- lift slowly while that contact is still active,
- hold only inside the stable contact window,
- then release cleanly.

## Event-Gated Expansion

Completed on `2026-06-11`.

The next expansion implemented the planned event-driven controller:

```powershell
python .\simulations\models\arm_hand_stage1_export\train_stage3_11d_b_event_contact_gated_refine_v0.py
```

It waits for true thumb+middle tip contact before lift, lifts until the
two-tip lifted window is met, holds inside the stable window, and then releases.
This is still parameter/action-phase search, not neural-network training.

Low-lift local refinement:

- Cases evaluated: `40`
- Full event true-pinch-release success: `27 / 40`
- Best hold lift max: `0.0643 m`
- Hold true two-tip fraction: `1.000`
- Hold wrap fraction: `0.000`
- Release success: `True`

High-lift refinement:

- Cases evaluated: `30`
- Full event true-pinch-release success: `18 / 30`
- Contact-gate success: `20 / 30`
- Lift gate success: `18 / 30`
- True-pinch morphology success: `18 / 30`
- Release success: `20 / 30`
- Best candidate: `event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100`
- Hold lift max: `0.11381 m`
- Hold lift mean: `0.11131 m`
- Hold true two-tip fraction: `1.000`
- Hold wrap fraction: `0.000`
- Hold non-tip ratio: `0.000`
- Release success: `True`

High-lift report and metadata:

- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_refine_highlift_v0_report.md`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_highlift_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_highlift_selected_v0.json`

High-lift visual evidence:

- `simulations/models/arm_hand_stage1_export/docs/v11db_highlift_vis/event_thumb_middle_tabdm0p350_tmcpp0p280_aabdm0p500_apipm0p700_sep0p060_gzp0p002_lj2m0p950_ls520_hs100_ml0p100_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/v11db_highlift_vis/multiview_best/front_default_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/v11db_highlift_vis/multiview_best/thumb_side_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/v11db_highlift_vis/multiview_best/finger_side_contact_sheet.png`
- `simulations/models/arm_hand_stage1_export/docs/v11db_highlift_vis/multiview_best/higher_oblique_contact_sheet.png`

Visual conclusion:

- The high-lift candidate clearly lifts the ball off the floor and releases it
  back to the floor.
- The side views, especially `finger_side_contact_sheet.png`, are the clearest
  evidence for the current two-tip lift/hold/release sequence.
- The default view is still partially occluded by the hand, and the ball remains
  close to the middle-finger side. It is a much better demo candidate than the
  broad-grid result, but still not polished enough for gallery promotion.

## Randomized Robustness And Motor Feedback Simulation

Completed on `2026-06-11`.

New robustness runner:

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_11d_b_event_contact_gated_robustness_v0.py --trials 24
```

It perturbs object pose, grasp target, radius, mass, and friction around the
selected high-lift event-gated case. It also enables simulated motor force
feedback by default.

Result:

- Full event true-pinch-release success: `13 / 24`
- Contact-gate success: `24 / 24`
- Lift gate success: `13 / 24`
- True-pinch morphology success: `13 / 24`
- Release success: `24 / 24`
- Terminal reasons: `{'lift_gate_failed': 11, 'success_event_contact_gated_true_pinch_release_ball': 13}`
- Successful hold lift mean/min/max: `0.11276 / 0.11135 / 0.11434 m`

Motor force-feedback simulation:

- New sensor module:
  `simulations/models/arm_hand_stage1_export/external_sensors/mujoco_motor_force_feedback_sensor.py`
- Force-feedback research note:
  `simulations/models/arm_hand_stage1_export/docs/stage3_11d_motor_force_feedback_simulation_v0.md`
- Max simulated global `|Iq|`: `3.0775 A`
- Max simulated global tendon-tension proxy: `287.1294 N`
- Max simulated hand-side `|Iq|`: `0.2097 A`
- Max simulated hand-side tendon-tension proxy: `19.3552 N`
- Current saturation trial fraction: `0.000`

Interpretation:

- The selected candidate is not robust enough for gallery promotion: randomized
  success is only `13 / 24`.
- The contact event itself is robust in this probe: `24 / 24` reached contact.
- The failure cluster is lift-window stability, not release.
- Global force feedback is dominated by arm joint load; future grasp control
  must use hand/finger-side force-feedback metrics.
- Phase-wise hand-side tension suggests the useful control signal is sustained
  slow-lift/hold tension, not just contact-gate tension. Slow-lift mean
  hand-side tension was higher in successful trials than failures.

## Next Plan

1. Treat the event-gated high-lift result as the current Stage3.11D-B diagnostic
   demo candidate, but not a robust baseline.
2. Add a force-feedback lift permission / lift-continuation gate using
   hand-side current/tension proxies during slow lift.
3. Add a gentle preload or micro-adjust phase when contact exists but slow-lift
   hand-side tension drops.
4. Add a clearer close-up demo camera for human review before any gallery
   promotion.
5. If robustness or visual cleanliness remains weak, branch into fingertip proxy
   geometry and material/contact modeling before neural policy training.
6. Only after robustness and visual review pass should this feed Stage3.11E
   constrained residual/full-action experiments.

## Organization Pass

Completed on `2026-06-11`.

Updated source-of-truth routing:

- `docs/project_quick_entrypoints.md`
- `docs/agentic_project_index.md`
- `docs/visual_evidence_index.md`
- `docs/project_progress_mindmap.json`
- `simulations/models/arm_hand_stage1_export/docs/stage3_progress_mindmap.json`
- `docs/nervous_system/root_project.json`
- `docs/nervous_system/lanes/simulation_stage3.json`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_refine_highlift_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_event_contact_gated_robustness_v0_report.md`
- `simulations/models/arm_hand_stage1_export/docs/stage3_11d_motor_force_feedback_simulation_v0.md`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_highlift_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_robustness_v0.json`
- `simulations/models/arm_hand_stage1_export/metadata/stage3_11d_b_event_contact_gated_refine_highlift_selected_v0.json`

Classification:

- Search script, report, closeout, and metadata are `official` Stage3.11D-B
  diagnostic artifacts.
- Event-gated refinement script, high-lift report, high-lift metadata, and
  selected high-lift config are `official` Stage3.11D-B diagnostic artifacts.
- Robustness runner, robustness report, force-feedback sensor module, and
  force-feedback simulation note are `official` Stage3.11D-B diagnostic
  artifacts.
- Visual folders are `closeout_backed` evidence.
- No demo-gallery promotion yet.
- No files were moved, deleted, or archived in this pass, so no cleanup move
  manifest was required.

Checks:

```powershell
python -m py_compile .\simulations\models\arm_hand_stage1_export\external_sensors\mujoco_motor_force_feedback_sensor.py
python -m py_compile .\simulations\models\arm_hand_stage1_export\train_stage3_11d_b_event_contact_gated_refine_v0.py
python -m py_compile .\simulations\models\arm_hand_stage1_export\run_stage3_11d_b_event_contact_gated_robustness_v0.py
python .\project_progress_mindmap_viewer.py --check
python .\simulations\models\arm_hand_stage1_export\stage3_progress_mindmap_viewer.py --check
python .\tools\check_project_nervous_system.py --tier light
```

All checks passed.
