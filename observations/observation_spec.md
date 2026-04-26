# Observation Specification

Status note (2026-03-20):

- The current maintained consumer of this observation layer is the `pre_grasp` pipeline.
- Oracle observations remain the default for the promoted expert-data and BC baseline.
- This split is being preserved so future deployable or real-hardware-aligned observations can be added without rewriting the environment API.

This directory separates simulator observations into two layers:

- `oracle`
  Rich simulator-side state for development, debugging, reward design, and oracle evaluation.
- `deployable`
  A future-facing observation interface intended to stay closer to what the real system can actually sense.

## Why This Split Exists

The project is preparing for future real-to-sim and sim-to-real work.
Because of that, we do not want the simulator API to assume that every policy will always have access to exact simulator state.

The observation split helps with:

- task-oriented policy development
- reward and success debugging with oracle information
- future sensor-aligned policy interfaces
- gradual migration from simulation-only assumptions to hardware-aware observations

## Oracle Observation

Oracle observation is intended for simulation-first development.
It may include exact state such as:

- exact object pose
- exact object velocity
- exact contact state
- exact palm pose
- joint positions and joint velocities

In this first refactor, the oracle observation module also preserves the legacy flattened vector layout used by the current scripts and BC checkpoints.

## Deployable Observation

Deployable observation is intended for future policy deployment on the real system.
It should only depend on signals that could plausibly exist on hardware, or on placeholders that make the future interface explicit.

The current placeholder deployable layer includes:

- joint positions
- joint velocities
- object pose estimate placeholder
- palm pose estimate placeholder
- motor and tendon signal placeholders

This is intentionally not a full perception stack.
The goal in this version is interface layering, not final sensing fidelity.

## Current Compatibility Decision

To avoid breaking the current demo, training, and evaluation scripts:

- both observation modes currently expose a backward-compatible flattened vector
- the richer structured content is available through the observation builders
- existing scripts can continue to call `env.get_obs()` while new code can choose `mode="oracle"` or `mode="deployable"`
