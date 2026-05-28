# Export4 Replay Report

Generated: 2026-05-26T10:14:50

- Dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export4_palmar_ypos_candidate_5ep_smoke_rollout.npz`
- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_palmar_ypos_collision_candidate.xml`
- Selected episode: `0`
- Frames replayed: `120`
- Status: **PASS**

## Dimension Check

- Dataset obs shape: `[2100, 112]`
- Dataset action shape: `[2100, 22]`
- Task API obs dim: `112`
- Task API action dim: `22`
- Action dim matches: `True`
- Obs dim matches task API: `True`
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
