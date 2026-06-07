# Stage3.9B3 ACT/DP Dense Sequence Dataset v0 报告

- 生成时间：`2026-06-07T10:16:27`
- 状态：`PASS`
- ACT ready：`True`
- DP ready：`True`
- ACT/DP ready：`True`
- NPZ：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v1_pinch30.npz`
- JSONL：`D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_skill_act_dp_sequence_dataset_v1_pinch30.jsonl`
- metadata：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_skill_act_dp_sequence_dataset_v1_pinch30.json`
- readiness definition：`D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_act_dp_readiness_definition_v0.md`

## 我们先怎么定义“能训练 ACT/DP”

不是指模型已经训练成功，而是指下一步可以直接开始写/运行训练脚本。最低条件是：每个 timestep 有 `obs_t`、`action_t`、`next_obs_t`、`done_t`，所有 canonical episode 成功，action 合法，维度一致，且能按 horizon 切出训练窗口。

## 数据规模

- episodes：`60`
- success：`60 / 60`
- total rows：`230450`
- obs shape：`[230450, 130]`
- actions shape：`[230450, 26]`
- padded obs shape：`[60, 5220, 130]`
- padded actions shape：`[60, 5220, 26]`
- episode length：min `2520` / mean `3840.8` / max `5220`

- diagnostic failed attempts：`3`

## 技能分布

| skill | episodes | success |
| --- | ---: | ---: |
| `full_hand_gentle_grasp` | 30 | 30 |
| `thumb_index_middle_pinch` | 30 | 30 |

## Horizon 窗口检查

| horizon | windows |
| ---: | ---: |
| 8 | 230030 |
| 16 | 229550 |
| 32 | 228590 |
| 64 | 226670 |
| 128 | 222830 |
| 256 | 215150 |

## Schema / 安全检查

- finite obs/actions/next_obs：`True`
- one done per episode：`True`
- action range ok：`True`
- blockers：`[]`

## 失败 attempt 记录

| source ep | trial | reason | true lift | hold slip |
| ---: | --- | --- | ---: | ---: |
| 82 | `right_low_zminus` | `vision_lift_too_small` | -0.0085 | 1.000 |
| 93 | `right_low_zminus` | `vision_lift_too_small` | -0.0088 | 1.000 |
| 96 | `back_large_lift` | `hold_slip_score_high` | 0.0963 | 1.000 |

## 如果成功

下一步进入 Stage3.9C/Stage3.10：写第一个 `train_stage3_act_dp_baseline_v0.py`，先做 dataloader + overfit smoke，再做 MuJoCo closed-loop eval。

## 如果失败

不训练模型。先看 blockers，修失败 episode、schema、action range 或 horizon 窗口问题。
