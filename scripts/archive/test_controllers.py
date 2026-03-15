#!/usr/bin/env python3
"""
控制器对比测试脚本

功能:
1. 对比不同控制器的性能指标
2. 生成控制统计报告
3. 可视化控制轨迹
"""

import time
import argparse
import numpy as np
import os
import sys
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils import model_loader
from src.controllers import get_available_controllers, create_controller


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='控制器对比测试')

    parser.add_argument('--controllers', type=str, nargs='+',
                       default=['linear', 'bio', 'enhanced'],
                       help='要测试的控制器列表')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='每个控制器测试持续时间（秒）')
    parser.add_argument('--model', type=str, default='shadow_hand',
                       choices=['shadow_hand', 'arm26', 'tendon'],
                       help='测试使用的模型')
    parser.add_argument('--output', type=str, default='console',
                       choices=['console', 'json', 'csv'],
                       help='输出格式')
    parser.add_argument('--visualize', action='store_true',
                       help='启用可视化（需要matplotlib）')

    return parser.parse_args()


class ControllerTester:
    """控制器测试器"""

    def __init__(self, model_type='shadow_hand'):
        self.model_type = model_type
        self.model = None
        self.data = None
        self.results = {}

    def setup(self):
        """设置测试环境"""
        print(f"正在加载 {self.model_type} 模型...")
        if self.model_type == 'shadow_hand':
            self.model, self.data = model_loader.load_shadow_hand_model()
        elif self.model_type == 'arm26':
            self.model, self.data = model_loader.load_arm26_model()
        elif self.model_type == 'tendon':
            self.model, self.data = model_loader.load_tendon_model()

        model_loader.print_model_info(self.model, self.data)
        print()

    def test_controller(self, controller_name: str, duration: float) -> Dict[str, Any]:
        """
        测试单个控制器

        参数:
            controller_name: 控制器名称
            duration: 测试持续时间

        返回:
            测试结果字典
        """
        print(f"测试控制器: {controller_name}")

        # 创建控制器
        try:
            controller = create_controller(controller_name, self.model, self.data)
        except Exception as e:
            print(f"  错误: 无法创建控制器 {controller_name}: {e}")
            return {
                'controller': controller_name,
                'success': False,
                'error': str(e)
            }

        # 重置控制器状态
        controller.reset()
        self.data.ctrl[:] = 0.0

        # 测试参数
        start_time = time.time()
        control_history = []
        time_history = []

        # 测试循环（无查看器）
        test_start = time.time()
        while (time.time() - test_start) < duration:
            current_time = time.time() - test_start

            # 准备控制器参数
            control_kwargs = self._get_control_kwargs(controller_name, current_time)

            # 应用控制
            controller.apply_control(current_time, **control_kwargs)

            # 记录数据
            control_history.append(self.data.ctrl.copy())
            time_history.append(current_time)

            # 模拟步进（无查看器）
            mujoco.mj_step(self.model, self.data)

            # 短暂延迟以控制速度
            time.sleep(0.001)

        # 收集结果
        control_array = np.array(control_history)
        time_array = np.array(time_history)

        # 计算统计指标
        stats = controller.get_control_stats()
        test_stats = self._compute_test_stats(control_array, time_array)

        result = {
            'controller': controller_name,
            'success': True,
            'duration': duration,
            'total_steps': len(control_history),
            'controller_stats': stats,
            'test_stats': test_stats,
            'control_trajectory': control_array,
            'time_points': time_array
        }

        print(f"  完成: {len(control_history)} 步")
        print(f"  平均控制幅度: {test_stats['avg_control_magnitude']:.4f}")
        print(f"  控制变化率: {test_stats['control_variance']:.4f}")
        print()

        return result

    def _get_control_kwargs(self, controller_name: str, t: float) -> Dict[str, Any]:
        """获取控制器参数"""
        if controller_name == 'linear':
            # 线性控制器：正弦波进度
            return {'progress': 0.5 + 0.5 * np.sin(t)}
        elif controller_name == 'bio':
            # 仿生控制器：正弦波进度
            return {'progress': 0.5 + 0.5 * np.sin(t * 0.8)}
        elif controller_name == 'enhanced':
            # 增强控制器：自动抓取循环
            cycle_time = t % 8.0
            if cycle_time < 3.0:
                grasp_strength = cycle_time / 3.0
            elif cycle_time < 5.0:
                grasp_strength = 1.0
            else:
                grasp_strength = (8.0 - cycle_time) / 3.0

            return {
                'grasp_strength': grasp_strength,
                'control_mode': 'force_hybrid'
            }
        else:
            return {}

    def _compute_test_stats(self, control_array: np.ndarray,
                           time_array: np.ndarray) -> Dict[str, float]:
        """计算测试统计指标"""
        if len(control_array) == 0:
            return {}

        # 基本统计
        avg_magnitude = np.mean(np.abs(control_array))
        control_variance = np.var(control_array)

        # 变化率（导数近似）
        if len(control_array) > 1:
            control_diff = np.diff(control_array, axis=0)
            time_diff = np.diff(time_array)
            if np.any(time_diff > 0):
                control_rate = np.mean(np.abs(control_diff / time_diff[:, np.newaxis]))
            else:
                control_rate = 0.0
        else:
            control_rate = 0.0

        # 能量消耗（控制值的平方和）
        energy = np.sum(control_array ** 2)

        return {
            'avg_control_magnitude': float(avg_magnitude),
            'control_variance': float(control_variance),
            'control_rate': float(control_rate),
            'energy_consumption': float(energy),
            'max_control': float(np.max(control_array)),
            'min_control': float(np.min(control_array))
        }

    def run_tests(self, controller_names: List[str], duration: float):
        """运行所有控制器测试"""
        self.results = {}
        for name in controller_names:
            result = self.test_controller(name, duration)
            self.results[name] = result

    def print_results(self, output_format='console'):
        """打印测试结果"""
        if output_format == 'console':
            self._print_console_results()
        elif output_format == 'json':
            self._print_json_results()
        elif output_format == 'csv':
            self._print_csv_results()

    def _print_console_results(self):
        """打印控制台格式结果"""
        print("\n" + "=" * 80)
        print("控制器对比测试结果")
        print("=" * 80)

        for controller_name, result in self.results.items():
            if not result['success']:
                print(f"\n控制器: {controller_name}")
                print(f"  状态: 失败")
                print(f"  错误: {result['error']}")
                continue

            print(f"\n控制器: {controller_name}")
            print(f"  状态: 成功")
            print(f"  测试时长: {result['duration']}秒")
            print(f"  总步数: {result['total_steps']}")

            test_stats = result['test_stats']
            print(f"  测试统计:")
            for key, value in test_stats.items():
                print(f"    {key}: {value:.6f}")

            controller_stats = result['controller_stats']
            print(f"  控制器统计:")
            print(f"    总控制次数: {controller_stats['total_controls']}")
            print(f"    平均控制幅度: {controller_stats['avg_control_magnitude']:.6f}")
            print(f"    控制范围: [{controller_stats['control_range'][0]:.6f}, "
                  f"{controller_stats['control_range'][1]:.6f}]")

        # 比较结果
        print("\n" + "-" * 80)
        print("性能比较")
        print("-" * 80)

        successful_results = {k: v for k, v in self.results.items() if v['success']}
        if not successful_results:
            print("无成功测试结果")
            return

        # 比较关键指标
        metrics = ['avg_control_magnitude', 'control_variance', 'energy_consumption']
        for metric in metrics:
            print(f"\n{metric}:")
            sorted_controllers = sorted(
                successful_results.items(),
                key=lambda x: x[1]['test_stats'].get(metric, 0)
            )
            for controller_name, result in sorted_controllers:
                value = result['test_stats'].get(metric, 0)
                print(f"  {controller_name}: {value:.6f}")

    def _print_json_results(self):
        """打印JSON格式结果（简化版）"""
        import json
        print(json.dumps(self.results, indent=2, default=str))

    def _print_csv_results(self):
        """打印CSV格式结果"""
        print("controller,success,duration,total_steps,avg_magnitude,variance,energy")
        for controller_name, result in self.results.items():
            if result['success']:
                test_stats = result['test_stats']
                line = f"{controller_name},true,{result['duration']},{result['total_steps']},"
                line += f"{test_stats.get('avg_control_magnitude', 0)},"
                line += f"{test_stats.get('control_variance', 0)},"
                line += f"{test_stats.get('energy_consumption', 0)}"
            else:
                line = f"{controller_name},false,0,0,0,0,0"
            print(line)


def main():
    """主函数"""
    args = parse_args()

    # 检查控制器可用性
    available = get_available_controllers()
    valid_controllers = []
    for controller in args.controllers:
        if controller in available:
            valid_controllers.append(controller)
        else:
            print(f"警告: 控制器 '{controller}' 不可用，跳过")

    if not valid_controllers:
        print("错误: 没有可用的控制器进行测试")
        print(f"可用的控制器: {list(available.keys())}")
        return

    # 运行测试
    tester = ControllerTester(args.model)
    tester.setup()
    tester.run_tests(valid_controllers, args.duration)
    tester.print_results(args.output)

    # 可视化（可选）
    if args.visualize:
        try:
            import matplotlib.pyplot as plt
            visualize_results(tester.results)
        except ImportError:
            print("警告: matplotlib 未安装，跳过可视化")
            print("安装: pip install matplotlib")


def visualize_results(results):
    """可视化测试结果"""
    import matplotlib.pyplot as plt

    successful_results = {k: v for k, v in results.items() if v['success']}
    if not successful_results:
        return

    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('控制器性能对比')

    # 1. 控制轨迹（第一个执行器）
    ax = axes[0, 0]
    for controller_name, result in successful_results.items():
        control_trajectory = result['control_trajectory']
        time_points = result['time_points']
        if len(control_trajectory) > 0:
            ax.plot(time_points, control_trajectory[:, 0],
                   label=controller_name, alpha=0.7)
    ax.set_xlabel('时间 (s)')
    ax.set_ylabel('控制值 (第一个执行器)')
    ax.set_title('控制轨迹')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. 平均控制幅度
    ax = axes[0, 1]
    controller_names = []
    avg_magnitudes = []
    for controller_name, result in successful_results.items():
        controller_names.append(controller_name)
        avg_magnitudes.append(result['test_stats']['avg_control_magnitude'])
    ax.bar(controller_names, avg_magnitudes)
    ax.set_xlabel('控制器')
    ax.set_ylabel('平均控制幅度')
    ax.set_title('控制幅度对比')
    ax.grid(True, alpha=0.3)

    # 3. 控制方差
    ax = axes[1, 0]
    controller_names = []
    variances = []
    for controller_name, result in successful_results.items():
        controller_names.append(controller_name)
        variances.append(result['test_stats']['control_variance'])
    ax.bar(controller_names, variances)
    ax.set_xlabel('控制器')
    ax.set_ylabel('控制方差')
    ax.set_title('控制稳定性对比')
    ax.grid(True, alpha=0.3)

    # 4. 能量消耗
    ax = axes[1, 1]
    controller_names = []
    energies = []
    for controller_name, result in successful_results.items():
        controller_names.append(controller_name)
        energies.append(result['test_stats']['energy_consumption'])
    ax.bar(controller_names, energies)
    ax.set_xlabel('控制器')
    ax.set_ylabel('能量消耗')
    ax.set_title('能量效率对比')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()