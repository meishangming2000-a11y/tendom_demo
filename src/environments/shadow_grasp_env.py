#!/usr/bin/env python3
"""
Shadow Hand 抓取环境
基于 MuJoCo 的最小训练环境，用于接近并接触简单物体的任务。

环境接口:
- reset(): 重置环境，返回初始观测
- step(action): 执行动作，返回 (obs, reward, done, info)
- get_obs(): 获取当前观测
- compute_reward(): 计算奖励值
- is_success(): 检查任务是否成功

任务: 控制 Shadow Hand 接近并接触场景中的物体（球体）。
"""

import numpy as np
import mujoco
from typing import Tuple, Dict, Any, Optional
from observations import get_observation_builder
from tasks import create_task
from ..adapters import create_hand_adapter

# 导入项目工具模块
from ..utils import model_loader, path_utils


class ShadowGraspEnv:
    """Shadow Hand 抓取环境"""

    def __init__(
        self,
        max_steps: int = 500,
        control_timestep: float = 0.002,
        enable_catch_task: bool = False,
        object_fall_speed: float = -0.3,
        task_name: Optional[str] = None,
        observation_mode: str = "oracle",
        task_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化环境

        参数:
            max_steps: 每个 episode 的最大步数
            control_timestep: 控制时间步长（秒）
            enable_catch_task: 是否启用接住任务（True: 物体下落，需要空中接住）
            object_fall_speed: 物体初始下落速度（m/s，负表示向下）
        """
        # 加载模型
        self.model, self.data = model_loader.load_shadow_hand_model()

        # 环境参数
        self.max_steps = max_steps
        self.control_timestep = control_timestep
        self.current_step = 0
        self.contact_duration = 0
        self.grasp_contact_duration = 0

        # 接住任务参数
        self.enable_catch_task = enable_catch_task
        self.object_fall_speed = object_fall_speed
        self.task_name = task_name
        self.task_kwargs = dict(task_kwargs or {})
        self.task = create_task(task_name, **self.task_kwargs) if task_name else None
        self.observation_mode = "oracle"
        self.observation_builder = None
        self.set_observation_mode(observation_mode)
        self.initial_object_height = 0.0

        # 获取模型信息
        self.nu = self.model.nu  # 执行器数量
        self.nq = self.model.nq  # 关节位置数量
        self.nv = self.model.nv  # 关节速度数量

        # 查找物体、手部和地面主体
        self.object_body_id = self._find_object_body()
        self.hand_body_id = self._find_hand_body()
        self.floor_body_id = self._find_floor_body()
        self.grasp_site_id = self._find_grasp_site()
        self.grasp_contact_body_ids = self._find_grasp_contact_body_ids()

        if self.object_body_id is None:
            raise ValueError("未找到物体主体，请检查模型文件")
        if self.hand_body_id is None:
            raise ValueError("未找到手部主体，请检查模型文件")

        print(f"环境初始化完成:")
        print(f"  - 执行器数量 (nu): {self.nu}")
        print(f"  - 关节位置数 (nq): {self.nq}")
        print(f"  - 关节速度数 (nv): {self.nv}")
        print(f"  - 物体主体ID: {self.object_body_id}")
        print(f"  - 手部主体ID: {self.hand_body_id}")
        print(f"  - 地面主体ID: {self.floor_body_id}")
        print(f"  - 有效抓取接触体数量: {len(self.grasp_contact_body_ids)}")

        # 保存初始状态用于重置
        self.initial_qpos = self.data.qpos.copy()
        self.initial_qvel = self.data.qvel.copy()

        # 奖励系数
        self.reward_coeffs = {
            'distance': -1.0,      # 距离奖励系数（负距离）
            'contact': 10.0,       # 接触奖励
            'maintain': 0.1,       # 持续接触奖励
            'catch': 15.0,         # 成功接住奖励（新增）
            'ground_penalty': -20.0, # 地面接触惩罚（新增）
            'action_penalty': -0.001,  # 动作惩罚
        }

        # 成功条件
        self.success_contact_duration = 50  # 需要连续接触的步数
        self.required_finger_groups_for_success = 3
        self.require_thumb_for_success = True

        # 执行器控制范围（用于归一化动作）
        self.actuator_ctrlrange = self._get_actuator_control_ranges()

        # 查找物体关节ID（用于设置速度）
        self.object_joint_id = self._find_object_joint()
        self.hand_adapter = create_hand_adapter(self)

        # 打印接住任务参数
        if self.enable_catch_task:
            print(f"接住任务已启用:")
            print(f"  - 物体下落速度: {self.object_fall_speed:.3f} m/s")
            print(f"  - 物体关节ID: {self.object_joint_id}")

        if self.task is not None:
            print(f"Structured task enabled: {self.task.get_name()}")
        print(f"Observation mode: {self.observation_mode}")

    def set_observation_mode(self, mode: str) -> None:
        """Set the active observation layer."""
        self.observation_mode = str(mode or "oracle").strip().lower()
        self.observation_builder = get_observation_builder(self.observation_mode)

    def set_task(self, task_name: Optional[str] = None, task=None, **task_kwargs) -> None:
        """Replace the active structured task."""
        if task is not None:
            self.task = task
            self.task_name = task.get_name()
            self.task_kwargs = {}
            return

        self.task_name = task_name
        self.task_kwargs = dict(task_kwargs)
        self.task = create_task(task_name, **self.task_kwargs) if task_name else None

    def get_hand_adapter(self):
        """Return the backend adapter used by task logic."""
        return self.hand_adapter

    def get_task_name(self) -> str:
        """Return the active structured task name or the legacy task label."""
        if self.task is not None:
            return self.task.get_name()
        return "catch_task" if self.enable_catch_task else "stable_grasp_legacy"

    def get_action_spec(self) -> Dict[str, Any]:
        """Return the current action interface spec."""
        if self.task is not None:
            return self.task.get_action_spec(self)

        return {
            "control_level": "joint",
            "shape": (self.nu,),
            "normalized": True,
            "range": [-1.0, 1.0],
            "notes": "Legacy environment action interface.",
        }

    def _find_object_joint(self) -> Optional[int]:
        """
        查找物体对应的关节ID

        返回:
            物体关节ID，如果未找到则返回None
        """
        if self.object_body_id is None:
            return None

        # 通过body的关节起始地址查找
        body_joint_adr = self.model.body_jntadr[self.object_body_id]
        if body_joint_adr >= 0:
            # 返回第一个关节ID
            return body_joint_adr

        # 如果通过body找不到，尝试通过名称查找
        for joint_id in range(self.model.njnt):
            joint_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
            if joint_name and 'object' in joint_name.lower():
                return joint_id

        return None

    def _find_object_body(self) -> Optional[int]:
        """查找场景中的物体主体

        查找顺序:
        1. 名称包含 'object' 的body
        2. 名称包含 'ball' 的body
        3. 名称包含 'sphere' 的body
        4. 名称包含 'cube' 的body
        5. 名称包含 'target' 的body
        6. 如果都找不到，返回None
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

    def _find_hand_body(self) -> Optional[int]:
        """查找手部主体（手掌或手腕）

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

    def _find_floor_body(self) -> Optional[int]:
        """查找地面主体

        首先尝试通过名称查找地面body，如果找不到则查找名称为'floor'的geom
        如果还找不到，返回None
        """
        # 方法1: 查找名称为'floor'的body
        for body_id in range(self.model.nbody):
            body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            if body_name and ('floor' in body_name.lower()):
                return body_id

        # 方法2: 查找名称为'floor'的geom，然后获取其body id
        for geom_id in range(self.model.ngeom):
            geom_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            if geom_name and ('floor' in geom_name.lower()):
                # 获取geom所属的body
                body_id = self.model.geom_bodyid[geom_id]
                return int(body_id)

        return None

    def _find_grasp_site(self) -> Optional[int]:
        """Return the palm-aligned grasp reference site when present."""
        preferred_names = ("grasp_site", "palm_site", "palm_center")
        for site_id in range(self.model.nsite):
            site_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_SITE, site_id)
            if site_name and site_name.lower() in preferred_names:
                return site_id

        for site_id in range(self.model.nsite):
            site_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_SITE, site_id)
            if site_name and "grasp" in site_name.lower():
                return site_id
        return None

    def _find_grasp_contact_body_ids(self) -> set[int]:
        """Return palm and finger bodies that count as a valid grasp contact."""
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
        """Check whether a contact body should count toward a successful grasp."""
        return body_id in self.grasp_contact_body_ids

    def _get_contact_group_for_body(self, body_id: int) -> Optional[str]:
        """Map a contacting body to the palm or a finger group name."""
        if body_id not in self.grasp_contact_body_ids:
            return None

        body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
        if not body_name:
            return None

        lower_name = body_name.lower()
        if "palm" in lower_name:
            return "palm"
        if "th" in lower_name:
            return "thumb"
        if "ff" in lower_name:
            return "index"
        if "mf" in lower_name:
            return "middle"
        if "rf" in lower_name:
            return "ring"
        if "lf" in lower_name:
            return "little"
        return None

    def _get_contact_state(self) -> Dict[str, Any]:
        """Collect detailed object-contact state for reporting and success checks."""
        contact_body_ids = set()
        contact_body_names = set()
        finger_groups = set()

        for contact_id in range(self.data.ncon):
            contact = self.data.contact[contact_id]
            geom1 = contact.geom1
            geom2 = contact.geom2
            body1 = int(self.model.geom_bodyid[geom1])
            body2 = int(self.model.geom_bodyid[geom2])

            other_body = None
            if body1 == self.object_body_id and body2 != self.object_body_id:
                other_body = body2
            elif body2 == self.object_body_id and body1 != self.object_body_id:
                other_body = body1

            if other_body is None or not self._is_valid_grasp_contact_body(other_body):
                continue

            contact_body_ids.add(other_body)
            body_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, other_body)
            if body_name:
                contact_body_names.add(body_name)

            contact_group = self._get_contact_group_for_body(other_body)
            if contact_group and contact_group != "palm":
                finger_groups.add(contact_group)

        has_valid_contact = bool(contact_body_ids)
        has_palm_contact = any(
            self._get_contact_group_for_body(body_id) == "palm"
            for body_id in contact_body_ids
        )
        finger_group_list = sorted(finger_groups)
        finger_group_count = len(finger_group_list)
        has_thumb_contact = "thumb" in finger_groups
        is_grasp_contact = (
            has_palm_contact
            and finger_group_count >= self.required_finger_groups_for_success
            and ((not self.require_thumb_for_success) or has_thumb_contact)
        )

        return {
            "has_valid_contact": has_valid_contact,
            "has_palm_contact": has_palm_contact,
            "has_thumb_contact": has_thumb_contact,
            "finger_groups": finger_group_list,
            "finger_group_count": finger_group_count,
            "contact_body_names": sorted(contact_body_names),
            "is_grasp_contact": is_grasp_contact,
            "is_palm_only_contact": has_palm_contact and finger_group_count == 0,
        }

    def _get_actuator_control_ranges(self) -> np.ndarray:
        """获取执行器控制范围，形状为 (nu, 2)"""
        ctrl_ranges = np.zeros((self.nu, 2))
        for i in range(self.nu):
            if self.model.actuator_ctrllimited[i]:
                ctrl_ranges[i] = self.model.actuator_ctrlrange[i]
            else:
                # 如果没有限制，使用默认范围 [-1, 1]
                ctrl_ranges[i] = np.array([-1.0, 1.0])
        return ctrl_ranges

    def _normalize_action(self, action: np.ndarray) -> np.ndarray:
        """
        将归一化的动作（范围 [-1, 1]）映射到执行器的实际控制范围

        参数:
            action: 归一化动作，形状 (nu,)，范围 [-1, 1]

        返回:
            ctrl: 实际控制信号，形状 (nu,)
        """
        ctrl = np.zeros_like(action)
        for i in range(self.nu):
            # 将 [-1, 1] 线性映射到 [ctrl_min, ctrl_max]
            ctrl_min, ctrl_max = self.actuator_ctrlrange[i]
            ctrl[i] = (action[i] + 1) / 2 * (ctrl_max - ctrl_min) + ctrl_min
        return ctrl

    def _denormalize_action(self, ctrl: np.ndarray) -> np.ndarray:
        """
        将实际控制信号映射回归一化的动作（范围 [-1, 1]）

        参数:
            ctrl: 实际控制信号，形状 (nu,)

        返回:
            action: 归一化动作，形状 (nu,)，范围 [-1, 1]
        """
        action = np.zeros_like(ctrl)
        for i in range(self.nu):
            ctrl_min, ctrl_max = self.actuator_ctrlrange[i]
            # 确保控制信号在执行器范围内
            ctrl_clipped = np.clip(ctrl[i], ctrl_min, ctrl_max)
            if ctrl_max == ctrl_min:
                # 避免除以零
                action[i] = 0.0
            else:
                # 将 [ctrl_min, ctrl_max] 线性映射到 [-1, 1]
                action[i] = 2 * ((ctrl_clipped - ctrl_min) / (ctrl_max - ctrl_min)) - 1
        return action

    def _get_hand_position(self) -> np.ndarray:
        """获取手部主体位置（手掌或手腕）"""
        return self.data.xpos[self.hand_body_id].copy()

    def _get_palm_reference_position(self) -> np.ndarray:
        """Return the task-space palm reference point used by pre-grasp."""
        if self.grasp_site_id is not None:
            return self.data.site_xpos[self.grasp_site_id].copy()
        return self._get_hand_position()

    def _get_object_position(self) -> np.ndarray:
        """获取物体位置"""
        return self.data.xpos[self.object_body_id].copy()

    def _get_hand_orientation(self) -> np.ndarray:
        """Return the current hand-body orientation quaternion."""
        return self.data.xquat[self.hand_body_id].copy()

    def _get_object_orientation(self) -> np.ndarray:
        """Return the current object orientation quaternion."""
        return self.data.xquat[self.object_body_id].copy()

    def _get_object_velocity(self) -> np.ndarray:
        """Return the object's linear velocity when available."""
        if self.object_body_id is None:
            return np.zeros(3, dtype=np.float32)

        body_joint_adr = self.model.body_jntadr[self.object_body_id]
        if body_joint_adr >= 0 and (body_joint_adr + 3) <= len(self.data.qvel):
            return self.data.qvel[body_joint_adr: body_joint_adr + 3].copy()
        return np.zeros(3, dtype=np.float32)

    def _get_distance(self) -> float:
        """计算手部与物体之间的距离"""
        hand_pos = self._get_hand_position()
        obj_pos = self._get_object_position()
        return np.linalg.norm(hand_pos - obj_pos)

    def _check_contact(self) -> bool:
        """检查手部与物体之间是否有接触"""
        return self._get_contact_state()["has_valid_contact"]

    def _check_object_on_floor(self) -> bool:
        """检查物体是否接触地面"""
        if self.floor_body_id is None or self.object_body_id is None:
            return False

        for contact_id in range(self.data.ncon):
            contact = self.data.contact[contact_id]
            geom1 = contact.geom1
            geom2 = contact.geom2
            body1 = self.model.geom_bodyid[geom1]
            body2 = self.model.geom_bodyid[geom2]

            # 检查是否涉及物体和地面
            if (body1 == self.object_body_id and body2 == self.floor_body_id) or \
               (body2 == self.object_body_id and body1 == self.floor_body_id):
                return True

        return False

    def _get_object_height(self) -> float:
        """获取物体高度（Z坐标）"""
        return self._get_object_position()[2]

    def reset(self) -> np.ndarray:
        """
        重置环境到初始状态

        返回:
            obs: 初始观测值
        """
        # 重置模拟数据
        mujoco.mj_resetData(self.model, self.data)

        # 恢复初始状态（如果需要，但 mj_resetData 应该已经处理了）
        self.data.qpos[:] = self.initial_qpos
        self.data.qvel[:] = self.initial_qvel

        # 如果启用接住任务，设置物体初始下落速度
        if self.enable_catch_task and self.object_joint_id is not None:
            # 自由关节：前3个是位置，后3个是速度
            # 首先找到物体的自由度起始索引
            body_joint_adr = self.model.body_jntadr[self.object_body_id]
            if body_joint_adr >= 0:
                # 自由关节有6个自由度：3个位置 + 3个速度
                # qvel索引对应关系：平移速度在旋转速度之前
                qvel_start = body_joint_adr
                self.data.qvel[qvel_start + 2] = self.object_fall_speed  # Z方向速度
                if self.object_fall_speed != 0:
                    print(f"  设置物体初始下落速度: {self.object_fall_speed:.3f} m/s")

        # 重置环境状态
        self.current_step = 0
        self.contact_duration = 0
        self.grasp_contact_duration = 0

        # 前进一步以确保数据有效
        mujoco.mj_step(self.model, self.data)
        self.initial_object_height = float(self._get_object_height())
        if self.task is not None:
            self.task.reset_task(self)

        return self.get_obs()

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        执行一个时间步

        参数:
            action: 动作向量，形状 (nu,)，范围 [-1, 1]

        返回:
            obs: 新观测值
            reward: 奖励值
            done: 是否结束
            info: 额外信息
        """
        # 检查动作形状
        if action.shape != (self.nu,):
            raise ValueError(f"动作形状应为 ({self.nu},)，但得到 {action.shape}")

        # 将归一化动作转换为实际控制信号
        ctrl = self._normalize_action(action)

        # 应用控制信号
        self.data.ctrl[:] = ctrl

        # 执行模拟步
        mujoco.mj_step(self.model, self.data)

        # 更新步数
        self.current_step += 1

        # 检查接触
        contact_state = self._get_contact_state()
        is_contact = contact_state["has_valid_contact"]
        is_grasp_contact = contact_state["is_grasp_contact"]
        if is_contact:
            self.contact_duration += 1
        else:
            self.contact_duration = 0
        if is_grasp_contact:
            self.grasp_contact_duration += 1
        else:
            self.grasp_contact_duration = 0

        # 检查物体是否接触地面
        ground_contact = self._check_object_on_floor()

        # 获取观测值
        obs = self.get_obs()

        # 计算奖励
        reward = self.compute_reward(action, is_contact)

        # 检查是否结束
        done = self._check_done()

        # 构建信息字典
        info = {
            'step': self.current_step,
            'distance': self._get_distance(),
            'contact': is_contact,
            'contact_duration': self.contact_duration,
            'grasp_contact': is_grasp_contact,
            'grasp_contact_duration': self.grasp_contact_duration,
            'palm_contact': contact_state["has_palm_contact"],
            'thumb_contact': contact_state["has_thumb_contact"],
            'palm_only_contact': contact_state["is_palm_only_contact"],
            'finger_contact_count': contact_state["finger_group_count"],
            'finger_contact_groups': contact_state["finger_groups"],
            'contact_body_names': contact_state["contact_body_names"],
            'object_on_floor': ground_contact,  # 新增：物体是否接触地面
            'object_height': self._get_object_height(),  # 新增：物体高度
            'catch_success': (is_grasp_contact and not ground_contact),  # 新增：是否成功接住
            'success': self.is_success()  # 最终成功标志（使用新标准）
        }

        return obs, reward, done, info

    def get_obs(self) -> np.ndarray:
        """
        获取当前观测值

        观测值组成:
        1. 关节位置 (nq)
        2. 关节速度 (nv)
        3. 手部位置 (3)
        4. 物体位置 (3)
        5. 手部与物体相对位置 (3)
        """
        # 关节位置和速度（归一化到 [-1, 1] 范围）
        qpos_norm = self.data.qpos.copy()
        qvel_norm = self.data.qvel.copy()

        # 简单归一化（实际中应根据关节范围调整）
        qpos_norm = np.clip(qpos_norm, -1.0, 1.0)
        qvel_norm = np.clip(qvel_norm, -1.0, 1.0)

        # 手部和物体位置
        hand_pos = self._get_hand_position()
        obj_pos = self._get_object_position()
        rel_pos = hand_pos - obj_pos

        # 拼接观测向量
        obs = np.concatenate([
            qpos_norm,
            qvel_norm,
            hand_pos,
            obj_pos,
            rel_pos
        ])

        return obs.astype(np.float32)

    def compute_reward(self, action: np.ndarray, is_contact: bool) -> float:
        """
        计算奖励值

        奖励组成:
        1. 距离奖励: -距离 * coeff
        2. 接触奖励: 如果接触则获得固定奖励
        3. 持续接触奖励: 如果持续接触，每步获得小奖励
        4. 成功接住奖励: 如果手接触物体且物体未接触地面
        5. 地面接触惩罚: 如果物体接触地面
        6. 动作惩罚: -动作幅度的平方和 * coeff
        """
        coeffs = self.reward_coeffs

        # 1. 距离奖励（负距离，鼓励靠近）
        distance = self._get_distance()
        distance_reward = coeffs['distance'] * distance

        # 2. 接触奖励
        contact_reward = coeffs['contact'] if is_contact else 0.0

        # 3. 持续接触奖励
        maintain_reward = coeffs['maintain'] * self.contact_duration if is_contact else 0.0

        # 4. 成功接住奖励（新增）
        ground_contact = self._check_object_on_floor()
        catch_reward = coeffs['catch'] if (is_contact and not ground_contact) else 0.0

        # 5. 地面接触惩罚（新增）
        ground_penalty = coeffs['ground_penalty'] if ground_contact else 0.0

        # 6. 动作惩罚（鼓励小动作）
        action_penalty = coeffs['action_penalty'] * np.sum(action ** 2)

        # 总奖励
        total_reward = distance_reward + contact_reward + maintain_reward + \
                       catch_reward + ground_penalty + action_penalty

        return float(total_reward)

    def _check_done(self) -> bool:
        """检查 episode 是否结束"""
        # 检查最大步数
        if self.current_step >= self.max_steps:
            return True

        # 检查是否成功（可选：成功即结束）
        # if self.is_success():
        #     return True

        return False

    def is_success(self) -> bool:
        """检查任务是否成功（持续接触足够长时间，且物体未接触地面）"""
        # 条件1：手部与物体持续接触足够长时间
        contact_success = self.grasp_contact_duration >= self.success_contact_duration

        if not self.enable_catch_task:
            # 如果禁用接住任务，使用原始标准
            return contact_success

        # 条件2：物体没有接触地面（关键新增条件）
        ground_contact = self._check_object_on_floor()

        # 真正接住：手接触物体 AND 物体不接触地面
        return contact_success and (not ground_contact)

    def get_observation_dict(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Return the structured observation payload for the requested mode."""
        builder = self.observation_builder if mode is None else get_observation_builder(mode)
        return builder.get_dict(self)

    def get_observation(self, mode: Optional[str] = None) -> np.ndarray:
        """Return the flattened observation vector for the requested mode."""
        builder = self.observation_builder if mode is None else get_observation_builder(mode)
        return builder.get_vector(self)

    def get_obs(self) -> np.ndarray:
        """Backward-compatible observation accessor."""
        return self.get_observation()

    def _build_base_info(self, contact_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build the shared info dictionary used by tasks and legacy scripts."""
        contact_state = contact_state or self._get_contact_state()
        is_contact = bool(contact_state["has_valid_contact"])
        is_grasp_contact = bool(contact_state["is_grasp_contact"])
        ground_contact = self._check_object_on_floor()

        return {
            "step": self.current_step,
            "control_timestep": self.control_timestep,
            "max_steps": self.max_steps,
            "distance": self._get_distance(),
            "contact": is_contact,
            "contact_duration": self.contact_duration,
            "grasp_contact": is_grasp_contact,
            "grasp_contact_duration": self.grasp_contact_duration,
            "palm_contact": contact_state["has_palm_contact"],
            "thumb_contact": contact_state["has_thumb_contact"],
            "palm_only_contact": contact_state["is_palm_only_contact"],
            "finger_contact_count": contact_state["finger_group_count"],
            "finger_contact_groups": contact_state["finger_groups"],
            "contact_body_names": contact_state["contact_body_names"],
            "object_on_floor": ground_contact,
            "object_height": self._get_object_height(),
            "catch_success": (is_grasp_contact and not ground_contact),
            "task_name": self.get_task_name(),
            "observation_mode": self.observation_mode,
            "backend_type": self.hand_adapter.get_backend_type(),
            "model_family": self.hand_adapter.get_model_family(),
        }

    def compute_default_reward(self, action: np.ndarray, info: Optional[Dict[str, Any]] = None) -> float:
        """Return the legacy environment reward."""
        reward_info = info or self._build_base_info()
        return self.compute_reward(action, is_contact=bool(reward_info.get("contact", False)))

    def compute_reward(self, action: np.ndarray, is_contact: Optional[bool] = None) -> float:
        """Return the default environment reward."""
        coeffs = self.reward_coeffs
        if is_contact is None:
            is_contact = self._check_contact()

        distance = self._get_distance()
        distance_reward = coeffs["distance"] * distance
        contact_reward = coeffs["contact"] if is_contact else 0.0
        maintain_reward = coeffs["maintain"] * self.contact_duration if is_contact else 0.0
        ground_contact = self._check_object_on_floor()
        catch_reward = coeffs["catch"] if (is_contact and not ground_contact) else 0.0
        ground_penalty = coeffs["ground_penalty"] if ground_contact else 0.0
        action_penalty = coeffs["action_penalty"] * np.sum(action ** 2)
        total_reward = (
            distance_reward
            + contact_reward
            + maintain_reward
            + catch_reward
            + ground_penalty
            + action_penalty
        )
        return float(total_reward)

    def _check_done(self, task_success: bool = False, task_failure: bool = False) -> bool:
        """Check whether the episode should terminate."""
        if self.current_step >= self.max_steps:
            return True
        if self.task is not None and (task_success or task_failure):
            return True
        return False

    def is_success(self) -> bool:
        """Check success for the active task or the legacy grasp rule."""
        if self.task is not None:
            return bool(self.task.check_success(self, info=self._build_base_info()))

        contact_success = self.grasp_contact_duration >= self.success_contact_duration
        if not self.enable_catch_task:
            return contact_success

        ground_contact = self._check_object_on_floor()
        return contact_success and (not ground_contact)

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """Execute one environment step."""
        if action.shape != (self.nu,):
            raise ValueError(f"鍔ㄤ綔褰㈢姸搴斾负 ({self.nu},)锛屼絾寰楀埌 {action.shape}")

        ctrl = self._normalize_action(action)
        self.data.ctrl[:] = ctrl
        mujoco.mj_step(self.model, self.data)
        self.current_step += 1

        contact_state = self._get_contact_state()
        is_contact = bool(contact_state["has_valid_contact"])
        is_grasp_contact = bool(contact_state["is_grasp_contact"])

        if is_contact:
            self.contact_duration += 1
        else:
            self.contact_duration = 0

        if is_grasp_contact:
            self.grasp_contact_duration += 1
        else:
            self.grasp_contact_duration = 0

        obs = self.get_obs()
        base_info = self._build_base_info(contact_state=contact_state)
        task_success = False
        task_failure = False

        if self.task is not None:
            reward = float(self.task.get_reward(self, action, info=base_info))
            task_success = bool(self.task.check_success(self, info=base_info))
            task_failure = bool(self.task.check_failure(self, info=base_info))
            info = dict(base_info)
            info.update(self.task.get_info(self, info=base_info) or {})
            info["success"] = task_success
            info["failure"] = task_failure
        else:
            reward = self.compute_default_reward(action, info=base_info)
            info = dict(base_info)
            info["success"] = self.is_success()
            info["failure"] = False

        done = self._check_done(task_success=task_success, task_failure=task_failure)
        return obs, reward, done, info

    def render(self, viewer=None):
        """渲染环境（可选，目前不实现）"""
        # 如果需要渲染，可以集成 mujoco.viewer
        pass

    def close(self):
        """关闭环境（清理资源）"""
        # 目前没有需要特殊清理的资源
        pass


# 测试代码
if __name__ == "__main__":
    # 创建环境
    env = ShadowGraspEnv(max_steps=100)

    # 测试重置
    print("\n=== 测试重置 ===")
    obs = env.reset()
    print(f"观测值形状: {obs.shape}")
    print(f"观测值范围: [{obs.min():.3f}, {obs.max():.3f}]")

    # 测试步进
    print("\n=== 测试步进 ===")
    action = np.random.uniform(-1, 1, size=env.nu)
    obs, reward, done, info = env.step(action)

    print(f"动作后观测值形状: {obs.shape}")
    print(f"奖励: {reward:.3f}")
    print(f"是否结束: {done}")
    print(f"信息: {info}")

    # 测试多个步进
    print("\n=== 测试多个步进 ===")
    for i in range(5):
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)
        print(f"步 {i+1}: 奖励={reward:.3f}, 距离={info['distance']:.3f}, 接触={info['contact']}")

    print("\n=== 环境测试完成 ===")
