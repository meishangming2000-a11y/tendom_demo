"""
查看器管理工具模块
统一处理查看器循环，消除重复代码
"""

import time
import mujoco
from typing import Callable, Optional, Any


def run_viewer_loop(model, data,
                   duration: float = 30.0,
                   control_func: Optional[Callable] = None,
                   step_callback: Optional[Callable] = None,
                   sleep_time: float = 0.001) -> None:
    """
    运行查看器循环
    替换11个文件中的重复代码

    参数:
        model: MuJoCo 模型
        data: MuJoCo 数据
        duration: 运行持续时间（秒），如果为None则无限运行
        control_func: 控制函数，每步调用 control_func(model, data, elapsed_time)
        step_callback: 步进回调函数，每步调用 step_callback(model, data)
        sleep_time: 每步睡眠时间（秒）
    """
    print(f"启动查看器，持续时间: {duration} 秒" if duration else "启动查看器（无限运行）")

    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            start_time = time.time()
            last_print_time = start_time

            while viewer.is_running():
                current_time = time.time()
                elapsed = current_time - start_time

                # 检查持续时间限制
                if duration and elapsed >= duration:
                    print(f"\n达到时间限制 ({duration} 秒)，停止运行")
                    break

                # 每1秒打印一次剩余时间
                if duration and current_time - last_print_time > 1.0:
                    remaining = duration - elapsed
                    if remaining > 0:
                        print(f"剩余时间: {remaining:.1f} 秒", end='\r')
                    last_print_time = current_time

                # 调用控制函数（如果提供）
                if control_func is not None:
                    control_func(model, data, elapsed)

                # 执行模拟步
                mujoco.mj_step(model, data)

                # 调用步进回调（如果提供）
                if step_callback is not None:
                    step_callback(model, data)

                # 同步查看器
                viewer.sync()

                # 睡眠控制循环速度
                if sleep_time > 0:
                    time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n用户中断查看器")
    except Exception as e:
        print(f"查看器运行错误: {e}")
        raise


def run_with_simple_control(model, data,
                          control_values: Optional[list] = None,
                          duration: float = 30.0) -> None:
    """
    使用简单控制运行查看器
    适用于不需要复杂控制逻辑的场景

    参数:
        model: MuJoCo 模型
        data: MuJoCo 数据
        control_values: 控制值列表，如果为None则使用零控制
        duration: 运行持续时间（秒）
    """
    if control_values is not None:
        if len(control_values) != model.nu:
            print(f"警告: 控制值数量({len(control_values)})与执行器数量({model.nu})不匹配")
            # 调整控制值长度
            if len(control_values) < model.nu:
                control_values = control_values + [0.0] * (model.nu - len(control_values))
            else:
                control_values = control_values[:model.nu]

        def simple_control_func(m, d, elapsed):
            d.ctrl[:] = control_values

        run_viewer_loop(model, data, duration, simple_control_func)
    else:
        # 无控制，仅运行查看器
        run_viewer_loop(model, data, duration)


class ViewerManager:
    """查看器管理器类，提供更高级的控制"""

    def __init__(self, model, data, **kwargs):
        self.model = model
        self.data = data
        self.viewer = None
        self.is_running = False
        self.start_time = 0
        self.config = {
            "sleep_time": kwargs.get("sleep_time", 0.001),
            "print_interval": kwargs.get("print_interval", 1.0),
            "auto_reset": kwargs.get("auto_reset", False),
        }

    def start(self):
        """启动查看器"""
        self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
        self.is_running = True
        self.start_time = time.time()
        print("查看器已启动")

    def stop(self):
        """停止查看器"""
        if self.viewer:
            self.viewer.close()
            self.is_running = False
            print("查看器已停止")

    def run_for_duration(self, duration: float, control_func: Optional[Callable] = None):
        """
        运行指定持续时间

        参数:
            duration: 运行持续时间（秒）
            control_func: 控制函数
        """
        if not self.is_running:
            self.start()

        end_time = time.time() + duration
        last_print_time = time.time()

        try:
            while self.is_running and time.time() < end_time:
                current_time = time.time()
                elapsed = current_time - self.start_time
                remaining = end_time - current_time

                # 打印剩余时间
                if current_time - last_print_time > self.config["print_interval"]:
                    print(f"剩余时间: {remaining:.1f} 秒", end='\r')
                    last_print_time = current_time

                # 调用控制函数
                if control_func:
                    control_func(self.model, self.data, elapsed)

                # 执行模拟步
                mujoco.mj_step(self.model, self.data)

                # 同步查看器
                self.viewer.sync()

                # 睡眠
                time.sleep(self.config["sleep_time"])

            if remaining <= 0:
                print(f"\n达到时间限制 ({duration} 秒)")

        except KeyboardInterrupt:
            print("\n用户中断")
        finally:
            if self.config["auto_reset"]:
                self.reset()

    def reset(self):
        """重置模拟状态"""
        mujoco.mj_resetData(self.model, self.data)
        print("模拟已重置")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def run_viewer_with_control(model, data, control_func: Callable,
                           duration: float = 30.0, **kwargs) -> None:
    """
    运行带控制函数的查看器（便捷函数）

    参数:
        model: MuJoCo 模型
        data: MuJoCo 数据
        control_func: 控制函数
        duration: 运行持续时间
        **kwargs: 传递给 run_viewer_loop 的参数
    """
    run_viewer_loop(model, data, duration=duration,
                   control_func=control_func, **kwargs)


def create_viewer_context(model, data, **kwargs):
    """
    创建查看器上下文管理器

    参数:
        model: MuJoCo 模型
        data: MuJoCo 数据
        **kwargs: 传递给 ViewerManager 的参数

    返回:
        ViewerManager 实例（上下文管理器）
    """
    return ViewerManager(model, data, **kwargs)


if __name__ == "__main__":
    # 测试代码
    print("=== 测试查看器工具 ===")

    # 注意：这个测试需要实际的模型，这里只是演示导入
    try:
        import mujoco
        from .model_loader import load_shadow_hand_model

        print("加载测试模型...")
        model, data = load_shadow_hand_model()

        print("\n1. 测试简单查看器循环:")
        # 由于测试环境可能没有图形界面，这里只是演示
        # run_viewer_loop(model, data, duration=2.0)

        print("\n2. 测试带控制的查看器循环:")
        def test_control_func(m, d, elapsed):
            # 简单正弦波控制
            import math
            for i in range(min(5, m.nu)):
                d.ctrl[i] = 0.1 * math.sin(elapsed * 2 + i)

        # run_viewer_loop(model, data, duration=2.0, control_func=test_control_func)

        print("\n=== 测试完成（查看器测试需要图形界面）===")

    except ImportError as e:
        print(f"导入错误: {e}")
    except Exception as e:
        print(f"测试错误: {e}")