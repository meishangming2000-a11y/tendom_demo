from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from clean_mesh_common import render_png, set_ball_position, write_json
from export3_common import (
    BALL_POSITION,
    DOCS_DIR,
    FOUR_FINGER_CLOSE_TARGETS,
    FOUR_FINGER_JOINTS,
    METADATA_DIR,
    MJCF_DIR,
    SCENE_XML,
    TIP_SITES,
    actuator_map,
    ball_contact_summary,
    joint_map,
    load_model,
    set_ctrl,
)


PALM_REPORT = DOCS_DIR / "export3_palm_orientation_audit.md"
PALM_JSON = METADATA_DIR / "export3_palm_orientation_audit.json"
BALL_REPORT = DOCS_DIR / "export3_ball_side_mirror_test.md"
FINGER_REPORT = DOCS_DIR / "export3_four_finger_flex_direction_audit.md"
STATUS_NOTES_JSON = METADATA_DIR / "export3_palm_side_status_notes.json"

PALM_VIS_DIR = DOCS_DIR / "visual_checks_export3_palm_orientation"
FINGER_VIS_DIR = DOCS_DIR / "visual_checks_export3_finger_direction"
MARKER_SCENE = MJCF_DIR / "scene_ball_export3_palm_orientation_debug.xml"

FINGER_NAMES = ["index", "middle", "ring", "little"]
MCP_BASE_BODIES = [f"{name}_mcp_flex_link" for name in FINGER_NAMES]
PROXIMAL_BODIES = [f"{name}_proximal_phalanx_link" for name in FINGER_NAMES]
FINGER_TIP_SITES = [f"{name}_tip_site" for name in FINGER_NAMES]
THUMB_BASE_BODIES = ["thumb_root_connector_link", "thumb_trapezium1_link"]
BALL_TEST_POSITIONS = [
    [0.0, -0.10, 0.21],
    [0.0, 0.10, 0.21],
    [0.0, -0.08, 0.21],
    [0.0, 0.08, 0.21],
]


def normalize(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm < 1e-9:
        return np.zeros_like(v, dtype=float)
    return (v / norm).astype(float)


def obj_body_pos(model, data, mujoco, name: str) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid < 0:
        raise RuntimeError(f"Missing body {name}")
    return np.array(data.xpos[bid], dtype=float)


def obj_site_pos(model, data, mujoco, name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if sid < 0:
        raise RuntimeError(f"Missing site {name}")
    return np.array(data.site_xpos[sid], dtype=float)


def set_qpos_direct(model, data, mujoco, targets: dict[str, float]) -> None:
    joints = joint_map(model, mujoco)
    for name, value in targets.items():
        jid = joints.get(name)
        if jid is None:
            continue
        data.qpos[int(model.jnt_qposadr[jid])] = float(value)


def collect_pose_geometry(model, data, mujoco) -> dict:
    palm_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if palm_bid < 0:
        raise RuntimeError("Missing palm_link body")
    palm_pos = np.array(data.xpos[palm_bid], dtype=float)
    palm_xmat = np.array(data.xmat[palm_bid], dtype=float).reshape(3, 3)
    local_axes = {
        "x": (palm_xmat @ np.array([1.0, 0.0, 0.0])).tolist(),
        "y": (palm_xmat @ np.array([0.0, 1.0, 0.0])).tolist(),
        "z": (palm_xmat @ np.array([0.0, 0.0, 1.0])).tolist(),
    }
    mcp_base_positions = {name: obj_body_pos(model, data, mujoco, body).tolist() for name, body in zip(FINGER_NAMES, MCP_BASE_BODIES)}
    proximal_base_positions = {name: obj_body_pos(model, data, mujoco, body).tolist() for name, body in zip(FINGER_NAMES, PROXIMAL_BODIES)}
    fingertip_positions = {name: obj_site_pos(model, data, mujoco, site).tolist() for name, site in zip(FINGER_NAMES, FINGER_TIP_SITES)}
    thumb_base_positions = {body: obj_body_pos(model, data, mujoco, body).tolist() for body in THUMB_BASE_BODIES}
    thumb_tip = obj_site_pos(model, data, mujoco, "thumb_tip_site").tolist()
    return {
        "palm_world_pos": palm_pos.tolist(),
        "palm_world_xmat": palm_xmat.tolist(),
        "palm_local_axes_world": local_axes,
        "mcp_base_positions": mcp_base_positions,
        "proximal_base_positions": proximal_base_positions,
        "fingertip_positions": fingertip_positions,
        "thumb_base_positions": thumb_base_positions,
        "thumb_tip_position": thumb_tip,
    }


def compute_orientation(model, data, mujoco, ball_position: list[float]) -> dict:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    open_geom = collect_pose_geometry(model, data, mujoco)
    palm = np.array(open_geom["palm_world_pos"], dtype=float)
    mcp_mean = np.mean([np.array(value, dtype=float) for value in open_geom["mcp_base_positions"].values()], axis=0)
    tip_mean = np.mean([np.array(value, dtype=float) for value in open_geom["fingertip_positions"].values()], axis=0)
    thumb_base = np.array(open_geom["thumb_base_positions"]["thumb_trapezium1_link"], dtype=float)
    finger_forward = normalize(tip_mean - mcp_mean)
    thumb_side = normalize(thumb_base - palm)

    data.qpos[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    set_qpos_direct(model, data, mujoco, FOUR_FINGER_CLOSE_TARGETS)
    mujoco.mj_forward(model, data)
    closed_geom = collect_pose_geometry(model, data, mujoco)
    open_tip_mean = tip_mean
    closed_tip_mean = np.mean([np.array(value, dtype=float) for value in closed_geom["fingertip_positions"].values()], axis=0)
    scripted_close_direction = normalize(closed_tip_mean - open_tip_mean)
    palm_normal_candidate = normalize(np.cross(finger_forward, thumb_side))
    if float(np.dot(palm_normal_candidate, scripted_close_direction)) < 0:
        palm_normal_candidate = -palm_normal_candidate
    # This is an inferred convention: palmar normal is perpendicular to the
    # finger-extension/thumb-side plane and oriented toward the current close motion.
    palmar_side = palm_normal_candidate
    dorsal_side = -palmar_side
    ball_vec = np.array(ball_position, dtype=float) - palm
    ball_side_score = float(np.dot(normalize(ball_vec), palmar_side))
    ball_projection_m = float(np.dot(ball_vec, palmar_side))
    return {
        "open_geometry": open_geom,
        "closed_four_finger_geometry": closed_geom,
        "finger_forward_direction_world": finger_forward.tolist(),
        "thumb_side_direction_world": thumb_side.tolist(),
        "scripted_four_finger_close_direction_world": scripted_close_direction.tolist(),
        "palm_normal_from_finger_thumb_cross_world": palmar_side.tolist(),
        "palm_normal_close_alignment": float(np.dot(palmar_side, scripted_close_direction)),
        "inferred_palmar_side_world": palmar_side.tolist(),
        "inferred_dorsal_side_world": dorsal_side.tolist(),
        "ball_position": ball_position,
        "ball_vector_from_palm": ball_vec.tolist(),
        "ball_side_score_dot_unit": ball_side_score,
        "ball_projection_on_palmar_axis_m": ball_projection_m,
        "ball_is_on_inferred_palmar_side": bool(ball_projection_m > 0),
        "notes": [
            "Palmar side is inferred as the palm-plane normal from finger-forward cross thumb-side, with sign chosen to align with scripted four-finger closing motion.",
            "If the scripted close direction is itself wrong, this palmar inference reveals the scripted bug rather than true CAD anatomy.",
        ],
    }


def write_marker_scene(markers: dict[str, list[float]]) -> None:
    def xyz(value):
        return " ".join(f"{float(x):.8g}" for x in value)

    palm = markers["palm_center_marker"]
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<mujoco model="hand_stage1_export3_palm_orientation_debug">',
        '  <include file="hand_stage1_export3.xml"/>',
        '  <visual>',
        '    <global azimuth="145" elevation="-25" offwidth="1280" offheight="900"/>',
        '  </visual>',
        '  <asset>',
        '    <texture type="2d" name="ground_checker" builtin="checker" rgb1="0.18 0.20 0.22" rgb2="0.28 0.30 0.32" width="300" height="300"/>',
        '    <material name="ground_mat" texture="ground_checker" texrepeat="5 5" reflectance="0.15"/>',
        '  </asset>',
        '  <worldbody>',
        '    <light pos="-0.25 0.25 0.5"/>',
        '    <geom name="ground" type="plane" pos="0 0 0" size="0.4 0.4 0.02" material="ground_mat" contype="1" conaffinity="3"/>',
        '    <body name="ball" pos="0 -0.1 0.21">',
        '      <freejoint name="ball_freejoint"/>',
        '      <geom name="ball_geom" type="sphere" size="0.025" rgba="0.95 0.23 0.18 1" mass="0.03" friction="0.8 0.05 0.001" condim="3" contype="2" conaffinity="1"/>',
        '    </body>',
        f'    <geom name="palm_center_marker" type="sphere" pos="{xyz(markers["palm_center_marker"])}" size="0.007" rgba="1 0.55 0.05 1" contype="0" conaffinity="0"/>',
        f'    <geom name="palmar_side_marker" type="sphere" pos="{xyz(markers["palmar_side_marker"])}" size="0.009" rgba="0.05 1 0.15 1" contype="0" conaffinity="0"/>',
        f'    <geom name="dorsal_side_marker" type="sphere" pos="{xyz(markers["dorsal_side_marker"])}" size="0.009" rgba="0.62 0.2 1 1" contype="0" conaffinity="0"/>',
        f'    <geom name="finger_forward_marker" type="sphere" pos="{xyz(markers["finger_forward_marker"])}" size="0.008" rgba="0.05 0.85 1 1" contype="0" conaffinity="0"/>',
        f'    <geom name="thumb_side_marker" type="sphere" pos="{xyz(markers["thumb_side_marker"])}" size="0.008" rgba="1 0.9 0.05 1" contype="0" conaffinity="0"/>',
        f'    <geom name="palmar_axis" type="capsule" fromto="{xyz(palm)} {xyz(markers["palmar_side_marker"])}" size="0.0025" rgba="0.05 1 0.15 1" contype="0" conaffinity="0"/>',
        f'    <geom name="dorsal_axis" type="capsule" fromto="{xyz(palm)} {xyz(markers["dorsal_side_marker"])}" size="0.0025" rgba="0.62 0.2 1 1" contype="0" conaffinity="0"/>',
        f'    <geom name="finger_forward_axis" type="capsule" fromto="{xyz(palm)} {xyz(markers["finger_forward_marker"])}" size="0.0025" rgba="0.05 0.85 1 1" contype="0" conaffinity="0"/>',
        f'    <geom name="thumb_side_axis" type="capsule" fromto="{xyz(palm)} {xyz(markers["thumb_side_marker"])}" size="0.0025" rgba="1 0.9 0.05 1" contype="0" conaffinity="0"/>',
        '    <camera name="full_hand_with_ball" pos="0.20 -0.34 0.29" xyaxes="0.834219 0.551433 0 -0.16379 0.247785 0.954869" fovy="45"/>',
        '    <camera name="front" pos="0.20 -0.34 0.29" xyaxes="0.834219 0.551433 0 -0.16379 0.247785 0.954869" fovy="45"/>',
        '    <camera name="side" pos="0.34 0.02 0.24" xyaxes="-0.190477 0.981692 0 -0.169999 -0.0329848 0.984892" fovy="45"/>',
        '    <camera name="top" pos="0.02 -0.06 0.48" xyaxes="0.707107 0.707107 0 -0.705346 0.705346 0.0705346" fovy="45"/>',
        '    <camera name="palm" pos="0.03 -0.23 0.21" xyaxes="0.995037 0.0995037 0 -0.030061 0.30061 0.953268" fovy="38"/>',
        '  </worldbody>',
        '</mujoco>',
        "",
    ]
    MARKER_SCENE.write_text("\n".join(lines), encoding="utf-8")


def render_marker_views(orientation: dict) -> list[dict]:
    PALM_VIS_DIR.mkdir(parents=True, exist_ok=True)
    palm = np.array(orientation["open_geometry"]["palm_world_pos"], dtype=float)
    palmar = np.array(orientation["inferred_palmar_side_world"], dtype=float)
    dorsal = np.array(orientation["inferred_dorsal_side_world"], dtype=float)
    finger = np.array(orientation["finger_forward_direction_world"], dtype=float)
    thumb = np.array(orientation["thumb_side_direction_world"], dtype=float)
    markers = {
        "palm_center_marker": palm.tolist(),
        "palmar_side_marker": (palm + 0.08 * palmar).tolist(),
        "dorsal_side_marker": (palm + 0.08 * dorsal).tolist(),
        "finger_forward_marker": (palm + 0.10 * finger).tolist(),
        "thumb_side_marker": (palm + 0.08 * thumb).tolist(),
    }
    write_marker_scene(markers)
    mujoco, model, data = load_model(MARKER_SCENE)
    model.opt.gravity[:] = 0.0
    set_ball_position(model, data, mujoco, [0.0, -0.1, 0.21])
    mujoco.mj_forward(model, data)
    renders = [
        render_png(model, data, mujoco, "front", PALM_VIS_DIR / "palm_side_debug_front.png", width=1200, height=850),
        render_png(model, data, mujoco, "side", PALM_VIS_DIR / "palm_side_debug_side.png", width=1200, height=850),
        render_png(model, data, mujoco, "top", PALM_VIS_DIR / "ball_current_side.png", width=1200, height=850),
    ]
    set_ball_position(model, data, mujoco, [0.0, 0.1, 0.21])
    mujoco.mj_forward(model, data)
    renders.append(render_png(model, data, mujoco, "top", PALM_VIS_DIR / "ball_mirrored_side.png", width=1200, height=850))
    return renders


def simulate_four_finger_close(ball_position: list[float]) -> dict:
    mujoco, model, data = load_model(SCENE_XML)
    model.opt.gravity[:] = 0.0
    act_map = actuator_map(model, mujoco)
    set_ball_position(model, data, mujoco, ball_position)
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)
    open_contacts = ball_contact_summary(model, data, mujoco)
    open_tip_dist = fingertip_ball_distances(model, data, mujoco)
    steps = 320
    for step in range(steps):
        fraction = (step + 1) / steps
        targets = {name: 0.0 for name in FOUR_FINGER_JOINTS}
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = float(value) * fraction
        for name, value in targets.items():
            aid = act_map.get(name)
            if aid is None:
                continue
            low, high = model.actuator_ctrlrange[aid]
            data.ctrl[aid] = min(max(value, low), high)
        set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_step(model, data)
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    hold_contacts = ball_contact_summary(model, data, mujoco)
    hold_tip_dist = fingertip_ball_distances(model, data, mujoco)
    return {
        "ball_position": ball_position,
        "open_contact_count": open_contacts["ball_contact_count"],
        "open_max_penetration": open_contacts["max_penetration"],
        "open_four_fingertip_ball_distances": open_tip_dist,
        "open_mean_four_fingertip_distance": float(np.mean(list(open_tip_dist.values()))),
        "hold_contact_count": hold_contacts["ball_contact_count"],
        "hold_max_penetration": hold_contacts["max_penetration"],
        "hold_four_fingertip_ball_distances": hold_tip_dist,
        "hold_mean_four_fingertip_distance": float(np.mean(list(hold_tip_dist.values()))),
        "hold_contacts": hold_contacts["ball_contacts"],
    }


def fingertip_ball_distances(model, data, mujoco) -> dict[str, float]:
    ball = obj_body_pos(model, data, mujoco, "ball")
    out = {}
    for site in FINGER_TIP_SITES:
        out[site] = float(np.linalg.norm(obj_site_pos(model, data, mujoco, site) - ball))
    return out


def ball_side_mirror_test(orientation: dict) -> dict:
    palm = np.array(orientation["open_geometry"]["palm_world_pos"], dtype=float)
    palmar = np.array(orientation["inferred_palmar_side_world"], dtype=float)
    rows = []
    for ball in BALL_TEST_POSITIONS:
        result = simulate_four_finger_close(ball)
        ball_vec = np.array(ball, dtype=float) - palm
        result["palmar_projection_m"] = float(np.dot(ball_vec, palmar))
        result["ball_is_on_inferred_palmar_side"] = bool(result["palmar_projection_m"] > 0)
        rows.append(result)
    return {"positions": rows}


def render_finger_direction(model, data, mujoco, joint_name: str, value: float, output: Path) -> dict:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, [0.0, -0.1, 0.21])
    set_qpos_direct(model, data, mujoco, {joint_name: value})
    mujoco.mj_forward(model, data)
    return render_png(model, data, mujoco, "top", output, width=1200, height=850)


def four_finger_direction_audit(orientation: dict, angle: float = 0.35) -> dict:
    mujoco, model, data = load_model(SCENE_XML)
    model.opt.gravity[:] = 0.0
    FINGER_VIS_DIR.mkdir(parents=True, exist_ok=True)
    palmar = np.array(orientation["inferred_palmar_side_world"], dtype=float)
    data.qpos[:] = 0.0
    set_ball_position(model, data, mujoco, [0.0, -0.1, 0.21])
    mujoco.mj_forward(model, data)
    baseline_tips = {site: obj_site_pos(model, data, mujoco, site) for site in FINGER_TIP_SITES}
    rows = {}
    renders = []
    for joint in FOUR_FINGER_JOINTS:
        finger = joint.split("_")[0]
        tip_site = f"{finger}_tip_site"
        rows[joint] = {}
        for label, value in [("positive", angle), ("negative", -angle)]:
            data.qpos[:] = 0.0
            set_ball_position(model, data, mujoco, [0.0, -0.1, 0.21])
            set_qpos_direct(model, data, mujoco, {joint: value})
            mujoco.mj_forward(model, data)
            tip = obj_site_pos(model, data, mujoco, tip_site)
            delta = tip - baseline_tips[tip_site]
            projection = float(np.dot(delta, palmar))
            rows[joint][label] = {
                "angle": value,
                "tip_delta": delta.tolist(),
                "tip_delta_norm": float(np.linalg.norm(delta)),
                "tip_delta_projection_on_inferred_palmar_axis_m": projection,
                "moves_toward_inferred_palmar_side": bool(projection > 0),
                "note": "Direct qpos test; negative values may be outside exported joint limits.",
            }
            stem = f"{joint}_{label}_{abs(value):.2f}".replace(".", "d")
            output = FINGER_VIS_DIR / f"{stem}.png"
            renders.append(render_png(model, data, mujoco, "top", output, width=1200, height=850))
    return {"angle": angle, "joints": rows, "renders": renders}


def write_palm_report(payload: dict) -> None:
    write_json(PALM_JSON, payload)
    o = payload["orientation"]
    lines = [
        "# Export3 Palm Orientation Audit",
        "",
        "Status: direction/orientation diagnostic only. No CAD/STL/tree/training changes.",
        "",
        f"- Scene: `{SCENE_XML}`",
        f"- Marker debug scene: `{MARKER_SCENE}`",
        f"- Current ball position: `{o['ball_position']}`",
        f"- Palm world position: `{o['open_geometry']['palm_world_pos']}`",
        "",
        "## Palm Local Axes In World",
        "",
        "| Axis | World direction |",
        "|---|---|",
    ]
    for axis, value in o["open_geometry"]["palm_local_axes_world"].items():
        lines.append(f"| palm local `{axis}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Inferred Anatomical / Task Directions",
            "",
            f"- Finger extension direction: `{o['finger_forward_direction_world']}`",
            f"- Thumb side direction: `{o['thumb_side_direction_world']}`",
            f"- Scripted four-finger close direction: `{o['scripted_four_finger_close_direction_world']}`",
            f"- Palm normal from finger/thumb cross: `{o['palm_normal_from_finger_thumb_cross_world']}`",
            f"- Palm normal / close alignment: `{o['palm_normal_close_alignment']:.6f}`",
            f"- Inferred palmar side: `{o['inferred_palmar_side_world']}`",
            f"- Inferred dorsal side: `{o['inferred_dorsal_side_world']}`",
            "",
            "## Ball Side",
            "",
            f"- Ball vector from palm: `{o['ball_vector_from_palm']}`",
            f"- Projection on inferred palmar axis: `{o['ball_projection_on_palmar_axis_m']:.6f} m`",
            f"- Ball is on inferred palmar side: `{o['ball_is_on_inferred_palmar_side']}`",
            "",
            "## MCP / Thumb / Tip Positions",
            "",
            f"- MCP base positions: `{o['open_geometry']['mcp_base_positions']}`",
            f"- Proximal base positions: `{o['open_geometry']['proximal_base_positions']}`",
            f"- Fingertip positions: `{o['open_geometry']['fingertip_positions']}`",
            f"- Thumb base positions: `{o['open_geometry']['thumb_base_positions']}`",
            "",
            "## Marker Renders",
            "",
        ]
    )
    for item in payload["marker_renders"]:
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in payload["interpretation"])
    lines.append("")
    PALM_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_ball_report(payload: dict) -> None:
    rows = payload["ball_side_mirror_test"]["positions"]
    lines = [
        "# Export3 Ball Side Mirror Test",
        "",
        "Status: four-finger-only ball-side diagnostic. Thumb target tuning is paused.",
        "",
        "| Ball position | On inferred palmar side? | Palmar projection (m) | Open contacts | Hold contacts | Max penetration | Mean open tip-ball | Mean hold tip-ball | Visual note |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        side = "palmar" if row["ball_is_on_inferred_palmar_side"] else "dorsal"
        if row["ball_is_on_inferred_palmar_side"] and row["hold_mean_four_fingertip_distance"] < 0.06:
            note = "more consistent with palm-side scripted closure"
        elif not row["ball_is_on_inferred_palmar_side"] and row["hold_mean_four_fingertip_distance"] < 0.06:
            note = "close numerically but on inferred dorsal side"
        else:
            note = f"{side} side; weak four-finger proximity"
        lines.append(
            f"| `{row['ball_position']}` | {row['ball_is_on_inferred_palmar_side']} | {row['palmar_projection_m']:.6f} | "
            f"{row['open_contact_count']} | {row['hold_contact_count']} | {row['hold_max_penetration']:.6f} | "
            f"{row['open_mean_four_fingertip_distance']:.6f} | {row['hold_mean_four_fingertip_distance']:.6f} | {note} |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in payload["ball_interpretation"])
    lines.append("")
    BALL_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_finger_report(payload: dict) -> None:
    audit = payload["four_finger_direction_audit"]
    lines = [
        "# Export3 Four-Finger Flex Direction Audit",
        "",
        "Status: single-joint positive/negative direction diagnostic. Direct qpos is used; negative values may be outside exported limits.",
        "",
        f"- Test angle: `{audit['angle']}` rad",
        f"- Palmar axis used for projection: `{payload['orientation']['inferred_palmar_side_world']}`",
        "",
        "| Joint | + projection on palmar axis | - projection on palmar axis | + closes to palm? | - closes to palm? | Suggested close sign |",
        "|---|---:|---:|---|---|---|",
    ]
    suggestions = {}
    for joint, rows in audit["joints"].items():
        pos = rows["positive"]
        neg = rows["negative"]
        if pos["tip_delta_projection_on_inferred_palmar_axis_m"] > neg["tip_delta_projection_on_inferred_palmar_axis_m"]:
            sign = "positive"
        elif neg["tip_delta_projection_on_inferred_palmar_axis_m"] > pos["tip_delta_projection_on_inferred_palmar_axis_m"]:
            sign = "negative"
        else:
            sign = "ambiguous"
        suggestions[joint] = sign
        lines.append(
            f"| `{joint}` | {pos['tip_delta_projection_on_inferred_palmar_axis_m']:.6f} | "
            f"{neg['tip_delta_projection_on_inferred_palmar_axis_m']:.6f} | {pos['moves_toward_inferred_palmar_side']} | "
            f"{neg['moves_toward_inferred_palmar_side']} | `{sign}` |"
        )
    lines.extend(["", "## Renders", ""])
    for item in audit["renders"]:
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in payload["finger_interpretation"])
    lines.append("")
    FINGER_REPORT.write_text("\n".join(lines), encoding="utf-8")


def build_interpretation(orientation: dict, ball_test: dict, finger_audit: dict) -> tuple[list[str], list[str], list[str], dict]:
    current = next(row for row in ball_test["positions"] if row["ball_position"] == [0.0, -0.1, 0.21])
    mirrored = next(row for row in ball_test["positions"] if row["ball_position"] == [0.0, 0.1, 0.21])
    palm_lines = [
        "The inferred palmar side is the finger-forward x thumb-side palm-plane normal, with sign chosen to align with the current scripted four-finger close motion.",
        f"Current ball `[0.0, -0.1, 0.21]` has palmar projection {current['palmar_projection_m']:.4f} m.",
        f"Mirrored ball `[0.0, 0.1, 0.21]` has palmar projection {mirrored['palmar_projection_m']:.4f} m.",
    ]
    if current["ball_is_on_inferred_palmar_side"] and not mirrored["ball_is_on_inferred_palmar_side"]:
        palm_lines.append("By the current scripted-close inference, the existing negative-Y ball position is on the palm-closing side.")
    elif mirrored["ball_is_on_inferred_palmar_side"] and not current["ball_is_on_inferred_palmar_side"]:
        palm_lines.append("By the current scripted-close inference, the mirrored positive-Y ball position is on the palm-closing side.")
    else:
        palm_lines.append("Both tested ball sides are ambiguous relative to the inferred palmar axis; inspect palm CSYS/mesh orientation.")

    ball_lines = []
    if mirrored["hold_mean_four_fingertip_distance"] + 0.01 < current["hold_mean_four_fingertip_distance"]:
        ball_lines.append("Mirrored positive-Y ball is clearly closer to four fingertips after close; old ball side is likely wrong.")
        ball_side_recommendation = "mirror_ball_side"
    elif current["hold_mean_four_fingertip_distance"] + 0.01 < mirrored["hold_mean_four_fingertip_distance"]:
        ball_lines.append("Current negative-Y ball is clearly closer to four fingertips after close; ball side may be consistent with scripted closure.")
        ball_side_recommendation = "keep_current_ball_side_for_current_script"
    else:
        ball_lines.append("Current and mirrored ball positions are similar by fingertip distance; visual inspection is required.")
        ball_side_recommendation = "ambiguous_visual_check_required"
    ball_lines.append("This test excludes thumb motion; it only checks palm side and long-finger closure.")

    finger_lines = []
    close_signs = {}
    for joint, rows in finger_audit["joints"].items():
        pos = rows["positive"]["tip_delta_projection_on_inferred_palmar_axis_m"]
        neg = rows["negative"]["tip_delta_projection_on_inferred_palmar_axis_m"]
        close_signs[joint] = "positive" if pos > neg else "negative" if neg > pos else "ambiguous"
    negative_close = [joint for joint, sign in close_signs.items() if sign == "negative"]
    positive_close = [joint for joint, sign in close_signs.items() if sign == "positive"]
    finger_lines.append(f"Joints whose negative test moves more toward inferred palmar side: `{negative_close}`.")
    finger_lines.append(f"Joints whose positive test moves more toward inferred palmar side: `{positive_close}`.")
    finger_lines.append("If these signs disagree with SolidWorks intended flexion conventions, scripted target signs or joint axes need review.")

    notes = {
        "current_ball_side_recommendation": ball_side_recommendation,
        "current_ball_on_inferred_palmar_side": current["ball_is_on_inferred_palmar_side"],
        "mirrored_ball_on_inferred_palmar_side": mirrored["ball_is_on_inferred_palmar_side"],
        "close_signs": close_signs,
    }
    return palm_lines, ball_lines, finger_lines, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit export3 palm side, ball side, and four-finger closure direction.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--joint-angle", type=float, default=0.35)
    args = parser.parse_args()

    mujoco, model, data = load_model(SCENE_XML)
    model.opt.gravity[:] = 0.0
    orientation = compute_orientation(model, data, mujoco, [args.ball_x, args.ball_y, args.ball_z])
    marker_renders = render_marker_views(orientation)
    ball_test = ball_side_mirror_test(orientation)
    finger_audit = four_finger_direction_audit(orientation, args.joint_angle)
    palm_lines, ball_lines, finger_lines, notes = build_interpretation(orientation, ball_test, finger_audit)
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_palm_side_orientation_no_model_edits",
        "scene": str(SCENE_XML),
        "marker_scene": str(MARKER_SCENE),
        "orientation": orientation,
        "marker_renders": marker_renders,
        "ball_side_mirror_test": ball_test,
        "four_finger_direction_audit": finger_audit,
        "interpretation": palm_lines,
        "ball_interpretation": ball_lines,
        "finger_interpretation": finger_lines,
        "status_notes": notes,
    }
    write_palm_report(payload)
    write_ball_report(payload)
    write_finger_report(payload)
    write_json(STATUS_NOTES_JSON, notes)
    print(json.dumps({"palm_report": str(PALM_REPORT), "ball_report": str(BALL_REPORT), "finger_report": str(FINGER_REPORT), "notes": notes}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
