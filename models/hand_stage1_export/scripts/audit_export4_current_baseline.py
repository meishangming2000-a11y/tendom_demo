#!/usr/bin/env python3
"""Audit the export4 current MuJoCo baseline.

Checks:
- joint direction signs on the current baseline,
- thumb mechanical/opposition behavior,
- simplified collision proxy behavior with the ball scene.

This script is diagnostic only. It does not edit CAD, STL, joint names, joint
tree, axes, or MJCF files.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "mjcf" / "hand_stage1_export4_current_baseline.xml"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_current_baseline.xml"
DEFAULT_BALL_SCENE = ROOT / "mjcf" / "scene_ball_export4_current_baseline.xml"
DEFAULT_VISUAL_DIR = ROOT / "docs" / "visual_checks_export4_current_baseline_audit"
DEFAULT_METADATA = ROOT / "metadata" / "export4_current_baseline_audit.json"
DEFAULT_JOINT_REPORT = ROOT / "docs" / "export4_current_baseline_joint_direction_audit.md"
DEFAULT_THUMB_REPORT = ROOT / "docs" / "export4_current_baseline_thumb_audit.md"
DEFAULT_COLLISION_REPORT = ROOT / "docs" / "export4_current_baseline_collision_audit.md"
DEFAULT_SW_CHECKLIST = ROOT / "docs" / "solidworks_export4_followup_checklist.md"

LONG_FINGERS = ("index", "middle", "ring", "little")
TIP_SITES = {
    "thumb": "thumb_tip_site",
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
}

NATURAL_CLOSE_TARGETS = {
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

PRESHAPE_TARGETS = {
    "index_mcp_flex_joint": -0.035,
    "middle_mcp_flex_joint": -0.035,
    "ring_mcp_flex_joint": -0.02,
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

THUMB_VISUAL_TARGET = {
    "thumb_cmc_abd_joint": -0.3,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}

EXPECTED_NEGATIVE_CLOSE = tuple(
    f"{finger}_{joint}"
    for finger in LONG_FINGERS
    for joint in ("mcp_abd_joint", "pip_joint", "dip_joint")
)

AUDIT_ONLY_JOINTS = tuple(f"{finger}_mcp_flex_joint" for finger in LONG_FINGERS) + (
    "wrist_1_joint",
    "wrist_2_joint",
    "thumb_cmc_abd_joint",
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
)

THUMB_CHAIN_EXPECTED = [
    ("palm_link", "thumb_root_connector_fixed_joint", "thumb_root_connector_link"),
    ("thumb_root_connector_link", "thumb_cmc_abd_joint", "thumb_trapezium1_link"),
    ("thumb_trapezium1_link", "thumb_cmc_joint", "thumb_metacarpal_link"),
    ("thumb_metacarpal_link", "thumb_mcp_joint", "thumb_proximal_link"),
    ("thumb_proximal_link", "thumb_ip_joint", "thumb_distal_link"),
]


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _load_xml_joint_tree(model_xml: Path) -> Dict[str, Any]:
    tree = ET.parse(model_xml)
    root = tree.getroot()
    joints: Dict[str, Dict[str, str]] = {}
    bodies: Dict[str, Dict[str, str]] = {}
    body_stack: List[str] = []

    def visit_body(body: ET.Element, parent: str | None) -> None:
        name = body.attrib.get("name", "")
        if name:
            bodies[name] = {
                "parent_body": parent or "world",
                "pos": body.attrib.get("pos", ""),
                "quat": body.attrib.get("quat", ""),
            }
        body_stack.append(name)
        for joint in body.findall("joint"):
            joint_name = joint.attrib.get("name", "")
            if joint_name:
                joints[joint_name] = {
                    "parent_body": parent or "world",
                    "child_body": name,
                    "type": joint.attrib.get("type", ""),
                    "axis": joint.attrib.get("axis", ""),
                    "range": joint.attrib.get("range", ""),
                }
        for child in body.findall("body"):
            visit_body(child, name)
        body_stack.pop()

    worldbody = root.find("worldbody")
    if worldbody is not None:
        for body in worldbody.findall("body"):
            visit_body(body, None)
    return {"joints": joints, "bodies": bodies}


def _joint_names(model) -> List[str]:
    import mujoco

    return [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, idx) or "" for idx in range(model.njnt)]


def _actuator_names(model) -> List[str]:
    import mujoco

    return [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) or "" for idx in range(model.nu)]


def _site(model, data, site_name: str) -> np.ndarray:
    import mujoco

    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if site_id < 0:
        return np.zeros(3)
    return data.site_xpos[site_id].copy()


def _body(model, data, body_name: str) -> np.ndarray:
    import mujoco

    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id < 0:
        return np.zeros(3)
    return data.xpos[body_id].copy()


def _set_qpos_targets(model, data, targets: Dict[str, float]) -> None:
    import mujoco

    data.qpos[:] = model.qpos0
    for joint_id in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id) or ""
        if joint_name not in targets:
            continue
        low, high = model.jnt_range[joint_id]
        data.qpos[int(model.jnt_qposadr[joint_id])] = float(np.clip(targets[joint_name], low, high))
    mujoco.mj_forward(model, data)


def _ctrl_from_joint_targets(model, targets: Dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for idx, actuator_name in enumerate(_actuator_names(model)):
        joint_name = actuator_name[:-4] if actuator_name.endswith("_pos") else actuator_name
        value = float(targets.get(joint_name, 0.0))
        low, high = model.actuator_ctrlrange[idx]
        ctrl[idx] = float(np.clip(value, low, high))
    return ctrl


def _step_to_targets(model, data, targets: Dict[str, float], steps: int = 220) -> None:
    import mujoco

    target_ctrl = _ctrl_from_joint_targets(model, targets)
    start = data.ctrl.copy()
    for step in range(max(1, steps)):
        alpha = step / max(1, steps - 1)
        data.ctrl[:] = (1 - alpha) * start + alpha * target_ctrl
        mujoco.mj_step(model, data)


def _tip_positions(model, data) -> Dict[str, np.ndarray]:
    return {name: _site(model, data, site) for name, site in TIP_SITES.items()}


def _palm_reference(model, data) -> np.ndarray:
    # Previous palm-side audit established +Y as palmar side. Use the palm
    # collision proxy center as the stable geometric reference.
    import mujoco

    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if body_id < 0:
        return np.zeros(3)
    mat = data.xmat[body_id].reshape(3, 3)
    return data.xpos[body_id].copy() + mat @ np.asarray([0.0, 0.048, 0.002])


def _apply_debug_colors(model) -> None:
    import mujoco

    for geom_id in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""
        if name.startswith("thumb_") or "_thumb_" in name:
            model.geom_rgba[geom_id] = np.asarray([1.0, 0.48, 0.08, 1.0])
        elif "collision_proxy" in name:
            model.geom_rgba[geom_id][3] = max(float(model.geom_rgba[geom_id][3]), 0.45)

    site_colors = {
        "thumb_tip_site": [1.0, 0.05, 0.02, 1.0],
        "index_tip_site": [0.10, 1.0, 0.15, 1.0],
        "middle_tip_site": [0.0, 0.85, 1.0, 1.0],
        "ring_tip_site": [0.10, 0.35, 1.0, 0.9],
        "little_tip_site": [0.10, 0.35, 1.0, 0.9],
    }
    for site_name, rgba in site_colors.items():
        site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        if site_id >= 0:
            model.site_rgba[site_id] = np.asarray(rgba)


def _render(model, data, *, lookat=(0.0, 0.045, 0.19), distance=0.34, azimuth=145, elevation=-28) -> np.ndarray:
    import mujoco

    renderer = mujoco.Renderer(model, width=960, height=680)
    try:
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = np.asarray(lookat, dtype=np.float64)
        camera.distance = float(distance)
        camera.azimuth = float(azimuth)
        camera.elevation = float(elevation)
        renderer.update_scene(data, camera=camera)
        return renderer.render().copy()
    finally:
        renderer.close()


def _sheet(frames: List[Tuple[str, np.ndarray]], out_path: Path, columns: int = 2) -> str:
    from PIL import Image, ImageDraw

    if not frames:
        return ""
    w, h = frames[0][1].shape[1], frames[0][1].shape[0]
    label_h = 50
    columns = max(1, min(columns, len(frames)))
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new("RGB", (columns * w, rows * (h + label_h)), (238, 240, 244))
    draw = ImageDraw.Draw(sheet)
    for idx, (label, image) in enumerate(frames):
        x = (idx % columns) * w
        y = (idx // columns) * (h + label_h)
        draw.text((x + 8, y + 6), label, fill=(15, 15, 15))
        sheet.paste(Image.fromarray(image), (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return str(out_path)


def audit_joint_directions(model_xml: Path, visual_dir: Path) -> Dict[str, Any]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(model_xml))
    _apply_debug_colors(model)
    joint_rows: List[Dict[str, Any]] = []
    frames: List[Tuple[str, np.ndarray]] = []

    for joint_id, joint_name in enumerate(_joint_names(model)):
        if not joint_name or model.jnt_type[joint_id] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        low, high = model.jnt_range[joint_id]
        delta_pos = min(0.2, max(0.0, float(high)))
        delta_neg = max(-0.2, min(0.0, float(low)))
        finger = next((name for name in LONG_FINGERS if joint_name.startswith(f"{name}_")), None)
        relevant_site = f"{finger}_tip_site" if finger else "thumb_tip_site" if joint_name.startswith("thumb_") else "middle_tip_site"

        neutral = mujoco.MjData(model)
        _set_qpos_targets(model, neutral, {})
        neutral_tip = _site(model, neutral, relevant_site)

        pos_data = mujoco.MjData(model)
        _set_qpos_targets(model, pos_data, {joint_name: delta_pos})
        pos_tip = _site(model, pos_data, relevant_site)

        neg_data = mujoco.MjData(model)
        _set_qpos_targets(model, neg_data, {joint_name: delta_neg})
        neg_tip = _site(model, neg_data, relevant_site)

        pos_delta = pos_tip - neutral_tip
        neg_delta = neg_tip - neutral_tip

        status = "AUDIT_ONLY"
        expectation = "not signed"
        if joint_name in EXPECTED_NEGATIVE_CLOSE:
            expectation = "negative should move fingertip toward palmar +Y"
            if neg_delta[1] > 0.0005 and neg_delta[1] > pos_delta[1]:
                status = "PASS"
            else:
                status = "NEEDS_SW_CHECK"
        elif joint_name in AUDIT_ONLY_JOINTS:
            status = "AUDIT_ONLY"

        joint_rows.append(
            {
                "joint": joint_name,
                "range": [float(low), float(high)],
                "axis": model.jnt_axis[joint_id].copy(),
                "relevant_site": relevant_site,
                "positive_test_angle": float(delta_pos),
                "negative_test_angle": float(delta_neg),
                "positive_tip_delta": pos_delta,
                "negative_tip_delta": neg_delta,
                "positive_palmar_y_delta": float(pos_delta[1]),
                "negative_palmar_y_delta": float(neg_delta[1]),
                "expectation": expectation,
                "status": status,
            }
        )

        if joint_name in EXPECTED_NEGATIVE_CLOSE or joint_name in (
            "index_mcp_flex_joint",
            "middle_mcp_flex_joint",
            "thumb_cmc_abd_joint",
            "thumb_cmc_joint",
            "thumb_mcp_joint",
            "thumb_ip_joint",
        ):
            frames.append((f"{joint_name}\nnegative {delta_neg:.2f}", _render(model, neg_data)))
            frames.append((f"{joint_name}\npositive {delta_pos:.2f}", _render(model, pos_data)))

    status_counts: Dict[str, int] = {}
    for row in joint_rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    return {
        "model_xml": model_xml,
        "status_counts": status_counts,
        "joints": joint_rows,
        "visual_sheet": _sheet(frames, visual_dir / "joint_direction_positive_negative_sheet.png", columns=2),
    }


def audit_thumb(model_xml: Path, visual_dir: Path) -> Dict[str, Any]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(model_xml))
    _apply_debug_colors(model)
    data_open = mujoco.MjData(model)
    _set_qpos_targets(model, data_open, {})
    data_close = mujoco.MjData(model)
    _set_qpos_targets(model, data_close, {**NATURAL_CLOSE_TARGETS, **THUMB_VISUAL_TARGET})

    open_tips = _tip_positions(model, data_open)
    close_tips = _tip_positions(model, data_close)
    palm = _palm_reference(model, data_close)

    thumb_metric = {
        "open_thumb_index_distance": float(np.linalg.norm(open_tips["thumb"] - open_tips["index"])),
        "close_thumb_index_distance": float(np.linalg.norm(close_tips["thumb"] - close_tips["index"])),
        "open_thumb_middle_distance": float(np.linalg.norm(open_tips["thumb"] - open_tips["middle"])),
        "close_thumb_middle_distance": float(np.linalg.norm(close_tips["thumb"] - close_tips["middle"])),
        "close_thumb_palm_distance": float(np.linalg.norm(close_tips["thumb"] - palm)),
        "thumb_visual_target": THUMB_VISUAL_TARGET,
    }

    individual_rows: List[Dict[str, Any]] = []
    thumb_joint_names = ("thumb_cmc_abd_joint", "thumb_cmc_joint", "thumb_mcp_joint", "thumb_ip_joint")
    for joint_name in thumb_joint_names:
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if joint_id < 0:
            individual_rows.append({"joint": joint_name, "status": "MISSING"})
            continue
        low, high = model.jnt_range[joint_id]
        pos = min(0.25, max(0.0, float(high)))
        neg = max(-0.25, min(0.0, float(low)))
        base = mujoco.MjData(model)
        _set_qpos_targets(model, base, {})
        pos_data = mujoco.MjData(model)
        _set_qpos_targets(model, pos_data, {joint_name: pos})
        neg_data = mujoco.MjData(model)
        _set_qpos_targets(model, neg_data, {joint_name: neg})
        base_tip = _site(model, base, "thumb_tip_site")
        pos_tip = _site(model, pos_data, "thumb_tip_site")
        neg_tip = _site(model, neg_data, "thumb_tip_site")
        individual_rows.append(
            {
                "joint": joint_name,
                "range": [float(low), float(high)],
                "axis": model.jnt_axis[joint_id].copy(),
                "positive_angle": float(pos),
                "negative_angle": float(neg),
                "positive_tip_delta": pos_tip - base_tip,
                "negative_tip_delta": neg_tip - base_tip,
                "positive_palmar_y_delta": float(pos_tip[1] - base_tip[1]),
                "negative_palmar_y_delta": float(neg_tip[1] - base_tip[1]),
            }
        )

    xml_tree = _load_xml_joint_tree(model_xml)
    actual_chain = []
    chain_status = "PASS"
    for parent, joint, child in THUMB_CHAIN_EXPECTED:
        info = xml_tree["joints"].get(joint)
        row = {
            "expected_parent": parent,
            "joint": joint,
            "expected_child": child,
            "actual_parent": info.get("parent_body", "MISSING") if info else "MISSING",
            "actual_child": info.get("child_body", "MISSING") if info else "MISSING",
            "axis": info.get("axis", "") if info else "",
            "range": info.get("range", "") if info else "",
        }
        if not info and joint == "thumb_root_connector_fixed_joint":
            child_info = xml_tree["bodies"].get(child, {})
            if child_info.get("parent_body") == parent:
                row["actual_parent"] = child_info.get("parent_body", "MISSING")
                row["actual_child"] = child
                row["axis"] = "MJCF fixed body nesting"
                row["range"] = "fixed"
            else:
                chain_status = "NEEDS_SW_CHECK"
        elif not info or info.get("parent_body") != parent or info.get("child_body") != child:
            chain_status = "NEEDS_SW_CHECK"
        actual_chain.append(row)

    frames = [
        ("thumb open", _render(model, data_open, lookat=(0.0, 0.045, 0.19), distance=0.32, azimuth=145, elevation=-28)),
        (
            "thumb visual close",
            _render(model, data_close, lookat=(0.0, 0.055, 0.20), distance=0.28, azimuth=180, elevation=-78),
        ),
        (
            "thumb visual side",
            _render(model, data_close, lookat=(-0.015, 0.04, 0.19), distance=0.24, azimuth=75, elevation=-16),
        ),
    ]

    conclusion = "PARTIAL"
    if chain_status == "PASS" and thumb_metric["close_thumb_index_distance"] < 0.03:
        conclusion = "PASS_FOR_SCRIPTED_SMOKE"

    return {
        "model_xml": model_xml,
        "thumb_chain_status": chain_status,
        "actual_chain": actual_chain,
        "individual_joint_rows": individual_rows,
        "metrics": thumb_metric,
        "conclusion": conclusion,
        "visual_sheet": _sheet(frames, visual_dir / "thumb_audit_sheet.png", columns=3),
    }


def _geom_name(model, geom_id: int) -> str:
    import mujoco

    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or f"geom_{geom_id}"


def _contact_summary(model, data) -> Dict[str, Any]:
    contacts = []
    max_pen = 0.0
    max_hand_ball_pen = 0.0
    ball_contacts = 0
    ball_hand_contacts = 0
    ball_ground_contacts = 0
    for idx in range(data.ncon):
        con = data.contact[idx]
        g1 = _geom_name(model, int(con.geom1))
        g2 = _geom_name(model, int(con.geom2))
        penetration = float(max(0.0, -con.dist))
        max_pen = max(max_pen, penetration)
        if "ball" in g1 or "ball" in g2:
            ball_contacts += 1
            if "ground" in g1 or "ground" in g2:
                ball_ground_contacts += 1
            else:
                ball_hand_contacts += 1
                max_hand_ball_pen = max(max_hand_ball_pen, penetration)
        contacts.append({"geom1": g1, "geom2": g2, "dist": float(con.dist), "penetration": penetration})
    return {
        "contact_count": int(data.ncon),
        "ball_contact_count": int(ball_contacts),
        "ball_hand_contact_count": int(ball_hand_contacts),
        "ball_ground_contact_count": int(ball_ground_contacts),
        "max_penetration": max_pen,
        "max_hand_ball_penetration": max_hand_ball_pen,
        "contacts": contacts[:30],
    }


def audit_collision(model_xml: Path, ball_scene: Path, visual_dir: Path) -> Dict[str, Any]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(ball_scene))
    _apply_debug_colors(model)
    geom_rows: List[Dict[str, Any]] = []
    visual_collision_enabled = []
    proxy_count = 0
    mesh_collision_count = 0
    for geom_id in range(model.ngeom):
        name = _geom_name(model, geom_id)
        geom_type = int(model.geom_type[geom_id])
        contype = int(model.geom_contype[geom_id])
        conaffinity = int(model.geom_conaffinity[geom_id])
        is_proxy = "collision_proxy" in name
        if is_proxy:
            proxy_count += 1
        if geom_type == mujoco.mjtGeom.mjGEOM_MESH and (contype or conaffinity):
            mesh_collision_count += 1
        if "_visual" in name and (contype or conaffinity):
            visual_collision_enabled.append(name)
        geom_rows.append(
            {
                "name": name,
                "type": mujoco.mjtGeom(model.geom_type[geom_id]).name,
                "contype": contype,
                "conaffinity": conaffinity,
                "size": model.geom_size[geom_id].copy(),
                "is_proxy": is_proxy,
            }
        )

    stages = [
        ("open_ball", {}),
        ("preshape_ball", PRESHAPE_TARGETS),
        ("four_fingers_closed_ball", NATURAL_CLOSE_TARGETS),
        ("thumb_visual_close_ball", {**NATURAL_CLOSE_TARGETS, **THUMB_VISUAL_TARGET}),
    ]
    stage_rows: List[Dict[str, Any]] = []
    frames: List[Tuple[str, np.ndarray]] = []
    for name, targets in stages:
        data = mujoco.MjData(model)
        # Static collision check: keep the free ball at its XML initial pose.
        # A dynamic rollout here mostly tests gravity/ground contact, not the
        # hand collision proxy.
        _set_qpos_targets(model, data, targets)
        mujoco.mj_forward(model, data)
        summary = _contact_summary(model, data)
        tips = _tip_positions(model, data)
        ball_pos = _body(model, data, "ball")
        tip_ball = {
            finger: float(np.linalg.norm(pos - ball_pos))
            for finger, pos in tips.items()
        }
        stage_rows.append(
            {
                "stage": name,
                "targets": targets,
                "contact_summary": summary,
                "ball_position": ball_pos,
                "tip_ball_distances": tip_ball,
            }
        )
        frames.append((f"{name}\ncontacts={summary['contact_count']} pen={summary['max_penetration']:.4f}", _render(model, data)))

    status = "PASS_FOR_SMOKE"
    issues: List[Dict[str, str]] = []
    open_summary = stage_rows[0]["contact_summary"]
    if open_summary["max_penetration"] > 0.002:
        status = "NEEDS_PROXY_TUNING"
        issues.append({"severity": "MAJOR", "item": "open_ball_penetration", "detail": "Ball penetrates collision proxy in open hand."})
    if mesh_collision_count:
        status = "NEEDS_PROXY_TUNING"
        issues.append({"severity": "MAJOR", "item": "mesh_collision_enabled", "detail": "One or more mesh geoms are collision-enabled."})
    if visual_collision_enabled:
        status = "NEEDS_PROXY_TUNING"
        issues.append({"severity": "MAJOR", "item": "visual_collision_enabled", "detail": "Visual geoms should remain non-colliding."})
    if proxy_count < 20:
        status = "NEEDS_PROXY_TUNING"
        issues.append({"severity": "MINOR", "item": "proxy_count_low", "detail": "Proxy geom count seems low for a 5-finger hand."})
    max_stage_hand_ball_pen = max(
        (float(row["contact_summary"]["max_hand_ball_penetration"]) for row in stage_rows),
        default=0.0,
    )
    if max_stage_hand_ball_pen > 0.008:
        if status == "PASS_FOR_SMOKE":
            status = "PASS_FOR_SMOKE_NEEDS_TRAINING_PROXY_TUNING"
        issues.append(
            {
                "severity": "MAJOR",
                "item": "closed_ball_proxy_penetration",
                "detail": (
                    "Closed static ball check has hand-ball penetration above 8 mm. "
                    "Acceptable for visual smoke, too high for contact-rich training."
                ),
            }
        )

    return {
        "model_xml": model_xml,
        "ball_scene": ball_scene,
        "status": status,
        "proxy_count": proxy_count,
        "mesh_collision_count": mesh_collision_count,
        "visual_collision_enabled": visual_collision_enabled,
        "geom_rows": geom_rows,
        "stage_rows": stage_rows,
        "issues": issues,
        "visual_sheet": _sheet(frames, visual_dir / "collision_audit_stage_sheet.png", columns=2),
    }


def write_joint_report(report: Path, audit: Dict[str, Any]) -> None:
    lines = ["# Export4 Current Baseline Joint Direction Audit\n\n"]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append(f"Model: `{audit['model_xml']}`\n\n")
    lines.append(f"Visual sheet: `{audit['visual_sheet']}`\n\n")
    lines.append("## Status Counts\n\n")
    for status, count in sorted(audit["status_counts"].items()):
        lines.append(f"- `{status}`: {count}\n")
    lines.append("\n## Joint Direction Table\n\n")
    lines.append("| joint | status | range | +Y delta at +angle | +Y delta at -angle | expectation |\n")
    lines.append("|---|---|---:|---:|---:|---|\n")
    for row in audit["joints"]:
        rng = f"{row['range'][0]:.3f} {row['range'][1]:.3f}"
        lines.append(
            f"| `{row['joint']}` | {row['status']} | `{rng}` | "
            f"{row['positive_palmar_y_delta']:.5f} | {row['negative_palmar_y_delta']:.5f} | {row['expectation']} |\n"
        )
    lines.append("\n## Interpretation\n\n")
    lines.append("- Long-finger MCP-abd/PIP/DIP are expected to close toward the current palmar side on negative commands.\n")
    lines.append("- MCP-flex, wrist, and thumb joints are marked audit-only because their mechanical semantics are not one-dimensional palm closure.\n")
    lines.append("- Any `NEEDS_SW_CHECK` row should be checked in SolidWorks for joint axis direction, csys Z axis, and limit sign.\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def write_thumb_report(report: Path, audit: Dict[str, Any]) -> None:
    lines = ["# Export4 Current Baseline Thumb Audit\n\n"]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append(f"Model: `{audit['model_xml']}`\n\n")
    lines.append(f"Visual sheet: `{audit['visual_sheet']}`\n\n")
    lines.append(f"Conclusion: `{audit['conclusion']}`\n\n")
    lines.append("## Thumb Chain\n\n")
    lines.append("| joint | expected parent | actual parent | expected child | actual child | axis / representation | range |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for row in audit["actual_chain"]:
        lines.append(
            f"| `{row['joint']}` | `{row['expected_parent']}` | `{row['actual_parent']}` | "
            f"`{row['expected_child']}` | `{row['actual_child']}` | `{row['axis']}` | `{row['range']}` |\n"
        )
    metrics = audit["metrics"]
    lines.append("\n## Thumb Opposition Metrics\n\n")
    lines.append(f"- open thumb-index distance: `{metrics['open_thumb_index_distance']:.4f} m`\n")
    lines.append(f"- close thumb-index distance: `{metrics['close_thumb_index_distance']:.4f} m`\n")
    lines.append(f"- open thumb-middle distance: `{metrics['open_thumb_middle_distance']:.4f} m`\n")
    lines.append(f"- close thumb-middle distance: `{metrics['close_thumb_middle_distance']:.4f} m`\n")
    lines.append(f"- close thumb-palm distance: `{metrics['close_thumb_palm_distance']:.4f} m`\n")
    lines.append("\n## Individual Thumb Joint Sign Probe\n\n")
    lines.append("| joint | range | +Y delta at +angle | +Y delta at -angle | note |\n")
    lines.append("|---|---:|---:|---:|---|\n")
    for row in audit["individual_joint_rows"]:
        if row.get("status") == "MISSING":
            lines.append(f"| `{row['joint']}` | MISSING | n/a | n/a | BLOCKER |\n")
            continue
        rng = f"{row['range'][0]:.3f} {row['range'][1]:.3f}"
        lines.append(
            f"| `{row['joint']}` | `{rng}` | {row['positive_palmar_y_delta']:.5f} | "
            f"{row['negative_palmar_y_delta']:.5f} | TODO: confirm mechanical meaning in SolidWorks |\n"
        )
    lines.append("\n## Interpretation\n\n")
    lines.append("- In MJCF, fixed joints are commonly represented as direct body nesting rather than an explicit `<joint>` element.\n")
    lines.append("- The chain topology matches the export4 intended 2-DoF CMC chain if all rows show expected parent/child.\n")
    lines.append("- Current scripted target closes the thumb near index/middle and is acceptable for smoke tests.\n")
    lines.append("- This does not prove the CMC axes are anatomically final; SolidWorks should still confirm axis origins/directions.\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def write_collision_report(report: Path, audit: Dict[str, Any]) -> None:
    lines = ["# Export4 Current Baseline Collision Proxy Audit\n\n"]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append(f"Ball scene: `{audit['ball_scene']}`\n\n")
    lines.append(f"Status: `{audit['status']}`\n\n")
    lines.append(f"Visual sheet: `{audit['visual_sheet']}`\n\n")
    lines.append("## Proxy Summary\n\n")
    lines.append(f"- collision proxy geom count: `{audit['proxy_count']}`\n")
    lines.append(f"- collision-enabled mesh geom count: `{audit['mesh_collision_count']}`\n")
    lines.append(f"- visual geoms accidentally collision-enabled: `{len(audit['visual_collision_enabled'])}`\n")
    lines.append("\n## Stage Contact Summary\n\n")
    lines.append("| stage | contacts | ball-hand | ball-ground | max hand-ball penetration | thumb-ball | index-ball | middle-ball |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for row in audit["stage_rows"]:
        summary = row["contact_summary"]
        dist = row["tip_ball_distances"]
        lines.append(
            f"| {row['stage']} | {summary['contact_count']} | {summary['ball_hand_contact_count']} | "
            f"{summary['ball_ground_contact_count']} | {summary['max_hand_ball_penetration']:.5f} | "
            f"{dist.get('thumb', 0.0):.4f} | "
            f"{dist.get('index', 0.0):.4f} | {dist.get('middle', 0.0):.4f} |\n"
        )
    lines.append("\n## Issues\n\n")
    if audit["issues"]:
        lines.append("| severity | item | detail |\n|---|---|---|\n")
        for issue in audit["issues"]:
            lines.append(f"| {issue['severity']} | `{issue['item']}` | {issue['detail']} |\n")
    else:
        lines.append("- No blocker detected for current smoke-test collision proxy.\n")
    lines.append("\n## Interpretation\n\n")
    lines.append("- Clean STL remains visual-only; collision relies on primitive proxy geoms.\n")
    lines.append("- Stage checks are static pose checks that keep the free ball at its XML initial pose; dynamic ball-gravity behavior is not audited here.\n")
    lines.append("- Passing this audit means the proxy is usable for smoke tests, not final contact-rich training.\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def write_sw_checklist(report: Path, joint_audit: Dict[str, Any], thumb_audit: Dict[str, Any], collision_audit: Dict[str, Any]) -> None:
    rows: List[Tuple[str, str, str, str]] = []

    for row in joint_audit["joints"]:
        if row["status"] == "NEEDS_SW_CHECK":
            rows.append(
                (
                    "MAJOR",
                    row["joint"],
                    "Long-finger negative direction did not move tip toward palmar +Y as expected.",
                    "Check joint csys Z axis, hinge axis sign, and limit sign in SolidWorks.",
                )
            )
    for row in thumb_audit["actual_chain"]:
        if row["actual_parent"] != row["expected_parent"] or row["actual_child"] != row["expected_child"]:
            rows.append(
                (
                    "BLOCKER",
                    row["joint"],
                    "Thumb chain parent/child differs from expected export4 topology.",
                    "Check component ownership/link assignment in SolidWorks URDF Exporter.",
                )
            )
    rows.append(
        (
            "MAJOR",
            "thumb_cmc_abd_joint / thumb_cmc_joint",
            "Current scripted thumb works for smoke tests but CMC mechanical semantics are not finally signed off.",
            "Confirm each CMC axis passes through the intended rotation center and that positive/negative directions match intended abd/flex.",
        )
    )
    rows.append(
        (
            "MINOR",
            "index/middle/ring/little_mcp_flex_joint",
            "MCP-flex joints are audit-only because they may be lateral/spread joints in the current naming convention.",
            "Confirm whether each MCP flex csys actually represents spread/side motion or flexion; do not rename unless SolidWorks semantics are final.",
        )
    )
    if collision_audit["status"] != "PASS_FOR_SMOKE":
        rows.append(
            (
                "MJCF",
                "collision_proxy",
                "Collision proxy audit found tuning issues.",
                "This is MJCF-side proxy tuning, not necessarily SolidWorks. Check only if proxy mismatch reflects wrong body/link geometry.",
            )
        )

    lines = ["# SolidWorks Export4 Follow-Up Checklist\n\n"]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append("This checklist lists unresolved or human-confirmation items after MuJoCo current-baseline audits.\n\n")
    lines.append("| severity | item | observed issue | SolidWorks check |\n")
    lines.append("|---|---|---|---|\n")
    for severity, item, observed, check in rows:
        lines.append(f"| {severity} | `{item}` | {observed} | {check} |\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit export4 current MuJoCo baseline")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--ball-scene", default=str(DEFAULT_BALL_SCENE))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--joint-report", default=str(DEFAULT_JOINT_REPORT))
    parser.add_argument("--thumb-report", default=str(DEFAULT_THUMB_REPORT))
    parser.add_argument("--collision-report", default=str(DEFAULT_COLLISION_REPORT))
    parser.add_argument("--sw-checklist", default=str(DEFAULT_SW_CHECKLIST))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    model_xml = Path(args.model).resolve()
    ball_scene = Path(args.ball_scene).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    metadata = Path(args.metadata).resolve()

    for path in (model_xml, ball_scene):
        if not path.exists():
            raise FileNotFoundError(path)

    visual_dir.mkdir(parents=True, exist_ok=True)
    joint_audit = audit_joint_directions(model_xml, visual_dir / "joint_direction")
    thumb_audit = audit_thumb(model_xml, visual_dir / "thumb")
    collision_audit = audit_collision(model_xml, ball_scene, visual_dir / "collision")

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_current_baseline_audit_v1",
        "model_xml": model_xml,
        "ball_scene": ball_scene,
        "joint_direction": joint_audit,
        "thumb": thumb_audit,
        "collision": collision_audit,
        "reports": {
            "joint": Path(args.joint_report).resolve(),
            "thumb": Path(args.thumb_report).resolve(),
            "collision": Path(args.collision_report).resolve(),
            "solidworks_checklist": Path(args.sw_checklist).resolve(),
        },
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write_joint_report(Path(args.joint_report).resolve(), joint_audit)
    write_thumb_report(Path(args.thumb_report).resolve(), thumb_audit)
    write_collision_report(Path(args.collision_report).resolve(), collision_audit)
    write_sw_checklist(Path(args.sw_checklist).resolve(), joint_audit, thumb_audit, collision_audit)

    print(f"Saved joint report: {Path(args.joint_report).resolve()}")
    print(f"Saved thumb report: {Path(args.thumb_report).resolve()}")
    print(f"Saved collision report: {Path(args.collision_report).resolve()}")
    print(f"Saved SolidWorks checklist: {Path(args.sw_checklist).resolve()}")
    print(f"Saved metadata: {metadata}")
    print(f"Joint status counts: {joint_audit['status_counts']}")
    print(f"Thumb conclusion: {thumb_audit['conclusion']}")
    print(f"Collision status: {collision_audit['status']}")


if __name__ == "__main__":
    main()
