#!/usr/bin/env python3
"""
检查奖励计算是否正确
"""

import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.environments.shadow_grasp_env import ShadowGraspEnv


def check_reward_components():
    """检查奖励各个组件的计算"""
    print("检查奖励组件计算")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=100)
    obs = env.reset()

    # 获取初始距离
    distance = env._get_distance()
    print(f"初始距离: {distance:.3f}")
    print(f"距离奖励系数: {env.reward_coeffs['distance']}")
    print(f"距离奖励: {env.reward_coeffs['distance'] * distance:.3f}")

    # 测试零动作（无接触）
    zero_action = np.zeros(env.nu)
    obs, reward, done, info = env.step(zero_action)

    print(f"\n零动作测试:")
    print(f"  距离: {info['distance']:.3f}")
    print(f"  接触: {info['contact']}")
    print(f"  接触持续时间: {info['contact_duration']}")
    print(f"  实际奖励: {reward:.3f}")

    # 手动计算预期奖励
    expected = (
        env.reward_coeffs['distance'] * info['distance'] +
        (env.reward_coeffs['contact'] if info['contact'] else 0.0) +
        (env.reward_coeffs['maintain'] * info['contact_duration'] if info['contact'] else 0.0) +
        env.reward_coeffs['action_penalty'] * np.sum(zero_action ** 2)
    )
    print(f"  预期奖励: {expected:.3f}")
    print(f"  差值: {abs(reward - expected):.6f}")

    if abs(reward - expected) < 0.001:
        print("  [PASS] 奖励计算正确")
    else:
        print("  [FAIL] 奖励计算错误")

    # 测试奖励随距离变化
    print("\n奖励随距离变化测试:")
    print("步骤 | 距离 | 奖励 | 接触 | 奖励变化")
    print("-" * 50)

    prev_reward = reward
    prev_distance = info['distance']

    for i in range(10):
        action = np.random.uniform(-0.5, 0.5, size=env.nu)  # 小幅度动作
        obs, reward, done, info = env.step(action)

        distance_change = info['distance'] - prev_distance
        reward_change = reward - prev_reward

        contact_str = "YES" if info['contact'] else "NO"
        print(f"{i+1:4d} | {info['distance']:6.3f} | {reward:7.3f} | {contact_str:4s} | {reward_change:7.3f}")

        # 检查奖励变化是否符合预期
        # 如果距离减小，奖励应该增加（因为距离奖励为负）
        if distance_change < -0.001:  # 距离减小
            if reward_change > -0.001:  # 奖励应该增加
                print(f"      [OK] 距离减小{abs(distance_change):.3f} -> 奖励增加{reward_change:.3f}")
            else:
                print(f"      [WARN] 距离减小但奖励未增加")

        prev_reward = reward
        prev_distance = info['distance']

    # 测试接触奖励
    print("\n接触奖励测试:")
    # 寻找接触状态
    contact_found = False
    for i in range(50):
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)

        if info['contact'] and not contact_found:
            contact_found = True
            print(f"第{i+1}步检测到接触!")
            print(f"  接触前距离: {prev_distance:.3f}")
            print(f"  接触时距离: {info['distance']:.3f}")
            print(f"  接触时奖励: {reward:.3f}")
            print(f"  接触奖励系数: {env.reward_coeffs['contact']}")
            print(f"  接触持续时间奖励系数: {env.reward_coeffs['maintain']}")

            # 检查接触奖励是否被应用
            if reward > 9.0:  # 接触奖励至少为10 - 距离惩罚
                print(f"  [PASS] 接触奖励正确应用")
            else:
                print(f"  [FAIL] 接触奖励可能未正确应用")
            break

        prev_distance = info['distance']

    if not contact_found:
        print("50步内未检测到接触（正常）")

    return True


def check_action_normalization():
    """检查动作归一化"""
    print("\n\n检查动作归一化")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=100)

    # 测试边界值
    test_cases = [
        ("最小值", -1.0),
        ("零值", 0.0),
        ("最大值", 1.0),
    ]

    for name, value in test_cases:
        action = np.full(env.nu, value)
        ctrl = env._normalize_action(action)

        # 检查是否在执行器范围内
        all_in_range = True
        for i in range(env.nu):
            ctrl_min, ctrl_max = env.actuator_ctrlrange[i]
            if ctrl[i] < ctrl_min - 0.001 or ctrl[i] > ctrl_max + 0.001:
                print(f"  [FAIL] {name}: 执行器{i}控制信号{ctrl[i]:.3f}超出范围[{ctrl_min:.3f}, {ctrl_max:.3f}]")
                all_in_range = False
                break

        if all_in_range:
            print(f"  [PASS] {name}: 所有执行器在范围内")

    # 显示示例映射
    print("\n示例映射（第一个执行器）:")
    for value in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        action = np.full(env.nu, value)
        ctrl = env._normalize_action(action)
        ctrl_min, ctrl_max = env.actuator_ctrlrange[0]
        print(f"  action={value:5.1f} -> ctrl={ctrl[0]:7.3f} (范围: [{ctrl_min:.3f}, {ctrl_max:.3f}])")

    return True


def main():
    """主函数"""
    print("ShadowGraspEnv 奖励和动作验证")
    print("=" * 60)

    check_reward_components()
    check_action_normalization()

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)


if __name__ == "__main__":
    main()