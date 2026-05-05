#!/usr/bin/env python3
"""Build a screening manifest for local hand open/close videos."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from vision.hand_open_close import (
    estimate_active_segment,
    json_ready,
    open_close_features_from_landmarks,
    summarize_open_close_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _video_info(path: Path) -> Dict[str, Any]:
    info = {
        "path": str(path),
        "bytes": int(path.stat().st_size) if path.exists() else 0,
        "frame_count": None,
        "fps": None,
        "duration_seconds": None,
    }
    try:
        import cv2
    except ImportError:
        return info
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return info
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        info["frame_count"] = frame_count
        info["fps"] = fps
        info["duration_seconds"] = float(frame_count / fps) if frame_count and fps > 1e-6 else None
    finally:
        cap.release()
    return info


def _load_json(path: Path) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _video_files(video_dir: Path) -> List[Path]:
    extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".ogv"}
    return sorted(
        [path for path in video_dir.rglob("*") if path.is_file() and path.suffix.lower() in extensions],
        key=lambda item: item.name.lower(),
    )


def _status_from_reasons(reasons: List[str]) -> str:
    return "usable" if not reasons else "review"


def build_item(
    video: Path,
    trace_dir: Path,
    retarget_dir: Path,
    reports_dir: Path,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    stem = video.stem
    trace_path = trace_dir / f"{stem}_palm_trace.npz"
    retarget_path = retarget_dir / f"{stem}_shadow_retarget.npz"
    rollout_path = retarget_dir / f"{stem}_shadow_retarget_replay.npz"
    trace_report = reports_dir / f"{stem}_palm_trace.json"
    retarget_report = reports_dir / f"{stem}_shadow_retarget.json"
    video_info = _video_info(video)
    reasons: List[str] = []

    item: Dict[str, Any] = {
        "video": str(video),
        "video_name": video.name,
        "trace": str(trace_path),
        "retarget": str(retarget_path),
        "rollout": str(rollout_path) if rollout_path.exists() else "",
        "trace_report": str(trace_report) if trace_report.exists() else "",
        "retarget_report": str(retarget_report) if retarget_report.exists() else "",
        "video_info": video_info,
    }

    if not trace_path.exists():
        item["status"] = "missing_trace"
        item["review_reasons"] = ["missing_trace"]
        return item

    payload = np.load(trace_path, allow_pickle=True)
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    timestamps = (
        np.asarray(payload["timestamps"], dtype=np.float32)
        if "timestamps" in payload
        else np.arange(landmarks.shape[0], dtype=np.float32)
    )
    features = open_close_features_from_landmarks(landmarks)
    summary = summarize_open_close_features(features, timestamps)
    segment = estimate_active_segment(
        features,
        padding=int(args.segment_padding),
        min_motion=float(args.min_curl_range),
    )

    coverage = None
    if video_info.get("frame_count"):
        coverage = float(summary["frames"] / max(int(video_info["frame_count"]), 1))
    if int(summary["frames"]) < int(args.min_detected_frames):
        reasons.append("too_few_detected_frames")
    if coverage is not None and coverage < float(args.min_detection_coverage):
        reasons.append("low_detection_coverage")
    if float(summary["curl_range"]) < float(args.min_curl_range):
        reasons.append("low_open_close_motion")
    if float(summary["palm_width_ratio"]) > float(args.max_palm_width_ratio):
        reasons.append("unstable_hand_scale")
    if not retarget_path.exists():
        reasons.append("missing_retarget")

    retarget_payload = _load_json(retarget_report)
    rollout_summary = retarget_payload.get("rollout_summary") if isinstance(retarget_payload, dict) else None
    if rollout_summary:
        item["rollout_summary"] = rollout_summary

    item.update(
        {
            "status": _status_from_reasons(reasons),
            "review_reasons": reasons,
            "detection_coverage": coverage,
            "open_close_summary": summary,
            "suggested_segment": segment,
            "manual_decision": "needs_review" if reasons else "auto_usable",
            "notes": "",
        }
    )
    return item


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an open/close video screening manifest")
    parser.add_argument("--video-dir", default=str(PROJECT_ROOT / "videos"))
    parser.add_argument(
        "--trace-dir",
        default=str(PROJECT_ROOT / "artifacts" / "vision_real_hand" / "video_folder_20260504" / "data"),
    )
    parser.add_argument(
        "--retarget-dir",
        default=str(PROJECT_ROOT / "artifacts" / "vision_real_hand" / "video_folder_20260504" / "retarget"),
    )
    parser.add_argument(
        "--reports-dir",
        default=str(PROJECT_ROOT / "artifacts" / "vision_real_hand" / "video_folder_20260504" / "reports"),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-detected-frames", type=int, default=60)
    parser.add_argument("--min-detection-coverage", type=float, default=0.35)
    parser.add_argument("--min-curl-range", type=float, default=0.12)
    parser.add_argument("--max-palm-width-ratio", type=float, default=2.8)
    parser.add_argument("--segment-padding", type=int, default=12)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    video_dir = Path(args.video_dir)
    trace_dir = Path(args.trace_dir)
    retarget_dir = Path(args.retarget_dir)
    reports_dir = Path(args.reports_dir)
    videos = _video_files(video_dir)
    items = [build_item(video, trace_dir, retarget_dir, reports_dir, args) for video in videos]
    summary = {
        "total_videos": len(items),
        "usable": sum(1 for item in items if item.get("status") == "usable"),
        "review": sum(1 for item in items if item.get("status") == "review"),
        "missing_trace": sum(1 for item in items if item.get("status") == "missing_trace"),
    }
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "open_close_video_manifest_v1",
        "video_dir": str(video_dir),
        "trace_dir": str(trace_dir),
        "retarget_dir": str(retarget_dir),
        "thresholds": {
            "min_detected_frames": int(args.min_detected_frames),
            "min_detection_coverage": float(args.min_detection_coverage),
            "min_curl_range": float(args.min_curl_range),
            "max_palm_width_ratio": float(args.max_palm_width_ratio),
            "segment_padding": int(args.segment_padding),
        },
        "summary": summary,
        "items": items,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(json_ready(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved manifest: {output}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
