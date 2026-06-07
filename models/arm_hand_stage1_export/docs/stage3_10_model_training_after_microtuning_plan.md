# Stage3.10 Model Training Plan After Final Microtuning

生成日期：2026-06-07

## 目的

Stage3.10 的目的不是继续做 demo 微调，而是把 Stage3.9G 得到的可用混合控制系统变成正式可训练、可比较、可扩展的模型训练路线。

当前已经有：

- 虚拟视觉定位。
- 合成触觉/滑移。
- full-hand gentle grasp。
- thumb-index-middle pinch。
- Stage3.7D full-hand fallback。
- ACT-lite hand chunk policy。
- tactile repair。
- visual-tactile final verification。

Stage3.10 要回答的问题是：

> 我们能不能训练一个比当前规则/脚本/ACT-lite 混合系统更通用的模型，同时仍然保留安全验收和失败分类？

## 分成 4 部分

### 1. 冻结 SkillZoo safety layer v0

产出：

- `stage3_skill_registry_v0.json` 中明确登记当前 safety layer。
- 固化 full-hand fallback、pinch repair、final verification 的参数。
- 写清楚哪些部分是脚本，哪些部分是学习模型，哪些部分是安全规则。

验收：

- 当前 Stage3.9G 命令可复现 `100 / 100`。
- router smoke 仍通过。
- 不宣称 full-action ACT/DP 已通过。

### 2. 扩展 ACT/DP 训练数据

产出：

- 更多 pose-noise、遮挡、抓法、失败恢复场景的数据。
- 数据中必须保存 obs、action、skill_id、phase、success、failure reason、risk flags。
- 保留 safety layer 介入时刻，方便训练 residual 或 policy。

验收：

- 数据集能被 ACT/CVAE 或 Diffusion Policy dataloader 直接读取。
- 每个 episode 都能追溯到技能、场景、结果和失败原因。

### 3. 训练正式模型 baseline

候选路线：

- ACT Transformer/CVAE：先训练 hand/finger chunk，不先做 full-action。
- Diffusion Policy：先作为对照，重点看闭环稳定性。
- phase-specific residual：如果全模型太重，先训练 tactile/vision repair residual。

验收：

- 与 Stage3.9G safety layer 同场景对比。
- 必须报告 success、hold slip、crush、penetration、floor contact、final vision。
- 如果模型不能超过或接近 Stage3.9G，不提升为主线。

### 4. 建立更大 benchmark

产出：

- 固定 benchmark：不同位置、不同 lift、不同可见性、full-hand / pinch 混合。
- 明确训练集、验证集、held-out 场景。
- 报告模板固定，不再只看单个 demo。

验收：

- 至少先跑过当前 `100 / 100` gate。
- 后续扩大到更多随机种子和更难遮挡。
- 出现失败时必须分类，而不是只报成功率。

## 如果成功

进入 Stage3.11：多技能泛化控制。

方向：

- skill router 更智能。
- 模型能根据视觉/触觉状态选择 full-hand、pinch 或 recovery。
- 逐步测试更复杂物体和更复杂场景。

## 如果失败

不回到 Stage3.9 小参数微调。

处理方式：

- 如果是数据覆盖不足，补数据。
- 如果是视觉遮挡，改 final verification 或多视角。
- 如果是动作表示不合适，改 phase-specific / residual / chunk 表示。
- 如果是 full-action 不稳定，继续保持 scripted arm/wrist，不强推端到端。

## 结束 Stage3.9 的边界

Stage3.9G 之后，只有两类工作可以继续留在 Stage3.9：

- 修复复现 bug。
- 修复文档/入口/可视化。

新的模型训练、数据扩展和 benchmark 扩大都进入 Stage3.10。
