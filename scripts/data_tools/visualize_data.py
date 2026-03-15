#!/usr/bin/env python3
"""
数据集可视化脚本
加载采集的专家数据并生成可视化图表。

可视化内容:
1. 奖励随时间变化曲线
2. 动作值分布直方图
3. 观测值关键维度分布
4. Episode成功情况对比
5. 距离随时间变化
"""

import sys
import os
import numpy as np
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import matplotlib.pyplot as plt


def load_dataset(data_path):
    """加载数据集"""
    print(f"加载数据集: {data_path}")

    if not os.path.exists(data_path):
        print(f"错误: 文件不存在: {data_path}")
        return None, None

    try:
        data = np.load(data_path, allow_pickle=True)
        print("数据加载成功")
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None, None

    # 检查必要字段
    required_keys = ['episodes', 'metadata']
    for key in required_keys:
        if key not in data:
            print(f"错误: 数据中缺少必要字段 '{key}'")
            return None, None

    episodes = data['episodes']
    metadata = data['metadata'].item() if hasattr(data['metadata'], 'item') else data['metadata']

    return episodes, metadata


def plot_reward_over_time(episodes, save_path=None):
    """绘制奖励随时间变化"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('奖励分析', fontsize=16)

    # 1. 所有episodes的奖励曲线
    ax1 = axes[0, 0]
    all_rewards = []
    for i, ep in enumerate(episodes):
        rewards = ep['rewards']
        timesteps = np.arange(len(rewards))
        ax1.plot(timesteps, rewards, alpha=0.7, label=f'Episode {i+1}')
        all_rewards.extend(rewards)

    ax1.set_xlabel('步数')
    ax1.set_ylabel('奖励')
    ax1.set_title('所有Episodes奖励曲线')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. 奖励分布直方图
    ax2 = axes[0, 1]
    ax2.hist(all_rewards, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax2.set_xlabel('奖励值')
    ax2.set_ylabel('频次')
    ax2.set_title('奖励值分布')
    ax2.grid(True, alpha=0.3)

    # 3. 累积奖励对比
    ax3 = axes[1, 0]
    episode_cum_rewards = []
    episode_lengths = []

    for i, ep in enumerate(episodes):
        cum_reward = np.sum(ep['rewards'])
        episode_cum_rewards.append(cum_reward)
        episode_lengths.append(ep['steps'])

    bars = ax3.bar(range(1, len(episodes) + 1), episode_cum_rewards, alpha=0.7)

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}', ha='center', va='bottom', fontsize=9)

    ax3.set_xlabel('Episode')
    ax3.set_ylabel('累积奖励')
    ax3.set_title('各Episode累积奖励对比')
    ax3.grid(True, alpha=0.3)

    # 4. 奖励统计信息
    ax4 = axes[1, 1]
    ax4.axis('off')  # 关闭坐标轴

    reward_stats = [
        f"总Episodes: {len(episodes)}",
        f"总步数: {sum(episode_lengths)}",
        f"平均累积奖励: {np.mean(episode_cum_rewards):.2f} ± {np.std(episode_cum_rewards):.2f}",
        f"最小累积奖励: {min(episode_cum_rewards):.2f}",
        f"最大累积奖励: {max(episode_cum_rewards):.2f}",
        f"平均Episode长度: {np.mean(episode_lengths):.1f} 步"
    ]

    # 添加成功信息
    success_flags = [ep.get('success', False) for ep in episodes]
    success_rate = sum(success_flags) / len(episodes) * 100
    reward_stats.append(f"成功率: {success_rate:.1f}%")

    stats_text = '\n'.join(reward_stats)
    ax4.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"奖励分析图已保存至: {save_path}")

    plt.show()


def plot_action_distribution(episodes, metadata, save_path=None):
    """绘制动作值分布"""
    # 合并所有动作数据
    all_actions = []
    for ep in episodes:
        all_actions.append(ep['actions'])

    if not all_actions:
        print("警告: 没有动作数据")
        return

    all_actions_concat = np.concatenate(all_actions, axis=0)
    act_dim = all_actions_concat.shape[1]

    # 创建子图
    n_cols = min(4, act_dim)
    n_rows = (act_dim + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 3))
    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes.reshape(1, -1)
    elif n_cols == 1:
        axes = axes.reshape(-1, 1)

    fig.suptitle('动作值分布 (按执行器维度)', fontsize=16)

    for i in range(act_dim):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col]

        actions_i = all_actions_concat[:, i]

        ax.hist(actions_i, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
        ax.set_xlabel(f'执行器 {i}')
        ax.set_ylabel('频次')
        ax.set_title(f'维度 {i}: [{actions_i.min():.3f}, {actions_i.max():.3f}]')
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3)

    # 隐藏多余的子图
    for i in range(act_dim, n_rows * n_cols):
        row = i // n_cols
        col = i % n_cols
        axes[row, col].axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"动作分布图已保存至: {save_path}")

    plt.show()


def plot_observation_analysis(episodes, metadata, save_path=None):
    """绘制观测值分析"""
    # 合并所有观测数据
    all_observations = []
    for ep in episodes:
        all_observations.append(ep['observations'])

    if not all_observations:
        print("警告: 没有观测数据")
        return

    all_obs_concat = np.concatenate(all_observations, axis=0)
    obs_dim = all_obs_concat.shape[1]

    # 只显示部分关键维度（前8个）
    n_dims_to_show = min(8, obs_dim)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('观测值分析', fontsize=16)

    # 1. 观测值范围（前几个维度）
    ax1 = axes[0, 0]
    dims_to_show = list(range(min(10, obs_dim)))
    obs_ranges = []

    for i in dims_to_show:
        obs_min = all_obs_concat[:, i].min()
        obs_max = all_obs_concat[:, i].max()
        obs_ranges.append((obs_min, obs_max))

    # 创建范围图
    x_pos = np.arange(len(dims_to_show))
    min_vals = [r[0] for r in obs_ranges]
    max_vals = [r[1] for r in obs_ranges]

    ax1.bar(x_pos, max_vals, alpha=0.5, color='lightblue', label='最大值')
    ax1.bar(x_pos, min_vals, alpha=0.5, color='lightcoral', label='最小值')

    ax1.set_xlabel('观测维度')
    ax1.set_ylabel('值范围')
    ax1.set_title(f'观测值范围（前{len(dims_to_show)}个维度）')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([f'Dim {i}' for i in dims_to_show], rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. 观测值随时间变化（第一个维度）
    ax2 = axes[0, 1]
    for i, ep in enumerate(episodes[:3]):  # 显示前3个episodes
        obs_dim0 = ep['observations'][:, 0]
        timesteps = np.arange(len(obs_dim0))
        ax2.plot(timesteps, obs_dim0, alpha=0.7, label=f'Episode {i+1}')

    ax2.set_xlabel('步数')
    ax2.set_ylabel('观测值 (维度 0)')
    ax2.set_title('观测值维度0随时间变化')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. 观测值相关性矩阵（前几个维度）
    ax3 = axes[1, 0]
    n_corr_dims = min(10, obs_dim)
    corr_matrix = np.corrcoef(all_obs_concat[:, :n_corr_dims].T)

    im = ax3.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    ax3.set_title(f'观测值相关性矩阵（前{n_corr_dims}个维度）')
    ax3.set_xlabel('维度')
    ax3.set_ylabel('维度')

    # 添加颜色条
    plt.colorbar(im, ax=ax3, shrink=0.8)

    # 4. 观测值统计信息
    ax4 = axes[1, 1]
    ax4.axis('off')  # 关闭坐标轴

    obs_stats = [
        f"观测维度总数: {obs_dim}",
        f"总观测样本数: {len(all_obs_concat)}",
        f"全局最小值: {all_obs_concat.min():.6f}",
        f"全局最大值: {all_obs_concat.max():.6f}",
        f"全局平均值: {all_obs_concat.mean():.6f}",
        f"全局标准差: {all_obs_concat.std():.6f}",
    ]

    # 检查NaN和无穷值
    has_nan = np.any(np.isnan(all_obs_concat))
    has_inf = np.any(np.isinf(all_obs_concat))
    obs_stats.append(f"包含NaN值: {'是' if has_nan else '否'}")
    obs_stats.append(f"包含无穷值: {'是' if has_inf else '否'}")

    stats_text = '\n'.join(obs_stats)
    ax4.text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"观测分析图已保存至: {save_path}")

    plt.show()


def plot_episode_comparison(episodes, save_path=None):
    """绘制Episode对比"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Episode对比分析', fontsize=16)

    # 收集Episode统计信息
    episode_stats = []
    for i, ep in enumerate(episodes):
        steps = ep['steps']
        success = ep.get('success', False)
        cum_reward = np.sum(ep['rewards'])
        contact_steps = sum(ep.get('contact_info', [0] * steps)) if 'contact_info' in ep else 0
        contact_rate = contact_steps / steps if steps > 0 else 0

        episode_stats.append({
            'episode': i + 1,
            'steps': steps,
            'success': success,
            'cum_reward': cum_reward,
            'contact_rate': contact_rate
        })

    # 1. Episode长度对比
    ax1 = axes[0, 0]
    episode_nums = [s['episode'] for s in episode_stats]
    episode_lengths = [s['steps'] for s in episode_stats]

    bars = ax1.bar(episode_nums, episode_lengths, alpha=0.7, color=['green' if s['success'] else 'red' for s in episode_stats])

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height}', ha='center', va='bottom', fontsize=9)

    ax1.set_xlabel('Episode')
    ax1.set_ylabel('步数')
    ax1.set_title('Episode长度对比 (绿色=成功，红色=失败)')
    ax1.grid(True, alpha=0.3)

    # 2. 累积奖励对比
    ax2 = axes[0, 1]
    cum_rewards = [s['cum_reward'] for s in episode_stats]

    bars = ax2.bar(episode_nums, cum_rewards, alpha=0.7, color=['green' if s['success'] else 'red' for s in episode_stats])

    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}', ha='center', va='bottom', fontsize=9)

    ax2.set_xlabel('Episode')
    ax2.set_ylabel('累积奖励')
    ax2.set_title('累积奖励对比')
    ax2.grid(True, alpha=0.3)

    # 3. 接触率对比
    ax3 = axes[1, 0]
    contact_rates = [s['contact_rate'] for s in episode_stats]

    bars = ax3.bar(episode_nums, contact_rates, alpha=0.7, color=['green' if s['success'] else 'red' for s in episode_stats])

    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.1%}', ha='center', va='bottom', fontsize=9)

    ax3.set_xlabel('Episode')
    ax3.set_ylabel('接触率')
    ax3.set_title('接触率对比')
    ax3.grid(True, alpha=0.3)

    # 4. Episode统计信息
    ax4 = axes[1, 1]
    ax4.axis('off')  # 关闭坐标轴

    if episode_stats:
        total_episodes = len(episode_stats)
        successful_episodes = sum(1 for s in episode_stats if s['success'])
        success_rate = successful_episodes / total_episodes * 100
        avg_steps = np.mean(episode_lengths)
        avg_reward = np.mean(cum_rewards)
        avg_contact_rate = np.mean(contact_rates)

        stats_text = [
            f"总Episodes: {total_episodes}",
            f"成功Episodes: {successful_episodes}",
            f"成功率: {success_rate:.1f}%",
            f"平均步数: {avg_steps:.1f}",
            f"平均累积奖励: {avg_reward:.1f}",
            f"平均接触率: {avg_contact_rate:.1%}",
        ]

        ax4.text(0.1, 0.5, '\n'.join(stats_text), fontsize=12,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Episode对比图已保存至: {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description='可视化专家数据集')
    parser.add_argument('--data', type=str, default='data/expert_data.npz',
                       help='数据集文件路径, 默认: data/expert_data.npz')
    parser.add_argument('--output-dir', type=str, default='figures',
                       help='输出图片目录, 默认: figures')
    parser.add_argument('--all', action='store_true',
                       help='生成所有可视化图表')
    parser.add_argument('--rewards', action='store_true',
                       help='仅生成奖励分析图')
    parser.add_argument('--actions', action='store_true',
                       help='仅生成动作分布图')
    parser.add_argument('--observations', action='store_true',
                       help='仅生成观测分析图')
    parser.add_argument('--episodes', action='store_true',
                       help='仅生成Episode对比图')

    args = parser.parse_args()

    # 检查matplotlib是否可用
    try:
        import matplotlib
        # 设置中文字体（如果需要）
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    except ImportError:
        print("错误: 需要安装 matplotlib 库")
        print("安装命令: pip install matplotlib")
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # 加载数据
    episodes, metadata = load_dataset(args.data)
    if episodes is None:
        sys.exit(1)

    print(f"\n数据集信息:")
    print(f"  Episodes数量: {len(episodes)}")
    print(f"  观测维度: {metadata.get('obs_dim', '未知')}")
    print(f"  动作维度: {metadata.get('act_dim', '未知')}")
    print(f"  控制器类型: {metadata.get('controller_type', '未知')}")

    success_flags = [ep.get('success', False) for ep in episodes]
    success_rate = sum(success_flags) / len(episodes) * 100
    print(f"  成功率: {success_rate:.1f}%")

    # 确定要生成哪些图表
    generate_all = args.all or not (args.rewards or args.actions or args.observations or args.episodes)

    # 生成图表
    if generate_all or args.rewards:
        print("\n生成奖励分析图...")
        reward_path = output_dir / 'reward_analysis.png'
        plot_reward_over_time(episodes, save_path=str(reward_path))

    if generate_all or args.actions:
        print("\n生成动作分布图...")
        action_path = output_dir / 'action_distribution.png'
        plot_action_distribution(episodes, metadata, save_path=str(action_path))

    if generate_all or args.observations:
        print("\n生成观测分析图...")
        obs_path = output_dir / 'observation_analysis.png'
        plot_observation_analysis(episodes, metadata, save_path=str(obs_path))

    if generate_all or args.episodes:
        print("\n生成Episode对比图...")
        episode_path = output_dir / 'episode_comparison.png'
        plot_episode_comparison(episodes, save_path=str(episode_path))

    print(f"\n可视化完成!")
    print(f"图表已保存至: {output_dir}/")
    print(f"\n可选后续步骤:")
    print("  1. 检查数据质量: python scripts/data_tools/check_dataset.py --data data/test_2.npz")
    print("  2. 训练行为克隆模型: python scripts/train_bc.py --data data/test_2.npz")


if __name__ == "__main__":
    main()
