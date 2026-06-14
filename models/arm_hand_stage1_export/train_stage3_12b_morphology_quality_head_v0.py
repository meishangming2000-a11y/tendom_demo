#!/usr/bin/env python3
"""Train Stage3.12B morphology-quality head.

The head predicts current morphology/quality labels from dense MuJoCo sensor
features. It is an offline shadow scorer only; it does not output actions and
does not promote a controller.
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

import export_stage3_11d_d_dense_sensor_fusion_dataset_v0 as dense
from train_stage3_11d_d_lift_quality_head_v0 import (
    LiftQualityHead,
    batch_indices,
    binary_auc,
    normalize,
    split_by_episode,
)


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_DATASET = DATA / "stage3_12b_morphology_quality_dataset_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_12b_morphology_quality_head_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_12b_morphology_quality_head_v0_train_report.md"
DEFAULT_METADATA = META / "stage3_12b_morphology_quality_head_v0_train.json"

STATUS = "stage3_12b_morphology_quality_head_v0_offline_trained_not_control_promoted"
GRASP_EVIDENCE_PHASES = {"contact_gate", "post_contact_settle", "preload", "slow_lift", "hold"}
TARGET_NAMES = [
    "morphology_clean_now",
    "good_two_tip_now",
    "low_non_tip_now",
    "wrap_now",
    "floor_contact_now",
    "penetration_risk_now",
    "lift_quality_now",
    "future_success",
]


@dataclass(frozen=True)
class FeatureBundle:
    x: np.ndarray
    y: np.ndarray
    row_mask: np.ndarray
    feature_names: list[str]
    target_names: list[str]
    episode_ids: np.ndarray
    candidate_ids: np.ndarray


def load_dataset(path: Path) -> np.lib.npyio.NpzFile:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=False)


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def parse_metadata_json(data: np.lib.npyio.NpzFile) -> dict[str, Any]:
    if "metadata_json" not in data.files:
        return {}
    return json.loads(str(data["metadata_json"][0]))


def require_fields(data: np.lib.npyio.NpzFile, fields: list[str]) -> None:
    missing = [field for field in fields if field not in data.files]
    if missing:
        raise KeyError(f"Dataset missing fields: {missing}")


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


def label_index(names: list[str], name: str) -> int:
    if name not in names:
        raise KeyError(f"Missing label {name!r}; available={names}")
    return int(names.index(name))


def feature_index(names: list[str], name: str) -> int:
    if name not in names:
        raise KeyError(f"Missing feature {name!r}; available={names}")
    return int(names.index(name))


def build_targets(data: np.lib.npyio.NpzFile, *, max_non_tip_ratio: float) -> np.ndarray:
    safety_names = string_list(data["safety_label_names"])
    tactile_names = string_list(data["tactile_feature_names"])
    labels = np.asarray(data["safety_labels"], dtype=np.float32)
    tactile = np.asarray(data["tactile_features"], dtype=np.float32)

    good_two_tip = labels[:, label_index(safety_names, "good_two_tip_now")] >= 0.5
    wrap = labels[:, label_index(safety_names, "wrap_now")] >= 0.5
    floor = labels[:, label_index(safety_names, "floor_contact_now")] >= 0.5
    penetration = labels[:, label_index(safety_names, "penetration_risk_now")] >= 0.5
    lift_quality = labels[:, label_index(safety_names, "lift_quality_now")] >= 0.5
    future_success = labels[:, label_index(safety_names, "future_success")] >= 0.5
    non_tip = tactile[:, feature_index(tactile_names, "non_tip_contact_ratio")]
    low_non_tip = non_tip <= float(max_non_tip_ratio)
    morphology_clean = good_two_tip & low_non_tip & (~wrap) & (~floor) & (~penetration)

    return np.stack(
        [
            morphology_clean.astype(np.float32),
            good_two_tip.astype(np.float32),
            low_non_tip.astype(np.float32),
            wrap.astype(np.float32),
            floor.astype(np.float32),
            penetration.astype(np.float32),
            lift_quality.astype(np.float32),
            future_success.astype(np.float32),
        ],
        axis=1,
    ).astype(np.float32)


def build_feature_bundle(
    data: np.lib.npyio.NpzFile,
    *,
    max_non_tip_ratio: float,
    use_vision: bool,
    use_tactile: bool,
    use_force: bool,
    use_context: bool,
    use_proprio: bool,
    use_phase_onehot: bool,
    use_candidate_onehot: bool,
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
            "tactile_feature_names",
            "phase_ids",
            "phase_names",
            "episode_ids",
            "candidate_ids",
            "candidate_names",
        ],
    )
    phase_names = string_list(data["phase_names"])
    phase_ids = np.asarray(data["phase_ids"], dtype=np.int32)
    phase_mask = np.asarray([phase_names[int(idx)] in GRASP_EVIDENCE_PHASES for idx in phase_ids], dtype=bool)

    parts: list[np.ndarray] = []
    names: list[str] = []
    add_block(parts, names, data, enabled=use_vision, array_name="vision_features", name_array="vision_feature_names", prefix="vision")
    add_block(parts, names, data, enabled=use_tactile, array_name="tactile_features", name_array="tactile_feature_names", prefix="tactile")
    add_block(parts, names, data, enabled=use_force, array_name="force_features", name_array="force_feature_names", prefix="force")
    add_block(parts, names, data, enabled=use_context, array_name="context_features", name_array="context_feature_names", prefix="context")
    add_block(parts, names, data, enabled=use_proprio, array_name="proprio_features", name_array="", prefix="proprio")
    if use_phase_onehot:
        parts.append(one_hot(phase_ids, len(phase_names)).astype(np.float32))
        names.extend([f"phase.{name}" for name in phase_names])
    candidate_ids = np.asarray(data["candidate_ids"], dtype=np.int32)
    candidate_names = string_list(data["candidate_names"])
    if use_candidate_onehot:
        parts.append(one_hot(candidate_ids, len(candidate_names)).astype(np.float32))
        names.extend([f"candidate.{name}" for name in candidate_names])
    if not parts:
        raise ValueError("At least one feature block must be enabled.")
    x_all = np.concatenate(parts, axis=1).astype(np.float32)
    y_all = build_targets(data, max_non_tip_ratio=max_non_tip_ratio)
    return FeatureBundle(
        x=x_all[phase_mask],
        y=y_all[phase_mask],
        row_mask=phase_mask,
        feature_names=names,
        target_names=TARGET_NAMES,
        episode_ids=np.asarray(data["episode_ids"], dtype=np.int32)[phase_mask],
        candidate_ids=candidate_ids[phase_mask],
    )


def evaluate(model: LiftQualityHead, x: np.ndarray, y: np.ndarray, target_names: list[str]) -> dict[str, Any]:
    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(x.astype(np.float32))).cpu().numpy()
    probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -60.0, 60.0)))
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


def candidate_metrics(
    model: LiftQualityHead,
    x: np.ndarray,
    y: np.ndarray,
    candidate_ids: np.ndarray,
    candidate_names: list[str],
    target_names: list[str],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for idx, name in enumerate(candidate_names):
        mask = candidate_ids == idx
        if not np.any(mask):
            continue
        out[name] = evaluate(model, x[mask], y[mask], target_names)
    return out


def primary_score(metrics: dict[str, Any]) -> float:
    return float(metrics.get("morphology_clean_now", {}).get("f1", 0.0))


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
    checkpoint: Path | None,
    dataset_metadata: dict[str, Any],
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
        for batch in batch_indices(len(train_x), int(batch_size), rng):
            xb = torch.from_numpy(train_x[batch])
            yb = torch.from_numpy(train_y[batch])
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            losses.append(float(loss.item()))
        val_metrics = evaluate(model, val_x, val_y, bundle.target_names)
        score = primary_score(val_metrics)
        history.append({"epoch": float(epoch), "train_loss": float(np.mean(losses)), "val_morphology_clean_f1": score})
        if score >= best_score:
            best_score = score
            best_epoch = int(epoch)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    train_metrics = evaluate(model, train_x, train_y, bundle.target_names)
    val_metrics = evaluate(model, val_x, val_y, bundle.target_names)
    candidate_names = [str(name) for name in dataset_metadata.get("candidate_names", [])]
    val_candidate_metrics = (
        candidate_metrics(model, val_x, val_y, bundle.candidate_ids[val_mask], candidate_names, bundle.target_names)
        if candidate_names
        else {}
    )
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
        "val_candidate_metrics": val_candidate_metrics,
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
                "dataset_metadata": dataset_metadata,
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
        "use_candidate_onehot": bool(args.use_candidate_onehot),
    }
    if not bool(args.ablation_suite):
        return [{"name": "all_sensors", **all_blocks}]
    return [
        {"name": "all_sensors", **all_blocks},
        {"name": "no_tactile", **{**all_blocks, "use_tactile": False}},
        {"name": "no_force", **{**all_blocks, "use_force": False}},
        {"name": "no_vision", **{**all_blocks, "use_vision": False}},
        {"name": "no_proprio", **{**all_blocks, "use_proprio": False}},
    ]


def write_report(path: Path, payload: dict[str, Any]) -> None:
    main = payload["main_result"]
    lines = [
        "# Stage3.12B Morphology Quality Head v0 Train Report\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- Offline MuJoCo-only classifier training from dense morphology-quality traces.\n",
        "- Predicts morphology/quality labels, not hand or arm actions.\n",
        "- No closed-loop controller, demo-gallery, full-action ACT/DP, or hardware-runtime promotion is made here.\n\n",
        "## Outputs\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Metadata: `{payload['metadata']}`\n\n",
        "## Main Result\n\n",
        f"- Rows total/train/val: `{main['rows_total']}` / `{main['rows_train']}` / `{main['rows_val']}`\n",
        f"- Input dim: `{main['input_dim']}`\n",
        f"- Best epoch: `{main['best_epoch']}`\n",
        f"- Primary val F1 (`morphology_clean_now`): `{main['primary_val_f1']:.4f}`\n\n",
        "| label | val accuracy | val precision | val recall | val F1 | val AUC | positive fraction |\n",
        "|---|---:|---:|---:|---:|---:|---:|\n",
    ]
    for name, m in main["val_metrics"].items():
        auc = m["auc"]
        auc_text = "nan" if np.isnan(auc) else f"{auc:.4f}"
        lines.append(
            f"| `{name}` | {m['accuracy']:.4f} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {auc_text} | {m['positive_fraction']:.4f} |\n"
        )
    if main.get("val_candidate_metrics"):
        lines.extend(
            [
                "\n## Candidate Validation Slice\n\n",
                "| candidate | morphology-clean F1 | good-two-tip F1 | lift-quality F1 | future-success F1 |\n",
                "|---|---:|---:|---:|---:|\n",
            ]
        )
        for candidate, metrics in main["val_candidate_metrics"].items():
            lines.append(
                f"| `{candidate}` | {metrics['morphology_clean_now']['f1']:.4f} | "
                f"{metrics['good_two_tip_now']['f1']:.4f} | {metrics['lift_quality_now']['f1']:.4f} | "
                f"{metrics['future_success']['f1']:.4f} |\n"
            )
    if payload.get("ablation_results"):
        lines.extend(["\n## Ablations\n\n", "| config | input dim | morphology-clean val F1 |\n", "|---|---:|---:|\n"])
        for row in payload["ablation_results"]:
            lines.append(f"| `{row['config_name']}` | {row['input_dim']} | {row['primary_val_f1']:.4f} |\n")
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is a current-state morphology/quality scorer. It can be used for shadow ranking and residual-window selection.\n",
            "- It is not yet an action policy. Promotion still requires closed-loop multiseed evidence against frozen D-I.\n\n",
            "## Next\n\n",
            "- Run the head in shadow on fresh D-I/lift candidates and log false positive/false negative windows.\n",
            "- Use only high-confidence low-quality windows to design a bounded residual teacher; reject any branch that trades lift failures for morphology failures.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train Stage3.12B morphology-quality head.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.08)
    parser.add_argument("--val-fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--max-non-tip-ratio", type=float, default=0.45)
    parser.add_argument("--use-candidate-onehot", action=argparse.BooleanOptionalAction, default=False)
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
            max_non_tip_ratio=float(args.max_non_tip_ratio),
            use_vision=bool(cfg["use_vision"]),
            use_tactile=bool(cfg["use_tactile"]),
            use_force=bool(cfg["use_force"]),
            use_context=bool(cfg["use_context"]),
            use_proprio=bool(cfg["use_proprio"]),
            use_phase_onehot=bool(cfg["use_phase_onehot"]),
            use_candidate_onehot=bool(cfg["use_candidate_onehot"]),
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
            f"val_morphology_clean_f1={result['primary_val_f1']:.4f}"
        )
        results.append(result)
        if cfg["name"] == "all_sensors":
            main_result = result
    assert main_result is not None

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.12B",
        "status": STATUS,
        "dataset": str(Path(args.dataset).resolve()),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "args": vars(args),
        "dataset_metadata": dataset_metadata,
        "main_result": main_result,
        "ablation_results": results,
        "boundary": {
            "mujoco_only": True,
            "offline_classifier": True,
            "predicts_actions": False,
            "hardware_runtime": False,
            "controller_promoted": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(dense.json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), dense.json_ready(payload))
    print(json.dumps(dense.json_ready(main_result["val_metrics"]), indent=2, ensure_ascii=False))
    print(f"Saved checkpoint: {args.checkpoint}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
