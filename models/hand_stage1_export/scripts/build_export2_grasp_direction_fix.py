from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"

SOURCE_XML = MJCF_DIR / "hand_stage1_clean_mesh_export2_draft.xml"
FIXED_XML = MJCF_DIR / "hand_stage1_clean_mesh_export2_graspfix.xml"
FIXED_SCENE_XML = MJCF_DIR / "scene_ball_clean_mesh_export2_graspfix.xml"
REPORT_MD = DOCS_DIR / "export2_grasp_direction_fix_report.md"
REPORT_JSON = METADATA_DIR / "export2_grasp_direction_fix.json"

LONG_FINGERS = ["index", "middle", "ring", "little"]

# Current CAD/URDF naming likely swaps MCP flex/abd semantics. In this stage1
# model, the scripted grasp uses *_mcp_abd_joint as the main MCP curling DOF.
FLEXION_LIKE_JOINTS = [
    *[f"{finger}_mcp_abd_joint" for finger in LONG_FINGERS],
    *[f"{finger}_pip_joint" for finger in LONG_FINGERS],
    *[f"{finger}_dip_joint" for finger in LONG_FINGERS],
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]


def parse_vec(text: str) -> list[float]:
    return [float(part) for part in text.split()]


def format_vec(values: list[float]) -> str:
    return " ".join(f"{value:.9g}" for value in values)


def pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def write_scene() -> None:
    FIXED_SCENE_XML.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="utf-8"?>',
                '<mujoco model="hand_stage1_ball_scene_clean_mesh_export2_graspfix">',
                '  <include file="hand_stage1_clean_mesh_export2_graspfix.xml"/>',
                "  <visual>",
                '    <global azimuth="145" elevation="-25" offwidth="1400" offheight="1000"/>',
                "  </visual>",
                "  <asset>",
                '    <texture type="2d" name="graspfix_ground_checker" builtin="checker" rgb1="0.18 0.20 0.22" rgb2="0.28 0.30 0.32" width="300" height="300"/>',
                '    <material name="graspfix_ground_mat" texture="graspfix_ground_checker" texrepeat="4 4" reflectance="0.15"/>',
                "  </asset>",
                "  <worldbody>",
                '    <light name="key_light" pos="0 -0.35 0.85" dir="0 0 -1" directional="true"/>',
                '    <light name="fill_light" pos="-0.35 0.25 0.55"/>',
                '    <geom name="ground" type="plane" pos="0 0 0" size="0.5 0.5 0.02" material="graspfix_ground_mat" contype="1" conaffinity="1"/>',
                '    <body name="ball" pos="0.01 -0.045 0.215">',
                '      <freejoint name="ball_freejoint"/>',
                '      <geom name="ball_geom" type="sphere" size="0.025" rgba="0.95 0.23 0.18 1" mass="0.03" friction="0.8 0.05 0.001" condim="3"/>',
                "    </body>",
                '    <camera name="front" pos="0.20 -0.34 0.30" xyaxes="0.834219 0.551433 0 -0.16379 0.247785 0.954869" fovy="45"/>',
                '    <camera name="side" pos="0.34 0.02 0.25" xyaxes="-0.190477 0.981692 0 -0.169999 -0.0329848 0.984892" fovy="45"/>',
                '    <camera name="top" pos="0.02 -0.06 0.55" xyaxes="0.707107 0.707107 0 -0.705346 0.705346 0.0705346" fovy="45"/>',
                '    <camera name="palm" pos="0.11 -0.20 0.24" xyaxes="0.875 0.484 0 -0.204 0.368 0.907" fovy="34"/>',
                '    <camera name="finger_root_closeup" pos="0.11 -0.20 0.25" xyaxes="0.875 0.484 0 -0.204 0.368 0.907" fovy="24"/>',
                '    <camera name="thumb_root_closeup" pos="-0.15 -0.11 0.19" xyaxes="0.594 -0.804 0 0.372 0.275 0.887" fovy="26"/>',
                '    <camera name="index_finger_closeup" pos="-0.14 -0.17 0.36" xyaxes="0.844 -0.537 0 0.211 0.331 0.920" fovy="24"/>',
                '    <camera name="full_hand_with_ball" pos="0.23 -0.38 0.34" xyaxes="0.850 0.527 0 -0.165 0.267 0.949" fovy="48"/>',
                "  </worldbody>",
                "</mujoco>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    tree = ET.parse(SOURCE_XML)
    root = tree.getroot()
    root.set("model", "hand_stage1_clean_mesh_export2_graspfix")
    root.insert(
        0,
        ET.Comment(
            "Diagnostic grasp direction fix: flexion-like hinge axes are inverted. "
            "Joint names and body tree are unchanged; mcp_flex/mcp_abd semantics remain TODO."
        ),
    )

    flipped = []
    missing = []
    for name in FLEXION_LIKE_JOINTS:
        joint = root.find(f".//joint[@name='{name}']")
        if joint is None:
            missing.append(name)
            continue
        old_axis = parse_vec(joint.get("axis", "0 0 1"))
        new_axis = [-value for value in old_axis]
        joint.set("axis", format_vec(new_axis))
        joint.set("user", "1")
        flipped.append({"joint": name, "old_axis": old_axis, "new_axis": new_axis, "range": joint.get("range")})

    FIXED_XML.write_text(pretty_xml(root), encoding="utf-8")
    write_scene()

    report = {
        "source_xml": str(SOURCE_XML),
        "fixed_xml": str(FIXED_XML),
        "fixed_scene_xml": str(FIXED_SCENE_XML),
        "joint_tree_changed": False,
        "joint_names_changed": False,
        "flipped_joint_count": len(flipped),
        "flipped_joints": flipped,
        "missing_requested_joints": missing,
        "notes": [
            "This is a diagnostic MJCF-only fix for the observed reversed grasp direction.",
            "The fix inverts flexion-like hinge axes while preserving positive scripted grasp targets.",
            "The four long-finger *_mcp_abd_joint entries are treated as MCP curl joints for this draft because flex/abd naming semantics remain suspect.",
            "Primitive collision geoms are retained; clean mesh geoms remain visual-only.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_markdown(report: dict) -> None:
    lines = [
        "# Export2 Grasp Direction Fix Report",
        "",
        f"- Source XML: `{report['source_xml']}`",
        f"- Fixed XML: `{report['fixed_xml']}`",
        f"- Fixed scene: `{report['fixed_scene_xml']}`",
        f"- Joint tree changed: {report['joint_tree_changed']}",
        f"- Joint names changed: {report['joint_names_changed']}",
        f"- Flipped joint count: {report['flipped_joint_count']}",
        "",
        "## Flipped Flexion-Like Hinge Axes",
        "",
        "| Joint | Old axis | New axis | Range |",
        "|---|---|---|---|",
    ]
    for item in report["flipped_joints"]:
        lines.append(
            f"| `{item['joint']}` | `{format_vec(item['old_axis'])}` | `{format_vec(item['new_axis'])}` | `{item['range']}` |"
        )
    if report["missing_requested_joints"]:
        lines.extend(["", "## Missing Requested Joints", ""])
        lines.extend(f"- `{name}`" for name in report["missing_requested_joints"])
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
