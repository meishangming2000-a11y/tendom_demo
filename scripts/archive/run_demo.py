#!/usr/bin/env python3
"""
统一演示启动器

用法:
    python run_demo.py --controller linear --duration 30
    python run_demo.py --controller bio --interactive
    python run_demo.py --controller enhanced --mode force_hybrid
"""

import argparse
import time
import mujoco
import mujoco.viewer
import numpy as np
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils import model_loader
from src.controllers import create_controller, get_available_controllers


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行MuJoCo肌腱控制演示')

    # 控制器选择
    parser.add_argument('--controller', type=str, default='linear',
                       choices=['linear', 'bio', 'enhanced'],
                       help='选择控制器类型')

    # 演示参数
    parser.add_argument('--duration', type=float, default=30.0,
                       help='演示持续时间（秒）')
    parser.add_argument('--model', type=str, default='shadow_hand',
                       choices=['shadow_hand', 'arm26', 'tendon'],
                       help='选择模型类型')

    # 控制器特定参数
    parser.add_argument('--amplitude', type=float, default=0.3,
                       help='控制幅度（线性控制器）')
    parser.add_argument('--grasp-strength', type=float, default=0.5,
                       help='抓取力度（增强控制器）')
    parser.add_argument('--mode', type=str, default='position',
                       choices=['position', 'force_hybrid'],
                       help='控制模式（增强控制器）')

    # 交互选项
    parser.add_argument('--interactive', action='store_true',
                       help='启用交互模式（如果支持）')
    parser.add_argument('--auto', action='store_true',
                       help='自动演示模式')

    # 输出选项
    parser.add_argument('--verbose', action='store_true',
                       help='详细输出')
    parser.add_argument('--stats-interval', type=float, default=5.0,
                       help='统计信息打印间隔（秒）')

    return parser.parse_args()


def load_model(model_type):
    """加载指定类型的模型"""
    try:
        if model_type == 'shadow_hand':
            model, data = model_loader.load_shadow_hand_model()
        elif model_type == 'arm26':
            model, data = model_loader.load_arm26_model()
        elif model_type == 'tendon':
            model, data = model_loader.load_tendon_model()
        else:
            raise ValueError(f"未知的模型类型: {model_type}")

        return model, data
    except FileNotFoundError as e:
        print(f"错误: 模型文件未找到")
        print(f"详情: {e}")
        print("\n请确保:")
        print("1. 模型文件存在于 models/ 目录")
        print("2. 路径配置正确（检查 src/utils/path_utils.py）")
        sys.exit(1)
    except Exception as e:
        print(f"模型加载错误: {e}")
        sys.exit(1)


def create_controller_with_args(controller_name, model, data, args):
    """根据参数创建控制器"""
    kwargs = {}

    if controller_name == 'linear':
        kwargs['control_amplitude'] = args.amplitude
    elif controller_name == 'enhanced':
        kwargs['force_feedback_gain'] = 0.1
        # 其他参数通过 compute_control 传递

    return create_controller(controller_name, model, data, **kwargs)


def run_demo(args):
    """运行主演示循环"""
    print("=" * 60)
    print(f"MuJoCo 肌腱控制演示")
    print(f"控制器: {args.controller}")
    print(f"模型: {args.model}")
    print(f"持续时间: {args.duration}秒")
    print("=" * 60)

    # 加载模型
    print(f"\n正在加载 {args.model} 模型...")
    model, data = load_model(args.model)
    model_loader.print_model_info(model, data)

    # 创建控制器
    print(f"\n创建 {args.controller} 控制器...")
    controller = create_controller_with_args(args.controller, model, data, args)
    controller.print_info()

    # 启动查看器
    print("\n启动 MuJoCo 查看器...")
    print("按 Ctrl+C 或关闭窗口停止演示")

    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            print("查看器已启动")
            if args.interactive:
                print("交互模式已启用")
                print("（注意：基础交互模式，高级交互请运行 src/demos/interactive_grasp.py）")

            # 演示循环
            start_time = time.time()
            last_stats_time = start_time

            while viewer.is_running() and (time.time() - start_time) < args.duration:
                current_time = time.time() - start_time

                # 准备控制器参数
                control_kwargs = {}

                if args.controller == 'linear':
                    # 线性控制器：基于时间的自动进度
                    pass
                elif args.controller == 'bio':
                    # 仿生控制器：基于时间的自动进度
                    pass
                elif args.controller == 'enhanced':
                    # 增强控制器
                    control_kwargs['grasp_strength'] = args.grasp_strength
                    control_kwargs['control_mode'] = args.mode

                    # 简单的自动抓取循环
                    if args.auto:
                        cycle_time = current_time % 10.0
                        if cycle_time < 4.0:
                            control_kwargs['grasp_strength'] = cycle_time / 4.0
                        elif cycle_time < 7.0:
                            control_kwargs['grasp_strength'] = 1.0
                        else:
                            control_kwargs['grasp_strength'] = (10.0 - cycle_time) / 3.0

                # 应用控制
                controller.apply_control(current_time, **control_kwargs)

                # 模拟步进
                mujoco.mj_step(model, data)
                viewer.sync()

                # 短暂延迟
                time.sleep(0.001)

                # 定期打印统计信息
                if args.verbose and (current_time - last_stats_time) >= args.stats_interval:
                    stats = controller.get_control_stats()
                    print(f"\n时间: {current_time:.1f}s")
                    print(f"控制统计: {stats}")
                    last_stats_time = current_time

            print("\n演示完成")

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"运行时错误: {e}")
        import traceback
        traceback.print_exc()

    # 打印最终统计信息
    print("\n" + "=" * 60)
    print("演示统计信息:")
    stats = controller.get_control_stats()
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                if isinstance(subvalue, (int, float)):
                    print(f"    {subkey}: {subvalue:.4f}")
    print("=" * 60)


def main():
    """主函数"""
    args = parse_args()

    # 检查控制器可用性
    available = get_available_controllers()
    if args.controller not in available:
        print(f"错误: 控制器 '{args.controller}' 不可用")
        print(f"可用的控制器: {list(available.keys())}")
        sys.exit(1)

    # 运行演示
    run_demo(args)


if __name__ == "__main__":
    main()