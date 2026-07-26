#!/usr/bin/env python3
"""Build a v2 body-connected scene with explicit orientation corrections.

This is an experiment branch only. It does not edit CAD, STL, URDF, or the
previous body-connected scene. The corrections come from visual review:

- stand the body mesh up by rotating the imported body visual +90 deg about X;
- flip the arm root 180 deg about the mount Z axis.
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_proxy.xml"
OUT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v2.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_corrected_v2"
REPORT = DOCS / "body_connection_orientation_corrected_v2_report.md"
META = ROOT / "metadata" / "body_connection_orientation_corrected_v2.json"

BODY_VISUAL_NAME = "rough_body_support_link_visual"
BODY_PROXY_NAME = "rough_body_support_collision_proxy_bbox_disabled"
ARM_ROOT_NAME = "base_link"

# MuJoCo quaternions are w x y z.
BODY_STAND_QUAT = np.array([math.sqrt(0.5), math.sqrt(0.5), 0.0, 0.0], dtype=np.float64)
ARM_FLIP_QUAT = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)


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


def quat_rotate(quat: np.ndarray, vec: np.ndarray) -> np.ndarray:
    w, x, y, z = quat
    qv = np.array([x, y, z], dtype=np.float64)
    return vec + 2.0 * np.cross(qv, np.cross(qv, vec) + w * vec)


def find_required(root: ET.Element, path: str, *, label: str) -> ET.Element:
    item = root.find(path)
    if item is None:
        raise RuntimeError(f"Missing {label}: {path}")
    return item


def build_scene() -> dict[str, Any]:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", "export4_connected_to_body_corrected_v2")

    body_visual = find_required(root, f".//geom[@name='{BODY_VISUAL_NAME}']", label=BODY_VISUAL_NAME)
    body_visual.set("quat", fmt_vec(BODY_STAND_QUAT))

    body_proxy = root.find(f".//geom[@name='{BODY_PROXY_NAME}']")
    original_proxy_pos = None
    corrected_proxy_pos = None
    if body_proxy is not None:
        original_proxy_pos = np.fromstring(body_proxy.get("pos", "0 0 0"), sep=" ")
        corrected_proxy_pos = quat_rotate(BODY_STAND_QUAT, original_proxy_pos)
        body_proxy.set("pos", fmt_vec(corrected_proxy_pos))
        body_proxy.set("quat", fmt_vec(BODY_STAND_QUAT))

    arm_root = find_required(root, f".//body[@name='{ARM_ROOT_NAME}']", label=ARM_ROOT_NAME)
    arm_root.set("quat", fmt_vec(ARM_FLIP_QUAT))

    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    OUT_SCENE.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUT_SCENE, encoding="utf-8", xml_declaration=True)

    return {
        "source_scene": SOURCE_SCENE,
        "output_scene": OUT_SCENE,
        "body_visual_name": BODY_VISUAL_NAME,
        "body_stand_rotation": {
            "axis": "+X",
            "angle_deg": 90,
            "quat_wxyz": BODY_STAND_QUAT,
            "reason": "Imported body appears horizontal; rotate exported Y length toward world Z.",
        },
        "arm_root_name": ARM_ROOT_NAME,
        "arm_flip_rotation": {
            "axis": "+Z at body mount",
            "angle_deg": 180,
            "quat_wxyz": ARM_FLIP_QUAT,
            "reason": "Visual review indicates arm is mounted on the wrong side and penetrates body.",
        },
        "body_proxy_adjustment": {
            "proxy_name": BODY_PROXY_NAME,
            "original_pos": original_proxy_pos,
            "corrected_pos": corrected_proxy_pos,
            "contact_enabled": False,
        },
        "status": "needs_user_visual_confirmation",
    }


def body_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


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


def actuator_for_joint(model: mujoco.MjModel, joint_name: str) -> int:
    for aid in range(model.nu):
        if model.actuator_trntype[aid] != mujoco.mjtTrn.mjTRN_JOINT:
            continue
        jid = int(model.actuator_trnid[aid, 0])
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        if name == joint_name:
            return aid
    return -1


def run_checks(payload: dict[str, Any]) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    body = body_pos(model, data, "rough_body_support_link")
    base = body_pos(model, data, "base_link")
    palm = body_pos(model, data, "palm_link")
    ball = body_pos(model, data, "ball")
    pts = [p for p in (body, base, palm, ball) if p is not None]
    full_center = np.mean(np.asarray(pts), axis=0)
    mount_center = base if base is not None else full_center
    hand_center = np.mean(np.asarray([p for p in (palm, ball) if p is not None]), axis=0)

    shots = {
        "corrected_full_front": render(model, data, VIS / "corrected_full_front.png", full_center, distance=0.95, azimuth=205, elevation=-22),
        "corrected_full_side": render(model, data, VIS / "corrected_full_side.png", full_center, distance=0.95, azimuth=110, elevation=-18),
        "corrected_mount_closeup": render(model, data, VIS / "corrected_mount_closeup.png", mount_center, distance=0.30, azimuth=205, elevation=-12),
        "corrected_hand_body_alignment": render(model, data, VIS / "corrected_hand_body_alignment.png", hand_center, distance=0.62, azimuth=205, elevation=-20),
    }

    start_body = body.copy() if body is not None else None
    start_base = base.copy() if base is not None else None
    start_palm = palm.copy() if palm is not None else None
    for joint_name, target in [("j1", 0.05), ("j2", -0.05), ("wrist_1_joint", 0.10), ("index_pip_joint", -0.25)]:
        aid = actuator_for_joint(model, joint_name)
        if aid >= 0:
            data.ctrl[aid] = target
    for _ in range(120):
        mujoco.mj_step(model, data)

    after_body = body_pos(model, data, "rough_body_support_link")
    after_base = body_pos(model, data, "base_link")
    after_palm = body_pos(model, data, "palm_link")
    body_drift = float(np.linalg.norm(after_body - start_body)) if start_body is not None and after_body is not None else None
    base_drift = float(np.linalg.norm(after_base - start_base)) if start_base is not None and after_base is not None else None
    palm_motion = float(np.linalg.norm(after_palm - start_palm)) if start_palm is not None and after_palm is not None else None
    blank_flags = {name: (shot["max_pixel"] - shot["min_pixel"] < 5) for name, shot in shots.items()}

    payload.update(
        {
            "generated_at": now(),
            "model_summary": {
                "nbody": int(model.nbody),
                "njnt": int(model.njnt),
                "nu": int(model.nu),
                "ngeom": int(model.ngeom),
                "nmesh": int(model.nmesh),
            },
            "load_ok": True,
            "finite_after_step": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
            "body_drift_m": body_drift,
            "base_link_drift_m": base_drift,
            "palm_motion_m": palm_motion,
            "screenshots": shots,
            "blank_flags": blank_flags,
        }
    )
    return payload


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    load_gate = payload["load_ok"] and payload["finite_after_step"] and not any(payload["blank_flags"].values())
    lines = [
        "# Body Connection Orientation Corrected V2 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Corrected scene: `{payload['output_scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Load/finite/render gate: `{'PASS' if load_gate else 'FAIL'}`\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Body drift after command: `{payload['body_drift_m']}` m\n",
        f"- Base link drift after command: `{payload['base_link_drift_m']}` m\n",
        f"- Palm motion after command: `{payload['palm_motion_m']}` m\n\n",
        "## Corrections\n\n",
        f"- Body visual `{BODY_VISUAL_NAME}`: +90 deg about X, quat `{fmt_vec(BODY_STAND_QUAT)}`.\n",
        f"- Arm root `{ARM_ROOT_NAME}`: 180 deg about mount Z, quat `{fmt_vec(ARM_FLIP_QUAT)}`.\n",
        "- Body collision proxy remains contact-disabled; this is still visual/load/motion only.\n\n",
        "## Screenshots\n\n",
    ]
    for name, shot in payload["screenshots"].items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This v2 scene encodes the user's visual diagnosis that the body was lying down and the arm root was mounted backwards.\n",
            "- The corrected scene is an experiment branch; the final SolidWorks `body_arm_mount_csys` axes should still be updated or confirmed upstream.\n",
            "- If the v2 render looks correct, mirror these frame corrections back into the CAD/export mount frame rather than baking more guessed offsets into MuJoCo.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_scene()
    payload = run_checks(payload)
    write_outputs(payload)
    print(f"Saved scene: {OUT_SCENE}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    for name, shot in payload["screenshots"].items():
        print(f"{name}: {shot['file']}")


if __name__ == "__main__":
    main()
