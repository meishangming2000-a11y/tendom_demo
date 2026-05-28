# Export4 Current Baseline Freeze

Generated: 2026-05-26

## Freeze Decision

`hand_stage1_export4_current_baseline.xml` is the current official diagnostic baseline for hand_stage1 export4. It should not be overwritten by wrist, collision, adapter, dataset, or scripted-grasp experiments.

All follow-up changes must be copied into separately named experimental files.

## Frozen Baseline Files

- `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_export4_current_baseline.xml`
- `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_export4_current_baseline.xml`
- `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_current_baseline.xml`

## Known Issues / Notes

1. `wrist_2_joint` was manually confirmed by the user to be an active joint. The frozen current-baseline MJCF already contains it as a hinge; experimental branches must keep/verify this.
2. Collision proxy has static ball penetration and must be tuned in MJCF, not in SolidWorks for now.
3. Four-finger `*_mcp_flex_joint` names are semantically misleading in the current export: they represent lateral spread / abduction-adduction motion, not palm flexion. Names are preserved for now.
4. `thumb_cmc_abd_joint` and `thumb_cmc_joint` axes are confirmed in SolidWorks to pass through true CMC rotation centers. Direction/sign remains handled by scripted MuJoCo targets.
5. Thumb is usable for scripted smoke tests but is not Shadow-equivalent.
6. No RL/BC/training should be started from this baseline until collision proxy, adapter tests, and dataset schema are signed off.

## Experimental Branch

The next experiment branch is:

- `mjcf\hand_stage1_export4_wrist2_collision_tuned.xml`
- `mjcf\scene_ball_export4_wrist2_collision_tuned.xml`

This branch may change only experimental MJCF collision proxy and wrist2 verification fields. It must not modify CAD, STL, joint names, or the frozen current-baseline files.
