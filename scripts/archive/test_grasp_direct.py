#!/usr/bin/env python3
"""
直接抓握测试
使用控制器直接控制环境，演示抓握动作
"""

import sys
import os
import numpy as np
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.environments.shadow_grasp_env import ShadowGraspEnv
from src.controllers import create_controller


def test_grasp_with_viewer():
    """使用增强控制器测试抓握（带可视化）"""
    print("=" * 60)
    print("增强控制器抓握测试（带可视化）")
    print("=" * 60)

    # 创建环境
    env = ShadowGraspEnv(max_steps=200, control_timestep=0.002)
    obs = env.reset()

    # 创建增强控制器
    try:
        controller = create_controller('enhanced', env.model, env.data)
        print(f"控制器创建成功: {controller.__class__.__name__}")
    except Exception as e:
        print(f"创建控制器失败: {e}")
        print("尝试使用简单控制器...")
        controller = create_controller('linear', env.model, env.data)

    print(f"\n初始状态:")
    print(f"  手部位置: {env._get_hand_position()}")
    print(f"  物体位置: {env._get_object_position()}")
    print(f"  初始距离: {env._get_distance():.3f}")

    # 启动可视化
    viewer = None
    try:
        import mujoco.viewer
        viewer = mujoco.viewer.launch(env.model, env.data)
        print("\nViewer 已启动，按空格键开始/暂停")
        print("等待 2 秒让 viewer 初始化...")
        time.sleep(2.0)
    except Exception as e:
        print(f"\n无法启动 viewer: {e}")
        viewer = None

    # 抓握测试序列
    grasp_sequence = [
        (0.0, 10, "张开"),
        (0.3, 30, "轻微抓握"),
        (0.6, 50, "中等抓握"),
        (0.9, 70, "强力抓握"),
        (0.4, 40, "放松"),
        (0.0, 20, "完全张开")
    ]

    total_steps = sum(steps for _, steps, _ in grasp_sequence)
    current_step = 0

    print(f"\n开始抓握测试序列（共{total_steps}步）:")

    for grasp_strength, steps, description in grasp_sequence:
        print(f"\n--- {description} (力度: {grasp_strength:.1f}, 步数: {steps}) ---")

        # 设置抓取状态
        if hasattr(controller, 'set_grasping'):
            controller.set_grasping(is_grasping=True, strength=grasp_strength)
        elif hasattr(controller, 'grasp_strength'):
            controller.grasp_strength = grasp_strength

        for i in range(steps):
            # 使用控制器计算控制
            if hasattr(controller, 'compute_control'):
                control_values = controller.compute_control(
                    t=current_step * env.control_timestep,
                    grasp_strength=grasp_strength,
                    control_mode='position'
                )
                # 直接应用控制到环境
                env.data.ctrl[:] = control_values
            else:
                # 简单控制器
                controller.apply_control(current_step * env.control_timestep)

            # 执行模拟步
            mujoco.mj_step(env.model, env.data)

            # 更新环境状态计数
            env.current_step += 1

            # 检查接触
            is_contact = env._check_contact()
            if is_contact:
                env.contact_duration += 1
            else:
                env.contact_duration = 0

            # 每10步打印一次
            if (current_step % 10 == 0) or (i == steps - 1):
                distance = env._get_distance()
                print(f"  步 {current_step:3d}: 距离={distance:.3f}, "
                      f"接触={'是' if is_contact else '否'}, "
                      f"接触持续时间={env.contact_duration}")

            # 更新viewer
            if viewer:
                try:
                    viewer.sync()
                    time.sleep(0.02)  # 20ms延迟，让运动更明显
                except Exception:
                    viewer = None

            current_step += 1

    # 最终统计
    print(f"\n" + "=" * 60)
    print("抓握测试完成")
    print("=" * 60)

    final_distance = env._get_distance()
    final_contact = env._check_contact()
    final_contact_duration = env.contact_duration
    is_success = env.is_success()

    print(f"最终状态:")
    print(f"  步数: {current_step}")
    print(f"  距离: {final_distance:.3f}")
    print(f"  接触: {'是' if final_contact else '否'}")
    print(f"  接触持续时间: {final_contact_duration}")
    print(f"  是否成功: {'是' if is_success else '否'}")

    if viewer:
        print(f"\nViewer 仍处于打开状态")
        print("按 ESC 键退出 viewer")
        time.sleep(2.0)

    return env, controller


def test_simple_grasp_without_viewer():
    """简单抓握测试（无可视化）"""
    print("\n" + "=" * 60)
    print("简单抓握测试（无可视化）")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=100)
    obs = env.reset()

    print("创建简单抓握模式...")

    # 手指分组（基于Shadow Hand）
    finger_groups = {
        'thumb': [2, 3, 4, 5, 6],
        'index': [7, 8, 9, 10],
        'middle': [11, 12, 13, 14],
        'ring': [15, 16, 17, 18],
        'little': [19, 20, 21, 22, 23]
    }

    results = []

    for strength in [0.0, 0.3, 0.6, 0.9]:
        print(f"\n测试抓握力度: {strength}")

        # 重置环境
        obs = env.reset()

        contact_count = 0
        total_reward = 0

        for i in range(30):
            # 创建简单抓握动作
            action = np.zeros(env.nu)

            # 应用抓握力度到所有手指
            for indices in finger_groups.values():
                for idx in indices:
                    if idx < env.nu:
                        action[idx] = strength

            # 执行步进
            obs, reward, done, info = env.step(action)

            total_reward += reward
            if info['contact']:
                contact_count += 1

            if (i + 1) % 10 == 0:
                print(f"  步 {i+1:2d}: 奖励={reward:.3f}, 距离={info['distance']:.3f}")

        results.append({
            'strength': strength,
            'avg_reward': total_reward / 30,
            'contact_rate': contact_count / 30,
            'final_distance': info['distance']
        })

        print(f"  平均奖励: {total_reward/30:.3f}")
        print(f"  接触率: {contact_count}/30 ({contact_count/30*100:.1f}%)")

    # 分析结果
    print(f"\n" + "=" * 60)
    print("抓握力度分析")
    print("=" * 60)

    best_result = max(results, key=lambda x: x['avg_reward'])
    print(f"最佳抓握力度: {best_result['strength']}")
    print(f"  平均奖励: {best_result['avg_reward']:.3f}")
    print(f"  接触率: {best_result['contact_rate']*100:.1f}%")
    print(f"  最终距离: {best_result['final_distance']:.3f}")

    return env, results


def main():
    """主函数"""
    print("Shadow Hand 抓握功能演示")
    print("=" * 60)

    print("\n选项:")
    print("1. 带可视化的增强控制器测试")
    print("2. 无可视化的简单抓握测试")
    print("3. 两者都运行")

    try:
        choice = int(input("\n请选择 (1-3): "))
    except:
        choice = 3

    if choice in [1, 3]:
        print("\n" + "=" * 60)
        env1, controller1 = test_grasp_with_viewer()

    if choice in [2, 3]:
        print("\n" + "=" * 60)
        env2, results = test_simple_grasp_without_viewer()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    print("\n进一步测试建议:")
    print("1. 运行增强控制器演示:")
    print("   python scripts/run_demo.py --controller enhanced --grasp-strength 0.7")

    print("\n2. 运行环境随机动作测试:")
    print("   python scripts/test_env.py --no-viewer --steps 100")

    print("\n3. 检查模型执行器范围:")
    print("   python scripts/inspect_model.py --model shadow_hand")


if __name__ == "__main__":
    main()