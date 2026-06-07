#!/usr/bin/env python3
"""Scripted pure-physics same-platform pick-place demo for the arm+hand scene."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np

import demo_arm_hand_lift_ball_scripted as base
from arm_hand_stage1_v3_pick_place_task_api import (
    CURRENT_PICK_PLACE_SCENE,
    DEFAULT_RELEASE_MAX_HAND_CONTACTS,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_CENTER,
    DEFAULT_TARGET_RADIUS_M,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
)
from demo_arm_hand_lift_ball_from_default import actuated_joint_targets_from_qpos
from render_arm_hand_lift_ball_video import FrameWriter


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_arm_hand_stage1_v3_pick_place"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_scripted_demo_report.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_scripted_demo.json"
DEFAULT_VIDEO = VIS / "pick_place_same_platform_scripted_demo.mp4"

TRANSPORT_ARM = {
    "j1": 2.95,
    "j2": -0.95,
    "j3": 0.52568695,
    "j4": base.ARM_LIFT["j4"],
}
DESCEND_ARM = {
    "j1": 2.95,
    "j2": -1.45,
    "j3": 0.52568695,
    "j4": base.ARM_LIFT["j4"],
}
RETREAT_ARM = {
    "j1": 2.95,
    "j2": -0.90,
    "j3": 0.52568695,
    "j4": base.ARM_LIFT["j4"],
}


def json_ready(value: Any) -> Any:
    return base.json_ready(value)


def ball_velocity_norm(model, data, mujoco) -> float:
    _, _, dadr = base.ball_indices(model, mujoco)
    return float(np.linalg.norm(data.qvel[dadr : dadr + 6]))


def pick_place_metrics(model, data, mujoco, initial_ball: np.ndarray, target_center: np.ndarray) -> dict[str, Any]:
    metrics = base.scalar_metrics(model, data, mujoco, initial_ball)
    ball = np.asarray(metrics["ball_position"], dtype=np.float64)
    delta = ball - target_center
    metrics.update(
        {
            "target_center": target_center,
            "target_delta_xyz": delta,
            "target_distance_xy": float(np.linalg.norm(delta[:2])),
            "target_distance_xyz": float(np.linalg.norm(delta)),
            "target_height_error": float(delta[2]),
            "ball_velocity_norm": ball_velocity_norm(model, data, mujoco),
        }
    )
    return metrics


def is_stable_on_target(metrics: dict[str, Any], target_radius: float) -> bool:
    contact = metrics["contact"]
    return bool(
        metrics["target_distance_xy"] <= target_radius
        and contact.get("ball_floor_contact_count", 0) >= 1
        and contact["ball_hand_contact_count"] <= DEFAULT_RELEASE_MAX_HAND_CONTACTS
        and contact["max_penetration"] <= 0.015
    )


def setup_pick_place_camera(model, data, mujoco, target_center: np.ndarray) -> object:
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultFreeCamera(model, cam)
    ball, _, _ = base.ball_indices(model, mujoco)
    ball_pos = data.xpos[ball].copy()
    cam.lookat[:] = 0.45 * ball_pos + 0.35 * target_center + 0.20 * np.array([0.22, 0.22, 0.02])
    cam.distance = 0.56
    cam.azimuth = 184
    cam.elevation = -20
    return cam


def append_video_frame(writer: FrameWriter, renderer, model, data, mujoco, target_center: np.ndarray) -> None:
    cam = setup_pick_place_camera(model, data, mujoco, target_center)
    renderer.update_scene(data, camera=cam)
    writer.append(renderer.render())


def render_snapshot(model, data, mujoco, target_center: np.ndarray, path: Path) -> str:
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = setup_pick_place_camera(model, data, mujoco, target_center)
        renderer.update_scene(data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, img)
    return str(path)


def run_interpolated_phase(
    model,
    data,
    mujoco,
    names: list[str],
    start_targets: dict[str, float],
    end_targets: dict[str, float],
    steps: int,
    *,
    target_center: np.ndarray,
    initial_ball: np.ndarray,
    phase_name: str,
    counters: dict[str, Any],
    target_radius: float,
    viewer=None,
    speed: float = 1.0,
    video_writer: FrameWriter | None = None,
    renderer=None,
    capture_every: int = 4,
) -> dict[str, Any]:
    for i in range(max(1, steps)):
        alpha = i / max(1, steps - 1)
        targets = base.blend_targets(start_targets, end_targets, alpha)
        data.ctrl[:] = base.ctrl_from_targets(model, mujoco, names, targets)
        mujoco.mj_step(model, data)
        metrics = pick_place_metrics(model, data, mujoco, initial_ball, target_center)
        contact = metrics["contact"]
        if (
            metrics["ball_lift_height"] >= 0.08
            and contact["ball_hand_contact_count"] >= 1
            and contact.get("ball_floor_contact_count", 0) == 0
        ):
            counters["lifted_once"] = True
        if phase_name in {"release", "retreat", "settle_on_target"}:
            counters["release_started"] = True
        if counters["lifted_once"] and not counters["release_started"] and phase_name in {"transport", "transport_hold", "descend_to_target"}:
            counters["transport_floor_contacts"] += int(contact.get("ball_floor_contact_count", 0) > 0)
        if counters["release_started"] and is_stable_on_target(metrics, target_radius):
            counters["stable_target_steps"] += 1
        elif counters["release_started"]:
            counters["stable_target_steps"] = 0
        counters["step_count"] += 1
        if video_writer is not None and renderer is not None and i % max(1, capture_every) == 0:
            append_video_frame(video_writer, renderer, model, data, mujoco, target_center)
        if viewer is not None:
            viewer.sync()
            time.sleep(model.opt.timestep / max(speed, 1e-6))
    return pick_place_metrics(model, data, mujoco, initial_ball, target_center)


def write_contact_sheet(snapshots: dict[str, str]) -> str:
    from PIL import Image, ImageDraw

    items = list(snapshots.items())
    thumbs = []
    for label, filename in items:
        img = Image.open(filename).convert("RGB")
        img.thumbnail((360, 253))
        canvas = Image.new("RGB", (380, 290), (245, 245, 245))
        canvas.paste(img, ((380 - img.width) // 2, 28))
        ImageDraw.Draw(canvas).text((12, 8), label, fill=(0, 0, 0))
        thumbs.append(canvas)
    rows = int(np.ceil(len(thumbs) / 3))
    sheet = Image.new("RGB", (3 * 380, rows * 290), (255, 255, 255))
    for i, img in enumerate(thumbs):
        sheet.paste(img, ((i % 3) * 380, (i // 3) * 290))
    out = VIS / "pick_place_same_platform_contact_sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return str(out)


def run_demo(args) -> dict[str, Any]:
    import mujoco

    scene = Path(args.scene).resolve()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    names = base.actuator_names(model, mujoco)
    target_center = np.asarray(args.target_center, dtype=np.float64)

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    initial_ball = data.xpos[base.ball_indices(model, mujoco)[0]].copy()
    base.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    default_targets = actuated_joint_targets_from_qpos(model, data, mujoco, names)
    pre_approach = {**default_targets, **base.ARM_PRE_APPROACH}
    approach = {**default_targets, **base.ARM_APPROACH}
    preshape = {**approach, **base.PRESHAPE_TARGETS}
    close_fingers = {**approach, **base.LONG_FINGER_TARGETS}
    close_thumb = {**close_fingers, **base.THUMB_SMOKE_TARGETS}
    lift = {**close_thumb, **base.ARM_LIFT}
    transport = {**close_thumb, **TRANSPORT_ARM}
    descend = {**close_thumb, **DESCEND_ARM}
    release_open = dict(DESCEND_ARM)
    retreat = dict(RETREAT_ARM)

    phases = [
        ("default_hold", default_targets, default_targets, args.default_hold_steps),
        ("move_to_pre_approach", default_targets, pre_approach, args.move_steps),
        ("approach_ball", pre_approach, approach, args.approach_steps),
        ("preshape", approach, preshape, args.hand_steps),
        ("close_four_fingers", preshape, close_fingers, args.hand_steps),
        ("close_thumb", close_fingers, close_thumb, args.hand_steps),
        ("lift", close_thumb, lift, args.lift_steps),
        ("hold_lift", lift, lift, args.hold_steps),
        ("transport", lift, transport, args.transport_steps),
        ("descend_to_target", transport, descend, args.descend_steps),
        ("pre_release_settle", descend, descend, args.pre_release_settle_steps),
        ("release", descend, release_open, args.release_steps),
        ("retreat", release_open, retreat, args.retreat_steps),
        ("settle_on_target", retreat, retreat, args.settle_steps),
    ]

    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    phase_rows = []
    render_snapshots = bool(getattr(args, "render_snapshots", True))
    snapshots: dict[str, str] = {}

    viewer_ctx = None
    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer_ctx = mujoco.viewer.launch_passive(model, data)
        viewer = viewer_ctx.__enter__()

    renderer = None
    writer_ctx = None
    video_path = str(Path(args.output).resolve()) if args.render_video else None
    try:
        if args.render_video:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            renderer = mujoco.Renderer(model, width=args.width, height=args.height)
            writer_ctx = FrameWriter(Path(args.output).resolve(), args.fps)
            writer = writer_ctx.__enter__()
            append_video_frame(writer, renderer, model, data, mujoco, target_center)
        else:
            writer = None

        for idx, (phase, start, end, steps) in enumerate(phases):
            metrics = run_interpolated_phase(
                model,
                data,
                mujoco,
                names,
                start,
                end,
                steps,
                target_center=target_center,
                initial_ball=initial_ball,
                phase_name=phase,
                counters=counters,
                target_radius=args.target_radius,
                viewer=viewer,
                speed=args.speed,
                video_writer=writer,
                renderer=renderer,
                capture_every=args.capture_every,
            )
            phase_rows.append({"phase": phase, "steps": int(steps), "metrics": metrics})
            if render_snapshots and phase in {"close_thumb", "lift", "transport", "descend_to_target", "release", "settle_on_target"}:
                snapshots[phase] = render_snapshot(model, data, mujoco, target_center, VIS / f"{idx:02d}_{phase}.png")
            if not bool(getattr(args, "quiet", False)):
                print(
                    f"{phase}: lift={metrics['ball_lift_height']:.4f} "
                    f"target_xy={metrics['target_distance_xy']:.4f} "
                    f"hand={metrics['contact']['ball_hand_contact_count']} "
                    f"floor={metrics['contact']['ball_floor_contact_count']} "
                    f"stable={counters['stable_target_steps']}"
                )
            if viewer is not None and not viewer.is_running():
                break
    finally:
        if writer_ctx is not None:
            writer_ctx.__exit__(None, None, None)
        if renderer is not None:
            renderer.close()
        if viewer_ctx is not None:
            viewer_ctx.__exit__(None, None, None)

    contact_sheet = write_contact_sheet(snapshots) if snapshots else None
    final = pick_place_metrics(model, data, mujoco, initial_ball, target_center)
    success = bool(
        counters["lifted_once"]
        and counters["release_started"]
        and counters["transport_floor_contacts"] == 0
        and counters["stable_target_steps"] >= args.required_stable_steps
        and is_stable_on_target(final, args.target_radius)
    )
    if success:
        status = "PASS"
        terminal_reason = "success_pick_place_ball"
    elif counters["transport_floor_contacts"] > 0:
        status = "PARTIAL"
        terminal_reason = "transport_floor_contact_before_release"
    elif final["target_distance_xy"] > args.target_radius:
        status = "PARTIAL"
        terminal_reason = "target_miss"
    elif final["contact"]["ball_hand_contact_count"] > DEFAULT_RELEASE_MAX_HAND_CONTACTS:
        status = "PARTIAL"
        terminal_reason = "release_contact_remaining"
    else:
        status = "PARTIAL"
        terminal_reason = "placement_not_stable"

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "scene": str(scene),
        "mode": "pure_physics_scripted_same_platform",
        "status": status,
        "terminal_reason": terminal_reason,
        "training_used": False,
        "dataset_ready": False,
        "video": video_path,
        "contact_sheet": contact_sheet,
        "snapshots": snapshots,
        "target_center": target_center,
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "counters": counters,
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
            "nmesh": int(model.nmesh),
        },
        "arm_targets": {
            "transport": TRANSPORT_ARM,
            "descend": DESCEND_ARM,
            "retreat": RETREAT_ARM,
        },
        "initial_ball": initial_ball,
        "phase_results": phase_rows,
        "final_metrics": final,
    }


def write_outputs(payload: dict[str, Any], report: Path, metadata: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    final = payload["final_metrics"]
    contact = final["contact"]
    lines = [
        "# Arm-Hand Stage1 V3 Pick-Place Scripted Demo Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{payload['status']}**\n",
        f"- Terminal reason: `{payload['terminal_reason']}`\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Mode: `{payload['mode']}`\n",
        f"- Training used: **No**\n",
        f"- Dataset ready: **No**\n",
        f"- Video: `{payload['video']}`\n",
        f"- Contact sheet: `{payload['contact_sheet']}`\n",
        f"- Target center: `{json_ready(payload['target_center'])}`\n",
        f"- Target radius: `{payload['target_radius']:.3f} m`\n",
        f"- Stable target steps: `{payload['counters']['stable_target_steps']} / {payload['required_stable_steps']}`\n",
        f"- Transport floor contacts before release: `{payload['counters']['transport_floor_contacts']}`\n\n",
        "## Final Metrics\n\n",
        f"- Ball position: `{json_ready(final['ball_position'])}`\n",
        f"- Ball lift height: `{final['ball_lift_height']:.6f} m`\n",
        f"- Target distance XY: `{final['target_distance_xy']:.6f} m`\n",
        f"- Ball velocity norm: `{final['ball_velocity_norm']:.6f}`\n",
        f"- Ball-hand contacts: `{contact['ball_hand_contact_count']}`\n",
        f"- Ball-floor contacts: `{contact['ball_floor_contact_count']}`\n",
        f"- Max penetration: `{contact['max_penetration']:.6f} m`\n\n",
        "## Phase Metrics\n\n",
        "| phase | steps | lift m | target xy m | velocity | hand contacts | floor contacts | max pen m |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["phase_results"]:
        metrics = row["metrics"]
        c = metrics["contact"]
        lines.append(
            f"| {row['phase']} | {row['steps']} | {metrics['ball_lift_height']:.4f} | "
            f"{metrics['target_distance_xy']:.4f} | {metrics['ball_velocity_norm']:.4f} | "
            f"{c['ball_hand_contact_count']} | {c['ball_floor_contact_count']} | {c['max_penetration']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "This is the first same-platform pick-place smoke demo. It proves the v3 task shape can be evaluated end to end, but it is still a scripted pure-physics rollout on collision proxy v2.\n\n",
            "The target displacement is intentionally modest. Larger target pads, two-platform transfer, randomized targets, dataset collection, and BC/RL training should remain gated behind additional scripted sweeps.\n",
        ]
    )
    report.write_text("".join(lines), encoding="utf-8")


def parse_target(raw: str) -> np.ndarray:
    parts = [float(item.strip()) for item in raw.split(",") if item.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("--target-center must contain exactly three comma-separated numbers")
    return np.asarray(parts, dtype=np.float64)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/render the same-platform Stage1 v3 pick-place scripted demo.")
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--target-center", type=parse_target, default=DEFAULT_TARGET_CENTER)
    parser.add_argument("--target-radius", type=float, default=DEFAULT_TARGET_RADIUS_M)
    parser.add_argument("--required-stable-steps", type=int, default=DEFAULT_REQUIRED_STABLE_STEPS)
    parser.add_argument("--output", type=Path, default=DEFAULT_VIDEO)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    parser.add_argument("--render-video", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--render-snapshots", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--speed", type=float, default=2.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--capture-every", type=int, default=4)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--transport-steps", type=int, default=900)
    parser.add_argument("--descend-steps", type=int, default=500)
    parser.add_argument("--pre-release-settle-steps", type=int, default=180)
    parser.add_argument("--release-steps", type=int, default=600)
    parser.add_argument("--retreat-steps", type=int, default=300)
    parser.add_argument("--settle-steps", type=int, default=600)
    args = parser.parse_args()

    payload = run_demo(args)
    write_outputs(payload, args.report, args.metadata)
    print(f"Status: {payload['status']} / {payload['terminal_reason']}")
    print(f"Video: {payload['video']}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
