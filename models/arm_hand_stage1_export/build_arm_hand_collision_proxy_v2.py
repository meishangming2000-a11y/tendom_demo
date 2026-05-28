#!/usr/bin/env python3
"""Build collision-proxy v2 for the arm + export4 hand.

v2 starts from the accepted v1 model and only changes palm-side collision
proxies. It does not touch CAD, STL, joints, actuators, or names.

Intent:
- keep the useful v1 palm-side contact pad;
- add one shallow palm cup rail on the measured sliding side;
- keep fingertip spheres at the v1 12 mm size;
- keep the result as a separate experiment.
"""

from __future__ import annotations

import json
import shutil
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
MJCF = ROOT / "mjcf"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
ARCHIVE = ROOT / "archive"

SRC_MODEL = MJCF / "arm_hand_export4_collision_proxy_v1.xml"
OUT_MODEL = MJCF / "arm_hand_export4_collision_proxy_v2.xml"
OUT_SCENE = MJCF / "scene_arm_hand_export4_collision_proxy_v2.xml"
OUT_BALL_SCENE = MJCF / "scene_arm_hand_export4_collision_proxy_v2_ball.xml"
REPORT = DOCS / "arm_hand_collision_proxy_v2_report.md"
META_OUT = META / "arm_hand_collision_proxy_v2.json"

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
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value


def backup(path: Path) -> str | None:
    if not path.exists():
        return None
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = ARCHIVE / f"{path.name}.before_collision_proxy_v2_{stamp}"
    shutil.copy2(path, dst)
    return str(dst)


def body(root: ET.Element, name: str) -> ET.Element:
    for item in root.findall(".//body"):
        if item.get("name") == name:
            return item
    raise KeyError(name)


def remove_named_geoms(parent: ET.Element, prefixes: tuple[str, ...]) -> list[str]:
    removed: list[str] = []
    for child in list(parent):
        if child.tag != "geom":
            continue
        name = child.get("name") or ""
        if any(name.startswith(prefix) for prefix in prefixes):
            parent.remove(child)
            removed.append(name)
    return removed


def add_geom(parent: ET.Element, attrs: dict[str, str]) -> None:
    parent.append(ET.Element("geom", attrs))


def set_tip_sphere_size(root: ET.Element, size: str) -> list[str]:
    changed: list[str] = []
    for geom in root.findall(".//geom"):
        name = geom.get("name") or ""
        if name.endswith("_tip_collision_proxy_sphere"):
            geom.set("size", size)
            geom.set("friction", "1.15 0.06 0.006")
            changed.append(name)
    return changed


def scene_xml(include_file: str, model_name: str, ball_pos: list[float] | None = None) -> str:
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

    backups = {str(path): backup(path) for path in [OUT_MODEL, OUT_SCENE, OUT_BALL_SCENE, REPORT, META_OUT]}

    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
    root.set("model", "arm_hand_export4_collision_proxy_v2")

    palm = body(root, "palm_link")
    removed = remove_named_geoms(
        palm,
        (
            "palm_link_palmar_pad_collision_proxy_v1",
            "palm_link_palmar_pad_collision_proxy_v2",
            "palm_link_negative_z_cup_rail_collision_proxy_v2",
        ),
    )

    add_geom(
        palm,
        {
            "name": "palm_link_palmar_pad_collision_proxy_v2",
            "type": "box",
            "pos": "0.018 0.087 -0.012",
            "size": "0.052 0.0055 0.044",
            "rgba": "0.08 0.95 0.72 0.30",
            "contype": "1",
            "conaffinity": "2",
            "group": "3",
            "friction": "1.6 0.12 0.008",
            "solref": "0.007 1",
            "solimp": "0.93 0.985 0.001",
        },
    )
    add_geom(
        palm,
        {
            "name": "palm_link_negative_z_cup_rail_collision_proxy_v2",
            "type": "box",
            "pos": "0.018 0.106 -0.059",
            "size": "0.050 0.018 0.004",
            "rgba": "0.05 0.65 1.00 0.28",
            "contype": "1",
            "conaffinity": "2",
            "group": "3",
            "friction": "1.4 0.10 0.006",
            "solref": "0.007 1",
            "solimp": "0.93 0.985 0.001",
        },
    )
    changed_tips = set_tip_sphere_size(root, "0.012000")

    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUT_MODEL, encoding="utf-8", xml_declaration=True)

    ball_pos = compute_ball_world(OUT_MODEL)
    OUT_SCENE.write_text(scene_xml(OUT_MODEL.name, "arm_hand_export4_collision_proxy_v2_scene"), encoding="utf-8")
    OUT_BALL_SCENE.write_text(
        scene_xml(OUT_MODEL.name, "arm_hand_export4_collision_proxy_v2_ball_scene", ball_pos=ball_pos),
        encoding="utf-8",
    )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_model": SRC_MODEL,
        "model": OUT_MODEL,
        "scene": OUT_SCENE,
        "ball_scene": OUT_BALL_SCENE,
        "ball_radius": BALL_RADIUS,
        "ball_local_offset": BALL_LOCAL_OFFSET,
        "ball_world_position": ball_pos,
        "backups": backups,
        "removed_geoms": removed,
        "changed_tip_geoms": changed_tips,
        "changes": [
            "Replaced v1 palm pad with v2 palm pad using slightly wider local-Z coverage and higher friction.",
            "Added one shallow negative-Z palm cup rail at measured free-ball slide side.",
            "Kept fingertip spheres at v1 12 mm size and did not modify visual meshes.",
            "Kept CAD/STL/joint tree/joint names/actuators unchanged.",
        ],
        "design_note": (
            "Free-ball analysis showed gravity and early ball motion in palm frame are mainly along local -Z and -Y. "
            "The v2 rail targets the local -Z slide path without enclosing the ball or forcing grasp contact."
        ),
    }
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Collision Proxy V2 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source model: `{SRC_MODEL}`\n",
        f"- V2 model: `{OUT_MODEL}`\n",
        f"- V2 scene: `{OUT_SCENE}`\n",
        f"- V2 ball scene: `{OUT_BALL_SCENE}`\n",
        f"- Ball radius: `{BALL_RADIUS:.3f} m`\n",
        f"- Ball palm-local offset: `{BALL_LOCAL_OFFSET.tolist()}`\n",
        f"- Ball world position: `{[round(v, 6) for v in ball_pos]}`\n\n",
        "## Design\n\n",
        "- V2 is separate from v1 and does not overwrite the frozen mount or old proxy models.\n",
        "- Replaced the v1 palm pad with `palm_link_palmar_pad_collision_proxy_v2`.\n",
        "- Added `palm_link_negative_z_cup_rail_collision_proxy_v2` on the measured local `-Z` slide side.\n",
        "- Increased palm-pad friction modestly; this is still a smoke proxy, not a final physical material model.\n",
        "- Did not edit CAD, STL, joint tree, joint names, tendon routing, or training code.\n\n",
        "## Evaluation Goal\n\n",
        "- Preserve low initial penetration near the palm.\n",
        "- Increase early palm-side contact stability without trapping the ball artificially.\n",
        "- Keep scripted hold max penetration below about `5 mm`.\n",
        "- Keep contact geoms interpretable: palm pad / palm rail / finger / thumb, not hand back or flange.\n",
    ]
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Generated: {OUT_MODEL}")
    print(f"Generated: {OUT_BALL_SCENE}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
