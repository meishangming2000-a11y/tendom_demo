#!/usr/bin/env python3
"""Smoke-test joints around the inserted motor bay candidate.

Checks:
- wrist_1_joint / wrist_2_joint: palm/wrist motion relative to motor_bay_link.
- j4: ee_mount-to-arm-end motion carrying motor_bay_link and hand with it.

This script does not modify the MJCF scene.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "mjcf" / "scene_export4_with_motor_bay_hand_insert_proxy_keep_clock_v0.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_motor_bay_joint_motion_smoke_v0"
REPORT = DOCS / "motor_bay_joint_motion_smoke_v0_report.md"
META_OUT = META / "motor_bay_joint_motion_smoke_v0.json"

WRIST_JOINTS = ["wrist_1_joint", "wrist_2_joint"]
ARM_END_JOINT = "j4"
TRACK_BODIES = [
    "link_3",
    "ee_mount",
    "motor_bay_link",
    "hand_base_link",
    "wrist_middle_link",
    "palm_link",
]

TESTS = [
    {
        "name": "neutral",
        "targets": {},
        "kind": "neutral",
        "description": "Neutral hold pose.",
    },
    {
        "name": "wrist_1_pos",
        "targets": {"wrist_1_joint": 0.45},
        "kind": "wrist",
        "description": "Positive wrist_1 motion between hand_base_link and wrist_middle_link.",
    },
    {
        "name": "wrist_1_neg",
        "targets": {"wrist_1_joint": -0.45},
        "kind": "wrist",
        "description": "Negative wrist_1 motion between hand_base_link and wrist_middle_link.",
    },
    {
        "name": "wrist_2_pos",
        "targets": {"wrist_2_joint": 0.45},
        "kind": "wrist",
        "description": "Positive wrist_2 motion between wrist_middle_link and palm_link.",
    },
    {
        "name": "wrist_2_neg",
        "targets": {"wrist_2_joint": -0.45},
        "kind": "wrist",
        "description": "Negative wrist_2 motion between wrist_middle_link and palm_link.",
    },
    {
        "name": "j4_pos",
        "targets": {"j4": 0.45},
        "kind": "arm_end",
        "description": "Positive arm-end joint motion carrying ee_mount, motor bay, and hand.",
    },
    {
        "name": "j4_neg",
        "targets": {"j4": -0.45},
        "kind": "arm_end",
        "description": "Negative arm-end joint motion carrying ee_mount, motor bay, and hand.",
    },
]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


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


def name(model: mujoco.MjModel, obj_type: mujoco.mjtObj, idx: int) -> str:
    return mujoco.mj_id2name(model, obj_type, idx) or f"<unnamed:{idx}>"


def joint_qpos(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str) -> float | None:
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if jid < 0:
        return None
    return float(data.qpos[model.jnt_qposadr[jid]])


def body_pose(model: mujoco.MjModel, data: mujoco.MjData, body_name: str) -> dict[str, np.ndarray] | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if bid < 0:
        return None
    return {
        "pos": data.xpos[bid].copy(),
        "quat": data.xquat[bid].copy(),
        "mat": data.xmat[bid].reshape(3, 3).copy(),
    }


def body_poses(model: mujoco.MjModel, data: mujoco.MjData) -> dict[str, dict[str, np.ndarray]]:
    poses = {}
    for body_name in TRACK_BODIES:
        pose = body_pose(model, data, body_name)
        if pose is not None:
            poses[body_name] = pose
    return poses


def actuator_joint_map(model: mujoco.MjModel) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for aid in range(model.nu):
        if model.actuator_trntype[aid] != mujoco.mjtTrn.mjTRN_JOINT:
            continue
        jid = int(model.actuator_trnid[aid, 0])
        if jid < 0:
            continue
        mapping[name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)] = aid
    return mapping


def apply_targets(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    targets: dict[str, float],
    mapping: dict[str, int],
) -> None:
    data.ctrl[:] = 0.0
    for joint_name, target in targets.items():
        aid = mapping.get(joint_name)
        if aid is None:
            raise RuntimeError(f"No actuator found for joint `{joint_name}`")
        data.ctrl[aid] = float(target)


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


def reset_data(model: mujoco.MjModel) -> mujoco.MjData:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return data


def run_case(model: mujoco.MjModel, mapping: dict[str, int], case: dict[str, Any]) -> dict[str, Any]:
    data = reset_data(model)
    initial_joints = {
        joint: joint_qpos(model, data, joint)
        for joint in [*WRIST_JOINTS, ARM_END_JOINT]
    }
    initial_poses = body_poses(model, data)

    apply_targets(model, data, case["targets"], mapping)
    for _ in range(450):
        mujoco.mj_step(model, data)

    final_joints = {
        joint: joint_qpos(model, data, joint)
        for joint in [*WRIST_JOINTS, ARM_END_JOINT]
    }
    final_poses = body_poses(model, data)
    joint_deltas = {
        joint: (
            None
            if initial_joints[joint] is None or final_joints[joint] is None
            else final_joints[joint] - initial_joints[joint]
        )
        for joint in initial_joints
    }
    body_displacement = {}
    for body_name, initial in initial_poses.items():
        final = final_poses.get(body_name)
        if final is None:
            continue
        body_displacement[body_name] = float(np.linalg.norm(final["pos"] - initial["pos"]))

    points = [pose["pos"] for pose in final_poses.values()]
    lookat = np.mean(np.asarray(points), axis=0)
    if case["kind"] == "wrist":
        focus = final_poses.get("motor_bay_link", final_poses.get("palm_link"))
        lookat = focus["pos"] if focus is not None else lookat
        distance = 0.58
    elif case["kind"] == "arm_end":
        focus = final_poses.get("ee_mount", final_poses.get("motor_bay_link"))
        lookat = focus["pos"] if focus is not None else lookat
        distance = 0.68
    else:
        distance = 0.82

    shots = {
        "side": render(
            model,
            data,
            VIS / case["name"] / "side.png",
            lookat,
            distance=distance,
            azimuth=110,
            elevation=-12,
        ),
        "top": render(
            model,
            data,
            VIS / case["name"] / "top.png",
            lookat,
            distance=distance,
            azimuth=180,
            elevation=-75,
        ),
    }
    blank_flags = {
        shot_name: shot["max_pixel"] - shot["min_pixel"] < 5
        for shot_name, shot in shots.items()
    }

    if case["kind"] == "wrist":
        target_joint = next(iter(case["targets"]))
        response = abs(joint_deltas[target_joint] or 0.0)
        palm_motion = body_displacement.get("palm_link", 0.0)
        motor_bay_motion = body_displacement.get("motor_bay_link", 0.0)
        pass_check = response > 0.08 and palm_motion > 0.002 and motor_bay_motion < 0.03
    elif case["kind"] == "arm_end":
        response = abs(joint_deltas[ARM_END_JOINT] or 0.0)
        motor_bay_motion = body_displacement.get("motor_bay_link", 0.0)
        hand_motion = body_displacement.get("hand_base_link", 0.0)
        pass_check = response > 0.08 and motor_bay_motion > 0.002 and hand_motion > 0.002
    else:
        pass_check = True

    return {
        "name": case["name"],
        "kind": case["kind"],
        "description": case["description"],
        "targets": case["targets"],
        "finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "initial_joints": initial_joints,
        "final_joints": final_joints,
        "joint_deltas": joint_deltas,
        "body_displacement_m": body_displacement,
        "screenshots": shots,
        "blank_flags": blank_flags,
        "pass_check": bool(pass_check and not any(blank_flags.values())),
    }


def main() -> int:
    model = mujoco.MjModel.from_xml_path(str(SCENE.resolve()))
    mapping = actuator_joint_map(model)
    missing = [joint for joint in [*WRIST_JOINTS, ARM_END_JOINT] if joint not in mapping]
    if missing:
        raise RuntimeError(f"Missing actuator mapping for joints: {missing}")

    cases = [run_case(model, mapping, case) for case in TESTS]
    wrist_cases = [case for case in cases if case["kind"] == "wrist"]
    arm_end_cases = [case for case in cases if case["kind"] == "arm_end"]
    payload = {
        "generated_at": now(),
        "scene": SCENE,
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
        },
        "actuator_joint_map_checked": {
            joint: mapping[joint] for joint in [*WRIST_JOINTS, ARM_END_JOINT]
        },
        "cases": cases,
        "wrist_gate": "PASS" if all(case["pass_check"] for case in wrist_cases) else "FAIL",
        "arm_end_gate": "PASS" if all(case["pass_check"] for case in arm_end_cases) else "FAIL",
    }
    payload["overall_gate"] = (
        "PASS"
        if payload["wrist_gate"] == "PASS" and payload["arm_end_gate"] == "PASS"
        else "FAIL"
    )

    META_OUT.parent.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Motor Bay Joint Motion Smoke V0 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{SCENE}`\n",
        f"- Overall gate: `{payload['overall_gate']}`\n",
        f"- Wrist gate: `{payload['wrist_gate']}`\n",
        f"- Arm-end gate: `{payload['arm_end_gate']}`\n",
        f"- Model summary: `nbody={model.nbody}`, `njnt={model.njnt}`, `nu={model.nu}`, `ngeom={model.ngeom}`\n",
        f"- Checked actuator map: `{payload['actuator_joint_map_checked']}`\n\n",
        "## Cases\n\n",
    ]
    for case in cases:
        lines.extend(
            [
                f"### {case['name']}\n\n",
                f"- Kind: `{case['kind']}`\n",
                f"- Pass: `{case['pass_check']}`\n",
                f"- Targets: `{case['targets']}`\n",
                f"- Joint deltas: `{case['joint_deltas']}`\n",
                f"- Body displacement m: `{case['body_displacement_m']}`\n",
                "- Screenshots:\n",
            ]
        )
        for shot_name, shot in case["screenshots"].items():
            lines.append(f"  - `{shot_name}`: `{shot['file']}`\n")
        lines.append("\n")
    lines.extend(
        [
            "## Interpretation\n\n",
            "- Wrist tests drive `wrist_1_joint` and `wrist_2_joint`; palm/wrist bodies move while the motor bay remains the upstream fixed parent.\n",
            "- Arm-end tests drive `j4`; `ee_mount`, `motor_bay_link`, and the hand move together as expected.\n",
            "- This checks MuJoCo actuator/joint continuity only; final collision tuning remains separate because motor bay collision is still disabled.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")

    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")
    print(f"Overall gate: {payload['overall_gate']}")
    print(f"Wrist gate: {payload['wrist_gate']}")
    print(f"Arm-end gate: {payload['arm_end_gate']}")
    return 0 if payload["overall_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
