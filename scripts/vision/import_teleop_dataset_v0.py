#!/usr/bin/env python3
"""Batch import teleop hand sources into teleop_episode_v0.

Phase 3 importer for the live/offline teleop path. It discovers videos,
landmark traces, and simple landmark JSON files, converts each source through
the Phase 2 runner, then writes a dataset manifest with episode-level QA,
splits, validation status, and provenance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np


SIM_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SIM_ROOT.parent
RUNNER_PATH = SIM_ROOT / "scripts" / "vision" / "run_live_hand_teleop_v0.py"
VALIDATOR_PATH = PROJECT_ROOT / "tools" / "validate_teleop_dataset_contract_v0.py"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
TRACE_EXTENSIONS = {".npz"}
JSON_EXTENSIONS = {".json"}
SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | TRACE_EXTENSIONS | JSON_EXTENSIONS


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


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_id(text: str, max_len: int = 72) -> str:
    lowered = text.lower()
    chars = [ch if ch.isalnum() else "_" for ch in lowered]
    collapsed = "_".join(part for part in "".join(chars).split("_") if part)
    if not collapsed:
        collapsed = "source"
    return collapsed[:max_len].strip("_") or "source"


def _short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _source_stat(path: Path, hash_source: bool) -> Dict[str, Any]:
    stat = path.stat()
    payload: Dict[str, Any] = {
        "size_bytes": int(stat.st_size),
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if hash_source:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        payload["sha256"] = digest.hexdigest()
    return payload


def _iter_sources(paths: Sequence[Path], recursive: bool) -> List[Path]:
    found: List[Path] = []
    seen = set()
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Input path does not exist: {path}")
        if path.is_file():
            candidates = [path]
        elif recursive:
            candidates = [item for item in path.rglob("*") if item.is_file()]
        else:
            candidates = [item for item in path.iterdir() if item.is_file()]
        for candidate in candidates:
            if candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            resolved = candidate.resolve()
            key = str(resolved).lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(resolved)
    found.sort(key=lambda item: str(item).lower())
    return found


def _npz_trace_info(path: Path) -> Tuple[bool, Dict[str, Any]]:
    try:
        payload = np.load(path, allow_pickle=True)
    except Exception as exc:  # noqa: BLE001
        return False, {"reason": "npz_load_failed", "error": str(exc)}
    keys = sorted(payload.files)
    if "landmarks" not in payload:
        return False, {"reason": "npz_missing_landmarks", "keys": keys}
    landmarks = np.asarray(payload["landmarks"])
    if landmarks.ndim != 3 or landmarks.shape[1:] != (21, 3):
        return False, {
            "reason": "npz_landmarks_shape_invalid",
            "shape": list(landmarks.shape),
            "keys": keys,
        }
    info = {
        "keys": keys,
        "landmark_shape": list(landmarks.shape),
        "frames_available": int(landmarks.shape[0]),
        "has_timestamps": bool("timestamps" in payload),
        "has_source_frame_indices": bool("source_frame_indices" in payload),
    }
    return True, info


def _json_source_kind(path: Path) -> Tuple[str, Dict[str, Any]]:
    try:
        payload = _read_json(path)
    except Exception as exc:  # noqa: BLE001
        return "unsupported_json", {"reason": "json_load_failed", "error": str(exc)}
    if payload.get("schema_version") == "teleop_episode_v0":
        return "existing_episode_json", {
            "episode_id": payload.get("episode_id", path.stem),
            "frames_available": len(payload.get("frames", [])),
        }
    if "landmarks" in payload:
        landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
        if landmarks.ndim == 3 and landmarks.shape[1:] == (21, 3):
            return "landmark_json", {"frames_available": int(landmarks.shape[0])}
        return "unsupported_json", {
            "reason": "json_landmarks_shape_invalid",
            "shape": list(landmarks.shape),
        }
    if "frames" in payload and isinstance(payload["frames"], list):
        landmarks = [
            frame.get("landmarks_21x3")
            for frame in payload["frames"]
            if isinstance(frame, dict) and frame.get("landmarks_21x3") is not None
        ]
        if landmarks:
            arr = np.asarray(landmarks, dtype=np.float32)
            if arr.ndim == 3 and arr.shape[1:] == (21, 3):
                return "landmark_json", {"frames_available": int(arr.shape[0])}
        return "unsupported_json", {"reason": "json_frames_without_landmarks_21x3"}
    return "unsupported_json", {"reason": "json_unknown_layout"}


def _source_kind(path: Path) -> Tuple[str, Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return "video_file", {"extension": suffix}
    if suffix in TRACE_EXTENSIONS:
        ok, info = _npz_trace_info(path)
        return ("trace_npz" if ok else "unsupported_npz", info)
    if suffix in JSON_EXTENSIONS:
        kind, info = _json_source_kind(path)
        info["extension"] = suffix
        return kind, info
    return "unsupported", {"extension": suffix}


def _landmark_json_to_npz(source_path: Path, output_path: Path) -> Dict[str, Any]:
    payload = _read_json(source_path)
    if "landmarks" in payload:
        landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
        timestamps = np.asarray(
            payload.get("timestamps", np.arange(landmarks.shape[0], dtype=np.float32) / 30.0),
            dtype=np.float32,
        )
        source_frame_indices = np.asarray(
            payload.get("source_frame_indices", np.arange(landmarks.shape[0], dtype=np.float32)),
            dtype=np.float32,
        )
    else:
        frames = payload.get("frames", [])
        landmarks = np.asarray([frame["landmarks_21x3"] for frame in frames], dtype=np.float32)
        timestamps = np.asarray(
            [frame.get("timestamp_s", idx / 30.0) for idx, frame in enumerate(frames)],
            dtype=np.float32,
        )
        source_frame_indices = np.asarray(
            [frame.get("source_frame_index", idx) or idx for idx, frame in enumerate(frames)],
            dtype=np.float32,
        )
    if landmarks.ndim != 3 or landmarks.shape[1:] != (21, 3):
        raise ValueError(f"Landmark JSON shape must be [N,21,3], got {landmarks.shape}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        landmarks=landmarks,
        timestamps=timestamps,
        source_frame_indices=source_frame_indices,
    )
    return {
        "converted_trace_path": str(output_path),
        "frames_available": int(landmarks.shape[0]),
    }


def _validate_episode(episode_path: Path) -> Dict[str, Any]:
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    import validate_teleop_dataset_contract_v0 as validator

    return validator.validate_file(
        sample_path=episode_path,
        schema_path=PROJECT_ROOT / "docs" / "teleop_dataset_contract_v0.schema.json",
    )


def _run_subprocess(command: Sequence[str]) -> Dict[str, Any]:
    started = time.time()
    result = subprocess.run(
        list(command),
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.time() - started
    return {
        "command": list(command),
        "returncode": int(result.returncode),
        "elapsed_seconds": float(elapsed),
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def _quality_ratio(report: Dict[str, Any], status_name: str) -> float:
    counts = report.get("quality_counts", {}) or {}
    total = sum(int(value) for value in counts.values()) or int(report.get("frames_detected", 0) or 0)
    if total <= 0:
        return 0.0
    return float(int(counts.get(status_name, 0)) / total)


def _classify_episode(
    report: Dict[str, Any],
    validation: Dict[str, Any] | None,
    min_detection_coverage: float,
    min_pass_quality_ratio: float,
) -> Tuple[str, List[str], bool]:
    reasons: List[str] = []
    frames_detected = int(report.get("frames_detected", 0) or 0)
    if frames_detected <= 0:
        reasons.append("no_frames_detected")
    if validation is None or validation.get("status") != "PASS":
        reasons.append("contract_validation_failed")
    detection_coverage = float(report.get("detection_coverage", 0.0) or 0.0)
    if frames_detected > 0 and detection_coverage < float(min_detection_coverage):
        reasons.append("low_detection_coverage")
    pass_quality_ratio = _quality_ratio(report, "pass")
    if frames_detected > 0 and pass_quality_ratio < float(min_pass_quality_ratio):
        reasons.append("low_pass_quality_ratio")
    action_dims = report.get("backend_action_dims", [])
    if action_dims and len(action_dims) != 1:
        reasons.append("inconsistent_backend_action_dim")
    if "no_frames_detected" in reasons or "contract_validation_failed" in reasons:
        return "reject", reasons, False
    if reasons:
        return "review", reasons, True
    return "pass", [], True


def _assign_splits(
    entries: List[Dict[str, Any]],
    train_ratio: float,
    val_ratio: float,
) -> None:
    pass_entries = [entry for entry in entries if entry.get("status") == "pass"]
    count = len(pass_entries)
    if count <= 0:
        for entry in entries:
            if entry.get("status") == "review":
                entry["split"] = "review"
            elif entry.get("status") == "reject":
                entry["split"] = "reject"
        return

    train_count = max(1, int(round(count * train_ratio)))
    val_count = int(round(count * val_ratio))
    if train_count + val_count > count:
        val_count = max(0, count - train_count)
    heldout_count = max(0, count - train_count - val_count)
    if count >= 3 and heldout_count == 0 and (1.0 - train_ratio - val_ratio) > 0:
        heldout_count = 1
        if val_count > 0:
            val_count -= 1
        else:
            train_count = max(1, train_count - 1)

    for idx, entry in enumerate(pass_entries):
        if idx < train_count:
            entry["split"] = "train"
        elif idx < train_count + val_count:
            entry["split"] = "val"
        else:
            entry["split"] = "heldout"

    for entry in entries:
        if entry.get("status") == "review":
            entry["split"] = "review"
        elif entry.get("status") == "reject":
            entry["split"] = "reject"


def _patch_episode(
    episode_path: Path,
    dataset_id: str,
    split: str,
    status: str,
    failure_reasons: List[str],
    manifest_path: Path,
) -> Dict[str, Any]:
    episode = _read_json(episode_path)
    episode["dataset_id"] = dataset_id
    labels = episode.setdefault("episode_labels", {})
    labels["split"] = split
    labels["status"] = status
    labels["terminal_reason"] = "completed" if status == "pass" else ("needs_review" if status == "review" else "invalid_source")
    labels["failure_reasons"] = list(failure_reasons)
    artifacts = list(episode.get("artifacts", []))
    manifest_artifact = {
        "artifact_type": "dataset_manifest",
        "path": str(manifest_path),
        "status": "generated",
    }
    if not any(item.get("artifact_type") == "dataset_manifest" for item in artifacts if isinstance(item, dict)):
        artifacts.append(manifest_artifact)
    episode["artifacts"] = artifacts
    _write_json(episode_path, episode)
    return _validate_episode(episode_path)


def _copy_existing_episode_json(
    source_path: Path,
    episode_dir: Path,
    episode_id: str,
    dataset_id: str,
    manifest_path: Path,
) -> Tuple[Path, Path, Dict[str, Any]]:
    episode_dir.mkdir(parents=True, exist_ok=True)
    episode_path = episode_dir / "teleop_episode_v0.json"
    shutil.copy2(source_path, episode_path)
    validation = _patch_episode(
        episode_path=episode_path,
        dataset_id=dataset_id,
        split="unassigned",
        status="review",
        failure_reasons=["existing_episode_needs_manifest_review"],
        manifest_path=manifest_path,
    )
    report = {
        "session_id": episode_id,
        "source_type": "existing_episode_json",
        "source_uri": str(source_path),
        "output_dir": str(episode_dir),
        "frames_detected": int(validation.get("frames", 0) or 0),
        "source_frames_read": int(validation.get("frames", 0) or 0),
        "detection_coverage": 1.0 if int(validation.get("frames", 0) or 0) else 0.0,
        "quality_counts": {"pass": 0, "review": int(validation.get("frames", 0) or 0), "reject": 0},
        "backend_action_dims": [int(validation.get("first_backend_action_dim", 0) or 0)],
        "overlays_written": 0,
        "dependency_status": {"existing_contract_episode": True},
        "status": "PASS" if validation.get("status") == "PASS" else "FAIL",
        "contract_validation": validation,
    }
    report_path = episode_dir / "session_report.json"
    _write_json(report_path, report)
    return episode_path, report_path, report


def _run_converter_for_source(
    args: argparse.Namespace,
    source_path: Path,
    source_kind: str,
    episode_id: str,
    dataset_root: Path,
    manifest_path: Path,
) -> Dict[str, Any]:
    episode_output_root = dataset_root / "episodes"
    episode_dir = episode_output_root / episode_id
    report_path = episode_dir / "session_report.json"
    episode_path = episode_dir / "teleop_episode_v0.json"

    if source_kind == "existing_episode_json":
        copied_episode, copied_report, report = _copy_existing_episode_json(
            source_path=source_path,
            episode_dir=episode_dir,
            episode_id=episode_id,
            dataset_id=args.dataset_id,
            manifest_path=manifest_path,
        )
        return {
            "episode_path": copied_episode,
            "report_path": copied_report,
            "report": report,
            "converter_result": {"returncode": 0, "command": ["copy-existing-episode-json"]},
        }

    input_path = source_path
    converted_from_json: Dict[str, Any] | None = None
    if source_kind == "landmark_json":
        input_path = dataset_root / "source_cache" / f"{episode_id}_landmarks.npz"
        converted_from_json = _landmark_json_to_npz(source_path, input_path)

    command = [
        sys.executable,
        str(RUNNER_PATH),
        "--output-root",
        str(episode_output_root),
        "--session-id",
        episode_id,
        "--operator-id",
        args.operator_id,
        "--skill-id",
        args.skill_id,
        "--phase-id",
        args.phase_id,
        "--backend",
        args.backend,
        "--duration-sec",
        str(args.duration_sec),
        "--max-source-frames",
        str(args.max_source_frames),
        "--max-detected-frames",
        str(args.max_detected_frames),
        "--overlay-stride",
        str(args.overlay_stride),
        "--headless",
    ]
    if args.save_overlays:
        command.append("--save-overlays")
    if args.mirror:
        command.append("--mirror")
    if args.mirror_x:
        command.append("--mirror-x")
    if args.hand_landmarker_model:
        command.extend(["--hand-landmarker-model", args.hand_landmarker_model])

    if source_kind == "video_file":
        command.extend(["--input-video", str(input_path)])
    elif source_kind in {"trace_npz", "landmark_json"}:
        command.extend(["--input-trace", str(input_path)])
    else:
        raise ValueError(f"Unsupported source kind for conversion: {source_kind}")

    result = _run_subprocess(command)
    report: Dict[str, Any] = {}
    if report_path.exists():
        report = _read_json(report_path)
    if converted_from_json is not None:
        report.setdefault("source_conversion", converted_from_json)
        _write_json(report_path, report)
    return {
        "episode_path": episode_path if episode_path.exists() else None,
        "report_path": report_path if report_path.exists() else None,
        "report": report,
        "converter_result": result,
    }


def _build_manifest(
    args: argparse.Namespace,
    dataset_root: Path,
    source_paths: List[Path],
    entries: List[Dict[str, Any]],
    started_at: float,
) -> Dict[str, Any]:
    status_counts = Counter(str(entry.get("status", "unknown")) for entry in entries)
    split_counts = Counter(str(entry.get("split", "unknown")) for entry in entries)
    source_kind_counts = Counter(str(entry.get("source_kind", "unknown")) for entry in entries)
    failure_counts: Counter[str] = Counter()
    frame_total = 0
    replay_eligible = 0
    for entry in entries:
        for reason in entry.get("failure_reasons", []) or []:
            failure_counts[str(reason)] += 1
        frame_total += int(entry.get("frames_detected", 0) or 0)
        if entry.get("contract_validation", {}).get("status") == "PASS" and entry.get("status") in {"pass", "review"}:
            replay_eligible += 1
    return {
        "schema_version": "teleop_dataset_manifest_v0",
        "dataset_id": args.dataset_id,
        "created_at_utc": _utc_stamp(),
        "status": "PASS" if status_counts.get("reject", 0) == 0 else "REVIEW_WITH_REJECTS",
        "classification": "generated",
        "output_dir": str(dataset_root),
        "source_roots": [str(item) for item in args.input_root],
        "import_config": {
            "recursive": bool(args.recursive),
            "max_sources": int(args.max_sources),
            "max_source_frames": int(args.max_source_frames),
            "max_detected_frames": int(args.max_detected_frames),
            "duration_sec": float(args.duration_sec),
            "backend": args.backend,
            "skill_id": args.skill_id,
            "phase_id": args.phase_id,
            "min_detection_coverage": float(args.min_detection_coverage),
            "min_pass_quality_ratio": float(args.min_pass_quality_ratio),
            "train_ratio": float(args.train_ratio),
            "val_ratio": float(args.val_ratio),
            "heldout_ratio": float(max(0.0, 1.0 - args.train_ratio - args.val_ratio)),
            "hash_source": bool(args.hash_source),
        },
        "discovery": {
            "sources_discovered": len(source_paths),
            "sources_attempted": len(entries),
            "source_kind_counts": dict(source_kind_counts),
        },
        "summary": {
            "episodes_total": len(entries),
            "status_counts": dict(status_counts),
            "split_counts": dict(split_counts),
            "frames_total": int(frame_total),
            "replay_eligible_episodes": int(replay_eligible),
            "failure_reason_counts": dict(failure_counts),
            "wall_time_seconds": float(time.time() - started_at),
        },
        "episodes": entries,
        "notes": [
            "Generated by simulations/scripts/vision/import_teleop_dataset_v0.py.",
            "pass/review episodes are contract-valid but not automatically train-ready.",
            "review episodes require replay or human QA before model-training inclusion.",
        ],
        "not_claimed": [
            "train-ready dataset",
            "camera calibration",
            "object-aware labels",
            "final tendon-hand action mapping",
            "hardware runtime integration",
        ],
    }


def _write_episode_index_csv(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "episode_id",
        "source_kind",
        "status",
        "split",
        "frames_detected",
        "detection_coverage",
        "contract_status",
        "source_uri",
        "episode_path",
        "failure_reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "episode_id": entry.get("episode_id", ""),
                    "source_kind": entry.get("source_kind", ""),
                    "status": entry.get("status", ""),
                    "split": entry.get("split", ""),
                    "frames_detected": entry.get("frames_detected", ""),
                    "detection_coverage": entry.get("detection_coverage", ""),
                    "contract_status": entry.get("contract_validation", {}).get("status", ""),
                    "source_uri": entry.get("source_uri", ""),
                    "episode_path": entry.get("episode_path", ""),
                    "failure_reasons": ";".join(entry.get("failure_reasons", []) or []),
                }
            )


def _write_summary_md(path: Path, manifest: Dict[str, Any]) -> None:
    summary = manifest["summary"]
    discovery = manifest["discovery"]
    lines = [
        f"# Teleop Dataset Import Summary: {manifest['dataset_id']}",
        "",
        f"Created: {manifest['created_at_utc']}",
        "",
        "## Status",
        "",
        f"- dataset status: `{manifest['status']}`",
        f"- sources discovered: {discovery['sources_discovered']}",
        f"- episodes total: {summary['episodes_total']}",
        f"- frames total: {summary['frames_total']}",
        f"- replay eligible episodes: {summary['replay_eligible_episodes']}",
        "",
        "## Counts",
        "",
        f"- status counts: `{json.dumps(summary['status_counts'], sort_keys=True)}`",
        f"- split counts: `{json.dumps(summary['split_counts'], sort_keys=True)}`",
        f"- source kinds: `{json.dumps(discovery['source_kind_counts'], sort_keys=True)}`",
        f"- failure reasons: `{json.dumps(summary['failure_reason_counts'], sort_keys=True)}`",
        "",
        "## Boundary",
        "",
        "This import is contract-valid data plumbing. It does not by itself make",
        "the imported episodes train-ready or hardware-ready.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch import teleop sources into teleop_episode_v0")
    parser.add_argument("--input-root", action="append", required=True, type=Path, help="Input file or directory; repeatable")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "teleop_datasets",
        help="Generated dataset artifact root",
    )
    parser.add_argument("--dataset-id", default="", help="Dataset id; default uses timestamp")
    parser.add_argument("--operator-id", default="external_dataset_operator")
    parser.add_argument("--skill-id", default="teleop_hand_open_close")
    parser.add_argument("--phase-id", default="capture")
    parser.add_argument("--backend", choices=["shadow_diagnostic", "none"], default="shadow_diagnostic")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-sources", type=int, default=0)
    parser.add_argument("--duration-sec", type=float, default=0.0, help="Forwarded to video runner; 0 disables wall-time cap")
    parser.add_argument("--max-source-frames", type=int, default=0)
    parser.add_argument("--max-detected-frames", type=int, default=0)
    parser.add_argument("--min-detection-coverage", type=float, default=0.2)
    parser.add_argument("--min-pass-quality-ratio", type=float, default=0.6)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--save-overlays", action="store_true")
    parser.add_argument("--overlay-stride", type=int, default=30)
    parser.add_argument("--mirror", action="store_true")
    parser.add_argument("--mirror-x", action="store_true")
    parser.add_argument("--hash-source", action="store_true", help="Compute source sha256; slower on large datasets")
    parser.add_argument(
        "--hand-landmarker-model",
        default=os.environ.get("MEDIAPIPE_HAND_LANDMARKER_MODEL", ""),
    )
    parser.add_argument("--dry-run", action="store_true", help="Only discover and classify source files")
    parser.add_argument("--fail-fast", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    if args.train_ratio < 0 or args.val_ratio < 0 or args.train_ratio + args.val_ratio > 1.0:
        raise SystemExit("--train-ratio and --val-ratio must be non-negative and sum to <= 1")

    args.input_root = [path.expanduser().resolve() for path in args.input_root]
    dataset_id = args.dataset_id or f"teleop_dataset_{_run_id()}"
    args.dataset_id = _safe_id(dataset_id, max_len=80)
    dataset_root = args.output_root.expanduser().resolve() / args.dataset_id
    dataset_root.mkdir(parents=True, exist_ok=True)
    manifest_path = dataset_root / "dataset_manifest.json"
    started = time.time()

    source_paths = _iter_sources(args.input_root, recursive=bool(args.recursive))
    if args.max_sources:
        source_paths = source_paths[: int(args.max_sources)]

    entries: List[Dict[str, Any]] = []
    for idx, source_path in enumerate(source_paths):
        source_kind, source_info = _source_kind(source_path)
        episode_id = f"{idx:04d}_{_safe_id(source_path.stem, max_len=48)}_{_short_hash(str(source_path))}"
        entry: Dict[str, Any] = {
            "episode_id": episode_id,
            "source_uri": str(source_path),
            "source_kind": source_kind,
            "source_info": source_info,
            "source_stat": _source_stat(source_path, hash_source=bool(args.hash_source)),
            "status": "reject" if source_kind.startswith("unsupported") else "discovered",
            "split": "reject" if source_kind.startswith("unsupported") else "unassigned",
            "failure_reasons": [],
            "episode_path": "",
            "report_path": "",
            "frames_detected": 0,
            "detection_coverage": 0.0,
            "contract_validation": {},
            "converter_result": {},
        }
        if source_kind.startswith("unsupported"):
            entry["failure_reasons"] = [str(source_info.get("reason", "unsupported_source"))]
            entries.append(entry)
            if args.fail_fast:
                break
            continue
        if args.dry_run:
            entry["status"] = "discovered"
            entries.append(entry)
            continue

        try:
            result = _run_converter_for_source(
                args=args,
                source_path=source_path,
                source_kind=source_kind,
                episode_id=episode_id,
                dataset_root=dataset_root,
                manifest_path=manifest_path,
            )
            report = result.get("report", {}) or {}
            converter_result = result.get("converter_result", {}) or {}
            episode_path = result.get("episode_path")
            report_path = result.get("report_path")
            validation: Dict[str, Any] | None = None
            if episode_path and Path(episode_path).exists():
                validation = _validate_episode(Path(episode_path))
            status, reasons, replay_eligible = _classify_episode(
                report=report,
                validation=validation,
                min_detection_coverage=args.min_detection_coverage,
                min_pass_quality_ratio=args.min_pass_quality_ratio,
            )
            if int(converter_result.get("returncode", 1)) != 0:
                status = "reject"
                replay_eligible = False
                if "converter_returncode_nonzero" not in reasons:
                    reasons.append("converter_returncode_nonzero")
            entry.update(
                {
                    "status": status,
                    "split": "unassigned",
                    "failure_reasons": reasons,
                    "replay_eligible": bool(replay_eligible),
                    "episode_path": str(episode_path) if episode_path else "",
                    "report_path": str(report_path) if report_path else "",
                    "frames_detected": int(report.get("frames_detected", validation.get("frames", 0) if validation else 0) or 0),
                    "source_frames_read": int(report.get("source_frames_read", 0) or 0),
                    "detection_coverage": float(report.get("detection_coverage", 0.0) or 0.0),
                    "quality_counts": report.get("quality_counts", {}),
                    "backend_action_dims": report.get("backend_action_dims", []),
                    "contract_validation": validation or {},
                    "converter_result": converter_result,
                }
            )
        except Exception as exc:  # noqa: BLE001
            entry.update(
                {
                    "status": "reject",
                    "split": "reject",
                    "failure_reasons": ["import_exception"],
                    "exception": str(exc),
                    "replay_eligible": False,
                }
            )
            entries.append(entry)
            if args.fail_fast:
                raise
            continue
        entries.append(entry)

    if not args.dry_run:
        _assign_splits(entries, train_ratio=args.train_ratio, val_ratio=args.val_ratio)
        for entry in entries:
            episode_path_raw = entry.get("episode_path", "")
            if not episode_path_raw:
                continue
            episode_path = Path(episode_path_raw)
            if not episode_path.exists():
                continue
            validation = _patch_episode(
                episode_path=episode_path,
                dataset_id=args.dataset_id,
                split=str(entry.get("split", "unassigned")),
                status=str(entry.get("status", "review")),
                failure_reasons=list(entry.get("failure_reasons", []) or []),
                manifest_path=manifest_path,
            )
            entry["contract_validation"] = validation
            report_path_raw = entry.get("report_path", "")
            if report_path_raw and Path(report_path_raw).exists():
                report = _read_json(Path(report_path_raw))
                report["dataset_import"] = {
                    "dataset_id": args.dataset_id,
                    "episode_id": entry.get("episode_id"),
                    "split": entry.get("split"),
                    "status": entry.get("status"),
                    "failure_reasons": entry.get("failure_reasons", []),
                    "contract_validation_after_manifest_patch": validation,
                }
                _write_json(Path(report_path_raw), report)

    manifest = _build_manifest(
        args=args,
        dataset_root=dataset_root,
        source_paths=source_paths,
        entries=entries,
        started_at=started,
    )
    _write_json(manifest_path, manifest)
    _write_episode_index_csv(dataset_root / "episode_index.csv", entries)
    _write_summary_md(dataset_root / "dataset_summary.md", manifest)

    print(
        json.dumps(
            _json_ready(
                {
                    "dataset_id": args.dataset_id,
                    "manifest": manifest_path,
                    "summary": manifest["summary"],
                    "status": manifest["status"],
                }
            ),
            indent=2,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
