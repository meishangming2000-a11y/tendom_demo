"""
路径处理工具模块
统一处理项目中的模型路径，消除重复代码
"""

import os
from pathlib import Path
from typing import Optional, Union

# 项目根目录（假设utils目录在项目根目录下）
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

# 预定义的模型路径配置
MODEL_PATHS = {
    "shadow_hand": {
        "base_dir": PROJECT_ROOT / "models" / "shadow_hand",
        "default_file": "scene_right.xml",
        "alternative_files": ["right_hand.xml"]
    },
    "arm26": {
        "base_dir": PROJECT_ROOT / "models",
        "default_file": "arm26.xml",
    },
    "tendon": {
        "base_dir": PROJECT_ROOT / "models",
        "default_file": "tendon.xml",
    }
}


def get_shadow_hand_model_path(file_name: Optional[str] = None) -> Path:
    """
    获取 Shadow Hand 模型路径
    替换10个文件中的重复代码

    参数:
        file_name: 模型文件名，默认为 "scene_right.xml"

    返回:
        Path: 完整的模型文件路径
    """
    config = MODEL_PATHS["shadow_hand"]
    base_dir = config["base_dir"]

    if file_name is None:
        file_name = config["default_file"]

    model_path = base_dir / file_name

    # 检查文件是否存在
    if not model_path.exists():
        # 尝试其他可能的文件名
        for alt_file in config.get("alternative_files", []):
            alt_path = base_dir / alt_file
            if alt_path.exists():
                print(f"警告: 使用备用文件 {alt_file} 替代 {file_name}")
                return alt_path

        raise FileNotFoundError(
            f"Shadow Hand 模型文件不存在: {model_path}\n"
            f"请检查路径是否正确: {base_dir}"
        )

    return model_path


def get_model_path(model_name: str, model_type: str = "shadow_hand",
                  file_name: Optional[str] = None) -> Path:
    """
    通用模型路径获取函数

    参数:
        model_name: 模型名称标识符
        model_type: 模型类型，默认为 "shadow_hand"
        file_name: 具体的文件名，如果为None则使用默认文件

    返回:
        Path: 完整的模型文件路径
    """
    if model_type not in MODEL_PATHS:
        raise ValueError(f"未知的模型类型: {model_type}。可选: {list(MODEL_PATHS.keys())}")

    config = MODEL_PATHS[model_type]
    base_dir = config["base_dir"]

    if file_name is None:
        file_name = config["default_file"]

    model_path = base_dir / file_name

    if not model_path.exists():
        # 对于shadow_hand，尝试备用文件
        if model_type == "shadow_hand":
            for alt_file in config.get("alternative_files", []):
                alt_path = base_dir / alt_file
                if alt_path.exists():
                    print(f"警告: 使用备用文件 {alt_file} 替代 {file_name}")
                    return alt_path

        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    return model_path


def get_arm26_model_path() -> Path:
    """
    获取 Arm26 模型路径

    返回:
        Path: arm26.xml 文件的完整路径
    """
    return get_model_path("arm26", model_type="arm26")


def get_tendon_model_path() -> Path:
    """
    获取简单肌腱模型路径

    返回:
        Path: tendon.xml 文件的完整路径
    """
    return get_model_path("tendon", model_type="tendon")


def check_model_path(model_type: str = "shadow_hand") -> bool:
    """
    检查模型路径是否存在

    参数:
        model_type: 模型类型

    返回:
        bool: 路径是否存在
    """
    try:
        if model_type == "shadow_hand":
            path = get_shadow_hand_model_path()
        elif model_type == "arm26":
            path = get_arm26_model_path()
        elif model_type == "tendon":
            path = get_tendon_model_path()
        else:
            path = get_model_path(model_type, model_type)

        return path.exists()
    except Exception:
        return False


def get_project_root() -> Path:
    """获取项目根目录路径"""
    return PROJECT_ROOT


def ensure_path_exists(path: Union[str, Path]) -> Path:
    """确保路径存在，如果不存在则创建目录"""
    path_obj = Path(path) if isinstance(path, str) else path

    if path_obj.is_dir():
        # 如果是目录，确保目录存在
        path_obj.mkdir(parents=True, exist_ok=True)
    else:
        # 如果是文件，确保父目录存在
        path_obj.parent.mkdir(parents=True, exist_ok=True)

    return path_obj


def convert_to_absolute_path(relative_path: Union[str, Path],
                           reference_path: Optional[Union[str, Path]] = None) -> Path:
    """
    将相对路径转换为绝对路径

    参数:
        relative_path: 相对路径
        reference_path: 参考路径（默认为当前文件所在目录）

    返回:
        Path: 绝对路径
    """
    if reference_path is None:
        # 默认使用调用者文件所在的目录
        import inspect
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        reference_path = Path(caller_file).parent

    ref_path = Path(reference_path) if isinstance(reference_path, str) else reference_path
    rel_path = Path(relative_path) if isinstance(relative_path, str) else relative_path

    # 如果已经是绝对路径，直接返回
    if rel_path.is_absolute():
        return rel_path

    # 转换为绝对路径
    absolute_path = (ref_path / rel_path).resolve()

    return absolute_path


def validate_model_path(model_path: Union[str, Path]) -> bool:
    """验证模型路径是否存在"""
    path_obj = Path(model_path) if isinstance(model_path, str) else model_path
    return path_obj.exists()


if __name__ == "__main__":
    # 测试代码
    print("项目根目录:", get_project_root())

    try:
        shadow_path = get_shadow_hand_model_path()
        print("Shadow Hand 路径:", shadow_path)
        print("文件存在:", validate_model_path(shadow_path))
    except Exception as e:
        print(f"错误: {e}")

    try:
        arm26_path = get_model_path("arm26", model_type="arm26")
        print("Arm26 路径:", arm26_path)
        print("文件存在:", validate_model_path(arm26_path))
    except Exception as e:
        print(f"错误: {e}")

    try:
        tendon_path = get_model_path("tendon", model_type="tendon")
        print("Tendon 路径:", tendon_path)
        print("文件存在:", validate_model_path(tendon_path))
    except Exception as e:
        print(f"错误: {e}")