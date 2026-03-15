#!/usr/bin/env python3
"""
模型检查脚本

功能:
1. 加载指定模型（默认Shadow Hand）
2. 打印模型基本信息（nq, nv, nu）
3. 打印所有关节信息（名称、类型、范围）
4. 打印所有执行器信息（名称、控制范围、关联对象）
5. 打印所有肌腱信息（如有）

输出格式清晰，便于后续定义action/state空间。
"""

import argparse
import os
import sys
import numpy as np
import mujoco

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils import model_loader, path_utils


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='检查MuJoCo模型结构')

    parser.add_argument('--model', type=str, default='shadow_hand',
                       choices=['shadow_hand', 'arm26', 'tendon'],
                       help='要检查的模型类型')

    parser.add_argument('--file', type=str, default=None,
                       help='指定模型文件名（默认使用模型类型的默认文件）')

    parser.add_argument('--output', type=str, default='console',
                       choices=['console', 'json'],
                       help='输出格式')

    parser.add_argument('--no-color', action='store_true',
                       help='禁用颜色输出（适合重定向到文件）')

    return parser.parse_args()


def load_model(model_type, file_name=None):
    """加载模型"""
    try:
        if model_type == 'shadow_hand':
            model, data = model_loader.load_shadow_hand_model(file_name)
        elif model_type == 'arm26':
            model, data = model_loader.load_arm26_model()
        elif model_type == 'tendon':
            model, data = model_loader.load_tendon_model()
        else:
            raise ValueError(f"未知的模型类型: {model_type}")

        return model, data
    except FileNotFoundError as e:
        print(f"错误: 模型文件未找到")
        print(f"详情: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"模型加载错误: {e}")
        sys.exit(1)


def get_joint_type_name(joint_type):
    """将关节类型代码转换为可读名称"""
    type_names = {
        0: '自由关节 (mjJNT_FREE)',
        1: '球关节 (mjJNT_BALL)',
        2: '滑动关节 (mjJNT_SLIDE)',
        3: '铰链关节 (mjJNT_HINGE)',
    }
    return type_names.get(joint_type, f"未知类型 ({joint_type})")


def get_actuator_type_name(actuator_type):
    """将执行器类型代码转换为可读名称"""
    type_names = {
        0: '电机 (motor)',
        1: '位置 (position)',
        2: '速度 (velocity)',
        3: '阻尼器 (damper)',
        4: '肌腱 (tendon)',
        5: '曲柄组 (crankset)',
        6: '悬挂 (suspension)',
    }
    return type_names.get(actuator_type, f"未知类型 ({actuator_type})")


def get_actuator_target(model, actuator_idx):
    """获取执行器关联的目标对象信息"""
    # actuator_trnid包含传输对象索引
    # trntype: 0=关节, 1=刚体, 2=肌腱
    trnid = model.actuator_trnid[actuator_idx]  # shape: (2,) for each actuator
    trntype = model.actuator_trntype[actuator_idx]

    if trntype == 0:  # 关节
        joint_idx = int(trnid[0])
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_idx)
        return f"关节: {joint_name if joint_name else f'joint_{joint_idx}'} (索引: {joint_idx})"
    elif trntype == 1:  # 刚体
        body_idx = int(trnid[0])
        body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_idx)
        return f"刚体: {body_name if body_name else f'body_{body_idx}'} (索引: {body_idx})"
    elif trntype == 2:  # 肌腱
        tendon_idx = int(trnid[0])
        tendon_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_TENDON, tendon_idx)
        return f"肌腱: {tendon_name if tendon_name else f'tendon_{tendon_idx}'} (索引: {tendon_idx})"
    else:
        return f"未知目标类型: {trntype}"


def print_basic_info(model, data):
    """打印模型基本信息"""
    print("=" * 80)
    print("模型基本信息")
    print("=" * 80)

    print(f"nq = {model.nq} (关节位置数)")
    print(f"nv = {model.nv} (关节速度数)")
    print(f"nu = {model.nu} (执行器数)")
    print(f"nbody = {model.nbody} (刚体数)")
    print(f"njnt = {model.njnt} (关节数)")
    print(f"ntendon = {model.ntendon} (肌腱数)")
    print(f"ngeom = {model.ngeom} (几何体数)")
    print(f"nsensor = {model.nsensor} (传感器数)")
    print(f"nmocap = {model.nmocap} (运动捕捉体数)")
    print()


def print_joint_info(model):
    """打印关节详细信息"""
    print("=" * 80)
    print("关节信息")
    print("=" * 80)

    if model.njnt == 0:
        print("模型中没有关节")
        print()
        return

    # 打印表头
    header = f"{'索引':<6} {'名称':<30} {'类型':<25} {'范围':<20} {'是否受限':<10}"
    print(header)
    print("-" * len(header))

    for i in range(model.njnt):
        # 关节名称
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        display_name = name if name else f"joint_{i}"

        # 关节类型
        jnt_type = model.jnt_type[i]
        type_name = get_joint_type_name(jnt_type)

        # 关节范围
        if model.jnt_limited[i]:
            jnt_range = model.jnt_range[i].tolist()  # shape: (2,) for each joint
            range_str = f"[{float(jnt_range[0]):.4f}, {float(jnt_range[1]):.4f}]"
        else:
            range_str = "无限制"

        # 是否受限
        limited = "是" if model.jnt_limited[i] else "否"

        # 打印行
        print(f"{i:<6} {display_name:<30} {type_name:<25} {range_str:<20} {limited:<10}")

    print()


def print_actuator_info(model):
    """打印执行器详细信息"""
    print("=" * 80)
    print("执行器信息")
    print("=" * 80)

    if model.nu == 0:
        print("模型中没有执行器")
        print()
        return

    # 打印表头
    header = f"{'索引':<6} {'名称':<30} {'类型':<25} {'控制范围':<20} {'关联对象':<40}"
    print(header)
    print("-" * len(header))

    for i in range(model.nu):
        # 执行器名称
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        display_name = name if name else f"actuator_{i}"

        # 执行器类型
        actuator_type = model.actuator_dyntype[i]
        type_name = get_actuator_type_name(actuator_type)

        # 控制范围
        if model.actuator_ctrllimited[i]:
            ctrl_range = model.actuator_ctrlrange[i].tolist()  # shape: (2,) for each actuator
            range_str = f"[{float(ctrl_range[0]):.4f}, {float(ctrl_range[1]):.4f}]"
        else:
            range_str = "无限制"

        # 关联对象
        target = get_actuator_target(model, i)

        # 打印行
        print(f"{i:<6} {display_name:<30} {type_name:<25} {range_str:<20} {target:<40}")

    print()


def print_tendon_info(model):
    """打印肌腱信息"""
    print("=" * 80)
    print("肌腱信息")
    print("=" * 80)

    if model.ntendon == 0:
        print("模型中没有肌腱")
        print()
        return

    # 打印表头
    header = f"{'索引':<6} {'名称':<40}"
    print(header)
    print("-" * len(header))

    for i in range(model.ntendon):
        # 肌腱名称
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_TENDON, i)
        display_name = name if name else f"tendon_{i}"

        # 打印行
        print(f"{i:<6} {display_name:<40}")

    print()


def print_summary_for_action_state(model):
    """打印用于定义action/state空间的摘要信息"""
    print("=" * 80)
    print("Action/State 空间定义参考")
    print("=" * 80)

    print(f"\n1. 关节空间 (用于状态观测)")
    print(f"   关节位置 (qpos) 维度: {model.nq}")
    print(f"   关节速度 (qvel) 维度: {model.nv}")

    if model.njnt > 0:
        print(f"   关节列表:")
        for i in range(model.njnt):
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
            display_name = name if name else f"joint_{i}"
            jnt_type = model.jnt_type[i]

            if jnt_type == 0:  # 自由关节 (6个自由度)
                dof_str = "6DOF (位置+旋转)"
            elif jnt_type == 1:  # 球关节 (3个自由度)
                dof_str = "3DOF (旋转)"
            elif jnt_type == 2:  # 滑动关节 (1个自由度)
                dof_str = "1DOF (平移)"
            elif jnt_type == 3:  # 铰链关节 (1个自由度)
                dof_str = "1DOF (旋转)"
            else:
                dof_str = "未知"

            print(f"     - {display_name}: {dof_str}")

    print(f"\n2. 执行器空间 (用于动作控制)")
    print(f"   执行器控制 (ctrl) 维度: {model.nu}")

    if model.nu > 0:
        print(f"   执行器列表:")
        for i in range(model.nu):
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
            display_name = name if name else f"actuator_{i}"
            actuator_type = model.actuator_dyntype[i]

            # 获取控制范围
            if model.actuator_ctrllimited[i]:
                ctrl_range = model.actuator_ctrlrange[i].tolist()  # shape: (2,) for each actuator
                range_str = f"[{float(ctrl_range[0]):.4f}, {float(ctrl_range[1]):.4f}]"
            else:
                range_str = "无限制"

            print(f"     - {display_name}: {get_actuator_type_name(actuator_type)}, 范围: {range_str}")

    print(f"\n3. 肌腱空间")
    print(f"   肌腱数量: {model.ntendon}")

    if model.ntendon > 0:
        print(f"   肌腱列表:")
        for i in range(model.ntendon):
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_TENDON, i)
            display_name = name if name else f"tendon_{i}"
            print(f"     - {display_name}")

    print()


def output_json(model, data, args):
    """以JSON格式输出模型信息"""
    import json

    info = {
        'basic_info': {
            'nq': int(model.nq),
            'nv': int(model.nv),
            'nu': int(model.nu),
            'nbody': int(model.nbody),
            'njnt': int(model.njnt),
            'ntendon': int(model.ntendon),
            'ngeom': int(model.ngeom),
            'nsensor': int(model.nsensor),
            'nmocap': int(model.nmocap),
        },
        'joints': [],
        'actuators': [],
        'tendons': []
    }

    # 关节信息
    for i in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        joint_info = {
            'index': i,
            'name': name if name else f"joint_{i}",
            'type': int(model.jnt_type[i]),
            'type_name': get_joint_type_name(model.jnt_type[i]),
            'limited': bool(model.jnt_limited[i]),
            'range': model.jnt_range[i].tolist() if model.jnt_limited[i] else None,  # shape: (2,) for each joint
        }
        info['joints'].append(joint_info)

    # 执行器信息
    for i in range(model.nu):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        actuator_info = {
            'index': i,
            'name': name if name else f"actuator_{i}",
            'type': int(model.actuator_dyntype[i]),
            'type_name': get_actuator_type_name(model.actuator_dyntype[i]),
            'limited': bool(model.actuator_ctrllimited[i]),
            'ctrl_range': model.actuator_ctrlrange[i].tolist() if model.actuator_ctrllimited[i] else None,  # shape: (2,) for each actuator
            'target': get_actuator_target(model, i),
        }
        info['actuators'].append(actuator_info)

    # 肌腱信息
    for i in range(model.ntendon):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_TENDON, i)
        tendon_info = {
            'index': i,
            'name': name if name else f"tendon_{i}",
        }
        info['tendons'].append(tendon_info)

    print(json.dumps(info, indent=2))


def main():
    """主函数"""
    args = parse_args()

    print(f"检查模型: {args.model}")
    if args.file:
        print(f"指定文件: {args.file}")

    # 加载模型
    model, data = load_model(args.model, args.file)

    # 根据输出格式选择输出方式
    if args.output == 'json':
        output_json(model, data, args)
        return

    # 控制台输出
    print_basic_info(model, data)
    print_joint_info(model)
    print_actuator_info(model)
    print_tendon_info(model)
    print_summary_for_action_state(model)

    print("=" * 80)
    print("模型检查完成")
    print("=" * 80)


if __name__ == "__main__":
    main()