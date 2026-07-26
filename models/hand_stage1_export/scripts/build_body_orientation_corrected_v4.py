#!/usr/bin/env python3
"""Apply the v4 visual mount feedback on top of the v3 body scene.

V4 keeps the accepted v3 body/arm orientation candidate and adds only the
latest visual deltas:

- lift the whole body/arm/hand chain above the floor,
- twist the hand mount 90 deg in the horizontal plane,
- add a simple support column placeholder under the body block.
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v3.xml"
OUT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v4.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_corrected_v4"
CANDIDATE_DIR = VIS / "candidates"
REPORT = DOCS / "body_connection_orientation_corrected_v4_report.md"
META = ROOT / "metadata" / "body_connection_orientation_corrected_v4.json"

BODY_ROOT_NAME = "rough_body_support_link"
HAND_ROOT_NAME = "hand_base_link"
SUPPORT_COLUMN_NAME = "body_support_column_visual_v4"

BODY_ROOT_Z_LIFT_M = 0.18
HAND_LOCAL_TWIST_AXIS = "Z"
HAND_LOCAL_TWIST_DEG = 90.0


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def fmt_vec(values: np.ndarray | list[float]) -> str:
    return " ".join(f"{float(v):.10g}" for v in values)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def axis_angle(axis: tuple[float, float, float], angle_deg: float) -> np.ndarray:
    axis_v = np.asarray(axis, dtype=np.float64)
    axis_v = axis_v / np.linalg.norm(axis_v)
    half = math.radians(angle_deg) * 0.5
    return np.array([math.cos(half), *(math.sin(half) * axis_v)], dtype=np.float64)


def quat_mul(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return np.array(
        [
            lw * rw - lx * rx - ly * ry - lz * rz,
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
        ],
        dtype=np.float64,
    )


def find_required(root: ET.Element, path: str, *, label: str) -> ET.Element:
    item = root.find(path)
    if item is None:
        raise RuntimeError(f"Missing {label}: {path}")
    return item


def add_support_column(world: ET.Element) -> None:
    existing = world.find(f".//geom[@name='{SUPPORT_COLUMN_NAME}']")
    if existing is not None:
        return
    world.append(
        ET.Element(
            "geom",
            {
                "name": SUPPORT_COLUMN_NAME,
                "type": "cylinder",
                "pos": "0.0 0.100 0.020",
                "size": "0.045 0.160",
                "rgba": "0.42 0.44 0.46 0.55",
                "contype": "0",
                "conaffinity": "0",
                "group": "2",
            },
        )
    )


def apply_v4_delta(tree: ET.ElementTree) -> dict[str, Any]:
    root = tree.getroot()
    root.set("model", "export4_connected_to_body_corrected_v4")

    body_root = find_required(root, f".//body[@name='{BODY_ROOT_NAME}']", label=BODY_ROOT_NAME)
    body_root.set("pos", f"0 0 {BODY_ROOT_Z_LIFT_M:.10g}")

    hand_root = find_required(root, f".//body[@name='{HAND_ROOT_NAME}']", label=HAND_ROOT_NAME)
    old_hand_quat = np.fromstring(hand_root.get("quat", "1 0 0 0"), sep=" ")
    local_twist = axis_angle((0, 0, 1), HAND_LOCAL_TWIST_DEG)
    new_hand_quat = quat_mul(old_hand_quat, local_twist)
    hand_root.set("quat", fmt_vec(new_hand_quat))

    world = find_required(root, "worldbody", label="worldbody")
    add_support_column(world)

    statistic = root.find("statistic")
    if statistic is not None:
        statistic.set("center", "0 0.06 0.34")
        statistic.set("extent", "1.05")

    return {
        "body_root_z_lift_m": BODY_ROOT_Z_LIFT_M,
        "old_hand_quat_wxyz": old_hand_quat,
        "hand_local_twist_axis": HAND_LOCAL_TWIST_AXIS,
        "hand_local_twist_deg": HAND_LOCAL_TWIST_DEG,
        "new_hand_quat_wxyz": new_hand_quat,
        "support_column": {
            "name": SUPPORT_COLUMN_NAME,
            "type": "cylinder",
            "pos": [0.0, 0.100, 0.020],
            "size_radius_halfheight": [0.045, 0.160],
            "contact_enabled": False,
        },
    }


def write_scene() -> dict[str, Any]:
    tree = ET.parse(SOURCE_SCENE)
    payload = apply_v4_delta(tree)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    OUT_SCENE.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUT_SCENE, encoding="utf-8", xml_declaration=True)
    return payload


def body_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def geom_z_bounds(model: mujoco.MjModel, data: mujoco.MjData, geom_name: str) -> tuple[float, float] | None:
    gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
    if gid < 0:
        return None
    z_center = float(data.geom_xpos[gid, 2])
    radius = float(model.geom_rbound[gid])
    return z_center - radius, z_center + radius


def pose_metrics(model: mujoco.MjModel, data: mujoco.MjData) -> dict[str, Any]:
    names = [BODY_ROOT_NAME, "base_link", "link_2", "ee_mount", HAND_ROOT_NAME, "palm_link"]
    positions = {name: body_pos(model, data, name) for name in names}
    floor_gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "floor")
    floor_z = float(data.geom_xpos[floor_gid, 2]) if floor_gid >= 0 else None
    support_bounds = geom_z_bounds(model, data, SUPPORT_COLUMN_NAME)

    base = positions.get("base_link")
    palm = positions.get("palm_link")
    arm_vec = palm - base if base is not None and palm is not None else np.zeros(3)
    return {
        "positions": {name: pos for name, pos in positions.items() if pos is not None},
        "base_to_palm": arm_vec,
        "base_to_palm_horizontal_ratio": float(np.linalg.norm(arm_vec[:2]) / max(np.linalg.norm(arm_vec), 1e-12)),
        "base_to_palm_z_delta_m": float(arm_vec[2]),
        "floor_z_m": floor_z,
        "support_column_z_bounds_m": support_bounds,
    }


def render(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    output: Path,
    lookat: np.ndarray,
    *,
    distance: float,
    azimuth: float,
    elevation: float,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=960, height=680)
    try:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = distance
        cam.azimuth = azimuth
        cam.elevation = elevation
        renderer.update_scene(data, camera=cam)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "mean_pixel": float(image.mean()),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
    }


def inspect_scene() -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    metrics = pose_metrics(model, data)
    pts = list(metrics["positions"].values())
    center = np.mean(np.asarray(pts), axis=0)
    base = metrics["positions"].get("base_link", center)
    palm = metrics["positions"].get("palm_link", center)
    arm_center = 0.5 * (base + palm)
    shots = {
        "front": render(model, data, CANDIDATE_DIR / "selected_v4_front.png", center, distance=1.18, azimuth=205, elevation=-20),
        "side": render(model, data, CANDIDATE_DIR / "selected_v4_side.png", center, distance=1.18, azimuth=110, elevation=-16),
        "mount": render(model, data, CANDIDATE_DIR / "selected_v4_mount.png", arm_center, distance=0.72, azimuth=205, elevation=-14),
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
        "metrics": metrics,
        "screenshots": shots,
        "blank_flags": {name: (shot["max_pixel"] - shot["min_pixel"] < 5) for name, shot in shots.items()},
    }


def motion_check() -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    start_body = body_pos(model, data, BODY_ROOT_NAME)
    start_base = body_pos(model, data, "base_link")
    for _ in range(60):
        mujoco.mj_step(model, data)
    after_body = body_pos(model, data, BODY_ROOT_NAME)
    after_base = body_pos(model, data, "base_link")
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
        "status": "v4_visual_feedback_candidate_needs_user_confirmation",
        "load_finite_render_gate": "PASS" if load_gate else "FAIL",
        "v4_delta": delta,
        "inspection": inspection,
        "motion_check": motion,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    delta = payload["v4_delta"]
    metrics = payload["inspection"]["metrics"]
    lines = [
        "# Body Connection Orientation Corrected V4 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Corrected scene: `{payload['output_scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Load/finite/render gate: `{payload['load_finite_render_gate']}`\n",
        f"- Body root z lift: `{delta['body_root_z_lift_m']:.3f} m`\n",
        f"- Hand local twist: `{delta['hand_local_twist_deg']:.1f} deg about local {delta['hand_local_twist_axis']}`\n",
        f"- New hand quat wxyz: `{fmt_vec(delta['new_hand_quat_wxyz'])}`\n",
        f"- Support column: `{delta['support_column']['name']}` contact-disabled visual cylinder\n\n",
        "## Selected Metrics\n\n",
        f"- floor_z_m: `{metrics['floor_z_m']}`\n",
        f"- support_column_z_bounds_m: `{metrics['support_column_z_bounds_m']}`\n",
        f"- base_to_palm_horizontal_ratio: `{metrics['base_to_palm_horizontal_ratio']:.6f}`\n",
        f"- base_to_palm_z_delta_m: `{metrics['base_to_palm_z_delta_m']:.6f}`\n\n",
        "## Final Screenshots\n\n",
    ]
    for name, shot in payload["inspection"]["screenshots"].items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Motion Smoke\n\n",
            f"- finite_after_step: `{payload['motion_check']['finite_after_step']}`\n",
            f"- body_drift_m: `{payload['motion_check']['body_drift_m']}`\n",
            f"- base_link_drift_m: `{payload['motion_check']['base_link_drift_m']}`\n\n",
            "## Notes\n\n",
            "- V4 is a visual mount candidate only. It preserves the v3 body and arm-root correction, then applies the latest user feedback as explicit deltas.\n",
            "- The support column is a contact-disabled placeholder until the CAD pillar/column part is exported into the runtime asset.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_payload()
    write_outputs(payload)
    print(f"Saved scene: {OUT_SCENE}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    print(f"Gate: {payload['load_finite_render_gate']}")


if __name__ == "__main__":
    main()
