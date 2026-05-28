# Export3 Scripted Dataset v0 Report

Status: diagnostic training asset, not a promoted stable_grasp baseline.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Dataset: `D:\tendon_project\simulations\models\hand_stage1_export\data\export3_scripted_pinned_wrap_smoke.npz`
- Metadata: `D:\tendon_project\simulations\models\hand_stage1_export\metadata\export3_scripted_dataset_smoke.json`
- Backup directory: none needed
- Episode count: 6
- Sample count: 228
- Observation dim: 100
- Action dim: 21
- Modes: `{'pinned': 6}`
- Classification counts: `{'PINNED_WRAP_PASS': 6}`
- Step stride: 6
- Speed: 5.0

## Dataset Semantics

- `observations`: state vector built from controlled joint qpos/qvel, ball pose/velocity, fingertip site positions, fingertip-ball distances, contact summary, previous ctrl, stage fraction, finger scale, thumb rank, and target ball position.
- `actions`: 21-D MuJoCo position actuator target vector after actuator ctrlrange clipping.
- `episode_class` / `sample_class`: scripted-trial diagnostic classification labels.
- This dataset is meant for first-pass BC/DAgger scaffolding over export3 scripted behavior.

## Limits

- The ball is pinned during scripted closing for collected `pinned` episodes.
- Successful pinned wrap is not equivalent to stable free-object grasp.
- Collision is still primitive proxy; clean STL remains visual-only.
- Thumb/wrist mechanical semantics still need manual confirmation before final task training.

## Episodes

| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Samples | Hold contacts | Hold penetration | Mean four-tip | Thumb-ball |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 1 | 38 | 2 | 0.006314 | 0.034256 | 0.087358 |
| 1 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 2 | 38 | 2 | 0.006315 | 0.034258 | 0.088840 |
| 2 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 3 | 38 | 2 | 0.006296 | 0.034240 | 0.087515 |
| 3 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 4 | 38 | 2 | 0.006316 | 0.034260 | 0.091169 |
| 4 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 0.85 | 5 | 38 | 2 | 0.006347 | 0.034298 | 0.093562 |
| 5 | pinned | PINNED_WRAP_PASS | `[0.0, -0.1, 0.21]` | 1.00 | 1 | 38 | 4 | 0.009781 | 0.033903 | 0.087173 |
