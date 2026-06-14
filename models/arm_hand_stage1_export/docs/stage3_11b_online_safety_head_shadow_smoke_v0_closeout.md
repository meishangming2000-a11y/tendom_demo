# Stage3.11B Online Safety-Head Shadow Mode v0 Closeout

- 生成时间：`2026-06-09T14:00:06`
- 状态：`PASS`
- safety head：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_10d_c_occlusion_safety_head_v0.npz`
- 模式：shadow only；只记录预测，不改变 MuJoCo 控制动作。
- 边界：MuJoCo-only；不是 full-action ACT/DP promotion；不是真实摄像头、真实触觉、超声或硬件 runtime。

## 做了什么

Stage3.11B 把 Stage3.10D-C 的 episode-level safety head 接到 Stage3.10C/D evaluator 里。每个 episode 结束后，metadata 会多出 `safety_head_shadow`：包括预测标签、真实标签、概率、mismatch，以及 false failure / missed failure / unsafe hold-safe 计数。这个 head 没有参与动作控制，所以它是旁路观察器，不是上线控制器。

## 总结果

| suite | episodes | success | shadow records | false failure | missed failure | unsafe hold-safe | label mismatch |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `db_v1` | 10 | 10 | 10 | 0 | 0 | 0 | 0 |
| `stress` | 6 | 5 | 6 | 0 | 0 | 0 | 2 |

## Case 明细

| suite | case | status | success | false failure | missed failure | unsafe hold-safe | mismatch | 风险标记 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `db_v1` | `pose008_strictvision` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `db_v1` | `pose010_corroborated` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `db_v1` | `initial_maskdrop30_pose005` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `db_v1` | `final_maskdrop55_occlusionaware_pose005` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `db_v1` | `final_occluder45_occlusionaware_pose008` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `stress` | `initial_depthnoise5_pose005` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `stress` | `final_falseblob_occlusionaware_pose005` | `PASS` | 2 / 2 | 0 | 0 | 0 | 0 | `{'early_contact_in_approach': 2, 'transient_or_hold_slip': 1, 'recovery_budget_exhausted': 1, 'transient_slip_high': 1}` |
| `stress` | `initial_combinedhard_pose003_boundary` | `PARTIAL` | 1 / 2 | 0 | 0 | 0 | 2 | `{'early_contact_in_approach': 1}` |

## 非危险 label mismatch

| case | mismatch labels | examples |
| --- | --- | --- |
| `initial_combinedhard_pose003_boundary` | `{'initial_quality_adapter_required': 1, 'pinch_repair_required_or_active': 1}` | `[{'episode_id': 1, 'skill_id': 'thumb_index_middle_pinch', 'success': False, 'terminal_reason': 'initial_vision_failed', 'mismatch_labels': ['initial_quality_adapter_required', 'pinch_repair_required_or_active']}]` |

## 发现的问题

- 这次没有发现 hard blocker：D-B v1 与新增 stress 在 shadow mode 下保持通过，且没有 false failure、missed failure 或 unsafe hold-safe prediction。
- 仍然有过程风险需要继续记录：`early_contact_in_approach`、`transient_slip_high` 和 `recovery_budget_exhausted` 仍会出现；shadow head 目前只是 episode-level，不能替代逐帧风险标签。
- `combined_hard` 仍作为合理拒绝边界：这里的目标不是强行抓，而是确认 safety head 能看到失败/拒绝，不把失败预测成 hold-safe。

## 如果成功

进入 Stage3.11C：把 shadow mode 里确认过的 safety/vision/tactile 状态展开成逐帧 noisy/occlusion labels，例如 `vision_degraded`、`vision_freeze`、`tactile_handoff`、`repair_active` 和 `risk_any`。

## 如果失败

先拆四类原因：feature alignment、checkpoint loading、label definition、online/offline distribution shift。修完 B 后再进入 C，不把错误标签喂给 residual/full-action 训练。
