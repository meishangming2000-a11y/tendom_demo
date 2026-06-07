#!/usr/bin/env python3
"""Compare perception-derived and ground-truth hand-relative egg poses."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from mujoco_egg_pose_sensor import (
    DEFAULT_SCENE,
    EggPoseSensorConfig,
    MujocoEggPoseSensor,
    json_ready,
    write_json,
)
from mujoco_hand_relative_pose import compute_hand_object_relative_pose, compare_relative_pose


SENSOR_ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = SENSOR_ROOT / "reports" / "stage3_hand_relative_perception_v0.md"
DEFAULT_METADATA = SENSOR_ROOT / "metadata" / "stage3_hand_relative_perception_v0.json"
DEFAULT_VISUAL_DIR = SENSOR_ROOT / "visual_checks" / "stage3_hand_relative_perception_v0"
EGG_BODY = "egg"
EGG_JOINT = "egg_freejoint"
DEFAULT_EGG_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)


PRESHAPE_TARGETS = {
    "index_mcp_flex_joint": -0.035,
    "middle_mcp_flex_joint": -0.035,
    "ring_mcp_flex_joint": -0.020,
    "little_mcp_flex_joint": -0.015,
    "index_mcp_abd_joint": -0.34,
    "middle_mcp_abd_joint": -0.38,
    "ring_mcp_abd_joint": -0.20,
    "little_mcp_abd_joint": -0.15,
    "index_pip_joint": -0.48,
    "middle_pip_joint": -0.52,
    "ring_pip_joint": -0.20,
    "little_pip_joint": -0.16,
    "index_dip_joint": -0.22,
    "middle_dip_joint": -0.24,
    "ring_dip_joint": -0.10,
    "little_dip_joint": -0.08,
}

LONG_FINGER_TARGETS = {
    "index_mcp_flex_joint": -0.06,
    "middle_mcp_flex_joint": -0.06,
    "ring_mcp_flex_joint": -0.05,
    "little_mcp_flex_joint": -0.04,
    "index_mcp_abd_joint": -0.58,
    "middle_mcp_abd_joint": -0.64,
    "ring_mcp_abd_joint": -0.62,
    "little_mcp_abd_joint": -0.54,
    "index_pip_joint": -0.82,
    "middle_pip_joint": -0.88,
    "ring_pip_joint": -0.84,
    "little_pip_joint": -0.76,
    "index_dip_joint": -0.42,
    "middle_dip_joint": -0.46,
    "ring_dip_joint": -0.44,
    "little_dip_joint": -0.40,
}

THUMB_SMOKE_TARGETS = {
    "thumb_cmc_abd_joint": -0.30,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}


def actuator_to_joint_name(actuator_name: str) -> str:
    if actuator_name.startswith("a_"):
        return actuator_name[2:]
    if actuator_name.endswith("_pos"):
        return actuator_name[:-4]
    return actuator_name


def joint_qadr(model, mujoco, joint_name: str) -> int:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        raise KeyError(f"Unknown joint: {joint_name}")
    return int(model.jnt_qposadr[joint_id])


def set_freejoint_pose(model, data, mujoco, joint_name: str, position: np.ndarray, quat: np.ndarray) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        raise ValueError(f"Unknown freejoint: {joint_name!r}")
    qadr = int(model.jnt_qposadr[joint_id])
    dadr = int(model.jnt_dofadr[joint_id])
    data.qpos[qadr : qadr + 3] = np.asarray(position, dtype=np.float64).reshape(3)
    data.qpos[qadr + 3 : qadr + 7] = np.asarray(quat, dtype=np.float64).reshape(4)
    data.qvel[dadr : dadr + 6] = 0.0


def apply_joint_targets(model, data, mujoco, targets: dict[str, float]) -> None:
    actuator_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) or f"actuator_{idx}"
        for idx in range(model.nu)
    ]
    for joint_name, value in targets.items():
        data.qpos[joint_qadr(model, mujoco, joint_name)] = float(value)
    for aid, actuator_name in enumerate(actuator_names):
        joint_name = actuator_to_joint_name(actuator_name)
        if joint_name not in targets:
            continue
        value = float(targets[joint_name])
        if bool(model.actuator_ctrllimited[aid]):
            low, high = model.actuator_ctrlrange[aid]
            value = float(np.clip(value, low, high))
        data.ctrl[aid] = value


def reset_state(model, data) -> None:
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0


def hand_pose_targets() -> dict[str, dict[str, float]]:
    close_preview = {**PRESHAPE_TARGETS, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}
    return {
        "open_default": {},
        "preshape_hand": dict(PRESHAPE_TARGETS),
        "close_preview_hand": close_preview,
    }


def pose_offsets() -> list[tuple[str, np.ndarray]]:
    return [
        ("center", np.array([0.0, 0.0, 0.0], dtype=np.float64)),
        ("left_low", np.array([-0.020, -0.015, 0.0], dtype=np.float64)),
        ("right_high", np.array([0.020, 0.015, 0.0], dtype=np.float64)),
        ("lifted_center", np.array([0.0, 0.0, 0.015], dtype=np.float64)),
        ("lifted_diag", np.array([0.014, -0.010, 0.012], dtype=np.float64)),
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test Stage3 egg perception integrated with hand FK anchors.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--max-relative-error-m", type=float, default=0.002)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--debug-first-per-hand", action=argparse.BooleanOptionalAction, default=True)
    return parser


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in rows if row["status"] == "ok"]
    if not ok:
        return {"samples": 0, "status": "failed", "reason": "no_ok_samples"}
    egg_errors = np.asarray([row["egg_position_error_m"] for row in ok], dtype=np.float64)
    palm_errors = np.asarray([row["relative_errors"]["palm_frame_object_error_m"] for row in ok], dtype=np.float64)
    tip_errors = np.asarray([row["relative_errors"]["max_tip_vector_error_m"] for row in ok], dtype=np.float64)
    return {
        "samples": int(len(ok)),
        "status": "ok",
        "max_egg_position_error_m": float(np.max(egg_errors)),
        "mean_egg_position_error_m": float(np.mean(egg_errors)),
        "max_palm_frame_error_m": float(np.max(palm_errors)),
        "mean_palm_frame_error_m": float(np.mean(palm_errors)),
        "max_tip_vector_error_m": float(np.max(tip_errors)),
        "mean_tip_vector_error_m": float(np.mean(tip_errors)),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Stage3 Hand-Relative Perception Test V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This test integrates the MuJoCo egg pose sensor with the mechanical hand anchors. The perception path uses image-derived egg position plus hand qpos/FK. The ground-truth path uses MuJoCo egg position plus the same hand qpos/FK. Ground truth is used only for comparison.\n\n",
        "## Inputs\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Perception camera: `{payload['camera']}`\n",
        f"- Resolution: `{payload['resolution'][0]} x {payload['resolution'][1]}`\n",
        f"- Hand poses: `{payload['hand_pose_names']}`\n",
        f"- Egg pose samples per hand pose: `{payload['egg_samples_per_hand']}`\n",
        f"- Max relative error threshold: `{payload['thresholds']['max_relative_error_m']:.6f} m`\n\n",
        "## Result\n\n",
        f"- Overall status: `{payload['overall_status']}`\n",
        f"- Max egg position error: `{payload['summary']['max_egg_position_error_m']:.8f} m`\n",
        f"- Max object-in-palm-frame error: `{payload['summary']['max_palm_frame_error_m']:.8f} m`\n",
        f"- Max fingertip vector error: `{payload['summary']['max_tip_vector_error_m']:.8f} m`\n\n",
        "## Per Hand Pose Summary\n\n",
        "| hand pose | samples | max egg error m | max palm-frame error m | max fingertip-vector error m |\n",
        "|---|---:|---:|---:|---:|\n",
    ]
    for hand_pose, summary in payload["summary_by_hand_pose"].items():
        if summary.get("status") != "ok":
            lines.append(f"| {hand_pose} | 0 | - | - | - |\n")
            continue
        lines.append(
            f"| {hand_pose} | {summary['samples']} | {summary['max_egg_position_error_m']:.8f} | "
            f"{summary['max_palm_frame_error_m']:.8f} | {summary['max_tip_vector_error_m']:.8f} |\n"
        )
    lines.extend(
        [
            "\n## Per-Sample Results\n\n",
            "| hand pose | egg sample | egg error m | palm-frame error m | max fingertip-vector error m | mask pixels | confidence |\n",
            "|---|---|---:|---:|---:|---:|---:|\n",
        ]
    )
    for row in payload["results"]:
        if row["status"] != "ok":
            lines.append(
                f"| {row['hand_pose']} | {row['egg_sample']} | fail | fail | fail | "
                f"{row.get('mask_pixels', 0)} | {row.get('confidence', 0.0):.3f} |\n"
            )
            continue
        rel = row["relative_errors"]
        lines.append(
            f"| {row['hand_pose']} | {row['egg_sample']} | {row['egg_position_error_m']:.8f} | "
            f"{rel['palm_frame_object_error_m']:.8f} | {rel['max_tip_vector_error_m']:.8f} | "
            f"{row['mask_pixels']} | {row['confidence']:.3f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- PASS means the image-derived egg position can be combined with mechanical-hand FK to reproduce the hand-relative pose that would be obtained from direct ground truth.\n",
            "- The current test still uses clean MuJoCo segmentation and a fixed perception camera.\n",
            "- The next risk to test is occlusion during actual approach/contact phases.\n\n",
            f"Metadata: `{payload['metadata']}`\n",
            f"Visual checks: `{payload['visual_dir']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    egg_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, EGG_BODY)
    if egg_body_id < 0:
        raise ValueError(f"Unknown egg body: {EGG_BODY!r}")
    base_position = data.xpos[egg_body_id].copy()
    sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )

    hand_targets = hand_pose_targets()
    results: list[dict[str, Any]] = []
    for hand_pose_name, targets in hand_targets.items():
        for sample_idx, (sample_name, offset) in enumerate(pose_offsets()):
            reset_state(model, data)
            apply_joint_targets(model, data, mujoco, targets)
            set_freejoint_pose(model, data, mujoco, EGG_JOINT, base_position + offset, DEFAULT_EGG_QUAT)
            mujoco.mj_forward(model, data)
            gt_egg_position = data.xpos[egg_body_id].copy()

            debug_dir = None
            if args.debug_first_per_hand and sample_idx == 0:
                debug_dir = visual_dir / hand_pose_name
            estimate = sensor.estimate(data, debug_dir=debug_dir, label=f"{hand_pose_name}_{sample_name}")
            row: dict[str, Any] = {
                "hand_pose": hand_pose_name,
                "egg_sample": sample_name,
                "status": estimate["status"],
                "gt_egg_position_world": gt_egg_position,
            }
            row.update(estimate)
            if estimate["status"] == "ok":
                est_egg_position = np.asarray(estimate["position_world_est"], dtype=np.float64)
                estimated_relative = compute_hand_object_relative_pose(model, data, mujoco, est_egg_position)
                gt_relative = compute_hand_object_relative_pose(model, data, mujoco, gt_egg_position)
                row["egg_position_error_m"] = float(np.linalg.norm(est_egg_position - gt_egg_position))
                row["egg_position_error_xyz_m"] = est_egg_position - gt_egg_position
                row["estimated_relative"] = estimated_relative
                row["ground_truth_relative"] = gt_relative
                row["relative_errors"] = compare_relative_pose(estimated_relative, gt_relative)
            results.append(row)

    summary = summarize(results)
    summary_by_hand_pose = {
        hand_pose_name: summarize([row for row in results if row["hand_pose"] == hand_pose_name])
        for hand_pose_name in hand_targets
    }
    all_ok = len([row for row in results if row["status"] == "ok"]) == len(results)
    max_rel_error = max(
        summary.get("max_palm_frame_error_m", float("inf")),
        summary.get("max_tip_vector_error_m", float("inf")),
    )
    pass_gate = all_ok and max_rel_error <= float(args.max_relative_error_m)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "camera": str(args.camera),
        "resolution": [int(args.width), int(args.height)],
        "thresholds": {"max_relative_error_m": float(args.max_relative_error_m)},
        "hand_pose_names": list(hand_targets.keys()),
        "egg_samples_per_hand": len(pose_offsets()),
        "results": results,
        "summary": summary,
        "summary_by_hand_pose": summary_by_hand_pose,
        "overall_status": "PASS" if pass_gate else "FAIL",
        "metadata": str(metadata),
        "visual_dir": str(visual_dir),
    }
    write_json(metadata, payload)
    report_payload = json.loads(json.dumps(json_ready(payload)))
    write_report(report, report_payload)
    print(f"Overall status: {payload['overall_status']}")
    print(f"Max palm-frame error m: {summary.get('max_palm_frame_error_m', float('inf')):.8f}")
    print(f"Max fingertip-vector error m: {summary.get('max_tip_vector_error_m', float('inf')):.8f}")
    print(f"Report: {report}")
    print(f"Metadata: {metadata}")
    print(f"Visual checks: {visual_dir}")


if __name__ == "__main__":
    main()
