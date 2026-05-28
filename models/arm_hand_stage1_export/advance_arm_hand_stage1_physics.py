#!/usr/bin/env python3
"""Advance the CAD-mounted arm + export4 hand through the physics v0 phases.

This script is intentionally conservative:
- it does not edit CAD/STL files;
- it does not overwrite the frozen CAD-mount candidate;
- it writes experimental MJCF files under ./mjcf;
- STL meshes stay visual-only;
- new arm collision uses primitive box proxies.
"""

from __future__ import annotations

import json
import math
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
ARCHIVE = ROOT / "archive"
VIS_TUNING = DOCS / "visual_checks_arm_hand_joint_limit_tuning"
VIS_COLLISION = DOCS / "visual_checks_arm_hand_collision_proxy"
MJCF = ROOT / "mjcf"

BASE_MODEL = ROOT / "arm_hand_export4_cad_mount_candidate.xml"
BASE_SCENE = ROOT / "scene_arm_hand_export4_cad_mount_candidate.xml"
BASE_META = META / "arm_hand_export4_cad_mount_candidate.json"

JOINT_TUNED_MODEL = MJCF / "arm_hand_export4_joint_limit_tuned.xml"
JOINT_TUNED_SCENE = MJCF / "scene_arm_hand_export4_joint_limit_tuned.xml"
COLLISION_MODEL = MJCF / "arm_hand_export4_joint_limit_collision_proxy.xml"
COLLISION_SCENE = MJCF / "scene_arm_hand_export4_joint_limit_collision_proxy.xml"
COLLISION_BALL_SCENE = MJCF / "scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml"

DEFAULT_BALL_RADIUS = 0.028
DEFAULT_BALL_LOCAL_OFFSET = np.array([0.04, 0.12, -0.02], dtype=np.float64)


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

POSES = {
    "open_hand": {},
    "preshape": PRESHAPE_TARGETS,
    "close_four_fingers": LONG_FINGER_TARGETS,
    "close_thumb_smoke": {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
}

FINGERTIP_SITES = [
    "index_tip_site",
    "middle_tip_site",
    "ring_tip_site",
    "little_tip_site",
    "thumb_tip_site",
]


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dirs() -> None:
    for path in [DOCS, META, ARCHIVE, MJCF, VIS_TUNING, VIS_COLLISION]:
        path.mkdir(parents=True, exist_ok=True)


def backup(path: Path, tag: str) -> str | None:
    if not path.exists():
        return None
    target = ARCHIVE / f"{path.stem}.{tag}.{timestamp()}{path.suffix}"
    shutil.copy2(path, target)
    return str(target)


def write_text(path: Path, text: str) -> None:
    backup(path, "autobak")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    backup(path, "autobak")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return str(value)
    return value


def fmt_vec(values: np.ndarray | list[float] | tuple[float, ...]) -> str:
    return " ".join(f"{float(v):.9g}" for v in values)


def load_model(scene_or_model: Path):
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene_or_model))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return mujoco, model, data


def names(model, mujoco, objtype) -> list[str]:
    return [mujoco.mj_id2name(model, objtype, i) or f"{objtype}_{i}" for i in range(get_count(model, objtype))]


def get_count(model, objtype) -> int:
    import mujoco

    if objtype == mujoco.mjtObj.mjOBJ_BODY:
        return model.nbody
    if objtype == mujoco.mjtObj.mjOBJ_JOINT:
        return model.njnt
    if objtype == mujoco.mjtObj.mjOBJ_ACTUATOR:
        return model.nu
    if objtype == mujoco.mjtObj.mjOBJ_GEOM:
        return model.ngeom
    if objtype == mujoco.mjtObj.mjOBJ_SITE:
        return model.nsite
    if objtype == mujoco.mjtObj.mjOBJ_MESH:
        return model.nmesh
    raise ValueError(objtype)


def model_summary(model) -> dict[str, int]:
    return {
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nu": int(model.nu),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "nmesh": int(model.nmesh),
        "nq": int(model.nq),
        "nv": int(model.nv),
    }


def render_image(model, data, mujoco, path: Path, lookat: np.ndarray, distance: float, azimuth: float, elevation: float) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=1280, height=900)
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
    imageio.imwrite(path, image)
    return {"file": str(path), "mean_pixel": float(image.mean()), "min_pixel": int(image.min()), "max_pixel": int(image.max())}


def clamp(model, jid: int, value: float) -> float:
    if bool(model.jnt_limited[jid]):
        lo, hi = model.jnt_range[jid]
        return float(np.clip(value, lo, hi))
    return float(value)


def apply_qpos_targets(model, data, mujoco, targets: dict[str, float]) -> dict[str, float]:
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    applied: dict[str, float] = {}
    for jid in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or ""
        if name not in targets:
            continue
        qadr = int(model.jnt_qposadr[jid])
        value = clamp(model, jid, targets[name])
        data.qpos[qadr] = value
        applied[name] = value
    mujoco.mj_forward(model, data)
    return applied


def ctrl_from_targets(model, mujoco, targets: dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for aid in range(model.nu):
        actuator_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid) or ""
        joint_name = actuator_name[:-4] if actuator_name.endswith("_pos") else actuator_name
        if actuator_name.startswith("a_"):
            joint_name = actuator_name[2:]
        value = float(targets.get(joint_name, 0.0))
        if bool(model.actuator_ctrllimited[aid]):
            lo, hi = model.actuator_ctrlrange[aid]
            value = float(np.clip(value, lo, hi))
        ctrl[aid] = value
    return ctrl


def contact_summary(model, data, mujoco) -> dict[str, Any]:
    rows = []
    max_pen = 0.0
    for i in range(data.ncon):
        contact = data.contact[i]
        g1 = int(contact.geom1)
        g2 = int(contact.geom2)
        b1 = int(model.geom_bodyid[g1])
        b2 = int(model.geom_bodyid[g2])
        dist = float(contact.dist)
        pen = max(0.0, -dist)
        max_pen = max(max_pen, pen)
        rows.append(
            {
                "geom1": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g1) or f"geom_{g1}",
                "geom2": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g2) or f"geom_{g2}",
                "body1": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b1) or f"body_{b1}",
                "body2": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b2) or f"body_{b2}",
                "dist": dist,
                "penetration": pen,
                "pos": np.array(contact.pos).copy(),
            }
        )
    rows.sort(key=lambda row: row["penetration"], reverse=True)
    return {"count": int(data.ncon), "max_penetration": float(max_pen), "top_contacts": rows[:20]}


def fingertip_positions(model, data, mujoco) -> dict[str, list[float]]:
    out = {}
    for site in FINGERTIP_SITES:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site)
        out[site] = data.site_xpos[sid].copy().tolist() if sid >= 0 else [float("nan")] * 3
    return out


def compute_palm_ball_position(model, data, mujoco) -> list[float]:
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if palm_id < 0:
        return [0.0, 0.1, 0.21]
    palm_pos = data.xpos[palm_id].copy()
    palm_mat = data.xmat[palm_id].reshape(3, 3)
    ball = palm_pos + palm_mat @ DEFAULT_BALL_LOCAL_OFFSET
    return ball.tolist()


def adjust_paths_for_mjcf_subdir(xml_root: ET.Element) -> None:
    for mesh in xml_root.findall(".//mesh"):
        file_attr = mesh.get("file")
        if not file_attr:
            continue
        if file_attr.startswith("../arm_stage1_export/"):
            mesh.set("file", "../" + file_attr)
        elif file_attr.startswith("../hand_stage1_export/"):
            mesh.set("file", "../" + file_attr)


def save_xml(root: ET.Element, path: Path) -> None:
    backup(path, "autobak")
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def copy_joint_tuned_model() -> dict[str, Any]:
    tree = ET.parse(BASE_MODEL)
    root = tree.getroot()
    root.set("model", "arm_hand_export4_joint_limit_tuned")
    adjust_paths_for_mjcf_subdir(root)
    save_xml(root, JOINT_TUNED_MODEL)

    scene = make_scene_xml(JOINT_TUNED_MODEL.name, "arm_hand_export4_joint_limit_tuned_scene", include_ball=False)
    write_text(JOINT_TUNED_SCENE, scene)
    return {"model": JOINT_TUNED_MODEL, "scene": JOINT_TUNED_SCENE}


def make_scene_xml(include_file: str, model_name: str, include_ball: bool, ball_pos: list[float] | None = None) -> str:
    ball = ""
    if include_ball:
        x, y, z = ball_pos or [0.0, 0.1, 0.21]
        ball = f"""
    <body name="ball" pos="{x:.9g} {y:.9g} {z:.9g}">
      <freejoint name="ball_freejoint"/>
      <geom name="ball_geom" type="sphere" size="{DEFAULT_BALL_RADIUS:.9g}" mass="0.025" rgba="1 0.45 0.08 1" contype="2" conaffinity="1" friction="0.9 0.04 0.001"/>
    </body>"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<mujoco model="{model_name}">
  <include file="{include_file}"/>
  <statistic extent="0.9" center="0 0 0.22"/>
  <visual>
    <rgba haze="0.15 0.25 0.35 1"/>
    <quality shadowsize="8192"/>
    <global azimuth="205" elevation="-22" offwidth="1280" offheight="900"/>
  </visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.30 0.50 0.70" rgb2="0.00 0.00 0.00" width="512" height="3072"/>
    <texture type="2d" name="ground_checker" builtin="checker" mark="edge" rgb1="0.20 0.30 0.40" rgb2="0.10 0.20 0.30" markrgb="0.80 0.80 0.80" width="300" height="300"/>
    <material name="ground" texture="ground_checker" texrepeat="5 5" texuniform="true" reflectance="0.20"/>
  </asset>
  <worldbody>
    <light name="fill_light" pos="0 0 1"/>
    <light name="key_light" pos="0.3 0 1.5" dir="0 0 -1" directional="true"/>
    <geom name="floor" type="plane" pos="0 0 -0.12" size="0 0 0.05" material="ground" contype="0" conaffinity="4"/>
    <camera name="overview" pos="-0.62 -0.72 0.42" xyaxes="0.757769 -0.652523 0 0.147191 0.170932 0.974226" fovy="45"/>{ball}
  </worldbody>
</mujoco>
"""


def body_element(root: ET.Element, name: str) -> ET.Element | None:
    for body in root.findall(".//body"):
        if body.get("name") == name:
            return body
    return None


def remove_named_geoms(body: ET.Element, suffix: str) -> None:
    for geom in list(body.findall("geom")):
        if (geom.get("name") or "").endswith(suffix):
            body.remove(geom)


def mesh_bbox(model, mujoco, mesh_name: str) -> dict[str, Any]:
    mid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_MESH, mesh_name)
    if mid < 0:
        raise ValueError(f"missing mesh {mesh_name}")
    adr = int(model.mesh_vertadr[mid])
    n = int(model.mesh_vertnum[mid])
    verts = model.mesh_vert[adr : adr + n]
    mn = verts.min(axis=0)
    mx = verts.max(axis=0)
    extent = mx - mn
    center = (mn + mx) / 2.0
    return {"min": mn, "max": mx, "extent": extent, "center": center, "vertices": n}


def add_arm_collision_proxies() -> dict[str, Any]:
    mujoco, source_model, _ = load_model(BASE_MODEL)
    tree = ET.parse(JOINT_TUNED_MODEL)
    root = tree.getroot()
    root.set("model", "arm_hand_export4_joint_limit_collision_proxy")

    arm_bodies = ["base_link", "link_1", "link_2", "link_3", "ee_mount"]
    proxies = []
    for body_name in arm_bodies:
        body = body_element(root, body_name)
        if body is None:
            proxies.append({"body": body_name, "status": "MISSING_BODY"})
            continue
        remove_named_geoms(body, "_arm_collision_proxy_box")
        bbox = mesh_bbox(source_model, mujoco, body_name)
        shrink = 0.82 if body_name != "ee_mount" else 0.72
        half_size = np.maximum(bbox["extent"] * 0.5 * shrink, np.array([0.006, 0.006, 0.006]))
        geom = ET.Element(
            "geom",
            {
                "name": f"{body_name}_arm_collision_proxy_box",
                "type": "box",
                "pos": fmt_vec(bbox["center"]),
                "size": fmt_vec(half_size),
                "rgba": "0.95 0.45 0.12 0.28",
                "contype": "1",
                "conaffinity": "2",
                "group": "4",
                "friction": "0.9 0.04 0.001",
            },
        )
        visual_geoms = [child for child in list(body) if child.tag == "geom"]
        if visual_geoms:
            insert_at = list(body).index(visual_geoms[-1]) + 1
            body.insert(insert_at, geom)
        else:
            body.insert(0, geom)
        proxies.append(
            {
                "body": body_name,
                "status": "ADDED",
                "bbox_center": bbox["center"],
                "bbox_extent": bbox["extent"],
                "proxy_size": half_size,
                "mesh_vertices": bbox["vertices"],
                "note": "Primitive box proxy; visual STL remains contype=0/conaffinity=0.",
            }
        )
    save_xml(root, COLLISION_MODEL)

    mujoco2, col_model, col_data = load_model(COLLISION_MODEL)
    ball_pos = compute_palm_ball_position(col_model, col_data, mujoco2)
    write_text(COLLISION_SCENE, make_scene_xml(COLLISION_MODEL.name, "arm_hand_export4_joint_limit_collision_proxy_scene", include_ball=False))
    write_text(COLLISION_BALL_SCENE, make_scene_xml(COLLISION_MODEL.name, "arm_hand_export4_joint_limit_collision_proxy_ball_scene", include_ball=True, ball_pos=ball_pos))
    return {"model": COLLISION_MODEL, "scene": COLLISION_SCENE, "ball_scene": COLLISION_BALL_SCENE, "proxies": proxies, "default_ball_pos": ball_pos}


def render_pose_set(scene: Path, out_dir: Path, collision: bool = False) -> dict[str, Any]:
    mujoco, model, data = load_model(scene)
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = data.xpos[palm_id].copy() if palm_id >= 0 else np.array([0.0, 0.0, 0.35])
    outputs = {}
    for pose_name, targets in POSES.items():
        applied = apply_qpos_targets(model, data, mujoco, targets)
        path = out_dir / f"{pose_name}.png"
        outputs[pose_name] = {
            "targets": applied,
            "render": render_image(model, data, mujoco, path, lookat, 0.78, 205, -22),
            "contact_summary": contact_summary(model, data, mujoco) if collision else None,
            "fingertips": fingertip_positions(model, data, mujoco),
        }
    return outputs


def freeze_entry_point() -> dict[str, Any]:
    mujoco, model, data = load_model(BASE_SCENE)
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = data.xpos[palm_id].copy() if palm_id >= 0 else np.array([0.0, 0.0, 0.35])
    render = render_image(model, data, mujoco, VIS_TUNING / "phase0_frozen_cad_mount_open.png", lookat, 0.78, 205, -22)
    joint_names = names(model, mujoco, mujoco.mjtObj.mjOBJ_JOINT)
    actuator_names = names(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR)
    mount_meta = json.loads(BASE_META.read_text(encoding="utf-8")) if BASE_META.exists() else {}
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "frozen_reference_model": str(BASE_MODEL),
        "frozen_reference_scene": str(BASE_SCENE),
        "status": "FROZEN_VIRTUAL_ENTRY_POINT",
        "model_summary": model_summary(model),
        "joint_names": joint_names,
        "actuator_names": actuator_names,
        "wrist_2_joint_type": "hinge" if "wrist_2_joint" in joint_names else "missing",
        "mount_alignment": mount_meta.get("mount", {}),
        "render": render,
        "notes": [
            "User visually accepted the CAD-frame mount as correct.",
            "+Y has been confirmed as the hand palm/grasp side.",
            "This file is a frozen reference. Later physics changes are generated as experiments under mjcf/.",
        ],
    }
    write_json(META / "arm_hand_stage1_virtual_entry_freeze.json", payload)
    lines = [
        "# Arm-Hand Stage1 Virtual Entry Freeze\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Freeze Decision\n\n",
        "The CAD-frame-mounted arm + export4 hand assembly is frozen as the current virtual-space entry point.\n\n",
        f"- Model: `{BASE_MODEL}`\n",
        f"- Scene: `{BASE_SCENE}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Joint count: `{len(joint_names)}`\n",
        f"- Actuator count: `{len(actuator_names)}`\n",
        f"- `wrist_2_joint`: `{payload['wrist_2_joint_type']}`\n",
        f"- Freeze render: `{render['file']}`\n\n",
        "## Known Issues Kept Out Of The Frozen Baseline\n\n",
        "- Full arm collision proxy is not complete in the frozen baseline.\n",
        "- The hand collision proxy is a smoke proxy, not final contact geometry.\n",
        "- Four-finger `*_mcp_flex_joint` names currently represent spread/abduction-adduction semantics; names are not changed.\n",
        "- No training or tendon routing is included.\n",
    ]
    write_text(DOCS / "arm_hand_stage1_virtual_entry_freeze.md", "".join(lines))
    return payload


def write_joint_tuning_reports(render_outputs: dict[str, Any]) -> dict[str, Any]:
    mujoco, model, data = load_model(JOINT_TUNED_SCENE)
    joint_rows = []
    for jid in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or f"joint_{jid}"
        body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.jnt_bodyid[jid])) or ""
        row = {
            "joint": name,
            "body": body,
            "type": int(model.jnt_type[jid]),
            "axis": model.jnt_axis[jid].copy(),
            "range": model.jnt_range[jid].copy() if bool(model.jnt_limited[jid]) else None,
        }
        if name.endswith("_mcp_flex_joint"):
            row["semantic_note"] = "User-confirmed spread / abduction-adduction semantic; name kept for compatibility."
        elif name.endswith("_mcp_abd_joint") or name.endswith("_pip_joint") or name.endswith("_dip_joint"):
            row["semantic_note"] = "Used as long-finger flexion/closure target in scripted smoke."
        elif name.startswith("thumb_"):
            row["semantic_note"] = "Thumb scripted-smoke target only; not Shadow-equivalent opposition."
        else:
            row["semantic_note"] = ""
        joint_rows.append(row)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": str(JOINT_TUNED_MODEL),
        "scene": str(JOINT_TUNED_SCENE),
        "status": "PASS_LOAD_AND_RENDER",
        "model_summary": model_summary(model),
        "scripted_poses": {name: {"targets": data["targets"], "render": data["render"]["file"]} for name, data in render_outputs.items()},
        "joint_table": joint_rows,
        "notes": [
            "No CAD/STL/joint-name changes were made.",
            "No broad new limits were introduced here; this experiment preserves the export4 tuned ranges already present in the CAD-mount candidate.",
            "The value of this phase is to make the semantic target table and visual pose set reproducible at arm+hand assembly scale.",
        ],
    }
    write_json(META / "arm_hand_joint_limit_tuning.json", payload)

    lines = [
        "# Arm-Hand Joint Limit And Pose Tuning Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Model: `{JOINT_TUNED_MODEL}`\n",
        f"- Scene: `{JOINT_TUNED_SCENE}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Model summary: `{payload['model_summary']}`\n\n",
        "## Scripted Poses\n\n",
        "| pose | render | applied target count |\n",
        "|---|---|---:|\n",
    ]
    for pose_name, row in render_outputs.items():
        lines.append(f"| {pose_name} | `{row['render']['file']}` | {len(row['targets'])} |\n")
    lines.extend(
        [
            "\n## Semantic Notes\n\n",
            "- `+Y` has been confirmed as palm/grasp side.\n",
            "- Four-finger `*_mcp_flex_joint` is treated as spread/abduction-adduction, despite the current name.\n",
            "- Four-finger closure uses current `*_mcp_abd_joint`, PIP, and DIP targets.\n",
            "- Thumb is kept as scripted-smoke only; no further target tuning is claimed here.\n\n",
            "## Joint Table\n\n",
            "| joint | body | range | note |\n",
            "|---|---|---|---|\n",
        ]
    )
    for row in joint_rows:
        rng = row["range"]
        range_text = "" if rng is None else f"{float(rng[0]):.3f} {float(rng[1]):.3f}"
        lines.append(f"| {row['joint']} | {row['body']} | `{range_text}` | {row['semantic_note']} |\n")
    write_text(DOCS / "arm_hand_joint_limit_tuning_report.md", "".join(lines))
    return payload


def run_staged_actuator_smoke(scene: Path, pin_ball: bool = True, steps_per_stage: int = 260) -> dict[str, Any]:
    mujoco, model, data = load_model(scene)
    ball_bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    ball_qadr = None
    ball_dadr = None
    initial_ball_pos = None
    if ball_bid >= 0:
        for jid in range(model.njnt):
            if int(model.jnt_bodyid[jid]) == ball_bid and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE:
                ball_qadr = int(model.jnt_qposadr[jid])
                ball_dadr = int(model.jnt_dofadr[jid])
                initial_ball_pos = data.xpos[ball_bid].copy()
                break
    stages = []
    finite = True
    for stage_name, targets in POSES.items():
        target_ctrl = ctrl_from_targets(model, mujoco, targets)
        start_ctrl = data.ctrl.copy()
        for step in range(max(1, steps_per_stage)):
            alpha = step / max(1, steps_per_stage - 1)
            data.ctrl[:] = (1.0 - alpha) * start_ctrl + alpha * target_ctrl
            if pin_ball and ball_qadr is not None and initial_ball_pos is not None:
                data.qpos[ball_qadr : ball_qadr + 3] = initial_ball_pos
                data.qpos[ball_qadr + 3 : ball_qadr + 7] = [1.0, 0.0, 0.0, 0.0]
                if ball_dadr is not None:
                    data.qvel[ball_dadr : ball_dadr + 6] = 0.0
            mujoco.mj_step(model, data)
            finite = finite and bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all() and np.isfinite(data.xpos).all())
        cs = contact_summary(model, data, mujoco)
        tips = fingertip_positions(model, data, mujoco)
        ball_pos = data.xpos[ball_bid].copy() if ball_bid >= 0 else np.full(3, np.nan)
        distances = {}
        for site, pos in tips.items():
            distances[site] = float(np.linalg.norm(np.asarray(pos) - ball_pos)) if not np.isnan(ball_pos).any() else float("nan")
        stages.append(
            {
                "stage": stage_name,
                "contact": cs,
                "fingertip_ball_distances": distances,
                "ball_position": ball_pos,
            }
        )
    ball_displacement = 0.0
    if ball_bid >= 0 and initial_ball_pos is not None:
        ball_displacement = float(np.linalg.norm(data.xpos[ball_bid] - initial_ball_pos))
    return {
        "scene": str(scene),
        "finite": finite,
        "ball_displacement": ball_displacement,
        "stages": stages,
        "status": "PASS" if finite else "FAIL",
    }


def write_collision_reports(build_info: dict[str, Any], pose_outputs: dict[str, Any], smoke: dict[str, Any]) -> dict[str, Any]:
    mujoco, model, data = load_model(COLLISION_SCENE)
    static_contacts = contact_summary(model, data, mujoco)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": str(COLLISION_MODEL),
        "scene": str(COLLISION_SCENE),
        "ball_scene": str(COLLISION_BALL_SCENE),
        "status": "PASS_LOAD_AND_SMOKE" if smoke["status"] == "PASS" else "PARTIAL",
        "model_summary": model_summary(model),
        "arm_collision_proxies": build_info["proxies"],
        "default_ball_pos": build_info["default_ball_pos"],
        "default_ball_radius": DEFAULT_BALL_RADIUS,
        "default_ball_local_offset_in_palm": DEFAULT_BALL_LOCAL_OFFSET,
        "static_open_contact": static_contacts,
        "pose_renders": {name: row["render"]["file"] for name, row in pose_outputs.items()},
        "ball_smoke": smoke,
        "limitations": [
            "Arm collision proxies are bbox-derived boxes for v0 external-object contact, not final robot self-collision geometry.",
            "Visual STL remains disabled for collision.",
            "Hand-hand and arm-arm self-collision are intentionally not fully enabled in v0 to avoid adjacent-link false positives.",
        ],
    }
    write_json(META / "arm_hand_collision_proxy.json", payload)

    hold = smoke["stages"][-1] if smoke["stages"] else {}
    lines = [
        "# Arm-Hand Collision Proxy V0 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Model: `{COLLISION_MODEL}`\n",
        f"- Scene: `{COLLISION_SCENE}`\n",
        f"- Ball scene: `{COLLISION_BALL_SCENE}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Open static contacts without ball: `{static_contacts['count']}`\n",
        f"- Open static max penetration without ball: `{static_contacts['max_penetration']:.6f} m`\n",
        f"- Default ball position: `{[round(v, 6) for v in build_info['default_ball_pos']]}`\n",
        f"- Default ball radius: `{DEFAULT_BALL_RADIUS:.3f} m`\n",
        f"- Default ball local offset in palm frame: `{[round(float(v), 4) for v in DEFAULT_BALL_LOCAL_OFFSET]}`\n",
        f"- Ball smoke status: `{smoke['status']}`\n",
        f"- Ball displacement during pinned smoke: `{smoke['ball_displacement']:.6f} m`\n",
    ]
    if hold:
        lines.append(f"- Hold contacts: `{hold['contact']['count']}`; hold max penetration: `{hold['contact']['max_penetration']:.6f} m`\n")
    lines.extend(
        [
            "\n## Added Arm Proxies\n\n",
            "| body | proxy size | bbox extent | status |\n",
            "|---|---|---|---|\n",
        ]
    )
    for proxy in build_info["proxies"]:
        lines.append(
            f"| {proxy['body']} | `{fmt_vec(proxy.get('proxy_size', []))}` | `{fmt_vec(proxy.get('bbox_extent', []))}` | {proxy['status']} |\n"
        )
    lines.extend(
        [
            "\n## Visual Checks\n\n",
            "| pose | render |\n",
            "|---|---|\n",
        ]
    )
    for name, row in pose_outputs.items():
        lines.append(f"| {name} | `{row['render']['file']}` |\n")
    lines.extend(
        [
            "\n## Limitations\n\n",
            "- These are simplified primitive proxies. They make the full arm+hand physically present to external objects, but are not final contact geometry.\n",
            "- Adjacent-link self-collision remains intentionally conservative/disabled in places.\n",
            "- This is still not training-ready.\n",
        ]
    )
    write_text(DOCS / "arm_hand_collision_proxy_report.md", "".join(lines))
    return payload


def write_active_docs(freeze: dict[str, Any], joint: dict[str, Any], collision: dict[str, Any]) -> None:
    active_index = [
        "# Arm-Hand Stage1 Active File Index\n\n",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}\n\n",
        "## Current Recommendation\n\n",
        "Use the Phase-2 collision-proxy experiment for physics smoke work, and keep the CAD mount candidate as the frozen alignment reference.\n\n",
        "## Open/View\n\n",
        f"- Visual/physics model: `{COLLISION_MODEL}`\n",
        f"- Scene without ball: `{COLLISION_SCENE}`\n",
        f"- Scene with palm-side ball: `{COLLISION_BALL_SCENE}`\n",
        f"- Frozen CAD mount reference: `{BASE_SCENE}`\n\n",
        "## Run\n\n",
        "- View current arm+hand: `python D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\view_arm_hand_export4.py`\n",
        "- Joint smoke on current CAD mount: `python D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\test_arm_hand_export4_joints.py`\n",
        "- Physics regression v0: `python D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\run_arm_hand_stage1_physics_regression.py`\n\n",
        "## Reports\n\n",
        f"- Freeze: `{DOCS / 'arm_hand_stage1_virtual_entry_freeze.md'}`\n",
        f"- Joint tuning: `{DOCS / 'arm_hand_joint_limit_tuning_report.md'}`\n",
        f"- Collision proxy: `{DOCS / 'arm_hand_collision_proxy_report.md'}`\n",
        f"- Closeout: `{DOCS / 'arm_hand_stage1_phase_closeout_report.md'}`\n",
    ]
    write_text(DOCS / "arm_hand_stage1_active_file_index.md", "".join(active_index))

    closeout = [
        "# Arm-Hand Stage1 Phase Closeout Report\n\n",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}\n\n",
        "## What Changed\n\n",
        "- Phase 0 froze the user-approved CAD mount as the virtual-space entry point.\n",
        "- Phase 1 generated an arm+hand joint-target/pose tuning experiment and visual pose renders.\n",
        "- Phase 2 added primitive arm collision proxy boxes while keeping all STL meshes visual-only.\n",
        "- A palm-side ball scene was generated from the current palm `+Y` direction.\n\n",
        "## Current Status\n\n",
        f"- Frozen reference model summary: `{freeze['model_summary']}`\n",
        f"- Joint tuned status: `{joint['status']}`\n",
        f"- Collision proxy status: `{collision['status']}`\n",
        f"- Collision model summary: `{collision['model_summary']}`\n",
        f"- Open static contact count without ball: `{collision['static_open_contact']['count']}`\n",
        f"- Open static max penetration without ball: `{collision['static_open_contact']['max_penetration']:.6f} m`\n\n",
        "## Blocker / Major / Minor\n\n",
        "- BLOCKER: none found in load/render generation for the current Phase-2 experiment.\n",
        "- MAJOR: collision proxy is still v0 and not anatomically tuned; do not train on it.\n",
        "- MAJOR: thumb remains smoke-usable but not Shadow-equivalent dexterity.\n",
        "- MINOR: current `*_mcp_flex_joint` names do not match their spread semantics; keep aliases in adapters instead of renaming.\n\n",
        "## Next Step\n\n",
        "Run the regression script, inspect its report, then decide whether to start tiny dataset collection v0. Training is still explicitly blocked.\n",
    ]
    write_text(DOCS / "arm_hand_stage1_phase_closeout_report.md", "".join(closeout))

    readme = [
        "# Arm-Hand Stage1 Export Workspace\n\n",
        "This workspace contains the current arm + export4 hand assembly work.\n\n",
        "## Current Files\n\n",
        f"- Frozen CAD mount scene: `{BASE_SCENE}`\n",
        f"- Active physics-v0 scene: `{COLLISION_SCENE}`\n",
        f"- Active physics-v0 ball scene: `{COLLISION_BALL_SCENE}`\n\n",
        "## Recommended Commands\n\n",
        "```powershell\n",
        "python D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\run_arm_hand_stage1_physics_regression.py\n",
        "python D:\\tendon_project\\simulations\\models\\arm_hand_stage1_export\\view_arm_hand_export4.py\n",
        "```\n\n",
        "## Guardrails\n\n",
        "- Do not edit CAD/STL from this workspace.\n",
        "- Do not overwrite the frozen CAD mount candidate.\n",
        "- Do not train yet.\n",
        "- Collision proxy is v0 and must be improved before real training or large datasets.\n",
    ]
    write_text(ROOT / "README.md", "".join(readme))


def main() -> None:
    ensure_dirs()
    freeze = freeze_entry_point()
    copy_joint_tuned_model()
    joint_renders = render_pose_set(JOINT_TUNED_SCENE, VIS_TUNING, collision=False)
    joint = write_joint_tuning_reports(joint_renders)
    collision_build = add_arm_collision_proxies()
    collision_renders = render_pose_set(COLLISION_SCENE, VIS_COLLISION, collision=True)
    smoke = run_staged_actuator_smoke(COLLISION_BALL_SCENE, pin_ball=True)
    collision = write_collision_reports(collision_build, collision_renders, smoke)
    write_active_docs(freeze, joint, collision)
    print("Phase advance generated:")
    for path in [
        DOCS / "arm_hand_stage1_virtual_entry_freeze.md",
        JOINT_TUNED_MODEL,
        JOINT_TUNED_SCENE,
        DOCS / "arm_hand_joint_limit_tuning_report.md",
        COLLISION_MODEL,
        COLLISION_SCENE,
        COLLISION_BALL_SCENE,
        DOCS / "arm_hand_collision_proxy_report.md",
        DOCS / "arm_hand_stage1_active_file_index.md",
        DOCS / "arm_hand_stage1_phase_closeout_report.md",
    ]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
