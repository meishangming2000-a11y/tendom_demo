#!/usr/bin/env python3
"""
可视化调试脚本
帮助诊断为什么手在viewer中不动
"""

import sys
import os
import numpy as np
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.environments.shadow_grasp_env import ShadowGraspEnv


def debug_viewer_issue():
    """调试 viewer 问题"""
    print("=" * 60)
    print("可视化调试 - 诊断手不动的问题")
    print("=" * 60)

    # 创建环境
    env = ShadowGraspEnv(max_steps=100, control_timestep=0.002)
    print(f"环境创建成功:")
    print(f"  - 动作空间维度: {env.nu}")
    print(f"  - 观测空间维度: {env.get_obs().shape[0]}")

    # 重置环境
    obs = env.reset()
    print(f"\n重置成功，观测形状: {obs.shape}")

    # 初始化 viewer
    viewer = None
    try:
        import mujoco.viewer
        print("\n1. 导入 mujoco.viewer 成功")

        # 启动 viewer
        print("2. 启动 viewer...")
        viewer = mujoco.viewer.launch(env.model, env.data)
        print("   Viewer 启动成功，窗口应该已打开")

        # 等待 viewer 初始化
        print("3. 等待 viewer 初始化 (3秒)...")
        time.sleep(3.0)

        # 测试直接控制
        print("\n4. 测试直接控制 (不通过 env.step):")
        for i in range(20):
            # 直接设置控制信号并步进
            env.data.ctrl[:] = np.random.uniform(-1, 1, env.nu)
            mujoco.mj_step(env.model, env.data)

            # 更新 viewer
            viewer.sync()
            print(f"   直接控制步 {i+1}: viewer.sync() 调用成功")

            time.sleep(0.05)

        # 测试通过 env.step
        print("\n5. 测试通过 env.step (10步):")
        for i in range(10):
            action = np.random.uniform(-1, 1, env.nu)

            # 记录步进前的状态
            before_qpos = env.data.qpos.copy()[:5]  # 前5个关节位置
            before_hand_pos = env._get_hand_position()

            # 执行步进
            obs, reward, done, info = env.step(action)

            # 记录步进后的状态
            after_qpos = env.data.qpos.copy()[:5]
            after_hand_pos = env._get_hand_position()

            # 检查状态是否变化
            qpos_changed = not np.allclose(before_qpos, after_qpos, atol=0.001)
            hand_pos_changed = not np.allclose(before_hand_pos, after_hand_pos, atol=0.001)

            print(f"   步 {i+1}:")
            print(f"     动作范围: [{action.min():.3f}, {action.max():.3f}]")
            print(f"     控制信号范围: [{env.data.ctrl.min():.3f}, {env.data.ctrl.max():.3f}]")
            print(f"     关节位置变化: {'是' if qpos_changed else '否'}")
            print(f"     手部位置变化: {'是' if hand_pos_changed else '否'}")
            print(f"     奖励: {reward:.3f}, 距离: {info['distance']:.3f}")

            # 更新 viewer
            viewer.sync()
            print(f"     viewer.sync() 完成")

            time.sleep(0.1)

        # 检查 viewer 是否仍然响应
        print("\n6. 检查 viewer 响应性 (5步慢速更新):")
        for i in range(5):
            action = np.random.uniform(-1, 1, env.nu)
            obs, reward, done, info = env.step(action)

            # 更长的延迟，观察窗口是否更新
            print(f"   慢速步 {i+1}: 等待 0.5 秒...")
            viewer.sync()
            time.sleep(0.5)

        print("\n7. 测试完成")

    except ImportError as e:
        print(f"\n错误: 未找到 mujoco.viewer - {e}")
        print("请确保使用 MuJoCo 3.0 或更高版本")
    except Exception as e:
        print(f"\nViewer 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if viewer:
            try:
                viewer.close()
                print("Viewer 已关闭")
            except:
                pass

    # 额外的诊断信息
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    # 检查动作归一化
    print("\n动作归一化测试:")
    test_actions = [
        ("全零", np.zeros(env.nu)),
        ("全0.5", np.full(env.nu, 0.5)),
        ("全-0.5", np.full(env.nu, -0.5)),
    ]

    for name, action in test_actions:
        ctrl = env._normalize_action(action)
        print(f"  {name}: action→ctrl [{ctrl[0]:.3f}, ..., {ctrl[-1]:.3f}]")

    # 检查模拟是否真的在运行
    print("\n模拟状态检查:")
    initial_hand_pos = env._get_hand_position()
    print(f"  初始手部位置: {initial_hand_pos}")

    # 运行几步并检查位置变化
    for i in range(3):
        action = np.random.uniform(-1, 1, env.nu)
        obs, reward, done, info = env.step(action)
        hand_pos = env._get_hand_position()
        print(f"  步 {i+1} 后手部位置: {hand_pos}")

    print("\n如果手在viewer中不动，但上面的位置在变化，说明:")
    print("  - 模拟正在运行 ✓")
    print("  - viewer 更新可能有问题 ✗")
    print("\n如果位置也没有变化，说明:")
    print("  - 动作可能没有正确应用")
    print("  - 控制信号可能太小")


def check_mujoco_viewer_details():
    """检查 MuJoCo viewer 的详细信息"""
    print("\n" + "=" * 60)
    print("MuJoCo Viewer 详细信息")
    print("=" * 60)

    try:
        import mujoco
        print(f"MuJoCo 版本: {mujoco.__version__}")

        # 尝试获取更多版本信息
        try:
            import mujoco.viewer
            print(f"mujoco.viewer 模块: 可用")

            # 检查 viewer 的具体函数
            import inspect
            viewer_funcs = [name for name in dir(mujoco.viewer) if not name.startswith('_')]
            print(f"viewer 函数: {', '.join(viewer_funcs[:5])}...")
        except ImportError:
            print("mujoco.viewer 模块: 不可用")

    except Exception as e:
        print(f"检查 MuJoCo 时出错: {e}")


if __name__ == "__main__":
    # 检查 MuJoCo 详情
    check_mujoco_viewer_details()

    # 运行调试
    debug_viewer_issue()

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)
    print("\n运行以下命令测试:")
    print("1. 基本 viewer 测试:")
    print("   python scripts/test_viewer_simple.py")
    print("\n2. 原始测试脚本 (无viewer):")
    print("   python scripts/test_env.py --no-viewer --steps 50")
    print("\n3. 原始测试脚本 (有viewer):")
    print("   python scripts/test_env.py --steps 50")