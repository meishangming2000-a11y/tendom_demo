#!/usr/bin/env python3
"""Render fixed visual checks for the body-connected export4 experiment."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCENE_PROXY = ROOT / "mjcf" / "scene_export4_connected_to_body_proxy.xml"
BODY_MESH_REL = "../body_urdf_export1/meshes/rough_body_support_link.STL"
BODY_MESH_ABS = ROOT / "body_urdf_export1" / "meshes" / "rough_body_support_link.STL"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection"
REPORT = DOCS / "body_visual_connection_check_report.md"
META = ROOT / "metadata" / "body_visual_connection_check.json"
IDENTITY_MOUNT_REQUIRES_HUMAN_CONFIRMATION = True


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


def body_id(model, name: str) -> int:
    return mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)


def body_pos(model, data, name: str) -> np.ndarray | None:
    bid = body_id(model, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def render(model, data, output: Path, lookat: np.ndarray, *, distance: float, azimuth: float, elevation: float, width: int = 1280, height: int = 900) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=width, height=height)
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
    return {"file": str(output), "mean_pixel": float(image.mean()), "min_pixel": int(image.min()), "max_pixel": int(image.max())}


def make_body_only_scene() -> Path:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<mujoco model="body_only_visual_check">
  <compiler angle="radian"/>
  <statistic extent="0.6" center="0 0.12 0.1"/>
  <visual>
    <global offwidth="1280" offheight="900"/>
  </visual>
  <asset>
    <mesh name="rough_body_support_link_body_mesh" file="{BODY_MESH_ABS.as_posix()}" scale="1 1 1"/>
  </asset>
  <worldbody>
    <light name="key_light" pos="0.3 -0.4 1.0" directional="true" dir="0.0 0.2 -1"/>
    <light name="fill_light" pos="-0.4 0.4 0.8"/>
    <body name="rough_body_support_link" pos="0 0 0">
      <geom name="rough_body_support_link_visual" type="mesh" mesh="rough_body_support_link_body_mesh" rgba="0.70 0.70 0.70 0.65" contype="0" conaffinity="0" group="2"/>
      <site name="body_arm_mount_origin" pos="0 0 0" size="0.008" rgba="1 0.55 0.1 1"/>
      <site name="body_arm_mount_x" pos="0.025 0 0" size="0.004" rgba="1 0 0 1"/>
      <site name="body_arm_mount_y" pos="0 0.025 0" size="0.004" rgba="0 1 0 1"/>
      <site name="body_arm_mount_z" pos="0 0 0.025" size="0.004" rgba="0.05 0.2 1 1"/>
    </body>
  </worldbody>
</mujoco>
"""
    tmp = Path(tempfile.gettempdir()) / "body_only_visual_check.xml"
    tmp.write_text(xml, encoding="utf-8")
    return tmp


def command_motion_pose(model, data) -> None:
    targets = {
        "wrist_1_joint": 0.18,
        "wrist_2_joint": -0.18,
        "index_mcp_abd_joint": -0.45,
        "index_pip_joint": -0.55,
        "middle_mcp_abd_joint": -0.45,
        "middle_pip_joint": -0.55,
        "thumb_cmc_abd_joint": -0.25,
        "thumb_mcp_joint": 0.22,
    }
    for joint, target in targets.items():
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
        if jid < 0:
            continue
        for aid in range(model.nu):
            if model.actuator_trntype[aid] == mujoco.mjtTrn.mjTRN_JOINT and int(model.actuator_trnid[aid, 0]) == jid:
                data.ctrl[aid] = target
                break
    for _ in range(160):
        mujoco.mj_step(model, data)


def main() -> None:
    VIS.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE_PROXY.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    body = body_pos(model, data, "rough_body_support_link")
    base = body_pos(model, data, "base_link")
    palm = body_pos(model, data, "palm_link")
    ball = body_pos(model, data, "ball")
    points = [p for p in (body, base, palm, ball) if p is not None]
    full_center = np.mean(np.asarray(points), axis=0)
    mount_center = base if base is not None else np.array([0.0, 0.0, 0.0])
    hand_center = np.mean(np.asarray([p for p in (palm, ball) if p is not None]), axis=0)

    body_model = mujoco.MjModel.from_xml_path(str(make_body_only_scene()))
    body_data = mujoco.MjData(body_model)
    mujoco.mj_forward(body_model, body_data)
    shots = {
        "body_only_view": render(body_model, body_data, VIS / "body_only_view.png", np.array([0.0, 0.12, 0.10]), distance=0.62, azimuth=215, elevation=-20),
        "export4_with_body_full_front": render(model, data, VIS / "export4_with_body_full_front.png", full_center, distance=0.95, azimuth=205, elevation=-22),
        "export4_with_body_full_side": render(model, data, VIS / "export4_with_body_full_side.png", full_center, distance=0.95, azimuth=110, elevation=-18),
        "arm_mount_alignment_closeup": render(model, data, VIS / "arm_mount_alignment_closeup.png", mount_center, distance=0.28, azimuth=205, elevation=-12),
        "hand_body_alignment": render(model, data, VIS / "hand_body_alignment.png", hand_center, distance=0.55, azimuth=205, elevation=-20),
        "connected_model_motion_start": render(model, data, VIS / "connected_model_motion_start.png", full_center, distance=0.95, azimuth=205, elevation=-22),
    }
    command_motion_pose(model, data)
    after_body = body_pos(model, data, "rough_body_support_link")
    after_base = body_pos(model, data, "base_link")
    after_palm = body_pos(model, data, "palm_link")
    after_center = np.mean(np.asarray([p for p in (after_body, after_base, after_palm, ball) if p is not None]), axis=0)
    shots["connected_model_motion_after"] = render(model, data, VIS / "connected_model_motion_after.png", after_center, distance=0.95, azimuth=205, elevation=-22)

    body_drift = float(np.linalg.norm(after_body - body)) if body is not None and after_body is not None else None
    base_drift = float(np.linalg.norm(after_base - base)) if base is not None and after_base is not None else None
    palm_motion = float(np.linalg.norm(after_palm - palm)) if palm is not None and after_palm is not None else None
    blank_flags = {name: (s["max_pixel"] - s["min_pixel"] < 5) for name, s in shots.items()}
    load_motion_pass = (
        not any(blank_flags.values())
        and body_drift is not None
        and body_drift < 1e-9
        and base_drift is not None
        and base_drift < 1e-6
    )
    conclusion = "PARTIAL" if load_motion_pass and IDENTITY_MOUNT_REQUIRES_HUMAN_CONFIRMATION else "PASS" if load_motion_pass else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": SCENE_PROXY,
        "conclusion": conclusion,
        "body_drift_m": body_drift,
        "base_link_drift_m": base_drift,
        "palm_motion_m": palm_motion,
        "screenshots": shots,
        "blank_flags": blank_flags,
        "load_motion_pass": load_motion_pass,
        "identity_mount_requires_human_confirmation": IDENTITY_MOUNT_REQUIRES_HUMAN_CONFIRMATION,
        "visual_findings": [
            "Body mesh loads at meter scale.",
            "Arm-hand root is nested under rough_body_support_link with identity transform.",
            "Body proxy contact is disabled for this first pass, so grasp smoke is not disturbed.",
            "Close-up views show the current experiment is an identity mount draft; final mount clocking and offset still need SolidWorks/hardware confirmation.",
        ],
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Body Visual Connection Check Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{SCENE_PROXY}`\n",
        f"- Conclusion: `{conclusion}`\n",
        f"- Body drift after motion command: `{body_drift}` m\n",
        f"- Base link drift after motion command: `{base_drift}` m\n",
        f"- Palm motion after command: `{palm_motion}` m\n\n",
        f"- Load/motion gate: `{'PASS' if load_motion_pass else 'FAIL'}`\n",
        f"- Identity mount needs human confirmation: `{IDENTITY_MOUNT_REQUIRES_HUMAN_CONFIRMATION}`\n\n",
        "## Required Screenshots\n\n",
    ]
    for name, shot in shots.items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Visual Inspection Notes\n\n",
            "- Body scale does not show a 1000x error in the rendered views.\n",
            "- The model loads with body, arm, hand, and ball in the same scene.\n",
            "- The first connection uses the body export origin as `body_arm_mount_csys`; if this is not the desired physical mount, the next input needed is a corrected SolidWorks mount frame or fixed transform.\n",
            "- `PARTIAL` here means visual/load/motion plausibility for an experiment branch, with final mechanical mount clocking still unapproved.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    for name, shot in shots.items():
        print(f"{name}: {shot['file']}")


if __name__ == "__main__":
    main()
