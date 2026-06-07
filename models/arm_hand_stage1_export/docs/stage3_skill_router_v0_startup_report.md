# Stage3.9C Skill Router v0 启动报告

- 生成时间：`2026-06-07T18:57:02`
- registry：`D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage3_skill_registry_v0.json`
- scene_cases：`D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_skill_router_v0_sample_scenes.json`
- 状态：`PASS`
- 技能数量：`7`
- 可执行技能数量：`2`
- 路由样例数量：`5`
- expectation 通过：`5 / 5`

## 路由结果

| case | selected skill | status | reason | confidence | expected | ok | executable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_clearance_prefers_pinch | thumb_index_middle_pinch | registered_baseline | pinch_clearance_and_vision_good | 0.8110 | thumb_index_middle_pinch | PASS | yes |
| low_clearance_prefers_full_hand | full_hand_gentle_grasp | registered_baseline | default_gentle_or_low_clearance_route | 0.7260 | full_hand_gentle_grasp | PASS | yes |
| contact_slip_requires_recovery | slip_recovery | planned_promote_from_embedded | contact_slip_high | 0.9700 | slip_recovery | PASS | no |
| weak_vision_reacquire_first | acquire_vision_pose | registered_sensor_primitive | vision_confidence_too_low_for_action | 0.6900 | acquire_vision_pose | PASS | no |
| unsafe_crush_abort | release_or_abort | planned_safety_skill | safety_metric_exceeded | 0.9500 | release_or_abort | PASS | no |

## Smoke 测试

本次没有运行 demo smoke。使用 `--run-smoke` 可以对已注册可执行技能做无窗口检查。

## 结论

这一步只证明 Stage3.9 的技能注册和规则路由入口已经可检查；它还不是 ACT/Diffusion Policy 训练，也不是 LLM/VLA 调度。

如果成功：下一步进入 Stage3.9B，开始把 Stage3.7D 和 Stage3.8B episode 转成统一数据格式。

如果失败：先修 registry、scene case、success gate 和 failure taxonomy，不扩大到模型训练。
