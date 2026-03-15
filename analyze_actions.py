#!/usr/bin/env python3
"""
专门分析动作数据的脚本
检查:
1. 动作值时间变化（平滑度）
2. 执行器之间的相关性
3. 动作值的统计分布
4. 超出范围的动作详细分析
"""

import numpy as np
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def load_actions(dataset_path):
    """加载动作数据"""
    print(f"加载数据集: {dataset_path}")

    if not os.path.exists(dataset_path):
        print(f"错误: 数据集文件不存在: {dataset_path}")
        return None

    try:
        data = np.load(dataset_path, allow_pickle=True)
        episodes = data['episodes']

        # 提取所有动作
        all_actions = []
        episode_lengths = []

        for episode in episodes:
            actions = episode['actions']
            all_actions.append(actions)
            episode_lengths.append(len(actions))

        # 拼接所有动作
        actions = np.concatenate(all_actions, axis=0)

        print(f"动作数据加载成功:")
        print(f"  总步数: {len(actions)}")
        print(f"  动作维度: {actions.shape[1]}")
        print(f"  Episode数量: {len(episodes)}")
        print(f"  Episode长度: {episode_lengths[:5]}... (总共{len(episode_lengths)}个)")

        return actions, episode_lengths

    except Exception as e:
        print(f"加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_action_ranges(actions):
    """分析动作值范围"""
    print("\n" + "="*60)
    print("动作值范围详细分析")
    print("="*60)

    num_actuators = actions.shape[1]

    print(f"执行器数量: {num_actuators}")
    print(f"动作值总体范围: [{np.min(actions):.6f}, {np.max(actions):.6f}]")

    # 检查每个执行器
    print("\n各执行器动作范围统计:")
    print("执行器 | 最小值 | 最大值 | 平均值 | 标准差 | 超出范围比例")
    print("-"*80)

    violation_stats = []

    for i in range(num_actuators):
        act_i = actions[:, i]
        violations = np.sum((act_i < -1.0) | (act_i > 1.0))
        violation_pct = violations / len(act_i) * 100

        print(f"{i:3d} | {np.min(act_i):7.3f} | {np.max(act_i):7.3f} | "
              f"{np.mean(act_i):7.3f} | {np.std(act_i):7.3f} | {violation_pct:6.1f}%")

        if violations > 0:
            violation_stats.append((i, violations, violation_pct,
                                   np.min(act_i), np.max(act_i)))

    # 按违反比例排序
    if violation_stats:
        print("\n违反比例最高的执行器:")
        violation_stats.sort(key=lambda x: x[2], reverse=True)
        for i, count, pct, min_val, max_val in violation_stats[:10]:
            print(f"  执行器 {i}: {pct:.1f}% ({count}次), 范围 [{min_val:.3f}, {max_val:.3f}]")

    return violation_stats

def analyze_action_smoothness(actions, episode_lengths):
    """分析动作平滑度（时间变化）"""
    print("\n" + "="*60)
    print("动作平滑度分析")
    print("="*60)

    num_actuators = actions.shape[1]

    # 计算动作变化率（差分）
    action_diff = np.diff(actions, axis=0)

    print(f"动作变化统计:")
    print(f"  平均变化幅度: {np.mean(np.abs(action_diff)):.6f}")
    print(f"  最大变化幅度: {np.max(np.abs(action_diff)):.6f}")
    print(f"  变化标准差: {np.std(action_diff):.6f}")

    # 检查零变化（动作保持不变）的比例
    zero_change = np.sum(np.abs(action_diff) < 1e-6) / action_diff.size * 100
    print(f"  零变化比例: {zero_change:.2f}%")

    # 按执行器分析
    print("\n各执行器变化统计（前10个）:")
    for i in range(min(10, num_actuators)):
        diff_i = action_diff[:, i]
        zero_pct = np.sum(np.abs(diff_i) < 1e-6) / len(diff_i) * 100
        print(f"  执行器 {i}: 平均变化={np.mean(np.abs(diff_i)):.4f}, "
              f"零变化={zero_pct:.1f}%")

    # 检查episode内的动作变化模式
    print(f"\nEpisode内动作变化分析:")

    # 分析前几个episode
    for ep_idx in range(min(3, len(episode_lengths))):
        start = sum(episode_lengths[:ep_idx])
        end = start + episode_lengths[ep_idx]
        ep_actions = actions[start:end]
        ep_diff = np.diff(ep_actions, axis=0)

        zero_ep = np.sum(np.abs(ep_diff) < 1e-6) / ep_diff.size * 100

        print(f"  Episode {ep_idx}: 长度={episode_lengths[ep_idx]}, "
              f"零变化={zero_ep:.1f}%, 平均变化={np.mean(np.abs(ep_diff)):.4f}")

def analyze_action_distribution(actions):
    """分析动作值分布"""
    print("\n" + "="*60)
    print("动作值分布分析")
    print("="*60)

    num_actuators = actions.shape[1]

    # 创建分布直方图
    bins = np.linspace(-1.5, 2.5, 17)  # 扩展到超出范围

    print(f"动作值分布直方图（所有执行器）:")
    hist, bin_edges = np.histogram(actions.flatten(), bins=bins)

    total = len(actions.flatten())
    for i in range(len(hist)):
        if hist[i] > 0:
            lower, upper = bin_edges[i], bin_edges[i+1]
            pct = hist[i] / total * 100
            range_desc = f"[{lower:.1f},{upper:.1f})"

            # 标记是否在[-1, 1]范围内
            if lower >= -1.0 and upper <= 1.0:
                range_desc += " [有效范围]"
            else:
                range_desc += " [超出范围]"

            print(f"  {range_desc}: {hist[i]}个 ({pct:.1f}%)")

    # 分析每个执行器的值分布
    print(f"\n各执行器值分布特征（前5个执行器）:")
    for i in range(min(5, num_actuators)):
        act_i = actions[:, i]

        # 计算在[-1, 1]范围内和外的比例
        in_range = np.sum((act_i >= -1.0) & (act_i <= 1.0)) / len(act_i) * 100
        below_range = np.sum(act_i < -1.0) / len(act_i) * 100
        above_range = np.sum(act_i > 1.0) / len(act_i) * 100

        print(f"  执行器 {i}:")
        print(f"    在范围内: {in_range:.1f}%")
        print(f"    低于范围: {below_range:.1f}%")
        print(f"    高于范围: {above_range:.1f}%")

        # 计算分布偏度
        from scipy import stats
        if len(act_i) > 1:
            skewness = stats.skew(act_i)
            kurtosis = stats.kurtosis(act_i)
            print(f"    偏度: {skewness:.3f}, 峰度: {kurtosis:.3f}")

def analyze_action_correlations(actions):
    """分析执行器之间的相关性"""
    print("\n" + "="*60)
    print("执行器间相关性分析")
    print("="*60)

    num_actuators = actions.shape[1]

    # 计算相关性矩阵（只计算前10个执行器以节省时间）
    n_analyze = min(10, num_actuators)
    corr_matrix = np.corrcoef(actions[:, :n_analyze].T)

    print(f"前{n_analyze}个执行器的相关性矩阵:")
    print("   " + " ".join([f"{i:4d}" for i in range(n_analyze)]))
    for i in range(n_analyze):
        row = [f"{corr_matrix[i, j]:.2f}" for j in range(n_analyze)]
        print(f"{i:2d} [" + " ".join(row) + "]")

    # 找出高度相关的执行器对
    print(f"\n高度相关的执行器对 (|r| > 0.8):")
    found = False
    for i in range(n_analyze):
        for j in range(i+1, n_analyze):
            corr = corr_matrix[i, j]
            if abs(corr) > 0.8:
                print(f"  执行器 {i} 和 {j}: r = {corr:.3f}")
                found = True

    if not found:
        print("  未找到高度相关的执行器对")

def analyze_episode_variability(actions, episode_lengths):
    """分析episode之间的变异性"""
    print("\n" + "="*60)
    print("Episode间变异性分析")
    print("="*60)

    num_episodes = len(episode_lengths)
    num_actuators = actions.shape[1]

    print(f"分析 {num_episodes} 个episodes 的变异性")

    # 提取每个episode的平均动作
    episode_means = []
    start_idx = 0

    for ep_len in episode_lengths:
        end_idx = start_idx + ep_len
        ep_actions = actions[start_idx:end_idx]
        episode_means.append(np.mean(ep_actions, axis=0))
        start_idx = end_idx

    episode_means = np.array(episode_means)  # 形状: (num_episodes, num_actuators)

    # 计算episode间方差
    episode_variance = np.var(episode_means, axis=0)
    avg_variance = np.mean(episode_variance)

    print(f"Episode间平均方差: {avg_variance:.6f}")

    # 检查方差较低的执行器（可能动作变化不大）
    low_variance_threshold = 0.001
    low_var_actuators = np.where(episode_variance < low_variance_threshold)[0]

    if len(low_var_actuators) > 0:
        print(f"\n方差较低的执行器 (<{low_variance_threshold}):")
        for i in low_var_actuators[:10]:  # 只显示前10个
            print(f"  执行器 {i}: 方差 = {episode_variance[i]:.6f}")

    # 计算episode间的相似性（前2个episode）
    if num_episodes >= 2:
        ep1_means = episode_means[0]
        ep2_means = episode_means[1]

        # 计算余弦相似性
        dot_product = np.dot(ep1_means, ep2_means)
        norm1 = np.linalg.norm(ep1_means)
        norm2 = np.linalg.norm(ep2_means)

        if norm1 > 0 and norm2 > 0:
            cosine_sim = dot_product / (norm1 * norm2)
            print(f"Episode 1-2 平均动作余弦相似性: {cosine_sim:.3f}")

        # 计算欧氏距离
        euclidean_dist = np.linalg.norm(ep1_means - ep2_means)
        print(f"Episode 1-2 平均动作欧氏距离: {euclidean_dist:.3f}")

def main():
    """主函数"""
    dataset_path = "data/bc_dataset_100.npz"

    print("="*80)
    print("动作数据深度分析")
    print("="*80)

    # 加载动作数据
    result = load_actions(dataset_path)
    if result is None:
        return

    actions, episode_lengths = result

    # 执行各项分析
    print("\n" + "="*80)
    print("开始详细分析...")
    print("="*80)

    # 1. 动作范围分析
    violation_stats = analyze_action_ranges(actions)

    # 2. 动作平滑度分析
    analyze_action_smoothness(actions, episode_lengths)

    # 3. 动作分布分析
    analyze_action_distribution(actions)

    # 4. 相关性分析
    analyze_action_correlations(actions)

    # 5. Episode变异性分析
    analyze_episode_variability(actions, episode_lengths)

    # 总结和建议
    print("\n" + "="*80)
    print("动作数据质量总结")
    print("="*80)

    total_actions = actions.size
    violations = np.sum((actions < -1.0) | (actions > 1.0))
    violation_pct = violations / total_actions * 100

    print(f"总动作数: {total_actions}")
    print(f"超出范围动作数: {violations} ({violation_pct:.2f}%)")

    # 检查动作变化
    action_diff = np.diff(actions, axis=0)
    zero_change_pct = np.sum(np.abs(action_diff) < 1e-6) / action_diff.size * 100

    print(f"零变化动作比例: {zero_change_pct:.2f}%")

    print(f"\n关键问题:")
    if violation_pct > 5.0:
        print(f"  1. [严重] 动作范围违反比例高 ({violation_pct:.1f}%)")
        print(f"     影响: BC模型可能学习到无效的动作")
        print(f"     建议: 重新收集数据或训练时添加动作裁剪")

    if zero_change_pct > 10.0:
        print(f"  2. [注意] 动作变化不足 ({zero_change_pct:.1f}%零变化)")
        print(f"     影响: 数据可能包含过多静态动作")
        print(f"     建议: 检查控制器输出或增加数据采集频率")

    if violation_pct < 1.0 and zero_change_pct < 5.0:
        print(f"  [良好] 动作数据质量可以接受")
        print(f"     可以用于BC训练")
    elif violation_pct < 5.0:
        print(f"  [中等] 动作数据质量中等")
        print(f"     可以使用，但训练时需注意动作裁剪")
    else:
        print(f"  [较差] 动作数据质量较差")
        print(f"     建议重新收集数据")

if __name__ == "__main__":
    main()