"""
控制器模块 - 提供统一接口的各种Shadow Hand控制器

设计原则:
1. 所有控制器继承自 BaseController
2. 统一接口: compute_control(t, **kwargs)
3. 易于对比和替换
"""

from .base_controller import BaseController

# 导入具体控制器（将在重构后可用）
try:
    from .linear_controller import LinearController
    LINEAR_AVAILABLE = True
except ImportError:
    LINEAR_AVAILABLE = False
    LinearController = None

try:
    from .bio_controller import BioHandController
    BIO_AVAILABLE = True
except ImportError:
    BIO_AVAILABLE = False
    BioHandController = None

try:
    from .enhanced_controller import EnhancedHandController
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    EnhancedHandController = None


def get_available_controllers() -> dict:
    """
    获取可用的控制器列表

    返回:
        dict: 控制器名称到类的映射
    """
    controllers = {}

    if LINEAR_AVAILABLE:
        controllers['linear'] = LinearController
    if BIO_AVAILABLE:
        controllers['bio'] = BioHandController
    if ENHANCED_AVAILABLE:
        controllers['enhanced'] = EnhancedHandController

    return controllers


def create_controller(name: str, model, data, **kwargs):
    """
    工厂函数：按名称创建控制器实例

    参数:
        name: 控制器名称 ('linear', 'bio', 'enhanced')
        model: MuJoCo 模型
        data: MuJoCo 数据
        **kwargs: 传递给控制器构造函数的参数

    返回:
        BaseController: 控制器实例

    抛出:
        ValueError: 如果控制器名称无效
    """
    controllers = get_available_controllers()

    if name not in controllers:
        available = list(controllers.keys())
        raise ValueError(f"未知的控制器: '{name}'。可用: {available}")

    ControllerClass = controllers[name]
    return ControllerClass(model, data, **kwargs)


__all__ = [
    'BaseController',
    'LinearController',
    'BioHandController',
    'EnhancedHandController',
    'get_available_controllers',
    'create_controller'
]