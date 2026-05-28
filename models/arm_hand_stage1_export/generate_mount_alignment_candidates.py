#!/usr/bin/env python3
"""Generate and render fixed-transform arm-hand mount alignment candidates.

The source arm and hand models are not modified. This script takes the already
merged arm+hand XML, changes only the local fixed transform of `hand_base_link`
under `ee_tool_frame`, and renders comparable close-up views.
"""

from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
BASE_XML = ROOT / "arm_hand_export4_palmar_ypos_candidate.xml"
OUT_DIR = ROOT / "mount_alignment_candidates"
VIS_DIR = ROOT / "visual_checks_mount_alignment"
DOCS = ROOT / "docs"
META = ROOT / "metadata" / "arm_hand_mount_alignment_candidates.json"
REPORT = DOCS / "arm_hand_mount_alignment_candidates.md"
ARCHIVE = ROOT / "archive"


@dataclass(frozen=True)
class Candidate:
    label: str
    pos: tuple[float, float, float]
    quat: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    note: str = ""


CANDIDATES = [
    Candidate("identity", (0.0, 0.0, 0.0), note="Current first assembly transform."),
    Candidate("tool_z_plus_12mm", (0.0, 0.0, 0.012), note="Move hand outward along ee_tool_frame local +Z."),
    Candidate("tool_z_plus_25mm", (0.0, 0.0, 0.025), note="Move hand outward along ee_tool_frame local +Z by about hand-base half-depth."),
    Candidate("tool_z_minus_12mm", (0.0, 0.0, -0.012), note="Move hand inward along ee_tool_frame local -Z."),
    Candidate("tool_z_minus_25mm", (0.0, 0.0, -0.025), note="Move hand inward along ee_tool_frame local -Z by about hand-base half-depth."),
    Candidate("tool_x_plus_15mm", (0.015, 0.0, 0.0), note="Lateral local +X centering diagnostic."),
    Candidate("tool_x_minus_15mm", (-0.015, 0.0, 0.0), note="Lateral local -X centering diagnostic."),
    Candidate("tool_y_plus_15mm", (0.0, 0.015, 0.0), note="Local +Y diagnostic."),
    Candidate("tool_y_minus_15mm", (0.0, -0.015, 0.0), note="Local -Y diagnostic."),
]


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


def ensure_site(body: ET.Element, name: str, rgba: str, pos: str = "0 0 0", size: str = "0.006") -> None:
    for site in body.findall("site"):
        if site.get("name") == name:
            return
    ET.SubElement(body, "site", {"name": name, "type": "sphere", "pos": pos, "size": size, "rgba": rgba})


def vec_text(values: tuple[float, ...]) -> str:
    return " ".join(f"{v:.6g}" for v in values)


def write_candidate_xml(candidate: Candidate) -> tuple[Path, Path]:
    tree = ET.parse(BASE_XML)
    root = tree.getroot()
    root.set("model", f"arm_hand_export4_mount_{candidate.label}")

    # Candidate XML files live one directory below the base combined XML, so
    # mesh paths inherited from the base file need one extra `..`.
    for mesh in root.findall(".//mesh"):
        file_name = mesh.get("file")
        if file_name and file_name.startswith("../"):
            mesh.set("file", f"../{file_name}")

    ee_tool = find_body(root, "ee_tool_frame")
    hand_base = find_body(root, "hand_base_link")
    if ee_tool is None or hand_base is None:
        raise RuntimeError("Could not find ee_tool_frame or hand_base_link in base combined XML")

    hand_base.set("pos", vec_text(candidate.pos))
    hand_base.set("quat", vec_text(candidate.quat))
    ensure_site(ee_tool, "mount_debug_ee_tool_frame_origin", "1 0.45 0.05 1", "0 0 0", "0.005")
    ensure_site(hand_base, "mount_debug_hand_base_origin", "0.05 0.65 1 1", "0 0 0", "0.005")
    ensure_site(hand_base, "mount_debug_hand_base_plus_z", "0.05 1 0.15 1", "0 0 0.025", "0.004")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    xml_path = OUT_DIR / f"arm_hand_export4_mount_{candidate.label}.xml"
    backup(xml_path, "before_mount_candidate")
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    scene_path = OUT_DIR / f"scene_arm_hand_export4_mount_{candidate.label}.xml"
    scene = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"arm_hand_export4_mount_{candidate.label}_scene\">
  <include file=\"{xml_path.name}\"/>
  <statistic extent=\"0.9\" center=\"0 0 0.12\"/>
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
    backup(scene_path, "before_mount_candidate_scene")
    scene_path.write_text(scene, encoding="utf-8")
    return xml_path, scene_path


def id_or_minus_one(model, mujoco, objtype, name: str) -> int:
    return mujoco.mj_name2id(model, objtype, name)


def render_candidate(scene_path: Path, label: str) -> dict[str, Any]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    ee_id = id_or_minus_one(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, "ee_tool_frame")
    hand_id = id_or_minus_one(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, "hand_base_link")
    palm_id = id_or_minus_one(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    ee_pos = data.xpos[ee_id].copy()
    hand_pos = data.xpos[hand_id].copy()
    palm_pos = data.xpos[palm_id].copy()
    lookat = (ee_pos + palm_pos) / 2.0

    VIS_DIR.mkdir(parents=True, exist_ok=True)
    views = {}
    specs = {
        "flange_closeup": (ee_pos, 0.16, 205, -4),
        "wrist_closeup": (lookat, 0.18, 110, -12),
        "top": (lookat, 0.38, 180, -78),
    }
    for view_name, (view_lookat, distance, azimuth, elevation) in specs.items():
        renderer = mujoco.Renderer(model, width=960, height=720)
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
        out = VIS_DIR / f"{label}_{view_name}.png"
        imageio.imwrite(out, image)
        views[view_name] = {
            "file": str(out),
            "mean_pixel": float(image.mean()),
            "min_pixel": int(image.min()),
            "max_pixel": int(image.max()),
        }
    return {
        "label": label,
        "scene": str(scene_path),
        "ee_tool_frame_world": ee_pos.tolist(),
        "hand_base_world": hand_pos.tolist(),
        "palm_world": palm_pos.tolist(),
        "ee_to_hand_base_distance": float(np.linalg.norm(hand_pos - ee_pos)),
        "views": views,
    }


def make_contact_sheet(results: list[dict[str, Any]], view_name: str) -> Path:
    images = []
    for result in results:
        image = imageio.imread(result["views"][view_name]["file"])
        images.append(image)
    cols = 3
    rows = int(np.ceil(len(images) / cols))
    h, w = images[0].shape[:2]
    sheet = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    for i, image in enumerate(images):
        r, c = divmod(i, cols)
        sheet[r * h : (r + 1) * h, c * w : (c + 1) * w] = image[:, :, :3]
    out = VIS_DIR / f"contact_sheet_{view_name}.png"
    imageio.imwrite(out, sheet)
    return out


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    backup(META, "before_mount_alignment_candidates")
    META.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Mount Alignment Candidates\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Purpose\n\n",
        "Diagnose whether the arm `ee_tool_frame` and hand `hand_base_link` origins represent physical mounting faces. ",
        "Only the fixed child transform of `hand_base_link` under `ee_tool_frame` is changed in these candidates. CAD, STL, joint names, and joint trees are unchanged.\n\n",
        "## Key Diagnosis\n\n",
        "- The current identity attachment is kinematically valid, but it does not prove flange-face calibration.\n",
        "- `hand_base_link` is a body origin near the wrist/root geometry, not necessarily the proximal mounting face.\n",
        "- If the flange disk remains too exposed, the likely fix is a fixed transform offset, not a new joint or training change.\n\n",
        "## Candidate Table\n\n",
        "| label | hand pos in ee_tool_frame | ee-to-hand-base distance | note |\n",
        "|---|---:|---:|---|\n",
    ]
    for item in payload["candidates"]:
        lines.append(
            f"| `{item['label']}` | `{item['pos']}` | {item['render']['ee_to_hand_base_distance']:.4f} m | {item['note']} |\n"
        )
    lines.extend(
        [
            "\n## Contact Sheets\n\n",
            f"- flange closeup: `{payload['contact_sheets']['flange_closeup']}`\n",
            f"- wrist closeup: `{payload['contact_sheets']['wrist_closeup']}`\n",
            f"- top: `{payload['contact_sheets']['top']}`\n\n",
            "## Current Recommendation\n\n",
            "Use the contact sheets for visual selection. Prefer a candidate where the hand wrist/root covers or seats against the visible flange face without burying the palm into the arm body. ",
            "If none looks right, the next check is whether the arm export has a missing flange-face frame distinct from `ee_tool_frame`.\n",
        ]
    )
    DOCS.mkdir(parents=True, exist_ok=True)
    backup(REPORT, "before_mount_alignment_candidates")
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    if not BASE_XML.exists():
        raise SystemExit(f"Base combined XML does not exist: {BASE_XML}")

    results = []
    candidate_payloads = []
    for candidate in CANDIDATES:
        xml_path, scene_path = write_candidate_xml(candidate)
        render = render_candidate(scene_path, candidate.label)
        results.append(render)
        candidate_payloads.append(
            {
                "label": candidate.label,
                "pos": list(candidate.pos),
                "quat": list(candidate.quat),
                "note": candidate.note,
                "xml": str(xml_path),
                "scene": str(scene_path),
                "render": render,
            }
        )
    contact_sheets = {
        "flange_closeup": str(make_contact_sheet(results, "flange_closeup")),
        "wrist_closeup": str(make_contact_sheet(results, "wrist_closeup")),
        "top": str(make_contact_sheet(results, "top")),
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_xml": str(BASE_XML),
        "candidates": candidate_payloads,
        "contact_sheets": contact_sheets,
        "status": "PENDING_VISUAL_SELECTION",
    }
    write_outputs(payload)
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    for name, path in contact_sheets.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
