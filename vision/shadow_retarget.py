"""Heuristic retargeting from 21 hand landmarks to Shadow Hand actions.

This module is intentionally small and calibration-light. It maps MediaPipe-style
21 hand landmarks into the current Shadow Hand normalized action layout so that
vision traces can be smoke-tested inside the MuJoCo tooling before a proper IK or
camera-calibrated retargeting stack exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from .palm_landmarks import (
    INDEX_MCP,
    MIDDLE_MCP,
    PINKY_MCP,
    WRIST,
    _safe_normalize,
    validate_landmarks,
)


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


SHADOW_ACTUATOR_NAMES = (
    "rh_A_WRJ2",
    "rh_A_WRJ1",
    "rh_A_THJ5",
    "rh_A_THJ4",
    "rh_A_THJ3",
    "rh_A_THJ2",
    "rh_A_THJ1",
    "rh_A_FFJ4",
    "rh_A_FFJ3",
    "rh_A_FFJ2",
    "rh_A_FFJ1",
    "rh_A_MFJ4",
    "rh_A_MFJ3",
    "rh_A_MFJ2",
    "rh_A_MFJ1",
    "rh_A_RFJ4",
    "rh_A_RFJ3",
    "rh_A_RFJ2",
    "rh_A_RFJ1",
    "rh_A_LFJ5",
    "rh_A_LFJ4",
    "rh_A_LFJ3",
    "rh_A_LFJ2",
    "rh_A_LFJ1",
)


FINGER_CHAINS = {
    "index": (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
    "middle": (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    "ring": (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
    "little": (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
}


@dataclass(frozen=True)
class RetargetConfig:
    """Configuration for the heuristic Shadow retargeter."""

    open_action: float = -0.65
    proximal_closed_action: float = 0.75
    distal_closed_action: float = 0.88
    abduction_scale: float = 0.45
    thumb_open_action: float = -0.55
    thumb_closed_action: float = 0.82
    wrist_scale: float = 0.0
    smoothing_alpha: float = 0.0
    mirror_x: bool = False


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


def _lerp_action(open_value: float, closed_value: float, amount: float) -> float:
    amount = float(np.clip(amount, 0.0, 1.0))
    return float(open_value + (closed_value - open_value) * amount)


def _prepare_landmarks(landmarks: np.ndarray, mirror_x: bool = False) -> np.ndarray:
    lm = validate_landmarks(landmarks).copy()
    if mirror_x:
        center_x = float(np.mean(lm[:, 0]))
        lm[:, 0] = (2.0 * center_x) - lm[:, 0]
    return lm


def _palm_frame(landmarks: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    palm_center = np.mean(
        landmarks[[WRIST, INDEX_MCP, MIDDLE_MCP, PINKY_MCP]],
        axis=0,
    ).astype(np.float32)
    palm_width = float(np.linalg.norm(landmarks[INDEX_MCP] - landmarks[PINKY_MCP]))
    x_axis = _safe_normalize(
        landmarks[INDEX_MCP] - landmarks[PINKY_MCP],
        fallback=(1.0, 0.0, 0.0),
    )
    y_axis = _safe_normalize(
        landmarks[MIDDLE_MCP] - landmarks[WRIST],
        fallback=(0.0, 1.0, 0.0),
    )
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
        "mcp_bend": float(mcp_bend),
        "pip_bend": float(pip_bend),
        "dip_bend": float(dip_bend),
        "proximal": proximal,
        "middle": middle,
        "distal": distal,
        "curl": curl,
        "spread": spread,
    }


def _thumb_metrics(
    landmarks: np.ndarray,
    palm_center: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    palm_width: float,
) -> Dict[str, float]:
    cmc_bend = _joint_bend(landmarks[WRIST], landmarks[THUMB_CMC], landmarks[THUMB_MCP])
    mcp_bend = _joint_bend(landmarks[THUMB_CMC], landmarks[THUMB_MCP], landmarks[THUMB_IP])
    ip_bend = _joint_bend(landmarks[THUMB_MCP], landmarks[THUMB_IP], landmarks[THUMB_TIP])
    thumb_dir = _safe_normalize(
        landmarks[THUMB_TIP] - landmarks[THUMB_CMC],
        fallback=(1.0, 0.0, 0.0),
    )
    lateral = float(np.dot(thumb_dir, x_axis))
    forward = float(np.dot(thumb_dir, y_axis))
    spread = float(np.clip(np.arctan2(lateral, max(abs(forward), 1e-4)) / 0.95, -1.0, 1.0))
    tip_distance = float(np.linalg.norm(landmarks[THUMB_TIP] - palm_center))
    opposition = float(np.clip(1.0 - tip_distance / max(1.45 * palm_width, 1e-6), 0.0, 1.0))
    curl = float(np.clip(0.25 * cmc_bend + 0.45 * mcp_bend + 0.30 * ip_bend, 0.0, 1.0))
    return {
        "cmc_bend": float(cmc_bend),
        "mcp_bend": float(mcp_bend),
        "ip_bend": float(ip_bend),
        "curl": curl,
        "spread": spread,
        "opposition": opposition,
    }


def retarget_landmarks_to_shadow_action(
    landmarks: np.ndarray,
    config: RetargetConfig | None = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Map one 21-landmark frame to a 24D Shadow normalized action."""
    cfg = config or RetargetConfig()
    lm = _prepare_landmarks(landmarks, mirror_x=cfg.mirror_x)
    palm_center, x_axis, y_axis, normal, palm_width = _palm_frame(lm)

    action = np.zeros(len(SHADOW_ACTUATOR_NAMES), dtype=np.float32)
    debug: Dict[str, Any] = {
        "palm_center": palm_center.astype(np.float32).tolist(),
        "palm_width": float(palm_width),
        "palm_x_axis": x_axis.astype(np.float32).tolist(),
        "palm_y_axis": y_axis.astype(np.float32).tolist(),
        "palm_normal": normal.astype(np.float32).tolist(),
        "finger_metrics": {},
    }

    if cfg.wrist_scale:
        action[0] = float(np.clip(cfg.wrist_scale * normal[1], -0.35, 0.35))
        action[1] = float(np.clip(cfg.wrist_scale * normal[0], -0.35, 0.35))

    thumb = _thumb_metrics(lm, palm_center, x_axis, y_axis, palm_width)
    debug["thumb_metrics"] = thumb
    thumb_curl = thumb["curl"]
    action[2] = float(np.clip(0.25 * thumb["spread"] + 0.20 * thumb["opposition"], -0.55, 0.65))
    action[3] = _lerp_action(cfg.thumb_open_action, cfg.thumb_closed_action, thumb_curl)
    action[4] = _lerp_action(-0.20, 0.55, 0.6 * thumb_curl + 0.4 * thumb["opposition"])
    action[5] = _lerp_action(-0.35, 0.68, thumb_curl)
    action[6] = _lerp_action(cfg.thumb_open_action, cfg.thumb_closed_action, thumb["ip_bend"])

    finger_layout = {
        "index": (7, 8, 9, 10),
        "middle": (11, 12, 13, 14),
        "ring": (15, 16, 17, 18),
        "little": (20, 21, 22, 23),
    }
    for name, chain in FINGER_CHAINS.items():
        metrics = _finger_metrics(lm, chain, x_axis, y_axis)
        debug["finger_metrics"][name] = metrics
        spread_idx, proximal_idx, middle_idx, distal_idx = finger_layout[name]
        curl_gain = 1.0
        if name == "ring":
            curl_gain = 0.95
        elif name == "little":
            curl_gain = 0.90

        action[spread_idx] = float(np.clip(cfg.abduction_scale * metrics["spread"], -0.5, 0.5))
        action[proximal_idx] = _lerp_action(
            cfg.open_action,
            cfg.proximal_closed_action,
            np.clip(curl_gain * metrics["proximal"], 0.0, 1.0),
        )
        action[middle_idx] = _lerp_action(
            cfg.open_action,
            cfg.distal_closed_action,
            np.clip(curl_gain * metrics["middle"], 0.0, 1.0),
        )
        action[distal_idx] = _lerp_action(
            cfg.open_action,
            cfg.distal_closed_action,
            np.clip(curl_gain * metrics["distal"], 0.0, 1.0),
        )

    little = debug["finger_metrics"]["little"]
    action[19] = float(np.clip(0.20 + 0.35 * little["curl"], -0.25, 0.65))

    action = np.clip(action, -1.0, 1.0).astype(np.float32)
    debug["action_norm"] = float(np.linalg.norm(action))
    debug["action_max_abs"] = float(np.max(np.abs(action))) if action.size else 0.0
    return action, debug


def smooth_actions(actions: np.ndarray, alpha: float) -> np.ndarray:
    """Apply simple exponential smoothing to an action trajectory."""
    actions = np.asarray(actions, dtype=np.float32)
    alpha = float(np.clip(alpha, 0.0, 0.99))
    if actions.size == 0 or alpha <= 0.0:
        return actions.astype(np.float32)

    smoothed = np.zeros_like(actions, dtype=np.float32)
    smoothed[0] = actions[0]
    for idx in range(1, actions.shape[0]):
        smoothed[idx] = alpha * smoothed[idx - 1] + (1.0 - alpha) * actions[idx]
    return smoothed.astype(np.float32)


def retarget_landmark_sequence(
    landmarks: Iterable[np.ndarray],
    config: RetargetConfig | None = None,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Map a landmark sequence to a Shadow normalized-action trajectory."""
    cfg = config or RetargetConfig()
    actions = []
    debug = []
    for frame in landmarks:
        action, frame_debug = retarget_landmarks_to_shadow_action(frame, config=cfg)
        actions.append(action)
        debug.append(frame_debug)

    action_array = np.asarray(actions, dtype=np.float32)
    action_array = smooth_actions(action_array, cfg.smoothing_alpha)
    return action_array, debug


def action_summary(actions: np.ndarray) -> Dict[str, Any]:
    """Return a compact summary of a Shadow action trajectory."""
    actions = np.asarray(actions, dtype=np.float32)
    if actions.size == 0:
        return {
            "frames": 0,
            "action_dim": len(SHADOW_ACTUATOR_NAMES),
        }

    return {
        "frames": int(actions.shape[0]),
        "action_dim": int(actions.shape[1]),
        "min": float(np.min(actions)),
        "max": float(np.max(actions)),
        "mean_abs": float(np.mean(np.abs(actions))),
        "max_abs": float(np.max(np.abs(actions))),
        "mean_action_norm": float(np.mean(np.linalg.norm(actions, axis=1))),
        "actuator_names": list(SHADOW_ACTUATOR_NAMES),
    }


def config_to_metadata(config: RetargetConfig) -> Dict[str, Any]:
    """Serialize a retarget config into JSON/NPZ-friendly metadata."""
    return {
        "open_action": float(config.open_action),
        "proximal_closed_action": float(config.proximal_closed_action),
        "distal_closed_action": float(config.distal_closed_action),
        "abduction_scale": float(config.abduction_scale),
        "thumb_open_action": float(config.thumb_open_action),
        "thumb_closed_action": float(config.thumb_closed_action),
        "wrist_scale": float(config.wrist_scale),
        "smoothing_alpha": float(config.smoothing_alpha),
        "mirror_x": bool(config.mirror_x),
    }
