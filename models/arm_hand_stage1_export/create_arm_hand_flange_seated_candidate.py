#!/usr/bin/env python3
"""Create the selected arm-hand flange-seated candidate.

This keeps CAD/STL/joint trees untouched and changes only the fixed local
transform of `hand_base_link` under arm `ee_tool_frame`.
"""

from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
BASE_XML = ROOT / "arm_hand_export4_palmar_ypos_candidate.xml"
OUT_XML = ROOT / "arm_hand_export4_flange_seated_candidate.xml"
SCENE_XML = ROOT / "scene_arm_hand_export4_flange_seated_candidate.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata" / "arm_hand_export4_flange_seated_candidate.json"
REPORT = DOCS / "arm_hand_export4_flange_seated_candidate_report.md"
ARCHIVE = ROOT / "archive"

# Selected from the mount-alignment grid plus ee_mount axis diagnosis.
# The visible flange/bolt plate is on the ee_mount local +Y side. Converting
# the difference between ee_tool_frame.y=0.01956 and the ee_mount +Y mesh
# boundary y=0.034106 into ee_tool_frame coordinates is almost exactly
# +0.01455 m along ee_tool_frame local +Z.
SELECTED_HAND_POS = (0.0, 0.0, 0.01455)
SELECTED_HAND_QUAT = (1.0, 0.0, 0.0, 0.0)


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


def vec_text(values: tuple[float, ...]) -> str:
    return " ".join(f"{v:.6g}" for v in values)


def create_candidate() -> dict[str, Any]:
    tree = ET.parse(BASE_XML)
    root = tree.getroot()
    root.set("model", "arm_hand_export4_flange_seated_candidate")

    hand_base = find_body(root, "hand_base_link")
    if hand_base is None:
        raise RuntimeError("Could not find hand_base_link")
    hand_base.set("pos", vec_text(SELECTED_HAND_POS))
    hand_base.set("quat", vec_text(SELECTED_HAND_QUAT))

    backup(OUT_XML, "before_flange_seated_candidate")
    ET.indent(tree, space="  ")
    tree.write(OUT_XML, encoding="utf-8", xml_declaration=True)

    scene = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"arm_hand_export4_flange_seated_scene\">
  <include file=\"{OUT_XML.name}\"/>
  <statistic extent=\"0.9\" center=\"0 0 0.12\"/>
  <visual>
    <rgba haze=\"0.15 0.25 0.35 1\"/>
    <quality shadowsize=\"8192\"/>
    <global azimuth=\"205\" elevation=\"-22\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"skybox\" builtin=\"gradient\" rgb1=\"0.30 0.50 0.70\" rgb2=\"0.00 0.00 0.00\" width=\"512\" height=\"3072\"/>
    <texture type=\"2d\" name=\"arm_hand_ground_checker\" builtin=\"checker\" mark=\"edge\" rgb1=\"0.20 0.30 0.40\" rgb2=\"0.10 0.20 0.30\" markrgb=\"0.80 0.80 0.80\" width=\"300\" height=\"300\"/>
    <material name=\"arm_hand_ground\" texture=\"arm_hand_ground_checker\" texrepeat=\"5 5\" texuniform=\"true\" reflectance=\"0.20\"/>
  </asset>
  <worldbody>
    <light name=\"arm_hand_fill_light\" pos=\"0 0 1\"/>
    <light name=\"arm_hand_key_light\" pos=\"0.3 0 1.5\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"arm_hand_floor\" type=\"plane\" pos=\"0 0 -0.12\" size=\"0 0 0.05\" material=\"arm_hand_ground\" contype=\"0\" conaffinity=\"4\"/>
    <camera name=\"arm_hand_overview\" pos=\"-0.62 -0.72 0.42\" xyaxes=\"0.757769 -0.652523 0 0.147191 0.170932 0.974226\" fovy=\"45\"/>
    <camera name=\"arm_hand_side\" pos=\"0.65 -0.25 0.35\" xyaxes=\"0.358979 0.933346 0 -0.171268 0.0658725 0.98302\" fovy=\"45\"/>
    <camera name=\"arm_hand_wrist_closeup\" pos=\"0.25 -0.32 0.24\" xyaxes=\"0.788 0.616 0 -0.185 0.237 0.954\" fovy=\"36\"/>
  </worldbody>
</mujoco>
"""
    backup(SCENE_XML, "before_flange_seated_scene")
    SCENE_XML.write_text(scene, encoding="utf-8")

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_xml": str(BASE_XML),
        "out_xml": str(OUT_XML),
        "scene_xml": str(SCENE_XML),
        "attachment_parent": "ee_tool_frame",
        "attached_body": "hand_base_link",
        "hand_root_pos_in_ee_tool_frame": list(SELECTED_HAND_POS),
        "hand_root_quat_in_ee_tool_frame": list(SELECTED_HAND_QUAT),
        "selection_reason": [
            "Identity was kinematically valid but used the internal ee_tool_frame origin.",
            "Axis debug shows the visible flange plate is on ee_mount local +Y.",
            "The ee_tool_frame is about 14.5 mm inside that +Y mesh boundary.",
            "The equivalent child offset is approximately ee_tool_frame local +Z = 14.55 mm.",
        ],
        "limits": [
            "This is MuJoCo fixed-transform calibration only.",
            "It is not a CAD-certified flange adapter.",
            "CAD/STL/joint tree/joint names were not modified.",
        ],
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    backup(META, "before_flange_seated_meta")
    META.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm + Export4 Flange-Seated Candidate\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## What Changed\n\n",
        "Only the fixed local transform of `hand_base_link` under arm `ee_tool_frame` was changed.\n\n",
        f"- Hand root local pos: `{payload['hand_root_pos_in_ee_tool_frame']}`\n",
        f"- Hand root local quat: `{payload['hand_root_quat_in_ee_tool_frame']}`\n",
        "- CAD/STL/joint tree/joint names unchanged.\n\n",
        "## Why\n\n",
        "The first identity attachment was kinematically correct, but it used the arm's internal `ee_tool_frame` origin rather than the visible flange face. ",
        "Axis debug showed that the visible bolt/flange plate is on the `ee_mount` local `+Y` side. ",
        "The `ee_tool_frame` is about `14.5 mm` inside that mesh boundary, and this direction maps to approximately `ee_tool_frame` local `+Z`. ",
        "A `+14.55 mm` local Z offset is selected as the first flange-face candidate.\n\n",
        "## Outputs\n\n",
        f"- MJCF: `{payload['out_xml']}`\n",
        f"- Scene: `{payload['scene_xml']}`\n\n",
        "## Caveat\n\n",
        "This is still not final mechanical flange calibration. If the exact flange face or bolt pattern matters, the arm CAD/export should expose a dedicated flange-mount frame and the hand should expose a dedicated wrist-mount frame.\n",
    ]
    DOCS.mkdir(parents=True, exist_ok=True)
    backup(REPORT, "before_flange_seated_report")
    REPORT.write_text("".join(lines), encoding="utf-8")
    return payload


def main() -> None:
    payload = create_candidate()
    print(f"Saved MJCF: {payload['out_xml']}")
    print(f"Saved scene: {payload['scene_xml']}")
    print(f"Saved report: {REPORT}")


if __name__ == "__main__":
    main()
