from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
ARCHIVE_DIR = ROOT / "archive"

SOURCE_HAND = MJCF_DIR / "hand_stage1_export3_palm_side_fixed.xml"
SOURCE_SCENE = MJCF_DIR / "scene_ball_export3_palm_side_fixed.xml"
REPAIRED_HAND = MJCF_DIR / "hand_stage1_export3_thumb_origin_repaired.xml"
REPAIRED_SCENE = MJCF_DIR / "scene_ball_export3_thumb_origin_repaired.xml"
REPORT_MD = DOCS_DIR / "export3_thumb_origin_repair_report.md"

# MJCF-only temporary repair values. These are not CAD truth.
# `thumb_cmc_flex_joint` was exported with a 150 mm offset; scale the same
# direction down to a small trapezium-to-metacarpal offset.
THUMB_METACARPAL_POS_REPAIRED = "0.002731 0.010273 0.014527"

# `thumb_mcp_joint` was exported with a 133 mm offset. Use the previously
# validated approximate thumb metacarpal-to-proximal span, about 52 mm.
THUMB_PROXIMAL_POS_REPAIRED = "-0.016224 0.049404 -0.000175"

# The metacarpal body is contiguous after the origin repair, but the mesh asset
# still compiles with a large visual offset. Shift only the visual geom so the
# mesh center sits near the repaired collision-proxy midpoint.
THUMB_METACARPAL_VISUAL_POS_REPAIRED = "0.119732 -0.014053 -0.039847"


def backup_if_exists(path: Path, tag: str) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_dir = ARCHIVE_DIR / f"{tag}_{stamp}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / path.name
    shutil.copy2(path, dst)
    return dst


def require(root: ET.Element, query: str) -> ET.Element:
    item = root.find(query)
    if item is None:
        raise RuntimeError(f"Missing XML element: {query}")
    return item


def build_hand() -> list[dict[str, str]]:
    tree = ET.parse(SOURCE_HAND)
    root = tree.getroot()
    changes: list[dict[str, str]] = []

    metacarpal_body = require(root, ".//body[@name='thumb_metacarpal_link']")
    old = metacarpal_body.get("pos") or ""
    metacarpal_body.set("pos", THUMB_METACARPAL_POS_REPAIRED)
    changes.append({"element": "body thumb_metacarpal_link pos", "old": old, "new": THUMB_METACARPAL_POS_REPAIRED})

    trapezium_proxy = require(root, ".//geom[@name='thumb_trapezium1_link_collision_proxy']")
    old = trapezium_proxy.get("fromto") or ""
    trapezium_proxy.set("fromto", f"0 0 0 {THUMB_METACARPAL_POS_REPAIRED}")
    changes.append(
        {
            "element": "geom thumb_trapezium1_link_collision_proxy fromto",
            "old": old,
            "new": f"0 0 0 {THUMB_METACARPAL_POS_REPAIRED}",
        }
    )

    proximal_body = require(root, ".//body[@name='thumb_proximal_link']")
    old = proximal_body.get("pos") or ""
    proximal_body.set("pos", THUMB_PROXIMAL_POS_REPAIRED)
    changes.append({"element": "body thumb_proximal_link pos", "old": old, "new": THUMB_PROXIMAL_POS_REPAIRED})

    metacarpal_proxy = require(root, ".//geom[@name='thumb_metacarpal_link_collision_proxy']")
    old = metacarpal_proxy.get("fromto") or ""
    metacarpal_proxy.set("fromto", f"0 0 0 {THUMB_PROXIMAL_POS_REPAIRED}")
    changes.append(
        {
            "element": "geom thumb_metacarpal_link_collision_proxy fromto",
            "old": old,
            "new": f"0 0 0 {THUMB_PROXIMAL_POS_REPAIRED}",
        }
    )

    metacarpal_visual = require(root, ".//geom[@name='thumb_metacarpal_link_export3_visual']")
    old = metacarpal_visual.get("pos") or ""
    metacarpal_visual.set("pos", THUMB_METACARPAL_VISUAL_POS_REPAIRED)
    changes.append(
        {
            "element": "geom thumb_metacarpal_link_export3_visual pos",
            "old": old,
            "new": THUMB_METACARPAL_VISUAL_POS_REPAIRED,
        }
    )

    backup_if_exists(REPAIRED_HAND, "before_export3_thumb_origin_repaired_hand")
    tree.write(REPAIRED_HAND, encoding="utf-8", xml_declaration=True)
    return changes


def build_scene() -> None:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    include = require(root, "include")
    include.set("file", REPAIRED_HAND.name)
    backup_if_exists(REPAIRED_SCENE, "before_export3_thumb_origin_repaired_scene")
    tree.write(REPAIRED_SCENE, encoding="utf-8", xml_declaration=True)


def write_report(changes: list[dict[str, str]]) -> None:
    lines = [
        "# Export3 Thumb Origin Repair Report",
        "",
        "## Summary",
        "",
        "- This is a temporary MJCF-only repair for visual/kinematic debugging.",
        "- CAD, STL files, URDF, link names, joint names, and joint tree were not changed.",
        f"- Source hand: `{SOURCE_HAND}`",
        f"- Repaired hand: `{REPAIRED_HAND}`",
        f"- Repaired scene: `{REPAIRED_SCENE}`",
        "",
        "## Why",
        "",
        "- `thumb_cmc_flex_joint` was exported with an adjacent-body offset of about `0.1506 m`.",
        "- `thumb_mcp_joint` was exported with an adjacent-body offset of about `0.1330 m`.",
        "- Those values make the thumb appear separated/suspended in the viewer.",
        "- After the body-origin repair, `thumb_metacarpal_link` still had a large visual mesh offset, so only its visual geom was shifted back to the repaired collision-proxy region.",
        "",
        "## Changes",
        "",
        "| Element | Old | New |",
        "|---|---|---|",
    ]
    for item in changes:
        lines.append(f"| `{item['element']}` | `{item['old']}` | `{item['new']}` |")
    lines.extend(
        [
            "",
            "## Status",
            "",
            "- Use this only to continue simulation smoke testing.",
            "- For final mechanical truth, fix the SolidWorks CSYS/origin for `thumb_cmc_flex_joint` and `thumb_mcp_joint` and re-export.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    changes = build_hand()
    build_scene()
    write_report(changes)
    print(f"Wrote {REPAIRED_HAND}")
    print(f"Wrote {REPAIRED_SCENE}")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
