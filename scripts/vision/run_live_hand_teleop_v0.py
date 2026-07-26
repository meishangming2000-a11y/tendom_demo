#!/usr/bin/env python3
"""Live/video hand teleop capture into teleop_episode_v0.

This runner is a Phase 2 diagnostic entrypoint. It can read a live camera,
pre-recorded video, or an existing palm-trace NPZ, then writes the common
teleop episode contract from docs/teleop_dataset_contract_v0.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from vision.hand_open_close import OPEN_CLOSE_FEATURE_NAMES, build_open_close_feature, json_ready
from vision.palm_landmarks import build_palm_feature, validate_landmarks
from vision.shadow_retarget import (
    SHADOW_ACTUATOR_NAMES,
    RetargetConfig,
    retarget_landmarks_to_shadow_action,
)


SIM_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SIM_ROOT.parent

HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)

SEMANTIC_FEATURES = (
    "thumb_curl",
    "thumb_opposition",
    "thumb_spread",
    "index_curl",
    "index_spread",
    "middle_curl",
    "middle_spread",
    "ring_curl",
    "ring_spread",
    "little_curl",
    "little_spread",
    "global_curl_mean",
    "index_little_tip_span",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _default_model_path() -> Path:
    return (
        PROJECT_ROOT
        / "artifacts"
        / "vision_real_hand"
        / "hand_example_20260429"
        / "one_command_compare"
        / "models"
        / "hand_landmarker.task"
    )


def _semantic_action(open_close_feature: np.ndarray) -> Dict[str, Any]:
    values_by_name = {
        name: float(open_close_feature[idx])
        for idx, name in enumerate(OPEN_CLOSE_FEATURE_NAMES)
    }
    return {
        "action_schema": "semantic_hand_action_v0",
        "action_surface": "hand_semantic",
        "values": {name: values_by_name[name] for name in SEMANTIC_FEATURES},
        "status": "pass",
    }


def _backend_action(
    landmarks: np.ndarray,
    backend: str,
    mirror_x: bool,
) -> Dict[str, Any]:
    if backend == "none":
        return {
            "backend_id": "none",
            "action_schema": "none",
            "action_dim": 0,
            "values": [],
            "actuator_names": [],
            "status": "review",
        }
    if backend != "shadow_diagnostic":
        raise ValueError(f"Unsupported backend: {backend}")
    action, _debug = retarget_landmarks_to_shadow_action(
        landmarks,
        config=RetargetConfig(mirror_x=bool(mirror_x)),
    )
    return {
        "backend_id": "shadow_diagnostic",
        "action_schema": "shadow_hand_normalized_action_v1",
        "action_dim": int(action.shape[0]),
        "values": action.astype(np.float32).tolist(),
        "actuator_names": list(SHADOW_ACTUATOR_NAMES),
        "status": "pass",
    }


def _quality(
    detection_confidence: float,
    tracking_confidence: float,
    handedness: str,
    review_reasons: Iterable[str] = (),
) -> Dict[str, Any]:
    reasons = [str(item) for item in review_reasons]
    return {
        "status": "pass" if not reasons else "review",
        "detection_confidence": float(np.clip(detection_confidence, 0.0, 1.0)),
        "tracking_confidence": float(np.clip(tracking_confidence, 0.0, 1.0)),
        "visibility_fraction": 1.0,
        "handedness": handedness if handedness in {"left", "right"} else "unknown",
        "review_reasons": reasons,
    }


def _frame_labels(skill_id: str, phase_id: str, operator_event: str = "none") -> Dict[str, Any]:
    return {
        "skill_id": skill_id,
        "phase_id": phase_id,
        "operator_event": operator_event,
        "failure_reasons": [],
        "safety_flags": [],
    }


def _build_frame(
    frame_index: int,
    timestamp_s: float,
    source_frame_index: int | None,
    landmarks: np.ndarray,
    backend: str,
    mirror_x: bool,
    skill_id: str,
    phase_id: str,
    quality: Dict[str, Any],
) -> Dict[str, Any]:
    lm = validate_landmarks(landmarks)
    palm_feature, _palm_meta = build_palm_feature(lm)
    open_close_feature, _open_close_meta = build_open_close_feature(lm)
    return {
        "frame_index": int(frame_index),
        "timestamp_ns": int(round(max(0.0, float(timestamp_s)) * 1_000_000_000)),
        "timestamp_s": float(max(0.0, timestamp_s)),
        "source_frame_index": None if source_frame_index is None else int(source_frame_index),
        "landmarks_21x3": lm.astype(np.float32).tolist(),
        "palm_feature_76": palm_feature.astype(np.float32).tolist(),
        "open_close_feature_35": open_close_feature.astype(np.float32).tolist(),
        "semantic_action_v0": _semantic_action(open_close_feature),
        "backend_action_v0": _backend_action(lm, backend=backend, mirror_x=mirror_x),
        "quality": quality,
        "labels": _frame_labels(skill_id=skill_id, phase_id=phase_id),
    }


def _draw_landmarks_on_frame(frame_bgr: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    import cv2

    out = frame_bgr.copy()
    height, width = out.shape[:2]

    def project(point: np.ndarray) -> Tuple[int, int]:
        x = int(np.clip(float(point[0]) * width, 0, width - 1))
        y = int(np.clip(float(point[1]) * height, 0, height - 1))
        return x, y

    lm = np.asarray(landmarks, dtype=np.float32)
    for start, end in HAND_CONNECTIONS:
        cv2.line(out, project(lm[start]), project(lm[end]), (255, 110, 40), 2, cv2.LINE_AA)
    for idx, point in enumerate(lm):
        color = (45, 210, 140) if idx == 0 else (30, 90, 230)
        cv2.circle(out, project(point), 4 if idx else 6, color, -1, cv2.LINE_AA)
    return out


def _draw_trace_landmarks(landmarks: np.ndarray, width: int = 720, height: int = 520) -> np.ndarray:
    import cv2

    canvas = np.full((height, width, 3), 246, dtype=np.uint8)
    lm = np.asarray(landmarks, dtype=np.float32)
    xy = lm[:, :2]
    xy_min = np.min(xy, axis=0)
    xy_max = np.max(xy, axis=0)
    span = np.maximum(xy_max - xy_min, 1e-6)
    pad = 0.15 * float(np.max(span))
    xmin, ymin = xy_min - pad
    xmax, ymax = xy_max + pad
    xspan = max(float(xmax - xmin), 1e-6)
    yspan = max(float(ymax - ymin), 1e-6)
    margin = 45

    def project(point: np.ndarray) -> Tuple[int, int]:
        x = margin + int(round(((float(point[0]) - xmin) / xspan) * (width - 2 * margin)))
        y = margin + int(round(((float(point[1]) - ymin) / yspan) * (height - 2 * margin)))
        return x, y

    cv2.rectangle(canvas, (margin, margin), (width - margin, height - margin), (220, 226, 234), 1)
    for start, end in HAND_CONNECTIONS:
        cv2.line(canvas, project(lm[start]), project(lm[end]), (126, 91, 48), 3, cv2.LINE_AA)
    for idx, point in enumerate(lm):
        color = (40, 150, 110) if idx == 0 else (36, 92, 219)
        cv2.circle(canvas, project(point), 5 if idx else 7, color, -1, cv2.LINE_AA)
    cv2.putText(
        canvas,
        "teleop trace landmark check",
        (18, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (30, 34, 42),
        2,
        cv2.LINE_AA,
    )
    return canvas


def _write_outputs(
    output_dir: Path,
    episode: Dict[str, Any],
    frames: List[Dict[str, Any]],
    report: Dict[str, Any],
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    episode_path = output_dir / "teleop_episode_v0.json"
    trace_jsonl_path = output_dir / "session_trace.jsonl"
    arrays_path = output_dir / "session_arrays.npz"
    report_path = output_dir / "session_report.json"

    artifacts = [
        {"artifact_type": "teleop_episode", "path": str(episode_path), "status": "generated"},
        {"artifact_type": "session_trace_jsonl", "path": str(trace_jsonl_path), "status": "generated"},
        {"artifact_type": "session_arrays_npz", "path": str(arrays_path), "status": "generated"},
        {"artifact_type": "session_report", "path": str(report_path), "status": "generated"},
    ]
    overlay_dir = output_dir / "overlays"
    if overlay_dir.exists():
        artifacts.append({"artifact_type": "overlay_dir", "path": str(overlay_dir), "status": "generated"})
    episode["artifacts"] = artifacts

    episode_path.write_text(json.dumps(json_ready(episode), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    with trace_jsonl_path.open("w", encoding="utf-8") as handle:
        for frame in frames:
            handle.write(json.dumps(json_ready(frame), ensure_ascii=True) + "\n")

    timestamps = np.asarray([frame["timestamp_s"] for frame in frames], dtype=np.float32)
    landmarks = np.asarray([frame["landmarks_21x3"] for frame in frames], dtype=np.float32)
    palm_features = np.asarray([frame["palm_feature_76"] for frame in frames], dtype=np.float32)
    open_close_features = np.asarray([frame["open_close_feature_35"] for frame in frames], dtype=np.float32)
    backend_actions = np.asarray(
        [frame["backend_action_v0"]["values"] for frame in frames],
        dtype=np.float32,
    )
    np.savez_compressed(
        arrays_path,
        timestamps=timestamps,
        landmarks=landmarks,
        palm_features=palm_features,
        open_close_features=open_close_features,
        backend_actions=backend_actions,
        open_close_feature_names=np.asarray(list(OPEN_CLOSE_FEATURE_NAMES), dtype=object),
        metadata=json_ready(report),
    )
    report_path.write_text(json.dumps(json_ready(report), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {
        "episode": episode_path,
        "trace_jsonl": trace_jsonl_path,
        "arrays": arrays_path,
        "report": report_path,
    }


def _build_episode_root(
    session_id: str,
    source_type: str,
    source_uri: str,
    capture_interface: str,
    operator_id: str,
    coordinate_frame: str,
    notes: str,
    backend_schema: str,
    frames: List[Dict[str, Any]],
    status: str,
    terminal_reason: str,
    failure_reasons: List[str],
) -> Dict[str, Any]:
    return {
        "schema_version": "teleop_episode_v0",
        "episode_id": session_id,
        "dataset_id": session_id,
        "created_at_utc": _utc_stamp(),
        "source": {
            "source_type": source_type,
            "source_uri": source_uri,
            "capture_interface": capture_interface,
            "operator_id": operator_id,
            "coordinate_frame": coordinate_frame,
            "notes": notes,
        },
        "contract": {
            "landmark_schema": "mediapipe_hand_landmarks_21x3_v0",
            "palm_feature_schema": "palm_feature_v1",
            "palm_feature_dim": 76,
            "open_close_feature_schema": "hand_open_close_feature_v1",
            "open_close_feature_dim": 35,
            "semantic_action_schema": "semantic_hand_action_v0",
            "backend_action_schema": backend_schema,
        },
        "frames": frames,
        "episode_labels": {
            "split": "unassigned",
            "status": status,
            "success": None,
            "terminal_reason": terminal_reason,
            "failure_reasons": failure_reasons,
        },
        "artifacts": [],
    }


def _summarize_session(
    session_id: str,
    source_type: str,
    source_uri: str,
    output_dir: Path,
    frames: List[Dict[str, Any]],
    source_frames_read: int,
    overlays_written: int,
    dependency_status: Dict[str, Any],
    started_at: float,
) -> Dict[str, Any]:
    elapsed = max(time.time() - started_at, 1e-6)
    detected = len(frames)
    timestamps = [float(frame["timestamp_s"]) for frame in frames]
    duration = float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0
    quality_status = [frame["quality"]["status"] for frame in frames]
    action_dims = sorted({int(frame["backend_action_v0"]["action_dim"]) for frame in frames})
    return {
        "session_id": session_id,
        "source_type": source_type,
        "source_uri": source_uri,
        "output_dir": str(output_dir),
        "frames_detected": detected,
        "source_frames_read": int(source_frames_read),
        "detection_coverage": float(detected / max(source_frames_read, 1)),
        "duration_seconds": duration,
        "wall_time_seconds": elapsed,
        "processing_fps": float(source_frames_read / elapsed),
        "detected_fps": float(detected / elapsed),
        "quality_counts": {
            "pass": int(sum(1 for item in quality_status if item == "pass")),
            "review": int(sum(1 for item in quality_status if item == "review")),
            "reject": int(sum(1 for item in quality_status if item == "reject")),
        },
        "backend_action_dims": action_dims,
        "overlays_written": int(overlays_written),
        "dependency_status": dependency_status,
        "status": "PASS" if frames else "FAIL",
    }


def _extract_handedness_solutions(result: Any) -> Tuple[str, float]:
    if not getattr(result, "multi_handedness", None):
        return "unknown", 1.0
    handedness = result.multi_handedness[0]
    if not handedness.classification:
        return "unknown", 1.0
    cls = handedness.classification[0]
    label = str(getattr(cls, "label", "unknown")).lower()
    score = float(getattr(cls, "score", 1.0))
    return label if label in {"left", "right"} else "unknown", score


def _extract_handedness_tasks(result: Any) -> Tuple[str, float]:
    if not getattr(result, "handedness", None):
        return "unknown", 1.0
    handedness = result.handedness[0]
    if not handedness:
        return "unknown", 1.0
    cls = handedness[0]
    label = str(getattr(cls, "category_name", "unknown")).lower()
    score = float(getattr(cls, "score", 1.0))
    return label if label in {"left", "right"} else "unknown", score


def _capture_with_solutions(args: argparse.Namespace, source: Any, output_dir: Path) -> Tuple[List[Dict[str, Any]], int, int, str]:
    import cv2
    import mediapipe as mp

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open vision source: {source}")

    overlay_dir = output_dir / "overlays"
    if args.save_overlays:
        overlay_dir.mkdir(parents=True, exist_ok=True)

    frames: List[Dict[str, Any]] = []
    source_frames_read = 0
    overlays_written = 0
    started = time.time()
    base_timestamp_s: float | None = None
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    mp_hands = mp.solutions.hands

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=float(args.min_detection_confidence),
        min_tracking_confidence=float(args.min_tracking_confidence),
    ) as hands:
        while cap.isOpened():
            if args.duration_sec and (time.time() - started) >= float(args.duration_sec):
                break
            ok, frame = cap.read()
            if not ok:
                break
            if args.mirror:
                frame = cv2.flip(frame, 1)
            timestamp_ms = float(cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
            if timestamp_ms <= 0.0:
                timestamp_s = source_frames_read / max(fps, 1e-6)
            else:
                timestamp_s = timestamp_ms / 1000.0
            if base_timestamp_s is None:
                base_timestamp_s = timestamp_s
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                landmarks = np.asarray([[lm.x, lm.y, lm.z] for lm in hand.landmark], dtype=np.float32)
                handedness, score = _extract_handedness_solutions(result)
                teleop_frame = _build_frame(
                    frame_index=len(frames),
                    timestamp_s=float(timestamp_s - base_timestamp_s),
                    source_frame_index=source_frames_read,
                    landmarks=landmarks,
                    backend=args.backend,
                    mirror_x=args.mirror_x,
                    skill_id=args.skill_id,
                    phase_id=args.phase_id,
                    quality=_quality(score, score, handedness),
                )
                frames.append(teleop_frame)
                if args.save_overlays and len(frames) % max(1, int(args.overlay_stride)) == 0:
                    overlay = _draw_landmarks_on_frame(frame, landmarks)
                    cv2.imwrite(str(overlay_dir / f"overlay_{len(frames) - 1:05d}.png"), overlay)
                    overlays_written += 1
                if args.show and not args.headless:
                    cv2.imshow("live hand teleop v0", _draw_landmarks_on_frame(frame, landmarks))
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            source_frames_read += 1
            if args.max_detected_frames and len(frames) >= int(args.max_detected_frames):
                break
            if args.max_source_frames and source_frames_read >= int(args.max_source_frames):
                break
    cap.release()
    if args.show and not args.headless:
        cv2.destroyAllWindows()
    return frames, source_frames_read, overlays_written, "opencv_mediapipe_solutions"


def _capture_with_tasks(args: argparse.Namespace, source: Any, output_dir: Path) -> Tuple[List[Dict[str, Any]], int, int, str]:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

    model_path = Path(args.hand_landmarker_model or _default_model_path())
    if not model_path.exists():
        raise FileNotFoundError(
            f"MediaPipe Tasks requires a hand_landmarker.task model. Missing: {model_path}"
        )
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open vision source: {source}")

    overlay_dir = output_dir / "overlays"
    if args.save_overlays:
        overlay_dir.mkdir(parents=True, exist_ok=True)

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=VisionTaskRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=float(args.min_detection_confidence),
        min_hand_presence_confidence=float(args.min_presence_confidence),
        min_tracking_confidence=float(args.min_tracking_confidence),
    )
    frames: List[Dict[str, Any]] = []
    source_frames_read = 0
    overlays_written = 0
    started = time.time()
    base_timestamp_s: float | None = None

    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            if args.duration_sec and (time.time() - started) >= float(args.duration_sec):
                break
            ok, frame = cap.read()
            if not ok:
                break
            if args.mirror:
                frame = cv2.flip(frame, 1)
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC) or 0)
            if timestamp_ms <= 0:
                timestamp_ms = int(round(source_frames_read * 1000.0 / max(fps, 1e-6)))
            timestamp_s = timestamp_ms / 1000.0
            if base_timestamp_s is None:
                base_timestamp_s = timestamp_s
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = landmarker.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                timestamp_ms,
            )
            if result.hand_landmarks:
                hand = result.hand_landmarks[0]
                landmarks = np.asarray([[lm.x, lm.y, lm.z] for lm in hand], dtype=np.float32)
                handedness, score = _extract_handedness_tasks(result)
                teleop_frame = _build_frame(
                    frame_index=len(frames),
                    timestamp_s=float(timestamp_s - base_timestamp_s),
                    source_frame_index=source_frames_read,
                    landmarks=landmarks,
                    backend=args.backend,
                    mirror_x=args.mirror_x,
                    skill_id=args.skill_id,
                    phase_id=args.phase_id,
                    quality=_quality(score, score, handedness),
                )
                frames.append(teleop_frame)
                if args.save_overlays and len(frames) % max(1, int(args.overlay_stride)) == 0:
                    overlay = _draw_landmarks_on_frame(frame, landmarks)
                    cv2.imwrite(str(overlay_dir / f"overlay_{len(frames) - 1:05d}.png"), overlay)
                    overlays_written += 1
                if args.show and not args.headless:
                    cv2.imshow("live hand teleop v0", _draw_landmarks_on_frame(frame, landmarks))
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            source_frames_read += 1
            if args.max_detected_frames and len(frames) >= int(args.max_detected_frames):
                break
            if args.max_source_frames and source_frames_read >= int(args.max_source_frames):
                break
    cap.release()
    if args.show and not args.headless:
        cv2.destroyAllWindows()
    return frames, source_frames_read, overlays_written, "opencv_mediapipe_tasks"


def _capture_from_cv_source(args: argparse.Namespace, source: Any, output_dir: Path) -> Tuple[List[Dict[str, Any]], int, int, str, Dict[str, Any]]:
    import mediapipe as mp

    dependency_status = {
        "cv2": True,
        "mediapipe": True,
        "mediapipe_has_solutions_hands": bool(hasattr(mp, "solutions") and hasattr(mp.solutions, "hands")),
    }
    if dependency_status["mediapipe_has_solutions_hands"]:
        frames, source_frames_read, overlays_written, interface = _capture_with_solutions(args, source, output_dir)
    else:
        frames, source_frames_read, overlays_written, interface = _capture_with_tasks(args, source, output_dir)
    return frames, source_frames_read, overlays_written, interface, dependency_status


def _capture_from_trace(args: argparse.Namespace, output_dir: Path) -> Tuple[List[Dict[str, Any]], int, int, str, Dict[str, Any]]:
    import cv2

    payload = np.load(args.input_trace, allow_pickle=True)
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    timestamps = (
        np.asarray(payload["timestamps"], dtype=np.float32)
        if "timestamps" in payload
        else np.arange(landmarks.shape[0], dtype=np.float32) / 30.0
    )
    source_frame_indices = (
        np.asarray(payload["source_frame_indices"], dtype=np.float32)
        if "source_frame_indices" in payload
        else np.arange(landmarks.shape[0], dtype=np.float32)
    )
    count = landmarks.shape[0]
    if args.max_detected_frames:
        count = min(count, int(args.max_detected_frames))
    base_timestamp = float(timestamps[0]) if timestamps.size else 0.0
    frames: List[Dict[str, Any]] = []
    overlay_dir = output_dir / "overlays"
    if args.save_overlays:
        overlay_dir.mkdir(parents=True, exist_ok=True)
    overlays_written = 0
    for idx in range(count):
        teleop_frame = _build_frame(
            frame_index=idx,
            timestamp_s=float(timestamps[idx] - base_timestamp) if idx < timestamps.shape[0] else idx / 30.0,
            source_frame_index=int(round(float(source_frame_indices[idx]))) if idx < source_frame_indices.shape[0] else idx,
            landmarks=landmarks[idx],
            backend=args.backend,
            mirror_x=args.mirror_x,
            skill_id=args.skill_id,
            phase_id=args.phase_id,
            quality=_quality(1.0, 1.0, "unknown", review_reasons=["precomputed_trace_no_live_confidence"]),
        )
        frames.append(teleop_frame)
        if args.save_overlays and (idx % max(1, int(args.overlay_stride)) == 0):
            overlay = _draw_trace_landmarks(landmarks[idx])
            cv2.imwrite(str(overlay_dir / f"overlay_{idx:05d}.png"), overlay)
            overlays_written += 1
    dependency_status = {
        "cv2": True,
        "mediapipe": "not_required_for_input_trace",
    }
    return frames, int(landmarks.shape[0]), overlays_written, "npz_trace_import", dependency_status


def _validate_episode(episode_path: Path) -> Dict[str, Any]:
    validator_path = PROJECT_ROOT / "tools" / "validate_teleop_dataset_contract_v0.py"
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    import validate_teleop_dataset_contract_v0 as validator

    return validator.validate_file(
        sample_path=episode_path,
        schema_path=PROJECT_ROOT / "docs" / "teleop_dataset_contract_v0.schema.json",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture live/video hand teleop into teleop_episode_v0")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--camera-index", type=int, default=None, help="Live camera index, e.g. 0")
    source.add_argument("--input-video", default="", help="Pre-recorded video path")
    source.add_argument("--input-trace", default="", help="Existing palm-trace NPZ with landmarks/timestamps")
    parser.add_argument(
        "--output-root",
        default=str(PROJECT_ROOT / "artifacts" / "live_hand_teleop"),
        help="Generated artifact root",
    )
    parser.add_argument("--session-id", default="", help="Session id; default uses timestamp")
    parser.add_argument("--operator-id", default="local_operator")
    parser.add_argument("--skill-id", default="teleop_hand_open_close")
    parser.add_argument("--phase-id", default="capture")
    parser.add_argument("--backend", choices=["shadow_diagnostic", "none"], default="shadow_diagnostic")
    parser.add_argument("--duration-sec", type=float, default=30.0, help="Live/video wall-time cap; 0 disables")
    parser.add_argument("--max-source-frames", type=int, default=0)
    parser.add_argument("--max-detected-frames", type=int, default=0)
    parser.add_argument("--mirror", action="store_true", help="Mirror camera/video frames before detection")
    parser.add_argument("--mirror-x", action="store_true", help="Mirror x before Shadow diagnostic retarget")
    parser.add_argument("--save-overlays", action="store_true")
    parser.add_argument("--overlay-stride", type=int, default=15)
    parser.add_argument("--show", action="store_true", help="Show live OpenCV window")
    parser.add_argument("--headless", action="store_true", help="Disable display even if --show is present")
    parser.add_argument(
        "--hand-landmarker-model",
        default=os.environ.get("MEDIAPIPE_HAND_LANDMARKER_MODEL", str(_default_model_path())),
    )
    parser.add_argument("--min-detection-confidence", type=float, default=0.5)
    parser.add_argument("--min-presence-confidence", type=float, default=0.5)
    parser.add_argument("--min-tracking-confidence", type=float, default=0.5)
    parser.add_argument("--skip-contract-validation", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    session_id = args.session_id or f"live_hand_teleop_{_run_id()}"
    output_dir = Path(args.output_root).resolve() / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    if args.input_trace:
        source_type = "landmark_file"
        source_uri = str(Path(args.input_trace).resolve())
        frames, source_frames_read, overlays_written, interface, dependency_status = _capture_from_trace(args, output_dir)
        coordinate_frame = "mediapipe_normalized_or_trace_source_xyz"
        notes = "Precomputed trace validation path for Phase 2 live interface."
    else:
        try:
            import cv2  # noqa: F401
            import mediapipe  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "OpenCV and MediaPipe are required for camera/video capture. "
                "Install with: pip install opencv-python mediapipe"
            ) from exc
        if args.input_video:
            source = str(Path(args.input_video).resolve())
            source_type = "video_file"
            source_uri = source
            notes = "Video fallback path for Phase 2 live interface."
        else:
            source = int(0 if args.camera_index is None else args.camera_index)
            source_type = "live_camera"
            source_uri = f"camera:{source}"
            notes = "Live camera diagnostic capture. User hardware validation is still pending."
        frames, source_frames_read, overlays_written, interface, dependency_status = _capture_from_cv_source(
            args,
            source,
            output_dir,
        )
        coordinate_frame = "mediapipe_normalized_camera_xyz"

    failure_reasons = [] if frames else ["no_hand_frames_detected"]
    episode_status = "pass" if frames else "reject"
    terminal_reason = "completed" if frames else "no_hand_frames_detected"
    backend_schema = "shadow_hand_normalized_action_v1" if args.backend == "shadow_diagnostic" else "none"
    episode = _build_episode_root(
        session_id=session_id,
        source_type=source_type,
        source_uri=source_uri,
        capture_interface=interface,
        operator_id=args.operator_id,
        coordinate_frame=coordinate_frame,
        notes=notes,
        backend_schema=backend_schema,
        frames=frames,
        status=episode_status,
        terminal_reason=terminal_reason,
        failure_reasons=failure_reasons,
    )
    report = _summarize_session(
        session_id=session_id,
        source_type=source_type,
        source_uri=source_uri,
        output_dir=output_dir,
        frames=frames,
        source_frames_read=source_frames_read,
        overlays_written=overlays_written,
        dependency_status=dependency_status,
        started_at=started,
    )
    paths = _write_outputs(output_dir, episode, frames, report)
    validation_result: Dict[str, Any] | None = None
    if not args.skip_contract_validation and frames:
        validation_result = _validate_episode(paths["episode"])
        report["contract_validation"] = validation_result
        paths["report"].write_text(json.dumps(json_ready(report), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        if validation_result["status"] != "PASS":
            raise SystemExit(1)
    printable_paths = {key: str(value) for key, value in paths.items()}
    print(json.dumps(json_ready({"paths": printable_paths, "report": report}), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
