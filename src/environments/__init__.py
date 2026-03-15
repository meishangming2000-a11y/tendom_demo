"""
环境模块 - 为阶段3（训练管线底座）预留

设计原则:
1. 保持与 gymnasium 兼容的接口
2. 控制器可作为环境的"专家示范"
3. 支持多种任务（接近、抓取、操控等）
"""

__all__ = ["ShadowGraspEnv"]  # 环境类列表

# 导入环境类
from .shadow_grasp_env import ShadowGraspEnv