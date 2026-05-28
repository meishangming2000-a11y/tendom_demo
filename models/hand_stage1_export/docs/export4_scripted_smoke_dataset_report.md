# Export4 Scripted Smoke Dataset Report

Generated: 2026-05-26T01:55:38

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export4_wrist2_collision_tuned.xml`
- Dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export4_scripted_smoke_dataset.npz`
- Episodes: `5`
- Steps per phase: `30`
- Obs shape: `[750, 86]`
- Action shape: `[750, 22]`
- Action dim: `22`
- wrist_2 in action: `True`
- Labels: `{'fail_far_from_ball': 2, 'visual_close_no_contact': 3}`

## Episode Summary

| episode | ball | label | contacts | max pen | four-tip avg | thumb-ball | thumb-index |
|---:|---|---|---:|---:|---:|---:|---:|
| 0 | `[0.0, -0.1, 0.21]` | fail_far_from_ball | 0 | 0.000000 | 0.153969 | 0.144270 | 0.019043 |
| 1 | `[0.0, 0.1, 0.21]` | visual_close_no_contact | 0 | 0.000000 | 0.061918 | 0.060092 | 0.019043 |
| 2 | `[0.0, 0.08, 0.21]` | visual_close_no_contact | 0 | 0.000000 | 0.047031 | 0.041609 | 0.019043 |
| 3 | `[0.0, -0.08, 0.21]` | fail_far_from_ball | 0 | 0.000000 | 0.134629 | 0.124474 | 0.019043 |
| 4 | `[0.015, 0.1, 0.21]` | visual_close_no_contact | 0 | 0.000000 | 0.062160 | 0.066276 | 0.019043 |

## Notes

- This is deliberately tiny: 5 scripted episodes only.
- It is useful for adapter, logging, shape, and replay tests.
- It is not yet suitable as training data because the default grasp side/contact behavior is still unresolved.
