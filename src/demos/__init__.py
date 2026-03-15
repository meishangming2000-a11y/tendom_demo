"""
演示模块 - 提供各种控制器演示

设计原则:
1. 每个演示文件应独立运行
2. 支持命令行参数选择控制器
3. 提供一致的演示体验
"""

import os
import sys

# 添加项目根目录到Python路径
_project_root = os.path.join(os.path.dirname(__file__), '..', '..')
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

__all__ = []  # 将在重构后添加具体演示