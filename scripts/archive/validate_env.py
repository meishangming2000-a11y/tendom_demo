#!/usr/bin/env python3
"""
环境验证脚本
全面验证 ShadowGraspEnv 的各个组件
"""

import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.environments.shadow_grasp_env import ShadowGraspEnv


def test_reset_consistency():
    """测试重置一致性：多次重置应该返回相同的观测值（在随机性允许范围内）"""
    print("=" * 60)
    print("测试1: 重置一致性")
    print("=" * 60)

    env = ShadowGraspEnv(max_steps=100)

    # 多次重置并比较观测值
    obs_list = []
    for i in range(5):
        obs = env.reset()
        obs_list.append(obs)
        print(f"  重置 {i+1}: 观测值形状={obs.shape}, 范围=[{obs.min():.3f}, {obs.max():.3f}]")

    # 检查观测值是否相似（允许微小差异）
    obs_array = np.array(obs_list)
    mean_obs = np.mean(obs_array, axis=0)
    std_obs = np.std(obs_array, axis=0)

    print(f"\n  观测值统计:")
    print(f"    均值范围: [{mean_obs.min():.3f}, {mean_obs.max():.3f}]")
    print(f"    标准差范围: [{std_obs.min():.3f}, {std_obs.max():.3f}]")
    print(f"    最大标准差: {std_obs.max():.6f}")

    # 如果标准差很小，说明重置一致
    if std_obs.max() < 0.01:
        print(f"  ✓ 重置一致性: 良好")
    else:
        print(f"  ⚠ 重置一致性: 有差异（可能模型有随机初始化）")

    return env


def test_action_normalization(env):
    """测试动作归一化：验证动作范围映射是否正确"""
    print("\n" + "=" * 60)
    print("测试2: 动作归一化")
    print("=" * 60)

    # 测试边界动作
    test_actions = [
        ("全-1", np.full(env.nu, -1.0)),
        ("全0", np.zeros(env.nu)),
        ("全+1", np.full(env.nu, 1.0)),
        ("随机", np.random.uniform(-1, 1, size=env.nu)),
    ]

    for name, action in test_actions:
        ctrl = env._normalize_action(action)

        # 检查控制信号是否在执行器范围内
        for i in range(env.nu):
            ctrl_min, ctrl_max = env.actuator_ctrlrange[i]
            if ctrl[i] < ctrl_min - 0.001 or ctrl[i] > ctrl_max + 0.001:
                print(f"  ⚠ {name}: 执行器{i}控制信号{ctrl[i]:.3f}超出范围[{ctrl_min:.3f}, {ctrl_max:.3f}]")
                break
        else:
            print(f"  ✓ {name}: 所有{env.nu}个执行器控制信号在范围内")

        # 打印示例
        if name == "全-1":
            print(f"    示例: action[-1] -> ctrl[{ctrl[0]:.3f}, ..., {ctrl[-1]:.3f}]")

    return True


def test_contact_detection(env):
    """测试接触检测：验证接触检测逻辑"""
    print("\n" + "=" * 60)
    print("测试3: 接触检测")
    print("=" * 60)

    obs = env.reset()

    print(f"  物体主体ID: {env.object_body_id}")
    print(f"  手部主体ID: {env.hand_body_id}")
    print(f"  地面主体ID: {env.floor_body_id}")

    # 获取初始距离
    initial_distance = env._get_distance()
    print(f"  初始距离: {initial_distance:.3f}")

    # 运行几步看是否有接触
    has_contact = False
    for i in range(20):
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)

        if info['contact']:
            has_contact = True
            print(f"  第{i+1}步检测到接触!")
            print(f"    距离: {info['distance']:.3f}")
            print(f"    奖励: {reward:.3f}")
            print(f"    接触持续时间: {info['contact_duration']}")
            break

    if not has_contact:
        print(f"  前20步未检测到接触（正常，随机动作可能无法接触）")

    return has_contact


def test_reward_calculation(env):
    """测试奖励计算：验证奖励组件是否正确"""
    print("\n" + "=" * 60)
    print("测试4: 奖励计算")
    print("=" * 60)

    obs = env.reset()

    # 测试零动作的奖励
    zero_action = np.zeros(env.nu)
    obs, zero_reward, done, info = env.step(zero_action)

    print(f"  零动作奖励: {zero_reward:.3f}")
    print(f"  零动作距离: {info['distance']:.3f}")
    print(f"  零动作接触: {info['contact']}")

    # 计算预期奖励
    distance = info['distance']
    is_contact = info['contact']
    contact_duration = info['contact_duration']

    expected_reward = (
        env.reward_coeffs['distance'] * distance +
        (env.reward_coeffs['contact'] if is_contact else 0.0) +
        (env.reward_coeffs['maintain'] * contact_duration if is_contact else 0.0) +
        env.reward_coeffs['action_penalty'] * np.sum(zero_action ** 2)
    )

    print(f"  预期奖励: {expected_reward:.3f}")
    print(f"  实际奖励: {zero_reward:.3f}")

    if abs(zero_reward - expected_reward) < 0.001:
        print(f"  ✓ 奖励计算正确")
    else:
        print(f"  ⚠ 奖励计算有差异: 差值={abs(zero_reward - expected_reward):.6f}")

    # 测试动作惩罚
    print(f"\n  测试动作惩罚:")
    large_action = np.full(env.nu, 0.5)
    obs, large_reward, done, info = env.step(large_action)

    action_penalty = env.reward_coeffs['action_penalty'] * np.sum(large_action ** 2)
    print(f"    动作幅度0.5的惩罚: {action_penalty:.6f}")
    print(f"    总奖励: {large_reward:.3f}")

    return True


def test_success_condition(env):
    """测试成功条件：验证连续接触50步后成功"""
    print("\n" + "=" * 60)
    print("测试5: 成功条件")
    print("=" * 60)

    print(f"  成功条件: 连续接触{env.success_contact_duration}步")

    # 重置环境
    obs = env.reset()

    # 尝试保持接触（使用随机动作，不一定能保持）
    success_steps = 0
    for i in range(100):
        action = np.random.uniform(-1, 1, size=env.nu)
        obs, reward, done, info = env.step(action)

        if info['contact']:
            success_steps += 1
        else:
            success_steps = 0

        if i % 20 == 0:
            print(f"    第{i+1}步: 接触={info['contact']}, 持续时间={info['contact_duration']}, 成功={info['success']}")

        if info['success']:
            print(f"  ✓ 第{i+1}步达到成功条件!")
            print(f"    连续接触步数: {info['contact_duration']}")
            return True

    print(f"  ⚠ 100步内未达到成功条件（随机动作可能无法保持接触）")
    print(f"    最长连续接触: {info['contact_duration']}步")
    return False


def test_observation_space(env):
    """测试观测空间：验证观测值维度是否正确"""
    print("\n" + "=" * 60)
    print("测试6: 观测空间")
    print("=" * 60)

    obs = env.reset()

    # 计算预期维度
    expected_dim = env.nq + env.nv + 3 + 3 + 3  # qpos + qvel + hand_pos + obj_pos + rel_pos
    actual_dim = obs.shape[0]

    print(f"  预期维度: {expected_dim}")
    print(f"  实际维度: {actual_dim}")

    if expected_dim == actual_dim:
        print(f"  ✓ 观测维度正确")
    else:
        print(f"  ✗ 观测维度错误: 预期{expected_dim}, 实际{actual_dim}")

    # 验证各组件
    print(f"\n  观测值组成:")
    print(f"    qpos (关节位置): 索引 0-{env.nq-1}, 实际值范围 [{obs[0]:.3f}, {obs[env.nq-1]:.3f}]")
    print(f"    qvel (关节速度): 索引 {env.nq}-{env.nq+env.nv-1}, 实际值范围 [{obs[env.nq]:.3f}, {obs[env.nq+env.nv-1]:.3f}]")

    hand_start = env.nq + env.nv
    hand_end = hand_start + 3 - 1
    obj_start = hand_end + 1
    obj_end = obj_start + 3 - 1
    rel_start = obj_end + 1
    rel_end = rel_start + 3 - 1

    print(f"    hand_pos (手部位置): 索引 {hand_start}-{hand_end}, 值 [{obs[hand_start]:.3f}, {obs[hand_start+1]:.3f}, {obs[hand_start+2]:.3f}]")
    print(f"    obj_pos (物体位置): 索引 {obj_start}-{obj_end}, 值 [{obs[obj_start]:.3f}, {obs[obj_start+1]:.3f}, {obs[obj_start+2]:.3f}]")
    print(f"    rel_pos (相对位置): 索引 {rel_start}-{rel_end}, 值 [{obs[rel_start]:.3f}, {obs[rel_start+1]:.3f}, {obs[rel_start+2]:.3f}]")

    # 验证相对位置 = hand_pos - obj_pos
    hand_pos = obs[hand_start:hand_start+3]
    obj_pos = obs[obj_start:obj_start+3]
    rel_pos = obs[rel_start:rel_start+3]
    expected_rel = hand_pos - obj_pos

    if np.allclose(rel_pos, expected_rel, atol=0.001):
        print(f"  ✓ 相对位置计算正确")
    else:
        print(f"  ⚠ 相对位置计算有误")
        print(f"    实际: {rel_pos}")
        print(f"    预期: {expected_rel}")

    return expected_dim == actual_dim


def main():
    """主函数"""
    print("ShadowGraspEnv 全面验证")
    print("=" * 60)

    # 创建环境
    env = ShadowGraspEnv(max_steps=200)

    # 运行各个测试
    test_reset_consistency()
    test_action_normalization(env)
    test_contact_detection(env)
    test_reward_calculation(env)
    test_success_condition(env)
    test_observation_space(env)

    # 环境总结
    print("\n" + "=" * 60)
    print("环境验证总结")
    print("=" * 60)

    obs = env.get_obs()
    print(f"环境基本信息:")
    print(f"  动作空间维度: {env.nu}")
    print(f"  观测空间维度: {obs.shape[0]}")
    print(f"  最大步数: {env.max_steps}")
    print(f"  控制时间步长: {env.control_timestep}")
    print(f"  物体主体ID: {env.object_body_id}")
    print(f"  手部主体ID: {env.hand_body_id}")
    print(f"  地面主体ID: {env.floor_body_id}")

    print(f"\n奖励系数:")
    for key, value in env.reward_coeffs.items():
        print(f"  {key}: {value}")

    print(f"\n成功条件: 连续接触{env.success_contact_duration}步")

    env.close()
    print("\n验证完成!")


if __name__ == "__main__":
    main()