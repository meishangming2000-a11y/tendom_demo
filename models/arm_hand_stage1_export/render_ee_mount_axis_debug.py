#!/usr/bin/env python3
"""Render ee_mount local axis markers for flange-frame diagnosis."""

from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
BASE_XML = ROOT / "arm_hand_export4_palmar_ypos_candidate.xml"
DEBUG_XML = ROOT / "arm_hand_export4_ee_mount_axis_debug.xml"
DEBUG_SCENE = ROOT / "scene_arm_hand_export4_ee_mount_axis_debug.xml"
VIS = ROOT / "visual_checks_mount_alignment"
DOCS = ROOT / "docs"
META = ROOT / "metadata" / "ee_mount_axis_debug.json"
REPORT = DOCS / "ee_mount_axis_debug.md"
ARCHIVE = ROOT / "archive"


def backup(path: Path, tag: str) -> None:
    if not path.exists():
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, ARCHIVE / f"{path.stem}.{tag}.{stamp}{path.suffix}")


def find_body(root: ET.Element, name: str) -> ET.Element | None:
    for body in root.findall(".//body"):
        if body.get("name") == name:
            return body
    return None


def add_site(body: ET.Element, name: str, pos: str, rgba: str, size: str = "0.008") -> None:
    for old in body.findall("site"):
        if old.get("name") == name:
            body.remove(old)
    ET.SubElement(body, "site", {"name": name, "type": "sphere", "pos": pos, "size": size, "rgba": rgba})


def write_debug_xml() -> None:
    tree = ET.parse(BASE_XML)
    root = tree.getroot()
    root.set("model", "arm_hand_export4_ee_mount_axis_debug")

    ee_mount = find_body(root, "ee_mount")
    ee_tool = find_body(root, "ee_tool_frame")
    if ee_mount is None or ee_tool is None:
        raise RuntimeError("Could not find ee_mount or ee_tool_frame")

    add_site(ee_mount, "debug_ee_mount_origin_white", "0 0 0", "1 1 1 1", "0.007")
    add_site(ee_mount, "debug_ee_mount_plus_x_red", "0.060 0 0", "1 0 0 1")
    add_site(ee_mount, "debug_ee_mount_minus_x_darkred", "-0.060 0 0", "0.45 0 0 1")
    add_site(ee_mount, "debug_ee_mount_plus_y_green", "0 0.060 0", "0 1 0 1")
    add_site(ee_mount, "debug_ee_mount_minus_y_darkgreen", "0 -0.060 0", "0 0.35 0 1")
    add_site(ee_mount, "debug_ee_mount_plus_z_blue", "0 0 0.060", "0.05 0.2 1 1")
    add_site(ee_mount, "debug_ee_mount_minus_z_yellow", "0 0 -0.060", "1 0.85 0.05 1")
    add_site(ee_tool, "debug_ee_tool_frame_orange", "0 0 0", "1 0.45 0 1", "0.008")

    backup(DEBUG_XML, "before_axis_debug")
    ET.indent(tree, space="  ")
    tree.write(DEBUG_XML, encoding="utf-8", xml_declaration=True)

    scene = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"arm_hand_export4_ee_mount_axis_debug_scene\">
  <include file=\"{DEBUG_XML.name}\"/>
  <visual>
    <rgba haze=\"0.15 0.25 0.35 1\"/>
    <quality shadowsize=\"8192\"/>
    <global azimuth=\"205\" elevation=\"-22\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"skybox\" builtin=\"gradient\" rgb1=\"0.30 0.50 0.70\" rgb2=\"0.00 0.00 0.00\" width=\"512\" height=\"3072\"/>
    <texture type=\"2d\" name=\"ground_checker\" builtin=\"checker\" mark=\"edge\" rgb1=\"0.20 0.30 0.40\" rgb2=\"0.10 0.20 0.30\" markrgb=\"0.80 0.80 0.80\" width=\"300\" height=\"300\"/>
    <material name=\"ground\" texture=\"ground_checker\" texrepeat=\"5 5\" texuniform=\"true\" reflectance=\"0.20\"/>
  </asset>
  <worldbody>
    <light name=\"fill_light\" pos=\"0 0 1\"/>
    <light name=\"key_light\" pos=\"0.3 0 1.5\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"floor\" type=\"plane\" pos=\"0 0 -0.12\" size=\"0 0 0.05\" material=\"ground\" contype=\"0\" conaffinity=\"4\"/>
  </worldbody>
</mujoco>
"""
    backup(DEBUG_SCENE, "before_axis_debug_scene")
    DEBUG_SCENE.write_text(scene, encoding="utf-8")


def render() -> dict[str, Any]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(DEBUG_SCENE))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    ee_mount_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ee_mount")
    ee_tool_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ee_tool_frame")
    hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "hand_base_link")
    lookat = (data.xpos[ee_tool_id] + data.xpos[hand_id]) / 2.0
    specs = {
        "axis_flange_closeup": (data.xpos[ee_tool_id], 0.20, 205, -4),
        "axis_wrist_closeup": (lookat, 0.22, 110, -12),
        "axis_top": (data.xpos[ee_mount_id], 0.42, 180, -78),
        "axis_side": (data.xpos[ee_mount_id], 0.36, 95, -12),
    }
    VIS.mkdir(parents=True, exist_ok=True)
    views = {}
    for name, (view_lookat, distance, azimuth, elevation) in specs.items():
        renderer = mujoco.Renderer(model, width=1280, height=900)
        try:
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = np.asarray(view_lookat, dtype=np.float64)
            camera.distance = distance
            camera.azimuth = azimuth
            camera.elevation = elevation
            renderer.update_scene(data, camera=camera)
            image = renderer.render()
        finally:
            renderer.close()
        out = VIS / f"{name}.png"
        imageio.imwrite(out, image)
        views[name] = str(out)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "debug_xml": str(DEBUG_XML),
        "debug_scene": str(DEBUG_SCENE),
        "views": views,
        "legend": {
            "+X": "red",
            "-X": "dark red",
            "+Y": "green",
            "-Y": "dark green",
            "+Z": "blue",
            "-Z": "yellow",
            "ee_tool_frame": "orange",
            "ee_mount_origin": "white",
        },
        "ee_mount_world": data.xpos[ee_mount_id].tolist(),
        "ee_tool_frame_world": data.xpos[ee_tool_id].tolist(),
        "hand_base_world": data.xpos[hand_id].tolist(),
        "ee_tool_frame_local_pos_in_ee_mount": model.body_pos[ee_tool_id].tolist(),
    }


def write_report(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    backup(META, "before_axis_debug_meta")
    META.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# EE Mount Axis Debug\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Legend\n\n",
        "- `+X`: red\n",
        "- `-X`: dark red\n",
        "- `+Y`: green\n",
        "- `-Y`: dark green\n",
        "- `+Z`: blue\n",
        "- `-Z`: yellow\n",
        "- `ee_tool_frame`: orange\n",
        "- `ee_mount` origin: white\n\n",
        "## Numeric Observation\n\n",
        f"- `ee_tool_frame` local pos in `ee_mount`: `{payload['ee_tool_frame_local_pos_in_ee_mount']}`\n\n",
        "## Views\n\n",
    ]
    for name, path in payload["views"].items():
        lines.append(f"- `{name}`: `{path}`\n")
    lines.append("\nUse these views to decide which `ee_mount` local side corresponds to the visible flange/mounting face.\n")
    DOCS.mkdir(parents=True, exist_ok=True)
    backup(REPORT, "before_axis_debug_report")
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    write_debug_xml()
    payload = render()
    write_report(payload)
    print(f"Saved report: {REPORT}")
    for name, path in payload["views"].items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
