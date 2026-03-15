#!/usr/bin/env python3
"""
Shadow Hand 抓取环境测试脚本（带可视化）
演示如何创建和使用训练环境，并可视化手和物体的交互。
"""

import sys
import os
import numpy as np
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.environments.shadow_grasp_env import ShadowGraspEnv


def test_environment_with_viewer(enable_viewer=True, max_steps=200, control_timestep=0.002):
    """
    测试环境的基本功能，可选可视化

    参数:
        enable_viewer: 是否启用可视化
        max_steps: 最大测试步数
        control_timestep: 控制时间步长
    """
    print("=" * 60)
    print("Shadow Hand 抓取环境测试（带可视化）")
    print("=" * 60)

    # 创建环境
    env = ShadowGraspEnv(max_steps=max_steps, control_timestep=control_timestep)
    print(f"环境创建成功:")
    print(f"  - 动作空间维度: {env.nu}")
    print(f"  - 观测空间维度: {env.get_obs().shape[0]}")
    print(f"  - 物体主体ID: {env.object_body_id}")
    print(f"  - 手部主体ID: {env.hand_body_id}")
    print(f"  - 地面主体ID: {env.floor_body_id}")

    # 测试重置
    print("\n1. 测试重置:")
    obs = env.reset()
    print(f"   初始观测值形状: {obs.shape}")
    print(f"   初始观测值范围: [{obs.min():.3f}, {obs.max():.3f}]")

    # 初始化可视化
    viewer = None
    if enable_viewer:
        try:
            import mujoco.viewer
            # 创建 viewer
            viewer = mujoco.viewer.launch(env.model, env.data)
            print("   可视化 viewer 已启动")
            # 给viewer一点时间初始化
            time.sleep(1.0)
        except ImportError:
            print("   警告: 未找到 mujoco.viewer，请确保使用 MuJoCo 3.0+")
            enable_viewer = False
        except Exception as e:
            print(f"   警告: 启动 viewer 时出错: {e}")
            enable_viewer = False

    # 测试随机动作步进
    print(f"\n2. 测试随机动作步进 ({max_steps}步):")
    total_reward = 0
    success_count = 0
    contact_count = 0

    for i in range(max_steps):
        # 生成随机动作（范围 [-1, 1]）
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)

        total_reward += reward
        if info['contact']:
            contact_count += 1
        if info['success']:
            success_count += 1

        # 每10步打印一次进度
        if (i + 1) % 10 == 0:
            print(f"   步 {i+1:3d}: 奖励={reward:7.3f}, "
                  f"距离={info['distance']:.3f}, "
                  f"接触={info['contact']}, "
                  f"接触持续时间={info['contact_duration']}, "
                  f"成功={info['success']}")

        # 如果启用可视化，更新viewer
        if enable_viewer and viewer:
            try:
                # 更新viewer显示
                viewer.sync()
                # 添加延迟以便观察（增加延迟让运动更明显）
                time.sleep(0.05)
            except Exception:
                # viewer可能已关闭
                enable_viewer = False

        if done:
            print(f"   Episode 在第 {i+1} 步结束")
            break

    # 关闭viewer
    if viewer:
        try:
            viewer.close()
        except:
            pass

    # 测试结果统计
    print("\n3. 测试结果统计:")
    print(f"   总步数: {min(max_steps, i+1)}")
    print(f"   总奖励: {total_reward:.3f}")
    print(f"   接触次数: {contact_count}")
    print(f"   成功次数: {success_count}")
    print(f"   最终距离: {info['distance']:.3f}")
    print(f"   最终接触持续时间: {info['contact_duration']}")
    print(f"   是否成功: {info['success']}")

    # 观测值组成分析
    print("\n4. 观测值组成分析:")
    obs = env.get_obs()
    nq, nv = env.nq, env.nv
    print(f"   关节位置 (nq={nq}): 索引 0-{nq-1}")
    print(f"   关节速度 (nv={nv}): 索引 {nq}-{nq+nv-1}")
    print(f"   手部位置 (3): 索引 {nq+nv}-{nq+nv+2}")
    print(f"   物体位置 (3): 索引 {nq+nv+3}-{nq+nv+5}")
    print(f"   相对位置 (3): 索引 {nq+nv+6}-{nq+nv+8}")
    print(f"   总维度: {obs.shape[0]}")

    # 奖励组成分析
    print("\n5. 奖励组成分析:")
    print(f"   距离奖励系数: {env.reward_coeffs['distance']}")
    print(f"   接触奖励系数: {env.reward_coeffs['contact']}")
    print(f"   持续接触奖励系数: {env.reward_coeffs['maintain']}")
    print(f"   动作惩罚系数: {env.reward_coeffs['action_penalty']}")

    # 环境参数总结
    print("\n" + "=" * 60)
    print("环境验证总结")
    print("=" * 60)
    print(f"环境稳定性: {'稳定' if i == max_steps-1 else '提前结束'}")
    print(f"观测空间维度: {obs.shape[0]}")
    print(f"动作空间维度: {env.nu}")
    print(f"奖励变化合理性: {'是' if total_reward != 0 else '需进一步验证'}")
    print(f"可视化状态: {'启用' if enable_viewer else '未启用'}")

    return env, total_reward, info


def quick_test_without_viewer():
    """快速测试（无可视化）"""
    print("\n" + "=" * 60)
    print("快速测试（无可视化）")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=50)
    obs = env.reset()
    done = False
    step_count = 0
    total_reward = 0
    rewards = []
    distances = []

    while not done:
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)

        total_reward += reward
        rewards.append(reward)
        distances.append(info['distance'])
        step_count += 1

        if step_count % 10 == 0:
            print(f"  步 {step_count}: 奖励={reward:.3f}, 距离={info['distance']:.3f}")

    print(f"\nEpisode 结束:")
    print(f"  总步数: {step_count}")
    print(f"  总奖励: {total_reward:.3f}")
    print(f"  平均奖励: {np.mean(rewards):.3f}")
    print(f"  平均距离: {np.mean(distances):.3f}")
    print(f"  最终距离: {info['distance']:.3f}")
    print(f"  是否成功: {info['success']}")

    env.close()

    # 简单奖励合理性检查
    if len(rewards) > 0:
        print(f"\n奖励变化检查:")
        print(f"  奖励范围: [{min(rewards):.3f}, {max(rewards):.3f}]")
        print(f"  距离范围: [{min(distances):.3f}, {max(distances):.3f}]")
        # 如果距离减小，奖励应增加（因为距离奖励为负）
        if distances[-1] < distances[0]:
            print(f"  距离减小: {distances[0]:.3f} -> {distances[-1]:.3f}")
            if total_reward > 0:
                print(f"  总奖励为正: {total_reward:.3f} ✓")
            else:
                print(f"  总奖励为负: {total_reward:.3f} (可能动作惩罚过大)")

    return env, total_reward, info


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='测试 Shadow Hand 抓取环境')
    parser.add_argument('--no-viewer', action='store_true',
                       help='禁用可视化（适合无显示环境）')
    parser.add_argument('--steps', type=int, default=200,
                       help='测试步数（默认: 200）')
    parser.add_argument('--quick', action='store_true',
                       help='快速测试（无可视化）')

    args = parser.parse_args()

    if args.quick:
        env, total_reward, info = quick_test_without_viewer()
    else:
        env, total_reward, info = test_environment_with_viewer(
            enable_viewer=not args.no_viewer,
            max_steps=args.steps
        )

    print("\n" + "=" * 60)
    print("运行命令总结:")
    print("=" * 60)
    print("1. 带可视化测试:")
    print("   python scripts/test_env.py")
    print()
    print("2. 无可视化测试:")
    print("   python scripts/test_env.py --no-viewer")
    print()
    print("3. 快速测试:")
    print("   python scripts/test_env.py --quick")
    print()
    print("4. 自定义步数:")
    print("   python scripts/test_env.py --steps 500")
    print()
    print("5. 在代码中使用环境:")
    print("   from src.environments.shadow_grasp_env import ShadowGraspEnv")
    print("   env = ShadowGraspEnv(max_steps=500)")
    print("   obs = env.reset()")
    print("   action = np.random.uniform(-1, 1, size=env.nu)")
    print("   obs, reward, done, info = env.step(action)")