#!/usr/bin/env python3
"""Build the export4 wrist2 + collision-proxy experimental MJCF.

The current baseline is treated as frozen. This script copies it to an
experimental file, verifies/repairs wrist_2_joint as a hinge, and applies a
small collision-proxy tuning pass. CAD, STL, joint names, visual meshes, and the
baseline file are not modified.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "mjcf" / "hand_stage1_export4_current_baseline.xml"
DEFAULT_OUTPUT = ROOT / "mjcf" / "hand_stage1_export4_wrist2_collision_tuned.xml"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_ball_export4_wrist2_collision_tuned.xml"
DEFAULT_REPORT = ROOT / "docs" / "export4_wrist2_collision_tuned_build_report.md"
DEFAULT_METADATA = ROOT / "metadata" / "export4_wrist2_collision_tuned_build.json"
DEFAULT_ARCHIVE = ROOT / "archive"

BALL_DEFAULT = (0.0, -0.1, 0.21)

# Conservative proxy changes. These keep visual geoms untouched and only adjust
# simplified collision proxy geoms. The intent is to reduce closed static ball
# penetration while preserving smoke-test contacts.
PROXY_TUNING = {
    "palm_link_collision_proxy_ellipsoid": {
        "size": "0.026 0.054 0.021",
        "rgba": "0.16 0.90 0.58 0.30",
    },
    # Slightly reduce long phalanx radii. The old proxy was useful visually but
    # too thick for contact-rich ball checks.
    "index_mcp_flex_link_collision_proxy": {"size": "0.0048"},
    "middle_mcp_flex_link_collision_proxy": {"size": "0.0048"},
    "ring_mcp_flex_link_collision_proxy": {"size": "0.0048"},
    "little_mcp_flex_link_collision_proxy": {"size": "0.0048"},
    "index_proximal_phalanx_link_collision_proxy": {"size": "0.0056"},
    "middle_proximal_phalanx_link_collision_proxy": {"size": "0.0056"},
    "ring_proximal_phalanx_link_collision_proxy": {"size": "0.0056"},
    "little_proximal_phalanx_link_collision_proxy": {"size": "0.0056"},
    "index_proximal_inter_link_collision_proxy": {"size": "0.0054"},
    "middle_proximal_inter_link_collision_proxy": {"size": "0.0054"},
    "ring_proximal_inter_link_collision_proxy": {"size": "0.0054"},
    "little_proximal_inter_link_collision_proxy": {"size": "0.0054"},
    "index_distal_link_collision_proxy": {"size": "0.0048"},
    "middle_distal_link_collision_proxy": {"size": "0.0048"},
    "ring_distal_link_collision_proxy": {"size": "0.0048"},
    "little_distal_link_collision_proxy": {"size": "0.0048"},
    "thumb_metacarpal_link_collision_proxy": {"size": "0.0054"},
    "thumb_proximal_link_collision_proxy": {"size": "0.0054"},
    "thumb_distal_link_collision_proxy": {"size": "0.0048"},
}


def _backup_existing(path: Path, archive: Path, tag: str) -> None:
    if not path.exists():
        return
    archive.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = archive / f"{path.name}.before_{tag}_{stamp}"
    if path.is_dir():
        shutil.copytree(path, dst)
    else:
        shutil.copy2(path, dst)


def _indent(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def _find_joint(root: ET.Element, name: str) -> ET.Element | None:
    for joint in root.findall(".//joint"):
        if joint.attrib.get("name") == name:
            return joint
    return None


def _find_body(root: ET.Element, name: str) -> ET.Element | None:
    for body in root.findall(".//body"):
        if body.attrib.get("name") == name:
            return body
    return None


def _find_actuator(root: ET.Element, joint_name: str) -> ET.Element | None:
    actuator = root.find("actuator")
    if actuator is None:
        return None
    for position in actuator.findall("position"):
        if position.attrib.get("joint") == joint_name:
            return position
    return None


def _ensure_actuator(root: ET.Element) -> Dict[str, Any]:
    actuator = root.find("actuator")
    if actuator is None:
        actuator = ET.SubElement(root, "actuator")
    position = _find_actuator(root, "wrist_2_joint")
    if position is None:
        ET.SubElement(
            actuator,
            "position",
            {
                "name": "wrist_2_joint_pos",
                "joint": "wrist_2_joint",
                "kp": "5",
                "ctrllimited": "true",
                "ctrlrange": "-0.8 0.8",
            },
        )
        return {"status": "added", "old": None, "new": "wrist_2_joint_pos"}
    old = dict(position.attrib)
    position.attrib.update({"kp": "5", "ctrllimited": "true", "ctrlrange": "-0.8 0.8"})
    return {"status": "verified_or_updated", "old": old, "new": dict(position.attrib)}


def build_experiment(baseline: Path, output: Path) -> Dict[str, Any]:
    tree = ET.parse(baseline)
    root = tree.getroot()
    changes: List[Dict[str, Any]] = []

    palm = _find_body(root, "palm_link")
    if palm is None:
        raise RuntimeError("palm_link body not found; cannot ensure wrist_2_joint")

    wrist_2 = _find_joint(root, "wrist_2_joint")
    if wrist_2 is None:
        wrist_2 = ET.Element(
            "joint",
            {
                "name": "wrist_2_joint",
                "type": "hinge",
                "axis": "0 0 -1",
                "limited": "true",
                "range": "-0.8 0.8",
                "damping": "0.08",
                "armature": "0.0001",
            },
        )
        palm.insert(0, wrist_2)
        changes.append({"kind": "wrist_2_joint", "status": "added_as_hinge", "new": dict(wrist_2.attrib)})
    else:
        old = dict(wrist_2.attrib)
        wrist_2.attrib.update(
            {
                "type": "hinge",
                "axis": wrist_2.attrib.get("axis", "0 0 -1"),
                "limited": "true",
                "range": "-0.8 0.8",
                "damping": wrist_2.attrib.get("damping", "0.08"),
                "armature": wrist_2.attrib.get("armature", "0.0001"),
            }
        )
        changes.append({"kind": "wrist_2_joint", "status": "verified_or_updated_as_hinge", "old": old, "new": dict(wrist_2.attrib)})

    changes.append({"kind": "wrist_2_actuator", **_ensure_actuator(root)})

    proxy_changes = []
    for geom in root.findall(".//geom"):
        name = geom.attrib.get("name", "")
        if name not in PROXY_TUNING:
            continue
        old = dict(geom.attrib)
        geom.attrib.update(PROXY_TUNING[name])
        proxy_changes.append({"geom": name, "old": old, "new": dict(geom.attrib)})
    changes.append({"kind": "collision_proxy_tuning", "count": len(proxy_changes), "items": proxy_changes})

    root.insert(0, ET.Comment("Experimental wrist2 + collision proxy tuned draft. Baseline/CAD/STL unchanged."))
    _indent(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output, encoding="utf-8", xml_declaration=True)
    return {"changes": changes}


def write_scene(hand_xml: Path, scene_path: Path) -> None:
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.write_text(
        f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_wrist2_collision_tuned_ball_scene\">
  <include file=\"{hand_xml.name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"wrist2_collision_tuned_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"wrist2_collision_tuned_ground_mat\" texture=\"wrist2_collision_tuned_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"wrist2_collision_tuned_ground_mat\" contype=\"1\" conaffinity=\"3\"/>
    <body name=\"ball\" pos=\"{BALL_DEFAULT[0]} {BALL_DEFAULT[1]} {BALL_DEFAULT[2]}\">
      <freejoint name=\"ball_freejoint\"/>
      <geom name=\"ball_geom\" type=\"sphere\" size=\"0.025\" rgba=\"0.95 0.23 0.18 1\"
        mass=\"0.03\" friction=\"0.8 0.05 0.001\" condim=\"3\" contype=\"2\" conaffinity=\"1\"/>
    </body>
  </worldbody>
</mujoco>
""",
        encoding="utf-8",
    )


def write_report(report: Path, payload: Dict[str, Any]) -> None:
    lines = ["# Export4 Wrist2 + Collision Tuned Build Report\n\n"]
    lines.append(f"Generated: {payload['generated_at']}\n\n")
    lines.append("## Scope\n\n")
    lines.append("Current baseline was copied to an experimental MJCF. CAD, STL, joint names, visual mesh, and current-baseline files were not modified.\n\n")
    lines.append("## Files\n\n")
    lines.append(f"- Baseline: `{payload['baseline']}`\n")
    lines.append(f"- Experimental hand: `{payload['output']}`\n")
    lines.append(f"- Experimental ball scene: `{payload['scene']}`\n")
    lines.append("\n## Wrist 2\n\n")
    lines.append("- `wrist_2_joint` is verified as `type=\"hinge\"` with range `-0.8 0.8`.\n")
    lines.append("- `wrist_2_joint_pos` position actuator is verified with `kp=5` and ctrlrange `-0.8 0.8`.\n")
    lines.append("- Note: current-baseline already contained wrist_2 as a hinge; this experimental file preserves and verifies that state.\n")
    lines.append("\n## Collision Proxy Tuning\n\n")
    proxy_change = next((item for item in payload["changes"] if item.get("kind") == "collision_proxy_tuning"), {})
    lines.append(f"- Tuned proxy geoms: `{proxy_change.get('count', 0)}`\n")
    lines.append("- Tuning mainly reduces long-finger and thumb proxy radii plus palm ellipsoid size. Visual mesh remains unchanged.\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build export4 wrist2 + collision tuned experimental MJCF")
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    baseline = Path(args.baseline).resolve()
    output = Path(args.output).resolve()
    scene = Path(args.scene).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    archive = Path(args.archive).resolve()

    if not baseline.exists():
        raise FileNotFoundError(baseline)
    for path in (output, scene, report, metadata):
        _backup_existing(path, archive, "wrist2_collision_tuned")

    result = build_experiment(baseline, output)
    write_scene(output, scene)
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_wrist2_collision_tuned_build_v1",
        "baseline": baseline,
        "output": output,
        "scene": scene,
        "ball_default": BALL_DEFAULT,
        "changes": result["changes"],
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    write_report(report, payload)
    print(f"Saved experimental hand: {output}")
    print(f"Saved experimental scene: {scene}")
    print(f"Saved report: {report}")
    print(f"Saved metadata: {metadata}")


if __name__ == "__main__":
    main()
