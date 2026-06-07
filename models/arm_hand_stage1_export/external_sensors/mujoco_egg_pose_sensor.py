#!/usr/bin/env python3
"""MuJoCo RGB-D/segmentation egg pose sensor for Stage3.

This module estimates the egg center from rendered depth and segmentation. The
MuJoCo ground-truth pose is intentionally not used by the estimator; it is used
only by the experiment runner for numerical validation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml"
DEFAULT_CAMERA = "stage3_egg_closeup"
DEFAULT_EGG_GEOM = "egg_geom"
DEFAULT_EGG_RADII_M = np.array([0.022, 0.032, 0.038], dtype=np.float64)


@dataclass(frozen=True)
class CameraIntrinsics:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    fovy_deg: float


@dataclass(frozen=True)
class EggPoseSensorConfig:
    camera_name: str = DEFAULT_CAMERA
    width: int = 640
    height: int = 480
    egg_geom_name: str = DEFAULT_EGG_GEOM
    egg_radii_m: tuple[float, float, float] = tuple(DEFAULT_EGG_RADII_M.tolist())
    min_mask_pixels: int = 80
    max_depth_m: float = 5.0


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def camera_intrinsics(model, mujoco, camera_name: str, width: int, height: int) -> CameraIntrinsics:
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
    if cam_id < 0:
        raise ValueError(f"Unknown MuJoCo camera: {camera_name!r}")
    fovy = float(model.cam_fovy[cam_id])
    fy = 0.5 * float(height) / np.tan(np.deg2rad(fovy) / 2.0)
    fx = fy
    return CameraIntrinsics(
        width=int(width),
        height=int(height),
        fx=float(fx),
        fy=float(fy),
        cx=float((width - 1) / 2.0),
        cy=float((height - 1) / 2.0),
        fovy_deg=fovy,
    )


def render_rgb_depth_segmentation(model, data, mujoco, config: EggPoseSensorConfig) -> dict[str, np.ndarray]:
    renderer = mujoco.Renderer(model, width=int(config.width), height=int(config.height))
    try:
        renderer.update_scene(data, camera=config.camera_name)
        rgb = renderer.render().copy()

        renderer.enable_depth_rendering()
        renderer.update_scene(data, camera=config.camera_name)
        depth = renderer.render().copy()
        renderer.disable_depth_rendering()

        renderer.enable_segmentation_rendering()
        renderer.update_scene(data, camera=config.camera_name)
        segmentation = renderer.render().copy()
        renderer.disable_segmentation_rendering()
    finally:
        renderer.close()
    return {"rgb": rgb, "depth": depth, "segmentation": segmentation}


def _mask_for_geom(segmentation: np.ndarray, mujoco, geom_id: int) -> np.ndarray:
    obj_ids = segmentation[:, :, 0]
    obj_types = segmentation[:, :, 1]
    geom_type = int(mujoco.mjtObj.mjOBJ_GEOM)
    return (obj_ids == int(geom_id)) & (obj_types == geom_type)


def unproject_mask_to_world(
    depth: np.ndarray,
    mask: np.ndarray,
    intrinsics: CameraIntrinsics,
    camera_pos_world: np.ndarray,
    camera_xmat_world: np.ndarray,
    *,
    max_depth_m: float,
) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return np.zeros((0, 3), dtype=np.float64)
    z_forward = depth[ys, xs].astype(np.float64)
    valid = np.isfinite(z_forward) & (z_forward > 0.0) & (z_forward < float(max_depth_m))
    ys = ys[valid]
    xs = xs[valid]
    z_forward = z_forward[valid]
    if ys.size == 0:
        return np.zeros((0, 3), dtype=np.float64)

    x_cam = (xs.astype(np.float64) - intrinsics.cx) * z_forward / intrinsics.fx
    y_cam = -(ys.astype(np.float64) - intrinsics.cy) * z_forward / intrinsics.fy
    z_cam = -z_forward
    points_camera = np.stack([x_cam, y_cam, z_cam], axis=1)

    camera_xmat_world = np.asarray(camera_xmat_world, dtype=np.float64).reshape(3, 3)
    camera_pos_world = np.asarray(camera_pos_world, dtype=np.float64).reshape(3)
    return camera_pos_world + points_camera @ camera_xmat_world.T


def estimate_ellipsoid_center_known_shape(points_world: np.ndarray, radii_m: np.ndarray) -> tuple[np.ndarray, float]:
    if points_world.shape[0] < 4:
        raise ValueError("Need at least four visible mask depth points to fit an ellipsoid center.")
    radii = np.asarray(radii_m, dtype=np.float64).reshape(3)
    if np.any(radii <= 0.0):
        raise ValueError(f"Invalid ellipsoid radii: {radii}")

    q = np.diag(1.0 / np.square(radii))
    p = np.asarray(points_world, dtype=np.float64)
    a = np.column_stack([2.0 * (p @ q), -np.ones(p.shape[0], dtype=np.float64)])
    b = np.einsum("ij,jk,ik->i", p, q, p)
    solution, *_ = np.linalg.lstsq(a, b, rcond=None)
    center = solution[:3]
    residual = a @ solution - b
    return center, float(np.sqrt(np.mean(np.square(residual))))


def _write_debug_images(
    output_dir: Path,
    label: str,
    rgb: np.ndarray,
    depth: np.ndarray,
    mask: np.ndarray,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
    rgb_path = output_dir / f"{safe}_rgb.png"
    mask_path = output_dir / f"{safe}_mask_overlay.png"
    depth_path = output_dir / f"{safe}_depth.png"

    imageio.imwrite(rgb_path, rgb)

    overlay = rgb.copy()
    overlay[mask] = (0.60 * overlay[mask] + np.array([255, 40, 40]) * 0.40).astype(np.uint8)
    imageio.imwrite(mask_path, overlay)

    depth_img = np.zeros(depth.shape, dtype=np.uint8)
    finite = np.isfinite(depth)
    if finite.any():
        lo = float(np.nanpercentile(depth[finite], 1))
        hi = float(np.nanpercentile(depth[finite], 99))
        if hi > lo:
            depth_img = np.clip((depth - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
    imageio.imwrite(depth_path, depth_img)

    return {"rgb": str(rgb_path), "mask_overlay": str(mask_path), "depth": str(depth_path)}


class MujocoEggPoseSensor:
    def __init__(self, model, mujoco, config: EggPoseSensorConfig | None = None):
        self.model = model
        self.mujoco = mujoco
        self.config = config or EggPoseSensorConfig()
        self.camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, self.config.camera_name)
        self.egg_geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, self.config.egg_geom_name)
        if self.camera_id < 0:
            raise ValueError(f"Unknown camera: {self.config.camera_name!r}")
        if self.egg_geom_id < 0:
            raise ValueError(f"Unknown egg geom: {self.config.egg_geom_name!r}")
        self.intrinsics = camera_intrinsics(
            model,
            mujoco,
            self.config.camera_name,
            self.config.width,
            self.config.height,
        )

    def estimate(self, data, *, debug_dir: Path | None = None, label: str = "sample") -> dict[str, Any]:
        images = render_rgb_depth_segmentation(self.model, data, self.mujoco, self.config)
        mask = _mask_for_geom(images["segmentation"], self.mujoco, self.egg_geom_id)
        debug_images = {}
        if debug_dir is not None:
            debug_images = _write_debug_images(debug_dir, label, images["rgb"], images["depth"], mask)
        mask_pixels = int(mask.sum())
        if mask_pixels < int(self.config.min_mask_pixels):
            return {
                "status": "failed",
                "reason": "too_few_mask_pixels",
                "camera": self.config.camera_name,
                "mask_pixels": mask_pixels,
                "min_mask_pixels": int(self.config.min_mask_pixels),
                "confidence": 0.0,
                "debug_images": debug_images,
            }

        camera_pos = data.cam_xpos[self.camera_id].copy()
        camera_xmat = data.cam_xmat[self.camera_id].reshape(3, 3).copy()
        points_world = unproject_mask_to_world(
            images["depth"],
            mask,
            self.intrinsics,
            camera_pos,
            camera_xmat,
            max_depth_m=float(self.config.max_depth_m),
        )
        if points_world.shape[0] < int(self.config.min_mask_pixels):
            return {
                "status": "failed",
                "reason": "too_few_valid_depth_points",
                "camera": self.config.camera_name,
                "mask_pixels": mask_pixels,
                "valid_depth_points": int(points_world.shape[0]),
                "confidence": 0.0,
                "debug_images": debug_images,
            }

        center_world, fit_residual_rms = estimate_ellipsoid_center_known_shape(
            points_world,
            np.asarray(self.config.egg_radii_m, dtype=np.float64),
        )
        surface_centroid = points_world.mean(axis=0)
        depth_values = images["depth"][mask]
        visibility = float(mask_pixels / (self.config.width * self.config.height))
        residual_score = float(np.exp(-min(fit_residual_rms / 0.25, 20.0)))
        pixel_score = float(min(1.0, mask_pixels / 1500.0))
        confidence = float(np.clip(pixel_score * residual_score, 0.0, 1.0))

        return {
            "status": "ok",
            "camera": self.config.camera_name,
            "position_world_est": center_world,
            "surface_centroid_world": surface_centroid,
            "mask_pixels": mask_pixels,
            "valid_depth_points": int(points_world.shape[0]),
            "visibility_fraction": visibility,
            "confidence": confidence,
            "fit_residual_rms": fit_residual_rms,
            "depth_m": {
                "min": float(np.min(depth_values)),
                "mean": float(np.mean(depth_values)),
                "max": float(np.max(depth_values)),
            },
            "intrinsics": asdict(self.intrinsics),
            "camera_pose": {
                "position_world": camera_pos,
                "xmat_world": camera_xmat,
            },
            "assumptions": {
                "object_shape": "known upright ellipsoid",
                "radii_m": list(self.config.egg_radii_m),
                "mask_source": "MuJoCo segmentation for egg_geom",
            },
            "debug_images": debug_images,
        }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2), encoding="utf-8")
