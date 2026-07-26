#!/usr/bin/env python3
"""Replay teleop_episode_v0 records through a deterministic data gate."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np


SIM_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SIM_ROOT.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_teleop_episode_v0 import validate_episode_file  # noqa: E402


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


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


def _safe_id(text: str, max_len: int = 96) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in text]
    collapsed = "_".join(part for part in "".join(chars).split("_") if part)
    return (collapsed[:max_len].strip("_") or "episode")


def _collect_manifest_episodes(manifest_path: Path) -> List[Path]:
    manifest = _read_json(manifest_path)
    episodes: List[Path] = []
    for entry in manifest.get("episodes", []) or []:
        if not isinstance(entry, dict):
            continue
        episode_path = entry.get("episode_path", "")
        if episode_path:
            episodes.append(Path(episode_path))
    return episodes


def _episode_paths_from_args(args: argparse.Namespace) -> List[Path]:
    paths: List[Path] = []
    if args.episode:
        paths.extend(args.episode)
    if args.manifest:
        paths.extend(_collect_manifest_episodes(args.manifest))
    resolved: List[Path] = []
    seen = set()
    for path in paths:
        item = path.expanduser().resolve()
        key = str(item).lower()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(item)
    return resolved


def _episode_arrays(frames: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    return {
        "timestamps": np.asarray([frame["timestamp_s"] for frame in frames], dtype=np.float32),
        "timestamp_ns": np.asarray([frame["timestamp_ns"] for frame in frames], dtype=np.int64),
        "source_frame_indices": np.asarray(
            [
                -1 if frame.get("source_frame_index") is None else int(frame.get("source_frame_index"))
                for frame in frames
            ],
            dtype=np.int64,
        ),
        "landmarks": np.asarray([frame["landmarks_21x3"] for frame in frames], dtype=np.float32),
        "palm_features": np.asarray([frame["palm_feature_76"] for frame in frames], dtype=np.float32),
        "open_close_features": np.asarray([frame["open_close_feature_35"] for frame in frames], dtype=np.float32),
        "backend_actions": np.asarray(
            [frame["backend_action_v0"]["values"] for frame in frames],
            dtype=np.float32,
        ),
        "quality_status": np.asarray(
            [str(frame.get("quality", {}).get("status", "unknown")) for frame in frames],
            dtype=object,
        ),
    }


def _write_replay_trace(path: Path, frames: List[Dict[str, Any]], validation_status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for frame in frames:
            item = {
                "frame_index": frame["frame_index"],
                "replay_time_s": frame["timestamp_s"],
                "timestamp_ns": frame["timestamp_ns"],
                "source_frame_index": frame.get("source_frame_index"),
                "quality_status": frame.get("quality", {}).get("status", "unknown"),
                "semantic_values": frame.get("semantic_action_v0", {}).get("values", {}),
                "backend_action_schema": frame.get("backend_action_v0", {}).get("action_schema", ""),
                "backend_action_dim": frame.get("backend_action_v0", {}).get("action_dim", 0),
                "backend_action_values": frame.get("backend_action_v0", {}).get("values", []),
                "episode_validation_status": validation_status,
            }
            handle.write(json.dumps(_json_ready(item), ensure_ascii=True) + "\n")


def _patch_episode_artifacts(episode_path: Path, replay_report_path: Path, replay_trace_path: Path, replay_arrays_path: Path) -> None:
    payload = _read_json(episode_path)
    artifacts = list(payload.get("artifacts", []) or [])
    new_items = [
        {"artifact_type": "replay_report", "path": str(replay_report_path), "status": "generated"},
        {"artifact_type": "replay_trace_jsonl", "path": str(replay_trace_path), "status": "generated"},
        {"artifact_type": "replay_arrays_npz", "path": str(replay_arrays_path), "status": "generated"},
    ]
    existing = {
        (str(item.get("artifact_type", "")), str(item.get("path", "")))
        for item in artifacts
        if isinstance(item, dict)
    }
    for item in new_items:
        key = (item["artifact_type"], item["path"])
        if key not in existing:
            artifacts.append(item)
    payload["artifacts"] = artifacts
    _write_json(episode_path, payload)


def _replay_one_episode(
    episode_path: Path,
    episode_output_root: Path,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    payload = _read_json(episode_path)
    episode_id = str(payload.get("episode_id", episode_path.stem))
    safe_episode_id = _safe_id(episode_id)
    out_dir = episode_output_root / safe_episode_id
    out_dir.mkdir(parents=True, exist_ok=True)

    validation = validate_episode_file(
        episode_path,
        max_timestamp_gap_s=args.max_timestamp_gap_s,
        max_action_abs=args.max_action_abs,
        max_saturation_fraction=args.max_saturation_fraction,
        max_action_step_abs=args.max_action_step_abs,
        max_review_frame_ratio=args.max_review_frame_ratio,
        min_detection_confidence=args.min_detection_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
    )
    frames = payload.get("frames", []) if isinstance(payload.get("frames"), list) else []
    arrays = _episode_arrays(frames) if frames else {
        "timestamps": np.asarray([], dtype=np.float32),
        "timestamp_ns": np.asarray([], dtype=np.int64),
        "source_frame_indices": np.asarray([], dtype=np.int64),
        "landmarks": np.asarray([], dtype=np.float32),
        "palm_features": np.asarray([], dtype=np.float32),
        "open_close_features": np.asarray([], dtype=np.float32),
        "backend_actions": np.asarray([], dtype=np.float32),
        "quality_status": np.asarray([], dtype=object),
    }

    replay_trace_path = out_dir / "replay_trace.jsonl"
    replay_arrays_path = out_dir / "replay_arrays.npz"
    replay_report_path = out_dir / "replay_report.json"
    validation_report_path = out_dir / "validation_report.json"

    _write_replay_trace(replay_trace_path, frames, validation["status"])
    np.savez_compressed(
        replay_arrays_path,
        **arrays,
        metadata=_json_ready(
            {
                "schema_version": "teleop_replay_arrays_v0",
                "episode_id": episode_id,
                "episode_path": str(episode_path),
                "validation_status": validation["status"],
            }
        ),
    )
    _write_json(validation_report_path, validation)

    status = validation["status"]
    replay_report = {
        "schema_version": "teleop_replay_report_v0",
        "created_at_utc": _utc_stamp(),
        "run_id": args.run_id,
        "episode_id": episode_id,
        "episode_path": str(episode_path),
        "output_dir": str(out_dir),
        "status": status,
        "replay_mode": "deterministic_data_replay",
        "frames_replayed": int(len(frames)),
        "duration_s": validation.get("metrics", {}).get("timestamps", {}).get("duration_s", 0.0),
        "backend_action": validation.get("metrics", {}).get("backend_action", {}),
        "quality": validation.get("metrics", {}).get("quality", {}),
        "reject_reasons": validation.get("reject_reasons", []),
        "review_reasons": validation.get("review_reasons", []),
        "paths": {
            "replay_trace_jsonl": str(replay_trace_path),
            "replay_arrays_npz": str(replay_arrays_path),
            "validation_report": str(validation_report_path),
            "replay_report": str(replay_report_path),
        },
        "not_claimed": [
            "physics_simulation",
            "task_success",
            "policy_promotion",
            "hardware_readiness",
        ],
    }
    _write_json(replay_report_path, replay_report)
    if args.patch_episode_artifacts:
        _patch_episode_artifacts(episode_path, replay_report_path, replay_trace_path, replay_arrays_path)

    return {
        "episode_id": episode_id,
        "episode_path": str(episode_path),
        "status": status,
        "frames_replayed": int(len(frames)),
        "duration_s": replay_report["duration_s"],
        "reject_reasons": replay_report["reject_reasons"],
        "review_reasons": replay_report["review_reasons"],
        "replay_report_path": str(replay_report_path),
        "validation_report_path": str(validation_report_path),
        "replay_trace_path": str(replay_trace_path),
        "replay_arrays_path": str(replay_arrays_path),
        "metrics": {
            "backend_action": replay_report["backend_action"],
            "quality": replay_report["quality"],
            "timestamps": validation.get("metrics", {}).get("timestamps", {}),
        },
    }


def _write_run_index_csv(path: Path, entries: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "episode_id",
        "status",
        "frames_replayed",
        "duration_s",
        "episode_path",
        "replay_report_path",
        "reject_reasons",
        "review_reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "episode_id": entry.get("episode_id", ""),
                    "status": entry.get("status", ""),
                    "frames_replayed": entry.get("frames_replayed", ""),
                    "duration_s": entry.get("duration_s", ""),
                    "episode_path": entry.get("episode_path", ""),
                    "replay_report_path": entry.get("replay_report_path", ""),
                    "reject_reasons": ";".join(entry.get("reject_reasons", []) or []),
                    "review_reasons": ";".join(entry.get("review_reasons", []) or []),
                }
            )


def _write_run_summary_md(path: Path, run_manifest: Dict[str, Any]) -> None:
    summary = run_manifest["summary"]
    lines = [
        f"# Teleop Replay Summary: {run_manifest['run_id']}",
        "",
        f"Created: {run_manifest['created_at_utc']}",
        "",
        "## Status",
        "",
        f"- run status: `{run_manifest['status']}`",
        f"- episodes total: {summary['episodes_total']}",
        f"- frames replayed: {summary['frames_replayed_total']}",
        f"- status counts: `{json.dumps(summary['status_counts'], sort_keys=True)}`",
        f"- review reasons: `{json.dumps(summary['review_reason_counts'], sort_keys=True)}`",
        f"- reject reasons: `{json.dumps(summary['reject_reason_counts'], sort_keys=True)}`",
        "",
        "## Boundary",
        "",
        "This replay is deterministic data playback and validation. It does not",
        "claim physics execution, task success, model promotion, or hardware readiness.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _build_run_manifest(args: argparse.Namespace, run_root: Path, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    status_counts = Counter(entry["status"] for entry in entries)
    review_reasons = Counter()
    reject_reasons = Counter()
    for entry in entries:
        for reason in entry.get("review_reasons", []) or []:
            review_reasons[str(reason)] += 1
        for reason in entry.get("reject_reasons", []) or []:
            reject_reasons[str(reason)] += 1
    if status_counts.get("REJECT", 0):
        status = "REJECT"
    elif status_counts.get("REVIEW", 0):
        status = "REVIEW"
    else:
        status = "PASS"
    return {
        "schema_version": "teleop_replay_manifest_v0",
        "run_id": args.run_id,
        "created_at_utc": _utc_stamp(),
        "status": status,
        "output_dir": str(run_root),
        "source_manifest": str(args.manifest) if args.manifest else "",
        "replay_mode": "deterministic_data_replay",
        "thresholds": {
            "max_timestamp_gap_s": float(args.max_timestamp_gap_s),
            "max_action_abs": float(args.max_action_abs),
            "max_saturation_fraction": float(args.max_saturation_fraction),
            "max_action_step_abs": float(args.max_action_step_abs),
            "max_review_frame_ratio": float(args.max_review_frame_ratio),
            "min_detection_confidence": float(args.min_detection_confidence),
            "min_tracking_confidence": float(args.min_tracking_confidence),
        },
        "summary": {
            "episodes_total": len(entries),
            "frames_replayed_total": int(sum(int(entry.get("frames_replayed", 0) or 0) for entry in entries)),
            "status_counts": dict(status_counts),
            "review_reason_counts": dict(review_reasons),
            "reject_reason_counts": dict(reject_reasons),
        },
        "episodes": entries,
        "not_claimed": [
            "train_ready_dataset",
            "physics_simulation",
            "closed_loop_policy_success",
            "hardware_runtime",
        ],
    }


def _write_back_manifest(manifest_path: Path, run_manifest: Dict[str, Any]) -> None:
    manifest = _read_json(manifest_path)
    by_path = {
        str(entry.get("episode_path", "")).lower(): entry
        for entry in manifest.get("episodes", []) or []
        if isinstance(entry, dict)
    }
    by_id = {
        str(entry.get("episode_id", "")): entry
        for entry in manifest.get("episodes", []) or []
        if isinstance(entry, dict)
    }
    for replay_entry in run_manifest.get("episodes", []) or []:
        entry = by_path.get(str(replay_entry.get("episode_path", "")).lower())
        if entry is None:
            entry = by_id.get(str(replay_entry.get("episode_id", "")))
        if entry is None:
            continue
        replay_status = replay_entry.get("status", "REJECT")
        entry["replay_validation"] = {
            "schema_version": "teleop_replay_validation_v0",
            "run_id": run_manifest["run_id"],
            "status": replay_status,
            "replay_report_path": replay_entry.get("replay_report_path", ""),
            "validation_report_path": replay_entry.get("validation_report_path", ""),
            "replay_trace_path": replay_entry.get("replay_trace_path", ""),
            "replay_arrays_path": replay_entry.get("replay_arrays_path", ""),
            "frames_replayed": replay_entry.get("frames_replayed", 0),
            "review_reasons": replay_entry.get("review_reasons", []),
            "reject_reasons": replay_entry.get("reject_reasons", []),
        }
        entry["replay_eligible"] = replay_status in {"PASS", "REVIEW"}

    manifest["replay_validation"] = {
        "schema_version": "teleop_replay_manifest_link_v0",
        "updated_at_utc": _utc_stamp(),
        "run_id": run_manifest["run_id"],
        "status": run_manifest["status"],
        "replay_manifest_path": str(Path(run_manifest["output_dir"]) / "replay_manifest.json"),
        "summary": run_manifest["summary"],
    }
    _write_json(manifest_path, manifest)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay teleop episodes through a deterministic data gate")
    parser.add_argument("--episode", action="append", type=Path, default=[])
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "teleop_replay",
    )
    parser.add_argument("--run-id", default="")
    parser.add_argument("--write-manifest", action="store_true", help="Write replay status back to --manifest")
    parser.add_argument("--patch-episode-artifacts", action=argparse.BooleanOptionalAction, default=True)
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
    if not args.episode and not args.manifest:
        raise SystemExit("Provide at least one --episode or --manifest")
    args.run_id = _safe_id(args.run_id or f"teleop_replay_{_run_id()}")
    if args.write_manifest and not args.manifest:
        raise SystemExit("--write-manifest requires --manifest")

    episode_paths = _episode_paths_from_args(args)
    if not episode_paths:
        raise SystemExit("No episode paths found")
    for episode_path in episode_paths:
        if not episode_path.exists():
            raise FileNotFoundError(f"Episode not found: {episode_path}")

    run_root = args.output_root.expanduser().resolve() / args.run_id
    episode_output_root = run_root / "episodes"
    entries = [_replay_one_episode(path, episode_output_root, args) for path in episode_paths]
    run_manifest = _build_run_manifest(args, run_root, entries)

    replay_manifest_path = run_root / "replay_manifest.json"
    replay_index_path = run_root / "replay_index.csv"
    replay_summary_path = run_root / "replay_summary.md"
    _write_json(replay_manifest_path, run_manifest)
    _write_run_index_csv(replay_index_path, entries)
    _write_run_summary_md(replay_summary_path, run_manifest)

    if args.write_manifest and args.manifest:
        _write_back_manifest(args.manifest.expanduser().resolve(), run_manifest)

    print(
        json.dumps(
            _json_ready(
                {
                    "run_id": args.run_id,
                    "status": run_manifest["status"],
                    "manifest": replay_manifest_path,
                    "summary": run_manifest["summary"],
                }
            ),
            indent=2,
            ensure_ascii=True,
        )
    )
    if run_manifest["status"] == "REJECT" or (args.fail_on_review and run_manifest["status"] == "REVIEW"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
