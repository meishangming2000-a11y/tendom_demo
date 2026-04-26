# Project Stage Report

Date: 2026-03-14

Project: Tendon Project Simulations

Scope: Shadow Hand static grasping and catch-and-hold behavior cloning pipeline

Update note (2026-03-20):

- This is a stage report for the earlier static-grasp and catch-centered phase.
- It remains useful as historical evidence, but it is not the current project baseline.
- The current maintained learning loop is `pre_grasp expert -> dataset -> BC -> eval -> report`.

## 1. Original Goal

The project started with a clear practical goal:

Build a complete grasp-learning pipeline around the Shadow Hand in MuJoCo, so that we can:

1. Run an expert controller to generate grasp demonstrations.
2. Convert those demonstrations into a behavior-cloning dataset.
3. Train a policy from the dataset.
4. Evaluate the trained policy under a meaningful success rule.
5. Present a demo that shows both the expert behavior and the learned behavior.

In short, the intended full chain was:

`expert controller -> data collection -> BC training -> BC evaluation -> demo showcase`

## 2. Main Problems Found Along The Way

Early in the review, several issues made the original results look better than they really were.

### 2.1 Success Definition Was Too Loose

The project originally counted a grasp as successful if the object simply stayed in contact with the palm or any finger for long enough. That allowed false positives such as:

- the ball being squeezed out through the fingers,
- the ball landing on the palm,
- the hand appearing to “hold” the object without a true enclosure grasp.

This meant some visually misleading trajectories were being marked as success.

### 2.2 Catch Task Was Not Evaluating A Real Falling Catch

For the catch task, the object’s falling speed was set during environment reset, but the object-placement helper later zeroed that velocity out. As a result, the object was often no longer truly falling when the episode began. This invalidated earlier catch claims.

### 2.3 Script Layout Had Become Hard To Maintain

The `scripts/` folder had accumulated too many mixed-purpose files. Entry points, utilities, diagnostics, and shared helpers were all placed together, which made the workflow harder to understand and maintain.

### 2.4 Expert Data Had A “Late-Phase Drift” Problem

Even after tightening the success rule, the expert controller often reached a good grasp and then later drifted or relaxed. That meant the dataset could contain useful grasping behavior mixed with less useful late-stage motion, which is harmful for BC.

## 3. What We Changed

### 3.1 Tightened The Success Rule

The static task success rule is now:

`palm_and_thumb_plus_3_finger_groups_contact_for_50_steps`

The catch task success rule is now:

`palm_and_thumb_plus_3_finger_groups_contact_for_50_steps_and_object_not_on_floor`

This is a much stricter and more physically meaningful definition than palm-only support.

### 3.2 Fixed The Catch Placement Physics Bug

The catch placement helper now preserves the object’s falling velocity after reset, so catch episodes actually begin as falling-object episodes.

### 3.3 Reorganized The Script Tree

The project layout is now categorized:

- `scripts/`: runnable entrypoints
- `scripts/common/`: shared helpers
- `scripts/data_tools/`: dataset utilities
- `scripts/diagnostics/`: validation and report checks

This makes the workflow easier to explain and easier to extend.

### 3.4 Improved Expert Data Collection

We changed collection in two important ways:

1. Early-stop collection after a stable grasp target is reached.
2. Add a dedicated static expert collection timing profile so the controller can reach a real `hold` phase within a 400-step episode.

This made the collected data better aligned with the target behavior that BC should imitate.

### 3.5 Added A Persistent Hold Phase To The Expert Controller

The enhanced controller can now transition from:

`approach -> close_fingers -> lift -> hold`

instead of effectively ending before a meaningful hold phase is recorded.

### 3.6 Updated The BC Workflow

The current recommended static BC workflow now uses:

- cleaned expert data,
- success-only filtering,
- an extra normalized phase feature,
- a finger-action ramp during inference.

These changes do not “solve” grasping, but they make the learned behavior more stable and closer to the expert timing.

## 4. Current End-To-End Status

At this stage, the static-grasp pipeline is fully runnable end to end.

### 4.1 Expert Demo

We have a working expert-controller demo:

- entrypoint: `python scripts/demo_grasp.py`

This demonstrates the hand-crafted controller behavior directly.

### 4.2 Data Collection

We have a working expert data collection pipeline:

- dataset: `data/expert_showcase_v5_50x400.npz`
- report: `reports/expert_showcase_v5_50x400.json`

### 4.3 BC Training

We have a trained static BC model:

- model: `models/bc_showcase_v5_success400_phase_h128_80ep.pth`

### 4.4 BC Evaluation

We have a formal evaluation report for the trained model:

- report: `reports/bc_showcase_v5_success400_demo_20_ramp160.json`

### 4.5 BC Demo

We have a working learned-policy showcase demo:

- entrypoint: `python scripts/demo_bc.py`

This demo now defaults to the v5 static model above.

## 5. Quantitative Results

### 5.1 Expert Data Quality

Current recommended static expert dataset:

- dataset: `data/expert_showcase_v5_50x400.npz`
- stable-grasp success: `47/50` = `94.0%`
- terminal success: `25/50` = `50.0%`
- average first success step: `296.4`

Interpretation:

- Most episodes do reach a valid stable grasp under the strict rule.
- About half of the episodes still remain successful all the way to the end.
- This is better aligned with BC than earlier versions that captured too much late drift.

### 5.2 BC Evaluation

Current recommended static BC model:

- model: `models/bc_showcase_v5_success400_phase_h128_80ep.pth`
- evaluation: `reports/bc_showcase_v5_success400_demo_20_ramp160.json`
- success rate: `10/20` = `50.0%`

Additional references:

- ramp sweep: `reports/sweep_v5_ramp160_s025.json` gave `6/10`
- no-ramp reference: `reports/bc_showcase_v5_success400_demo_10_no_ramp.json` gave `0/10`

Interpretation:

- The learned policy is now demonstrably functional.
- Inference-time pacing still matters a lot.
- The model can perform valid strict-rule grasps, but robustness is still limited.

### 5.3 Catch Task Status

What is completed:

- catch placement velocity bug fixed
- catch validation script confirms falling velocity is preserved

What is not completed:

- a fresh catch retrain and updated catch baseline under the corrected physics

So the catch pipeline is technically repaired at the environment/collection level, but not yet refreshed as a final learning result.

## 6. What This Project Has Proven

At the current stage, the project has successfully proven the following:

### 6.1 The Core Learning Pipeline Works

We have demonstrated that the full static pipeline can run from expert control to trained BC policy and produce a valid demo.

This is the most important project-level milestone, because it confirms the pipeline is real and not just a collection of disconnected scripts.

### 6.2 Success Metrics Matter Enormously

A major contribution of this work is showing that an apparently strong result can collapse once the success rule is made physically meaningful.

This is valuable because it prevents us from over-claiming performance and gives the project a more credible evaluation standard.

### 6.3 Better Expert Timing Produces Better Learning Targets

By pushing the expert controller into a real hold phase and collecting around that phase, we improved dataset quality and reached a more trustworthy learned-policy demo.

### 6.4 The Static Demo Is Ready For Presentation

We now have two presentable demos:

- expert controller demo
- learned BC policy demo

That means the project has reached a usable demonstration stage.

## 7. Strengths Of The Current Project

### 7.1 The Pipeline Is End To End

This is no longer a partial prototype. The static workflow is connected from controller to demo.

### 7.2 Evaluation Is More Honest

The stricter success rule avoids the biggest false positives, especially palm-only support.

### 7.3 The Codebase Is More Organized

The script layout is much clearer than before, which lowers maintenance cost and makes the project easier to present.

### 7.4 The Demo Is Real

The current BC demo is not a placeholder. It runs from a trained checkpoint and succeeds under the stricter grasp definition.

### 7.5 There Is Clear Experimental Traceability

The project now includes datasets, reports, sweeps, diagnostics, and documented current defaults. This makes the stage result much easier to defend in a report or presentation.

## 8. Current Weaknesses And Limitations

### 8.1 BC Robustness Is Still Moderate

`10/20` under the recommended static evaluation is enough to demonstrate capability, but not enough to claim robust deployment-quality grasping.

### 8.2 The Policy Still Depends On Inference Pacing

Without the finger ramp, the v5 model fails badly. This means the learned policy still benefits from a hand-crafted timing assist.

### 8.3 Expert Quality Is Better But Not Yet Ideal

The dataset is much improved, but terminal success is only `25/50`, which means the expert itself is still not consistently perfect.

### 8.4 Scene Generalization Is Not Solved

The project currently demonstrates a strong static showcase workflow in `demo` placement conditions. Generalization to more varied placements or scenes is still a major open problem.

### 8.5 Catch Learning Is Not Fully Revalidated

The catch environment logic is corrected, but the final catch BC story still needs a fresh retrain and reevaluation before it can be presented with confidence.

## 9. Where We Are In The Overall Project

The best way to describe the current project stage is:

`pipeline validation and showcase stage`

We are beyond the “basic prototype” stage because:

- the static chain is complete,
- the demos are runnable,
- the metrics are meaningful,
- the code structure is usable.

We are not yet at the “strong benchmark / generalized policy” stage because:

- robustness is limited,
- inference still needs a ramp,
- catch learning is not fully refreshed,
- broader scene generalization remains weak.

So, in project terms, we are at:

1. Problem formulation: completed
2. Core environment and controller setup: completed
3. Expert data pipeline: completed
4. Static BC training and evaluation loop: completed
5. Demo-ready static showcase: completed
6. Robust generalization and mature benchmark phase: not yet completed

## 10. Recommended Presentation Framing

For a report or oral presentation, the safest and strongest framing is:

This project successfully built and validated a full static grasp-learning pipeline for the Shadow Hand. We corrected misleading evaluation criteria, repaired a key catch-task physics bug, reorganized the codebase, improved expert data quality, and produced both an expert-controller demo and a trained-policy demo. The system now demonstrates real end-to-end learning capability under a stricter success rule, while still leaving robustness, scene generalization, and refreshed catch-task learning as the next major steps.

## 11. Key Demo And Evidence Files

Primary demo entrypoints:

- `scripts/demo_grasp.py`
- `scripts/demo_bc.py`

Primary current static artifacts:

- `data/expert_showcase_v5_50x400.npz`
- `reports/expert_showcase_v5_50x400.json`
- `models/bc_showcase_v5_success400_phase_h128_80ep.pth`
- `reports/bc_showcase_v5_success400_demo_20_ramp160.json`
- `reports/sweep_v5_ramp160_s025.json`
- `reports/bc_showcase_v5_success400_demo_10_no_ramp.json`

Supporting project references:

- `README.md`
- `scripts/README.md`
- `scripts/diagnostics/test_catch_task.py`

## 12. Suggested Next Steps

The next strongest project steps would be:

1. Improve static robustness beyond the current `10/20` level.
2. Reduce or remove dependence on inference-time finger ramping.
3. Retrain the catch pipeline under the corrected falling-object physics.
4. Move from `demo` placement toward broader scene generalization.
5. If needed, evolve from pure BC toward richer policy representations or hybrid training.
