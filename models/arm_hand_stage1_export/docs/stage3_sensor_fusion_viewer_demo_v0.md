# Stage3 Sensor Fusion Viewer Demo V0

Generated: 2026-06-04

## Purpose

This demo makes the current Stage3 sensor-aware loop visible in MuJoCo:

```text
virtual camera egg pose estimate -> approach
MuJoCo contact-derived tactile/slip -> gentle close, lift, hold
```

It is a visualization/demo entry point, not a new policy and not a hardware
integration test.

## Open The MuJoCo Demo

From the repository root:

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py
```

The demo loops until the MuJoCo viewer window is closed.

Useful variants:

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py --trial lifted_diag
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py --trial right_high_nominal --speed 0.6
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py --no-loop
```

Fast non-GUI smoke test:

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py --headless-smoke
```

## What To Look For

Viewer overlay:

- green sphere/ray: virtual-camera egg pose estimate
- colored contact dots: tactile contact regions inferred from MuJoCo contacts
- red halo: slip risk above the Stage3 gate
- top-left text: current phase, vision status, confidence, mask pixels, contact,
  tactile regions, slip, crush, penetration, and lift height
- top-right text: color legend

Tactile color legend:

- thumb: cyan
- index: yellow
- middle: purple
- ring: orange
- little: green
- palm: magenta
- floor/support: gray

Expected visual story:

1. During `approach`, the green virtual-vision marker/ray shows where the egg
   was localized.
2. During `gentle_close_*`, colored contact dots appear on the fingers/palm as
   tactile regions become active.
3. During `slow_lift` and `hold`, the text should show stable tactile contact,
   low final slip, low crush risk, and positive lift height.

## Current Smoke Result

Command:

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_sensor_fusion_viewer.py --headless-smoke
```

Result:

```text
trial=center_nominal
vision=ok
confidence=0.983
final_lift=0.0993 m
stable=True
final_slip=0.016
max_slip=1.000
max_crush=0.113
max_penetration=0.002259 m
```

Interpretation:

- The end state is stable and lifted.
- The max slip spike comes from the lift transition and matches the known
  Stage3.5 risk flag; final hold slip is low.
