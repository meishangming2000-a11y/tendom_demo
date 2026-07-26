#!/usr/bin/env python3
"""Build the selected MuJoCo body connection after v7 candidate review.

V8 keeps the accepted v6 body/arm orientation and the original body-arm mount
origin. The only geometry cleanup is the temporary visual support column:
bottom flush with the floor and top aligned to the body root height.
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
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v6.xml"
OUT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v8.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_corrected_v8"
CANDIDATE_DIR = VIS / "candidates"
REPORT = DOCS / "body_connection_orientation_corrected_v8_report.md"
META = ROOT / "metadata" / "body_connection_orientation_corrected_v8.json"

BODY_ROOT_NAME = "rough_body_support_link"
ARM_ROOT_NAME = "base_link"
HAND_ROOT_NAME = "hand_base_link"
SUPPORT_COLUMN_NAME = "body_support_column_visual_v8"

V6_ARM_QUAT_WXYZ = np.array([0.5, 0.5, -0.5, 0.5], dtype=np.float64)
BODY_ROOT_Z_LIFT_M = 0.18
FLOOR_Z_M = -0.12
SUPPORT_RADIUS_M = 0.045
SUPPORT_HALFHEIGHT_M = (BODY_ROOT_Z_LIFT_M - FLOOR_Z_M) * 0.5
SUPPORT_CENTER_Z_M = (BODY_ROOT_Z_LIFT_M + FLOOR_Z_M) * 0.5
SUPPORT_POS_M = np.array([0.0, 0.100, SUPPORT_CENTER_Z_M], dtype=np.float64)


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


def set_floor_z(root: ET.Element) -> None:
    floor = find_required(root, ".//geom[@name='floor']", label="floor")
    pos = parse_vec(floor.get("pos", "0 0 0"), (0.0, 0.0, 0.0))
    pos[2] = FLOOR_Z_M
    floor.set("pos", v5.fmt_vec(pos))


def replace_support_column(root: ET.Element) -> dict[str, Any]:
    world = find_required(root, "worldbody", label="worldbody")
    for geom in list(world.findall("geom")):
        name = geom.get("name", "")
        if name.startswith("body_support_column_visual_"):
            world.remove(geom)
    support = ET.Element(
        "geom",
        {
            "name": SUPPORT_COLUMN_NAME,
            "type": "cylinder",
            "pos": v5.fmt_vec(SUPPORT_POS_M),
            "size": v5.fmt_vec([SUPPORT_RADIUS_M, SUPPORT_HALFHEIGHT_M]),
            "rgba": "0.42 0.44 0.46 0.55",
            "contype": "0",
            "conaffinity": "0",
            "group": "2",
        },
    )
    world.append(support)
    return {
        "name": SUPPORT_COLUMN_NAME,
        "type": "cylinder",
        "pos": SUPPORT_POS_M,
        "size_radius_halfheight": [SUPPORT_RADIUS_M, SUPPORT_HALFHEIGHT_M],
        "exact_z_span_m": [FLOOR_Z_M, BODY_ROOT_Z_LIFT_M],
        "contact_enabled": False,
    }


def write_scene() -> dict[str, Any]:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", "export4_connected_to_body_corrected_v8")

    body_root = find_required(root, f".//body[@name='{BODY_ROOT_NAME}']", label=BODY_ROOT_NAME)
    body_root.set("pos", f"0 0 {BODY_ROOT_Z_LIFT_M:.10g}")

    arm_root = find_required(root, f".//body[@name='{ARM_ROOT_NAME}']", label=ARM_ROOT_NAME)
    old_arm_pos = parse_vec(arm_root.get("pos", "0 0 0"), (0.0, 0.0, 0.0))
    old_arm_quat = parse_vec(arm_root.get("quat", "1 0 0 0"), (1.0, 0.0, 0.0, 0.0))
    arm_root.set("pos", "0 0 0")
    arm_root.set("quat", v5.fmt_vec(V6_ARM_QUAT_WXYZ))

    hand_root = find_required(root, f".//body[@name='{HAND_ROOT_NAME}']", label=HAND_ROOT_NAME)
    hand_quat = parse_vec(hand_root.get("quat", "1 0 0 0"), (1.0, 0.0, 0.0, 0.0))

    set_floor_z(root)
    support = replace_support_column(root)

    statistic = root.find("statistic")
    if statistic is not None:
        statistic.set("center", "0 0.04 0.34")
        statistic.set("extent", "1.05")

    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    OUT_SCENE.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUT_SCENE, encoding="utf-8", xml_declaration=True)
    return {
        "source_scene": SOURCE_SCENE,
        "body_root_z_lift_m": BODY_ROOT_Z_LIFT_M,
        "old_arm_pos_m": old_arm_pos,
        "new_arm_pos_m": [0.0, 0.0, 0.0],
        "old_arm_quat_wxyz": old_arm_quat,
        "new_arm_quat_wxyz": V6_ARM_QUAT_WXYZ,
        "arm_world_yaw_axis": "world_Z",
        "arm_world_yaw_deg": -90.0,
        "hand_quat_wxyz": hand_quat,
        "hand_local_twist_applied": False,
        "floor_z_m": FLOOR_Z_M,
        "support_column": support,
    }


def body_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def inspect_scene() -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    names = [BODY_ROOT_NAME, ARM_ROOT_NAME, "link_2", "ee_mount", HAND_ROOT_NAME, "palm_link"]
    positions = {name: body_pos(model, data, name) for name in names}
    pts = [pos for pos in positions.values() if pos is not None]
    center = np.mean(np.asarray(pts), axis=0)
    base = positions.get(ARM_ROOT_NAME, center)
    palm = positions.get("palm_link", center)
    arm_center = 0.5 * (base + palm)
    arm_vec = palm - base

    shots = {
        "front": v5.render(model, data, CANDIDATE_DIR / "selected_v8_front.png", center, distance=1.18, azimuth=205, elevation=-20),
        "side": v5.render(model, data, CANDIDATE_DIR / "selected_v8_side.png", center, distance=1.18, azimuth=110, elevation=-16),
        "mount": v5.render(model, data, CANDIDATE_DIR / "selected_v8_mount.png", arm_center, distance=0.72, azimuth=205, elevation=-14),
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
        "base_to_palm": arm_vec,
        "base_to_palm_horizontal_ratio": float(np.linalg.norm(arm_vec[:2]) / max(np.linalg.norm(arm_vec), 1e-12)),
        "base_to_palm_z_delta_m": float(arm_vec[2]),
        "floor_z_m": FLOOR_Z_M,
        "support_column_exact_z_span_m": [FLOOR_Z_M, BODY_ROOT_Z_LIFT_M],
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
    load_gate = inspection["finite"] and motion["finite_after_step"] and not any(inspection["blank_flags"].values())
    return {
        "generated_at": now(),
        "source_scene": SOURCE_SCENE,
        "output_scene": OUT_SCENE,
        "status": "v8_mount_origin_preserved_support_flush_selected_needs_user_confirmation",
        "supersedes": {
            "scene": ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v6.xml",
            "reason": "v6 direction is preserved; v8 cleans up the temporary support/floor visual after v7 candidate review.",
        },
        "v7_candidate_sweep": {
            "report": ROOT / "docs" / "body_connection_v7_candidate_sweep_report.md",
            "contact_sheet": ROOT / "docs" / "visual_checks_body_connection_v7_candidates" / "body_connection_v7_candidate_contact_sheet.png",
            "selected_candidate": "origin_floor_clear",
            "rejected_offsets": ["outward_15mm", "outward_30mm", "inward_15mm"],
            "reason": "Offsets visibly start detaching or increasing penetration risk; preserving the v6 mount origin is safer until CAD confirms a different mate frame.",
        },
        "load_finite_render_gate": "PASS" if load_gate else "FAIL",
        "v8_delta": delta,
        "inspection": inspection,
        "motion_check": motion,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(v5.json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    delta = payload["v8_delta"]
    inspection = payload["inspection"]
    lines = [
        "# Body Connection Orientation Corrected V8 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Corrected scene: `{payload['output_scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Supersedes reason: `{payload['supersedes']['reason']}`\n",
        f"- V7 candidate contact sheet: `{payload['v7_candidate_sweep']['contact_sheet']}`\n",
        f"- Load/finite/render gate: `{payload['load_finite_render_gate']}`\n",
        f"- Body root z lift: `{delta['body_root_z_lift_m']:.3f} m`\n",
        f"- Arm root pos: `{v5.fmt_vec(delta['new_arm_pos_m'])}`\n",
        f"- Arm quat wxyz: `{v5.fmt_vec(delta['new_arm_quat_wxyz'])}`\n",
        f"- Hand local twist applied: `{delta['hand_local_twist_applied']}`\n",
        f"- Floor z: `{delta['floor_z_m']:.3f} m`\n",
        f"- Support column: `{delta['support_column']['name']}` exact z span `{v5.fmt_vec(delta['support_column']['exact_z_span_m'])}`\n\n",
        "## Selected Metrics\n\n",
        f"- base_to_palm: `{v5.fmt_vec(inspection['base_to_palm'])}`\n",
        f"- base_to_palm_horizontal_ratio: `{inspection['base_to_palm_horizontal_ratio']:.6f}`\n",
        f"- base_to_palm_z_delta_m: `{inspection['base_to_palm_z_delta_m']:.6f}`\n\n",
        "## Final Screenshots\n\n",
    ]
    for name, shot in inspection["screenshots"].items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Motion Smoke\n\n",
            f"- finite_after_step: `{payload['motion_check']['finite_after_step']}`\n",
            f"- body_drift_m: `{payload['motion_check']['body_drift_m']}`\n",
            f"- base_link_drift_m: `{payload['motion_check']['base_link_drift_m']}`\n\n",
            "## Notes\n\n",
            "- V8 preserves the v6 user-selected body side and whole-arm -90 deg world-Z yaw.\n",
            "- V7 offset candidates are retained as evidence but not promoted because the mount origin should not move without CAD mate confirmation.\n",
            "- The support column remains a contact-disabled visual placeholder until the real CAD support/pillar is exported.\n",
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
