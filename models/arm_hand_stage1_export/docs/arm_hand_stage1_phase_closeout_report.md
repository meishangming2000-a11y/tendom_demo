# Arm-Hand Stage1 Phase Closeout Report

Generated: 2026-05-27T02:26:19

## What Changed

- Phase 0 froze the user-approved CAD mount as the virtual-space entry point.
- Phase 1 generated an arm+hand joint-target/pose tuning experiment and visual pose renders.
- Phase 2 added primitive arm collision proxy boxes while keeping all STL meshes visual-only.
- A palm-side ball scene was generated from the current palm `+Y` direction.

## Current Status

- Frozen reference model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 59, 'nsite': 14, 'nmesh': 29, 'nq': 26, 'nv': 26}`
- Joint tuned status: `PASS_LOAD_AND_RENDER`
- Collision proxy status: `PASS_LOAD_AND_SMOKE`
- Collision model summary: `{'nbody': 31, 'njnt': 26, 'nu': 26, 'ngeom': 64, 'nsite': 14, 'nmesh': 29, 'nq': 26, 'nv': 26}`
- Open static contact count without ball: `0`
- Open static max penetration without ball: `0.000000 m`

## Blocker / Major / Minor

- BLOCKER: none found in load/render generation for the current Phase-2 experiment.
- MAJOR: collision proxy is still v0 and not anatomically tuned; do not train on it.
- MAJOR: thumb remains smoke-usable but not Shadow-equivalent dexterity.
- MINOR: current `*_mcp_flex_joint` names do not match their spread semantics; keep aliases in adapters instead of renaming.

## Next Step

Run the regression script, inspect its report, then decide whether to start tiny dataset collection v0. Training is still explicitly blocked.
