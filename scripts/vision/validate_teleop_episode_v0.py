#!/usr/bin/env python3
"""Validate replay readiness for one teleop_episode_v0 file."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


SIM_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SIM_ROOT.parent
TOOLS_ROOT = PROJECT_ROOT / "tools"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, Path):
        return str(value)
    return value


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _load_contract_validation(episode_path: Path) -> Dict[str, Any]:
    sys.path.insert(0, str(TOOLS_ROOT))
    import validate_teleop_dataset_contract_v0 as contract_validator

    return contract_validator.validate_file(
        sample_path=episode_path,
        schema_path=PROJECT_ROOT / "docs" / "teleop_dataset_contract_v0.schema.json",
    )


def _as_float_array(values: Any, shape_tail: Tuple[int, ...] | None = None) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if shape_tail is not None and arr.shape[-len(shape_tail) :] != shape_tail:
        raise ValueError(f"expected trailing shape {shape_tail}, got {arr.shape}")
    return arr


def _finite_summary(name: str, arr: np.ndarray) -> Dict[str, Any]:
    finite = np.isfinite(arr)
    finite_count = int(np.sum(finite))
    total = int(arr.size)
    payload: Dict[str, Any] = {
        "name": name,
        "shape": list(arr.shape),
        "total": total,
        "finite_count": finite_count,
        "nonfinite_count": int(total - finite_count),
    }
    if finite_count:
        finite_values = arr[finite]
        payload.update(
            {
                "min": float(np.min(finite_values)),
                "max": float(np.max(finite_values)),
                "mean_abs": float(np.mean(np.abs(finite_values))),
                "max_abs": float(np.max(np.abs(finite_values))),
            }
        )
    return payload


def _status_from_reasons(reject_reasons: List[str], review_reasons: List[str]) -> str:
    if reject_reasons:
        return "REJECT"
    if review_reasons:
        return "REVIEW"
    return "PASS"


def _quality_summary(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    statuses = [str(frame.get("quality", {}).get("status", "unknown")) for frame in frames]
    handedness = [str(frame.get("quality", {}).get("handedness", "unknown")) for frame in frames]
    detection = np.asarray(
        [float(frame.get("quality", {}).get("detection_confidence", 0.0) or 0.0) for frame in frames],
        dtype=np.float64,
    )
    tracking = np.asarray(
        [float(frame.get("quality", {}).get("tracking_confidence", 0.0) or 0.0) for frame in frames],
        dtype=np.float64,
    )
    total = max(len(frames), 1)
    return {
        "status_counts": dict(Counter(statuses)),
        "handedness_counts": dict(Counter(handedness)),
        "review_frame_ratio": float(sum(1 for status in statuses if status == "review") / total),
        "reject_frame_ratio": float(sum(1 for status in statuses if status == "reject") / total),
        "min_detection_confidence": float(np.min(detection)) if detection.size else 0.0,
        "min_tracking_confidence": float(np.min(tracking)) if tracking.size else 0.0,
        "mean_detection_confidence": float(np.mean(detection)) if detection.size else 0.0,
        "mean_tracking_confidence": float(np.mean(tracking)) if tracking.size else 0.0,
    }


def _timestamp_summary(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    timestamps = np.asarray([float(frame.get("timestamp_s", 0.0)) for frame in frames], dtype=np.float64)
    timestamp_ns = np.asarray([int(frame.get("timestamp_ns", 0) or 0) for frame in frames], dtype=np.int64)
    if timestamps.size <= 1:
        gaps = np.asarray([], dtype=np.float64)
    else:
        gaps = np.diff(timestamps)
    ns_from_s = np.rint(timestamps * 1_000_000_000).astype(np.int64) if timestamps.size else np.asarray([], dtype=np.int64)
    ns_delta = np.abs(timestamp_ns - ns_from_s) if timestamp_ns.size else np.asarray([], dtype=np.int64)
    median_gap = float(np.median(gaps)) if gaps.size else 0.0
    jitter = np.abs(gaps - median_gap) if gaps.size else np.asarray([], dtype=np.float64)
    return {
        "start_s": float(timestamps[0]) if timestamps.size else 0.0,
        "end_s": float(timestamps[-1]) if timestamps.size else 0.0,
        "duration_s": float(timestamps[-1] - timestamps[0]) if timestamps.size > 1 else 0.0,
        "gap_count": int(gaps.size),
        "negative_gap_count": int(np.sum(gaps < -1e-9)) if gaps.size else 0,
        "zero_gap_count": int(np.sum(np.isclose(gaps, 0.0, atol=1e-9))) if gaps.size else 0,
        "max_gap_s": float(np.max(gaps)) if gaps.size else 0.0,
        "median_gap_s": median_gap,
        "mean_gap_s": float(np.mean(gaps)) if gaps.size else 0.0,
        "max_abs_jitter_s": float(np.max(jitter)) if jitter.size else 0.0,
        "timestamp_ns_mismatch_max": int(np.max(ns_delta)) if ns_delta.size else 0,
    }


def _source_index_summary(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    values = [
        frame.get("source_frame_index")
        for frame in frames
        if frame.get("source_frame_index") is not None
    ]
    if not values:
        return {
            "available": False,
            "count": 0,
            "negative_gap_count": 0,
            "duplicate_gap_count": 0,
            "max_gap": 0,
        }
    arr = np.asarray(values, dtype=np.int64)
    gaps = np.diff(arr) if arr.size > 1 else np.asarray([], dtype=np.int64)
    return {
        "available": True,
        "count": int(arr.size),
        "first": int(arr[0]),
        "last": int(arr[-1]),
        "negative_gap_count": int(np.sum(gaps < 0)) if gaps.size else 0,
        "duplicate_gap_count": int(np.sum(gaps == 0)) if gaps.size else 0,
        "max_gap": int(np.max(gaps)) if gaps.size else 0,
    }


def _action_summary(actions: np.ndarray, action_dims: List[int]) -> Dict[str, Any]:
    if actions.size == 0:
        return {
            "frames": 0,
            "action_dim_set": action_dims,
            "max_abs": 0.0,
            "saturation_fraction": 0.0,
            "out_of_range_fraction": 0.0,
            "max_step_abs": 0.0,
            "max_step_l2": 0.0,
        }
    deltas = np.diff(actions, axis=0) if actions.shape[0] > 1 else np.zeros((0, actions.shape[1]), dtype=np.float64)
    return {
        "frames": int(actions.shape[0]),
        "action_dim": int(actions.shape[1]) if actions.ndim == 2 else 0,
        "action_dim_set": action_dims,
        "min": float(np.min(actions)),
        "max": float(np.max(actions)),
        "mean_abs": float(np.mean(np.abs(actions))),
        "max_abs": float(np.max(np.abs(actions))),
        "saturation_fraction": float(np.mean(np.abs(actions) >= 0.999)),
        "out_of_range_fraction": float(np.mean(np.abs(actions) > 1.000001)),
        "max_step_abs": float(np.max(np.abs(deltas))) if deltas.size else 0.0,
        "mean_step_abs": float(np.mean(np.abs(deltas))) if deltas.size else 0.0,
        "max_step_l2": float(np.max(np.linalg.norm(deltas, axis=1))) if deltas.size else 0.0,
        "mean_step_l2": float(np.mean(np.linalg.norm(deltas, axis=1))) if deltas.size else 0.0,
    }


def _frame_index_summary(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    expected = list(range(len(frames)))
    actual = [int(frame.get("frame_index", -1)) for frame in frames]
    mismatches = [idx for idx, (lhs, rhs) in enumerate(zip(actual, expected)) if lhs != rhs]
    return {
        "count": len(frames),
        "mismatch_count": len(mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
    }


def validate_episode_payload(
    payload: Dict[str, Any],
    episode_path: Path,
    contract_validation: Dict[str, Any],
    *,
    max_timestamp_gap_s: float = 0.25,
    max_action_abs: float = 1.000001,
    max_saturation_fraction: float = 0.2,
    max_action_step_abs: float = 1.25,
    max_review_frame_ratio: float = 0.5,
    min_detection_confidence: float = 0.35,
    min_tracking_confidence: float = 0.35,
) -> Dict[str, Any]:
    frames = payload.get("frames", [])
    if not isinstance(frames, list):
        frames = []

    reject_reasons: List[str] = []
    review_reasons: List[str] = []
    if contract_validation.get("status") != "PASS":
        reject_reasons.append("contract_validation_failed")
    if not frames:
        reject_reasons.append("no_frames")

    frame_index = _frame_index_summary(frames)
    timestamps = _timestamp_summary(frames)
    source_index = _source_index_summary(frames)
    quality = _quality_summary(frames)

    try:
        landmarks = _as_float_array([frame["landmarks_21x3"] for frame in frames], (21, 3))
        palm_features = _as_float_array([frame["palm_feature_76"] for frame in frames], (76,))
        open_close_features = _as_float_array([frame["open_close_feature_35"] for frame in frames], (35,))
        action_dims = sorted(
            {
                int(frame.get("backend_action_v0", {}).get("action_dim", -1))
                for frame in frames
            }
        )
        actions = _as_float_array(
            [frame.get("backend_action_v0", {}).get("values", []) for frame in frames],
            None,
        )
    except Exception as exc:  # noqa: BLE001
        landmarks = np.asarray([], dtype=np.float64)
        palm_features = np.asarray([], dtype=np.float64)
        open_close_features = np.asarray([], dtype=np.float64)
        actions = np.asarray([], dtype=np.float64)
        action_dims = []
        reject_reasons.append(f"array_load_failed:{exc}")

    finite = {
        "landmarks": _finite_summary("landmarks", landmarks),
        "palm_features": _finite_summary("palm_features", palm_features),
        "open_close_features": _finite_summary("open_close_features", open_close_features),
        "backend_actions": _finite_summary("backend_actions", actions),
    }
    actions_summary = _action_summary(actions, action_dims)

    if frame_index["mismatch_count"]:
        reject_reasons.append("frame_index_not_contiguous")
    if timestamps["negative_gap_count"]:
        reject_reasons.append("timestamp_not_monotonic")
    if timestamps["max_gap_s"] > max_timestamp_gap_s:
        review_reasons.append("large_timestamp_gap")
    if timestamps["timestamp_ns_mismatch_max"] > 1_000_000:
        review_reasons.append("timestamp_ns_s_mismatch")
    if source_index["negative_gap_count"]:
        review_reasons.append("source_frame_index_not_monotonic")
    if source_index["max_gap"] > 5:
        review_reasons.append("source_frame_gap")

    for item in finite.values():
        if int(item.get("nonfinite_count", 0)) > 0:
            reject_reasons.append(f"nonfinite_{item['name']}")

    if len(action_dims) != 1:
        reject_reasons.append("inconsistent_backend_action_dim")
    elif action_dims and actions.ndim == 2 and actions.shape[1] != action_dims[0]:
        reject_reasons.append("backend_action_dim_shape_mismatch")
    if actions_summary["max_abs"] > max_action_abs:
        reject_reasons.append("backend_action_out_of_range")
    if actions_summary["saturation_fraction"] > max_saturation_fraction:
        review_reasons.append("backend_action_saturation_high")
    if actions_summary["max_step_abs"] > max_action_step_abs:
        review_reasons.append("backend_action_step_jump")

    if quality["reject_frame_ratio"] > 0:
        reject_reasons.append("frame_quality_reject_present")
    if quality["review_frame_ratio"] > max_review_frame_ratio:
        review_reasons.append("frame_quality_review_ratio_high")
    if quality["min_detection_confidence"] < min_detection_confidence:
        review_reasons.append("low_detection_confidence")
    if quality["min_tracking_confidence"] < min_tracking_confidence:
        review_reasons.append("low_tracking_confidence")

    # Preserve pre-existing episode review/reject labels as review context.
    episode_labels = payload.get("episode_labels", {}) if isinstance(payload.get("episode_labels"), dict) else {}
    if episode_labels.get("status") == "review":
        review_reasons.append("episode_label_status_review")
    elif episode_labels.get("status") == "reject":
        reject_reasons.append("episode_label_status_reject")
    for reason in episode_labels.get("failure_reasons", []) or []:
        if reason and str(reason) not in review_reasons and str(reason) not in reject_reasons:
            review_reasons.append(str(reason))

    review_reasons = sorted(set(review_reasons))
    reject_reasons = sorted(set(reject_reasons))
    status = _status_from_reasons(reject_reasons, review_reasons)
    return {
        "schema_version": "teleop_episode_validation_v0",
        "created_at_utc": _utc_stamp(),
        "episode_path": str(episode_path),
        "episode_id": payload.get("episode_id", episode_path.stem),
        "dataset_id": payload.get("dataset_id", ""),
        "status": status,
        "reject_reasons": reject_reasons,
        "review_reasons": review_reasons,
        "contract_validation": contract_validation,
        "metrics": {
            "frame_index": frame_index,
            "timestamps": timestamps,
            "source_frame_index": source_index,
            "quality": quality,
            "finite": finite,
            "backend_action": actions_summary,
        },
        "thresholds": {
            "max_timestamp_gap_s": float(max_timestamp_gap_s),
            "max_action_abs": float(max_action_abs),
            "max_saturation_fraction": float(max_saturation_fraction),
            "max_action_step_abs": float(max_action_step_abs),
            "max_review_frame_ratio": float(max_review_frame_ratio),
            "min_detection_confidence": float(min_detection_confidence),
            "min_tracking_confidence": float(min_tracking_confidence),
        },
        "not_claimed": [
            "task_success",
            "closed_loop_policy_success",
            "hardware_readiness",
            "train_ready_dataset",
        ],
    }


def validate_episode_file(
    episode_path: Path,
    *,
    max_timestamp_gap_s: float = 0.25,
    max_action_abs: float = 1.000001,
    max_saturation_fraction: float = 0.2,
    max_action_step_abs: float = 1.25,
    max_review_frame_ratio: float = 0.5,
    min_detection_confidence: float = 0.35,
    min_tracking_confidence: float = 0.35,
) -> Dict[str, Any]:
    episode_path = episode_path.expanduser().resolve()
    payload = _read_json(episode_path)
    contract_validation = _load_contract_validation(episode_path)
    return validate_episode_payload(
        payload,
        episode_path,
        contract_validation,
        max_timestamp_gap_s=max_timestamp_gap_s,
        max_action_abs=max_action_abs,
        max_saturation_fraction=max_saturation_fraction,
        max_action_step_abs=max_action_step_abs,
        max_review_frame_ratio=max_review_frame_ratio,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate teleop_episode_v0 replay readiness")
    parser.add_argument("--episode", required=True, type=Path)
    parser.add_argument("--output-report", type=Path, default=None)
    parser.add_argument("--max-timestamp-gap-s", type=float, default=0.25)
    parser.add_argument("--max-action-abs", type=float, default=1.000001)
    parser.add_argument("--max-saturation-fraction", type=float, default=0.2)
    parser.add_argument("--max-action-step-abs", type=float, default=1.25)
    parser.add_argument("--max-review-frame-ratio", type=float, default=0.5)
    parser.add_argument("--min-detection-confidence", type=float, default=0.35)
    parser.add_argument("--min-tracking-confidence", type=float, default=0.35)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    report = validate_episode_file(
        args.episode,
        max_timestamp_gap_s=args.max_timestamp_gap_s,
        max_action_abs=args.max_action_abs,
        max_saturation_fraction=args.max_saturation_fraction,
        max_action_step_abs=args.max_action_step_abs,
        max_review_frame_ratio=args.max_review_frame_ratio,
        min_detection_confidence=args.min_detection_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
    )
    if args.output_report:
        _write_json(args.output_report, report)
    print(json.dumps(_json_ready(report), indent=2, ensure_ascii=True))
    if report["status"] == "REJECT" or (args.fail_on_review and report["status"] == "REVIEW"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
