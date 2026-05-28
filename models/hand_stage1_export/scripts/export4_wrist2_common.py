#!/usr/bin/env python3
"""Shared utilities for the export4 wrist2/collision-proxy experiment.

Diagnostic helpers only. These functions do not edit CAD, STL, joint names,
joint tree, or tendon routing.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
ARCHIVE_DIR = ROOT / "archive"
DATA_DIR = ROOT / "data"

HAND_TUNED = MJCF_DIR / "hand_stage1_export4_wrist2_collision_tuned.xml"
SCENE_TUNED = MJCF_DIR / "scene_ball_export4_wrist2_collision_tuned.xml"
HAND_BASELINE = MJCF_DIR / "hand_stage1_export4_current_baseline.xml"
SCENE_BASELINE = MJCF_DIR / "scene_ball_export4_current_baseline.xml"

DEFAULT_BALL_POSITION = [0.0, -0.1, 0.21]
BALL_RADIUS = 0.025
LONG_FINGERS = ("index", "middle", "ring", "little")
TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}

PRESHAPE_TARGETS = {
    "index_mcp_flex_joint": -0.035,
    "middle_mcp_flex_joint": -0.035,
    "ring_mcp_flex_joint": -0.020,
    "little_mcp_flex_joint": -0.015,
    "index_mcp_abd_joint": -0.34,
    "middle_mcp_abd_joint": -0.38,
    "ring_mcp_abd_joint": -0.20,
    "little_mcp_abd_joint": -0.15,
    "index_pip_joint": -0.48,
    "middle_pip_joint": -0.52,
    "ring_pip_joint": -0.20,
    "little_pip_joint": -0.16,
    "index_dip_joint": -0.22,
    "middle_dip_joint": -0.24,
    "ring_dip_joint": -0.10,
    "little_dip_joint": -0.08,
}

LONG_FINGER_TARGETS = {
    "index_mcp_flex_joint": -0.06,
    "middle_mcp_flex_joint": -0.06,
    "ring_mcp_flex_joint": -0.05,
    "little_mcp_flex_joint": -0.04,
    "index_mcp_abd_joint": -0.58,
    "middle_mcp_abd_joint": -0.64,
    "ring_mcp_abd_joint": -0.62,
    "little_mcp_abd_joint": -0.54,
    "index_pip_joint": -0.82,
    "middle_pip_joint": -0.88,
    "ring_pip_joint": -0.84,
    "little_pip_joint": -0.76,
    "index_dip_joint": -0.42,
    "middle_dip_joint": -0.46,
    "ring_dip_joint": -0.44,
    "little_dip_joint": -0.40,
}

THUMB_SMOKE_TARGETS = {
    "thumb_cmc_abd_joint": -0.30,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dirs() -> None:
    for path in (DOCS_DIR, METADATA_DIR, ARCHIVE_DIR, DATA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def backup_if_exists(path: Path, tag: str) -> str | None:
    if not path.exists():
        return None
    ensure_dirs()
    target = ARCHIVE_DIR / f"{path.stem}.{tag}.{timestamp()}{path.suffix}"
    shutil.copy2(path, target)
    return str(target)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    return value


def write_json(path: Path, payload: Dict[str, Any], tag: str) -> None:
    backup_if_exists(path, tag)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str, tag: str) -> None:
    backup_if_exists(path, tag)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_model(xml_path: Path):
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(xml_path.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def named_ids(model, obj_type) -> Dict[str, int]:
    import mujoco

    if obj_type == mujoco.mjtObj.mjOBJ_JOINT:
        count = model.njnt
    elif obj_type == mujoco.mjtObj.mjOBJ_ACTUATOR:
        count = model.nu
    elif obj_type == mujoco.mjtObj.mjOBJ_BODY:
        count = model.nbody
    elif obj_type == mujoco.mjtObj.mjOBJ_GEOM:
        count = model.ngeom
    elif obj_type == mujoco.mjtObj.mjOBJ_SITE:
        count = model.nsite
    else:
        raise ValueError(f"Unsupported object type: {obj_type}")
    rows = {}
    for idx in range(count):
        name = mujoco.mj_id2name(model, obj_type, idx)
        if name:
            rows[name] = idx
    return rows


def joint_names(model) -> List[str]:
    import mujoco

    return [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, idx) or f"joint_{idx}"
        for idx in range(model.njnt)
    ]


def actuator_names(model) -> List[str]:
    import mujoco

    return [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) or f"actuator_{idx}"
        for idx in range(model.nu)
    ]


def model_summary(model) -> Dict[str, int]:
    return {
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "nmesh": int(model.nmesh),
    }


def ball_joint_id(model, mujoco) -> int:
    return int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint"))


def set_ball_position(model, data, mujoco, position: Iterable[float]) -> None:
    jid = ball_joint_id(model, mujoco)
    if jid < 0:
        return
    pos = np.asarray(list(position), dtype=np.float64)
    qadr = int(model.jnt_qposadr[jid])
    dadr = int(model.jnt_dofadr[jid])
    data.qpos[qadr : qadr + 3] = pos
    data.qpos[qadr + 3 : qadr + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[dadr : dadr + 6] = 0.0


def body_pos(model, data, mujoco, body_name: str) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if bid < 0:
        return np.full(3, np.nan)
    return data.xpos[bid].copy()


def site_pos(model, data, mujoco, site_name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if sid < 0:
        return np.full(3, np.nan)
    return data.site_xpos[sid].copy()


def clamp_joint(model, jid: int, value: float) -> float:
    low, high = model.jnt_range[jid]
    if np.isfinite(low) and np.isfinite(high) and high > low:
        return float(np.clip(value, low, high))
    return float(value)


def set_qpos_targets(model, data, mujoco, targets: Dict[str, float], ball_position=None) -> Dict[str, float]:
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    applied: Dict[str, float] = {}
    for jid in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or ""
        if name not in targets:
            continue
        qadr = int(model.jnt_qposadr[jid])
        value = clamp_joint(model, jid, float(targets[name]))
        data.qpos[qadr] = value
        applied[name] = value
    if ball_position is not None:
        set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    return applied


def ctrl_from_targets(model, targets: Dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for idx, actuator_name in enumerate(actuator_names(model)):
        joint_name = actuator_name[:-4] if actuator_name.endswith("_pos") else actuator_name
        value = float(targets.get(joint_name, 0.0))
        low, high = model.actuator_ctrlrange[idx]
        ctrl[idx] = float(np.clip(value, low, high))
    return ctrl


def step_ctrl(
    model,
    data,
    mujoco,
    target_ctrl: np.ndarray,
    steps: int,
    *,
    ball_position: Iterable[float] | None = None,
    pin_ball: bool = True,
    viewer=None,
) -> None:
    start = data.ctrl.copy()
    total = max(1, int(steps))
    for step in range(total):
        alpha = step / max(1, total - 1)
        data.ctrl[:] = (1.0 - alpha) * start + alpha * target_ctrl
        if pin_ball and ball_position is not None:
            set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_step(model, data)
        if pin_ball and ball_position is not None:
            set_ball_position(model, data, mujoco, ball_position)
            mujoco.mj_forward(model, data)
        if viewer is not None:
            viewer.sync()


def geom_name(model, mujoco, gid: int) -> str:
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(gid)) or f"geom_{gid}"


def body_name_for_geom(model, mujoco, gid: int) -> str:
    bid = int(model.geom_bodyid[int(gid)])
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, bid) or f"body_{bid}"


def classify_contact(geom1: str, geom2: str, body1: str, body2: str) -> str:
    names = " ".join([geom1, geom2, body1, body2]).lower()
    if "ball" in names and "ground" in names:
        return "ball-ground"
    if "ball" in names and ("palm" in names or "finger" in names or "thumb" in names or "distal" in names or "proximal" in names):
        return "ball-hand"
    if "ground" in names and ("hand" in names or "wrist" in names or "palm" in names or "finger" in names or "thumb" in names):
        return "hand-ground"
    if "palm_link_collision" in names:
        return "hand-hand:palm-proxy"
    if "thumb" in names:
        return "hand-hand:thumb-proxy"
    if "distal" in names:
        return "hand-hand:fingertip-proxy"
    if "proximal" in names or "mcp" in names:
        return "hand-hand:finger-proxy"
    return "other"


def contact_rows(model, data, mujoco, top_n: int | None = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx in range(data.ncon):
        contact = data.contact[idx]
        g1 = geom_name(model, mujoco, contact.geom1)
        g2 = geom_name(model, mujoco, contact.geom2)
        b1 = body_name_for_geom(model, mujoco, contact.geom1)
        b2 = body_name_for_geom(model, mujoco, contact.geom2)
        rows.append(
            {
                "index": idx,
                "geom1": g1,
                "geom2": g2,
                "body1": b1,
                "body2": b2,
                "dist": float(contact.dist),
                "penetration": float(max(0.0, -contact.dist)),
                "position": contact.pos.copy(),
                "source": classify_contact(g1, g2, b1, b2),
            }
        )
    rows.sort(key=lambda row: row["penetration"], reverse=True)
    if top_n is not None:
        return rows[:top_n]
    return rows


def contact_summary(model, data, mujoco) -> Dict[str, Any]:
    rows = contact_rows(model, data, mujoco)
    ball_rows = [row for row in rows if row["source"] == "ball-hand"]
    return {
        "contact_count": int(data.ncon),
        "max_penetration": float(max([0.0] + [row["penetration"] for row in rows])),
        "ball_hand_contact_count": len(ball_rows),
        "ball_hand_max_penetration": float(max([0.0] + [row["penetration"] for row in ball_rows])),
        "source_counts": {
            source: sum(1 for row in rows if row["source"] == source)
            for source in sorted({row["source"] for row in rows})
        },
    }


def fingertip_metrics(model, data, mujoco) -> Dict[str, Any]:
    ball = body_pos(model, data, mujoco, "ball")
    tips = {finger: site_pos(model, data, mujoco, site) for finger, site in TIP_SITES.items()}
    four = [tips[name] for name in LONG_FINGERS if not np.isnan(tips[name]).any()]
    four_distances = {
        name: float(np.linalg.norm(tips[name] - ball))
        for name in LONG_FINGERS
        if not np.isnan(tips[name]).any() and not np.isnan(ball).any()
    }
    thumb_ball = float(np.linalg.norm(tips["thumb"] - ball)) if not np.isnan(tips["thumb"]).any() and not np.isnan(ball).any() else float("nan")
    thumb_index = (
        float(np.linalg.norm(tips["thumb"] - tips["index"]))
        if not np.isnan(tips["thumb"]).any() and not np.isnan(tips["index"]).any()
        else float("nan")
    )
    return {
        "ball_position": ball,
        "tip_positions": tips,
        "four_finger_tip_ball_distances": four_distances,
        "four_finger_avg_tip_ball_distance": float(np.mean(list(four_distances.values()))) if four_distances else float("nan"),
        "thumb_ball_distance": thumb_ball,
        "thumb_index_distance": thumb_index,
        "long_tip_centroid": np.mean(np.vstack(four), axis=0) if four else np.full(3, np.nan),
    }


def phase_metrics(model, data, mujoco, initial_ball: Iterable[float] | None = None) -> Dict[str, Any]:
    contact = contact_summary(model, data, mujoco)
    tips = fingertip_metrics(model, data, mujoco)
    ball = tips["ball_position"]
    initial = np.asarray(list(initial_ball), dtype=np.float64) if initial_ball is not None else ball
    return {
        **contact,
        "ball_displacement": float(np.linalg.norm(ball - initial)) if not np.isnan(ball).any() else float("nan"),
        "four_finger_avg_tip_ball_distance": tips["four_finger_avg_tip_ball_distance"],
        "four_finger_tip_ball_distances": tips["four_finger_tip_ball_distances"],
        "thumb_ball_distance": tips["thumb_ball_distance"],
        "thumb_index_distance": tips["thumb_index_distance"],
    }


def render_free_camera(
    model,
    data,
    mujoco,
    output: Path,
    *,
    lookat: Tuple[float, float, float] = (0.0, 0.045, 0.20),
    distance: float = 0.32,
    azimuth: float = 145.0,
    elevation: float = -25.0,
    width: int = 1280,
    height: int = 900,
) -> Dict[str, Any]:
    import imageio.v2 as imageio

    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=width, height=height)
    try:
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = np.asarray(lookat, dtype=np.float64)
        camera.distance = float(distance)
        camera.azimuth = float(azimuth)
        camera.elevation = float(elevation)
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "shape": list(image.shape),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
        "mean_pixel": float(image.mean()),
        "lookat": list(lookat),
        "distance": distance,
        "azimuth": azimuth,
        "elevation": elevation,
    }


def render_standard_views(model, data, mujoco, visual_dir: Path, stem: str) -> Dict[str, Any]:
    views = {
        "front": {"lookat": (0.0, 0.045, 0.20), "distance": 0.34, "azimuth": 145, "elevation": -25},
        "side": {"lookat": (0.0, 0.045, 0.20), "distance": 0.34, "azimuth": 90, "elevation": -20},
        "top": {"lookat": (0.0, 0.045, 0.20), "distance": 0.30, "azimuth": 180, "elevation": -78},
        "thumb": {"lookat": (-0.015, 0.035, 0.19), "distance": 0.26, "azimuth": 75, "elevation": -18},
    }
    outputs = {}
    for name, kwargs in views.items():
        try:
            outputs[name] = render_free_camera(model, data, mujoco, visual_dir / f"{stem}_{name}.png", **kwargs)
        except Exception as exc:  # pragma: no cover - render backend dependent
            outputs[name] = {"error": str(exc), "file": str(visual_dir / f"{stem}_{name}.png")}
    return outputs

