"""Palm-landmark feature extraction utilities.

The current representation is MediaPipe-compatible but intentionally generic:
any source that provides 21 hand landmarks as xyz triples can feed this module.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


WRIST = 0
INDEX_MCP = 5
MIDDLE_MCP = 9
PINKY_MCP = 17
PALM_ANCHORS = (WRIST, INDEX_MCP, MIDDLE_MCP, PINKY_MCP)
PALM_FEATURE_DIM = 76


def _safe_normalize(vector: np.ndarray, fallback: Iterable[float]) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm < 1e-8:
        return np.asarray(list(fallback), dtype=np.float32)
    return (vector / norm).astype(np.float32)


def validate_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """Return landmarks as a validated float32 array shaped (21, 3)."""
    arr = np.asarray(landmarks, dtype=np.float32)
    if arr.shape != (21, 3):
        raise ValueError(f"Expected landmarks with shape (21, 3), got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Palm landmarks contain NaN or inf values")
    return arr


def build_palm_feature(landmarks: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Build a stable palm feature vector from 21 xyz landmarks."""
    lm = validate_landmarks(landmarks)
    palm_center = np.mean(lm[list(PALM_ANCHORS)], axis=0).astype(np.float32)
    palm_width = float(np.linalg.norm(lm[INDEX_MCP] - lm[PINKY_MCP]))
    scale = max(palm_width, 1e-6)

    x_axis = _safe_normalize(lm[INDEX_MCP] - lm[PINKY_MCP], fallback=(1.0, 0.0, 0.0))
    y_axis = _safe_normalize(lm[MIDDLE_MCP] - lm[WRIST], fallback=(0.0, 1.0, 0.0))
    normal = _safe_normalize(np.cross(x_axis, y_axis), fallback=(0.0, 0.0, 1.0))
    y_axis = _safe_normalize(np.cross(normal, x_axis), fallback=(0.0, 1.0, 0.0))

    normalized_landmarks = ((lm - palm_center) / scale).astype(np.float32)
    feature = np.concatenate(
        [
            normalized_landmarks.reshape(-1),
            palm_center,
            x_axis,
            y_axis,
            normal,
            np.asarray([palm_width], dtype=np.float32),
        ]
    ).astype(np.float32)

    if feature.shape[0] != PALM_FEATURE_DIM:
        raise RuntimeError(f"Unexpected palm feature dimension: {feature.shape[0]}")

    metadata = {
        "palm_center": palm_center.tolist(),
        "palm_width": palm_width,
        "palm_x_axis": x_axis.tolist(),
        "palm_y_axis": y_axis.tolist(),
        "palm_normal": normal.tolist(),
        "feature_dim": PALM_FEATURE_DIM,
    }
    return feature, metadata


def extract_landmarks_from_json_frame(frame: Any) -> Tuple[float, np.ndarray]:
    """Parse a JSON frame into timestamp and landmarks."""
    if isinstance(frame, dict):
        timestamp = float(frame.get("timestamp", frame.get("time", 0.0)))
        landmarks = frame.get("landmarks")
    else:
        timestamp = 0.0
        landmarks = frame

    if landmarks is None:
        raise ValueError("JSON frame is missing landmarks")
    return timestamp, validate_landmarks(np.asarray(landmarks, dtype=np.float32))


def summarize_palm_trace(features: np.ndarray, timestamps: np.ndarray) -> Dict[str, Any]:
    """Return a compact JSON-friendly summary for a palm trace."""
    features = np.asarray(features, dtype=np.float32)
    timestamps = np.asarray(timestamps, dtype=np.float32)
    if features.size == 0:
        return {
            "frames": 0,
            "feature_dim": PALM_FEATURE_DIM,
            "duration_seconds": 0.0,
        }

    return {
        "frames": int(features.shape[0]),
        "feature_dim": int(features.shape[1]),
        "duration_seconds": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
        "feature_min": float(np.min(features)),
        "feature_max": float(np.max(features)),
        "feature_mean": float(np.mean(features)),
        "feature_std": float(np.std(features)),
    }


def frames_to_arrays(frames: List[Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """Convert JSON-like frames to timestamps, landmarks, features, and per-frame metadata."""
    timestamps = []
    landmarks = []
    features = []
    frame_metadata = []

    for frame in frames:
        timestamp, lm = extract_landmarks_from_json_frame(frame)
        feature, metadata = build_palm_feature(lm)
        timestamps.append(timestamp)
        landmarks.append(lm)
        features.append(feature)
        frame_metadata.append(metadata)

    return (
        np.asarray(timestamps, dtype=np.float32),
        np.asarray(landmarks, dtype=np.float32),
        np.asarray(features, dtype=np.float32),
        frame_metadata,
    )
