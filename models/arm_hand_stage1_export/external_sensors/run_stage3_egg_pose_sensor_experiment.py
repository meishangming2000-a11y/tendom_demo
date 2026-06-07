#!/usr/bin/env python3
"""Run Stage3 egg pose sensor accuracy experiments."""

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


ROOT = Path(__file__).resolve().parents[1]
SENSOR_ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = SENSOR_ROOT / "reports" / "stage3_egg_pose_sensor_accuracy_v0.md"
DEFAULT_METADATA = SENSOR_ROOT / "metadata" / "stage3_egg_pose_sensor_accuracy_v0.json"
DEFAULT_VISUAL_DIR = SENSOR_ROOT / "visual_checks" / "stage3_egg_pose_sensor_accuracy_v0"
EGG_BODY = "egg"
EGG_JOINT = "egg_freejoint"
DEFAULT_EGG_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)


def set_freejoint_pose(model, data, mujoco, joint_name: str, position: np.ndarray, quat: np.ndarray) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        raise ValueError(f"Unknown freejoint: {joint_name!r}")
    qadr = int(model.jnt_qposadr[joint_id])
    dadr = int(model.jnt_dofadr[joint_id])
    data.qpos[qadr : qadr + 3] = np.asarray(position, dtype=np.float64).reshape(3)
    data.qpos[qadr + 3 : qadr + 7] = np.asarray(quat, dtype=np.float64).reshape(4)
    data.qvel[dadr : dadr + 6] = 0.0
    mujoco.mj_forward(model, data)


def default_pose_offsets() -> list[tuple[str, np.ndarray]]:
    rows: list[tuple[str, np.ndarray]] = []
    for dx in (-0.020, 0.0, 0.020):
        for dy in (-0.015, 0.0, 0.015):
            rows.append((f"floor_dx{dx:+.3f}_dy{dy:+.3f}", np.array([dx, dy, 0.0], dtype=np.float64)))
    rows.extend(
        [
            ("lifted_center_z+0.015", np.array([0.0, 0.0, 0.015], dtype=np.float64)),
            ("lifted_diag_z+0.012", np.array([0.014, -0.010, 0.012], dtype=np.float64)),
        ]
    )
    return rows


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate MuJoCo RGB-D egg pose sensor accuracy.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--cameras", nargs="+", default=["stage3_egg_closeup"])
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--max-error-m", type=float, default=0.002)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--debug-every", action=argparse.BooleanOptionalAction, default=True)
    return parser


def summarize_camera(results: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in results if row["status"] == "ok"]
    errors = np.asarray([row["position_error_m"] for row in ok], dtype=np.float64)
    mask_pixels = np.asarray([row["mask_pixels"] for row in ok], dtype=np.float64)
    if errors.size == 0:
        return {"samples": 0, "status": "failed", "reason": "no_ok_samples"}
    return {
        "samples": int(errors.size),
        "status": "ok",
        "mean_error_m": float(np.mean(errors)),
        "max_error_m": float(np.max(errors)),
        "rms_error_m": float(np.sqrt(np.mean(np.square(errors)))),
        "min_mask_pixels": int(np.min(mask_pixels)),
        "mean_mask_pixels": float(np.mean(mask_pixels)),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Stage3 Egg Pose Sensor Accuracy V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This is a MuJoCo-only Stage3.2b perception-geometry experiment. It tests whether an external sensor tool can estimate the egg position from rendered depth and segmentation. MuJoCo ground truth is used only for evaluation.\n\n",
        "## Inputs\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Cameras: `{payload['cameras']}`\n",
        f"- Resolution: `{payload['resolution'][0]} x {payload['resolution'][1]}`\n",
        f"- Max pass error: `{payload['thresholds']['max_error_m']:.6f} m`\n",
        f"- Pose samples: `{len(payload['pose_samples'])}`\n\n",
        "## Result\n\n",
        f"- Overall status: `{payload['overall_status']}`\n",
        f"- Overall max error: `{payload['overall_max_error_m']:.6f} m`\n\n",
        "## Camera Summary\n\n",
        "| camera | samples | mean error m | max error m | rms error m | min mask pixels |\n",
        "|---|---:|---:|---:|---:|---:|\n",
    ]
    for camera, summary in payload["summary_by_camera"].items():
        if summary.get("status") != "ok":
            lines.append(f"| {camera} | 0 | - | - | - | - |\n")
            continue
        lines.append(
            f"| {camera} | {summary['samples']} | {summary['mean_error_m']:.8f} | "
            f"{summary['max_error_m']:.8f} | {summary['rms_error_m']:.8f} | {summary['min_mask_pixels']} |\n"
        )
    lines.extend(
        [
            "\n## Per-Sample Results\n\n",
            "| camera | sample | gt xyz m | estimated xyz m | error m | mask pixels | confidence |\n",
            "|---|---|---|---|---:|---:|---:|\n",
        ]
    )
    for row in payload["results"]:
        if row["status"] != "ok":
            lines.append(
                f"| {row['camera']} | {row['sample']} | `{row.get('gt_position_world', '-')}` | failed | - | "
                f"{row.get('mask_pixels', 0)} | {row.get('confidence', 0.0):.3f} |\n"
            )
            continue
        lines.append(
            f"| {row['camera']} | {row['sample']} | `{np.round(row['gt_position_world'], 6).tolist()}` | "
            f"`{np.round(row['position_world_est'], 6).tolist()}` | {row['position_error_m']:.8f} | "
            f"{row['mask_pixels']} | {row['confidence']:.3f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- PASS here means the geometry sensor can recover egg center position from rendered images for fixed test poses.\n",
            "- This does not yet test fingertip-relative pose, occlusion during grasp, or real camera images.\n",
            "- The next Stage3.2b step is to add palm/fingertip FK and report object-to-hand relative vectors.\n\n",
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

    pose_samples = [
        {"name": name, "offset_xyz": offset, "position_world": base_position + offset}
        for name, offset in default_pose_offsets()
    ]
    results: list[dict[str, Any]] = []

    for camera_name in args.cameras:
        sensor = MujocoEggPoseSensor(
            model,
            mujoco,
            EggPoseSensorConfig(
                camera_name=camera_name,
                width=int(args.width),
                height=int(args.height),
            ),
        )
        for sample in pose_samples:
            set_freejoint_pose(model, data, mujoco, EGG_JOINT, sample["position_world"], DEFAULT_EGG_QUAT)
            gt_position = data.xpos[egg_body_id].copy()
            label = f"{camera_name}_{sample['name']}"
            debug_dir = visual_dir / camera_name if args.debug_every else None
            estimate = sensor.estimate(data, debug_dir=debug_dir, label=label)
            row: dict[str, Any] = {
                "camera": camera_name,
                "sample": sample["name"],
                "status": estimate["status"],
                "gt_position_world": gt_position,
            }
            row.update(estimate)
            if estimate["status"] == "ok":
                est = np.asarray(estimate["position_world_est"], dtype=np.float64)
                row["position_error_m"] = float(np.linalg.norm(est - gt_position))
                row["position_error_xyz_m"] = est - gt_position
            results.append(row)

    summary_by_camera = {
        camera_name: summarize_camera([row for row in results if row["camera"] == camera_name])
        for camera_name in args.cameras
    }
    ok_errors = [row["position_error_m"] for row in results if row["status"] == "ok"]
    overall_max = float(max(ok_errors)) if ok_errors else float("inf")
    all_ok = len(ok_errors) == len(results) and overall_max <= float(args.max_error_m)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "cameras": list(args.cameras),
        "resolution": [int(args.width), int(args.height)],
        "thresholds": {"max_error_m": float(args.max_error_m)},
        "pose_samples": pose_samples,
        "results": results,
        "summary_by_camera": summary_by_camera,
        "overall_max_error_m": overall_max,
        "overall_status": "PASS" if all_ok else "FAIL",
        "metadata": str(metadata),
        "visual_dir": str(visual_dir),
    }
    write_json(metadata, payload)
    write_report(report, json.loads(json.dumps(json_ready(payload))))
    print(f"Overall status: {payload['overall_status']}")
    print(f"Overall max error m: {payload['overall_max_error_m']:.8f}")
    print(f"Report: {report}")
    print(f"Metadata: {metadata}")
    print(f"Visual checks: {visual_dir}")


if __name__ == "__main__":
    main()
