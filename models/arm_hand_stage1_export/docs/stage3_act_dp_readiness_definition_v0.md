# Stage3 ACT/DP 可训练就绪定义 v0

- 日期：`2026-06-07`
- 范围：只定义 MuJoCo Stage3 技能数据何时可以进入 ACT / Diffusion Policy 训练，不包含真实硬件、真实摄像头或真实触觉。

## 一句话定义

当每条 canonical 技能演示都能提供完整、有限、维度一致的 `obs_t -> action_t -> next_obs_t` 序列，并且这些演示全部通过当前视觉/触觉/抬升验收时，就可以进入 ACT/DP 训练。

## 必须满足的门槛

1. 数据必须是 dense sequence，不是稀疏 trace：每个 timestep 都有 `obs`、`action`、`next_obs`、`done`、`episode_id`、`skill_id`、`phase_id`。
2. 观测必须来自 Stage3 sensor abstraction：虚拟视觉 + 合成触觉/滑移 + 本体状态；真值只能作为 QA/评估字段，不能作为默认 policy input。
3. action 必须是实际送入 MuJoCo actuator 的控制目标，并且全部落在 actuator control range 内。
4. canonical training episodes 至少 `40` 条：`30` 条全手温和抓取 + `10` 条 thumb/index/middle 捏持，并且成功率为 `40 / 40`。
5. 每个 episode 必须只有一个 terminal `done=True`，且 terminal reason 是对应技能的成功原因。
6. 数据集中必须包含 normalization statistics：`obs_mean/std`、`action_mean/std`、`action_min/max`。
7. 数据必须能按 action chunk / sequence horizon 切窗口，至少通过 `16`、`32`、`64` 三种 horizon 的窗口数量检查。

## 什么时候算还不能训练

- 只有 episode summary 或稀疏 trace，缺少每步 action。
- 捏持和全手抓取使用不同 obs/action schema，不能被同一个 dataloader 读取。
- 部分 canonical episode 失败，但没有明确过滤或失败标签。
- action 没有经过 range 检查，或者包含 NaN/Inf。
- 没有 train/val 切分建议和 normalization statistics。

## 如果成功

下一步可以写 `train_stage3_act_dp_baseline_v0.py`，先做小规模 overfit/smoke，再做 closed-loop MuJoCo eval。

## 如果失败

不进入模型训练；先修数据采集器、技能重放、失败 episode 或 schema 对齐问题。
