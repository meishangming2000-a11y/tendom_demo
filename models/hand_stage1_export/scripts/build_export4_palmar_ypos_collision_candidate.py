#!/usr/bin/env python3
"""Build an export4 +Y palmar-side fingertip-collision candidate.

This is an experimental branch only. It does not modify CAD, STL, URDF, joint
names, or the frozen/current-baseline MJCF files.
"""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from export4_wrist2_common import ARCHIVE_DIR, MJCF_DIR, write_json, write_text


SOURCE_HAND = MJCF_DIR / "hand_stage1_export4_wrist2_collision_tuned.xml"
OUT_HAND = MJCF_DIR / "hand_stage1_export4_palmar_ypos_collision_candidate.xml"
OUT_SCENE = MJCF_DIR / "scene_ball_export4_palmar_ypos_collision_candidate.xml"
REPORT = Path(__file__).resolve().parents[1] / "docs" / "export4_palmar_ypos_collision_candidate_report.md"
META = Path(__file__).resolve().parents[1] / "metadata" / "export4_palmar_ypos_collision_candidate.json"

TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}


def backup(path: Path, tag: str) -> str | None:
    if not path.exists():
        return None
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = ARCHIVE_DIR / f"{path.stem}.{tag}.{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return str(target)


def add_tip_spheres(root: ET.Element, radius: float) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []

    def visit(body: ET.Element) -> None:
        body_name = body.get("name", "")
        site_children = list(body.findall("site"))
        existing_geom_names = {geom.get("name") for geom in body.findall("geom")}
        for site in site_children:
            site_name = site.get("name")
            if site_name not in TIP_SITES.values():
                continue
            finger = next(name for name, candidate in TIP_SITES.items() if candidate == site_name)
            geom_name = f"{finger}_tip_collision_proxy_sphere"
            if geom_name in existing_geom_names:
                geom = body.find(f"geom[@name='{geom_name}']")
            else:
                geom = ET.Element("geom")
                body.insert(list(body).index(site), geom)
            geom.set("name", geom_name)
            geom.set("type", "sphere")
            geom.set("pos", site.get("pos", "0 0 0"))
            geom.set("size", f"{radius:.6f}")
            geom.set("rgba", "1.0 0.78 0.10 0.42")
            geom.set("contype", "1")
            geom.set("conaffinity", "2")
            geom.set("group", "3")
            geom.set("friction", "0.9 0.04 0.001")
            changes.append(
                {
                    "finger": finger,
                    "site": site_name,
                    "body": body_name,
                    "geom": geom_name,
                    "pos": site.get("pos", "0 0 0"),
                    "radius": radius,
                }
            )
        for child in body.findall("body"):
            visit(child)

    world = root.find("worldbody")
    if world is not None:
        for body in world.findall("body"):
            visit(body)
    return changes


def indent_xml(path: Path) -> None:
    try:
        tree = ET.parse(path)
        ET.indent(tree, space="  ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
    except Exception:
        pass


def write_scene(path: Path, hand_file: str, ball: tuple[float, float, float]) -> None:
    text = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_palmar_ypos_collision_candidate_scene\">
  <include file=\"{hand_file}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"palmar_ypos_candidate_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"palmar_ypos_candidate_ground_mat\" texture=\"palmar_ypos_candidate_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"palmar_ypos_candidate_ground_mat\" contype=\"1\" conaffinity=\"3\"/>
    <body name=\"ball\" pos=\"{ball[0]} {ball[1]} {ball[2]}\">
      <freejoint name=\"ball_freejoint\"/>
      <geom name=\"ball_geom\" type=\"sphere\" size=\"0.025\" rgba=\"0.95 0.23 0.18 1\"
        mass=\"0.03\" friction=\"0.8 0.05 0.001\" condim=\"3\" contype=\"2\" conaffinity=\"1\"/>
    </body>
  </worldbody>
</mujoco>
"""
    backup(path, "before_palmar_ypos_candidate_scene")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build +Y palmar-side export4 collision candidate.")
    parser.add_argument("--source-hand", default=str(SOURCE_HAND))
    parser.add_argument("--output-hand", default=str(OUT_HAND))
    parser.add_argument("--output-scene", default=str(OUT_SCENE))
    parser.add_argument("--tip-radius", type=float, default=0.015)
    parser.add_argument("--ball-x", type=float, default=0.0)
    parser.add_argument("--ball-y", type=float, default=0.08)
    parser.add_argument("--ball-z", type=float, default=0.21)
    args = parser.parse_args()

    src = Path(args.source_hand).resolve()
    out_hand = Path(args.output_hand).resolve()
    out_scene = Path(args.output_scene).resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    backup(out_hand, "before_palmar_ypos_candidate")
    tree = ET.parse(src)
    root = tree.getroot()
    root.set("model", "hand_stage1_export4_palmar_ypos_collision_candidate")
    changes = add_tip_spheres(root, float(args.tip_radius))
    ET.indent(tree, space="  ")
    tree.write(out_hand, encoding="utf-8", xml_declaration=True)
    write_scene(out_scene, out_hand.name, (args.ball_x, args.ball_y, args.ball_z))
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_hand": str(src),
        "output_hand": str(out_hand),
        "output_scene": str(out_scene),
        "tip_radius": float(args.tip_radius),
        "ball_position": [args.ball_x, args.ball_y, args.ball_z],
        "changes": changes,
        "scope": "experimental candidate only; no CAD/STL/URDF/current-baseline changes",
    }
    write_json(META, payload, "before_palmar_ypos_candidate_meta")
    lines = [
        "# Export4 +Y Palmar Collision Candidate Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Experimental MJCF-only branch. CAD, STL, URDF joint tree, joint names, and frozen/current-baseline files were not modified.\n\n",
        "## Changes\n\n",
        f"- Source hand: `{payload['source_hand']}`\n",
        f"- Output hand: `{payload['output_hand']}`\n",
        f"- Output scene: `{payload['output_scene']}`\n",
        f"- Default candidate ball: `{payload['ball_position']}`\n",
        f"- Added fingertip collision sphere radius: `{payload['tip_radius']}` m\n\n",
        "| finger | body | site | geom | pos | radius |\n",
        "|---|---|---|---|---|---:|\n",
    ]
    for row in changes:
        lines.append(f"| {row['finger']} | `{row['body']}` | `{row['site']}` | `{row['geom']}` | `{row['pos']}` | {row['radius']:.4f} |\n")
    lines.extend(
        [
            "\n## Rationale\n\n",
            "- Prior diagnostics show the default `-Y` ball side is far from the closing fingertips.\n",
            "- The mirror/+Y side is visually closer but still lacked contact with conservative capsule-only proxy.\n",
            "- This branch adds only local fingertip spheres instead of inflating palm or whole-finger collision geoms.\n",
            "- TODO: promote only if regression shows improved contact without open-pose penetration.\n",
        ]
    )
    write_text(REPORT, "".join(lines), "before_palmar_ypos_candidate_report")
    print(f"Saved candidate hand: {out_hand}")
    print(f"Saved candidate scene: {out_scene}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")


if __name__ == "__main__":
    main()
