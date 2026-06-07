#!/usr/bin/env python3
"""Hand-relative object pose helpers for Stage3 external sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


PALM_BODY_NAME = "palm_link"
TIP_SITE_NAMES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}


@dataclass(frozen=True)
class HandAnchorConfig:
    palm_body_name: str = PALM_BODY_NAME
    tip_site_names: dict[str, str] | None = None


def _body_id(model, mujoco, name: str) -> int:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if body_id < 0:
        raise ValueError(f"Unknown body: {name!r}")
    return int(body_id)


def _site_id(model, mujoco, name: str) -> int:
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if site_id < 0:
        raise ValueError(f"Unknown site: {name!r}")
    return int(site_id)


def compute_hand_object_relative_pose(
    model,
    data,
    mujoco,
    object_position_world: np.ndarray,
    *,
    config: HandAnchorConfig | None = None,
) -> dict[str, Any]:
    cfg = config or HandAnchorConfig()
    tip_names = cfg.tip_site_names or TIP_SITE_NAMES
    object_pos = np.asarray(object_position_world, dtype=np.float64).reshape(3)

    palm_id = _body_id(model, mujoco, cfg.palm_body_name)
    palm_pos = data.xpos[palm_id].copy()
    palm_xmat = data.xmat[palm_id].reshape(3, 3).copy()
    palm_to_object_world = object_pos - palm_pos
    object_in_palm_frame = palm_xmat.T @ palm_to_object_world

    fingertips: dict[str, Any] = {}
    for label, site_name in tip_names.items():
        site_id = _site_id(model, mujoco, site_name)
        tip_pos = data.site_xpos[site_id].copy()
        tip_to_object = object_pos - tip_pos
        fingertips[label] = {
            "site": site_name,
            "position_world": tip_pos,
            "tip_to_object_world": tip_to_object,
            "object_to_tip_world": -tip_to_object,
            "distance_m": float(np.linalg.norm(tip_to_object)),
        }

    return {
        "object_position_world": object_pos,
        "palm": {
            "body": cfg.palm_body_name,
            "position_world": palm_pos,
            "xmat_world": palm_xmat,
            "palm_to_object_world": palm_to_object_world,
            "object_in_palm_frame": object_in_palm_frame,
            "distance_m": float(np.linalg.norm(palm_to_object_world)),
        },
        "fingertips": fingertips,
    }


def compare_relative_pose(estimated: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    palm_est = np.asarray(estimated["palm"]["object_in_palm_frame"], dtype=np.float64)
    palm_gt = np.asarray(ground_truth["palm"]["object_in_palm_frame"], dtype=np.float64)
    palm_frame_error = float(np.linalg.norm(palm_est - palm_gt))

    fingertip_errors: dict[str, Any] = {}
    for label, gt_tip in ground_truth["fingertips"].items():
        est_tip = estimated["fingertips"][label]
        vec_est = np.asarray(est_tip["tip_to_object_world"], dtype=np.float64)
        vec_gt = np.asarray(gt_tip["tip_to_object_world"], dtype=np.float64)
        dist_est = float(est_tip["distance_m"])
        dist_gt = float(gt_tip["distance_m"])
        fingertip_errors[label] = {
            "tip_to_object_vector_error_m": float(np.linalg.norm(vec_est - vec_gt)),
            "distance_abs_error_m": float(abs(dist_est - dist_gt)),
        }

    vector_errors = [v["tip_to_object_vector_error_m"] for v in fingertip_errors.values()]
    distance_errors = [v["distance_abs_error_m"] for v in fingertip_errors.values()]
    return {
        "palm_frame_object_error_m": palm_frame_error,
        "max_tip_vector_error_m": float(max(vector_errors)) if vector_errors else 0.0,
        "mean_tip_vector_error_m": float(np.mean(vector_errors)) if vector_errors else 0.0,
        "max_tip_distance_error_m": float(max(distance_errors)) if distance_errors else 0.0,
        "fingertips": fingertip_errors,
    }
