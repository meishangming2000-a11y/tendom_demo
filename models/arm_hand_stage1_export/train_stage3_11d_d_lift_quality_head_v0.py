#!/usr/bin/env python3
"""Train Stage3.11D-D lift-quality head from dense sensor-fusion traces.

This is an offline MuJoCo-only classifier. It predicts whether the current
grasp/lift evidence is good enough to keep lifting/holding, plus auxiliary
adjust-needed and hold-safe labels. It does not output full hand actions and
does not promote a closed-loop controller.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from arm_hand_stage1_task_api import json_ready


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_DATASET = DATA / "stage3_11d_d_dense_sensor_fusion_dataset_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_11d_d_lift_quality_head_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_11d_d_lift_quality_head_v0_train_report.md"
DEFAULT_METADATA = META / "stage3_11d_d_lift_quality_head_v0_train.json"

STATUS = "stage3_11d_d_lift_quality_head_v0_offline_trained_not_closed_loop_promoted"
GRASP_EVIDENCE_PHASES = {"contact_gate", "post_contact_settle", "preload", "slow_lift", "hold"}
TARGET_LABELS = ["lift_quality_now", "adjust_needed_now", "hold_safe_now"]


@dataclass(frozen=True)
class FeatureBundle:
    x: np.ndarray
    y: np.ndarray
    row_mask: np.ndarray
    feature_names: list[str]
    target_names: list[str]
    episode_ids: np.ndarray


class LiftQualityHead(nn.Module):
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(int(input_dim), int(hidden_dim)),
            nn.LayerNorm(int(hidden_dim)),
            nn.GELU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), max(32, int(hidden_dim) // 2)),
            nn.GELU(),
            nn.Dropout(float(dropout)),
            nn.Linear(max(32, int(hidden_dim) // 2), int(output_dim)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def load_dataset(path: Path) -> np.lib.npyio.NpzFile:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=False)


def require_fields(data: np.lib.npyio.NpzFile, fields: list[str]) -> None:
    missing = [field for field in fields if field not in data.files]
    if missing:
        raise KeyError(f"Dataset missing fields: {missing}")


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def parse_metadata_json(data: np.lib.npyio.NpzFile) -> dict[str, Any]:
    if "metadata_json" not in data.files:
        return {}
    return json.loads(str(data["metadata_json"][0]))


def one_hot(ids: np.ndarray, count: int) -> np.ndarray:
    out = np.zeros((len(ids), int(count)), dtype=np.float32)
    valid = (ids >= 0) & (ids < int(count))
    out[np.arange(len(ids))[valid], ids[valid].astype(np.int64)] = 1.0
    return out


def add_block(
    parts: list[np.ndarray],
    names: list[str],
    data: np.lib.npyio.NpzFile,
    *,
    enabled: bool,
    array_name: str,
    name_array: str,
    prefix: str,
) -> None:
    if not enabled:
        return
    block = np.asarray(data[array_name], dtype=np.float32)
    parts.append(block)
    block_names = string_list(data[name_array]) if name_array in data.files else [f"{prefix}_{i}" for i in range(block.shape[1])]
    names.extend([f"{prefix}.{name}" for name in block_names])


def build_feature_bundle(
    data: np.lib.npyio.NpzFile,
    *,
    use_vision: bool,
    use_tactile: bool,
    use_force: bool,
    use_context: bool,
    use_proprio: bool,
    use_phase_onehot: bool,
) -> FeatureBundle:
    require_fields(
        data,
        [
            "vision_features",
            "tactile_features",
            "force_features",
            "context_features",
            "proprio_features",
            "safety_labels",
            "safety_label_names",
            "phase_ids",
            "phase_names",
            "episode_ids",
        ],
    )
    phase_names = string_list(data["phase_names"])
    safety_label_names = string_list(data["safety_label_names"])
    target_indices = [safety_label_names.index(name) for name in TARGET_LABELS]
    phase_ids = np.asarray(data["phase_ids"], dtype=np.int32)
    phase_mask = np.asarray([phase_names[int(idx)] in GRASP_EVIDENCE_PHASES for idx in phase_ids], dtype=bool)

    parts: list[np.ndarray] = []
    names: list[str] = []
    add_block(
        parts,
        names,
        data,
        enabled=use_vision,
        array_name="vision_features",
        name_array="vision_feature_names",
        prefix="vision",
    )
    add_block(
        parts,
        names,
        data,
        enabled=use_tactile,
        array_name="tactile_features",
        name_array="tactile_feature_names",
        prefix="tactile",
    )
    add_block(
        parts,
        names,
        data,
        enabled=use_force,
        array_name="force_features",
        name_array="force_feature_names",
        prefix="force",
    )
    add_block(
        parts,
        names,
        data,
        enabled=use_context,
        array_name="context_features",
        name_array="context_feature_names",
        prefix="context",
    )
    add_block(
        parts,
        names,
        data,
        enabled=use_proprio,
        array_name="proprio_features",
        name_array="proprio_feature_names",
        prefix="proprio",
    )
    if use_phase_onehot:
        parts.append(one_hot(phase_ids, len(phase_names)).astype(np.float32))
        names.extend([f"phase.{name}" for name in phase_names])
    if not parts:
        raise ValueError("At least one feature block must be enabled.")
    x_all = np.concatenate(parts, axis=1).astype(np.float32)
    y_all = np.asarray(data["safety_labels"], dtype=np.float32)[:, target_indices]
    return FeatureBundle(
        x=x_all[phase_mask],
        y=y_all[phase_mask],
        row_mask=phase_mask,
        feature_names=names,
        target_names=TARGET_LABELS,
        episode_ids=np.asarray(data["episode_ids"], dtype=np.int32)[phase_mask],
    )


def split_by_episode(
    episode_ids: np.ndarray,
    *,
    val_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[int], list[int]]:
    unique = np.unique(episode_ids.astype(np.int32))
    if len(unique) <= 2:
        mask = np.ones_like(episode_ids, dtype=bool)
        return mask.copy(), mask.copy(), unique.tolist(), unique.tolist()
    rng = np.random.default_rng(int(seed))
    shuffled = unique.copy()
    rng.shuffle(shuffled)
    val_count = max(1, int(round(len(shuffled) * float(val_fraction))))
    val_eps = set(int(v) for v in shuffled[:val_count])
    val_mask = np.asarray([int(v) in val_eps for v in episode_ids], dtype=bool)
    train_mask = ~val_mask
    if not np.any(train_mask):
        train_mask[:] = True
    return train_mask, val_mask, np.unique(episode_ids[train_mask]).astype(int).tolist(), sorted(val_eps)


def normalize(train_x: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0).astype(np.float32)
    std = train_x.std(axis=0).astype(np.float32)
    std = np.maximum(std, 1e-6)
    return ((x - mean.reshape(1, -1)) / std.reshape(1, -1)).astype(np.float32), mean, std


def batch_indices(count: int, batch_size: int, rng: np.random.Generator) -> list[np.ndarray]:
    order = np.arange(int(count), dtype=np.int64)
    rng.shuffle(order)
    return [order[start : start + int(batch_size)] for start in range(0, int(count), int(batch_size))]


def binary_auc(y_true: np.ndarray, score: np.ndarray) -> float:
    y = y_true.astype(np.float32)
    n_pos = int(np.sum(y > 0.5))
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(score)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(score) + 1, dtype=np.float64)
    pos_rank_sum = float(np.sum(ranks[y > 0.5]))
    return float((pos_rank_sum - n_pos * (n_pos + 1) / 2.0) / max(1.0, n_pos * n_neg))


def evaluate(model: LiftQualityHead, x: np.ndarray, y: np.ndarray, target_names: list[str]) -> dict[str, Any]:
    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(x.astype(np.float32))).cpu().numpy()
    probs = 1.0 / (1.0 + np.exp(-logits))
    preds = probs >= 0.5
    metrics: dict[str, Any] = {}
    for idx, name in enumerate(target_names):
        truth = y[:, idx] >= 0.5
        pred = preds[:, idx]
        tp = int(np.sum(pred & truth))
        tn = int(np.sum((~pred) & (~truth)))
        fp = int(np.sum(pred & (~truth)))
        fn = int(np.sum((~pred) & truth))
        precision = float(tp / max(1, tp + fp))
        recall = float(tp / max(1, tp + fn))
        f1 = float(2.0 * precision * recall / max(1e-9, precision + recall))
        metrics[name] = {
            "accuracy": float((tp + tn) / max(1, len(truth))),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "auc": binary_auc(y[:, idx], probs[:, idx]),
            "positive_fraction": float(np.mean(y[:, idx])) if len(y) else 0.0,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        }
    return metrics


def mean_primary_score(metrics: dict[str, Any]) -> float:
    primary = metrics.get("lift_quality_now", {})
    return float(primary.get("f1", 0.0))


def train_once(
    bundle: FeatureBundle,
    *,
    config_name: str,
    epochs: int,
    batch_size: int,
    lr: float,
    hidden_dim: int,
    dropout: float,
    val_fraction: float,
    seed: int,
    checkpoint: Path | None = None,
    dataset_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    train_mask, val_mask, train_eps, val_eps = split_by_episode(bundle.episode_ids, val_fraction=val_fraction, seed=seed)
    train_x_raw = bundle.x[train_mask]
    val_x_raw = bundle.x[val_mask]
    train_y = bundle.y[train_mask].astype(np.float32)
    val_y = bundle.y[val_mask].astype(np.float32)
    train_x, mean, std = normalize(train_x_raw, train_x_raw)
    val_x = ((val_x_raw - mean.reshape(1, -1)) / std.reshape(1, -1)).astype(np.float32)

    torch.manual_seed(int(seed))
    model = LiftQualityHead(train_x.shape[1], train_y.shape[1], hidden_dim, dropout)
    pos = train_y.sum(axis=0)
    neg = train_y.shape[0] - pos
    pos_weight = np.clip(neg / np.maximum(pos, 1.0), 0.25, 12.0).astype(np.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.from_numpy(pos_weight))
    optimizer = optim.AdamW(model.parameters(), lr=float(lr), weight_decay=1e-4)
    rng = np.random.default_rng(int(seed))
    history: list[dict[str, float]] = []
    best_state: dict[str, torch.Tensor] | None = None
    best_score = -1.0
    best_epoch = 0

    for epoch in range(1, int(epochs) + 1):
        model.train()
        losses = []
        for batch in batch_indices(len(train_x), batch_size, rng):
            xb = torch.from_numpy(train_x[batch])
            yb = torch.from_numpy(train_y[batch])
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            losses.append(float(loss.item()))
        val_metrics = evaluate(model, val_x, val_y, bundle.target_names)
        score = mean_primary_score(val_metrics)
        history.append({"epoch": float(epoch), "train_loss": float(np.mean(losses)), "val_lift_quality_f1": score})
        if score >= best_score:
            best_score = score
            best_epoch = int(epoch)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    train_metrics = evaluate(model, train_x, train_y, bundle.target_names)
    val_metrics = evaluate(model, val_x, val_y, bundle.target_names)
    result = {
        "config_name": config_name,
        "status": STATUS,
        "rows_total": int(len(bundle.x)),
        "rows_train": int(len(train_x)),
        "rows_val": int(len(val_x)),
        "episodes_train": train_eps,
        "episodes_val": val_eps,
        "input_dim": int(train_x.shape[1]),
        "target_names": bundle.target_names,
        "feature_count": int(len(bundle.feature_names)),
        "epochs": int(epochs),
        "best_epoch": int(best_epoch),
        "pos_weight": pos_weight.tolist(),
        "history_tail": history[-5:],
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "primary_val_f1": float(best_score),
    }
    if checkpoint is not None:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "status": STATUS,
                "config_name": config_name,
                "model_state_dict": model.state_dict(),
                "input_dim": int(train_x.shape[1]),
                "target_names": bundle.target_names,
                "feature_names": bundle.feature_names,
                "obs_mean": mean,
                "obs_std": std,
                "hidden_dim": int(hidden_dim),
                "dropout": float(dropout),
                "dataset_metadata": dataset_metadata or {},
                "train_result": result,
            },
            checkpoint,
        )
        result["checkpoint"] = str(checkpoint.resolve())
    return result


def config_variants(args: argparse.Namespace) -> list[dict[str, Any]]:
    all_blocks = {
        "use_vision": True,
        "use_tactile": True,
        "use_force": True,
        "use_context": True,
        "use_proprio": True,
        "use_phase_onehot": True,
    }
    if not bool(args.ablation_suite):
        return [{"name": "all_sensors", **all_blocks}]
    return [
        {"name": "all_sensors", **all_blocks},
        {"name": "no_force", **{**all_blocks, "use_force": False}},
        {"name": "no_tactile", **{**all_blocks, "use_tactile": False}},
        {"name": "no_vision", **{**all_blocks, "use_vision": False}},
        {"name": "no_proprio", **{**all_blocks, "use_proprio": False}},
    ]


def write_report(path: Path, payload: dict[str, Any]) -> None:
    main = payload["main_result"]
    lines = [
        "# Stage3.11D-D Lift Quality Head v0 Train Report\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- Offline MuJoCo-only classifier training from dense sensor-fusion traces.\n",
        "- Predicts lift/grasp quality labels, not full hand actions.\n",
        "- No closed-loop controller or demo-gallery promotion is made here.\n\n",
        "## Outputs\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Metadata: `{payload['metadata']}`\n\n",
        "## Main Result\n\n",
        f"- Rows total/train/val: `{main['rows_total']}` / `{main['rows_train']}` / `{main['rows_val']}`\n",
        f"- Input dim: `{main['input_dim']}`\n",
        f"- Best epoch: `{main['best_epoch']}`\n",
        f"- Primary val F1 (`lift_quality_now`): `{main['primary_val_f1']:.4f}`\n\n",
        "| label | val accuracy | val precision | val recall | val F1 | val AUC |\n",
        "|---|---:|---:|---:|---:|---:|\n",
    ]
    for name, m in main["val_metrics"].items():
        auc = m["auc"]
        auc_text = "nan" if np.isnan(auc) else f"{auc:.4f}"
        lines.append(
            f"| `{name}` | {m['accuracy']:.4f} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {auc_text} |\n"
        )
    if payload.get("ablation_results"):
        lines.extend(["\n## Ablations\n\n", "| config | input dim | lift-quality val F1 |\n", "|---|---:|---:|\n"])
        for row in payload["ablation_results"]:
            lines.append(f"| `{row['config_name']}` | {row['input_dim']} | {row['primary_val_f1']:.4f} |\n")
    lines.extend(
        [
            "\n## Next\n\n",
            "- Use this head as a shadow evaluator in Stage3.11D-E before any control-loop intervention.\n",
            "- If all-sensor beats ablations, add a bounded residual micro-adjust teacher around low-quality windows.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train Stage3.11D-D lift-quality head.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--epochs", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.08)
    parser.add_argument("--val-fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=20260612)
    parser.add_argument("--ablation-suite", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    data = load_dataset(Path(args.dataset))
    dataset_metadata = parse_metadata_json(data)
    results = []
    main_result: dict[str, Any] | None = None
    for idx, cfg in enumerate(config_variants(args)):
        bundle = build_feature_bundle(
            data,
            use_vision=bool(cfg["use_vision"]),
            use_tactile=bool(cfg["use_tactile"]),
            use_force=bool(cfg["use_force"]),
            use_context=bool(cfg["use_context"]),
            use_proprio=bool(cfg["use_proprio"]),
            use_phase_onehot=bool(cfg["use_phase_onehot"]),
        )
        checkpoint = Path(args.checkpoint) if cfg["name"] == "all_sensors" else None
        result = train_once(
            bundle,
            config_name=str(cfg["name"]),
            epochs=int(args.epochs),
            batch_size=int(args.batch_size),
            lr=float(args.lr),
            hidden_dim=int(args.hidden_dim),
            dropout=float(args.dropout),
            val_fraction=float(args.val_fraction),
            seed=int(args.seed) + idx,
            checkpoint=checkpoint,
            dataset_metadata=dataset_metadata,
        )
        print(
            f"{result['config_name']}: rows={result['rows_total']} input={result['input_dim']} "
            f"val_lift_quality_f1={result['primary_val_f1']:.4f}"
        )
        results.append(result)
        if cfg["name"] == "all_sensors":
            main_result = result
    assert main_result is not None
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-D",
        "status": STATUS,
        "dataset": str(Path(args.dataset).resolve()),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "report": str(Path(args.report).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "args": vars(args),
        "dataset_metadata": dataset_metadata,
        "main_result": main_result,
        "ablation_results": results,
        "boundary": {
            "mujoco_only": True,
            "offline_classifier_only": True,
            "full_action_policy": False,
            "closed_loop_promoted": False,
            "hardware_runtime": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), payload)
    print(json.dumps(json_ready({"status": STATUS, "main_result": main_result}), indent=2, ensure_ascii=False))
    print(f"Saved checkpoint: {args.checkpoint}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
