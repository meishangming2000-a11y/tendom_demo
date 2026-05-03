# arm_stage1_shadow_combo

Transitional combo wrapper for the current Stage 1 arm import and the temporary
Shadow Hand backend.

## Scope

This model connects:

- `../arm_stage1_export/robot.xml` semantics:
  `base_link -> link_1 -> link_2 -> link_3 -> ee_mount`
- `../shadow_arm_combo/shadow_right_hand_mountable.xml`

The combo is a structural bridge only. It is intended to make arm-hand mounting,
action layout, and adapter boundaries inspectable while the custom tendon-hand
MuJoCo model is still being built.

## Current Strategy

- keep the active arm source model unchanged
- keep the Shadow source and wrapper unchanged
- use a combo-local arm wrapper with mesh paths resolved from this directory
- weld `ee_mount` to `rh_forearm`
- lock the Shadow wrist from the wrapper side for simple structural inspection

## Not A Claim

This is not the final tendon-hand model, not a hardware-calibrated dynamics
model, and not a promoted training environment. It is a bridge for interface
work until the real hand import is available.

## Smoke Check

From `simulations/`:

```bash
python scripts/diagnostics/check_mujoco_model.py --model models/arm_stage1_shadow_combo/scene.xml --require-body ee_mount --require-body rh_forearm --require-body rh_palm --require-actuator a_j1 --require-actuator rh_A_FFJ3
```

## Visual Demo

From `simulations/`:

```bash
python scripts/demo_arm_stage1_shadow.py
```

Headless validation:

```bash
python scripts/demo_arm_stage1_shadow.py --no-viewer --steps 200
```

The demo only checks mount geometry and actuator ordering with gentle scripted
motion. By default it hides the temporary Shadow forearm shell, aligns `rh_wrist`
to `ee_tool_frame_site` with a small forward offset, and re-projects that visual
mount each step so the hand follows the arm mount without using the Shadow
forearm shell as a fake mechanical adapter.

It is not a promoted task environment.
