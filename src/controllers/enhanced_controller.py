"""
增强型控制器 - 带物体交互、力反馈和自适应控制

功能特点:
1. 物体检测与定位
2. 力反馈控制
3. 自适应抓取算法
4. 轨迹规划
5. 键盘交互支持
"""

import numpy as np
import mujoco
from typing import Optional, Dict, List, Any, Tuple
from .base_controller import BaseController


class EnhancedHandController(BaseController):
    """
    增强型控制器 - 支持物体交互和力反馈的高级控制
    """

    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData,
                 force_feedback_gain: float = 0.1, **kwargs):
        """
        初始化增强型控制器

        参数:
            model: MuJoCo 模型
            data: MuJoCo 数据
            force_feedback_gain: 力反馈增益
            **kwargs: 传递给基类的参数
        """
        super().__init__(model, data, **kwargs)

        # 关节类型分类
        self.joint_types = self._classify_joints()

        # 物体信息
        self.object_body_id = self._find_object_body()
        self.object_geom_id = self._find_object_geom()
        self.hand_body_id = self._find_hand_body()
        self.grasp_contact_body_ids = self._find_grasp_contact_body_ids()

        # 控制状态
        self.grasp_strength = 0.0  # 抓取力度 (0-1)
        self.is_grasping = False   # 是否正在抓取
        self.target_position = np.array([0.3, 0.0, 0.1])  # 默认目标位置
        self.control_mode = 'position'  # 'position' 或 'force_hybrid'

        # 三阶段抓取状态
        self.grasp_phase = 'approach'  # 'approach', 'close_fingers', 'lift', 'hold'
        self.grasp_phase_timer = 0
        self.phase_durations = {
            'approach': 80,      # 减少：更快接近（原100）
            'close_fingers': 30, # 减少：更快闭合手指（原50）
            'lift': 50           # 减少：更快稳定（原100）
        }
        self.lift_target_offset = np.array([0.0, 0.0, 0.1])  # 提起目标偏移
        self.hold_after_lift = False
        self.hold_wrist_strength = 0.05

        # 力反馈参数
        self.force_feedback_gain = force_feedback_gain
        self.min_grasp_force = 0.2
        self.max_grasp_force = 0.8

        # 轨迹规划参数
        self.trajectory_points = []
        self.current_trajectory_index = 0

        # 接触力历史
        self.contact_forces = []
        self.max_contact_history = 100

        # 自适应控制参数
        self.adaptive_gain = 0.1
        self.last_contact_force = 0.0

        print(f"增强控制器初始化完成")
        print(f"  - 执行器数量: {self.nu}")
        print(f"  - 物体主体ID: {self.object_body_id}")
        print(f"  - 物体几何体ID: {self.object_geom_id}")

    def _classify_joints(self) -> Dict[str, List[int]]:
        """
        根据控制范围分类关节类型

        返回:
            关节类型到索引列表的映射
        """
        joint_types = {
            'wrist': [],      # 手腕关节
            'thumb_base': [], # 拇指基部
            'thumb_flex': [], # 拇指弯曲关节
            'finger_abduct': [], # 手指外展/内收
            'finger_proximal': [], # 近端指节
            'finger_distal': []   # 远端指节
        }

        # 简化的分类：基于索引位置
        joint_types['wrist'] = [0, 1]
        joint_types['thumb_base'] = [2]
        joint_types['thumb_flex'] = [3, 4, 5, 6]
        joint_types['finger_abduct'] = [7, 11, 15, 19]
        joint_types['finger_proximal'] = [8, 12, 16, 20]
        joint_types['finger_distal'] = [9, 10, 13, 14, 17, 18, 21, 22, 23]

        return joint_types

    def _find_object_body(self) -> Optional[int]:
        """
        查找场景中的物体主体

        使用与环境相同的搜索模式，确保一致性。
        查找顺序:
        1. 名称包含 'object' 的body
        2. 名称包含 'ball' 的body
        3. 名称包含 'sphere' 的body
        4. 名称包含 'cube' 的body
        5. 名称包含 'target' 的body
        6. 名称包含 'obj' 的body
        7. 如果都找不到，返回None
        """
        possible_names = ['object', 'ball', 'sphere', 'cube', 'target', 'obj']

        for body_id in range(self.model.nbody):
            body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            if body_name:
                lower_name = body_name.lower()
                for name in possible_names:
                    if name in lower_name:
                        return body_id

        # 如果找不到，尝试查找包含物体的geom
        for geom_id in range(self.model.ngeom):
            geom_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            if geom_name:
                lower_name = geom_name.lower()
                for name in possible_names:
                    if name in lower_name:
                        # 获取geom所属的body
                        body_id = self.model.geom_bodyid[geom_id]
                        return int(body_id)

        return None

    def _find_object_geom(self) -> Optional[int]:
        """
        查找场景中的物体几何体

        返回:
            物体几何体ID，如果未找到则返回None
        """
        possible_names = ['object', 'ball', 'sphere', 'cube', 'target', 'obj']

        # 方法1: 按名称查找几何体
        for geom_id in range(self.model.ngeom):
            geom_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            if geom_name:
                lower_name = geom_name.lower()
                for name in possible_names:
                    if name in lower_name:
                        return geom_id

        # 方法2: 如果通过名称找不到，尝试通过物体body id查找几何体
        if self.object_body_id is not None:
            for geom_id in range(self.model.ngeom):
                if self.model.geom_bodyid[geom_id] == self.object_body_id:
                    return geom_id

        return None

    def _find_hand_body(self) -> Optional[int]:
        """
        查找手部主体

        使用与环境相同的搜索模式，确保一致性。
        查找顺序:
        1. 名称包含 'palm' 的body
        2. 名称包含 'wrist' 的body
        3. 名称包含 'hand' 的body
        4. 名称包含 'right_hand' 的body
        5. 名称包含 'shadow' 的body
        6. 如果都找不到，返回第一个body
        """
        possible_names = ['palm', 'wrist', 'hand', 'right_hand', 'shadow']

        for body_id in range(self.model.nbody):
            body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            if body_name:
                lower_name = body_name.lower()
                for name in possible_names:
                    if name in lower_name:
                        return body_id

        # 如果没找到，返回第一个 body
        return 0 if self.model.nbody > 0 else None

    def _find_grasp_contact_body_ids(self) -> set[int]:
        """Return palm and finger bodies that count as valid grasp contact."""
        include_keywords = ('palm', 'ff', 'mf', 'rf', 'lf', 'th')
        exclude_keywords = ('wrist', 'forearm', 'object', 'floor', 'world')
        body_ids = set()

        for body_id in range(self.model.nbody):
            body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            if not body_name:
                continue

            lower_name = body_name.lower()
            if any(keyword in lower_name for keyword in exclude_keywords):
                continue
            if any(keyword in lower_name for keyword in include_keywords):
                body_ids.add(body_id)

        return body_ids

    def _is_valid_grasp_contact_body(self, body_id: int) -> bool:
        """Check whether a contact body should contribute to grasp feedback."""
        return body_id in self.grasp_contact_body_ids

    def compute_control(self, t: float, **kwargs) -> np.ndarray:
        """
        计算增强控制输出

        参数:
            t: 当前时间（秒）
            **kwargs: 额外的控制参数，支持:
                - grasp_strength: 抓取力度（0-1）
                - target_position: 目标位置 [x, y, z]
                - control_mode: 控制模式 ('position', 'force_hybrid')
                - adaptive_gain: 自适应增益

        返回:
            control_values: 形状为 (nu,) 的控制值数组
        """
        # 处理参数
        grasp_strength = kwargs.get('grasp_strength', self.grasp_strength)
        target_position = kwargs.get('target_position', self.target_position)
        control_mode = kwargs.get('control_mode', self.control_mode)
        adaptive_gain = kwargs.get('adaptive_gain', self.adaptive_gain)

        # 更新内部状态
        self.grasp_strength = np.clip(grasp_strength, 0.0, 1.0)
        self.target_position = np.array(target_position)
        self.control_mode = control_mode
        self.adaptive_gain = adaptive_gain

        # 检测接触力
        contact_force = self._get_contact_force()

        # 更新抓取阶段
        if self.is_grasping:
            self._update_grasp_phase()

        # 根据控制模式计算控制值
        if control_mode == 'position':
            control_values = self._position_control(t, contact_force)
        elif control_mode == 'force_hybrid':
            control_values = self._force_hybrid_control(t, contact_force)
        else:
            # 默认回退到位置控制
            control_values = self._position_control(t, contact_force)

        # 应用自适应抓取调整
        if self.is_grasping and contact_force > 0:
            control_values = self._apply_adaptive_grasp(
                control_values, contact_force, adaptive_gain
            )

        # 记录接触力历史
        self._record_contact_force(contact_force)

        return control_values

    def reset(self):
        """Reset controller state between episodes."""
        super().reset()
        self.grasp_strength = 0.0
        self.is_grasping = False
        self.grasp_phase = 'approach'
        self.grasp_phase_timer = 0
        self.target_position = np.array([0.3, 0.0, 0.1])
        self.control_mode = 'position'
        self.trajectory_points = []
        self.current_trajectory_index = 0
        self.contact_forces = []
        self.last_contact_force = 0.0

    def _position_control(self, t: float, contact_force: float) -> np.ndarray:
        """
        位置控制模式（集成三阶段抓取逻辑）

        参数:
            t: 当前时间
            contact_force: 接触力

        返回:
            控制值数组
        """
        control_values = np.zeros(self.nu)

        # 获取当前阶段的抓取参数
        if self.is_grasping:
            grasp_strength, wrist_strength = self._get_phase_based_grasp_params()
        else:
            # 非抓取模式使用默认参数
            grasp_strength = self.grasp_strength
            wrist_strength = 0.0

        # 根据关节类型应用不同的控制
        for joint_type, indices in self.joint_types.items():
            if indices:
                # 根据关节类型调整力度
                if joint_type == 'wrist':
                    strength = wrist_strength  # 手腕控制独立
                    range_fraction = 0.70
                elif joint_type == 'thumb_base':
                    strength = grasp_strength * 0.8
                    range_fraction = 0.70
                elif joint_type == 'thumb_flex':
                    strength = grasp_strength * 1.0
                    range_fraction = 0.90
                elif joint_type == 'finger_abduct':
                    strength = grasp_strength * 0.15  # 外展保持较弱，避免把球推出去
                    range_fraction = 0.35
                elif joint_type == 'finger_proximal':
                    strength = grasp_strength * 1.0
                    range_fraction = 0.95
                elif joint_type == 'finger_distal':
                    strength = grasp_strength * 1.1  # 远端更紧，避免夹住后掉落
                    range_fraction = 1.00
                else:
                    strength = grasp_strength
                    range_fraction = 0.85

                # 应用控制
                for idx in indices:
                    if idx < self.nu:
                        control_values[idx] = self._get_joint_target_ctrl(
                            idx,
                            np.clip(strength, 0.0, 1.0),
                            range_fraction
                        )

        return control_values

    def _force_hybrid_control(self, t: float, contact_force: float) -> np.ndarray:
        """
        力混合控制模式

        参数:
            t: 当前时间
            contact_force: 接触力

        返回:
            控制值数组
        """
        control_values = np.zeros(self.nu)

        # 基础抓取控制
        base_grasp = self.grasp_strength

        # 力反馈调整
        force_adjustment = 0.0
        if contact_force > 0:
            # 如果检测到接触，根据接触力调整抓取力度
            force_adjustment = np.clip(
                contact_force * self.force_feedback_gain,
                -0.3, 0.3
            )

        adjusted_grasp = np.clip(base_grasp + force_adjustment, 0.0, 1.0)

        # 根据关节类型应用控制
        for joint_type, indices in self.joint_types.items():
            if indices:
                # 关节类型特定的调整
                if joint_type in ['thumb_flex', 'finger_proximal']:
                    strength = adjusted_grasp
                else:
                    strength = adjusted_grasp * 0.7

                # 应用控制
                for idx in indices:
                    if idx < self.nu:
                        control_values[idx] = strength * 0.5

        return control_values

    def _get_contact_force(self) -> float:
        """
        检查手部与物体是否有接触

        返回:
            如果有接触返回1.0，否则返回0.0
        """
        if self.object_geom_id is None or self.hand_body_id is None:
            return 0.0

        # 简化实现：只检查是否有接触，不计算力的大小
        # 遍历所有接触
        for i in range(self.data.ncon):
            contact = self.data.contact[i]

            # 检查是否涉及物体几何体
            geom1, geom2 = contact.geom1, contact.geom2

            # 如果接触涉及物体
            if (geom1 == self.object_geom_id or geom2 == self.object_geom_id):
                # 获取接触几何体对应的body
                body1 = self.model.geom_bodyid[geom1]
                body2 = self.model.geom_bodyid[geom2]

                # 只把掌心或手指接触视为有效抓取反馈
                if body1 == self.object_body_id and self._is_valid_grasp_contact_body(body2):
                    return 1.0
                elif body2 == self.object_body_id and self._is_valid_grasp_contact_body(body1):
                    return 1.0

        return 0.0

    def _update_grasp_phase(self):
        """
        更新抓取阶段
        """
        self.grasp_phase_timer += 1

        if self.grasp_phase == 'hold':
            return

        # 检查是否应该切换到下一个阶段
        if self.grasp_phase_timer >= self.phase_durations.get(self.grasp_phase, 100):
            if self.grasp_phase == 'approach':
                self.grasp_phase = 'close_fingers'
                print(f"抓取阶段切换: approach → close_fingers")
            elif self.grasp_phase == 'close_fingers':
                self.grasp_phase = 'lift'
                print(f"抓取阶段切换: close_fingers → lift")
            elif self.grasp_phase == 'lift':
                if self.hold_after_lift:
                    self.grasp_phase = 'hold'
                    print("抓取阶段切换: lift → hold")
                else:
                    # 完成抓取，回到初始状态
                    self.grasp_phase = 'approach'
                    self.is_grasping = False
                    print(f"抓取完成，回到 approach 阶段")

            self.grasp_phase_timer = 0

    def _get_phase_based_grasp_params(self):
        """
        根据当前阶段获取抓取参数

        返回:
            grasp_strength: 抓取力度
            wrist_strength: 手腕控制力度
        """
        phase_progress = min(1.0, self.grasp_phase_timer / max(1, self.phase_durations.get(self.grasp_phase, 100)))

        if self.grasp_phase == 'approach':
            # 接近阶段: 手指保持半开，给手腕更多前送量
            return 0.18, 0.55
        elif self.grasp_phase == 'close_fingers':
            # 闭合手指阶段: 更快、更彻底地握紧
            grasp_strength = 0.55 + 0.45 * phase_progress
            return grasp_strength, 0.15
        elif self.grasp_phase == 'lift':
            # 提起阶段: 保持最大握力，防止球从指缝滑落
            return 1.0, 0.25
        elif self.grasp_phase == 'hold':
            return 1.0, self.hold_wrist_strength
        else:
            return 0.0, 0.0

    def _get_joint_target_ctrl(self, actuator_idx: int, progress: float,
                               range_fraction: float) -> float:
        """
        Map a 0-1 progress value to a flexion-biased actuator target.
        """
        ctrl_min, ctrl_max = self.ctrl_ranges[actuator_idx]
        progress = float(np.clip(progress, 0.0, 1.0))
        range_fraction = float(np.clip(range_fraction, 0.0, 1.0))

        if ctrl_max <= 0:
            return ctrl_max * progress

        if ctrl_min < 0:
            flexion_target = max(0.0, ctrl_min + (ctrl_max - ctrl_min) * range_fraction)
        else:
            flexion_target = ctrl_min + (ctrl_max - ctrl_min) * range_fraction

        return progress * flexion_target

    def start_grasp_sequence(self):
        """
        开始三阶段抓取序列
        """
        self.grasp_phase = 'approach'
        self.grasp_phase_timer = 0
        self.is_grasping = True
        print(f"开始三阶段抓取序列: {self.grasp_phase}")

    def _apply_adaptive_grasp(self, control_values: np.ndarray,
                            contact_force: float, gain: float) -> np.ndarray:
        """
        应用自适应抓取调整

        参数:
            control_values: 原始控制值
            contact_force: 接触力（0或1）
            gain: 自适应增益

        返回:
            调整后的控制值
        """
        if contact_force <= 0:
            return control_values

        # 简化：如果有接触，稍微增加抓取力度
        adjustment = gain * 0.1  # 小幅度调整

        # 应用调整（主要影响抓取相关的执行器）
        adjusted_values = control_values.copy()

        # 调整拇指和手指的控制值
        for joint_type in ['thumb_flex', 'finger_proximal', 'finger_distal']:
            if joint_type in self.joint_types:
                for idx in self.joint_types[joint_type]:
                    if idx < len(adjusted_values):
                        adjusted_values[idx] += adjustment
                        # 限制在安全范围内
                        adjusted_values[idx] = np.clip(adjusted_values[idx], 0.0, 1.2)

        self.last_contact_force = contact_force
        return adjusted_values

    def _record_contact_force(self, force: float):
        """
        记录接触力历史

        参数:
            force: 接触力
        """
        self.contact_forces.append(force)
        if len(self.contact_forces) > self.max_contact_history:
            self.contact_forces = self.contact_forces[-self.max_contact_history:]

    def set_grasping(self, is_grasping: bool, strength: float = 0.5):
        """
        设置抓取状态

        参数:
            is_grasping: 是否抓取
            strength: 抓取力度（0-1）
        """
        self.is_grasping = is_grasping
        self.grasp_strength = np.clip(strength, 0.0, 1.0)

    def set_target_position(self, position: np.ndarray):
        """
        设置目标位置

        参数:
            position: 目标位置 [x, y, z]
        """
        self.target_position = np.array(position)

    def get_contact_stats(self) -> Dict[str, float]:
        """
        获取接触统计信息

        返回:
            接触统计信息字典
        """
        if not self.contact_forces:
            return {
                'avg_force': 0.0,
                'max_force': 0.0,
                'min_force': 0.0,
                'recent_force': 0.0
            }

        forces = np.array(self.contact_forces)
        return {
            'avg_force': float(np.mean(forces)),
            'max_force': float(np.max(forces)),
            'min_force': float(np.min(forces)),
            'recent_force': float(self.contact_forces[-1] if self.contact_forces else 0.0)
        }

    def get_state_info(self) -> Dict[str, Any]:
        """
        获取控制器状态信息

        返回:
            包含状态信息的字典
        """
        base_stats = super().get_control_stats()
        contact_stats = self.get_contact_stats()

        return {
            **base_stats,
            **contact_stats,
            'controller_type': 'enhanced',
            'grasp_strength': self.grasp_strength,
            'is_grasping': self.is_grasping,
            'grasp_phase': self.grasp_phase,
            'grasp_phase_timer': self.grasp_phase_timer,
            'target_position': self.target_position.tolist(),
            'control_mode': self.control_mode,
            'force_feedback_gain': self.force_feedback_gain,
            'adaptive_gain': self.adaptive_gain,
            'object_body_id': self.object_body_id,
            'object_geom_id': self.object_geom_id,
            'hand_body_id': self.hand_body_id
        }

    def print_info(self):
        """
        打印控制器信息
        """
        super().print_info()
        print(f"控制模式: {self.control_mode}")
        print(f"抓取状态: {'正在抓取' if self.is_grasping else '未抓取'}")
        if self.is_grasping:
            print(f"抓取阶段: {self.grasp_phase} (计时器: {self.grasp_phase_timer})")
        print(f"抓取力度: {self.grasp_strength:.3f}")
        print(f"目标位置: {self.target_position}")
        print(f"力反馈增益: {self.force_feedback_gain}")
        print(f"自适应增益: {self.adaptive_gain}")

        contact_stats = self.get_contact_stats()
        print(f"接触力统计: 平均={contact_stats['avg_force']:.3f}, "
              f"最大={contact_stats['max_force']:.3f}, "
              f"最近={contact_stats['recent_force']:.3f}")

        print("关节类型分布:")
        for joint_type, indices in self.joint_types.items():
            if indices:
                print(f"  {joint_type}: {len(indices)} 个执行器")
