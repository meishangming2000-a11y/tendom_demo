#!/usr/bin/env python3
"""Build proxy hand-insertion candidates for the motor bay.

The motor bay export currently provides only `motor_bay_mount_csys`. Until a
real wrist-side CSYS is exported, these candidates use the motor-bay STL distal
end as a proxy hand-side frame. They are diagnostic, not final mechanical truth.
"""

from __future__ import annotations

import json
import struct
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_with_motor_bay_fixed_v0_candidate.xml"
MESH_PATH = ROOT / "meshes_export4" / "motor_bay_link.STL"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_motor_bay_hand_insert_proxy_v0"
REPORT = DOCS / "motor_bay_hand_insert_proxy_v0_report.md"
META_OUT = META / "motor_bay_hand_insert_proxy_v0.json"


VARIANTS = [
    {
        "name": "keep_current_hand_clock",
        "scene": ROOT / "mjcf" / "scene_export4_with_motor_bay_hand_insert_proxy_keep_clock_v0.xml",
        "hand_quat": "0 0 0 1",
        "meaning": "Preserve the existing hand clocking relative to the arm flange; relative rotation is local RotZ(pi).",
    },
    {
        "name": "flip_hand_clock_180",
        "scene": ROOT / "mjcf" / "scene_export4_with_motor_bay_hand_insert_proxy_flip_clock_v0.xml",
        "hand_quat": "1 0 0 0",
        "meaning": "Flip the hand clocking by 180 degrees around the motor-bay local Z compared with the current hand mount.",
    },
]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def fmt(values: np.ndarray | list[float] | tuple[float, ...], *, precision: int = 12) -> str:
    return " ".join(f"{float(v):.{precision}g}" for v in values)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def stl_bbox(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    verts: list[tuple[float, float, float]] = []
    if len(data) >= 84:
        tri_count = struct.unpack("<I", data[80:84])[0]
        expected = 84 + 50 * tri_count
        if expected == len(data):
            offset = 84
            for _ in range(tri_count):
                offset += 12
                values = struct.unpack("<9f", data[offset : offset + 36])
                offset += 38
                verts.extend([values[0:3], values[3:6], values[6:9]])
    if not verts:
        raise RuntimeError(f"Could not parse binary STL bbox: {path}")
    mins = np.array([min(v[i] for v in verts) for i in range(3)], dtype=np.float64)
    maxs = np.array([max(v[i] for v in verts) for i in range(3)], dtype=np.float64)
    return {
        "min": mins,
        "max": maxs,
        "size": maxs - mins,
        "triangles": len(verts) // 3,
    }


def find_body(root: ET.Element, name: str) -> ET.Element:
    body = root.find(f".//body[@name='{name}']")
    if body is None:
        raise RuntimeError(f"Missing body `{name}` in {SOURCE_SCENE}")
    return body


def remove_child(parent: ET.Element, child: ET.Element) -> None:
    for item in list(parent):
        if item is child:
            parent.remove(item)
            return
    raise RuntimeError("Expected child was not a direct child of parent")


def remove_existing_proxy_sites(motor_bay: ET.Element) -> None:
    for item in list(motor_bay.findall("site")):
        if item.get("name", "").startswith("motor_bay_wrist_proxy"):
            motor_bay.remove(item)


def add_proxy_sites(motor_bay: ET.Element, z_m: float) -> None:
    remove_existing_proxy_sites(motor_bay)
    sites = [
        ("motor_bay_wrist_proxy_origin", [0.0, 0.0, z_m], "1 0.85 0.1 1", "0.006"),
        ("motor_bay_wrist_proxy_x", [0.055, 0.0, z_m], "1 0 0 1", "0.004"),
        ("motor_bay_wrist_proxy_y", [0.0, 0.055, z_m], "0 1 0 1", "0.004"),
        ("motor_bay_wrist_proxy_z", [0.0, 0.0, z_m + 0.055], "0.05 0.2 1 1", "0.004"),
    ]
    for name, pos, rgba, size in sites:
        motor_bay.append(
            ET.Element(
                "site",
                {
                    "name": name,
                    "pos": fmt(pos),
                    "size": size,
                    "rgba": rgba,
                    "type": "sphere",
                },
            )
        )


def build_variant(variant: dict[str, Any], distal_z_m: float) -> Path:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", f"export4_with_motor_bay_hand_insert_proxy_{variant['name']}_v0")
    ee_mount = find_body(root, "ee_mount")
    motor_bay = find_body(root, "motor_bay_link")
    hand = ee_mount.find("body[@name='hand_base_link']")
    if hand is None:
        raise RuntimeError("Expected `hand_base_link` as direct child of `ee_mount` before proxy insertion")

    remove_child(ee_mount, hand)
    add_proxy_sites(motor_bay, distal_z_m)
    hand.set("pos", fmt([0.0, 0.0, distal_z_m]))
    hand.set("quat", variant["hand_quat"])
    motor_bay.append(hand)

    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    out_scene = Path(variant["scene"])
    out_scene.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_scene, encoding="utf-8", xml_declaration=True)
    return out_scene


def body_pose(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> dict[str, Any] | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid < 0:
        return None
    return {
        "world_pos": data.xpos[bid].copy(),
        "world_xquat": data.xquat[bid].copy(),
    }


def site_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if sid < 0:
        return None
    return data.site_xpos[sid].copy()


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
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = lookat
        camera.distance = float(distance)
        camera.azimuth = float(azimuth)
        camera.elevation = float(elevation)
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": output,
        "mean_pixel": float(image.mean()),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
    }


def inspect_variant(variant: dict[str, Any], scene: Path) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    poses = {
        "ee_mount": body_pose(model, data, "ee_mount"),
        "motor_bay_link": body_pose(model, data, "motor_bay_link"),
        "hand_base_link": body_pose(model, data, "hand_base_link"),
        "palm_link": body_pose(model, data, "palm_link"),
    }
    wrist_proxy = site_pos(model, data, "motor_bay_wrist_proxy_origin")
    hand_pos = poses["hand_base_link"]["world_pos"] if poses["hand_base_link"] else None
    hand_proxy_delta = None
    if wrist_proxy is not None and hand_pos is not None:
        hand_proxy_delta = hand_pos - wrist_proxy

    qpos0 = data.qpos.copy()
    qvel0 = data.qvel.copy()
    for _ in range(120):
        mujoco.mj_step(model, data)
    finite_after_step = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    data.qpos[:] = qpos0
    data.qvel[:] = qvel0
    mujoco.mj_forward(model, data)

    centers = [
        pose["world_pos"]
        for pose in poses.values()
        if pose is not None
    ]
    center = np.mean(np.asarray(centers), axis=0)
    mount_center = poses["motor_bay_link"]["world_pos"] if poses["motor_bay_link"] else center
    shots = {}
    render_error = None
    try:
        shot_dir = VIS / variant["name"]
        shots = {
            "full": render(
                model,
                data,
                shot_dir / "full.png",
                center,
                distance=0.95,
                azimuth=205,
                elevation=-18,
            ),
            "side": render(
                model,
                data,
                shot_dir / "side.png",
                mount_center,
                distance=0.55,
                azimuth=110,
                elevation=-12,
            ),
            "top": render(
                model,
                data,
                shot_dir / "top.png",
                mount_center,
                distance=0.55,
                azimuth=180,
                elevation=-75,
            ),
        }
    except Exception as exc:
        render_error = repr(exc)
    blank_flags = {
        name: (shot["max_pixel"] - shot["min_pixel"] < 5)
        for name, shot in shots.items()
    }
    return {
        "scene": scene,
        "meaning": variant["meaning"],
        "hand_local_pos": None,
        "hand_local_quat": variant["hand_quat"],
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
        },
        "finite_initial": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "finite_after_step": finite_after_step,
        "poses": poses,
        "hand_proxy_delta_norm_m": None if hand_proxy_delta is None else float(np.linalg.norm(hand_proxy_delta)),
        "hand_proxy_delta_xyz_m": hand_proxy_delta,
        "render_error": render_error,
        "screenshots": shots,
        "blank_flags": blank_flags,
    }


def compare_to_fixed_candidate() -> dict[str, Any]:
    fixed = mujoco.MjModel.from_xml_path(str(SOURCE_SCENE.resolve()))
    fixed_actuators = [
        mujoco.mj_id2name(fixed, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        for i in range(fixed.nu)
    ]
    fixed_joints = [
        mujoco.mj_id2name(fixed, mujoco.mjtObj.mjOBJ_JOINT, i)
        for i in range(fixed.njnt)
    ]
    return {
        "fixed_candidate_counts": {
            "nbody": int(fixed.nbody),
            "njnt": int(fixed.njnt),
            "nu": int(fixed.nu),
            "ngeom": int(fixed.ngeom),
            "nmesh": int(fixed.nmesh),
        },
        "fixed_candidate_actuators": fixed_actuators,
        "fixed_candidate_joints": fixed_joints,
    }


def main() -> int:
    if not SOURCE_SCENE.exists():
        raise FileNotFoundError(f"Run build_motor_bay_fixed_v0_candidate.py first: {SOURCE_SCENE}")
    bbox = stl_bbox(MESH_PATH)
    distal_z_m = float(bbox["max"][2])
    baseline = compare_to_fixed_candidate()
    variants = []
    for variant in VARIANTS:
        scene = build_variant(variant, distal_z_m)
        inspected = inspect_variant(variant, scene)
        inspected["hand_local_pos"] = [0.0, 0.0, distal_z_m]
        variants.append(inspected)

    for item in variants:
        item["joint_count_unchanged_from_fixed_candidate"] = (
            item["model_summary"]["njnt"] == baseline["fixed_candidate_counts"]["njnt"]
        )
        item["action_dim_unchanged_from_fixed_candidate"] = (
            item["model_summary"]["nu"] == baseline["fixed_candidate_counts"]["nu"]
        )
        item["gate"] = (
            "PASS"
            if item["finite_initial"]
            and item["finite_after_step"]
            and item["hand_proxy_delta_norm_m"] is not None
            and item["hand_proxy_delta_norm_m"] < 1e-9
            and item["render_error"] is None
            and not any(item["blank_flags"].values())
            else "PARTIAL"
        )

    payload = {
        "generated_at": now(),
        "status": "PASS" if all(item["gate"] == "PASS" for item in variants) else "PARTIAL",
        "source_scene": SOURCE_SCENE,
        "motor_bay_stl_bbox": bbox,
        "proxy_assumption": {
            "status": "needs_user_confirmation",
            "description": "Use motor bay STL local +Z distal end as a temporary hand-side frame.",
            "distal_z_m": distal_z_m,
        },
        "baseline": baseline["fixed_candidate_counts"],
        "variants": variants,
        "recommended_first_visual_review": "keep_current_hand_clock",
    }
    META_OUT.parent.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Motor Bay Hand Insert Proxy V0 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Source scene: `{SOURCE_SCENE}`\n",
        "- Scope: diagnostic hand insertion only; no final mechanical truth claim.\n",
        f"- Proxy hand-side frame: motor bay STL local `+Z` distal end at `{distal_z_m:.12g}` m\n",
        "- Parent chain: `ee_mount -> motor_bay_link -> hand_base_link`\n",
        "- Motor bay collision remains disabled.\n\n",
        "## Variants\n\n",
    ]
    for item in variants:
        lines.extend(
            [
                f"### {Path(item['scene']).stem}\n\n",
                f"- Gate: `{item['gate']}`\n",
                f"- Scene: `{item['scene']}`\n",
                f"- Meaning: {item['meaning']}\n",
                f"- Hand local pos: `{fmt(item['hand_local_pos'])}`\n",
                f"- Hand local quat: `{item['hand_local_quat']}`\n",
                f"- Hand/proxy delta: `{item['hand_proxy_delta_norm_m']:.12g}` m\n",
                f"- Model summary: `nbody={item['model_summary']['nbody']}`, "
                f"`njnt={item['model_summary']['njnt']}`, "
                f"`nu={item['model_summary']['nu']}`, "
                f"`ngeom={item['model_summary']['ngeom']}`, "
                f"`nmesh={item['model_summary']['nmesh']}`\n",
                "- Screenshots:\n",
            ]
        )
        if item["render_error"]:
            lines.append(f"  - Render error: `{item['render_error']}`\n")
        else:
            for shot_name, shot in item["screenshots"].items():
                lines.append(f"  - `{shot_name}`: `{shot['file']}`\n")
        lines.append("\n")
    lines.extend(
        [
            "## Notes\n\n",
            "- Both variants keep the same joint names and action dimension as the fixed motor-bay candidate.\n",
            "- This uses a proxy distal frame because SolidWorks has not exported `motor_bay_wrist_mount_csys` yet.\n",
            "- If neither visual variant matches the real assembly, export/provide `motor_bay_wrist_mount_csys` from SolidWorks.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")

    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")
    for item in variants:
        print(f"{item['gate']}: {item['scene']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
