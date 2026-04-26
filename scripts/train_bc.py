#!/usr/bin/env python3
"""
Behavior-cloning training script.

Canonical example:
    python scripts/train_bc.py --task pre_grasp --data data/expert_pre_grasp_mixed_v2.npz --epochs 20 --output models/bc_pre_grasp_v2.pth

Compatibility note:
    Generic defaults such as data/expert_data.npz and models/bc_model.pth remain for backward compatibility.
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError:
    print("PyTorch is required. Install it with: pip install torch")
    sys.exit(1)


def resolve_structured_task_name(task_name_arg=""):
    """Normalize the optional task selector used for task-specific defaults."""
    return (task_name_arg or "").strip() or None


def default_dataset_path_for_task(structured_task_name):
    """Return the dataset path implied by the selected task."""
    if structured_task_name:
        return f"data/expert_{structured_task_name}.npz"
    return "data/expert_data.npz"


def default_model_path_for_task(structured_task_name):
    """Return the checkpoint path implied by the selected task."""
    if structured_task_name:
        return f"models/bc_{structured_task_name}.pth"
    return "models/bc_model.pth"


def append_phase_feature(observations, horizon):
    """Append a normalized phase feature in [0, 1] to one episode."""
    phase = np.arange(observations.shape[0], dtype=np.float32) / max(1, horizon - 1)
    phase = np.clip(phase, 0.0, 1.0)
    return np.concatenate([observations.astype(np.float32), phase[:, None]], axis=1)


def load_dataset(
    data_path,
    success_only=False,
    truncate_steps=None,
    add_phase_feature=False,
    min_grasp_duration=0,
):
    """Load the dataset and flatten it into BC training arrays."""
    print(f"Loading dataset: {data_path}")

    if not os.path.exists(data_path):
        print(f"Error: file not found: {data_path}")
        return None

    try:
        data = np.load(data_path, allow_pickle=True)
    except Exception as exc:
        print(f"Failed to load dataset: {exc}")
        return None

    if "episodes" not in data:
        print("Error: dataset is missing the 'episodes' field")
        return None

    episodes = data["episodes"]
    raw_metadata = data["metadata"].item() if hasattr(data["metadata"], "item") else data["metadata"]
    metadata = dict(raw_metadata)

    print("Dataset info:")
    print(f"  Episodes: {len(episodes)}")
    print(f"  Obs dim: {metadata.get('obs_dim', 'unknown')}")
    print(f"  Act dim: {metadata.get('act_dim', 'unknown')}")
    if success_only:
        print("  Filter: success-only episodes")
    if min_grasp_duration > 0:
        print(f"  Filter: max stable-grasp duration >= {min_grasp_duration}")
    if truncate_steps is not None:
        print(f"  Truncate steps: {truncate_steps}")
    if add_phase_feature:
        print("  Extra feature: normalized phase")

    all_observations = []
    all_actions = []
    retained_episodes = 0
    phase_horizon = int(truncate_steps or metadata.get("max_steps") or 1)

    for episode_idx, episode in enumerate(episodes):
        if success_only and not bool(episode.get("success", False)):
            continue
        episode_metrics = episode.get("metrics", {})
        if int(episode_metrics.get("max_grasp_contact_duration", 0)) < min_grasp_duration:
            continue

        observations = episode["observations"]
        actions = episode["actions"]

        if truncate_steps is not None:
            observations = observations[:truncate_steps]
            actions = actions[:truncate_steps]

        if observations.shape[0] != actions.shape[0]:
            print(
                f"Warning: episode {episode_idx} obs/action length mismatch: "
                f"{observations.shape[0]} != {actions.shape[0]}"
            )
            continue

        if observations.shape[0] == 0:
            print(f"Warning: episode {episode_idx} is empty after truncation, skipping")
            continue

        if add_phase_feature:
            observations = append_phase_feature(observations, phase_horizon)

        all_observations.append(observations)
        all_actions.append(actions)
        retained_episodes += 1

    if not all_observations:
        print("Error: no valid training data found")
        return None

    X = np.concatenate(all_observations, axis=0).astype(np.float32)
    y = np.concatenate(all_actions, axis=0).astype(np.float32)

    print("Dataset stats:")
    print(f"  Retained episodes: {retained_episodes}")
    print(f"  Total samples: {X.shape[0]}")
    print(f"  Observation range: [{X.min():.3f}, {X.max():.3f}]")
    print(f"  Action range: [{y.min():.3f}, {y.max():.3f}]")

    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        print("Warning: NaN values detected in the dataset")

    metadata["base_obs_dim"] = int(metadata.get("obs_dim", X.shape[1] - (1 if add_phase_feature else 0)))
    metadata["obs_dim"] = int(X.shape[1])
    metadata["phase_feature"] = bool(add_phase_feature)
    metadata["phase_feature_horizon"] = int(phase_horizon if add_phase_feature else 0)

    return X, y, metadata


class SimpleBCModel(nn.Module):
    """Simple MLP policy used for behavior cloning."""

    def __init__(self, obs_dim=70, act_dim=24, hidden_dim=64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, act_dim),
            nn.Tanh(),
        )

    def forward(self, x):
        return self.network(x)


def train_model(X, y, obs_dim, act_dim, args):
    """Train the BC model."""
    print("\n" + "=" * 60)
    print("Start BC Training")
    print("=" * 60)

    X_tensor = torch.from_numpy(X)
    y_tensor = torch.from_numpy(y)

    dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    print(f"Total samples: {len(dataset)}")
    print(f"Batch size: {args.batch_size}")
    print(f"Batches per epoch: {len(dataloader)}")

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    print(f"Device: {device}")

    model = SimpleBCModel(obs_dim=obs_dim, act_dim=act_dim, hidden_dim=args.hidden_dim)
    model.to(device)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    losses = []
    print(f"\nTraining for {args.epochs} epochs...")

    for epoch in range(args.epochs):
        epoch_loss = 0.0
        batch_count = 0

        for batch_X, batch_y in dataloader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batch_count += 1

        avg_loss = epoch_loss / max(1, batch_count)
        losses.append(avg_loss)

        if (epoch + 1) % args.log_interval == 0 or epoch == 0 or epoch == args.epochs - 1:
            print(f"Epoch [{epoch + 1:3d}/{args.epochs}] | Loss: {avg_loss:.6f}")

    print("\nTraining complete!")
    print(f"Final loss: {losses[-1]:.6f}")

    return model, losses


def evaluate_model(model, X, y, device):
    """Evaluate the BC model on the training data."""
    model.eval()

    with torch.no_grad():
        X_tensor = torch.from_numpy(X).to(device)
        y_tensor = torch.from_numpy(y).to(device)
        predictions = model(X_tensor)
        mse_loss = nn.MSELoss()(predictions, y_tensor).item()

    print("\nEvaluation:")
    print(f"  Training-set MSE: {mse_loss:.6f}")
    return mse_loss


def save_model(model, metadata, output_path, args):
    """Save the trained model and metadata."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "obs_dim": metadata.get("obs_dim", 70),
            "act_dim": metadata.get("act_dim", 24),
            "hidden_dim": args.hidden_dim,
            "args": vars(args),
            "metadata": metadata,
        },
        output_path,
    )

    print(f"Saved model to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Train a behavior-cloning model")
    parser.add_argument("--data", type=str, default="", help="Path to the expert dataset (.npz)")
    parser.add_argument("--output", type=str, default="", help="Output checkpoint path")
    parser.add_argument(
        "--task",
        type=str,
        default="",
        choices=["", "pre_grasp", "stable_grasp", "lift_and_hold"],
        help="Optional task selector used to infer default dataset/output paths",
    )
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--hidden-dim", type=int, default=64, help="Hidden layer dimension")
    parser.add_argument("--log-interval", type=int, default=10, help="Epoch interval for progress logs")
    parser.add_argument("--no-cuda", action="store_true", help="Disable CUDA even if available")
    parser.add_argument("--success-only", action="store_true", help="Train only on successful episodes")
    parser.add_argument(
        "--truncate-steps",
        type=int,
        default=None,
        help="Use only the first N steps from each episode",
    )
    parser.add_argument(
        "--add-phase-feature",
        action="store_true",
        help="Append a normalized phase feature so the policy can learn when to close",
    )
    parser.add_argument(
        "--min-grasp-duration",
        type=int,
        default=0,
        help="Retain only episodes whose max stable-grasp duration reaches at least this many steps",
    )

    args = parser.parse_args()
    structured_task_name = resolve_structured_task_name(args.task)
    args.data = args.data or default_dataset_path_for_task(structured_task_name)
    args.output = args.output or default_model_path_for_task(structured_task_name)

    print("=" * 60)
    print("Behavior Cloning Training")
    print("=" * 60)
    if structured_task_name:
        print(f"Structured task: {structured_task_name}")
    print(f"Dataset: {args.data}")
    print(f"Output: {args.output}")

    result = load_dataset(
        args.data,
        success_only=args.success_only,
        truncate_steps=args.truncate_steps,
        add_phase_feature=args.add_phase_feature,
        min_grasp_duration=args.min_grasp_duration,
    )
    if result is None:
        sys.exit(1)

    X, y, metadata = result
    obs_dim = metadata.get("obs_dim", X.shape[1])
    act_dim = metadata.get("act_dim", y.shape[1])

    print("\nTraining config:")
    print(f"  Task: {metadata.get('task_name', structured_task_name or 'static_grasp')}")
    print(f"  Success rule: {metadata.get('success_rule', 'unknown')}")
    print(f"  Obs dim: {obs_dim}")
    print(f"  Act dim: {act_dim}")
    print(f"  Total samples: {X.shape[0]}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.lr}")
    print(f"  Hidden dim: {args.hidden_dim}")
    print(f"  Success only: {args.success_only}")
    print(f"  Min grasp duration: {args.min_grasp_duration}")
    print(f"  Truncate steps: {args.truncate_steps if args.truncate_steps is not None else 'full'}")
    print(f"  Phase feature: {args.add_phase_feature}")

    model, _losses = train_model(X, y, obs_dim, act_dim, args)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    evaluate_model(model, X, y, device)
    save_model(model, metadata, args.output, args)

    print("\n" + "=" * 60)
    print("Training Finished")
    print("=" * 60)
    eval_cmd = f"python scripts/eval_bc.py --model {args.output} --episodes 1"
    if metadata.get("enable_catch_task", False):
        eval_cmd += " --enable-catch-task"
    elif metadata.get("structured_task_name") == "pre_grasp":
        eval_cmd += " --placement-mode demo"
        placement_jitters = metadata.get("placement_jitters", [])
        if placement_jitters:
            eval_cmd += " --placement-jitters " + ",".join(str(item) for item in placement_jitters)
    else:
        eval_cmd += " --placement-mode demo --finger-ramp-steps 200 --finger-ramp-start-scale 0.25"
    print(f"Next: {eval_cmd}")


if __name__ == "__main__":
    main()
