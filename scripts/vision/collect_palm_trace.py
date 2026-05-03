#!/usr/bin/env python3
"""Collect or convert visual palm landmarks into a project palm-trace dataset."""

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

from vision.palm_landmarks import frames_to_arrays, summarize_palm_trace


def _load_json_frames(path: Path) -> List[Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        frames = payload.get("frames", [])
    else:
        frames = payload
    if not isinstance(frames, list):
        raise ValueError("Expected JSON frames to be a list or {'frames': [...]} payload")
    return frames


def _collect_with_mediapipe_solutions(
    cap,
    max_frames: int,
    max_source_frames: int,
    mirror: bool,
    min_detection_confidence: float,
) -> List[Dict[str, Any]]:
    import cv2
    import mediapipe as mp

    mp_hands = mp.solutions.hands
    frames: List[Dict[str, Any]] = []
    start = time.time()
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=float(min_detection_confidence),
    ) as hands:
        source_frame_idx = 0
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            source_frame_idx += 1
            if mirror:
                frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                landmarks = [
                    [float(item.x), float(item.y), float(item.z)]
                    for item in hand.landmark
                ]
                frames.append(
                    {
                        "timestamp": float(time.time() - start),
                        "landmarks": landmarks,
                    }
                )
            if max_frames and len(frames) >= max_frames:
                break
            if max_source_frames and source_frame_idx >= max_source_frames:
                break
    return frames


def _collect_with_mediapipe_tasks(
    cap,
    max_frames: int,
    max_source_frames: int,
    mirror: bool,
    model_path: str,
    min_detection_confidence: float,
    min_presence_confidence: float,
    min_tracking_confidence: float,
) -> List[Dict[str, Any]]:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

    if not model_path:
        raise RuntimeError(
            "This MediaPipe build exposes the Tasks API instead of mp.solutions.hands. "
            "Provide --hand-landmarker-model pointing to hand_landmarker.task."
        )
    model_file = Path(model_path)
    if not model_file.exists():
        raise FileNotFoundError(model_file)

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_file)),
        running_mode=VisionTaskRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=float(min_detection_confidence),
        min_hand_presence_confidence=float(min_presence_confidence),
        min_tracking_confidence=float(min_tracking_confidence),
    )
    frames: List[Dict[str, Any]] = []
    frame_idx = 0
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            if mirror:
                frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            if timestamp_ms <= 0:
                timestamp_ms = int(round(frame_idx * 1000.0 / max(fps, 1e-6)))
            result = landmarker.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                timestamp_ms,
            )
            if result.hand_landmarks:
                hand = result.hand_landmarks[0]
                landmarks = [
                    [float(item.x), float(item.y), float(item.z)]
                    for item in hand
                ]
                frames.append(
                    {
                        "timestamp": float(timestamp_ms / 1000.0),
                        "landmarks": landmarks,
                    }
                )
            frame_idx += 1
            if max_frames and len(frames) >= max_frames:
                break
            if max_source_frames and frame_idx >= max_source_frames:
                break
    return frames


def _collect_with_mediapipe(
    source: str,
    max_frames: int,
    max_source_frames: int,
    mirror: bool,
    hand_landmarker_model: str,
    min_detection_confidence: float,
    min_presence_confidence: float,
    min_tracking_confidence: float,
) -> List[Dict[str, Any]]:
    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV and MediaPipe are required for live/video collection. "
            "Install with: pip install opencv-python mediapipe"
        ) from exc

    capture_source = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(capture_source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open vision source: {source}")

    try:
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            return _collect_with_mediapipe_solutions(
                cap=cap,
                max_frames=max_frames,
                max_source_frames=max_source_frames,
                mirror=mirror,
                min_detection_confidence=min_detection_confidence,
            )
        return _collect_with_mediapipe_tasks(
            cap=cap,
            max_frames=max_frames,
            max_source_frames=max_source_frames,
            mirror=mirror,
            model_path=hand_landmarker_model,
            min_detection_confidence=min_detection_confidence,
            min_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
    finally:
        cap.release()


def save_trace(
    output_path: Path,
    timestamps: np.ndarray,
    landmarks: np.ndarray,
    features: np.ndarray,
    metadata: Dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        timestamps=timestamps,
        landmarks=landmarks,
        features=features,
        metadata=metadata,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect visual palm landmarks")
    parser.add_argument("--source", default="0", help="Camera index or video path for MediaPipe collection")
    parser.add_argument("--input-json", default="", help="JSON landmark frames to convert instead of live capture")
    parser.add_argument("--output", default="data/vision_palm_trace_latest.npz", help="Output palm trace NPZ")
    parser.add_argument("--report", default="", help="Optional JSON report path")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N detected frames; 0 means until source ends")
    parser.add_argument(
        "--max-source-frames",
        type=int,
        default=0,
        help="Stop after reading N source frames even if fewer hands were detected; 0 means until source ends",
    )
    parser.add_argument("--mirror", action="store_true", help="Mirror camera frames before detection")
    parser.add_argument("--source-label", default="", help="Human-readable source label for metadata")
    parser.add_argument(
        "--hand-landmarker-model",
        default=os.environ.get("MEDIAPIPE_HAND_LANDMARKER_MODEL", ""),
        help="Path to hand_landmarker.task for MediaPipe Tasks builds",
    )
    parser.add_argument("--min-detection-confidence", type=float, default=0.5, help="MediaPipe hand detection threshold")
    parser.add_argument("--min-presence-confidence", type=float, default=0.5, help="MediaPipe hand presence threshold")
    parser.add_argument("--min-tracking-confidence", type=float, default=0.5, help="MediaPipe hand tracking threshold")
    args = parser.parse_args()

    if args.input_json:
        frames = _load_json_frames(Path(args.input_json))
        source_kind = "json_landmarks"
    else:
        frames = _collect_with_mediapipe(
            args.source,
            args.max_frames,
            args.max_source_frames,
            args.mirror,
            args.hand_landmarker_model,
            args.min_detection_confidence,
            args.min_presence_confidence,
            args.min_tracking_confidence,
        )
        source_kind = "mediapipe"

    timestamps, landmarks, features, frame_metadata = frames_to_arrays(frames)
    metadata = {
        "dataset_type": "vision_palm_trace",
        "source_kind": source_kind,
        "source": args.source_label or (args.input_json or args.source),
        "hand_landmarker_model": args.hand_landmarker_model,
        "min_detection_confidence": float(args.min_detection_confidence),
        "min_presence_confidence": float(args.min_presence_confidence),
        "min_tracking_confidence": float(args.min_tracking_confidence),
        "feature_schema": "normalized_21_landmarks_plus_palm_frame_v1",
        "feature_dim": int(features.shape[1]) if features.size else 0,
        "landmark_count": 21,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "frame_metadata_preview": frame_metadata[:3],
        "summary": summarize_palm_trace(features, timestamps),
    }

    output_path = Path(args.output)
    save_trace(output_path, timestamps, landmarks, features, metadata)
    print(f"Saved palm trace: {output_path}")
    print(json.dumps(metadata["summary"], indent=2, ensure_ascii=False))

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
