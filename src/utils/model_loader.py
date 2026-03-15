"""
模型加载工具模块
统一处理模型加载逻辑，消除重复代码
"""

import os
import numpy as np
import mujoco
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Tuple, Union

from . import path_utils


@contextmanager
def model_loading_context(model_dir: Optional[Union[str, Path]] = None):
    """
    模型加载的上下文管理器
    处理工作目录切换，确保正确加载相对路径资源

    参数:
        model_dir: 模型文件所在目录，如果为None则不切换目录

    使用示例:
        with model_loading_context(model_dir):
            model = mujoco.MjModel.from_xml_path(model_file)
    """
    original_cwd = os.getcwd()

    try:
        if model_dir is not None:
            model_dir_path = Path(model_dir) if isinstance(model_dir, str) else model_dir
            os.chdir(str(model_dir_path.absolute()))
            yield
        else:
            yield
    finally:
        # 确保恢复原始工作目录
        os.chdir(original_cwd)


def load_shadow_hand_model(model_file: Optional[str] = None) -> Tuple[mujoco.MjModel, mujoco.MjData]:
    """
    加载 Shadow Hand 模型
    替换12个文件中的重复代码

    参数:
        model_file: 模型文件名，默认为 None（使用默认文件）

    返回:
        tuple: (model, data)
    """
    # 获取模型路径
    model_path = path_utils.get_shadow_hand_model_path(model_file)
    model_dir = model_path.parent

    print(f"加载模型: {model_path}")

    # 使用上下文管理器加载模型，处理工作目录切换
    with model_loading_context(model_dir):
        model = mujoco.MjModel.from_xml_path(model_path.name)
        data = mujoco.MjData(model)

    return model, data


def load_model(model_path: Union[str, Path],
              switch_working_dir: bool = True) -> Tuple[mujoco.MjModel, mujoco.MjData]:
    """
    通用模型加载函数

    参数:
        model_path: 模型文件路径
        switch_working_dir: 是否切换工作目录（用于处理相对路径资源）

    返回:
        tuple: (model, data)
    """
    model_path_obj = Path(model_path) if isinstance(model_path, str) else model_path

    if not model_path_obj.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path_obj}")

    print(f"加载模型: {model_path_obj}")

    model_dir = model_path_obj.parent if switch_working_dir else None

    with model_loading_context(model_dir):
        model = mujoco.MjModel.from_xml_path(model_path_obj.name if switch_working_dir else str(model_path_obj))
        data = mujoco.MjData(model)

    return model, data


def load_model_by_type(model_type: str = "shadow_hand",
                      model_file: Optional[str] = None) -> Tuple[mujoco.MjModel, mujoco.MjData]:
    """
    根据模型类型加载模型

    参数:
        model_type: 模型类型（shadow_hand, arm26, tendon）
        model_file: 具体的模型文件名

    返回:
        tuple: (model, data)
    """
    # 获取模型路径
    model_path = path_utils.get_model_path(model_type, model_type, model_file)

    # 根据模型类型决定是否需要切换工作目录
    # Shadow Hand 需要切换目录（因为有assets/等相对路径）
    # 简单的tendon.xml可能不需要
    switch_dir = model_type in ["shadow_hand", "arm26"]

    return load_model(model_path, switch_working_dir=switch_dir)


def load_arm26_model() -> Tuple[mujoco.MjModel, mujoco.MjData]:
    """
    加载 Arm26 模型（便捷函数）

    返回:
        tuple: (model, data)
    """
    return load_model_by_type("arm26")


def load_tendon_model() -> Tuple[mujoco.MjModel, mujoco.MjData]:
    """
    加载简单肌腱模型（便捷函数）

    返回:
        tuple: (model, data)
    """
    return load_model_by_type("tendon")


def print_model_info(model: mujoco.MjModel, data: mujoco.MjData):
    """打印模型基本信息"""
    print(f"模型信息:")
    print(f"  nq = {model.nq} (关节位置数)")
    print(f"  nv = {model.nv} (关节速度数)")
    print(f"  nu = {model.nu} (执行器数)")
    print(f"  nbody = {model.nbody} (刚体数)")
    print(f"  ntendon = {model.ntendon} (肌腱数)")
    print(f"  ngeom = {model.ngeom} (几何体数)")
    print(f"  nsensor = {model.nsensor} (传感器数)")

    if model.nu > 0:
        print(f"\n执行器数量: {model.nu}")


def get_actuator_info(model: mujoco.MjModel) -> dict:
    """
    获取执行器详细信息

    参数:
        model: MuJoCo 模型

    返回:
        包含执行器信息的字典
    """
    info = {
        'num_actuators': model.nu,
        'actuator_names': [],
        'actuator_types': [],
        'control_ranges': [],
        'is_limited': []
    }

    for i in range(model.nu):
        # 执行器名称
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        info['actuator_names'].append(name if name else f"actuator_{i}")

        # 执行器类型
        actuator_type = model.actuator_type[i]
        type_names = {
            0: 'motor',
            1: 'position',
            2: 'velocity',
            3: 'damper',
            4: 'tendon',
            5: 'crankset',
            6: 'suspension'
        }
        info['actuator_types'].append(type_names.get(actuator_type, f"unknown_{actuator_type}"))

        # 控制范围
        if model.actuator_ctrllimited[i]:
            ctrl_range = model.actuator_ctrlrange[i].tolist()
        else:
            ctrl_range = [-np.inf, np.inf] if hasattr(np, 'inf') else [-1e10, 1e10]
        info['control_ranges'].append(ctrl_range)

        # 是否有限制
        info['is_limited'].append(bool(model.actuator_ctrllimited[i]))

    return info


if __name__ == "__main__":
    # 测试代码
    print("=== 测试模型加载 ===")

    try:
        print("\n1. 加载 Shadow Hand 模型:")
        model1, data1 = load_shadow_hand_model()
        print_model_info(model1, data1)
    except Exception as e:
        print(f"错误: {e}")

    try:
        print("\n2. 加载 Arm26 模型:")
        model2, data2 = load_model_by_type("arm26")
        print_model_info(model2, data2)
    except Exception as e:
        print(f"错误: {e}")

    try:
        print("\n3. 加载 Tendon 模型:")
        model3, data3 = load_model_by_type("tendon")
        print_model_info(model3, data3)
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 测试完成 ===")