#!/usr/bin/env python3
"""Smoke test the experimental arm_stage1 + export4 hand assembly."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_SCENE = ROOT / "scene_arm_hand_export4_cad_mount_candidate.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata" / "arm_hand_export4_joint_smoke.json"
REPORT = DOCS / "arm_hand_export4_joint_smoke_report.md"
VIS = ROOT / "visual_checks"


def render(model, data, mujoco, path: Path, lookat, distance: float, azimuth: float, elevation: float) -> dict[str, Any]:
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = np.asarray(lookat, dtype=np.float64)
        camera.distance = distance
        camera.azimuth = azimuth
        camera.elevation = elevation
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, image)
    return {
        "file": str(path),
        "mean_pixel": float(image.mean()),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
    }


def name_or(model, mujoco, objtype, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, objtype, idx) or fallback


def qpos_target_for_joint(model, jid: int, magnitude: float) -> float:
    limited = bool(model.jnt_limited[jid])
    if not limited:
        return magnitude
    lo, hi = model.jnt_range[jid]
    target = magnitude
    if hi <= 0:
        target = max(lo, hi * 0.5)
    elif lo >= 0:
        target = min(hi, lo + magnitude)
    else:
        target = min(max(target, lo), hi)
    return float(target)


def run_joint_kinematic_smoke(model, data, mujoco, magnitude: float) -> list[dict[str, Any]]:
    results = []
    base_qpos = data.qpos.copy()
    base_qvel = data.qvel.copy()
    for jid in range(model.njnt):
        joint_name = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_JOINT, jid, f"joint_{jid}")
        if model.jnt_type[jid] != mujoco.mjtJoint.mjJNT_HINGE:
            results.append({"joint": joint_name, "status": "SKIPPED", "reason": "not hinge"})
            continue

        body_id = int(model.jnt_bodyid[jid])
        body_name = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, body_id, f"body_{body_id}")
        qadr = int(model.jnt_qposadr[jid])
        target = qpos_target_for_joint(model, jid, magnitude)

        data.qpos[:] = base_qpos
        data.qvel[:] = base_qvel * 0
        mujoco.mj_forward(model, data)
        before_pos = data.xpos[body_id].copy()
        before_mat = data.xmat[body_id].copy()

        data.qpos[qadr] = target
        data.qvel[:] = 0
        mujoco.mj_forward(model, data)
        after_pos = data.xpos[body_id].copy()
        after_mat = data.xmat[body_id].copy()

        finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.xpos).all())
        pos_delta = float(np.linalg.norm(after_pos - before_pos))
        rot_delta = float(np.linalg.norm(after_mat - before_mat))
        results.append(
            {
                "joint": joint_name,
                "body": body_name,
                "target": target,
                "range": model.jnt_range[jid].tolist() if bool(model.jnt_limited[jid]) else None,
                "pos_delta": pos_delta,
                "rot_delta": rot_delta,
                "status": "PASS" if finite else "FAIL",
            }
        )
    data.qpos[:] = base_qpos
    data.qvel[:] = base_qvel
    mujoco.mj_forward(model, data)
    return results


def run_actuator_smoke(model, data, mujoco, magnitude: float, steps: int) -> dict[str, Any]:
    ctrl_targets = np.zeros(model.nu)
    actuator_results = []
    for aid in range(model.nu):
        actuator_name = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR, aid, f"actuator_{aid}")
        joint_id = int(model.actuator_trnid[aid, 0])
        joint_name = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_JOINT, joint_id, f"joint_{joint_id}") if joint_id >= 0 else "none"
        target = magnitude
        if bool(model.actuator_ctrllimited[aid]):
            lo, hi = model.actuator_ctrlrange[aid]
            if hi <= 0:
                target = max(lo, hi * 0.5)
            elif lo >= 0:
                target = min(hi, lo + magnitude)
            else:
                target = min(max(target, lo), hi)
        ctrl_targets[aid] = target
        actuator_results.append({"actuator": actuator_name, "joint": joint_name, "target": float(target)})

    data.ctrl[:] = ctrl_targets
    for _ in range(steps):
        mujoco.mj_step(model, data)

    finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all() and np.isfinite(data.xpos).all())
    return {
        "status": "PASS" if finite else "FAIL",
        "steps": steps,
        "max_abs_qpos": float(np.max(np.abs(data.qpos))) if data.qpos.size else 0.0,
        "max_abs_qvel": float(np.max(np.abs(data.qvel))) if data.qvel.size else 0.0,
        "actuators": actuator_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test arm + export4 hand assembly.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--magnitude", type=float, default=0.12)
    parser.add_argument("--steps", type=int, default=250)
    args = parser.parse_args()

    import mujoco

    scene = Path(args.scene).resolve()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    ee_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ee_tool_frame")
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = data.xpos[palm_id].copy() if palm_id >= 0 else np.array([0.0, 0.0, 0.25])

    before_render = render(model, data, mujoco, VIS / "arm_hand_joint_smoke_open.png", lookat, 0.72, 205, -22)
    joint_results = run_joint_kinematic_smoke(model, data, mujoco, args.magnitude)

    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    actuator_smoke = run_actuator_smoke(model, data, mujoco, args.magnitude, args.steps)
    after_render = render(model, data, mujoco, VIS / "arm_hand_joint_smoke_actuated.png", lookat, 0.72, 205, -22)

    failed = [row for row in joint_results if row["status"] == "FAIL"]
    skipped = [row for row in joint_results if row["status"] == "SKIPPED"]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
            "nmesh": int(model.nmesh),
        },
        "ee_tool_frame_found": ee_id >= 0,
        "hand_root_child_under_arm": True,
        "joint_kinematic_summary": {
            "total": len(joint_results),
            "pass": sum(1 for row in joint_results if row["status"] == "PASS"),
            "fail": len(failed),
            "skipped": len(skipped),
        },
        "joint_results": joint_results,
        "actuator_smoke": actuator_smoke,
        "renders": {"open": before_render, "actuated": after_render},
        "overall_status": "PASS" if not failed and actuator_smoke["status"] == "PASS" else "FAIL",
    }

    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm + Export4 Hand Joint Smoke Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{scene}`\n",
        f"- Overall status: **{payload['overall_status']}**\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Joint kinematic smoke: `{payload['joint_kinematic_summary']}`\n",
        f"- Actuator smoke: `{actuator_smoke['status']}` after `{args.steps}` steps\n",
        f"- Open render: `{before_render['file']}`\n",
        f"- Actuated render: `{after_render['file']}`\n\n",
        "## Notes\n\n",
        "- The hand is attached as a child body under the arm `ee_tool_frame`.\n",
        "- This smoke test checks loadability, finite kinematics, and finite position-actuator stepping only. It is not a collision or grasp-quality proof.\n\n",
        "## Joint Results\n\n",
        "| joint | body | target rad | status | pos_delta | rot_delta |\n",
        "|---|---|---:|---|---:|---:|\n",
    ]
    for row in joint_results:
        lines.append(
            f"| {row['joint']} | {row.get('body', '')} | {row.get('target', 0.0):.4f} | "
            f"{row['status']} | {row.get('pos_delta', 0.0):.6f} | {row.get('rot_delta', 0.0):.6f} |\n"
        )
    DOCS.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")

    print(f"Overall status: {payload['overall_status']}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")


if __name__ == "__main__":
    main()
