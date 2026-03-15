#!/usr/bin/env python3
"""
简单的 MuJoCo viewer 测试
验证 viewer 是否能正常显示和更新动画
"""

import sys
import os
import numpy as np
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 导入模型加载器
from src.utils import model_loader


def test_basic_viewer():
    """测试基本的 viewer 功能"""
    print("=" * 60)
    print("简单 MuJoCo viewer 测试")
    print("=" * 60)

    # 加载 Shadow Hand 模型
    print("加载模型...")
    model, data = model_loader.load_shadow_hand_model()
    print(f"模型加载成功: nq={model.nq}, nv={model.nv}, nu={model.nu}")

    # 尝试启动 viewer
    print("\n尝试启动 viewer...")
    try:
        import mujoco.viewer
        print("mujoco.viewer 导入成功")

        # 启动 viewer
        viewer = mujoco.viewer.launch(model, data)
        print("Viewer 启动成功，窗口应该已经打开")
        print("等待 2 秒让 viewer 初始化...")
        time.sleep(2.0)

        # 运行一些步进并更新 viewer
        print("\n开始运行 100 步随机动作...")
        for i in range(100):
            # 生成随机控制信号
            data.ctrl[:] = np.random.uniform(-1, 1, model.nu)

            # 执行模拟步
            mujoco.mj_step(model, data)

            # 更新 viewer
            viewer.sync()

            # 每10步打印一次
            if (i + 1) % 10 == 0:
                print(f"  已完成 {i+1} 步")

            # 短暂延迟
            time.sleep(0.01)

        print("\n测试完成，关闭 viewer...")
        viewer.close()

    except ImportError as e:
        print(f"错误: 未找到 mujoco.viewer - {e}")
        print("请确保使用 MuJoCo 3.0 或更高版本")
    except Exception as e:
        print(f"Viewer 错误: {e}")
        import traceback
        traceback.print_exc()


def test_viewer_with_env():
    """使用环境类测试 viewer"""
    print("\n" + "=" * 60)
    print("使用 ShadowGraspEnv 测试 viewer")
    print("=" * 60)

    from src.environments.shadow_grasp_env import ShadowGraspEnv

    env = ShadowGraspEnv(max_steps=50)
    print(f"环境创建成功: nu={env.nu}")

    # 重置环境
    obs = env.reset()
    print(f"重置成功，观测维度: {obs.shape}")

    try:
        import mujoco.viewer

        # 启动 viewer
        viewer = mujoco.viewer.launch(env.model, env.data)
        print("Viewer 启动成功")
        time.sleep(1.0)

        # 运行一些步进
        for i in range(50):
            action = np.random.uniform(-1, 1, env.nu)
            obs, reward, done, info = env.step(action)

            # 更新 viewer
            viewer.sync()

            if (i + 1) % 10 == 0:
                print(f"  步 {i+1}: 奖励={reward:.3f}, 距离={info['distance']:.3f}")

            time.sleep(0.01)

        viewer.close()
        print("\n测试完成")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


def check_mujoco_version():
    """检查 MuJoCo 版本"""
    print("\n" + "=" * 60)
    print("MuJoCo 版本检查")
    print("=" * 60)

    try:
        import mujoco
        print(f"MuJoCo 版本: {mujoco.__version__}")
        print(f"MuJoCo 路径: {mujoco.__file__}")

        # 检查 viewer 是否可用
        try:
            import mujoco.viewer
            print("✓ mujoco.viewer 模块可用")
        except ImportError:
            print("✗ mujoco.viewer 模块不可用")

    except Exception as e:
        print(f"导入 MuJoCo 时出错: {e}")


def main():
    """主函数"""
    print("MuJoCo Viewer 诊断测试")
    print("=" * 60)

    # 检查版本
    check_mujoco_version()

    # 运行测试
    test_option = input("\n选择测试 (1=基本viewer, 2=环境viewer, 3=两者): ").strip()

    if test_option in ['1', '3']:
        test_basic_viewer()

    if test_option in ['2', '3']:
        test_viewer_with_env()

    print("\n测试完成!")


if __name__ == "__main__":
    main()