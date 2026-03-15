"""
控制器基类 - 定义所有控制器的统一接口

设计目标:
1. 统一接口: 所有控制器必须实现 compute_control() 方法
2. 可对比性: 相同接口便于性能对比
3. 可扩展性: 新控制器只需继承基类并实现一个方法
4. 接口隔离: 为"换成自家手"做准备
"""

import numpy as np
import mujoco
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod


class BaseController(ABC):
    """
    控制器基类 - 所有具体控制器的父类
    """

    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData):
        """
        初始化控制器

        参数:
            model: MuJoCo 模型
            data: MuJoCo 数据
        """
        self.model = model
        self.data = data
        self.nu = model.nu

        # 执行器信息
        self.ctrl_ranges = model.actuator_ctrlrange  # shape: (nu, 2)
        self.ctrl_limited = model.actuator_ctrllimited  # shape: (nu,)

        # 手指分组（基于Shadow Hand的默认分组，子类可覆盖）
        self.finger_groups = self._create_default_finger_groups()

        # 控制状态
        self.is_active = True
        self.control_history = []
        self.max_history_size = 1000

    def _create_default_finger_groups(self) -> Dict[str, List[int]]:
        """
        创建默认的手指分组（针对Shadow Hand）
        子类可以覆盖此方法以适应不同的手部模型
        """
        return {
            'wrist': [0, 1],      # 手腕关节
            'thumb': [2, 3, 4, 5, 6],  # 拇指
            'index': [7, 8, 9, 10],    # 食指
            'middle': [11, 12, 13, 14], # 中指
            'ring': [15, 16, 17, 18],   # 无名指
            'little': [19, 20, 21, 22, 23]  # 小指
        }

    @abstractmethod
    def compute_control(self, t: float, **kwargs) -> np.ndarray:
        """
        计算控制输出 - 必须由子类实现

        参数:
            t: 当前时间（秒）
            **kwargs: 额外的控制参数

        返回:
            control_values: 形状为 (nu,) 的控制值数组
        """
        pass

    def reset(self):
        """
        重置控制器状态
        """
        self.control_history.clear()
        self.data.ctrl[:] = 0.0

    def apply_control(self, t: float, **kwargs):
        """
        应用控制到模型（调用 compute_control 并更新 data.ctrl）

        参数:
            t: 当前时间
            **kwargs: 传递给 compute_control 的参数
        """
        if not self.is_active:
            return

        control_values = self.compute_control(t, **kwargs)

        # 确保控制值形状正确
        if control_values.shape != (self.nu,):
            raise ValueError(f"控制值形状应为 ({self.nu},)，但得到 {control_values.shape}")

        # 应用控制值
        self.data.ctrl[:] = control_values

        # 记录控制历史
        self.control_history.append({
            'time': t,
            'control': control_values.copy(),
            'kwargs': kwargs.copy() if kwargs else {}
        })

        # 限制历史大小
        if len(self.control_history) > self.max_history_size:
            self.control_history = self.control_history[-self.max_history_size:]

    def set_finger_group(self, group_name: str, value: float,
                         use_range_fraction: float = 0.5):
        """
        设置手指组的控制值（通用辅助方法）

        参数:
            group_name: 手指组名称
            value: 控制值（0-1）
            use_range_fraction: 使用执行器范围的比例（0-1）
        """
        if group_name not in self.finger_groups:
            raise KeyError(f"未知的手指组: {group_name}。可选: {list(self.finger_groups.keys())}")

        for idx in self.finger_groups[group_name]:
            if idx < self.nu:
                self._set_actuator(idx, value, use_range_fraction)

    def _set_actuator(self, index: int, progress: float,
                     use_range_fraction: float = 0.5):
        """
        设置单个执行器的控制值（通用辅助方法）
        """
        if index < self.nu:
            if self.ctrl_limited[index]:
                ctrl_min, ctrl_max = self.ctrl_ranges[index]
                # 对于有负值的范围，我们通常想要向正方向运动（弯曲）
                if ctrl_min < 0:
                    # 使用范围的上半部分（从0到正方向）
                    target_value = max(0, ctrl_min + (ctrl_max - ctrl_min) * use_range_fraction)
                else:
                    target_value = ctrl_min + (ctrl_max - ctrl_min) * use_range_fraction
                self.data.ctrl[index] = progress * target_value
            else:
                self.data.ctrl[index] = progress * 0.3

    def get_control_stats(self) -> Dict[str, Any]:
        """
        获取控制统计信息

        返回:
            包含控制统计信息的字典
        """
        if not self.control_history:
            return {
                'total_controls': 0,
                'avg_control_magnitude': 0.0,
                'control_range': (0.0, 0.0)
            }

        controls = np.array([h['control'] for h in self.control_history])

        return {
            'total_controls': len(self.control_history),
            'avg_control_magnitude': np.mean(np.abs(controls)),
            'control_range': (float(np.min(controls)), float(np.max(controls))),
            'finger_group_stats': self._get_finger_group_stats(controls)
        }

    def _get_finger_group_stats(self, controls: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        获取各手指组的控制统计信息
        """
        stats = {}
        for group_name, indices in self.finger_groups.items():
            if indices:
                group_controls = controls[:, indices]
                stats[group_name] = {
                    'avg_magnitude': float(np.mean(np.abs(group_controls))),
                    'min': float(np.min(group_controls)),
                    'max': float(np.max(group_controls)),
                    'std': float(np.std(group_controls))
                }
        return stats

    def print_info(self):
        """
        打印控制器信息
        """
        print(f"控制器: {self.__class__.__name__}")
        print(f"执行器数量: {self.nu}")
        print(f"手指分组: {list(self.finger_groups.keys())}")
        print(f"历史记录: {len(self.control_history)} 条")

        for group_name, indices in self.finger_groups.items():
            if indices:
                print(f"  {group_name}: {len(indices)} 个执行器 (索引: {indices})")

    def __call__(self, t: float, **kwargs):
        """
        使控制器可调用，等价于 apply_control
        """
        return self.apply_control(t, **kwargs)