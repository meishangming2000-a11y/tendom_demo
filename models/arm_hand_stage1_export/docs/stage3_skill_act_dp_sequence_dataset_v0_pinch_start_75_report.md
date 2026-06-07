# Stage3.9B3 ACT/DP Dense Sequence Dataset v0 报告

- 生成时间：`2026-06-07T02:23:11`
- 状态：`BLOCKED`
- ACT ready：`False`
- DP ready：`False`
- ACT/DP ready：`False`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v0_pinch_start_75.npz`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v0_pinch_start_75.jsonl`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_skill_act_dp_sequence_dataset_v0_pinch_start_75.json`
- readiness definition：`D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_act_dp_readiness_definition_v0.md`

## 我们先怎么定义“能训练 ACT/DP”

不是指模型已经训练成功，而是指下一步可以直接开始写/运行训练脚本。最低条件是：每个 timestep 有 `obs_t`、`action_t`、`next_obs_t`、`done_t`，所有 canonical episode 成功，action 合法，维度一致，且能按 horizon 切出训练窗口。

## 数据规模

- episodes：`10`
- success：`8 / 10`
- total rows：`25456`
- obs shape：`[25456, 130]`
- actions shape：`[25456, 26]`
- padded obs shape：`[10, 2754, 130]`
- padded actions shape：`[10, 2754, 26]`
- episode length：min `2520` / mean `2545.6` / max `2754`

## 技能分布

| skill | episodes | success |
| --- | ---: | ---: |
| `full_hand_gentle_grasp` | 0 | 0 |
| `thumb_index_middle_pinch` | 10 | 8 |

## Horizon 窗口检查

| horizon | windows |
| ---: | ---: |
| 8 | 20360 |
| 16 | 20296 |
| 32 | 20168 |
| 64 | 19912 |
| 128 | 19400 |
| 256 | 18376 |

## Schema / 安全检查

- finite obs/actions/next_obs：`True`
- one done per episode：`True`
- action range ok：`True`
- blockers：`['canonical_episode_count_below_40', 'canonical_episode_failure_present', 'full_hand_success_count_below_30', 'pinch_success_count_below_10']`

## 如果成功

下一步进入 Stage3.9C/Stage3.10：写第一个 `train_stage3_act_dp_baseline_v0.py`，先做 dataloader + overfit smoke，再做 MuJoCo closed-loop eval。

## 如果失败

不训练模型。先看 blockers，修失败 episode、schema、action range 或 horizon 窗口问题。
