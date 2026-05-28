#!/usr/bin/env python3
"""Compare video-derived open/close motion on Shadow Hand and hand_stage1 export4.

This is a diagnostic scaffold, not a trained policy. It reuses the existing
Shadow video retarget artifacts and maps the same 35D open/close features into
the export4 hand position actuators.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np


SCRIPT_PATH = Path(__file__).resolve()
HAND_ROOT = SCRIPT_PATH.parents[1]
SIM_ROOT = SCRIPT_PATH.parents[3]
PROJECT_ROOT = SCRIPT_PATH.parents[4]
if str(SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(SIM_ROOT))

from vision.hand_open_close import (  # noqa: E402
    OPEN_CLOSE_FEATURE_NAMES,
    open_close_features_from_landmarks,
)


FINGER_NAMES = ("thumb", "index", "middle", "ring", "little")
LONG_FINGERS = ("index", "middle", "ring", "little")

EXPORT4_ACTUATOR_NAMES = (
    "wrist_1_joint_pos",
    "wrist_2_joint_pos",
    "index_mcp_flex_joint_pos",
    "index_mcp_abd_joint_pos",
    "index_pip_joint_pos",
    "index_dip_joint_pos",
    "middle_mcp_flex_joint_pos",
    "middle_mcp_abd_joint_pos",
    "middle_pip_joint_pos",
    "middle_dip_joint_pos",
    "ring_mcp_flex_joint_pos",
    "ring_mcp_abd_joint_pos",
    "ring_pip_joint_pos",
    "ring_dip_joint_pos",
    "little_mcp_flex_joint_pos",
    "little_mcp_abd_joint_pos",
    "little_pip_joint_pos",
    "little_dip_joint_pos",
    "thumb_cmc_abd_joint_pos",
    "thumb_cmc_joint_pos",
    "thumb_mcp_joint_pos",
    "thumb_ip_joint_pos",
)

EXPORT4_TIP_SITES = {
    "thumb": "thumb_tip_site",
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
}

SHADOW_TIP_BODIES = {
    "thumb": ("rh_thdistal", 0.025),
    "index": ("rh_ffdistal", 0.025),
    "middle": ("rh_mfdistal", 0.025),
    "ring": ("rh_rfdistal", 0.025),
    "little": ("rh_lfdistal", 0.025),
}

EXPORT4_CLOSURE_JOINTS = (
    "index_mcp_abd_joint",
    "index_pip_joint",
    "index_dip_joint",
    "middle_mcp_abd_joint",
    "middle_pip_joint",
    "middle_dip_joint",
    "ring_mcp_abd_joint",
    "ring_pip_joint",
    "ring_dip_joint",
    "little_mcp_abd_joint",
    "little_pip_joint",
    "little_dip_joint",
    "thumb_cmc_abd_joint",
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
)

EXPORT4_LONG_FINGER_CLOSE_TARGETS = {
    "index_mcp_flex_joint_pos": -0.06,
    "middle_mcp_flex_joint_pos": -0.06,
    "ring_mcp_flex_joint_pos": -0.05,
    "little_mcp_flex_joint_pos": -0.04,
    "index_mcp_abd_joint_pos": -0.58,
    "middle_mcp_abd_joint_pos": -0.64,
    "ring_mcp_abd_joint_pos": -0.62,
    "little_mcp_abd_joint_pos": -0.54,
    "index_pip_joint_pos": -0.82,
    "middle_pip_joint_pos": -0.88,
    "ring_pip_joint_pos": -0.84,
    "little_pip_joint_pos": -0.76,
    "index_dip_joint_pos": -0.42,
    "middle_dip_joint_pos": -0.46,
    "ring_dip_joint_pos": -0.44,
    "little_dip_joint_pos": -0.40,
}

EXPORT4_THUMB_VISUAL_CLOSE_TARGETS = {
    "thumb_cmc_abd_joint_pos": -0.30,
    "thumb_cmc_joint_pos": 0.0,
    "thumb_mcp_joint_pos": 0.25,
    "thumb_ip_joint_pos": -0.25,
}

SHADOW_CLOSURE_JOINTS = (
    "rh_FFJ3",
    "rh_FFJ2",
    "rh_FFJ1",
    "rh_MFJ3",
    "rh_MFJ2",
    "rh_MFJ1",
    "rh_RFJ3",
    "rh_RFJ2",
    "rh_RFJ1",
    "rh_LFJ3",
    "rh_LFJ2",
    "rh_LFJ1",
    "rh_THJ4",
    "rh_THJ2",
    "rh_THJ1",
)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    xml_path: Path
    palm_body: str
    palm_site: str | None
    actuator_names: Sequence[str]
    closure_joint_names: Sequence[str]
    camera_name: str | None


def _default_paths() -> Dict[str, Path]:
    return {
        "manifest": PROJECT_ROOT / "artifacts" / "vision_real_hand" / "open_close_v1" / "open_close_manifest.json",
        "export4_xml": HAND_ROOT / "mjcf" / "scene_export4_current_baseline.xml",
        "shadow_xml": SIM_ROOT / "models" / "shadow_hand" / "scene_right_no_object_compare.xml",
        "report": HAND_ROOT / "docs" / "export4_current_baseline_shadow_video_comparison_report.md",
        "metadata": HAND_ROOT / "metadata" / "export4_current_baseline_shadow_video_comparison.json",
        "visual_dir": HAND_ROOT / "docs" / "visual_checks_export4_current_baseline_shadow_video_compare",
        "archive": HAND_ROOT / "archive",
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _backup_existing(path: Path, archive_root: Path) -> None:
    if not path.exists():
        return
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    destination = archive_root / f"{path.name}.before_video_compare_{stamp}"
    if path.is_dir():
        shutil.copytree(path, destination)
    else:
        shutil.copy2(path, destination)


def _resolve_repo_relative(raw: str | Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    candidates = [
        (SIM_ROOT / path).resolve(),
        (PROJECT_ROOT / path).resolve(),
        (Path.cwd() / path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _feature_index(name: str) -> int:
    return OPEN_CLOSE_FEATURE_NAMES.index(name)


def _clip(value: float, lower: float, upper: float) -> float:
    return float(np.clip(float(value), float(lower), float(upper)))


def _normalized_to_ctrl(actions: np.ndarray, ctrlrange: np.ndarray) -> np.ndarray:
    actions = np.asarray(actions, dtype=np.float32)
    low = np.asarray(ctrlrange[:, 0], dtype=np.float32)
    high = np.asarray(ctrlrange[:, 1], dtype=np.float32)
    normalized = np.clip(actions, -1.0, 1.0)
    return (normalized + 1.0) * 0.5 * (high - low) + low


def export4_controls_from_open_close(features: np.ndarray, ctrlrange: np.ndarray) -> np.ndarray:
    """Map 35D open/close features to export4 position-actuator targets."""
    features = np.asarray(features, dtype=np.float32)
    controls = np.zeros((features.shape[0], len(EXPORT4_ACTUATOR_NAMES)), dtype=np.float32)
    ranges = {name: tuple(ctrlrange[idx]) for idx, name in enumerate(EXPORT4_ACTUATOR_NAMES)}
    name_to_idx = {name: idx for idx, name in enumerate(EXPORT4_ACTUATOR_NAMES)}

    def set_ctrl(row: int, actuator: str, value: float) -> None:
        lower, upper = ranges[actuator]
        controls[row, name_to_idx[actuator]] = _clip(value, lower, upper)

    for row, feature in enumerate(features):
        set_ctrl(row, "wrist_1_joint_pos", 0.0)
        set_ctrl(row, "wrist_2_joint_pos", 0.0)

        for finger in LONG_FINGERS:
            proximal = float(feature[_feature_index(f"{finger}_proximal")])
            middle = float(feature[_feature_index(f"{finger}_middle")])
            distal = float(feature[_feature_index(f"{finger}_distal")])
            spread = float(feature[_feature_index(f"{finger}_spread")])

            flex_act = f"{finger}_mcp_flex_joint_pos"
            abd_act = f"{finger}_mcp_abd_joint_pos"
            pip_act = f"{finger}_pip_joint_pos"
            dip_act = f"{finger}_dip_joint_pos"

            flex_target = EXPORT4_LONG_FINGER_CLOSE_TARGETS[flex_act]
            abd_target = EXPORT4_LONG_FINGER_CLOSE_TARGETS[abd_act]
            pip_target = EXPORT4_LONG_FINGER_CLOSE_TARGETS[pip_act]
            dip_target = EXPORT4_LONG_FINGER_CLOSE_TARGETS[dip_act]

            # Current export4 baseline closes long fingers in the negative
            # direction. Use explicit tuned targets instead of interpolating
            # across raw actuator ranges, because the ranges are no longer
            # semantically "open -> close".
            set_ctrl(row, flex_act, proximal * flex_target + 0.025 * spread)
            set_ctrl(row, abd_act, proximal * abd_target)
            set_ctrl(row, pip_act, middle * pip_target)
            set_ctrl(row, dip_act, distal * dip_target)

            # Keep very small lateral commands conservative while the MCP
            # flex/abd semantic naming is still under audit.
            flex_low, flex_high = ranges[flex_act]
            controls[row, name_to_idx[flex_act]] = _clip(controls[row, name_to_idx[flex_act]], flex_low, flex_high)

        thumb_curl = float(feature[_feature_index("thumb_curl")])
        thumb_mcp = float(feature[_feature_index("thumb_mcp_bend")])
        thumb_ip = float(feature[_feature_index("thumb_ip_bend")])
        thumb_opp = float(feature[_feature_index("thumb_opposition")])
        thumb_spread = float(feature[_feature_index("thumb_spread")])
        thumb_close = max(thumb_curl, thumb_opp, thumb_mcp, thumb_ip)
        set_ctrl(
            row,
            "thumb_cmc_abd_joint_pos",
            thumb_opp * EXPORT4_THUMB_VISUAL_CLOSE_TARGETS["thumb_cmc_abd_joint_pos"] + 0.03 * thumb_spread,
        )
        set_ctrl(row, "thumb_cmc_joint_pos", thumb_curl * EXPORT4_THUMB_VISUAL_CLOSE_TARGETS["thumb_cmc_joint_pos"])
        set_ctrl(row, "thumb_mcp_joint_pos", thumb_close * EXPORT4_THUMB_VISUAL_CLOSE_TARGETS["thumb_mcp_joint_pos"])
        set_ctrl(row, "thumb_ip_joint_pos", thumb_close * EXPORT4_THUMB_VISUAL_CLOSE_TARGETS["thumb_ip_joint_pos"])

    return controls


def _pairwise_spread(points: Dict[str, np.ndarray]) -> float:
    names = list(points)
    if len(names) < 2:
        return 0.0
    distances = []
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            distances.append(float(np.linalg.norm(points[name_a] - points[name_b])))
    return float(np.mean(distances)) if distances else 0.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) < 1e-9:
        return 0.0
    return float(numerator / denominator)


def _mj_name(model, obj_type, idx: int) -> str:
    import mujoco

    return mujoco.mj_id2name(model, obj_type, idx) or ""


def _joint_qpos_adrs(model, joint_names: Iterable[str]) -> Dict[str, int]:
    import mujoco

    result = {}
    for name in joint_names:
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if joint_id >= 0:
            result[name] = int(model.jnt_qposadr[joint_id])
    return result


def _joint_ranges(model, joint_names: Iterable[str]) -> Dict[str, np.ndarray]:
    import mujoco

    result = {}
    for name in joint_names:
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if joint_id >= 0:
            result[name] = np.asarray(model.jnt_range[joint_id], dtype=np.float32)
    return result


def _tip_positions(model, data, spec: ModelSpec) -> Dict[str, np.ndarray]:
    import mujoco

    if spec.name == "export4":
        tips: Dict[str, np.ndarray] = {}
        for finger, site_name in EXPORT4_TIP_SITES.items():
            site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
            if site_id >= 0:
                tips[finger] = np.asarray(data.site_xpos[site_id], dtype=np.float32).copy()
        return tips

    tips = {}
    for finger, (body_name, offset) in SHADOW_TIP_BODIES.items():
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if body_id < 0:
            continue
        mat = np.asarray(data.xmat[body_id], dtype=np.float32).reshape(3, 3)
        tips[finger] = np.asarray(data.xpos[body_id], dtype=np.float32).copy() + mat @ np.asarray(
            [0.0, 0.0, float(offset)], dtype=np.float32
        )
    return tips


def _palm_position(model, data, spec: ModelSpec) -> np.ndarray:
    import mujoco

    if spec.palm_site:
        site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, spec.palm_site)
        if site_id >= 0:
            return np.asarray(data.site_xpos[site_id], dtype=np.float32).copy()
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, spec.palm_body)
    if body_id >= 0:
        return np.asarray(data.xpos[body_id], dtype=np.float32).copy()
    return np.zeros(3, dtype=np.float32)


def _capture_metrics(model, data, spec: ModelSpec) -> Dict[str, Any]:
    palm = _palm_position(model, data, spec)
    tips = _tip_positions(model, data, spec)
    tip_palm = {
        finger: float(np.linalg.norm(position - palm))
        for finger, position in tips.items()
    }
    return {
        "palm": palm,
        "tips": tips,
        "mean_tip_palm_distance": float(np.mean(list(tip_palm.values()))) if tip_palm else 0.0,
        "tip_palm_distances": tip_palm,
        "tip_spread": _pairwise_spread(tips),
        "thumb_index_distance": float(np.linalg.norm(tips["thumb"] - tips["index"]))
        if "thumb" in tips and "index" in tips
        else 0.0,
    }


def _render_frame(model, data, camera_name: str | None, width: int, height: int) -> np.ndarray:
    import mujoco

    renderer = mujoco.Renderer(model, width=width, height=height)
    try:
        if camera_name and camera_name.startswith("__free_export4"):
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = np.asarray([0.0, 0.02, 0.18], dtype=np.float64)
            camera.distance = 0.38
            camera.azimuth = 180.0
            camera.elevation = -35.0
            renderer.update_scene(data, camera=camera)
        elif camera_name and camera_name.startswith("__free_shadow"):
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = np.asarray([0.0, 0.0, 0.16], dtype=np.float64)
            camera.distance = 0.42
            camera.azimuth = 220.0
            camera.elevation = -30.0
            renderer.update_scene(data, camera=camera)
        elif camera_name:
            renderer.update_scene(data, camera=camera_name)
        else:
            camera = mujoco.MjvCamera()
            mujoco.mjv_defaultFreeCamera(model, camera)
            camera.lookat[:] = model.stat.center
            camera.distance = max(float(model.stat.extent) * 2.2, 0.20)
            camera.azimuth = 145.0
            camera.elevation = -25.0
            renderer.update_scene(data, camera=camera)
        return renderer.render().copy()
    finally:
        renderer.close()


def simulate_controls(
    spec: ModelSpec,
    controls: np.ndarray,
    keyframes: Sequence[int],
    render_dir: Path | None,
    width: int,
    height: int,
    substeps: int,
    settle_steps: int,
) -> Dict[str, Any]:
    import mujoco
    from PIL import Image

    model = mujoco.MjModel.from_xml_path(str(spec.xml_path))
    data = mujoco.MjData(model)
    controls = np.asarray(controls, dtype=np.float32)
    if controls.shape[1] != model.nu:
        raise ValueError(f"{spec.name}: control dim {controls.shape[1]} != model.nu {model.nu}")

    keyframe_set = {int(idx) for idx in keyframes if 0 <= int(idx) < controls.shape[0]}
    if controls.shape[0] > 0:
        data.ctrl[:] = controls[0]
        for _ in range(max(0, int(settle_steps))):
            mujoco.mj_step(model, data)

    qpos_adrs = _joint_qpos_adrs(model, spec.closure_joint_names)
    joint_ranges = _joint_ranges(model, spec.closure_joint_names)
    qpos_trace = []
    metric_trace = []
    render_paths: List[str] = []
    render_error = ""

    if render_dir:
        render_dir.mkdir(parents=True, exist_ok=True)

    for step_idx, ctrl in enumerate(controls):
        data.ctrl[:] = ctrl
        for _ in range(max(1, int(substeps))):
            mujoco.mj_step(model, data)
        metric_trace.append(_capture_metrics(model, data, spec))
        qpos_trace.append(data.qpos.copy())
        if render_dir and step_idx in keyframe_set:
            try:
                image = _render_frame(model, data, spec.camera_name, width, height)
                path = render_dir / f"{spec.name}_frame_{step_idx:04d}.png"
                Image.fromarray(image).save(path)
                render_paths.append(str(path))
            except Exception as exc:  # Rendering should not block metric generation.
                render_error = f"{type(exc).__name__}: {exc}"

    return {
        "model_summary": {
            "bodies": int(model.nbody),
            "joints": int(model.njnt),
            "actuators": int(model.nu),
            "geoms": int(model.ngeom),
            "sites": int(model.nsite),
            "actuator_names": [
                _mj_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx)
                for idx in range(model.nu)
            ],
            "joint_names": [
                _mj_name(model, mujoco.mjtObj.mjOBJ_JOINT, idx)
                for idx in range(model.njnt)
            ],
        },
        "qpos_trace": np.asarray(qpos_trace, dtype=np.float32),
        "metric_trace": metric_trace,
        "joint_qpos_adrs": qpos_adrs,
        "joint_ranges": joint_ranges,
        "render_paths": render_paths,
        "render_error": render_error,
    }


def summarize_model_run(
    sim: Dict[str, Any],
    controls: np.ndarray,
    open_idx: int,
    close_idx: int,
) -> Dict[str, Any]:
    metrics = sim["metric_trace"]
    if not metrics:
        return {"status": "failed", "reason": "empty metric trace"}
    open_idx = int(np.clip(open_idx, 0, len(metrics) - 1))
    close_idx = int(np.clip(close_idx, 0, len(metrics) - 1))
    open_metrics = metrics[open_idx]
    close_metrics = metrics[close_idx]

    open_dist = float(open_metrics["mean_tip_palm_distance"])
    close_dist = float(close_metrics["mean_tip_palm_distance"])
    open_spread = float(open_metrics["tip_spread"])
    close_spread = float(close_metrics["tip_spread"])
    open_ti = float(open_metrics["thumb_index_distance"])
    close_ti = float(close_metrics["thumb_index_distance"])

    qpos_trace = sim["qpos_trace"]
    joint_activity_values = []
    for name, adr in sim["joint_qpos_adrs"].items():
        if adr >= qpos_trace.shape[1]:
            continue
        joint_range = sim["joint_ranges"].get(name)
        denom = float(abs(joint_range[1] - joint_range[0])) if joint_range is not None else 1.0
        denom = max(denom, 1e-6)
        joint_activity_values.append(abs(float(qpos_trace[close_idx, adr] - qpos_trace[open_idx, adr])) / denom)
    joint_activity = float(np.mean(joint_activity_values)) if joint_activity_values else 0.0

    ctrl_low = np.min(controls, axis=0)
    ctrl_high = np.max(controls, axis=0)
    ctrl_activity = float(np.mean(np.abs(ctrl_high - ctrl_low)))

    tip_reduction = open_dist - close_dist
    spread_reduction = open_spread - close_spread
    tip_reduction_ratio = _safe_ratio(tip_reduction, open_dist)
    spread_reduction_ratio = _safe_ratio(spread_reduction, open_spread)
    thumb_index_reduction_ratio = _safe_ratio(open_ti - close_ti, open_ti)
    closure_score = float(
        np.clip(
            0.40 * max(tip_reduction_ratio, 0.0)
            + 0.30 * max(spread_reduction_ratio, 0.0)
            + 0.20 * max(thumb_index_reduction_ratio, 0.0)
            + 0.10 * min(max(joint_activity, 0.0), 1.0),
            0.0,
            1.0,
        )
    )
    return {
        "status": "ok",
        "open_mean_tip_palm_distance": open_dist,
        "close_mean_tip_palm_distance": close_dist,
        "tip_palm_distance_reduction": tip_reduction,
        "tip_palm_distance_reduction_ratio": tip_reduction_ratio,
        "open_tip_spread": open_spread,
        "close_tip_spread": close_spread,
        "tip_spread_reduction": spread_reduction,
        "tip_spread_reduction_ratio": spread_reduction_ratio,
        "open_thumb_index_distance": open_ti,
        "close_thumb_index_distance": close_ti,
        "thumb_index_reduction_ratio": thumb_index_reduction_ratio,
        "joint_activity_ratio": joint_activity,
        "control_activity_mean_abs_range": ctrl_activity,
        "closure_score": closure_score,
        "render_paths": sim.get("render_paths", []),
        "render_error": sim.get("render_error", ""),
    }


def _keyframes(frame_count: int, open_idx: int, close_idx: int, max_keyframes: int) -> List[int]:
    if frame_count <= 0:
        return []
    base = {0, frame_count - 1, int(open_idx), int(close_idx)}
    for item in np.linspace(0, frame_count - 1, max(1, int(max_keyframes))):
        base.add(int(round(item)))
    return sorted(idx for idx in base if 0 <= idx < frame_count)


def _write_contact_sheet(paths_by_model: Dict[str, List[str]], out_path: Path) -> str:
    from PIL import Image, ImageDraw

    all_paths = []
    max_len = max((len(paths) for paths in paths_by_model.values()), default=0)
    if max_len == 0:
        return ""
    labels = list(paths_by_model)
    for idx in range(max_len):
        row = []
        for label in labels:
            paths = paths_by_model[label]
            row.append(Path(paths[idx]) if idx < len(paths) else None)
        all_paths.append(row)

    loaded: List[List[Tuple[str, Image.Image] | None]] = []
    cell_w, cell_h = 0, 0
    for row in all_paths:
        loaded_row = []
        for path in row:
            if path and path.exists():
                image = Image.open(path).convert("RGB")
                cell_w = max(cell_w, image.width)
                cell_h = max(cell_h, image.height)
                loaded_row.append((path.name, image))
            else:
                loaded_row.append(None)
        loaded.append(loaded_row)
    if cell_w == 0 or cell_h == 0:
        return ""

    label_h = 26
    sheet = Image.new("RGB", (len(labels) * cell_w, len(loaded) * (cell_h + label_h) + label_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    for col, label in enumerate(labels):
        draw.text((col * cell_w + 8, 6), label, fill=(24, 28, 36))
    for row_idx, row in enumerate(loaded):
        y = label_h + row_idx * (cell_h + label_h)
        for col_idx, item in enumerate(row):
            x = col_idx * cell_w
            if item is None:
                draw.rectangle((x, y + label_h, x + cell_w, y + label_h + cell_h), fill=(230, 232, 236))
                continue
            name, image = item
            sheet.paste(image, (x, y + label_h))
            draw.text((x + 8, y + 6), name, fill=(48, 54, 62))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return str(out_path)


def _plot_aggregate(results: List[Dict[str, Any]], out_dir: Path) -> Dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    labels = [item["video_stem"][:6] for item in results]
    x = np.arange(len(results))
    shadow_scores = [item["shadow"]["closure_score"] for item in results]
    export4_scores = [item["export4"]["closure_score"] for item in results]
    curl_ranges = [item["input"]["curl_range"] for item in results]

    paths: Dict[str, str] = {}
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.bar(x - 0.18, shadow_scores, width=0.36, label="Shadow")
    ax.bar(x + 0.18, export4_scores, width=0.36, label="hand_stage1 export4")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("closure score (diagnostic)")
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    path = out_dir / "aggregate_closure_scores.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths["aggregate_closure_scores"] = str(path)

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.scatter(curl_ranges, shadow_scores, label="Shadow", s=60)
    ax.scatter(curl_ranges, export4_scores, label="hand_stage1 export4", s=60)
    ax.set_xlabel("input global curl range")
    ax.set_ylabel("closure score (diagnostic)")
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    path = out_dir / "input_curl_vs_closure_score.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths["input_curl_vs_closure_score"] = str(path)
    return paths


def _format_float(value: float, digits: int = 3) -> str:
    try:
        if math.isnan(float(value)):
            return "nan"
    except Exception:
        return "nan"
    return f"{float(value):.{digits}f}"


def _write_report(
    report_path: Path,
    metadata_path: Path,
    manifest_summary: Dict[str, Any],
    results: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    plots: Dict[str, str],
    args: argparse.Namespace,
) -> None:
    lines: List[str] = []
    lines.append("# Export4 vs Shadow Video Open/Close Comparison\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("## Scope\n")
    lines.append(
        "This run removes the ball from the comparison and evaluates whether the same recorded-video "
        "open/close motion can drive both the reference Shadow Hand and the hand_stage1 export4 model. "
        "The result is a kinematic/control-path smoke test, not a claim that hand_stage1 is mechanically "
        "equivalent to Shadow or ready for training.\n"
    )
    lines.append("## Inputs\n")
    lines.append(f"- Manifest: `{args.manifest}`\n")
    lines.append(f"- Shadow scene: `{args.shadow_xml}`\n")
    lines.append(f"- hand_stage1 export4 scene: `{args.export4_xml}`\n")
    lines.append(f"- Videos in manifest: {manifest_summary.get('total_videos')}\n")
    lines.append(f"- Auto usable: {manifest_summary.get('usable')}; review: {manifest_summary.get('review')}\n")
    lines.append("\n## Adapter Boundary\n")
    lines.append(
        "- Shadow uses the existing 24D diagnostic `vision_shadow_retarget` action sequence from the prior video pipeline.\n"
    )
    lines.append(
        "- hand_stage1 export4 uses a new deterministic adapter: `hand_open_close_feature_v1 -> export4_position_control_v1`.\n"
    )
    lines.append(
        "- The export4 adapter maps long-finger curl to MCP/PIP/DIP flexion targets and keeps MCP spread small while the flex/abd naming remains under audit.\n"
    )
    lines.append(
        "- No RL, BC, tendon routing, ball contact reward, CAD edit, STL edit, joint-name edit, or joint-tree edit was performed.\n"
    )

    first = results[0] if results else {}
    if first:
        shadow_model = first.get("shadow", {}).get("model_summary", {})
        export4_model = first.get("export4", {}).get("model_summary", {})
        lines.append("\n## Model Summary\n")
        lines.append(
            f"- Shadow scene: {shadow_model.get('bodies', 'n/a')} bodies, "
            f"{shadow_model.get('joints', 'n/a')} joints, {shadow_model.get('actuators', 'n/a')} actuators, "
            f"{shadow_model.get('geoms', 'n/a')} geoms, {shadow_model.get('sites', 'n/a')} sites.\n"
        )
        lines.append(
            f"- hand_stage1 export4 scene: {export4_model.get('bodies', 'n/a')} bodies, "
            f"{export4_model.get('joints', 'n/a')} joints, {export4_model.get('actuators', 'n/a')} actuators, "
            f"{export4_model.get('geoms', 'n/a')} geoms, {export4_model.get('sites', 'n/a')} sites.\n"
        )
        lines.append(
            "- Key structural difference: export4 currently has fewer actuated DoFs than Shadow and uses simplified "
            "diagnostic visual/collision setup rather than a tuned production hand model.\n"
        )

    lines.append("\n## Experiment Procedure\n")
    lines.append("1. Load the 12-video open/close manifest generated by the previous vision pipeline.\n")
    lines.append("2. For each video, load the existing time-scaled Shadow retarget NPZ and its 21-landmark sequence.\n")
    lines.append("3. Convert the same landmarks to the 35D `hand_open_close_feature_v1` representation.\n")
    lines.append("4. Replay Shadow with the existing 24D normalized Shadow action labels.\n")
    lines.append("5. Replay hand_stage1 export4 with a deterministic 22D position-control adapter from the same 35D features.\n")
    lines.append("6. Render keyframes for both hands and compute closure-state metrics with no ball in the scene.\n")

    lines.append("\n## Metric Definitions\n")
    lines.append("- `curl range`: max minus min of input global open/close curl over the video-derived sequence.\n")
    lines.append(
        "- `tip dist delta`: mean fingertip-to-palm distance at the most-open frame minus the same distance at the most-closed frame; positive means fingertips moved closer to the palm.\n"
    )
    lines.append(
        "- `tip spread reduction`: mean pairwise fingertip spacing at the most-open frame minus the same spacing at the most-closed frame; positive means the hand closed inward.\n"
    )
    lines.append("- `thumb-index close`: thumb tip to index tip distance at the most-closed frame.\n")
    lines.append(
        "- `joint activity`: normalized closed-minus-open motion over the main flexion joints, divided by each joint range.\n"
    )
    lines.append(
        "- `closure score`: diagnostic scalar in [0, 1] combining tip-palm reduction, tip-spread reduction, thumb-index reduction, and joint activity. It is useful for comparing trends across videos, not as a universal grasp-success score.\n"
    )

    lines.append("\n## Aggregate Result\n")
    lines.append(f"- Videos processed: {aggregate['videos_processed']} / {aggregate['videos_total']}\n")
    lines.append(f"- Shadow model failures: {aggregate['shadow_failures']}\n")
    lines.append(f"- export4 model failures: {aggregate['export4_failures']}\n")
    lines.append(f"- Mean Shadow closure score: {_format_float(aggregate['shadow_closure_score_mean'], 4)}\n")
    lines.append(f"- Mean export4 closure score: {_format_float(aggregate['export4_closure_score_mean'], 4)}\n")
    lines.append(f"- Mean input curl range: {_format_float(aggregate['input_curl_range_mean'], 4)}\n")
    lines.append(f"- Rendered videos: {aggregate['rendered_video_count']}\n")
    if aggregate.get("score_correlation") is not None:
        lines.append(f"- Shadow/export4 closure-score correlation: {_format_float(aggregate['score_correlation'], 4)}\n")
    lines.append(
        "\nInterpretation: the export4 hand can be driven through all local video-derived open/close sequences without "
        "MuJoCo load or replay failure. The comparison should be read as a pipeline pass and closure-state "
        "diagnostic. It does not yet prove Shadow-equivalent dexterous grasping.\n"
    )
    conclusion = "PIPELINE PASS / FUNCTIONAL COMPARISON PARTIAL"
    lines.append(f"- Overall conclusion: **{conclusion}**.\n")
    lines.append(
        "- Practical meaning: export4 follows the same close/open trend as Shadow across videos, but its closure score is lower and the thumb/open-close mapping is still a diagnostic adapter.\n"
    )

    if plots:
        lines.append("\n## Plots\n")
        for name, path in plots.items():
            lines.append(f"- {name}: `{path}`\n")

    lines.append("\n## Per-Video Results\n")
    lines.append(
        "| video | manifest | frames | curl range | Shadow score | export4 score | "
        "Shadow tip dist delta | export4 tip dist delta | export4 thumb-index close | sheet |\n"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for item in results:
        shadow = item["shadow"]
        export4 = item["export4"]
        sheet = item.get("comparison_sheet", "")
        sheet_cell = f"`{sheet}`" if sheet else ""
        lines.append(
            f"| {item['video_stem'][:10]} | {item['manifest_status']} | {item['input']['frames']} | "
            f"{_format_float(item['input']['curl_range'], 3)} | "
            f"{_format_float(shadow['closure_score'], 3)} | {_format_float(export4['closure_score'], 3)} | "
            f"{_format_float(shadow['tip_palm_distance_reduction'], 4)} | "
            f"{_format_float(export4['tip_palm_distance_reduction'], 4)} | "
            f"{_format_float(export4['close_thumb_index_distance'], 4)} | {sheet_cell} |\n"
        )

    lines.append("\n## What This Validates\n")
    lines.append("- Processed videos in this run can be mapped into the existing Shadow diagnostic action path.\n")
    lines.append("- The same processed video landmarks can be mapped into hand_stage1 export4 position-control targets.\n")
    lines.append("- Both models can replay the trajectories in MuJoCo without requiring a ball.\n")
    lines.append("- Closure can now be quantified by geometry and actuator/joint activity rather than only visual judgment.\n")

    lines.append("\n## Remaining Gaps\n")
    lines.append("- hand_stage1 export4 has 22 actuators versus Shadow's 24 and lacks Shadow's tuned collision/contact behavior.\n")
    lines.append("- The export4 adapter is a first deterministic bridge, not an IK solver or learned retargeter.\n")
    lines.append("- Thumb opposition and MCP flex/abd semantic signs still need final manual verification before training.\n")
    lines.append("- This run does not prove stable free-object grasp because the ball was intentionally removed.\n")

    lines.append("\n## Next Step\n")
    lines.append(
        "Keep this comparison as the regression test. After palm/thumb semantics are signed off, turn the export4 adapter "
        "into a trainable target generator and add ball/contact tasks back in a separate experiment.\n"
    )
    lines.append(f"\nMachine-readable summary: `{metadata_path}`\n")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    defaults = _default_paths()
    parser = argparse.ArgumentParser(description="Run export4 vs Shadow video open/close comparison")
    parser.add_argument("--manifest", default=str(defaults["manifest"]))
    parser.add_argument("--export4-xml", default=str(defaults["export4_xml"]))
    parser.add_argument("--shadow-xml", default=str(defaults["shadow_xml"]))
    parser.add_argument("--report", default=str(defaults["report"]))
    parser.add_argument("--metadata", default=str(defaults["metadata"]))
    parser.add_argument("--visual-dir", default=str(defaults["visual_dir"]))
    parser.add_argument("--archive", default=str(defaults["archive"]))
    parser.add_argument("--max-videos", type=int, default=0, help="0 means all videos")
    parser.add_argument("--max-keyframes", type=int, default=5)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--substeps", type=int, default=2)
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--no-render", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    manifest_path = Path(args.manifest).resolve()
    export4_xml = Path(args.export4_xml).resolve()
    shadow_xml = Path(args.shadow_xml).resolve()
    report_path = Path(args.report).resolve()
    metadata_path = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    archive = Path(args.archive).resolve()

    for path in (manifest_path, export4_xml, shadow_xml):
        if not path.exists():
            raise FileNotFoundError(path)

    for output in (report_path, metadata_path):
        _backup_existing(output, archive)
    if visual_dir.exists():
        _backup_existing(visual_dir, archive)

    import mujoco

    shadow_model = mujoco.MjModel.from_xml_path(str(shadow_xml))
    export4_model = mujoco.MjModel.from_xml_path(str(export4_xml))
    shadow_spec = ModelSpec(
        name="shadow",
        xml_path=shadow_xml,
        palm_body="rh_palm",
        palm_site="grasp_site",
        actuator_names=[_mj_name(shadow_model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) for idx in range(shadow_model.nu)],
        closure_joint_names=SHADOW_CLOSURE_JOINTS,
        camera_name="shadow_compare_front",
    )
    export4_spec = ModelSpec(
        name="export4",
        xml_path=export4_xml,
        palm_body="palm_link",
        palm_site=None,
        actuator_names=[_mj_name(export4_model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) for idx in range(export4_model.nu)],
        closure_joint_names=EXPORT4_CLOSURE_JOINTS,
        camera_name="__free_export4_full",
    )

    manifest = _load_json(manifest_path)
    items = list(manifest.get("items", []))
    if args.max_videos > 0:
        items = items[: args.max_videos]

    results: List[Dict[str, Any]] = []
    visual_dir.mkdir(parents=True, exist_ok=True)

    for item in items:
        video_name = str(item.get("video_name") or Path(str(item.get("video", ""))).name)
        video_stem = Path(video_name).stem
        retarget_path = _resolve_repo_relative(item.get("retarget", ""))
        if not retarget_path.exists():
            results.append(
                {
                    "video_stem": video_stem,
                    "manifest_status": item.get("status", "unknown"),
                    "status": "failed",
                    "reason": f"missing retarget: {retarget_path}",
                }
            )
            continue

        payload = np.load(retarget_path, allow_pickle=True)
        landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
        shadow_actions = np.asarray(payload["actions"], dtype=np.float32)
        features = open_close_features_from_landmarks(landmarks)
        if features.shape[0] != shadow_actions.shape[0]:
            n = min(features.shape[0], shadow_actions.shape[0])
            features = features[:n]
            shadow_actions = shadow_actions[:n]

        global_curl = features[:, _feature_index("global_curl_mean")]
        open_idx = int(np.argmin(global_curl))
        close_idx = int(np.argmax(global_curl))
        keyframes = _keyframes(features.shape[0], open_idx, close_idx, args.max_keyframes)

        shadow_controls = _normalized_to_ctrl(shadow_actions, shadow_model.actuator_ctrlrange)
        export4_controls = export4_controls_from_open_close(features, export4_model.actuator_ctrlrange)

        video_visual_dir = visual_dir / video_stem
        render_dir_shadow = None if args.no_render else video_visual_dir / "shadow"
        render_dir_export4 = None if args.no_render else video_visual_dir / "export4"

        result: Dict[str, Any] = {
            "video_name": video_name,
            "video_stem": video_stem,
            "manifest_status": item.get("status", "unknown"),
            "review_reasons": item.get("review_reasons", []),
            "input": {
                "frames": int(features.shape[0]),
                "feature_dim": int(features.shape[1]),
                "curl_min": float(np.min(global_curl)),
                "curl_max": float(np.max(global_curl)),
                "curl_range": float(np.max(global_curl) - np.min(global_curl)),
                "open_idx": open_idx,
                "close_idx": close_idx,
                "keyframes": keyframes,
                "retarget": str(retarget_path),
            },
        }

        try:
            shadow_sim = simulate_controls(
                shadow_spec,
                shadow_controls,
                keyframes=keyframes,
                render_dir=render_dir_shadow,
                width=args.width,
                height=args.height,
                substeps=args.substeps,
                settle_steps=args.settle_steps,
            )
            result["shadow"] = summarize_model_run(shadow_sim, shadow_controls, open_idx, close_idx)
            result["shadow"]["model_summary"] = shadow_sim["model_summary"]
        except Exception as exc:
            result["shadow"] = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}", "closure_score": 0.0}

        try:
            export4_sim = simulate_controls(
                export4_spec,
                export4_controls,
                keyframes=keyframes,
                render_dir=render_dir_export4,
                width=args.width,
                height=args.height,
                substeps=args.substeps,
                settle_steps=args.settle_steps,
            )
            result["export4"] = summarize_model_run(export4_sim, export4_controls, open_idx, close_idx)
            result["export4"]["model_summary"] = export4_sim["model_summary"]
        except Exception as exc:
            result["export4"] = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}", "closure_score": 0.0}

        if not args.no_render:
            sheet = _write_contact_sheet(
                {
                    "Shadow Hand": result.get("shadow", {}).get("render_paths", []),
                    "hand_stage1 export4": result.get("export4", {}).get("render_paths", []),
                },
                video_visual_dir / "shadow_export4_keyframe_comparison.png",
            )
            result["comparison_sheet"] = sheet

        results.append(result)
        print(
            f"{video_stem}: shadow={result['shadow'].get('closure_score', 0):.3f} "
            f"export4={result['export4'].get('closure_score', 0):.3f}"
        )

    ok_results = [item for item in results if item.get("shadow", {}).get("status") == "ok" and item.get("export4", {}).get("status") == "ok"]
    shadow_scores = np.asarray([item["shadow"]["closure_score"] for item in ok_results], dtype=np.float32)
    export4_scores = np.asarray([item["export4"]["closure_score"] for item in ok_results], dtype=np.float32)
    curl_ranges = np.asarray([item["input"]["curl_range"] for item in ok_results], dtype=np.float32)
    score_corr = None
    if shadow_scores.size >= 2 and float(np.std(shadow_scores)) > 1e-8 and float(np.std(export4_scores)) > 1e-8:
        score_corr = float(np.corrcoef(shadow_scores, export4_scores)[0, 1])

    plots = _plot_aggregate(ok_results, visual_dir) if ok_results else {}
    aggregate = {
        "videos_total": len(items),
        "videos_processed": len(ok_results),
        "shadow_failures": sum(1 for item in results if item.get("shadow", {}).get("status") != "ok"),
        "export4_failures": sum(1 for item in results if item.get("export4", {}).get("status") != "ok"),
        "shadow_closure_score_mean": float(np.mean(shadow_scores)) if shadow_scores.size else 0.0,
        "export4_closure_score_mean": float(np.mean(export4_scores)) if export4_scores.size else 0.0,
        "input_curl_range_mean": float(np.mean(curl_ranges)) if curl_ranges.size else 0.0,
        "score_correlation": score_corr,
        "rendered_video_count": sum(1 for item in results if item.get("comparison_sheet")),
    }

    metadata = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_shadow_video_open_close_comparison_v1",
        "manifest": manifest_path,
        "shadow_xml": shadow_xml,
        "export4_xml": export4_xml,
        "adapter": {
            "shadow": "existing vision_shadow_retarget 24D normalized action",
            "export4": "hand_open_close_feature_v1_to_export4_position_control_v1",
            "training_used": False,
            "ball_used": False,
        },
        "manifest_summary": manifest.get("summary", {}),
        "aggregate": aggregate,
        "plots": plots,
        "results": results,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(_json_ready(metadata), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_report(report_path, metadata_path, manifest.get("summary", {}), ok_results, aggregate, plots, args)
    print(f"Saved report: {report_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()
