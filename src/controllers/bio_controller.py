"""
仿生控制器 - 生物启发的手指协调控制

功能特点:
1. 关节类型自动识别和分类
2. 仿生握紧序列：近端关节先动，远端关节后动
3. 拇指特殊处理
4. 基于关节范围的智能控制
"""

import numpy as np
import mujoco
from typing import Dict, List, Optional, Any
from .base_controller import BaseController


class BioHandController(BaseController):
    """
    仿生控制器 - 模拟生物手指协调运动
    """

    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData,
                 use_range_fraction: float = 0.6, **kwargs):
        """
        初始化仿生控制器

        参数:
            model: MuJoCo 模型
            data: MuJoCo 数据
            use_range_fraction: 使用执行器范围的比例（0-1）
            **kwargs: 传递给基类的参数
        """
        super().__init__(model, data, **kwargs)
        self.use_range_fraction = use_range_fraction

        # 关节类型分组（基于控制范围特征）
        self.joint_types = {
            'knuckle': [],      # 指根关节（外展/内收）
            'proximal': [],     # 近端指节（弯曲）
            'middle_distal': [], # 中段和远端指节（弯曲）
            'thumb_special': []  # 拇指特殊关节
        }

        # 阶段权重（仿生握紧序列）
        self.phase_weights = {
            'wrist': 0.1,           # 手腕轻微调整
            'thumb_special': 0.8,   # 拇指对掌
            'knuckle': 0.6,         # 指根内收
            'proximal': 1.0,        # 近端指节弯曲
            'middle_distal': 0.7    # 中远端指节弯曲（稍晚）
        }

        # 自动识别关节类型
        self._classify_joints()

        # 控制状态
        self.current_overall_progress = 0.0

    def _classify_joints(self):
        """根据控制范围自动识别关节类型"""
        for i in range(self.nu):
            if self.ctrl_limited[i]:
                ctrl_min, ctrl_max = self.ctrl_ranges[i]

                # 根据范围特征分类
                if ctrl_min < -0.3 and ctrl_max > 0.3:
                    # 双向范围较大的关节（如手腕、拇指基部）
                    if i in self.finger_groups['wrist']:
                        pass  # 手腕关节，不单独分类
                    elif i in self.finger_groups['thumb']:
                        self.joint_types['thumb_special'].append(i)
                elif abs(ctrl_min) < 0.1 and ctrl_max > 1.0:
                    # 主要是正向弯曲的关节（近端指节）
                    self.joint_types['proximal'].append(i)
                elif ctrl_min >= -0.4 and ctrl_max <= 0.4:
                    # 小范围双向关节（指根外展/内收）
                    self.joint_types['knuckle'].append(i)
                elif ctrl_min >= 0 and ctrl_max > 2.0:
                    # 大范围正向关节（中段和远端指节）
                    self.joint_types['middle_distal'].append(i)

        # 打印分类结果
        print(f"仿生控制器关节分类完成:")
        for joint_type, indices in self.joint_types.items():
            if indices:
                print(f"  {joint_type}: {len(indices)} 个执行器")

    def compute_control(self, t: float, **kwargs) -> np.ndarray:
        """
        计算仿生控制输出

        参数:
            t: 当前时间（秒）
            **kwargs: 额外的控制参数，支持:
                - progress: 整体进度值（0-1），覆盖内部计算
                - phase_weights: 阶段权重字典
                - use_range_fraction: 范围使用比例

        返回:
            control_values: 形状为 (nu,) 的控制值数组
        """
        # 处理参数
        manual_progress = kwargs.get('progress')
        phase_weights = kwargs.get('phase_weights', self.phase_weights)
        use_range_fraction = kwargs.get('use_range_fraction', self.use_range_fraction)

        if manual_progress is not None:
            # 使用手动指定的进度
            overall_progress = np.clip(manual_progress, 0.0, 1.0)
        else:
            # 基于时间的自动进度（简单正弦波）
            overall_progress = 0.5 + 0.5 * np.sin(t * 0.5)  # 0到1之间变化

        # 应用仿生握紧序列
        control_values = self._bio_grasp_sequence(
            overall_progress, phase_weights, use_range_fraction
        )

        # 更新内部状态
        self.current_overall_progress = overall_progress

        return control_values

    def _bio_grasp_sequence(self, overall_progress: float,
                           phase_weights: Optional[Dict[str, float]] = None,
                           use_range_fraction: float = 0.6) -> np.ndarray:
        """
        仿生握紧序列核心算法

        参数:
            overall_progress: 整体进度（0-1）
            phase_weights: 阶段权重字典
            use_range_fraction: 范围使用比例

        返回:
            control_values: 控制值数组
        """
        if phase_weights is None:
            phase_weights = self.phase_weights

        # 初始化控制值为0
        control_values = np.zeros(self.nu)

        # 计算各阶段的进度并设置控制值
        for joint_type, weight in phase_weights.items():
            phase_progress = overall_progress * weight
            if phase_progress > 1.0:
                phase_progress = 1.0

            # 设置该关节类型的控制值
            if joint_type in self.joint_types:
                for idx in self.joint_types[joint_type]:
                    control_values[idx] = self._compute_actuator_value(
                        idx, phase_progress, use_range_fraction
                    )

        # 特别处理拇指：在握紧后期增加拇指弯曲
        if 'thumb' in self.finger_groups:
            thumb_progress = overall_progress * 1.2
            if thumb_progress > 1.0:
                thumb_progress = 1.0

            for idx in self.finger_groups['thumb']:
                control_values[idx] = self._compute_actuator_value(
                    idx, thumb_progress, use_range_fraction
                )

        return control_values

    def _compute_actuator_value(self, index: int, progress: float,
                               use_range_fraction: float) -> float:
        """
        计算单个执行器的控制值（考虑控制范围）

        参数:
            index: 执行器索引
            progress: 进度值（0-1）
            use_range_fraction: 范围使用比例

        返回:
            控制值
        """
        if index >= self.nu:
            return 0.0

        if self.ctrl_limited[index]:
            ctrl_min, ctrl_max = self.ctrl_ranges[index]
            # 对于有负值的范围，我们通常想要向正方向运动（弯曲）
            if ctrl_min < 0:
                # 使用范围的上半部分（从0到正方向）
                target_value = max(0, ctrl_min + (ctrl_max - ctrl_min) * use_range_fraction)
            else:
                target_value = ctrl_min + (ctrl_max - ctrl_min) * use_range_fraction
            return progress * target_value
        else:
            return progress * 0.3

    def set_phase_weights(self, phase_weights: Dict[str, float]):
        """
        设置阶段权重

        参数:
            phase_weights: 阶段权重字典
        """
        self.phase_weights = phase_weights

    def get_joint_type_info(self) -> Dict[str, List[int]]:
        """
        获取关节类型信息

        返回:
            关节类型到索引列表的映射
        """
        return {k: v.copy() for k, v in self.joint_types.items()}

    def get_state_info(self) -> Dict[str, Any]:
        """
        获取控制器状态信息

        返回:
            包含状态信息的字典
        """
        base_stats = super().get_control_stats()

        return {
            **base_stats,
            'controller_type': 'bio',
            'use_range_fraction': self.use_range_fraction,
            'current_overall_progress': self.current_overall_progress,
            'phase_weights': self.phase_weights.copy(),
            'joint_type_counts': {k: len(v) for k, v in self.joint_types.items()}
        }

    def print_info(self):
        """
        打印控制器信息
        """
        super().print_info()
        print(f"范围使用比例: {self.use_range_fraction}")
        print(f"当前整体进度: {self.current_overall_progress:.3f}")
        print("阶段权重:")
        for joint_type, weight in self.phase_weights.items():
            count = len(self.joint_types.get(joint_type, []))
            print(f"  {joint_type}: 权重={weight:.2f}, 执行器={count}个")
        print("关节类型分布:")
        for joint_type, indices in self.joint_types.items():
            if indices:
                print(f"  {joint_type}: {len(indices)} 个执行器 (索引: {indices})")