#!/usr/bin/env python3
"""Generate small MuJoCo refinement candidates after the accepted v6 direction.

V6 fixed the body side and whole-arm yaw. This script deliberately keeps that
orientation frozen and sweeps only shallow assembly details: arm-root depth at
the body interface and floor/support-column visual clipping.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw

import build_body_orientation_corrected_v5 as v5


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v6.xml"
CANDIDATE_SCENE_DIR = ROOT / "mjcf"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_v7_candidates"
IMAGE_DIR = VIS / "candidates"
REPORT = DOCS / "body_connection_v7_candidate_sweep_report.md"
META = ROOT / "metadata" / "body_connection_v7_candidate_sweep.json"
CONTACT_SHEET = VIS / "body_connection_v7_candidate_contact_sheet.png"

ARM_ROOT_NAME = "base_link"
BODY_ROOT_NAME = "rough_body_support_link"
SUPPORT_NAME_V6 = "body_support_column_visual_v6"
SUPPORT_NAME_V7 = "body_support_column_visual_v7"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    arm_root_y_offset_m: float
    floor_z_m: float
    note: str


CANDIDATES = [
    Candidate(
        candidate_id="origin_floor_clear",
        arm_root_y_offset_m=0.0,
        floor_z_m=-0.165,
        note="Keep accepted v6 mount origin; lower only the visual floor to avoid support-column clipping.",
    ),
    Candidate(
        candidate_id="outward_15mm",
        arm_root_y_offset_m=-0.015,
        floor_z_m=-0.165,
        note="Move the arm 15 mm outward along the accepted horizontal direction.",
    ),
    Candidate(
        candidate_id="outward_30mm",
        arm_root_y_offset_m=-0.030,
        floor_z_m=-0.165,
        note="Move the arm 30 mm outward along the accepted horizontal direction.",
    ),
    Candidate(
        candidate_id="inward_15mm",
        arm_root_y_offset_m=0.015,
        floor_z_m=-0.165,
        note="Move the arm 15 mm inward as a negative control for interface penetration.",
    ),
]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_vec(text: str, fallback: tuple[float, ...]) -> np.ndarray:
    values = np.fromstring(text or "", sep=" ")
    return values if values.size else np.asarray(fallback, dtype=np.float64)


def find_required(root: ET.Element, path: str, *, label: str) -> ET.Element:
    item = root.find(path)
    if item is None:
        raise RuntimeError(f"Missing {label}: {path}")
    return item


def set_floor_z(root: ET.Element, floor_z_m: float) -> None:
    floor = find_required(root, ".//geom[@name='floor']", label="floor")
    pos = parse_vec(floor.get("pos", "0 0 0"), (0.0, 0.0, 0.0))
    pos[2] = floor_z_m
    floor.set("pos", v5.fmt_vec(pos))


def replace_support_column(root: ET.Element) -> dict[str, Any]:
    world = find_required(root, "worldbody", label="worldbody")
    for geom in list(world.findall("geom")):
        if geom.get("name") in {SUPPORT_NAME_V6, SUPPORT_NAME_V7}:
            world.remove(geom)
    support = ET.Element(
        "geom",
        {
            "name": SUPPORT_NAME_V7,
            "type": "cylinder",
            "pos": "0.0 0.100 0.015",
            "size": "0.045 0.145",
            "rgba": "0.42 0.44 0.46 0.55",
            "contype": "0",
            "conaffinity": "0",
            "group": "2",
        },
    )
    world.append(support)
    return {
        "geom": SUPPORT_NAME_V7,
        "pos": [0.0, 0.100, 0.015],
        "size_radius_halfheight": [0.045, 0.145],
        "contact_enabled": False,
    }


def write_candidate_scene(candidate: Candidate) -> Path:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", f"export4_connected_to_body_v7_{candidate.candidate_id}")

    arm_root = find_required(root, f".//body[@name='{ARM_ROOT_NAME}']", label=ARM_ROOT_NAME)
    arm_pos = parse_vec(arm_root.get("pos", "0 0 0"), (0.0, 0.0, 0.0))
    arm_pos[1] += candidate.arm_root_y_offset_m
    arm_root.set("pos", v5.fmt_vec(arm_pos))

    set_floor_z(root, candidate.floor_z_m)
    replace_support_column(root)

    statistic = root.find("statistic")
    if statistic is not None:
        statistic.set("center", "0 -0.02 0.33")
        statistic.set("extent", "1.05")

    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    CANDIDATE_SCENE_DIR.mkdir(parents=True, exist_ok=True)
    out = CANDIDATE_SCENE_DIR / f"scene_export4_connected_to_body_v7_{candidate.candidate_id}.xml"
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def body_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def geom_z_bounds(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> tuple[float, float] | None:
    gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
    if gid < 0:
        return None
    z_center = float(data.geom_xpos[gid, 2])
    radius = float(model.geom_rbound[gid])
    return z_center - radius, z_center + radius


def inspect_candidate(candidate: Candidate, scene_path: Path) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene_path.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    names = [BODY_ROOT_NAME, ARM_ROOT_NAME, "link_2", "ee_mount", "hand_base_link", "palm_link"]
    positions = {name: body_pos(model, data, name) for name in names}
    pts = [pos for pos in positions.values() if pos is not None]
    center = np.mean(np.asarray(pts), axis=0)
    base = positions.get(ARM_ROOT_NAME, center)
    palm = positions.get("palm_link", center)
    arm_center = 0.5 * (base + palm)

    prefix = IMAGE_DIR / candidate.candidate_id
    shots = {
        "side": v5.render(model, data, prefix.with_name(f"{candidate.candidate_id}_side.png"), center, distance=1.18, azimuth=110, elevation=-16),
        "mount": v5.render(model, data, prefix.with_name(f"{candidate.candidate_id}_mount.png"), arm_center, distance=0.72, azimuth=205, elevation=-14),
        "front": v5.render(model, data, prefix.with_name(f"{candidate.candidate_id}_front.png"), center, distance=1.18, azimuth=205, elevation=-20),
    }

    start_body = positions[BODY_ROOT_NAME]
    start_base = positions[ARM_ROOT_NAME]
    for _ in range(60):
        mujoco.mj_step(model, data)
    end_body = body_pos(model, data, BODY_ROOT_NAME)
    end_base = body_pos(model, data, ARM_ROOT_NAME)

    arm_vec = palm - base
    floor_gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "floor")
    floor_z = float(data.geom_xpos[floor_gid, 2]) if floor_gid >= 0 else None
    support_bounds = geom_z_bounds(model, data, SUPPORT_NAME_V7)
    support_floor_clearance = None
    if support_bounds is not None and floor_z is not None:
        support_floor_clearance = float(support_bounds[0] - floor_z)

    return {
        "candidate_id": candidate.candidate_id,
        "note": candidate.note,
        "scene": scene_path,
        "arm_root_y_offset_m": candidate.arm_root_y_offset_m,
        "floor_z_m": floor_z,
        "support_column": {
            "geom": SUPPORT_NAME_V7,
            "z_bounds_m": support_bounds,
            "bottom_minus_floor_m": support_floor_clearance,
            "contact_enabled": False,
        },
        "positions": {name: pos for name, pos in positions.items() if pos is not None},
        "base_to_palm": arm_vec,
        "base_to_palm_horizontal_ratio": float(np.linalg.norm(arm_vec[:2]) / max(np.linalg.norm(arm_vec), 1e-12)),
        "base_to_palm_z_delta_m": float(arm_vec[2]),
        "finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "motion": {
            "body_drift_m": float(np.linalg.norm(end_body - start_body)) if start_body is not None and end_body is not None else None,
            "base_link_drift_m": float(np.linalg.norm(end_base - start_base)) if start_base is not None and end_base is not None else None,
            "finite_after_step": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        },
        "screenshots": shots,
        "blank_flags": {name: (shot["max_pixel"] - shot["min_pixel"] < 5) for name, shot in shots.items()},
    }


def make_contact_sheet(results: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[Image.Image] = []
    label_h = 38
    cell_w = 480
    cell_h = 340
    for result in results:
        cells = []
        for view_name in ("side", "mount", "front"):
            image_path = Path(result["screenshots"][view_name]["file"])
            image = Image.open(image_path).convert("RGB").resize((cell_w, cell_h))
            cells.append(image)
        row = Image.new("RGB", (cell_w * 3, cell_h + label_h), (22, 26, 30))
        draw = ImageDraw.Draw(row)
        label = (
            f"{result['candidate_id']} | y_offset={result['arm_root_y_offset_m']:+.3f}m | "
            f"floor={result['floor_z_m']:.3f}m | support-floor={result['support_column']['bottom_minus_floor_m']:.3f}m"
        )
        draw.text((10, 10), label, fill=(235, 235, 235))
        for idx, cell in enumerate(cells):
            row.paste(cell, (idx * cell_w, label_h))
        rows.append(row)

    sheet = Image.new("RGB", (cell_w * 3, (cell_h + label_h) * len(rows)), (10, 12, 14))
    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)
    arr = np.asarray(sheet)
    return {
        "file": str(CONTACT_SHEET),
        "mean_pixel": float(arr.mean()),
        "min_pixel": int(arr.min()),
        "max_pixel": int(arr.max()),
    }


def score_candidate(result: dict[str, Any]) -> tuple[int, str]:
    if not result["finite"] or not result["motion"]["finite_after_step"] or any(result["blank_flags"].values()):
        return 0, "fail_load_or_render"
    if result["support_column"]["bottom_minus_floor_m"] is not None and result["support_column"]["bottom_minus_floor_m"] < -0.005:
        return 1, "support_clips_floor"
    if abs(float(result["base_to_palm_z_delta_m"])) > 0.010:
        return 1, "arm_not_horizontal"
    # Prefer preserving the CAD mount origin unless visual review shows a gap.
    origin_penalty = abs(float(result["arm_root_y_offset_m"]))
    score = int(1000 - origin_penalty * 10000)
    return score, "preserve_mount_origin_floor_clear"


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(v5.json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Body Connection V7 Candidate Sweep Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Contact sheet: `{payload['contact_sheet']['file']}`\n",
        f"- Selected by automatic gate: `{payload['selected_candidate_id']}`\n",
        "- Orientation policy: keep v6 whole-arm world-Z -90 deg correction; no hand-local twist.\n",
        "- Sweep policy: only arm-root depth and floor/support visual cleanup are changed.\n\n",
        "## Candidates\n\n",
    ]
    for result in payload["candidates"]:
        lines.extend(
            [
                f"### {result['candidate_id']}\n\n",
                f"- scene: `{result['scene']}`\n",
                f"- note: {result['note']}\n",
                f"- arm_root_y_offset_m: `{result['arm_root_y_offset_m']}`\n",
                f"- floor_z_m: `{result['floor_z_m']}`\n",
                f"- support_bottom_minus_floor_m: `{result['support_column']['bottom_minus_floor_m']}`\n",
                f"- base_to_palm_horizontal_ratio: `{result['base_to_palm_horizontal_ratio']:.6f}`\n",
                f"- base_to_palm_z_delta_m: `{result['base_to_palm_z_delta_m']:.6f}`\n",
                f"- gate_reason: `{result['gate_reason']}`\n",
                f"- score: `{result['score']}`\n",
                f"- side: `{result['screenshots']['side']['file']}`\n",
                f"- mount: `{result['screenshots']['mount']['file']}`\n",
                f"- front: `{result['screenshots']['front']['file']}`\n\n",
            ]
        )
    lines.extend(
        [
            "## Notes\n\n",
            "- The selected candidate is still `needs_user_confirmation` because the body-side CAD mount frame is represented by one exported body link plus visual proxies.\n",
            "- Positive y offsets move the arm inward relative to the accepted v6 direction; negative y offsets move it outward.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    results = []
    for candidate in CANDIDATES:
        scene_path = write_candidate_scene(candidate)
        result = inspect_candidate(candidate, scene_path)
        score, reason = score_candidate(result)
        result["score"] = score
        result["gate_reason"] = reason
        results.append(result)

    selected = max(results, key=lambda item: item["score"])
    contact_sheet = make_contact_sheet(results)
    payload = {
        "generated_at": now(),
        "source_scene": SOURCE_SCENE,
        "selected_candidate_id": selected["candidate_id"],
        "contact_sheet": contact_sheet,
        "candidates": results,
    }
    write_outputs(payload)
    print(f"Saved metadata: {META}")
    print(f"Saved report: {REPORT}")
    print(f"Saved contact sheet: {CONTACT_SHEET}")
    print(f"Selected candidate: {selected['candidate_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
