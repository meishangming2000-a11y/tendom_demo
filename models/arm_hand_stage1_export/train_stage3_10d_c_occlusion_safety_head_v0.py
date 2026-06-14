#!/usr/bin/env python3
"""Stage3.10D-C episode-level noisy-vision / occlusion safety head.

This script turns Stage3.10D-B benchmark metadata into a compact supervised
dataset and trains a lightweight multi-label logistic head. It is deliberately
episode-level: the goal is to verify whether the closed-loop evidence can
explain when the system should trust final vision, hand off to tactile
corroboration, use the accepted-nominal quality adapter, or apply pinch repair.

It is not a full-action ACT/DP policy and it is not a hardware integration.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_BENCHMARKS = [
    META / "stage3_10d_b_occlusion_benchmark_v0.json",
    META / "stage3_10d_b_occlusion_benchmark_v1.json",
]
DEFAULT_DATASET = DATA / "stage3_10d_c_occlusion_safety_head_dataset_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_10d_c_occlusion_safety_head_v0.npz"
DEFAULT_METADATA = META / "stage3_10d_c_occlusion_safety_head_v0.json"
DEFAULT_REPORT = DOCS / "stage3_10d_c_occlusion_safety_head_v0_closeout.md"

LABEL_NAMES = [
    "initial_quality_adapter_required",
    "final_tactile_handoff_required",
    "final_occlusion_aware_required",
    "pinch_repair_required_or_active",
    "strict_final_vision_safe",
    "hold_safe",
    "failure_or_blocked",
    "floor_or_hold_failure",
]

FEATURE_NAMES = [
    "skill_is_full_hand",
    "skill_is_pinch",
    "random_offset_std",
    "verification_is_strict_vision",
    "verification_is_corroborated",
    "verification_is_occlusion_aware",
    "initial_stress_is_none",
    "initial_stress_is_maskdrop30",
    "final_stress_is_none",
    "final_stress_is_maskdrop55",
    "final_stress_is_occluder45",
    "initial_vision_accepted",
    "initial_vision_confidence",
    "initial_vision_mask_pixels_k",
    "initial_vision_mask_retention_ratio",
    "initial_vision_visibility_fraction",
    "initial_stress_samples",
    "policy_quality_is_accepted_nominal",
    "policy_vision_confidence",
    "policy_vision_occlusion",
    "final_vision_primary_accepted",
    "final_vision_accepted",
    "final_vision_confidence",
    "final_vision_mask_pixels_k",
    "final_vision_mask_retention_ratio",
    "final_vision_visibility_fraction",
    "final_stress_samples",
    "final_low_confidence_vision_ok",
    "final_occluded_vision_mask_ok",
    "final_tactile_hold_ok",
    "final_floor_contacts",
    "true_lift_height_m",
    "vision_lift_height_m",
    "vision_true_lift_error_m",
    "hold_stable_fraction",
    "hold_pinch_fraction",
    "hold_max_slip_score",
    "max_slip_score",
    "max_crush_risk",
    "max_penetration_m",
    "pinch_repair_mode_all",
    "pinch_repair_event_count",
    "pinch_repair_max_close_delta",
    "pinch_repair_max_expert_alpha",
]


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        val = float(value)
        return val if math.isfinite(val) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def finite_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(numeric):
        return float(default)
    return numeric


def finite_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "pass", "ok"}


def stress_name(value: Any) -> str:
    text = str(value or "none").strip()
    return text if text else "none"


def repair_event_count(summary: dict[str, Any]) -> int:
    counts = summary.get("repair_event_counts") or {}
    if not isinstance(counts, dict):
        return 0
    total = 0
    for value in counts.values():
        try:
            total += int(value)
        except (TypeError, ValueError):
            continue
    return total


@dataclass
class EpisodeRecord:
    source_benchmark: str
    case_id: str
    episode_id: int
    skill_id: str
    success: bool
    features: list[float]
    labels: list[float]
    row: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def case_metadata_path(case: dict[str, Any]) -> Path:
    raw = Path(str(case["metadata"]))
    if raw.exists():
        return raw
    return ROOT / raw


def make_features_and_labels(
    *,
    benchmark_path: Path,
    case: dict[str, Any],
    payload: dict[str, Any],
    result: dict[str, Any],
) -> tuple[list[float], list[float], dict[str, Any]]:
    args = payload.get("args", {})
    summary = result.get("summary", {})
    skill_id = str(result.get("skill_id", "unknown"))
    final_mode = str(case.get("final_verification_mode", args.get("pinch_final_verification_mode", "strict_vision")))
    initial_stress = stress_name(
        summary.get("initial_vision_stress_scenario", case.get("initial_vision_stress_scenario", "none"))
    )
    final_stress = stress_name(summary.get("final_vision_stress_scenario", case.get("final_vision_stress_scenario", "none")))
    policy_quality = str(summary.get("policy_vision_quality_mode", args.get("policy_vision_quality_mode", "raw")))
    repair_mode = str(summary.get("repair_mode", args.get("pinch_repair_mode", "none")))
    event_count = repair_event_count(summary)

    initial_conf = finite_float(summary.get("initial_vision_confidence", summary.get("vision_confidence", 1.0)), 1.0)
    initial_mask_pixels = finite_float(summary.get("initial_vision_mask_pixels", 0.0), 0.0)
    initial_retention = finite_float(summary.get("initial_vision_mask_retention_ratio", 1.0), 1.0)
    initial_visibility = finite_float(summary.get("initial_vision_visibility_fraction", initial_retention), initial_retention)

    final_conf = finite_float(summary.get("final_vision_confidence", 0.0), 0.0)
    final_mask_pixels = finite_float(summary.get("final_vision_mask_pixels", 0.0), 0.0)
    final_retention = finite_float(summary.get("final_vision_mask_retention_ratio", 1.0), 1.0)
    final_visibility = finite_float(summary.get("final_vision_visibility_fraction", final_retention), final_retention)

    initial_samples = finite_float(
        summary.get("initial_vision_stress_samples", case.get("initial_vision_stress_samples", args.get("initial_vision_stress_samples", 1))),
        1.0,
    )
    final_samples = finite_float(
        summary.get("final_vision_stress_samples", case.get("final_vision_stress_samples", args.get("final_vision_stress_samples", 1))),
        1.0,
    )

    final_primary = finite_bool(summary.get("final_vision_primary_accepted", summary.get("final_vision_accepted", False)))
    final_accepted = finite_bool(summary.get("final_vision_accepted", False))
    tactile_hold_ok = finite_bool(summary.get("final_tactile_hold_ok", False))
    final_low_conf_ok = finite_bool(summary.get("final_low_confidence_vision_ok", False))
    final_occluded_mask_ok = finite_bool(summary.get("final_occluded_vision_mask_ok", False))

    hold_stable = finite_float(summary.get("hold_stable_fraction", 0.0), 0.0)
    hold_slip = finite_float(summary.get("hold_max_slip_score", 1.0), 1.0)
    max_slip = finite_float(summary.get("max_slip_score", hold_slip), hold_slip)
    crush = finite_float(summary.get("max_crush_risk", 0.0), 0.0)
    penetration = finite_float(summary.get("max_penetration_m", 0.0), 0.0)
    floor_contacts = finite_float(summary.get("final_floor_contacts", 0.0), 0.0)

    success = bool(result.get("success", False))
    failure_reasons = [str(item) for item in result.get("failure_reasons", [])]
    accepted_by = str(summary.get("final_vision_accepted_by", "none"))

    initial_quality_adapter_required = bool(
        initial_stress != "none"
        and finite_bool(summary.get("initial_vision_accepted", summary.get("vision_accepted", True)))
        and (initial_conf < 0.95 or initial_visibility < 0.80 or initial_retention < 0.80)
    )
    final_tactile_handoff_required = bool(
        accepted_by in {"vision_tactile_corroborated", "vision_tactile_occlusion_aware"}
        or (not final_primary and tactile_hold_ok and (final_low_conf_ok or final_occluded_mask_ok))
    )
    final_occlusion_aware_required = bool(
        final_mode == "vision_tactile_occlusion_aware"
        and final_stress != "none"
        and tactile_hold_ok
        and (final_accepted or final_occluded_mask_ok)
    )
    pinch_repair_required = bool(skill_id == "thumb_index_middle_pinch" and (event_count > 0 or repair_mode == "all"))
    strict_final_vision_safe = bool(
        skill_id == "thumb_index_middle_pinch"
        and final_primary
        and final_accepted
        and success
        and not final_tactile_handoff_required
    )
    hold_safe = bool(
        success
        and hold_stable >= 0.99
        and hold_slip <= 0.35
        and crush <= 0.25
        and penetration <= 0.0045
        and floor_contacts <= 0.0
    )
    failure_or_blocked = bool((not success) or failure_reasons)
    floor_or_hold_failure = bool(
        floor_contacts > 0.0
        or hold_stable < 0.99
        or "hold_tactile_unstable" in failure_reasons
        or "egg_still_touching_floor" in failure_reasons
    )

    features = [
        float(skill_id == "full_hand_gentle_grasp"),
        float(skill_id == "thumb_index_middle_pinch"),
        finite_float(case.get("random_offset_std", 0.0), 0.0),
        float(final_mode == "strict_vision"),
        float(final_mode == "vision_tactile_corroborated"),
        float(final_mode == "vision_tactile_occlusion_aware"),
        float(initial_stress == "none"),
        float(initial_stress == "mask_dropout_30"),
        float(final_stress == "none"),
        float(final_stress == "mask_dropout_55"),
        float(final_stress == "synthetic_occluder_45"),
        float(finite_bool(summary.get("initial_vision_accepted", summary.get("vision_accepted", True)))),
        initial_conf,
        initial_mask_pixels / 1000.0,
        initial_retention,
        initial_visibility,
        initial_samples,
        float(policy_quality == "accepted_nominal"),
        finite_float(summary.get("policy_vision_confidence", initial_conf), initial_conf),
        finite_float(summary.get("policy_vision_occlusion", 1.0 - initial_visibility), 1.0 - initial_visibility),
        float(final_primary),
        float(final_accepted),
        final_conf,
        final_mask_pixels / 1000.0,
        final_retention,
        final_visibility,
        final_samples,
        float(final_low_conf_ok),
        float(final_occluded_mask_ok),
        float(tactile_hold_ok),
        floor_contacts,
        finite_float(summary.get("true_lift_height_m", summary.get("final_lift_height_m", 0.0)), 0.0),
        finite_float(summary.get("vision_lift_height_m", 0.0), 0.0),
        finite_float(summary.get("vision_true_lift_error_m", 0.0), 0.0),
        hold_stable,
        finite_float(summary.get("hold_pinch_fraction", 0.0), 0.0),
        hold_slip,
        max_slip,
        crush,
        penetration,
        float(repair_mode == "all"),
        float(event_count),
        finite_float(summary.get("repair_max_close_delta", 0.0), 0.0),
        finite_float(summary.get("repair_max_expert_alpha", 0.0), 0.0),
    ]

    labels = [
        float(initial_quality_adapter_required),
        float(final_tactile_handoff_required),
        float(final_occlusion_aware_required),
        float(pinch_repair_required),
        float(strict_final_vision_safe),
        float(hold_safe),
        float(failure_or_blocked),
        float(floor_or_hold_failure),
    ]

    row = {
        "source_benchmark": str(Path(benchmark_path).name),
        "case_id": str(case.get("case_id", "unknown")),
        "episode_id": int(result.get("episode_id", -1)),
        "skill_id": skill_id,
        "success": success,
        "terminal_reason": str(result.get("terminal_reason", "")),
        "failure_reasons": failure_reasons,
        "risk_flags": [str(item) for item in result.get("risk_flags", [])],
        "final_vision_accepted_by": accepted_by,
        "initial_vision_stress_scenario": initial_stress,
        "final_vision_stress_scenario": final_stress,
        "policy_vision_quality_mode": policy_quality,
        "pinch_repair_mode": repair_mode,
        "feature_values": dict(zip(FEATURE_NAMES, features)),
        "label_values": dict(zip(LABEL_NAMES, labels)),
    }
    return features, labels, row


def build_records(benchmarks: list[Path]) -> list[EpisodeRecord]:
    records: list[EpisodeRecord] = []
    for benchmark_path in benchmarks:
        benchmark = load_json(benchmark_path)
        for case in benchmark.get("cases", []):
            metadata_path = case_metadata_path(case)
            payload = load_json(metadata_path)
            for result in payload.get("results", []):
                features, labels, row = make_features_and_labels(
                    benchmark_path=benchmark_path,
                    case=case,
                    payload=payload,
                    result=result,
                )
                records.append(
                    EpisodeRecord(
                        source_benchmark=str(Path(benchmark_path).name),
                        case_id=str(case.get("case_id", "unknown")),
                        episode_id=int(result.get("episode_id", -1)),
                        skill_id=str(result.get("skill_id", "unknown")),
                        success=bool(result.get("success", False)),
                        features=features,
                        labels=labels,
                        row=row,
                    )
                )
    return records


def find_split(labels: np.ndarray, *, val_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    n = int(labels.shape[0])
    val_count = max(1, min(n - 1, int(round(n * float(val_fraction)))))
    candidates = range(int(seed), int(seed) + 1000)
    for split_seed in candidates:
        rng = np.random.default_rng(split_seed)
        order = rng.permutation(n)
        val_idx = np.sort(order[:val_count])
        train_idx = np.sort(order[val_count:])
        ok = True
        for col in range(labels.shape[1]):
            total_pos = int(labels[:, col].sum())
            total_neg = int(labels.shape[0] - total_pos)
            if total_pos == 0 or total_neg == 0:
                continue
            val_pos = int(labels[val_idx, col].sum())
            val_neg = int(len(val_idx) - val_pos)
            train_pos = int(labels[train_idx, col].sum())
            train_neg = int(len(train_idx) - train_pos)
            if min(val_pos, val_neg, train_pos, train_neg) <= 0:
                ok = False
                break
        if ok:
            return train_idx, val_idx
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    return np.sort(order[val_count:]), np.sort(order[:val_count])


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def train_logistic_head(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[np.ndarray, list[dict[str, float]]]:
    x_aug = np.concatenate([x_train, np.ones((x_train.shape[0], 1), dtype=np.float32)], axis=1)
    weights = np.zeros((x_aug.shape[1], y_train.shape[1]), dtype=np.float64)
    pos = np.maximum(y_train.sum(axis=0), 1.0)
    neg = np.maximum(y_train.shape[0] - y_train.sum(axis=0), 1.0)
    pos_weight = np.clip(neg / pos, 1.0, 20.0)
    history: list[dict[str, float]] = []
    for epoch in range(1, int(epochs) + 1):
        logits = x_aug @ weights
        probs = sigmoid(logits)
        sample_weight = np.where(y_train > 0.5, pos_weight.reshape(1, -1), 1.0)
        grad = (x_aug.T @ ((probs - y_train) * sample_weight)) / float(x_aug.shape[0])
        grad[:-1] += float(l2) * weights[:-1]
        weights -= float(lr) * grad
        if epoch == 1 or epoch == int(epochs) or epoch % max(1, int(epochs) // 10) == 0:
            eps = 1e-7
            loss = -np.mean(sample_weight * (y_train * np.log(probs + eps) + (1.0 - y_train) * np.log(1.0 - probs + eps)))
            loss += 0.5 * float(l2) * float(np.mean(weights[:-1] ** 2))
            history.append({"epoch": float(epoch), "loss": float(loss)})
    return weights.astype(np.float32), history


def predict(weights: np.ndarray, x: np.ndarray) -> np.ndarray:
    x_aug = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float32)], axis=1)
    return sigmoid(x_aug @ weights)


def binary_metrics(probs: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    pred = probs >= 0.5
    truth = labels >= 0.5
    output: dict[str, Any] = {}
    per_label: dict[str, Any] = {}
    accuracies = []
    recalls = []
    f1s = []
    for idx, name in enumerate(LABEL_NAMES):
        tp = int(np.logical_and(pred[:, idx], truth[:, idx]).sum())
        tn = int(np.logical_and(~pred[:, idx], ~truth[:, idx]).sum())
        fp = int(np.logical_and(pred[:, idx], ~truth[:, idx]).sum())
        fn = int(np.logical_and(~pred[:, idx], truth[:, idx]).sum())
        positives = int(truth[:, idx].sum())
        negatives = int(truth.shape[0] - positives)
        accuracy = float((tp + tn) / max(1, truth.shape[0]))
        precision = float(tp / max(1, tp + fp))
        recall = float(tp / max(1, tp + fn))
        f1 = float(2.0 * precision * recall / max(1e-9, precision + recall))
        evaluable = bool(positives > 0 and negatives > 0)
        per_label[name] = {
            "evaluable": evaluable,
            "positives": positives,
            "negatives": negatives,
            "predicted_positives": int(pred[:, idx].sum()),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
        accuracies.append(accuracy)
        if evaluable:
            recalls.append(recall)
            f1s.append(f1)
    output["per_label"] = per_label
    output["mean_accuracy"] = float(np.mean(accuracies)) if accuracies else 0.0
    output["mean_evaluable_recall"] = float(np.mean(recalls)) if recalls else 0.0
    output["mean_evaluable_f1"] = float(np.mean(f1s)) if f1s else 0.0
    return output


def count_by(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in values:
        counts[item] = counts.get(item, 0) + 1
    return counts


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(json_ready(row), ensure_ascii=False) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = payload["label_distribution"]
    val_metrics = payload["metrics"]["val"]["per_label"]
    holdout = payload["metrics"].get("v0_train_v1_holdout", {})
    lines = [
        "# Stage3.10D-C Occlusion Safety Head v0 Closeout\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{payload['status']}`\n",
        f"- episode 样本：`{payload['record_count']}`\n",
        f"- 数据集：`{payload['dataset']}`\n",
        f"- checkpoint：`{payload['checkpoint']}`\n",
        f"- metadata：`{payload['metadata']}`\n",
        "- 边界：这是 MuJoCo episode-level safety evidence head；不是 full-action ACT/DP，也不是硬件/真实摄像头集成。\n\n",
        "## 这一步做了什么\n\n",
        "D-B v1 已经能在遮挡/noisy-vision 下通过 `100 / 100`，但里面仍有经验规则：多帧视觉选择、`accepted_nominal` 质量适配、最终视觉/触觉融合验收，以及更早的 pinch tactile fallback。D-C 把 D-B v0/v1 的闭环结果抽成监督数据，训练一个轻量多标签 safety head，用来检查这些规则是否能被机器可读地表达出来。\n\n",
        "## 标签分布\n\n",
        "| label | positive / total | 含义 |\n",
        "| --- | ---: | --- |\n",
    ]
    meanings = {
        "initial_quality_adapter_required": "初始视觉通过但质量字段偏 noisy，需要控制侧质量适配",
        "final_tactile_handoff_required": "最终视觉不够强，需要触觉 hold/局部视觉共同兜底",
        "final_occlusion_aware_required": "最终遮挡场景下应走 occlusion-aware 验收",
        "pinch_repair_required_or_active": "捏持过程中需要或触发 repair/fallback",
        "strict_final_vision_safe": "严格最终视觉足够确认捏持成功",
        "hold_safe": "真实 hold/slip/crush/penetration/floor-contact 均在门内",
        "failure_or_blocked": "episode 失败或被 failure reason 阻塞",
        "floor_or_hold_failure": "地面接触或 hold 不稳定类失败",
    }
    for name in LABEL_NAMES:
        row = labels[name]
        lines.append(f"| `{name}` | `{row['positive']} / {row['total']}` | {meanings[name]} |\n")

    lines.extend(
        [
            "\n## Random validation\n\n",
            f"- val mean accuracy：`{payload['metrics']['val']['mean_accuracy']:.6f}`\n",
            f"- val mean evaluable recall：`{payload['metrics']['val']['mean_evaluable_recall']:.6f}`\n",
            f"- val mean evaluable F1：`{payload['metrics']['val']['mean_evaluable_f1']:.6f}`\n\n",
            "| label | acc | precision | recall | F1 | positives | predicted positives |\n",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n",
        ]
    )
    for name in LABEL_NAMES:
        row = val_metrics[name]
        lines.append(
            f"| `{name}` | `{row['accuracy']:.3f}` | `{row['precision']:.3f}` | `{row['recall']:.3f}` | "
            f"`{row['f1']:.3f}` | `{row['positives']}` | `{row['predicted_positives']}` |\n"
        )

    if holdout:
        lines.extend(
            [
                "\n## v0 -> v1 holdout\n\n",
                "额外检查：只用 D-B v0 训练，再在 D-B v1 上测试，看看安全头能否识别修补后的 v1 事件分布。这个不是最终推广门槛，因为 v1 没有失败样本，但它能检查 occlusion/adapter/repair 标签是否仍可读。\n\n",
                f"- v1 holdout mean accuracy：`{holdout['mean_accuracy']:.6f}`\n",
                f"- v1 holdout mean evaluable recall：`{holdout['mean_evaluable_recall']:.6f}`\n",
                f"- v1 holdout mean evaluable F1：`{holdout['mean_evaluable_f1']:.6f}`\n\n",
            ]
        )

    lines.extend(
        [
            "## 判断\n\n",
            f"- `stage3_10d_c_ready_for_d_d`：`{payload['stage3_10d_c_ready_for_d_d']}`\n",
            "- 这一步说明：我们已经不只是会跑过 D-B，而是能把“视觉质量异常、最终遮挡、触觉兜底、捏持 repair、真实 hold 失败”整理成可训练/可评估的安全证据。\n",
            "- 仍然不能夸大：这个 head 使用 episode-level 事后证据，下一步要么把它接进 evaluator 的在线 summary 检查，要么导出逐帧版本接回 ACT/DP 数据。\n\n",
            "## 如果成功\n\n",
            "进入 Stage3.10D-D：用 D-C 的 safety head 重新扫描 D-B v1 和一个新增 stress 小基准，确认它不会把遮挡成功样本误判成失败，也不会把真实 hold/floor-contact 失败放过。\n\n",
            "## 如果失败\n\n",
            "先查标签定义和样本覆盖：尤其是失败样本只有 D-B v0 的 12 条，不能靠放宽 slip/crush/penetration 阈值过关。必要时再补跑专门的失败采样，而不是继续微调单个 demo。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmarks", nargs="+", type=Path, default=DEFAULT_BENCHMARKS)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DATA / "stage3_10d_c_occlusion_safety_head_dataset_v0.jsonl")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--seed", type=int, default=310)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--epochs", type=int, default=2500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1e-4)
    args = parser.parse_args()

    records = build_records([Path(p) for p in args.benchmarks])
    if not records:
        raise RuntimeError("No Stage3.10D-B episode records found.")

    features = np.asarray([record.features for record in records], dtype=np.float32)
    labels = np.asarray([record.labels for record in records], dtype=np.float32)
    row_json = np.asarray([json.dumps(json_ready(record.row), ensure_ascii=False) for record in records], dtype=str)
    train_idx, val_idx = find_split(labels, val_fraction=float(args.val_fraction), seed=int(args.seed))

    mean = features[train_idx].mean(axis=0)
    std = np.maximum(features[train_idx].std(axis=0), 1e-6)
    x_train = (features[train_idx] - mean.reshape(1, -1)) / std.reshape(1, -1)
    x_val = (features[val_idx] - mean.reshape(1, -1)) / std.reshape(1, -1)
    weights, history = train_logistic_head(
        x_train,
        labels[train_idx],
        epochs=int(args.epochs),
        lr=float(args.lr),
        l2=float(args.l2),
    )
    train_probs = predict(weights, x_train)
    val_probs = predict(weights, x_val)

    metrics = {
        "train": binary_metrics(train_probs, labels[train_idx]),
        "val": binary_metrics(val_probs, labels[val_idx]),
    }

    source_names = [record.source_benchmark for record in records]
    v0_idx = np.asarray([i for i, name in enumerate(source_names) if name.endswith("_v0.json")], dtype=np.int64)
    v1_idx = np.asarray([i for i, name in enumerate(source_names) if name.endswith("_v1.json")], dtype=np.int64)
    if len(v0_idx) > 0 and len(v1_idx) > 0:
        v0_mean = features[v0_idx].mean(axis=0)
        v0_std = np.maximum(features[v0_idx].std(axis=0), 1e-6)
        v0_weights, _ = train_logistic_head(
            (features[v0_idx] - v0_mean.reshape(1, -1)) / v0_std.reshape(1, -1),
            labels[v0_idx],
            epochs=int(args.epochs),
            lr=float(args.lr),
            l2=float(args.l2),
        )
        v1_probs = predict(v0_weights, (features[v1_idx] - v0_mean.reshape(1, -1)) / v0_std.reshape(1, -1))
        metrics["v0_train_v1_holdout"] = binary_metrics(v1_probs, labels[v1_idx])

    label_distribution = {
        name: {
            "positive": int(labels[:, idx].sum()),
            "negative": int(labels.shape[0] - labels[:, idx].sum()),
            "total": int(labels.shape[0]),
        }
        for idx, name in enumerate(LABEL_NAMES)
    }
    readiness_labels = [
        "initial_quality_adapter_required",
        "final_tactile_handoff_required",
        "final_occlusion_aware_required",
        "pinch_repair_required_or_active",
        "hold_safe",
        "failure_or_blocked",
        "floor_or_hold_failure",
    ]
    val_per_label = metrics["val"]["per_label"]
    ready = all(
        (not val_per_label[name]["evaluable"])
        or (val_per_label[name]["recall"] >= 0.90 and val_per_label[name]["f1"] >= 0.85)
        for name in readiness_labels
    )

    args.dataset.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.dataset,
        features=features,
        labels=labels,
        train_indices=train_idx,
        val_indices=val_idx,
        feature_names=np.asarray(FEATURE_NAMES, dtype=str),
        label_names=np.asarray(LABEL_NAMES, dtype=str),
        row_json=row_json,
    )
    write_jsonl(Path(args.jsonl), [record.row for record in records])

    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.checkpoint,
        weights=weights,
        feature_mean=mean,
        feature_std=std,
        feature_names=np.asarray(FEATURE_NAMES, dtype=str),
        label_names=np.asarray(LABEL_NAMES, dtype=str),
        train_indices=train_idx,
        val_indices=val_idx,
    )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "PASS" if ready else "NEEDS_MORE_DATA",
        "stage": "Stage3.10D-C",
        "record_count": int(len(records)),
        "feature_count": int(features.shape[1]),
        "label_count": int(labels.shape[1]),
        "feature_names": FEATURE_NAMES,
        "label_names": LABEL_NAMES,
        "source_benchmarks": [str(Path(p).resolve()) for p in args.benchmarks],
        "source_counts": count_by(source_names),
        "case_counts": count_by([record.case_id for record in records]),
        "skill_counts": count_by([record.skill_id for record in records]),
        "label_distribution": label_distribution,
        "train_count": int(len(train_idx)),
        "val_count": int(len(val_idx)),
        "train_indices": train_idx.tolist(),
        "val_indices": val_idx.tolist(),
        "metrics": metrics,
        "history": history,
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "stage3_10d_c_ready_for_d_d": bool(ready),
        "boundary": {
            "mujoco_only": True,
            "episode_level_evidence_head": True,
            "full_action_act_dp_promoted": False,
            "hardware_integration": False,
            "real_camera": False,
        },
        "next": "Stage3.10D-D: re-scan D-B v1 plus a small new stress benchmark with this safety head before closing Stage3.10.",
    }

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(Path(args.report), payload)
    print(
        "Stage3.10D-C occlusion safety head: "
        f"status={payload['status']} records={payload['record_count']} "
        f"val_mean_f1={metrics['val']['mean_evaluable_f1']:.6f}"
    )
    print(f"dataset={Path(args.dataset).resolve()}")
    print(f"checkpoint={Path(args.checkpoint).resolve()}")
    print(f"report={Path(args.report).resolve()}")
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
