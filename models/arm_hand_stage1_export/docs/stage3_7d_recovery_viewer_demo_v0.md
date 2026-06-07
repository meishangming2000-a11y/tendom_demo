# Stage3.7D 专用可视化 Demo V0

生成日期：2026-06-06

## 目的

这个 demo 用来专门检查 Stage3.7D 的接触转换恢复微阶段。

它展示的是真实 Stage3.7D 控制链：

```text
虚拟摄像机估计鸡蛋位置
-> 脚本式手臂/手腕接近
-> Stage3.6 学习到的手指策略闭合
-> Stage3.7B 触觉抬升许可门控
-> Stage3.7D slow_lift 高滑移恢复微阶段
```

它不是硬件集成，也不是现实摄像头测试。所有视觉、触觉和滑移信号都来自 MuJoCo 仿真。

## 直接打开 MuJoCo 演示

从项目根目录运行：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py --trial center_nominal --speed 0.4 --no-loop
```

默认是展示模式：

- 隐藏 MuJoCo 左右控制面板，让结果更清楚。
- 快进非 recovery 阶段，直接进入 `slow_lift` 附近，避免等很久才看到重点。
- 关闭窗口即可结束 demo；`--no-loop` 会让一次 episode 结束后停在最终画面。

常用变体：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py --trial center_nominal --speed 0.4 --no-loop --show-ui
python .\simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py --trial right_high_nominal --speed 0.6 --no-loop
python .\simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py --trial center_nominal --speed 0.4 --no-loop --no-demo-focus
```

快速无窗口检查：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py --headless-smoke --trial center_nominal
```

## 画面里应该看什么

左侧状态栏：

- `VISION`：虚拟摄像机估计是否成功、置信度、mask 像素数。
- `TACTILE`：是否接触、是否稳定、触觉区域、滑移分数、挤压风险、穿透量、抬升高度。
- `RECOVERY`：Stage3.7D 是否触发恢复、触发次数、恢复步数、预算使用量、恢复原因、抬升许可门控状态。

画面覆盖层：

- 绿色线/标记：虚拟摄像机估计到的鸡蛋位置。
- 彩色点：触觉接触区域。
- 红色 halo：滑移风险偏高。
- 橙色 halo 或竖条：Stage3.7D 恢复动作和恢复预算。

通俗解释：绿色说明“眼睛看到哪里”，彩色点说明“手哪里碰到了”，红色说明“现在有滑移风险”，橙色说明“控制器正在或刚刚执行过恢复动作”。

## 当前 smoke 结果

命令：

```powershell
python .\simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py --headless-smoke --trial center_nominal
```

结果：

```text
Stage3.7D recovery viewer smoke: trial=center_nominal vision=ok conf=0.983 lift=0.0993 stable=True final_slip=0.010 max_slip=0.420 hold_slip=0.115 recovery_steps=200 recovery_events=37 budget_exhausted=True
```

解释：

- 这次中心样例能稳定抓起并保持鸡蛋。
- Stage3.7D 的 recovery 确实触发了，不是只显示旧的 Stage3.5 传感器 viewer。
- `budget_exhausted=True` 说明恢复预算仍会被用满，这也是 Stage3.7D 之后进入 Stage3.8 鲁棒性验证时要继续观察的风险。

## 验收标准

成功时应该看到：

- MuJoCo 窗口可以直接打开。
- 画面默认没有左右控制面板遮挡。
- 很快进入 `slow_lift`，不用从头等完整 approach/close/settle。
- 绿色视觉估计、彩色触觉点、红色滑移风险、橙色 recovery 标记都能看见。
- headless smoke 输出 `vision=ok`、`stable=True`，并且有非零 `recovery_steps` 或 `recovery_events`。

失败时先按下面顺序排查：

- 如果文件打不开，确认命令路径是 `simulations\models\arm_hand_stage1_export\demo_stage3_7d_recovery_viewer.py`。
- 如果窗口打开但看不到重点，确认没有加 `--no-demo-focus`。
- 如果画面文字遮挡，先用默认隐藏 UI 模式；只有需要调参时才加 `--show-ui`。
- 如果 smoke 失败，先回到 `eval_stage3_contact_transition_recovery_v0.py` 检查 Stage3.7D 控制链，而不是继续调 viewer。
