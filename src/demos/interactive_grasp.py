"""
交互式物体抓取与操控演示
基于 MuJoCo 和 Shadow Hand 的复杂控制演示

功能特点:
1. 增强型控制器，支持力反馈和自适应抓取
2. 物体检测与定位
3. 键盘实时控制 (WASD/方向键移动，空格抓取)
4. 轨迹规划和协调运动
5. 实时状态显示和可视化反馈
"""

import time
import mujoco
import mujoco.viewer
import os
import sys
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

# 添加项目根目录到Python路径，以便导入utils模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入统一工具模块
from utils import model_loader
from utils.enhanced_controller import EnhancedHandController

# 尝试导入键盘控制库
try:
    import pynput
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    print("警告: pynput 未安装，键盘控制功能受限")
    print("安装: pip install pynput")
    KEYBOARD_AVAILABLE = False




class KeyboardController:
    """键盘控制管理器"""

    def __init__(self):
        self.keys_pressed = set()
        self.listener = None
        self.control_state = {
            'move_x': 0,   # -1:左, 0:不动, 1:右
            'move_y': 0,   # -1:后, 0:不动, 1:前
            'move_z': 0,   # -1:下, 0:不动, 1:上
            'grasp': False,
            'release': False,
            'reset': False,
            'mode': 0      # 0:位置控制, 1:力混合控制
        }

        if KEYBOARD_AVAILABLE:
            self._setup_keyboard_listener()

    def _setup_keyboard_listener(self):
        """设置键盘监听器"""
        def on_press(key):
            try:
                key_char = key.char.lower()
            except AttributeError:
                key_char = None

            # 处理按键
            if key_char == 'w' or key == keyboard.Key.up:
                self.control_state['move_y'] = 1
            elif key_char == 's' or key == keyboard.Key.down:
                self.control_state['move_y'] = -1
            elif key_char == 'a' or key == keyboard.Key.left:
                self.control_state['move_x'] = -1
            elif key_char == 'd' or key == keyboard.Key.right:
                self.control_state['move_x'] = 1
            elif key_char == 'q':
                self.control_state['move_z'] = 1  # 上移
            elif key_char == 'e':
                self.control_state['move_z'] = -1  # 下移
            elif key_char == ' ':
                self.control_state['grasp'] = True
            elif key_char == 'r':
                self.control_state['reset'] = True
            elif key_char == '1':
                self.control_state['mode'] = 0
            elif key_char == '2':
                self.control_state['mode'] = 1

        def on_release(key):
            try:
                key_char = key.char.lower()
            except AttributeError:
                key_char = None

            # 释放按键时重置移动状态
            if key_char == 'w' or key == keyboard.Key.up:
                if self.control_state['move_y'] == 1:
                    self.control_state['move_y'] = 0
            elif key_char == 's' or key == keyboard.Key.down:
                if self.control_state['move_y'] == -1:
                    self.control_state['move_y'] = 0
            elif key_char == 'a' or key == keyboard.Key.left:
                if self.control_state['move_x'] == -1:
                    self.control_state['move_x'] = 0
            elif key_char == 'd' or key == keyboard.Key.right:
                if self.control_state['move_x'] == 1:
                    self.control_state['move_x'] = 0
            elif key_char == 'q' or key_char == 'e':
                self.control_state['move_z'] = 0
            elif key_char == ' ':
                self.control_state['grasp'] = False
            elif key_char == 'r':
                self.control_state['reset'] = False

        # 启动监听器
        self.listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release)
        self.listener.start()

    def get_control_state(self) -> Dict[str, Any]:
        """获取当前控制状态"""
        return self.control_state.copy()

    def stop(self):
        """停止键盘监听"""
        if self.listener:
            self.listener.stop()


def print_controls():
    """打印控制说明"""
    print("\n" + "="*60)
    print("交互式抓取演示 - 控制说明")
    print("="*60)
    print("移动控制:")
    print("  W / ↑     : 向前移动")
    print("  S / ↓     : 向后移动")
    print("  A / ←     : 向左移动")
    print("  D / →     : 向右移动")
    print("  Q         : 向上移动")
    print("  E         : 向下移动")
    print("\n抓取控制:")
    print("  空格键     : 抓取/释放切换")
    print("  R         : 重置场景")
    print("\n模式切换:")
    print("  1         : 位置控制模式")
    print("  2         : 力混合控制模式")
    print("\n状态查看:")
    print("  P         : 打印当前状态")
    print("  ESC       : 退出演示")
    print("="*60)


def main_demo():
    """主演示函数"""
    print("="*60)
    print("Shadow Hand 交互式物体抓取演示")
    print("="*60)

    # 加载模型
    try:
        model, data = model_loader.load_shadow_hand_model()
    except Exception as e:
        print(f"模型加载错误: {e}")
        print("请确保模型文件存在且路径正确。")
        return

    # 创建增强控制器
    controller = EnhancedHandController(model, data)

    # 创建键盘控制器
    keyboard_ctrl = KeyboardController()

    # 打印控制说明
    print_controls()

    print("\n正在启动查看器...")
    print("按 ESC 键或关闭查看器窗口退出演示")

    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            print("查看器已启动！")

            last_print_time = time.time()
            print_interval = 2.0  # 每2秒打印一次状态

            while viewer.is_running():
                # 获取键盘输入
                ctrl_state = keyboard_ctrl.get_control_state()

                # 处理移动控制
                move_speed = 0.005
                hand_pos = controller.get_hand_position()

                # 计算目标位置偏移
                target_offset = np.array([
                    ctrl_state['move_x'] * move_speed,
                    ctrl_state['move_y'] * move_speed,
                    ctrl_state['move_z'] * move_speed
                ])

                # 更新目标位置
                controller.target_position = hand_pos + target_offset

                # 移动到目标位置
                controller.move_hand_to_position(controller.target_position, speed=0.02)

                # 处理抓取控制
                if ctrl_state['grasp']:
                    if not controller.is_grasping:
                        # 开始抓取
                        print("开始自适应抓取...")
                        controller.adaptive_grasp(target_strength=0.7)
                    else:
                        # 持续调整抓取
                        result = controller.adaptive_grasp(target_strength=0.7)

                        # 如果抓取质量好，可以移动物体（简化实现）
                        if result['grasp_quality'] > 0.6:
                            # 这里可以添加物体跟随手部移动的逻辑
                            pass
                else:
                    if controller.is_grasping:
                        print("释放抓取...")
                        controller.release_grasp()

                # 处理重置
                if ctrl_state['reset']:
                    print("重置场景...")
                    mujoco.mj_resetData(model, data)
                    controller.release_grasp()
                    ctrl_state['reset'] = False

                # 处理模式切换
                if ctrl_state['mode'] == 0:
                    controller.control_mode = 'position'
                elif ctrl_state['mode'] == 1:
                    controller.control_mode = 'force_hybrid'

                # 定期打印状态
                current_time = time.time()
                if current_time - last_print_time > print_interval:
                    controller.print_status()
                    last_print_time = current_time

                # 执行模拟步
                mujoco.mj_step(model, data)
                viewer.sync()

                # 控制循环速度
                time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n演示被用户中断。")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        keyboard_ctrl.stop()
        print("演示结束。")


def auto_demo_mode():
    """自动演示模式（不需要键盘交互）"""
    print("="*60)
    print("Shadow Hand 自动抓取演示")
    print("="*60)

    # 加载模型
    try:
        model, data = model_loader.load_shadow_hand_model()
    except Exception as e:
        print(f"模型加载错误: {e}")
        return

    # 创建增强控制器
    controller = EnhancedHandController(model, data)

    print("\n开始自动演示流程...")

    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            print("查看器已启动！")

            # 阶段1: 移动到物体附近
            print("\n阶段1: 接近物体")
            obj_pos = controller.get_object_position()
            if obj_pos is not None:
                # 设置接近位置（物体上方）
                approach_pos = obj_pos + np.array([0.0, 0.0, 0.05])
                controller.generate_trajectory(controller.get_hand_position(), approach_pos, 30)

                # 跟随轨迹
                for _ in range(50):
                    if not viewer.is_running():
                        break

                    completed, target = controller.follow_trajectory()
                    controller.move_hand_to_position(target, speed=0.03)

                    mujoco.mj_step(model, data)
                    viewer.sync()
                    time.sleep(0.02)

            time.sleep(1.0)

            # 阶段2: 自适应抓取
            print("\n阶段2: 自适应抓取")
            for step in range(100):
                if not viewer.is_running():
                    break

                result = controller.adaptive_grasp(target_strength=0.75)

                # 打印抓取进度
                if step % 20 == 0:
                    print(f"  抓取力度: {result['grasp_strength']:.3f}, "
                          f"接触力: {result['contact_force']:.4f}, "
                          f"质量: {result['grasp_quality']:.3f}")

                mujoco.mj_step(model, data)
                viewer.sync()
                time.sleep(0.02)

            time.sleep(2.0)

            # 阶段3: 移动物体
            print("\n阶段3: 移动物体（如果抓取成功）")
            if controller.calculate_grasp_quality() > 0.5:
                # 生成移动轨迹
                start_pos = controller.get_hand_position()
                end_pos = start_pos + np.array([0.1, 0.0, 0.05])
                controller.generate_trajectory(start_pos, end_pos, 40)

                for _ in range(50):
                    if not viewer.is_running():
                        break

                    completed, target = controller.follow_trajectory()
                    controller.move_hand_to_position(target, speed=0.02)

                    # 持续调整抓取
                    controller.adaptive_grasp(target_strength=0.7)

                    mujoco.mj_step(model, data)
                    viewer.sync()
                    time.sleep(0.02)

            time.sleep(2.0)

            # 阶段4: 释放物体
            print("\n阶段4: 释放物体")
            controller.release_grasp()

            for _ in range(30):
                if not viewer.is_running():
                    break

                mujoco.mj_step(model, data)
                viewer.sync()
                time.sleep(0.02)

            print("\n自动演示完成！")
            print("保持最终状态，关闭窗口退出。")

            # 保持最终状态
            while viewer.is_running():
                mujoco.mj_step(model, data)
                viewer.sync()
                time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n演示被用户中断。")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Shadow Hand 交互式物体抓取演示')
    parser.add_argument('--auto', action='store_true',
                       help='运行自动演示模式（不需要键盘）')
    parser.add_argument('--no-keyboard', action='store_true',
                       help='禁用键盘控制（即使pynput可用）')

    args = parser.parse_args()

    if args.auto:
        auto_demo_mode()
    else:
        if args.no_keyboard:
            global KEYBOARD_AVAILABLE
            KEYBOARD_AVAILABLE = False
            print("键盘控制已禁用")

        main_demo()


if __name__ == "__main__":
    main()