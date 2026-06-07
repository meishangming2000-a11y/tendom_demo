# Stage3.9B3 ACT/DP Dense Sequence Dataset v0 报告

- 生成时间：`2026-06-07T02:07:16`
- 状态：`BLOCKED`
- ACT ready：`False`
- DP ready：`False`
- ACT/DP ready：`False`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v0_smoke.npz`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v0_smoke.jsonl`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_skill_act_dp_sequence_dataset_v0_smoke.json`
- readiness definition：`D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_act_dp_readiness_definition_v0.md`

## 我们先怎么定义“能训练 ACT/DP”

不是指模型已经训练成功，而是指下一步可以直接开始写/运行训练脚本。最低条件是：每个 timestep 有 `obs_t`、`action_t`、`next_obs_t`、`done_t`，所有 canonical episode 成功，action 合法，维度一致，且能按 horizon 切出训练窗口。

## 数据规模

- episodes：`2`
- success：`2 / 2`
- total rows：`7546`
- obs shape：`[7546, 130]`
- actions shape：`[7546, 26]`
- padded obs shape：`[2, 5026, 130]`
- padded actions shape：`[2, 5026, 26]`
- episode length：min `2520` / mean `3773.0` / max `5026`

## 技能分布

| skill | episodes | success |
| --- | ---: | ---: |
| `full_hand_gentle_grasp` | 1 | 1 |
| `thumb_index_middle_pinch` | 1 | 1 |

## Horizon 窗口检查

| horizon | windows |
| ---: | ---: |
| 8 | 7532 |
| 16 | 7516 |
| 32 | 7484 |
| 64 | 7420 |
| 128 | 7292 |
| 256 | 7036 |

## Schema / 安全检查

- finite obs/actions/next_obs：`True`
- one done per episode：`True`
- action range ok：`True`
- blockers：`['canonical_episode_count_below_40', 'full_hand_success_count_below_30', 'pinch_success_count_below_10']`

## 如果成功

下一步进入 Stage3.9C/Stage3.10：写第一个 `train_stage3_act_dp_baseline_v0.py`，先做 dataloader + overfit smoke，再做 MuJoCo closed-loop eval。

## 如果失败

不训练模型。先看 blockers，修失败 episode、schema、action range 或 horizon 窗口问题。
