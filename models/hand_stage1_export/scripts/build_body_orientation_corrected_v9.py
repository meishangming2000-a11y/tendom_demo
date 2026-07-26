#!/usr/bin/env python3
"""Build v9: preserve v8 pose, attach the support visual to the body root.

V8 imports and renders in Isaac Lab, but the temporary support column is a
world-level MJCF geom. Isaac's MJCF importer appears to drop or de-emphasize
that world geom. V9 keeps the same world pose while moving the support column
under `rough_body_support_link`, so it is part of the imported body asset.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

import build_body_orientation_corrected_v5 as v5


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v8.xml"
OUT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v9.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_corrected_v9"
CANDIDATE_DIR = VIS / "candidates"
REPORT = DOCS / "body_connection_orientation_corrected_v9_report.md"
META = ROOT / "metadata" / "body_connection_orientation_corrected_v9.json"

BODY_ROOT_NAME = "rough_body_support_link"
ARM_ROOT_NAME = "base_link"
HAND_ROOT_NAME = "hand_base_link"
OLD_SUPPORT_NAME = "body_support_column_visual_v8"
SUPPORT_COLUMN_NAME = "body_support_column_visual_v9"

BODY_ROOT_WORLD_POS_M = np.array([0.0, 0.0, 0.18], dtype=np.float64)
SUPPORT_WORLD_POS_M = np.array([0.0, 0.100, 0.030], dtype=np.float64)
SUPPORT_LOCAL_POS_M = SUPPORT_WORLD_POS_M - BODY_ROOT_WORLD_POS_M
SUPPORT_SIZE_M = [0.045, 0.150]
FLOOR_Z_M = -0.12


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def find_required(root: ET.Element, path: str, *, label: str) -> ET.Element:
    item = root.find(path)
    if item is None:
        raise RuntimeError(f"Missing {label}: {path}")
    return item


def remove_world_support(world: ET.Element) -> None:
    for geom in list(world.findall("geom")):
        if geom.get("name", "").startswith("body_support_column_visual_"):
            world.remove(geom)


def add_body_support(body_root: ET.Element) -> dict[str, Any]:
    for geom in list(body_root.findall("geom")):
        if geom.get("name", "").startswith("body_support_column_visual_"):
            body_root.remove(geom)
    support = ET.Element(
        "geom",
        {
            "name": SUPPORT_COLUMN_NAME,
            "type": "cylinder",
            "pos": v5.fmt_vec(SUPPORT_LOCAL_POS_M),
            "size": v5.fmt_vec(SUPPORT_SIZE_M),
            "rgba": "0.42 0.44 0.46 0.55",
            "contype": "0",
            "conaffinity": "0",
            "group": "2",
        },
    )
    body_root.append(support)
    return {
        "name": SUPPORT_COLUMN_NAME,
        "old_world_geom": OLD_SUPPORT_NAME,
        "new_parent_body": BODY_ROOT_NAME,
        "world_pos_m": SUPPORT_WORLD_POS_M,
        "local_pos_m": SUPPORT_LOCAL_POS_M,
        "size_radius_halfheight_m": SUPPORT_SIZE_M,
        "exact_z_span_m": [FLOOR_Z_M, float(BODY_ROOT_WORLD_POS_M[2])],
        "contact_enabled": False,
    }


def write_scene() -> dict[str, Any]:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", "export4_connected_to_body_corrected_v9")
    body_root = find_required(root, f".//body[@name='{BODY_ROOT_NAME}']", label=BODY_ROOT_NAME)
    world = find_required(root, "worldbody", label="worldbody")
    remove_world_support(world)
    support = add_body_support(body_root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    OUT_SCENE.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUT_SCENE, encoding="utf-8", xml_declaration=True)
    return {
        "source_scene": SOURCE_SCENE,
        "body_root_world_pos_m": BODY_ROOT_WORLD_POS_M,
        "arm_root_pose_policy": "unchanged_from_v8",
        "support_column": support,
    }


def body_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def geom_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
    return data.geom_xpos[gid].copy() if gid >= 0 else None


def inspect_scene() -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    names = [BODY_ROOT_NAME, ARM_ROOT_NAME, "link_2", "ee_mount", HAND_ROOT_NAME, "palm_link"]
    positions = {name: body_pos(model, data, name) for name in names}
    support_world = geom_pos(model, data, SUPPORT_COLUMN_NAME)
    pts = [pos for pos in positions.values() if pos is not None]
    center = np.mean(np.asarray(pts), axis=0)
    base = positions.get(ARM_ROOT_NAME, center)
    palm = positions.get("palm_link", center)
    arm_center = 0.5 * (base + palm)
    arm_vec = palm - base
    shots = {
        "front": v5.render(model, data, CANDIDATE_DIR / "selected_v9_front.png", center, distance=1.18, azimuth=205, elevation=-20),
        "side": v5.render(model, data, CANDIDATE_DIR / "selected_v9_side.png", center, distance=1.18, azimuth=110, elevation=-16),
        "mount": v5.render(model, data, CANDIDATE_DIR / "selected_v9_mount.png", arm_center, distance=0.72, azimuth=205, elevation=-14),
    }
    return {
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
        },
        "finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "positions": {name: pos for name, pos in positions.items() if pos is not None},
        "support_column_world_pos_m": support_world,
        "base_to_palm": arm_vec,
        "base_to_palm_horizontal_ratio": float(np.linalg.norm(arm_vec[:2]) / max(np.linalg.norm(arm_vec), 1e-12)),
        "base_to_palm_z_delta_m": float(arm_vec[2]),
        "screenshots": shots,
        "blank_flags": {name: (shot["max_pixel"] - shot["min_pixel"] < 5) for name, shot in shots.items()},
    }


def motion_check() -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    start_body = body_pos(model, data, BODY_ROOT_NAME)
    start_base = body_pos(model, data, ARM_ROOT_NAME)
    for _ in range(60):
        mujoco.mj_step(model, data)
    after_body = body_pos(model, data, BODY_ROOT_NAME)
    after_base = body_pos(model, data, ARM_ROOT_NAME)
    return {
        "finite_after_step": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "body_drift_m": float(np.linalg.norm(after_body - start_body)) if start_body is not None and after_body is not None else None,
        "base_link_drift_m": float(np.linalg.norm(after_base - start_base)) if start_base is not None and after_base is not None else None,
    }


def build_payload() -> dict[str, Any]:
    delta = write_scene()
    inspection = inspect_scene()
    motion = motion_check()
    gate = inspection["finite"] and motion["finite_after_step"] and not any(inspection["blank_flags"].values())
    return {
        "generated_at": now(),
        "source_scene": SOURCE_SCENE,
        "output_scene": OUT_SCENE,
        "status": "v9_support_attached_to_body_root_for_isaac_import_needs_visual_confirmation",
        "load_finite_render_gate": "PASS" if gate else "FAIL",
        "v9_delta": delta,
        "inspection": inspection,
        "motion_check": motion,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(v5.json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    delta = payload["v9_delta"]
    inspection = payload["inspection"]
    lines = [
        "# Body Connection Orientation Corrected V9 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Corrected scene: `{payload['output_scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Load/finite/render gate: `{payload['load_finite_render_gate']}`\n",
        "- Arm/body orientation: `unchanged_from_v8`\n",
        f"- Support column parent: `{delta['support_column']['new_parent_body']}`\n",
        f"- Support column local pos: `{v5.fmt_vec(delta['support_column']['local_pos_m'])}`\n",
        f"- Support column world pos: `{v5.fmt_vec(inspection['support_column_world_pos_m'])}`\n\n",
        "## Selected Metrics\n\n",
        f"- base_to_palm_horizontal_ratio: `{inspection['base_to_palm_horizontal_ratio']:.6f}`\n",
        f"- base_to_palm_z_delta_m: `{inspection['base_to_palm_z_delta_m']:.6f}`\n\n",
        "## Final Screenshots\n\n",
    ]
    for name, shot in inspection["screenshots"].items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Notes\n\n",
            "- V9 changes only the temporary support-column parent in MJCF; it keeps the v8 world pose and arm orientation.\n",
            "- This is an Isaac-import compatibility candidate, not a new CAD truth claim.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    payload = build_payload()
    write_outputs(payload)
    print(f"Saved scene: {OUT_SCENE}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    print(f"Gate: {payload['load_finite_render_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
