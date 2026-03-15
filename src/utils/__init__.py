"""
工具模块 - 提供统一的路径处理、模型加载和查看器管理功能
"""

from .path_utils import (
    get_project_root,
    get_model_path,
    get_shadow_hand_model_path,
    get_arm26_model_path,
    get_tendon_model_path,
    check_model_path
)

from .model_loader import (
    load_model,
    load_shadow_hand_model,
    load_arm26_model,
    load_tendon_model,
    print_model_info,
    get_actuator_info
)

from .viewer_utils import (
    run_viewer_loop,
    run_viewer_with_control,
    create_viewer_context
)

__all__ = [
    # path_utils
    'get_project_root',
    'get_model_path',
    'get_shadow_hand_model_path',
    'get_arm26_model_path',
    'get_tendon_model_path',
    'check_model_path',

    # model_loader
    'load_model',
    'load_shadow_hand_model',
    'load_arm26_model',
    'load_tendon_model',
    'print_model_info',
    'get_actuator_info',

    # viewer_utils
    'run_viewer_loop',
    'run_viewer_with_control',
    'create_viewer_context'
]