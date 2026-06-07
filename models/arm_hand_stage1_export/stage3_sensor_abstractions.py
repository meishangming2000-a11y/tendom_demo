#!/usr/bin/env python3
"""Replay-safe Stage3 sensor abstraction helpers.

The functions here turn MuJoCo ground-truth state into policy-visible
sensor-style fields. Noise is keyed by base seed, episode id, step index, and
stream name, so replay does not depend on call order.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

import numpy as np


VISION_FIELD_NAMES = (
    "object_pose_xyz_est",
    "object_axis_est",
    "object_shape_params_est",
    "goal_pose_xyz_est",
    "object_to_goal_est",
    "confidence",
    "occlusion",
    "latency_steps",
    "noise_std",
)

TACTILE_FIELD_NAMES = (
    "contact_present",
    "contact_regions",
    "normal_contact_proxy",
    "contact_persistence",
    "relative_tangential_motion",
    "slip_score",
    "grip_stable",
    "crush_risk",
    "release_contact_clear",
)


@dataclass(frozen=True)
class Stage3VisionConfig:
    pose_noise_std_m: float = 0.002
    axis_noise_std: float = 0.01
    shape_noise_std_m: float = 0.001
    confidence_nominal: float = 0.95
    occlusion: float = 0.0
    latency_steps: int = 2


@dataclass(frozen=True)
class Stage3TactileConfig:
    slip_tangential_scale_mps: float = 0.12
    slip_downward_scale_mps: float = 0.08
    grip_stable_min_persistence_steps: int = 30
    release_max_hand_contacts: int = 0


@dataclass(frozen=True)
class Stage3SensorConfig:
    base_seed: int = 80
    vision: Stage3VisionConfig = Stage3VisionConfig()
    tactile: Stage3TactileConfig = Stage3TactileConfig()

    def as_metadata(self) -> dict[str, Any]:
        return {
            "base_seed": int(self.base_seed),
            "vision": asdict(self.vision),
            "tactile": asdict(self.tactile),
            "replay_key": "sha256(base_seed, episode_id, step_index, stream)",
        }


@dataclass(frozen=True)
class Stage3SensorReplayKey:
    base_seed: int
    episode_id: int
    step_index: int

    def stream_seed(self, stream: str) -> int:
        text = f"{int(self.base_seed)}:{int(self.episode_id)}:{int(self.step_index)}:{stream}"
        digest = hashlib.sha256(text.encode("ascii")).digest()
        return int.from_bytes(digest[:8], "little", signed=False) % (2**32)

    def rng(self, stream: str) -> np.random.Generator:
        return np.random.default_rng(self.stream_seed(stream))

    def as_metadata(self) -> dict[str, int]:
        return {
            "base_seed": int(self.base_seed),
            "episode_id": int(self.episode_id),
            "step_index": int(self.step_index),
        }


def safe_unit(vec: Iterable[float], fallback: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(vec), dtype=np.float64)
    fallback_arr = np.asarray(list(fallback), dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if norm <= 1e-12:
        return fallback_arr.copy()
    return arr / norm


def delayed_position(
    current_position: np.ndarray,
    pose_history_xyz: Sequence[Iterable[float]] | None,
    latency_steps: int,
) -> tuple[np.ndarray, str]:
    if pose_history_xyz is None or latency_steps <= 0:
        return current_position.copy(), "current"
    if len(pose_history_xyz) <= latency_steps:
        return np.asarray(list(pose_history_xyz[0]), dtype=np.float64).copy(), "history_clamped"
    return np.asarray(list(pose_history_xyz[-1 - latency_steps]), dtype=np.float64).copy(), "history"


def build_vision_observation(
    *,
    object_position: Iterable[float],
    object_axis: Iterable[float],
    object_shape_params: Iterable[float],
    goal_pose_xyz: Iterable[float],
    config: Stage3VisionConfig,
    replay_key: Stage3SensorReplayKey,
    pose_history_xyz: Sequence[Iterable[float]] | None = None,
) -> dict[str, Any]:
    position = np.asarray(list(object_position), dtype=np.float64)
    axis = safe_unit(object_axis, [0.0, 0.0, 1.0])
    shape = np.asarray(list(object_shape_params), dtype=np.float64)
    goal = np.asarray(list(goal_pose_xyz), dtype=np.float64)
    base_position, latency_source = delayed_position(position, pose_history_xyz, int(config.latency_steps))
    pose_noise = replay_key.rng("vision_pose").normal(0.0, float(config.pose_noise_std_m), size=3)
    axis_noise = replay_key.rng("vision_axis").normal(0.0, float(config.axis_noise_std), size=3)
    shape_noise = replay_key.rng("vision_shape").normal(0.0, float(config.shape_noise_std_m), size=3)
    pose_est = base_position + pose_noise
    axis_est = safe_unit(axis + axis_noise, [0.0, 0.0, 1.0])
    shape_est = np.maximum(0.001, shape + shape_noise)
    confidence = float(np.clip(config.confidence_nominal - 8.0 * config.pose_noise_std_m - 0.35 * config.occlusion, 0.0, 1.0))
    return {
        "object_pose_xyz_est": pose_est,
        "object_axis_est": axis_est,
        "object_shape_params_est": shape_est,
        "goal_pose_xyz_est": goal,
        "object_to_goal_est": goal - pose_est,
        "confidence": confidence,
        "occlusion": float(config.occlusion),
        "latency_steps": int(config.latency_steps),
        "noise_std": float(config.pose_noise_std_m),
        "latency_source": latency_source,
    }


def build_tactile_observation(
    *,
    contact_summary: dict[str, Any],
    object_velocity: Iterable[float],
    contact_persistence_steps: int,
    success_max_slip_score: float,
    success_max_crush_risk: float,
    failure_max_penetration_m: float,
    config: Stage3TactileConfig,
) -> dict[str, Any]:
    vel = np.asarray(list(object_velocity), dtype=np.float64)
    tangential = float(np.linalg.norm(vel[:2]))
    downward = float(max(0.0, -vel[2])) if vel.size >= 3 else 0.0
    hand_contacts = int(contact_summary.get("egg_hand_contact_count", 0))
    contact_present = hand_contacts > 0
    max_pen = float(contact_summary.get("max_penetration", 0.0))
    slip_score = 0.0
    if contact_present:
        slip_score = float(
            np.clip(
                (tangential / max(float(config.slip_tangential_scale_mps), 1e-9))
                + (downward / max(float(config.slip_downward_scale_mps), 1e-9)),
                0.0,
                1.0,
            )
        )
    crush_risk = float(np.clip(max_pen / max(float(failure_max_penetration_m), 1e-9), 0.0, 1.0))
    grip_stable = bool(
        contact_present
        and int(contact_persistence_steps) >= int(config.grip_stable_min_persistence_steps)
        and slip_score <= float(success_max_slip_score)
        and crush_risk <= float(success_max_crush_risk)
    )
    return {
        "contact_present": bool(contact_present),
        "contact_regions": list(contact_summary.get("egg_contact_regions", [])),
        "normal_contact_proxy": max_pen,
        "contact_persistence": int(contact_persistence_steps),
        "relative_tangential_motion": tangential,
        "slip_score": slip_score,
        "grip_stable": grip_stable,
        "crush_risk": crush_risk,
        "release_contact_clear": bool(hand_contacts <= int(config.release_max_hand_contacts)),
    }


def sensor_scalars_vector(vision: dict[str, Any], tactile: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            vision["confidence"],
            vision["occlusion"],
            vision["latency_steps"],
            vision["noise_std"],
            float(tactile["contact_present"]),
            tactile["normal_contact_proxy"],
            tactile["contact_persistence"],
            tactile["relative_tangential_motion"],
            tactile["slip_score"],
            float(tactile["grip_stable"]),
            tactile["crush_risk"],
            float(tactile["release_contact_clear"]),
        ],
        dtype=np.float64,
    )


def validate_sensor_observation(vision: dict[str, Any], tactile: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    for field in VISION_FIELD_NAMES:
        if field not in vision:
            failures.append(f"missing vision.{field}")
    for field in TACTILE_FIELD_NAMES:
        if field not in tactile:
            failures.append(f"missing tactile.{field}")
    if failures:
        return {"status": "FAIL", "failures": failures, "warnings": warnings}

    checks = {
        "vision_pose_finite": bool(np.isfinite(vision["object_pose_xyz_est"]).all()),
        "vision_axis_finite": bool(np.isfinite(vision["object_axis_est"]).all()),
        "vision_axis_unit": abs(float(np.linalg.norm(vision["object_axis_est"])) - 1.0) <= 1e-6,
        "vision_shape_positive": bool(np.all(np.asarray(vision["object_shape_params_est"], dtype=np.float64) > 0.0)),
        "vision_confidence_range": 0.0 <= float(vision["confidence"]) <= 1.0,
        "vision_occlusion_range": 0.0 <= float(vision["occlusion"]) <= 1.0,
        "vision_latency_nonnegative": int(vision["latency_steps"]) >= 0,
        "vision_noise_nonnegative": float(vision["noise_std"]) >= 0.0,
        "tactile_contact_persistence_nonnegative": int(tactile["contact_persistence"]) >= 0,
        "tactile_motion_nonnegative": float(tactile["relative_tangential_motion"]) >= 0.0,
        "tactile_slip_range": 0.0 <= float(tactile["slip_score"]) <= 1.0,
        "tactile_crush_range": 0.0 <= float(tactile["crush_risk"]) <= 1.0,
        "tactile_regions_symbolic": isinstance(tactile["contact_regions"], list),
    }
    for key, ok in checks.items():
        if not ok:
            failures.append(key)
    status = "PASS" if not failures else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "failures": failures,
        "warnings": warnings,
    }

