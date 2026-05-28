# Export4 Current Baseline Status

Generated: 2026-05-25 01:45:00

## Baseline Files

- Hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_current_baseline.xml`
- No-ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_export4_current_baseline.xml`
- Ball scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_current_baseline.xml`
- Thumb tuning report: `D:\tendon_project\simulations\models\hand_stage1_export\docs\export4_thumb_joint_tuning_report.md`
- Thumb close demo report: `D:\tendon_project\simulations\models\hand_stage1_export\docs\export4_thumb_tuned_close_demo_report.md`

## What This Baseline Contains

- Export4 clean visual mesh.
- Simplified collision proxy inherited from the export4 MuJoCo draft.
- Position actuators.
- Long-finger sign correction and conservative long-finger tuning.
- Experimental thumb range tuning.
- Visual recommended thumb target:
  - `thumb_cmc_abd_joint = -0.3`
  - `thumb_cmc_joint = 0.0`
  - `thumb_mcp_joint = 0.25`
  - `thumb_ip_joint = -0.25`

## Load Check

- `hand_stage1_export4_current_baseline.xml`: `25 bodies / 22 joints / 22 actuators / 48 geoms / 5 sites`
- `scene_export4_current_baseline.xml`: `25 bodies / 22 joints / 22 actuators / 49 geoms / 5 sites`
- `scene_ball_export4_current_baseline.xml`: `26 bodies / 23 joints / 22 actuators / 50 geoms / 5 sites`

## Thumb Result

- Score-best target remains recorded, but the visual recommended target is preferred for scripted tasks because it adds mild MCP/IP flexion.
- Thumb-tuned close demo hold metrics:
  - thumb-index distance: `0.0195 m`
  - thumb-middle distance: `0.0332 m`
  - thumb-long-tip-centroid distance: `0.0314 m`
  - contact count: `0`
  - max penetration: `0.00000 m`

## Current Interpretation

This is now the current diagnostic baseline for export4. It is good enough for:

- joint direction audit,
- thumb audit,
- collision audit,
- Shadow/video mapping comparison,
- scripted grasp-state quantification,
- pre-training adapter/data-schema design.

It is not yet a training-ready dexterous hand model. Training should still wait until collision, task reward, action adapter, and evaluation metrics are stabilized.

## Open Cautions

- Thumb CMC semantics are much improved visually, but still need final SolidWorks sign/origin confirmation.
- Collision proxy is simplified and should not be treated as final contact geometry.
- The baseline is a MuJoCo experimental file, not a replacement for CAD or raw export4.
