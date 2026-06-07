# Stage2 Pick-Place Sim-to-Real Strategy

Generated: 2026-06-02

## Purpose

The 50cm pick-place work is not valuable because the final product needs to move one ball exactly 50cm.  It is valuable because it is the first full manipulation task that stresses the whole stack:

- grasp
- lift
- long transport
- target approach
- release
- stable placement
- dataset QA
- BC training
- online evaluation
- visual demo
- failure diagnosis

The real project goal is to build a repeatable manipulation workflow that can move from simulation toward hardware without pretending that a single neural policy is ready for direct real-world deployment.

## Current Strategic Lesson

The v0.7.1 and v0.7.2 results show:

- Expert/scripted trajectories can complete fixed 50cm pick-place targets.
- Replay-clean datasets are necessary but not sufficient.
- Low offline BC loss is not enough; online MuJoCo rollout is the gate.
- Fully live-observation BC is unstable during early grasp/lift because small deviations can push the ball out of the demonstration manifold.
- Phase-gated/static-target control is currently much more stable than one monolithic observation-conditioned policy.

The project should therefore avoid drifting into endless "collect more data, train one more MLP" loops.

## What 50cm Pick-Place Gives Sim-to-Real

It gives these sim-to-real assets:

1. **Mechanical feasibility evidence**
   - The arm-hand geometry and workspace can complete grasp, carry, and place in simulation.

2. **Failure-mode inventory**
   - Early ball push/roll.
   - Transport drop.
   - Release contact remaining.
   - Placement miss.
   - Observation-conditioned closed-loop drift.

3. **Evaluation gates**
   - Replay QA.
   - Fixed target success rate.
   - Narrow target sweep.
   - Transport floor contact count.
   - Final hand contact count.
   - Final placement error.
   - Rendered demo only after numeric PASS.

4. **Hardware architecture guidance**
   - Use a staged controller, not end-to-end policy control from the beginning.
   - Keep approach/grasp/lift conservative and phase-gated.
   - Use learned modules or residuals only where they improve transport, descent, release, or recovery.

5. **Tactile/slip task context**
   - Detect secure grasp.
   - Detect slip during lift/transport.
   - Detect contact during release.
   - Decide whether to retry or abort.

## Recommended Control Direction

Prefer this hierarchy for future work:

```text
state machine / phase scheduler
  -> low-level joint/position control
  -> phase-specific learned modules
  -> optional tactile/vision residuals
  -> recovery logic
```

Do not jump straight to:

```text
one neural network controls the whole task from live observation
```

## Roadmap Alignment

### Stage2.5: MuJoCo Training Maturity

Stage2.5 keeps the current pick-place work inside MuJoCo. Its job is to mature the training workflow before the project moves to sensor-aware fragile-object manipulation.

Current Stage2.5 lesson after Gate2:

- v0.9 Gate2 hard-gated nearest-expert phase MoE reached fixed 7 target success, exact local 5x5 success around `-165`, `-135`, and `-105`, and held-out midpoint 4x4 success around all three regions.
- This is a staged-control baseline, not a smooth continuous target-interpolation policy.
- Fixed-target success is still not enough; the next useful work is inter-region holdout eval, perturbation robustness, and standardized training/reporting.
- Use the optimized workflow in `stage2_5_pick_place_training_workflow_after_gate2.md`: probe narrowly, repair by failure type, then run the full gate.
- Gate4 policy-structure maturity is complete: keep phase-gated / phase-specific control as the mainline. Early approach/grasp/lift should not use fully live-observation BC. Transport, descend, and release may test learned phase-specific modules or residuals only against the hard-gated MoE control baseline.

### Stage3: Sensor-Aware MuJoCo Manipulation

Stage3 is not the hardware-interface stage. Hardware is not available yet, so Stage3 stays in MuJoCo and prepares for future real-world manipulation by adding:

- egg-like fragile object benchmark
- simulated vision abstraction
- synthetic tactile/slip abstraction
- gentle grasp/lift/hold task
- crush/slip/failure metrics
- noisy pose, friction, contact, and actuator perturbations
- recovery or abort logic

The Stage3 anchor task is:

```text
approach egg -> gentle grasp -> lift 5 cm -> hold 3 s -> no slip -> no crush
```

Detailed Stage3 outline:

- `simulations/models/arm_hand_stage1_export/docs/stage3_sensor_aware_mujoco_manipulation_outline.md`

### Stage4: Hardware Interface

Stage4 is reserved for real-hand integration:

- motor command interface
- real sensor data interface
- camera calibration
- tactile/ultrasound integration when available
- hardware-safe state machine
- small staged real-hand tests

Do not treat Stage4 as the active main line until Stage3 has produced a stable sensor-aware MuJoCo baseline.

## Non-Goals For Now

- Do not start RL yet.
- Do not claim hardware-ready policy.
- Do not describe Stage3 as hardware integration; Stage4 owns the hardware interface.
- Do not claim phase-table playback is target-general learning.
- Do not keep collecting datasets without a specific failed gate to repair.
- Do not modify hardware/CAD/STL as part of this training loop unless explicitly requested.

## One-Sentence Memory

The 50cm pick-place task is a sim-to-real scaffold: use it to build a staged, measurable, failure-aware manipulation workflow, not to endlessly optimize a single demo or prematurely deploy end-to-end BC.
