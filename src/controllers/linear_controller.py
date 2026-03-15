"""
线性控制器 - 简单的线性渐变控制

功能特点:
1. 所有执行器同步线性渐变
2. 支持周期性握紧/松开循环
3. 简单的开环控制
"""

import numpy as np
import mujoco
from typing import Dict, Any, Optional
from .base_controller import BaseController


class LinearController(BaseController):
    """
    线性控制器 - 所有执行器同步线性渐变
    """

    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData,
                 control_amplitude: float = 0.3, **kwargs):
        """
        初始化线性控制器

        参数:
            model: MuJoCo 模型
            data: MuJoCo 数据
            control_amplitude: 控制幅度（默认0.3）
            **kwargs: 传递给基类的参数
        """
        super().__init__(model, data, **kwargs)
        self.control_amplitude = control_amplitude

        # 控制状态
        self.current_progress = 0.0
        self.current_direction = 1  # 1: 增加, -1: 减少
        self.cycle_count = 0

        # 控制参数
        self.close_duration = 3.0  # 握紧时间（秒）
        self.open_duration = 3.0   # 松开时间（秒）
        self.hold_duration = 1.0   # 保持时间（秒）

    def compute_control(self, t: float, **kwargs) -> np.ndarray:
        """
        计算线性控制输出

        参数:
            t: 当前时间（秒）
            **kwargs: 额外的控制参数，支持:
                - progress: 直接指定进度值（0-1），覆盖内部计算
                - direction: 方向（1: 握紧, -1: 松开）
                - amplitude: 控制幅度

        返回:
            control_values: 形状为 (nu,) 的控制值数组
        """
        # 处理参数
        amplitude = kwargs.get('amplitude', self.control_amplitude)
        manual_progress = kwargs.get('progress')

        if manual_progress is not None:
            # 使用手动指定的进度
            progress = np.clip(manual_progress, 0.0, 1.0)
        else:
            # 自动计算基于时间的进度
            direction = kwargs.get('direction', self.current_direction)
            progress = self._compute_auto_progress(t, direction)

        # 生成线性控制值
        control_values = np.ones(self.nu) * progress * amplitude

        # 更新内部状态
        self.current_progress = progress

        return control_values

    def _compute_auto_progress(self, t: float, direction: int) -> float:
        """
        计算基于时间的自动进度

        参数:
            t: 当前时间
            direction: 方向（1: 握紧, -1: 松开）

        返回:
            progress: 进度值（0-1）
        """
        # 简化版本：基于时间的正弦波
        # 实际上，更复杂的控制器可以跟踪循环状态
        cycle_duration = self.close_duration + self.hold_duration + self.open_duration + self.hold_duration
        if cycle_duration == 0:
            return 0.0

        # 计算当前周期内的归一化时间
        t_in_cycle = t % cycle_duration

        if t_in_cycle < self.close_duration:
            # 握紧阶段
            return t_in_cycle / self.close_duration
        elif t_in_cycle < self.close_duration + self.hold_duration:
            # 保持握紧阶段
            return 1.0
        elif t_in_cycle < self.close_duration + self.hold_duration + self.open_duration:
            # 松开阶段
            t_in_open = t_in_cycle - (self.close_duration + self.hold_duration)
            return 1.0 - (t_in_open / self.open_duration)
        else:
            # 保持松开阶段
            return 0.0

    def set_cycle_parameters(self, close_duration: float = 3.0,
                            open_duration: float = 3.0,
                            hold_duration: float = 1.0):
        """
        设置循环参数

        参数:
            close_duration: 握紧时间（秒）
            open_duration: 松开时间（秒）
            hold_duration: 保持时间（秒）
        """
        self.close_duration = close_duration
        self.open_duration = open_duration
        self.hold_duration = hold_duration

    def get_state_info(self) -> Dict[str, Any]:
        """
        获取控制器状态信息

        返回:
            包含状态信息的字典
        """
        base_stats = super().get_control_stats()

        return {
            **base_stats,
            'controller_type': 'linear',
            'control_amplitude': self.control_amplitude,
            'current_progress': self.current_progress,
            'close_duration': self.close_duration,
            'open_duration': self.open_duration,
            'hold_duration': self.hold_duration
        }

    def print_info(self):
        """
        打印控制器信息
        """
        super().print_info()
        print(f"控制幅度: {self.control_amplitude}")
        print(f"循环参数: 握紧={self.close_duration}s, "
              f"松开={self.open_duration}s, 保持={self.hold_duration}s")
        print(f"当前进度: {self.current_progress:.3f}")