#!/usr/bin/env python3
"""Stage3.2c noisy MuJoCo virtual-camera perception test.

The sensor still uses MuJoCo-rendered RGB-D/segmentation. This script corrupts
the rendered mask/depth/calibration path to stress the virtual perception gate.
MuJoCo ground truth is used only for evaluation.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import (
    DEFAULT_EGG_RADII_M,
    DEFAULT_SCENE,
    EggPoseSensorConfig,
    _mask_for_geom,
    camera_intrinsics,
    estimate_ellipsoid_center_known_shape,
    json_ready,
    render_rgb_depth_segmentation,
    unproject_mask_to_world,
    write_json,
)


SENSOR_ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = SENSOR_ROOT / "reports" / "stage3_noisy_virtual_camera_perception_v0.md"
DEFAULT_METADATA = SENSOR_ROOT / "metadata" / "stage3_noisy_virtual_camera_perception_v0.json"
DEFAULT_VISUAL_DIR = SENSOR_ROOT / "visual_checks" / "stage3_noisy_virtual_camera_perception_v0"


@dataclass(frozen=True)
class NoiseScenario:
    name: str
    mask_dropout: float = 0.0
    occluder_fraction: float = 0.0
    false_positive_blobs: int = 0
    false_positive_radius_px: int = 0
    depth_noise_std_m: float = 0.0
    calibration_bias_m: tuple[float, float, float] = (0.0, 0.0, 0.0)


def noise_scenarios() -> list[NoiseScenario]:
    return [
        NoiseScenario("clean_reference"),
        NoiseScenario("mask_dropout_30", mask_dropout=0.30),
        NoiseScenario("mask_dropout_55", mask_dropout=0.55),
        NoiseScenario("synthetic_occluder_45", occluder_fraction=0.45),
        NoiseScenario("depth_noise_5mm", depth_noise_std_m=0.005),
        NoiseScenario("false_positive_blob", false_positive_blobs=1, false_positive_radius_px=42),
        NoiseScenario("combined_hard", mask_dropout=0.35, occluder_fraction=0.35, false_positive_blobs=1, false_positive_radius_px=30, depth_noise_std_m=0.004),
        NoiseScenario("calibration_bias_12mm", calibration_bias_m=(0.012, -0.006, 0.003)),
    ]


def scenario_rng(seed: int, trial: str, scenario: str) -> np.random.Generator:
    text = f"{int(seed)}:{trial}:{scenario}"
    value = np.frombuffer(text.encode("utf-8"), dtype=np.uint8).sum(dtype=np.uint64)
    # Use a simple deterministic fold; this is a stress-test generator, not a cryptographic stream.
    folded = int((value * 2654435761) % (2**32))
    return np.random.default_rng(folded)


def apply_mask_dropout(mask: np.ndarray, dropout: float, rng: np.random.Generator) -> np.ndarray:
    if dropout <= 0.0:
        return mask
    keep = rng.random(mask.shape) >= float(dropout)
    return mask & keep


def apply_rect_occluder(mask: np.ndarray, fraction: float) -> np.ndarray:
    if fraction <= 0.0 or not mask.any():
        return mask
    ys, xs = np.nonzero(mask)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    width = max(1, x1 - x0 + 1)
    cut_w = int(round(width * min(max(float(fraction), 0.0), 0.95)))
    out = mask.copy()
    out[y0 : y1 + 1, x0 : min(x1 + 1, x0 + cut_w)] = False
    return out


def apply_false_positive_blobs(mask: np.ndarray, count: int, radius_px: int, rng: np.random.Generator) -> np.ndarray:
    if count <= 0 or radius_px <= 0:
        return mask
    h, w = mask.shape
    out = mask.copy()
    yy, xx = np.ogrid[:h, :w]
    for _ in range(int(count)):
        cx = int(rng.integers(low=max(1, radius_px), high=max(radius_px + 1, w - radius_px)))
        cy = int(rng.integers(low=max(1, radius_px), high=max(radius_px + 1, h - radius_px)))
        blob = (xx - cx) ** 2 + (yy - cy) ** 2 <= int(radius_px) ** 2
        out |= blob
    return out


def corrupt_depth(depth: np.ndarray, mask: np.ndarray, std_m: float, rng: np.random.Generator) -> np.ndarray:
    if std_m <= 0.0 or not mask.any():
        return depth
    out = depth.copy()
    out[mask] = np.maximum(1e-4, out[mask] + rng.normal(0.0, float(std_m), size=int(mask.sum())))
    return out


def median_depth_ray_center(
    depth: np.ndarray,
    mask: np.ndarray,
    intrinsics,
    camera_pos_world: np.ndarray,
    camera_xmat_world: np.ndarray,
    *,
    max_depth_m: float,
    depth_noise_std_m: float,
    min_points: int,
) -> tuple[np.ndarray, float, int] | None:
    """Robust center fallback for depth-noisy masks.

    Least-squares ellipsoid fitting is sensitive when every visible point has
    independent depth noise. This fallback uses the median inlier depth and the
    mask centroid ray to estimate the near surface, then moves one approximate
    egg radius along the camera ray.
    """

    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return None
    z = depth[ys, xs].astype(np.float64)
    valid = np.isfinite(z) & (z > 0.0) & (z < float(max_depth_m))
    if int(valid.sum()) < int(min_points):
        return None
    ys = ys[valid].astype(np.float64)
    xs = xs[valid].astype(np.float64)
    z = z[valid]
    med_z = float(np.median(z))
    abs_dev = np.abs(z - med_z)
    mad = float(np.median(abs_dev))
    robust_sigma = 1.4826 * mad
    depth_window = max(0.012, 4.0 * float(depth_noise_std_m), 4.0 * robust_sigma)
    inlier = abs_dev <= depth_window
    if int(inlier.sum()) < int(min_points):
        return None
    xs_i = xs[inlier]
    ys_i = ys[inlier]
    z_i = z[inlier]
    u = float(np.mean(xs_i))
    v = float(np.mean(ys_i))
    z_forward = float(np.median(z_i))
    x_cam = (u - intrinsics.cx) * z_forward / intrinsics.fx
    y_cam = -(v - intrinsics.cy) * z_forward / intrinsics.fy
    surface_camera = np.asarray([x_cam, y_cam, -z_forward], dtype=np.float64)
    ray_camera = surface_camera / max(1e-9, float(np.linalg.norm(surface_camera)))
    camera_xmat_world = np.asarray(camera_xmat_world, dtype=np.float64).reshape(3, 3)
    camera_pos_world = np.asarray(camera_pos_world, dtype=np.float64).reshape(3)
    surface_world = camera_pos_world + surface_camera @ camera_xmat_world.T
    ray_world = ray_camera @ camera_xmat_world.T
    ray_world = ray_world / max(1e-9, float(np.linalg.norm(ray_world)))
    radius_along_ray = float(np.median(DEFAULT_EGG_RADII_M))
    center_world = surface_world + ray_world * radius_along_ray
    residual = float(np.sqrt(np.mean(np.square(z_i - z_forward))))
    return center_world, residual, int(inlier.sum())


def write_debug_images(output_dir: Path, label: str, rgb: np.ndarray, depth: np.ndarray, clean_mask: np.ndarray, noisy_mask: np.ndarray) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
    rgb_path = output_dir / f"{safe}_rgb.png"
    clean_path = output_dir / f"{safe}_clean_mask_overlay.png"
    noisy_path = output_dir / f"{safe}_noisy_mask_overlay.png"
    depth_path = output_dir / f"{safe}_depth.png"
    imageio.imwrite(rgb_path, rgb)
    clean_overlay = rgb.copy()
    clean_overlay[clean_mask] = (0.60 * clean_overlay[clean_mask] + np.array([40, 255, 40]) * 0.40).astype(np.uint8)
    imageio.imwrite(clean_path, clean_overlay)
    noisy_overlay = rgb.copy()
    noisy_overlay[noisy_mask] = (0.55 * noisy_overlay[noisy_mask] + np.array([255, 40, 40]) * 0.45).astype(np.uint8)
    imageio.imwrite(noisy_path, noisy_overlay)
    finite = np.isfinite(depth)
    depth_img = np.zeros(depth.shape, dtype=np.uint8)
    if finite.any():
        lo = float(np.nanpercentile(depth[finite], 1))
        hi = float(np.nanpercentile(depth[finite], 99))
        if hi > lo:
            depth_img = np.clip((depth - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
    imageio.imwrite(depth_path, depth_img)
    return {
        "rgb": str(rgb_path),
        "clean_mask_overlay": str(clean_path),
        "noisy_mask_overlay": str(noisy_path),
        "depth": str(depth_path),
    }


def estimate_noisy_pose(
    *,
    model,
    data,
    mujoco,
    config: EggPoseSensorConfig,
    scenario: NoiseScenario,
    rng: np.random.Generator,
    debug_dir: Path | None = None,
    label: str = "sample",
) -> dict[str, Any]:
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, config.camera_name)
    geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, config.egg_geom_name)
    intrinsics = camera_intrinsics(model, mujoco, config.camera_name, int(config.width), int(config.height))
    images = render_rgb_depth_segmentation(model, data, mujoco, config)
    clean_mask = _mask_for_geom(images["segmentation"], mujoco, geom_id)
    noisy_mask = apply_mask_dropout(clean_mask, scenario.mask_dropout, rng)
    noisy_mask = apply_rect_occluder(noisy_mask, scenario.occluder_fraction)
    noisy_mask = apply_false_positive_blobs(noisy_mask, scenario.false_positive_blobs, scenario.false_positive_radius_px, rng)
    noisy_depth = corrupt_depth(images["depth"], noisy_mask, scenario.depth_noise_std_m, rng)
    debug_images = {}
    if debug_dir is not None:
        debug_images = write_debug_images(debug_dir, label, images["rgb"], noisy_depth, clean_mask, noisy_mask)

    clean_pixels = int(clean_mask.sum())
    noisy_pixels = int(noisy_mask.sum())
    retained_clean_pixels = int((clean_mask & noisy_mask).sum())
    image_pixels = int(config.width) * int(config.height)
    visibility = float(noisy_pixels / max(1, image_pixels))
    clean_visibility = float(clean_pixels / max(1, image_pixels))
    mask_retention = float(retained_clean_pixels / max(1, clean_pixels))
    if noisy_pixels < int(config.min_mask_pixels):
        return {
            "status": "failed",
            "reason": "too_few_noisy_mask_pixels",
            "scenario": asdict(scenario),
            "mask_pixels": noisy_pixels,
            "clean_mask_pixels": clean_pixels,
            "retained_clean_pixels": retained_clean_pixels,
            "mask_retention_ratio": mask_retention,
            "visibility_fraction": visibility,
            "clean_visibility_fraction": clean_visibility,
            "confidence": 0.0,
            "debug_images": debug_images,
        }

    camera_pos = data.cam_xpos[cam_id].copy() + np.asarray(scenario.calibration_bias_m, dtype=np.float64)
    camera_xmat = data.cam_xmat[cam_id].reshape(3, 3).copy()
    points_world = unproject_mask_to_world(
        noisy_depth,
        noisy_mask,
        intrinsics,
        camera_pos,
        camera_xmat,
        max_depth_m=float(config.max_depth_m),
    )
    if points_world.shape[0] < int(config.min_mask_pixels):
        return {
            "status": "failed",
            "reason": "too_few_valid_depth_points",
            "scenario": asdict(scenario),
            "mask_pixels": noisy_pixels,
            "clean_mask_pixels": clean_pixels,
            "retained_clean_pixels": retained_clean_pixels,
            "mask_retention_ratio": mask_retention,
            "visibility_fraction": visibility,
            "clean_visibility_fraction": clean_visibility,
            "valid_depth_points": int(points_world.shape[0]),
            "confidence": 0.0,
            "debug_images": debug_images,
        }

    center_world, fit_residual_rms = estimate_ellipsoid_center_known_shape(points_world, DEFAULT_EGG_RADII_M)
    estimator = "ellipsoid_lstsq"
    robust_depth_inliers = 0
    robust_depth_residual = float("nan")
    robust_center = median_depth_ray_center(
        noisy_depth,
        noisy_mask,
        intrinsics,
        camera_pos,
        camera_xmat,
        max_depth_m=float(config.max_depth_m),
        depth_noise_std_m=float(scenario.depth_noise_std_m),
        min_points=int(config.min_mask_pixels),
    )
    if robust_center is not None:
        robust_position, robust_residual, robust_inliers = robust_center
        robust_depth_residual = float(robust_residual)
        robust_depth_inliers = int(robust_inliers)
        if float(scenario.depth_noise_std_m) > 0.0 and (fit_residual_rms > 0.050):
            center_world = robust_position
            fit_residual_rms = robust_residual
            estimator = "median_depth_ray_fallback"
    contamination = float(max(0, noisy_pixels - retained_clean_pixels) / max(1, noisy_pixels))
    residual_score = float(np.exp(-min(fit_residual_rms / 0.020, 20.0)))
    pixel_score = float(min(1.0, retained_clean_pixels / 1500.0))
    contamination_score = float(np.clip(1.0 - 2.5 * contamination, 0.0, 1.0))
    retention_score = float(np.clip(mask_retention / 0.70, 0.0, 1.0))
    confidence = float(np.clip(pixel_score * residual_score * contamination_score * retention_score, 0.0, 1.0))
    return {
        "status": "ok",
        "scenario": asdict(scenario),
        "position_world_est": center_world,
        "surface_centroid_world": points_world.mean(axis=0),
        "mask_pixels": noisy_pixels,
        "clean_mask_pixels": clean_pixels,
        "retained_clean_pixels": retained_clean_pixels,
        "mask_retention_ratio": mask_retention,
        "mask_contamination_ratio": contamination,
        "visibility_fraction": visibility,
        "clean_visibility_fraction": clean_visibility,
        "valid_depth_points": int(points_world.shape[0]),
        "confidence": confidence,
        "fit_residual_rms": fit_residual_rms,
        "estimator": estimator,
        "robust_depth_inliers": robust_depth_inliers,
        "robust_depth_residual": robust_depth_residual,
        "depth_noise_std_m": float(scenario.depth_noise_std_m),
        "calibration_bias_m": list(scenario.calibration_bias_m),
        "debug_images": debug_images,
    }


def run_trial_sample(model, data, mujoco, *, trial: sweep.TrialConfig, scenario: NoiseScenario, base_egg_position: np.ndarray, args: argparse.Namespace, debug: bool) -> dict[str, Any]:
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    sweep.reset_episode(model, data, mujoco, egg_position)
    rng = scenario_rng(int(args.seed), trial.name, scenario.name)
    config = EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height), min_mask_pixels=int(args.min_mask_pixels))
    debug_dir = Path(args.visual_dir).resolve() / trial.name if debug else None
    estimate = estimate_noisy_pose(
        model=model,
        data=data,
        mujoco=mujoco,
        config=config,
        scenario=scenario,
        rng=rng,
        debug_dir=debug_dir,
        label=f"{trial.name}_{scenario.name}",
    )
    truth = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    error = math.inf
    accepted = False
    false_confident_bad = False
    if estimate["status"] == "ok":
        pos = np.asarray(estimate["position_world_est"], dtype=np.float64)
        error = float(np.linalg.norm(pos - truth))
        accepted = bool(float(estimate["confidence"]) >= float(args.min_accept_confidence))
        false_confident_bad = bool(accepted and error > float(args.bad_estimate_error))
    should_freeze = not accepted
    freeze_is_safe = bool(should_freeze or error <= float(args.bad_estimate_error))
    return {
        "trial": trial.name,
        "trial_config": asdict(trial),
        "scenario": scenario.name,
        "estimate": estimate,
        "truth_position_world": truth,
        "position_error_m": error,
        "accepted_as_pose_update": accepted,
        "freeze_last_good": should_freeze,
        "freeze_decision_safe": freeze_is_safe,
        "false_confident_bad_estimate": false_confident_bad,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_errors = [
        float(row["position_error_m"])
        for row in rows
        if row["accepted_as_pose_update"] and np.isfinite(float(row["position_error_m"]))
    ]
    ok_errors = [
        float(row["position_error_m"])
        for row in rows
        if row["estimate"]["status"] == "ok" and np.isfinite(float(row["position_error_m"]))
    ]
    by_scenario: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = by_scenario.setdefault(
            row["scenario"],
            {
                "samples": 0,
                "ok": 0,
                "accepted": 0,
                "frozen": 0,
                "false_confident_bad": 0,
                "max_error_m": 0.0,
                "max_accepted_error_m": 0.0,
                "min_confidence": math.inf,
                "mean_confidence_values": [],
            },
        )
        item["samples"] += 1
        item["ok"] += int(row["estimate"]["status"] == "ok")
        item["accepted"] += int(row["accepted_as_pose_update"])
        item["frozen"] += int(row["freeze_last_good"])
        item["false_confident_bad"] += int(row["false_confident_bad_estimate"])
        if np.isfinite(float(row["position_error_m"])):
            item["max_error_m"] = max(float(item["max_error_m"]), float(row["position_error_m"]))
            if row["accepted_as_pose_update"]:
                item["max_accepted_error_m"] = max(float(item["max_accepted_error_m"]), float(row["position_error_m"]))
        conf = float(row["estimate"].get("confidence", 0.0))
        item["min_confidence"] = min(float(item["min_confidence"]), conf)
        item["mean_confidence_values"].append(conf)
    for item in by_scenario.values():
        vals = item.pop("mean_confidence_values")
        item["mean_confidence"] = float(np.mean(vals)) if vals else 0.0
        if item["min_confidence"] == math.inf:
            item["min_confidence"] = 0.0
    return {
        "samples": len(rows),
        "sensor_ok_samples": int(sum(1 for row in rows if row["estimate"]["status"] == "ok")),
        "accepted_updates": int(sum(1 for row in rows if row["accepted_as_pose_update"])),
        "frozen_updates": int(sum(1 for row in rows if row["freeze_last_good"])),
        "false_confident_bad_estimates": int(sum(1 for row in rows if row["false_confident_bad_estimate"])),
        "unsafe_freeze_decisions": int(sum(1 for row in rows if not row["freeze_decision_safe"])),
        "max_accepted_error_m": float(max(accepted_errors)) if accepted_errors else 0.0,
        "mean_accepted_error_m": float(np.mean(accepted_errors)) if accepted_errors else 0.0,
        "max_sensor_ok_error_m": float(max(ok_errors)) if ok_errors else 0.0,
        "scenario_summary": by_scenario,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.2c Noisy Virtual-Camera Perception V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This MuJoCo-only test stresses the virtual perception camera by corrupting the rendered egg mask, depth, and calibration path. It checks whether the perception gate accepts good estimates and freezes unreliable ones instead of producing false confident bad pose updates.\n\n",
        "## Result\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Camera: `{payload['camera']}`\n",
        f"- Trial groups: `{payload['trial_groups']}`\n",
        f"- Scenarios: `{payload['scenario_count']}`\n",
        f"- Samples: `{s['samples']}`\n",
        f"- Accepted updates: `{s['accepted_updates']}`\n",
        f"- Frozen updates: `{s['frozen_updates']}`\n",
        f"- False confident bad estimates: `{s['false_confident_bad_estimates']}`\n",
        f"- Max accepted error: `{s['max_accepted_error_m']:.6f} m`\n",
        f"- Max sensor-ok error: `{s['max_sensor_ok_error_m']:.6f} m`\n\n",
        "## Scenario Summary\n\n",
        "| scenario | samples | ok | accepted | frozen | false-conf bad | mean conf | max accepted err m | max err m |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for name, row in s["scenario_summary"].items():
        lines.append(
            f"| {name} | {row['samples']} | {row['ok']} | {row['accepted']} | {row['frozen']} | "
            f"{row['false_confident_bad']} | {row['mean_confidence']:.3f} | "
            f"{row['max_accepted_error_m']:.6f} | {row['max_error_m']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
        ]
    )
    if payload["status"] == "PASS":
        lines.append("- The noisy virtual-camera gate passed: no corrupted input produced an accepted pose update above the bad-estimate threshold.\n")
    else:
        lines.append("- The noisy virtual-camera gate failed; inspect scenarios with false confident bad estimates before using noisy perception for grasp control.\n")
    lines.extend(
        [
            "- This is still MuJoCo virtual-camera work. It does not use or require real hardware.\n",
            "- Frozen updates mean the controller should reuse last-good pose and rely more on contact/tactile/slip signals after approach.\n\n",
            f"Metadata: `{payload['metadata']}`\n",
            f"Visual checks: `{payload['visual_dir']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage3.2c noisy MuJoCo virtual-camera perception test.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-mask-pixels", type=int, default=80)
    parser.add_argument("--min-accept-confidence", type=float, default=0.55)
    parser.add_argument("--bad-estimate-error", type=float, default=0.015)
    parser.add_argument("--seed", type=int, default=320)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--debug-trials", default="center_nominal,right_high_nominal,lifted_diag")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    debug_trials = {item.strip() for item in str(args.debug_trials).split(",") if item.strip()}
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    rows: list[dict[str, Any]] = []
    scenarios = noise_scenarios()
    trials = sweep.trial_configs()
    for trial in trials:
        for scenario in scenarios:
            row = run_trial_sample(
                model,
                data,
                mujoco,
                trial=trial,
                scenario=scenario,
                base_egg_position=base_egg_position,
                args=args,
                debug=trial.name in debug_trials,
            )
            rows.append(row)
        print(f"{trial.name}: completed {len(scenarios)} noisy camera scenarios")

    summary = summarize(rows)
    status = "PASS" if summary["false_confident_bad_estimates"] == 0 and summary["max_accepted_error_m"] <= float(args.bad_estimate_error) else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "scene": str(scene),
        "camera": str(args.camera),
        "trial_groups": len(trials),
        "scenario_count": len(scenarios),
        "thresholds": {
            "min_accept_confidence": float(args.min_accept_confidence),
            "bad_estimate_error_m": float(args.bad_estimate_error),
        },
        "scenarios": [asdict(item) for item in scenarios],
        "results": rows,
        "summary": summary,
        "metadata": str(metadata),
        "visual_dir": str(visual_dir),
    }
    write_json(metadata, payload)
    report_payload = json.loads(json.dumps(json_ready(payload)))
    write_report(report, report_payload)
    print(f"Status: {status}")
    print(f"False confident bad estimates: {summary['false_confident_bad_estimates']}")
    print(f"Max accepted error: {summary['max_accepted_error_m']:.6f} m")
    print(f"Report: {report}")
    print(f"Metadata: {metadata}")


if __name__ == "__main__":
    main()
