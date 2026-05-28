from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
ARCHIVE_DIR = ROOT / "archive"

SOURCE_HAND = MJCF_DIR / "hand_stage1_export3.xml"
SOURCE_SCENE = MJCF_DIR / "scene_ball_export3.xml"
FIXED_HAND = MJCF_DIR / "hand_stage1_export3_palm_side_fixed.xml"
FIXED_SCENE = MJCF_DIR / "scene_ball_export3_palm_side_fixed.xml"
REPORT_MD = DOCS_DIR / "export3_palm_side_fix_report.md"

# The first visual mirror test used Y=+0.10, but that left the ball too far
# from the long-finger closure envelope. This point keeps the ball on the
# corrected visual palm side while sitting inside the four-finger wrap region.
BALL_PALM_SIDE = [0.0, 0.045, 0.22]

# These joints are the long-finger closure hinges in the current export3
# scripted policy. MCP flex is kept as spread/lateral control for now.
FINGER_CLOSURE_JOINTS = [
    "index_mcp_abd_joint",
    "index_pip_joint",
    "index_dip_joint",
    "middle_mcp_abd_joint",
    "middle_pip_joint",
    "middle_dip_joint",
    "ring_mcp_abd_joint",
    "ring_pip_joint",
    "ring_dip_joint",
    "little_mcp_abd_joint",
    "little_pip_joint",
    "little_dip_joint",
]


def backup_if_exists(path: Path, tag: str) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_dir = ARCHIVE_DIR / f"{tag}_{stamp}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / path.name
    shutil.copy2(path, dst)
    return dst


def negate_axis(axis_text: str) -> str:
    values = [float(value) for value in axis_text.split()]
    return " ".join(f"{-value:.12g}" for value in values)


def build_hand() -> list[dict[str, str]]:
    tree = ET.parse(SOURCE_HAND)
    root = tree.getroot()
    changed: list[dict[str, str]] = []
    for joint in root.findall(".//joint"):
        name = joint.get("name")
        if name not in FINGER_CLOSURE_JOINTS:
            continue
        old_axis = joint.get("axis")
        if not old_axis:
            continue
        new_axis = negate_axis(old_axis)
        joint.set("axis", new_axis)
        changed.append({"joint": name, "old_axis": old_axis, "new_axis": new_axis})
    if len(changed) != len(FINGER_CLOSURE_JOINTS):
        missing = sorted(set(FINGER_CLOSURE_JOINTS) - {item["joint"] for item in changed})
        raise RuntimeError(f"Missing expected closure joints: {missing}")
    backup_if_exists(FIXED_HAND, "before_export3_palm_side_fixed_hand")
    tree.write(FIXED_HAND, encoding="utf-8", xml_declaration=True)
    return changed


def mirror_camera_y(camera: ET.Element) -> None:
    pos = camera.get("pos")
    if pos:
        values = [float(value) for value in pos.split()]
        if len(values) == 3:
            values[1] = -values[1]
            camera.set("pos", " ".join(f"{value:.9g}" for value in values))
    xyaxes = camera.get("xyaxes")
    if xyaxes:
        values = [float(value) for value in xyaxes.split()]
        if len(values) == 6:
            values[1] = -values[1]
            values[4] = -values[4]
            camera.set("xyaxes", " ".join(f"{value:.9g}" for value in values))


def build_scene() -> None:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    include = root.find("include")
    if include is None:
        raise RuntimeError("Source scene has no include element")
    include.set("file", FIXED_HAND.name)

    ball = root.find(".//body[@name='ball']")
    if ball is None:
        raise RuntimeError("Source scene has no ball body")
    ball.set("pos", " ".join(f"{value:.9g}" for value in BALL_PALM_SIDE))

    # Put the default rendered cameras on the same side as the corrected ball.
    for camera in root.findall(".//camera"):
        name = camera.get("name") or ""
        if name in {"full_hand_with_ball", "front", "palm", "thumb_root_closeup", "index_finger_closeup"}:
            mirror_camera_y(camera)

    backup_if_exists(FIXED_SCENE, "before_export3_palm_side_fixed_scene")
    tree.write(FIXED_SCENE, encoding="utf-8", xml_declaration=True)


def write_report(changed: list[dict[str, str]]) -> None:
    lines = [
        "# Export3 Palm-Side Fix Report",
        "",
        "## Summary",
        "",
        "- User visual check indicates the previous ball side was the anatomical dorsal/back side.",
        "- This fix keeps CAD, STL files, link tree, joint names, and original export3 files unchanged.",
        f"- New hand MJCF: `{FIXED_HAND}`",
        f"- New scene MJCF: `{FIXED_SCENE}`",
        f"- Corrected ball position: `{BALL_PALM_SIDE}`",
        "",
        "## Sim-Side Changes",
        "",
        "- Ball moved from the old dorsal-side `Y=-0.1` scene to the corrected visual palm-side position `Y=+0.045`.",
        "- The long-finger closure axes below were negated in the corrected MJCF so the existing positive flexion targets close toward the corrected palm side.",
        "- `*_mcp_flex_joint` is left unchanged because it is being used as lateral/spread control in the current scripted policy.",
        "",
        "| Joint | Old axis | New axis |",
        "|---|---|---|",
    ]
    for item in changed:
        lines.append(f"| `{item['joint']}` | `{item['old_axis']}` | `{item['new_axis']}` |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is an experimental simulation-side orientation fix, not a CAD or URDF source edit.",
            "- If this visually matches the anatomical palm side, export4 should add explicit palm/dorsal reference CSYS markers so future scripts do not infer the wrong side.",
            "- Thumb target tuning remains paused; this fix only addresses ball side and long-finger close direction.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    changed = build_hand()
    build_scene()
    write_report(changed)
    print(f"Wrote {FIXED_HAND}")
    print(f"Wrote {FIXED_SCENE}")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
