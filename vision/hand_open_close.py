"""Open/close hand-feature extraction from 21 landmarks.

This module is the first device-independent bridge between visual hand motion
and a concrete robot backend. It converts MediaPipe-style 21-point hand
landmarks into compact per-finger curl/spread features.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from .palm_landmarks import INDEX_MCP, MIDDLE_MCP, PINKY_MCP, WRIST, _safe_normalize, validate_landmarks


THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

FINGER_CHAINS = {
    "index": (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
    "middle": (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    "ring": (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
    "little": (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
}

OPEN_CLOSE_FEATURE_NAMES = (
    "thumb_curl",
    "thumb_mcp_bend",
    "thumb_ip_bend",
    "thumb_opposition",
    "thumb_spread",
    "index_curl",
    "index_proximal",
    "index_middle",
    "index_distal",
    "index_spread",
    "middle_curl",
    "middle_proximal",
    "middle_middle",
    "middle_distal",
    "middle_spread",
    "ring_curl",
    "ring_proximal",
    "ring_middle",
    "ring_distal",
    "ring_spread",
    "little_curl",
    "little_proximal",
    "little_middle",
    "little_distal",
    "little_spread",
    "global_curl_mean",
    "global_curl_std",
    "index_little_tip_span",
    "palm_width",
    "palm_normal_x",
    "palm_normal_y",
    "palm_normal_z",
    "palm_center_x",
    "palm_center_y",
    "palm_center_z",
)
OPEN_CLOSE_FEATURE_DIM = len(OPEN_CLOSE_FEATURE_NAMES)
GLOBAL_CURL_INDEX = OPEN_CLOSE_FEATURE_NAMES.index("global_curl_mean")
PALM_WIDTH_INDEX = OPEN_CLOSE_FEATURE_NAMES.index("palm_width")


def _angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    n1 = float(np.linalg.norm(v1))
    n2 = float(np.linalg.norm(v2))
    if n1 < 1e-8 or n2 < 1e-8:
        return float(np.pi)
    cosine = float(np.dot(v1, v2) / (n1 * n2))
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))


def _joint_bend(prev_pt: np.ndarray, joint_pt: np.ndarray, next_pt: np.ndarray) -> float:
    """Return a 0=open, 1=folded bend estimate from three landmarks."""
    angle = _angle_between(prev_pt - joint_pt, next_pt - joint_pt)
    return float(np.clip((np.pi - angle) / (0.72 * np.pi), 0.0, 1.0))


def palm_frame(landmarks: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Return center, x/y axes, normal, and palm width."""
    lm = validate_landmarks(landmarks)
    palm_center = np.mean(lm[[WRIST, INDEX_MCP, MIDDLE_MCP, PINKY_MCP]], axis=0).astype(np.float32)
    palm_width = float(np.linalg.norm(lm[INDEX_MCP] - lm[PINKY_MCP]))
    x_axis = _safe_normalize(lm[INDEX_MCP] - lm[PINKY_MCP], fallback=(1.0, 0.0, 0.0))
    y_axis = _safe_normalize(lm[MIDDLE_MCP] - lm[WRIST], fallback=(0.0, 1.0, 0.0))
    normal = _safe_normalize(np.cross(x_axis, y_axis), fallback=(0.0, 0.0, 1.0))
    y_axis = _safe_normalize(np.cross(normal, x_axis), fallback=(0.0, 1.0, 0.0))
    return palm_center, x_axis, y_axis, normal, palm_width


def _finger_metrics(
    landmarks: np.ndarray,
    chain: Tuple[int, int, int, int],
    x_axis: np.ndarray,
    y_axis: np.ndarray,
) -> Dict[str, float]:
    mcp, pip, dip, tip = chain
    mcp_bend = _joint_bend(landmarks[WRIST], landmarks[mcp], landmarks[pip])
    pip_bend = _joint_bend(landmarks[mcp], landmarks[pip], landmarks[dip])
    dip_bend = _joint_bend(landmarks[pip], landmarks[dip], landmarks[tip])
    base_dir = _safe_normalize(landmarks[pip] - landmarks[mcp], fallback=(0.0, 1.0, 0.0))
    lateral = float(np.dot(base_dir, x_axis))
    forward = float(np.dot(base_dir, y_axis))
    spread = float(np.clip(np.arctan2(lateral, max(abs(forward), 1e-4)) / 0.65, -1.0, 1.0))
    proximal = float(np.clip(0.65 * mcp_bend + 0.35 * pip_bend, 0.0, 1.0))
    middle = float(np.clip(0.75 * pip_bend + 0.25 * dip_bend, 0.0, 1.0))
    distal = float(np.clip(0.80 * dip_bend + 0.20 * pip_bend, 0.0, 1.0))
    curl = float(np.clip((proximal + middle + distal) / 3.0, 0.0, 1.0))
    return {
        "curl": curl,
        "proximal": proximal,
        "middle": middle,
        "distal": distal,
        "spread": spread,
    }


def _thumb_metrics(
    landmarks: np.ndarray,
    palm_center: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    palm_width: float,
) -> Dict[str, float]:
    mcp_bend = _joint_bend(landmarks[THUMB_CMC], landmarks[THUMB_MCP], landmarks[THUMB_IP])
    ip_bend = _joint_bend(landmarks[THUMB_MCP], landmarks[THUMB_IP], landmarks[THUMB_TIP])
    thumb_dir = _safe_normalize(landmarks[THUMB_TIP] - landmarks[THUMB_CMC], fallback=(1.0, 0.0, 0.0))
    lateral = float(np.dot(thumb_dir, x_axis))
    forward = float(np.dot(thumb_dir, y_axis))
    spread = float(np.clip(np.arctan2(lateral, max(abs(forward), 1e-4)) / 0.95, -1.0, 1.0))
    tip_distance = float(np.linalg.norm(landmarks[THUMB_TIP] - palm_center))
    opposition = float(np.clip(1.0 - tip_distance / max(1.45 * palm_width, 1e-6), 0.0, 1.0))
    curl = float(np.clip(0.60 * mcp_bend + 0.40 * ip_bend, 0.0, 1.0))
    return {
        "curl": curl,
        "mcp_bend": float(mcp_bend),
        "ip_bend": float(ip_bend),
        "opposition": opposition,
        "spread": spread,
    }


def build_open_close_feature(landmarks: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Build one 35D open/close semantic feature vector."""
    lm = validate_landmarks(landmarks)
    palm_center, x_axis, y_axis, normal, palm_width = palm_frame(lm)
    thumb = _thumb_metrics(lm, palm_center, x_axis, y_axis, palm_width)
    fingers = {
        name: _finger_metrics(lm, chain, x_axis, y_axis)
        for name, chain in FINGER_CHAINS.items()
    }
    curls = np.asarray(
        [
            thumb["curl"],
            fingers["index"]["curl"],
            fingers["middle"]["curl"],
            fingers["ring"]["curl"],
            fingers["little"]["curl"],
        ],
        dtype=np.float32,
    )
    tip_span = float(np.linalg.norm(lm[INDEX_TIP] - lm[PINKY_TIP]) / max(palm_width, 1e-6))

    values: List[float] = [
        thumb["curl"],
        thumb["mcp_bend"],
        thumb["ip_bend"],
        thumb["opposition"],
        thumb["spread"],
    ]
    for name in ("index", "middle", "ring", "little"):
        metrics = fingers[name]
        values.extend(
            [
                metrics["curl"],
                metrics["proximal"],
                metrics["middle"],
                metrics["distal"],
                metrics["spread"],
            ]
        )
    values.extend(
        [
            float(np.mean(curls)),
            float(np.std(curls)),
            tip_span,
            float(palm_width),
            float(normal[0]),
            float(normal[1]),
            float(normal[2]),
            float(palm_center[0]),
            float(palm_center[1]),
            float(palm_center[2]),
        ]
    )
    feature = np.asarray(values, dtype=np.float32)
    if feature.shape[0] != OPEN_CLOSE_FEATURE_DIM:
        raise RuntimeError(f"Unexpected open/close feature dimension: {feature.shape[0]}")
    metadata = {
        "feature_dim": OPEN_CLOSE_FEATURE_DIM,
        "global_curl": float(feature[GLOBAL_CURL_INDEX]),
        "palm_width": float(palm_width),
        "thumb": thumb,
        "fingers": fingers,
    }
    return feature, metadata


def open_close_features_from_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """Convert a landmark sequence into open/close features."""
    frames = np.asarray(landmarks, dtype=np.float32)
    if frames.size == 0:
        return np.zeros((0, OPEN_CLOSE_FEATURE_DIM), dtype=np.float32)
    return np.asarray([build_open_close_feature(frame)[0] for frame in frames], dtype=np.float32)


def _smooth(values: np.ndarray, window: int = 7) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    if values.shape[0] < 3 or window <= 1:
        return values
    window = int(min(max(1, window), values.shape[0]))
    kernel = np.ones(window, dtype=np.float32) / float(window)
    return np.convolve(values, kernel, mode="same").astype(np.float32)


def estimate_active_segment(
    open_close_features: np.ndarray,
    padding: int = 12,
    min_motion: float = 0.12,
) -> Dict[str, Any]:
    """Estimate the most useful open/close span in feature-frame indices."""
    features = np.asarray(open_close_features, dtype=np.float32)
    if features.size == 0:
        return {
            "start_frame": 0,
            "end_frame_exclusive": 0,
            "motion_range": 0.0,
            "motion_score": 0.0,
            "status": "empty",
        }
    curl = features[:, GLOBAL_CURL_INDEX]
    smooth = _smooth(curl, window=7)
    motion_range = float(np.max(smooth) - np.min(smooth))
    derivatives = np.abs(np.diff(smooth, prepend=smooth[0]))
    if derivatives.size == 0 or float(np.max(derivatives)) < 1e-6:
        active = np.asarray([], dtype=np.int64)
    else:
        threshold = max(float(np.percentile(derivatives, 75)), float(np.max(derivatives)) * 0.15)
        active = np.nonzero(derivatives >= threshold)[0]
    if active.size == 0:
        start = 0
        end = int(features.shape[0])
    else:
        start = max(0, int(active[0]) - int(padding))
        end = min(int(features.shape[0]), int(active[-1]) + int(padding) + 1)
    selected = smooth[start:end] if end > start else smooth
    selected_range = float(np.max(selected) - np.min(selected)) if selected.size else 0.0
    return {
        "start_frame": int(start),
        "end_frame_exclusive": int(end),
        "frames": int(max(0, end - start)),
        "motion_range": motion_range,
        "selected_motion_range": selected_range,
        "motion_score": float(motion_range + np.mean(derivatives) * 10.0),
        "status": "usable_motion" if motion_range >= float(min_motion) else "low_motion",
    }


def summarize_open_close_features(
    open_close_features: np.ndarray,
    timestamps: np.ndarray | None = None,
) -> Dict[str, Any]:
    """Return a compact summary for manifest/report files."""
    features = np.asarray(open_close_features, dtype=np.float32)
    if features.size == 0:
        return {
            "frames": 0,
            "feature_dim": OPEN_CLOSE_FEATURE_DIM,
            "curl_range": 0.0,
        }
    curl = features[:, GLOBAL_CURL_INDEX]
    palm_width = features[:, PALM_WIDTH_INDEX]
    timestamps = np.asarray(timestamps, dtype=np.float32) if timestamps is not None else np.zeros((0,), dtype=np.float32)
    duration = float(timestamps[-1] - timestamps[0]) if timestamps.shape[0] > 1 else 0.0
    min_width = float(np.min(palm_width))
    max_width = float(np.max(palm_width))
    return {
        "frames": int(features.shape[0]),
        "feature_dim": int(features.shape[1]),
        "duration_seconds": duration,
        "curl_min": float(np.min(curl)),
        "curl_max": float(np.max(curl)),
        "curl_mean": float(np.mean(curl)),
        "curl_std": float(np.std(curl)),
        "curl_range": float(np.max(curl) - np.min(curl)),
        "palm_width_min": min_width,
        "palm_width_max": max_width,
        "palm_width_ratio": float(max_width / max(min_width, 1e-6)),
    }


def json_ready(value: Any) -> Any:
    """Convert numpy-heavy values into JSON-friendly objects."""
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    return value
