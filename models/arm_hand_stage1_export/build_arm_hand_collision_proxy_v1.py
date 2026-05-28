#!/usr/bin/env python3
"""Build collision-proxy v1 for the arm + export4 hand.

v1 keeps the v0 joint tree and visual meshes untouched. It only changes
primitive collision geoms in a new experimental MJCF:

- adds a thin palmar pad to `palm_link` so a free ball can initially contact
  the palm side instead of immediately falling away;
- reduces fingertip sphere radii from 15 mm to 12 mm;
- keeps arm collision proxies and clean STL visual geoms as-is.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
MJCF = ROOT / "mjcf"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
SRC_MODEL = MJCF / "arm_hand_export4_joint_limit_collision_proxy.xml"
OUT_MODEL = MJCF / "arm_hand_export4_collision_proxy_v1.xml"
OUT_SCENE = MJCF / "scene_arm_hand_export4_collision_proxy_v1.xml"
OUT_BALL_SCENE = MJCF / "scene_arm_hand_export4_collision_proxy_v1_ball.xml"
REPORT = DOCS / "arm_hand_collision_proxy_v1_report.md"
META_OUT = META / "arm_hand_collision_proxy_v1.json"

BALL_RADIUS = 0.028
BALL_LOCAL_OFFSET = np.array([0.04, 0.12, -0.02], dtype=np.float64)


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def body(root: ET.Element, name: str) -> ET.Element:
    for item in root.findall(".//body"):
        if item.get("name") == name:
            return item
    raise KeyError(name)


def remove_geom(root_or_body: ET.Element, name: str) -> None:
    for parent in root_or_body.iter():
        for geom in list(parent.findall("geom")):
            if geom.get("name") == name:
                parent.remove(geom)


def set_geom_size(root: ET.Element, suffix: str, size: str) -> list[str]:
    changed = []
    for geom in root.findall(".//geom"):
        name = geom.get("name") or ""
        if name.endswith(suffix):
            geom.set("size", size)
            changed.append(name)
    return changed


def scene_xml(include_file: str, model_name: str, *, ball_pos: list[float] | None = None) -> str:
    ball = ""
    if ball_pos is not None:
        x, y, z = ball_pos
        ball = f"""
    <body name="ball" pos="{x:.9g} {y:.9g} {z:.9g}">
      <freejoint name="ball_freejoint"/>
      <geom name="ball_geom" type="sphere" size="{BALL_RADIUS:.9g}" mass="0.025" rgba="1 0.45 0.08 1" contype="2" conaffinity="1" friction="1.2 0.08 0.003"/>
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


def compute_ball_world(model_path: Path) -> list[float]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    palm_pos = data.xpos[palm_id].copy()
    palm_mat = data.xmat[palm_id].reshape(3, 3)
    return (palm_pos + palm_mat @ BALL_LOCAL_OFFSET).tolist()


def main() -> None:
    if not SRC_MODEL.exists():
        raise FileNotFoundError(SRC_MODEL)
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    MJCF.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
    root.set("model", "arm_hand_export4_collision_proxy_v1")

    palm = body(root, "palm_link")
    remove_geom(palm, "palm_link_palmar_pad_collision_proxy_v1")
    pad = ET.Element(
        "geom",
        {
            "name": "palm_link_palmar_pad_collision_proxy_v1",
            "type": "box",
            "pos": "0.018 0.087 -0.012",
            "size": "0.052 0.0055 0.042",
            "rgba": "0.08 0.95 0.72 0.30",
            "contype": "1",
            "conaffinity": "2",
            "group": "3",
            "friction": "1.2 0.08 0.003",
            "solref": "0.008 1",
            "solimp": "0.92 0.98 0.001",
        },
    )
    palm_geoms = [child for child in list(palm) if child.tag == "geom"]
    insert_at = list(palm).index(palm_geoms[-1]) + 1 if palm_geoms else 0
    palm.insert(insert_at, pad)

    changed_tips = set_geom_size(root, "_tip_collision_proxy_sphere", "0.012000")

    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUT_MODEL, encoding="utf-8", xml_declaration=True)

    ball_pos = compute_ball_world(OUT_MODEL)
    OUT_SCENE.write_text(scene_xml(OUT_MODEL.name, "arm_hand_export4_collision_proxy_v1_scene"), encoding="utf-8")
    OUT_BALL_SCENE.write_text(scene_xml(OUT_MODEL.name, "arm_hand_export4_collision_proxy_v1_ball_scene", ball_pos=ball_pos), encoding="utf-8")

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_model": SRC_MODEL,
        "model": OUT_MODEL,
        "scene": OUT_SCENE,
        "ball_scene": OUT_BALL_SCENE,
        "ball_radius": BALL_RADIUS,
        "ball_local_offset": BALL_LOCAL_OFFSET,
        "ball_world_position": ball_pos,
        "changes": [
            "Added palm_link_palmar_pad_collision_proxy_v1 thin box at palm +Y side.",
            "Reduced *_tip_collision_proxy_sphere size from 0.015 m to 0.012 m.",
            "Kept clean STL visual-only and kept joint tree/names unchanged.",
        ],
        "changed_tip_geoms": changed_tips,
    }
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Collision Proxy V1 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source model: `{SRC_MODEL}`\n",
        f"- V1 model: `{OUT_MODEL}`\n",
        f"- V1 scene: `{OUT_SCENE}`\n",
        f"- V1 ball scene: `{OUT_BALL_SCENE}`\n",
        f"- Ball radius: `{BALL_RADIUS:.3f} m`\n",
        f"- Ball palm-local offset: `{BALL_LOCAL_OFFSET.tolist()}`\n",
        f"- Ball world position: `{[round(v, 6) for v in ball_pos]}`\n\n",
        "## Changes\n\n",
        "- Added a thin palmar pad on `palm_link` so the free ball has a physical palm-side surface to contact.\n",
        "- Reduced fingertip collision spheres from `0.015 m` to `0.012 m` to reduce over-large fingertip contact.\n",
        "- Did not modify CAD, STL, joint names, or joint tree.\n\n",
        "## Tip Geoms Changed\n\n",
    ]
    for name in changed_tips:
        lines.append(f"- `{name}`\n")
    lines.extend(
        [
            "\n## TODO\n\n",
            "- Run free-ball and scripted close smoke before promoting v1 to active.\n",
            "- Visually inspect palm pad and fingertip proxy behavior.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Generated: {OUT_MODEL}")
    print(f"Generated: {OUT_BALL_SCENE}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
