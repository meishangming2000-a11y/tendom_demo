# Export4 Replay Report

Generated: 2026-05-26T02:09:11

- Dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export4_scripted_smoke_dataset.npz`
- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Selected episode: `0`
- Frames replayed: `120`
- Status: **PASS**

## Dimension Check

- Dataset obs shape: `[750, 86]`
- Dataset action shape: `[750, 22]`
- Task API obs dim: `112`
- Task API action dim: `22`
- Action dim matches: `True`
- Obs dim matches task API: `False`
- qpos prefix available: `True`
- qvel prefix available: `True`

## Replay Metrics

- Final contact count: `0`
- Final max penetration: `0.000000`

## Screenshots

- No keyframe screenshots requested.

## Notes

- Replay passing means dataset shape and qpos/action replay are usable; it does not mean the grasp task succeeds.
- Dataset collection v0 should wait until canonical ball side and contact proxy are fixed.
