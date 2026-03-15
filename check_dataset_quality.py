#!/usr/bin/env python3
"""
分析数据集质量的详细脚本
检查:
1. 动作值范围违反比例
2. 观察值异常值
3. 奖励分布合理性
4. 数据多样性
5. 时间序列连续性
"""

import numpy as np
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def load_dataset(dataset_path):
    """加载数据集"""
    print(f"加载数据集: {dataset_path}")

    if not os.path.exists(dataset_path):
        print(f"错误: 数据集文件不存在: {dataset_path}")
        return None

    try:
        data = np.load(dataset_path, allow_pickle=True)

        # 获取episodes和元数据
        episodes = data['episodes']
        metadata = data['metadata'].item() if 'metadata' in data else {}

        # 合并所有episode的数据
        all_observations = []
        all_actions = []
        all_rewards = []
        episode_starts = []
        current_idx = 0

        print(f"数据集包含 {len(episodes)} 个episodes")

        for i, episode in enumerate(episodes):
            obs = episode['observations']
            acts = episode['actions']
            rews = episode['rewards']

            all_observations.append(obs)
            all_actions.append(acts)
            all_rewards.append(rews)
            episode_starts.append(current_idx)
            current_idx += len(obs)

        # 拼接所有数据
        observations = np.concatenate(all_observations, axis=0)
        actions = np.concatenate(all_actions, axis=0)
        rewards = np.concatenate(all_rewards, axis=0)

        print(f"数据集加载成功:")
        print(f"  总步数: {len(observations)}")
        print(f"  观察值形状: {observations.shape}")
        print(f"  动作形状: {actions.shape}")
        print(f"  奖励形状: {rewards.shape}")
        print(f"  Episode数量: {len(episodes)}")

        # 添加episode_starts到metadata
        metadata['episode_starts'] = episode_starts

        return observations, actions, rewards, metadata

    except Exception as e:
        print(f"加载数据集失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_action_range_violations(actions):
    """检查动作值范围违反情况"""
    print("\n" + "="*60)
    print("动作值范围检查")
    print("="*60)

    total_actions = actions.size
    violations = np.sum((actions < -1.0) | (actions > 1.0))
    violation_percentage = (violations / total_actions) * 100

    print(f"动作总数: {total_actions}")
    print(f"超出[-1, 1]范围的动作数: {violations}")
    print(f"违反比例: {violation_percentage:.2f}%")

    # 详细统计
    min_val = np.min(actions)
    max_val = np.max(actions)
    mean_val = np.mean(actions)
    std_val = np.std(actions)

    print(f"动作值范围: [{min_val:.6f}, {max_val:.6f}]")
    print(f"动作平均值: {mean_val:.6f} ± {std_val:.6f}")

    # 按执行器维度检查
    print("\n按执行器维度的动作范围:")
    for i in range(min(10, actions.shape[1])):  # 只检查前10个执行器
        act_i = actions[:, i]
        violations_i = np.sum((act_i < -1.0) | (act_i > 1.0))
        if violations_i > 0:
            print(f"  执行器 {i}: 范围 [{np.min(act_i):.3f}, {np.max(act_i):.3f}], "
                  f"违反数 {violations_i} ({violations_i/len(act_i)*100:.1f}%)")

    # 检查是否有执行器总是超出范围
    print("\n最常违反的执行器:")
    violation_counts = []
    for i in range(actions.shape[1]):
        violations_i = np.sum((actions[:, i] < -1.0) | (actions[:, i] > 1.0))
        if violations_i > 0:
            violation_counts.append((i, violations_i, violations_i/len(actions)*100))

    violation_counts.sort(key=lambda x: x[1], reverse=True)
    for i, count, percent in violation_counts[:5]:
        print(f"  执行器 {i}: {count}次违反 ({percent:.1f}%)")

    return violation_percentage

def check_observation_quality(observations):
    """检查观察值质量"""
    print("\n" + "="*60)
    print("观察值质量检查")
    print("="*60)

    # 检查NaN和无限值
    nan_count = np.sum(np.isnan(observations))
    inf_count = np.sum(np.isinf(observations))

    print(f"NaN值数量: {nan_count}")
    print(f"无限值数量: {inf_count}")

    # 检查观察值范围
    obs_min = np.min(observations, axis=0)
    obs_max = np.max(observations, axis=0)
    obs_mean = np.mean(observations, axis=0)
    obs_std = np.std(observations, axis=0)

    print(f"观察值总体范围: [{np.min(obs_min):.3f}, {np.max(obs_max):.3f}]")

    # 检查是否有观察值超出合理范围（假设[-10, 10]为合理）
    extreme_threshold = 10.0
    extreme_count = np.sum(np.abs(observations) > extreme_threshold)
    extreme_percentage = (extreme_count / observations.size) * 100

    print(f"超出±{extreme_threshold}范围的观察值: {extreme_count} ({extreme_percentage:.2f}%)")

    # 检查观察值维度之间的相关性（简单版本）
    print("\n观察值各维度统计（前10个维度）:")
    for i in range(min(10, observations.shape[1])):
        dim_data = observations[:, i]
        print(f"  维度 {i}: 范围 [{np.min(dim_data):.3f}, {np.max(dim_data):.3f}], "
              f"均值 {np.mean(dim_data):.3f} ± {np.std(dim_data):.3f}")

    return nan_count == 0 and inf_count == 0

def check_reward_consistency(rewards):
    """检查奖励一致性"""
    print("\n" + "="*60)
    print("奖励质量检查")
    print("="*60)

    # 基本统计
    print(f"总奖励: {np.sum(rewards):.3f}")
    print(f"平均每步奖励: {np.mean(rewards):.3f} ± {np.std(rewards):.3f}")
    print(f"奖励范围: [{np.min(rewards):.3f}, {np.max(rewards):.3f}]")

    # 检查奖励分布
    reward_hist, bins = np.histogram(rewards, bins=20)
    print(f"\n奖励分布:")
    for i in range(len(reward_hist)):
        if reward_hist[i] > 0:
            print(f"  [{bins[i]:.3f}, {bins[i+1]:.3f}): {reward_hist[i]}步 ({reward_hist[i]/len(rewards)*100:.1f}%)")

    # 检查是否有异常低的奖励（可能表示失败）
    low_reward_threshold = np.percentile(rewards, 10)
    low_reward_steps = np.sum(rewards < low_reward_threshold)

    print(f"\n低奖励分析 (最低10%阈值={low_reward_threshold:.3f}):")
    print(f"  低奖励步数: {low_reward_steps} ({low_reward_steps/len(rewards)*100:.1f}%)")

    # 检查奖励时间序列的突变
    reward_diff = np.abs(np.diff(rewards))
    large_jumps = np.sum(reward_diff > np.std(rewards) * 3)

    print(f"\n奖励突变分析:")
    print(f"  奖励变化标准差: {np.std(reward_diff):.3f}")
    print(f"  大于3σ的突变次数: {large_jumps}")

    return True

def check_episode_consistency(observations, actions, rewards, episode_starts):
    """检查episode一致性"""
    print("\n" + "="*60)
    print("Episode一致性检查")
    print("="*60)

    num_episodes = len(episode_starts)
    print(f"Episode数量: {num_episodes}")

    episode_lengths = []
    episode_rewards = []

    for i in range(num_episodes):
        start_idx = episode_starts[i]
        end_idx = episode_starts[i+1] if i+1 < num_episodes else len(observations)

        length = end_idx - start_idx
        total_reward = np.sum(rewards[start_idx:end_idx])

        episode_lengths.append(length)
        episode_rewards.append(total_reward)

    # 转换为numpy数组
    episode_lengths = np.array(episode_lengths)
    episode_rewards = np.array(episode_rewards)

    print(f"Episode长度统计:")
    print(f"  平均长度: {np.mean(episode_lengths):.1f} ± {np.std(episode_lengths):.1f}")
    print(f"  最小长度: {np.min(episode_lengths)}")
    print(f"  最大长度: {np.max(episode_lengths)}")
    print(f"  长度一致性: {np.std(episode_lengths)/np.mean(episode_lengths)*100:.1f}%")

    print(f"\nEpisode奖励统计:")
    print(f"  平均奖励: {np.mean(episode_rewards):.1f} ± {np.std(episode_rewards):.1f}")
    print(f"  最小奖励: {np.min(episode_rewards):.1f}")
    print(f"  最大奖励: {np.max(episode_rewards):.1f}")

    # 检查是否有异常短的episode
    min_expected_length = 100  # 假设每个episode至少100步
    short_episodes = np.sum(episode_lengths < min_expected_length)

    if short_episodes > 0:
        print(f"\n警告: 找到{short_episodes}个长度小于{min_expected_length}的episode")

    return np.std(episode_lengths) < np.mean(episode_lengths) * 0.5  # 长度变化小于50%

def check_data_diversity(observations, actions, episode_starts):
    """检查数据多样性"""
    print("\n" + "="*60)
    print("数据多样性检查")
    print("="*60)

    num_episodes = len(episode_starts)

    # 计算每个episode的起始观察值差异
    start_observations = []
    for i in range(num_episodes):
        start_idx = episode_starts[i]
        start_obs = observations[start_idx]
        start_observations.append(start_obs)

    start_observations = np.array(start_observations)

    # 计算起始观察值的方差
    obs_variance = np.mean(np.var(start_observations, axis=0))

    print(f"起始观察值平均方差: {obs_variance:.6f}")

    # 计算动作多样性
    action_variance = np.mean(np.var(actions, axis=0))
    print(f"动作平均方差: {action_variance:.6f}")

    # 检查episode之间的相似性
    if num_episodes > 1:
        # 计算前两个episode的观察值相关性
        ep1_start = episode_starts[0]
        ep1_end = episode_starts[1]
        ep2_start = episode_starts[1]
        ep2_end = episode_starts[2] if num_episodes > 2 else len(observations)

        # 对齐长度
        min_len = min(ep1_end - ep1_start, ep2_end - ep2_start)
        ep1_obs = observations[ep1_start:ep1_start+min_len]
        ep2_obs = observations[ep2_start:ep2_start+min_len]

        # 计算相关性
        correlations = []
        for dim in range(min(10, observations.shape[1])):  # 只检查前10个维度
            corr = np.corrcoef(ep1_obs[:, dim], ep2_obs[:, dim])[0, 1]
            if not np.isnan(corr):
                correlations.append(corr)

        avg_correlation = np.mean(correlations) if correlations else 0
        print(f"Episode 1-2 观察值平均相关性: {avg_correlation:.3f}")

    # 动作值分布均匀性
    print(f"\n动作值分布:")
    for i in range(min(5, actions.shape[1])):  # 只检查前5个执行器
        act_i = actions[:, i]
        hist, bins = np.histogram(act_i, bins=5, range=(-1, 1))
        print(f"  执行器 {i}: ", end="")
        for j in range(len(hist)):
            if hist[j] > 0:
                print(f"[{bins[j]:.1f},{bins[j+1]:.1f}):{hist[j]} ", end="")
        print()

    return obs_variance > 0.001 and action_variance > 0.001  # 简单阈值

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='数据集质量深度分析')
    parser.add_argument('--data', type=str, default='data/bc_dataset_100.npz',
                       help='数据集文件路径，默认: data/bc_dataset_100.npz')
    args = parser.parse_args()
    dataset_path = args.data

    print("="*80)
    print("数据集质量深度分析")
    print("="*80)

    # 加载数据集
    result = load_dataset(dataset_path)
    if result is None:
        return

    observations, actions, rewards, metadata = result

    # 获取episode起始索引
    episode_starts = metadata.get('episode_starts', [0])

    # 执行各项检查
    quality_metrics = {}

    # 1. 动作范围检查
    violation_percentage = check_action_range_violations(actions)
    quality_metrics['action_violation'] = violation_percentage

    # 2. 观察值质量检查
    obs_ok = check_observation_quality(observations)
    quality_metrics['observations_ok'] = obs_ok

    # 3. 奖励一致性检查
    reward_ok = check_reward_consistency(rewards)
    quality_metrics['rewards_ok'] = reward_ok

    # 4. Episode一致性检查
    episode_ok = check_episode_consistency(observations, actions, rewards, episode_starts)
    quality_metrics['episodes_ok'] = episode_ok

    # 5. 数据多样性检查
    diversity_ok = check_data_diversity(observations, actions, episode_starts)
    quality_metrics['diversity_ok'] = diversity_ok

    # 总结报告
    print("\n" + "="*80)
    print("数据集质量总结")
    print("="*80)

    print(f"数据集: {dataset_path}")
    print(f"总步数: {len(observations)}")
    print(f"Episode数: {len(episode_starts)}")
    print(f"动作维度: {actions.shape[1]}")
    print(f"观察值维度: {observations.shape[1]}")

    print(f"\n关键指标:")
    print(f"  1. 动作范围违反比例: {violation_percentage:.2f}%")
    print(f"  2. 观察值质量: {'通过' if obs_ok else '警告'}")
    print(f"  3. 奖励一致性: {'通过' if reward_ok else '警告'}")
    print(f"  4. Episode一致性: {'通过' if episode_ok else '警告'}")
    print(f"  5. 数据多样性: {'通过' if diversity_ok else '警告'}")

    # 训练建议
    print(f"\n训练建议:")

    if violation_percentage > 5.0:
        print(f"  [WARNING] 动作范围违反比例较高 ({violation_percentage:.1f}%)")
        print(f"     建议重新收集数据或使用动作裁剪")
    elif violation_percentage > 0.1:
        print(f"  [CAUTION] 动作范围违反比例中等 ({violation_percentage:.1f}%)")
        print(f"     可以考虑使用，但训练时可能需要动作裁剪")
    else:
        print(f"  [OK] 动作范围违反比例低 ({violation_percentage:.1f}%)")
        print(f"     适合用于训练")

    if not diversity_ok:
        print(f"  [CAUTION] 数据多样性可能不足")
        print(f"     考虑收集更多样化的演示")
    else:
        print(f"  [OK] 数据多样性良好")

    if not obs_ok:
        print(f"  [WARNING] 观察值质量问题")
        print(f"     需要检查数据收集过程")
    else:
        print(f"  [OK] 观察值质量良好")

    # 最终评估
    print(f"\n最终评估:")
    if violation_percentage < 1.0 and obs_ok and diversity_ok:
        print(f"  [OK] 数据集质量良好，适合用于训练")
        print(f"     可以考虑直接使用")
    elif violation_percentage < 5.0 and obs_ok:
        print(f"  [WARNING] 数据集质量中等，可以使用但需注意")
        print(f"     建议在训练时添加动作裁剪")
    else:
        print(f"  [CRITICAL] 数据集质量较差，建议重新收集")
        print(f"     或进行数据清洗")

if __name__ == "__main__":
    main()