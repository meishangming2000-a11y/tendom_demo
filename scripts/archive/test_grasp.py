#!/usr/bin/env python3
"""
抓握测试脚本
演示如何使用增强控制器让Shadow Hand抓握物体
对比：随机动作 vs 协调抓握动作
"""

import sys
import os
import numpy as np
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.environments.shadow_grasp_env import ShadowGraspEnv
from src.controllers import create_controller


def test_random_actions():
    """测试随机动作（对比基准）"""
    print("=" * 60)
    print("测试1: 随机动作（基准）")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=100)
    obs = env.reset()

    print(f"环境初始化:")
    print(f"  - 动作维度: {env.nu}")
    print(f"  - 观测维度: {obs.shape[0]}")
    print(f"  - 物体位置: {env._get_object_position()}")
    print(f"  - 手部位置: {env._get_hand_position()}")
    print(f"  - 初始距离: {env._get_distance():.3f}")

    print("\n运行50步随机动作:")
    contact_count = 0
    success_count = 0

    for i in range(50):
        # 完全随机动作
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)

        if info['contact']:
            contact_count += 1
        if info['success']:
            success_count += 1

        if (i + 1) % 10 == 0:
            print(f"  步 {i+1:2d}: 奖励={reward:7.3f}, "
                  f"距离={info['distance']:.3f}, "
                  f"接触={info['contact']}")

    print(f"\n统计:")
    print(f"  接触次数: {contact_count}/50")
    print(f"  成功次数: {success_count}/50")
    print(f"  最终距离: {info['distance']:.3f}")
    print(f"  最终奖励: {reward:.3f}")

    return env, info


def test_enhanced_controller_grasp():
    """测试增强控制器的抓握功能"""
    print("\n" + "=" * 60)
    print("测试2: 增强控制器 - 协调抓握")
    print("=" * 60)

    # 创建环境
    env = ShadowGraspEnv(max_steps=100)
    obs = env.reset()

    # 创建增强控制器
    controller = create_controller('enhanced', env.model, env.data)

    print(f"控制器创建: {controller.__class__.__name__}")
    print(f"抓取力度范围: 0.0 (张开) -> 1.0 (握紧)")

    # 测试不同的抓取力度
    grasp_strengths = [0.0, 0.3, 0.6, 0.9]

    for strength in grasp_strengths:
        print(f"\n--- 测试抓取力度: {strength} ---")

        # 重置环境
        obs = env.reset()

        # 设置抓取状态
        controller.set_grasping(is_grasping=True, strength=strength)

        contact_durations = []
        rewards = []

        for i in range(50):
            # 使用控制器计算控制信号
            control_values = controller.compute_control(
                t=i * env.control_timestep,
                grasp_strength=strength,
                control_mode='position'
            )

            # 将控制信号转换为环境动作（需要归一化）
            # 注意：环境期望 [-1, 1] 的动作，但控制器输出的是实际控制值
            # 这里我们需要反向归一化
            action = env._denormalize_action(control_values)

            obs, reward, done, info = env.step(action)

            contact_durations.append(info['contact_duration'])
            rewards.append(reward)

            if (i + 1) % 10 == 0:
                print(f"  步 {i+1:2d}: 力度={strength:.1f}, "
                      f"奖励={reward:7.3f}, "
                      f"距离={info['distance']:.3f}, "
                      f"接触={info['contact']}")

        # 统计
        avg_reward = np.mean(rewards)
        max_contact = max(contact_durations) if contact_durations else 0

        print(f"  平均奖励: {avg_reward:.3f}")
        print(f"  最长连续接触: {max_contact}步")
        print(f"  是否成功: {info['success']}")

    return env, controller, info


def test_simple_grasp_pattern():
    """测试简单的手抓握模式（不使用完整控制器）"""
    print("\n" + "=" * 60)
    print("测试3: 简单抓握模式")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=100)
    obs = env.reset()

    print(f"创建简单抓握模式:")
    print(f"  - 只控制手指弯曲关节（忽略手腕）")
    print(f"  - 使用对称抓握动作")

    # 手指分组（简化版）
    finger_groups = {
        'thumb': [2, 3, 4, 5, 6],      # 拇指
        'index': [7, 8, 9, 10],        # 食指
        'middle': [11, 12, 13, 14],    # 中指
        'ring': [15, 16, 17, 18],      # 无名指
        'little': [19, 20, 21, 22, 23] # 小指
    }

    # 测试不同的抓握力度
    for strength in [0.2, 0.5, 0.8]:
        print(f"\n--- 简单抓握力度: {strength} ---")

        obs = env.reset()
        total_reward = 0

        for i in range(50):
            # 创建简单抓握动作
            action = np.zeros(env.nu)

            # 对所有手指应用相同的弯曲力度
            for finger_name, indices in finger_groups.items():
                for idx in indices:
                    if idx < env.nu:
                        # 正动作表示弯曲（抓握）
                        action[idx] = strength

            # 手腕保持中立
            action[0] = 0.0  # 手腕旋转1
            action[1] = 0.0  # 手腕旋转2

            obs, reward, done, info = env.step(action)
            total_reward += reward

            if (i + 1) % 10 == 0:
                print(f"  步 {i+1:2d}: 力度={strength:.1f}, "
                      f"奖励={reward:7.3f}, "
                      f"距离={info['distance']:.3f}, "
                      f"接触={info['contact']}")

        print(f"  总奖励: {total_reward:.3f}")
        print(f"  最终接触持续时间: {info['contact_duration']}")

    return env, info


def explain_why_random_actions_dont_grasp():
    """解释为什么随机动作不能让手抓握"""
    print("\n" + "=" * 60)
    print("为什么随机动作不能让手抓握？")
    print("=" * 60)

    print("\n1. 执行器数量多且复杂:")
    print("   - Shadow Hand 有 24 个执行器")
    print("   - 每个执行器控制不同的关节")
    print("   - 随机动作很难产生协调的手指运动")

    print("\n2. 控制范围不对称:")
    print("   - 许多执行器控制范围不是对称的 [-1, 1]")
    print("   - 例如: [-0.524, 0.175] (负范围大于正范围)")
    print("   - 随机动作可能导致关节向错误方向运动")

    print("\n3. 需要协调控制:")
    print("   - 抓握需要手指同时弯曲")
    print("   - 手腕需要适当定位")
    print("   - 随机动作各关节独立，难以协调")

    print("\n4. 接触检测需要精确:")
    print("   - 手必须正确定位到物体")
    print("   - 手指必须适当弯曲以接触物体")
    print("   - 随机动作很难达到这种精确度")

    print("\n解决方案:")
    print("  1. 使用增强控制器 (EnhancedController)")
    print("  2. 使用简单抓握模式 (如测试3)")
    print("  3. 设计专门的抓握动作序列")


def main():
    """主函数"""
    print("Shadow Hand 抓握功能测试")
    print("=" * 60)

    # 运行测试
    env1, info1 = test_random_actions()

    try:
        env2, controller, info2 = test_enhanced_controller_grasp()
    except Exception as e:
        print(f"\n增强控制器测试失败: {e}")
        print("尝试简单抓握模式...")
        env2, info2 = test_simple_grasp_pattern()

    env3, info3 = test_simple_grasp_pattern()

    # 解释
    explain_why_random_actions_dont_grasp()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    print("\n运行命令:")
    print("1. 随机动作测试:")
    print("   python scripts/test_env.py --no-viewer --steps 50")

    print("\n2. 增强控制器演示:")
    print("   python scripts/run_demo.py --controller enhanced --grasp-strength 0.7")

    print("\n3. 快速抓握测试:")
    print("   python scripts/test_grasp.py")

    print("\n4. 带可视化的抓握测试:")
    print("   python scripts/test_env_with_grasp.py (如果创建了该脚本)")


if __name__ == "__main__":
    main()