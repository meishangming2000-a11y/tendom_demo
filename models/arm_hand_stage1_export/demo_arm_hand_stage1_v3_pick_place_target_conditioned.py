#!/usr/bin/env python3
"""Target-conditioned scripted pick-place prototype for Stage2 v0.7.

This script is an expert-design probe, not a trained policy. It computes
transport/hover/place arm targets from a requested target center, then runs
the same hand grasp sequence used by the earlier v3 demos.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
from scipy.optimize import minimize

import demo_arm_hand_lift_ball_scripted as base
import demo_arm_hand_stage1_v3_pick_place_scripted as v3
from arm_hand_stage1_v3_pick_place_task_api import (
    DEFAULT_RELEASE_MAX_HAND_CONTACTS,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_RADIUS_M,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
)
from demo_arm_hand_lift_ball_from_default import actuated_joint_targets_from_qpos
from render_arm_hand_lift_ball_video import FrameWriter


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_arm_hand_stage1_v3_pick_place_v0_7"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_pick_place_50cm_v0_7.xml"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_v0_7_target_conditioned_report.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_v0_7_target_conditioned.json"
DEFAULT_VIDEO = VIS / "pick_place_50cm_target_conditioned_demo.mp4"

DEFAULT_INITIAL_BALL = np.array([0.19022382, 0.187702, -0.06538044], dtype=np.float64)
DEFAULT_TARGET_HEIGHT = -0.06538044
DEFAULT_TARGET_DISTANCE = 0.50
DEFAULT_TARGET_ANGLE_DEG = -135.0


def json_ready(value: Any) -> Any:
    return base.json_ready(value)


def target_from_distance_angle(initial_ball: np.ndarray, distance: float, angle_deg: float) -> np.ndarray:
    angle = math.radians(float(angle_deg))
    target = np.asarray(initial_ball, dtype=np.float64).copy()
    target[:2] = target[:2] + float(distance) * np.array([math.cos(angle), math.sin(angle)], dtype=np.float64)
    target[2] = DEFAULT_TARGET_HEIGHT
    return target


def parse_target(raw: str) -> np.ndarray:
    parts = [float(item.strip()) for item in raw.split(",") if item.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("--target-center must contain exactly three comma-separated numbers")
    return np.asarray(parts, dtype=np.float64)


def joint_vector(targets: dict[str, float]) -> np.ndarray:
    return np.asarray([float(targets[joint]) for joint in base.ARM_JOINTS], dtype=np.float64)


class ArmIkSolver:
    def __init__(self, model, mujoco):
        self.model = model
        self.mujoco = mujoco
        self.data = mujoco.MjData(model)
        self.qadr = {joint: base.joint_qadr(model, mujoco, joint) for joint in base.ARM_JOINTS}
        self.bounds = []
        for joint in base.ARM_JOINTS:
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
            self.bounds.append(tuple(float(v) for v in model.jnt_range[jid]))

    def proxy_position(self, joints: np.ndarray) -> np.ndarray:
        self.data.qpos[:] = self.model.qpos0
        self.data.qvel[:] = 0.0
        for idx, joint in enumerate(base.ARM_JOINTS):
            self.data.qpos[self.qadr[joint]] = float(joints[idx])
        self.mujoco.mj_forward(self.model, self.data)
        return base.palm_relative_ball_position(self.model, self.data, self.mujoco)

    def solve(self, target_proxy: np.ndarray, *, z_weight: float = 8.0) -> dict[str, Any]:
        seeds = [
            joint_vector(base.ARM_LIFT),
            joint_vector(v3.TRANSPORT_ARM),
            joint_vector(v3.DESCEND_ARM),
            np.array([-0.73, -1.5708, -0.13, 2.90], dtype=np.float64),
            np.array([-0.25, -1.47, 0.47, 2.90], dtype=np.float64),
            np.array([0.33, -1.46, 0.55, 2.77], dtype=np.float64),
        ]
        for j1 in np.linspace(-2.8, 1.5, 10):
            seeds.append(np.array([j1, -1.48, 0.45, 2.60], dtype=np.float64))

        def objective(joints: np.ndarray) -> float:
            err = self.proxy_position(joints) - target_proxy
            return float(30.0 * (err[0] * err[0] + err[1] * err[1]) + float(z_weight) * err[2] * err[2])

        best = None
        for seed in seeds:
            result = minimize(objective, seed, method="L-BFGS-B", bounds=self.bounds, options={"maxiter": 160})
            joints = np.asarray(result.x, dtype=np.float64)
            proxy = self.proxy_position(joints)
            dxy = float(np.linalg.norm((proxy - target_proxy)[:2]))
            dz = abs(float(proxy[2] - target_proxy[2]))
            score = dxy + 0.25 * dz
            row = {
                "score": score,
                "dxy": dxy,
                "dz": dz,
                "joints": joints,
                "proxy": proxy,
                "optimizer_success": bool(result.success),
            }
            if best is None or row["score"] < best["score"]:
                best = row
        assert best is not None
        return best


def arm_dict(solution: dict[str, Any]) -> dict[str, float]:
    joints = np.asarray(solution["joints"], dtype=np.float64)
    return {joint: float(joints[idx]) for idx, joint in enumerate(base.ARM_JOINTS)}


def conditioned_arm_targets(
    model,
    mujoco,
    target_center: np.ndarray,
    *,
    pre_release_z_drop: float,
    hover_z_lift: float = 0.0,
) -> dict[str, Any]:
    solver = ArmIkSolver(model, mujoco)
    old_target = np.array([0.165, 0.230, DEFAULT_TARGET_HEIGHT], dtype=np.float64)
    descend_proxy_offset = solver.proxy_position(joint_vector(v3.DESCEND_ARM)) - old_target
    transport_proxy_offset = solver.proxy_position(joint_vector(v3.TRANSPORT_ARM)) - old_target

    base_hover_proxy = np.asarray(target_center, dtype=np.float64) + descend_proxy_offset
    hover_proxy = base_hover_proxy.copy()
    hover_proxy[2] += float(hover_z_lift)
    place_proxy = base_hover_proxy.copy()
    place_proxy[2] -= float(pre_release_z_drop)
    transport_proxy = np.asarray(target_center, dtype=np.float64) + np.array(
        [transport_proxy_offset[0], transport_proxy_offset[1], transport_proxy_offset[2]], dtype=np.float64
    )

    transport_solution = solver.solve(transport_proxy, z_weight=4.0)
    hover_solution = solver.solve(hover_proxy, z_weight=8.0)
    place_solution = solver.solve(place_proxy, z_weight=10.0)
    return {
        "transport": arm_dict(transport_solution),
        "hover": arm_dict(hover_solution),
        "place": arm_dict(place_solution),
        "retreat": arm_dict(transport_solution),
        "ik": {
            "target_center": target_center,
            "descend_proxy_offset": descend_proxy_offset,
            "transport_proxy_offset": transport_proxy_offset,
            "pre_release_z_drop": float(pre_release_z_drop),
            "hover_z_lift": float(hover_z_lift),
            "transport_solution": transport_solution,
            "hover_solution": hover_solution,
            "place_solution": place_solution,
        },
    }


def render_snapshot(model, data, mujoco, target_center: np.ndarray, path: Path) -> str:
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = v3.setup_pick_place_camera(model, data, mujoco, target_center)
        renderer.update_scene(data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, img)
    return str(path)


def write_contact_sheet(snapshots: dict[str, str], output: Path) -> str | None:
    from PIL import Image, ImageDraw

    items = list(snapshots.items())
    if not items:
        return None
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
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return str(output)


def run_demo(args) -> dict[str, Any]:
    import mujoco

    scene = Path(args.scene).resolve()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    names = base.actuator_names(model, mujoco)

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    initial_ball = data.xpos[base.ball_indices(model, mujoco)[0]].copy()
    base.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    target_center = np.asarray(args.target_center, dtype=np.float64) if args.target_center is not None else target_from_distance_angle(
        initial_ball,
        args.target_distance,
        args.target_angle_deg,
    )
    arm = conditioned_arm_targets(model, mujoco, target_center, pre_release_z_drop=args.pre_release_z_drop)

    default_targets = actuated_joint_targets_from_qpos(model, data, mujoco, names)
    pre_approach = {**default_targets, **base.ARM_PRE_APPROACH}
    approach = {**default_targets, **base.ARM_APPROACH}
    preshape = {**approach, **base.PRESHAPE_TARGETS}
    close_fingers = {**approach, **base.LONG_FINGER_TARGETS}
    close_thumb = {**close_fingers, **base.THUMB_SMOKE_TARGETS}
    lift = {**close_thumb, **base.ARM_LIFT}
    transport = {**close_thumb, **arm["transport"]}
    hover = {**close_thumb, **arm["hover"]}
    place = {**close_thumb, **arm["place"]}
    release_open = dict(arm["place"])
    release_clear = dict(arm["hover"])
    retreat = dict(arm["retreat"])

    phases = [
        ("default_hold", default_targets, default_targets, args.default_hold_steps),
        ("move_to_pre_approach", default_targets, pre_approach, args.move_steps),
        ("approach_ball", pre_approach, approach, args.approach_steps),
        ("preshape", approach, preshape, args.hand_steps),
        ("close_four_fingers", preshape, close_fingers, args.hand_steps),
        ("close_thumb", close_fingers, close_thumb, args.close_thumb_steps),
        ("close_hold", close_thumb, close_thumb, args.close_hold_steps),
        ("lift", close_thumb, lift, args.lift_steps),
        ("hold_lift", lift, lift, args.hold_steps),
        ("transport", lift, transport, args.transport_steps),
        ("transport_hold", transport, transport, args.transport_hold_steps),
        ("descend_to_target", transport, hover, args.descend_steps),
        ("pre_release_settle", hover, place, args.pre_release_settle_steps),
        ("release", place, release_open, args.release_steps),
    ]
    if args.post_release_clear_steps > 0:
        phases.append(("post_release_clear", release_open, release_clear, args.post_release_clear_steps))
        settle_start = release_clear
    else:
        settle_start = release_open
    phases.append(("settle_on_target", settle_start, settle_start, args.settle_steps))
    if args.retreat_after_success:
        phases.extend(
            [
                ("retreat", settle_start, retreat, args.retreat_steps),
                ("settle_after_retreat", retreat, retreat, args.settle_after_retreat_steps),
            ]
        )

    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    phase_rows = []
    snapshots: dict[str, str] = {}
    render_dir = Path(args.output).resolve().parent if args.render_video else Path(args.report).resolve().parent.parent / "visuals"

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
            v3.append_video_frame(writer, renderer, model, data, mujoco, target_center)
        else:
            writer = None

        snapshot_phases = {
            "close_thumb",
            "close_hold",
            "lift",
            "transport",
            "transport_hold",
            "descend_to_target",
            "pre_release_settle",
            "release",
            "post_release_clear",
            "settle_on_target",
        }
        for idx, (phase, start, end, steps) in enumerate(phases):
            metrics = v3.run_interpolated_phase(
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
            if args.render_snapshots and phase in snapshot_phases:
                snapshots[phase] = render_snapshot(model, data, mujoco, target_center, render_dir / f"v0_7_{idx:02d}_{phase}.png")
            if not args.quiet:
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

    contact_sheet = write_contact_sheet(snapshots, render_dir / "v0_7_target_conditioned_contact_sheet.png") if snapshots else None
    final = v3.pick_place_metrics(model, data, mujoco, initial_ball, target_center)
    success = bool(
        counters["lifted_once"]
        and counters["release_started"]
        and counters["transport_floor_contacts"] == 0
        and counters["stable_target_steps"] >= args.required_stable_steps
        and v3.is_stable_on_target(final, args.target_radius)
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
        "mode": "target_conditioned_scripted_v0_7",
        "status": status,
        "terminal_reason": terminal_reason,
        "training_used": False,
        "dataset_ready": bool(success),
        "video": video_path,
        "contact_sheet": contact_sheet,
        "snapshots": snapshots,
        "initial_ball": initial_ball,
        "target_center": target_center,
        "target_distance_from_initial_xy": float(np.linalg.norm((target_center - initial_ball)[:2])),
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "counters": counters,
        "arm_targets": {
            "transport": arm["transport"],
            "hover": arm["hover"],
            "place": arm["place"],
            "retreat": arm["retreat"],
        },
        "ik": arm["ik"],
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
        "# Arm-Hand Stage1 V3 Pick-Place V0.7 Target-Conditioned Scripted Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{payload['status']}**\n",
        f"- Terminal reason: `{payload['terminal_reason']}`\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Mode: `{payload['mode']}`\n",
        f"- Training used: **No**\n",
        f"- Dataset ready: **{payload['dataset_ready']}**\n",
        f"- Video: `{payload['video']}`\n",
        f"- Contact sheet: `{payload['contact_sheet']}`\n",
        f"- Initial ball: `{json_ready(payload['initial_ball'])}`\n",
        f"- Target center: `{json_ready(payload['target_center'])}`\n",
        f"- Initial-to-target XY: `{payload['target_distance_from_initial_xy']:.6f} m`\n",
        f"- Target radius: `{payload['target_radius']:.3f} m`\n",
        f"- Stable target steps: `{payload['counters']['stable_target_steps']} / {payload['required_stable_steps']}`\n",
        f"- Transport floor contacts before release: `{payload['counters']['transport_floor_contacts']}`\n\n",
        "## IK Summary\n\n",
        "| target | score | dxy | dz | proxy xyz |\n",
        "|---|---:|---:|---:|---|\n",
    ]
    for name in ["transport_solution", "hover_solution", "place_solution"]:
        sol = payload["ik"][name]
        lines.append(
            f"| {name} | {sol['score']:.6f} | {sol['dxy']:.6f} | {sol['dz']:.6f} | `{json_ready(sol['proxy'])}` |\n"
        )
    lines.extend(
        [
            "\n## Final Metrics\n\n",
            f"- Ball position: `{json_ready(final['ball_position'])}`\n",
            f"- Ball lift height: `{final['ball_lift_height']:.6f} m`\n",
            f"- Target distance XY: `{final['target_distance_xy']:.6f} m`\n",
            f"- Ball velocity norm: `{final['ball_velocity_norm']:.6f}`\n",
            f"- Ball-hand contacts: `{contact['ball_hand_contact_count']}`\n",
            f"- Ball-floor contacts: `{contact['ball_floor_contact_count']}`\n",
            f"- Max penetration: `{contact['max_penetration']:.6f} m`\n\n",
            "## Phase Metrics\n\n",
            "| phase | steps | lift m | target xy m | velocity | hand contacts | floor contacts | stable steps |\n",
            "|---|---:|---:|---:|---:|---:|---:|---:|\n",
        ]
    )
    for row in payload["phase_results"]:
        metrics = row["metrics"]
        c = metrics["contact"]
        lines.append(
            f"| {row['phase']} | {row['steps']} | {metrics['ball_lift_height']:.4f} | "
            f"{metrics['target_distance_xy']:.4f} | {metrics['ball_velocity_norm']:.4f} | "
            f"{c['ball_hand_contact_count']} | {c['ball_floor_contact_count']} | "
            f"{row.get('stable_target_steps', payload['counters']['stable_target_steps'])} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- V0.7 introduces target-conditioned arm targets for long-distance transfer.\n",
            "- The default target is a 50cm reachable far target, not the old 5cm same-platform target.\n",
            "- If this report is PASS, the next gate is v0.7 dataset collection from the same target-conditioned expert.\n",
        ]
    )
    report.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/render v0.7 target-conditioned Stage1 pick-place scripted demo.")
    parser.add_argument("--scene", type=Path, default=DEFAULT_SCENE)
    parser.add_argument("--target-center", type=parse_target, default=None)
    parser.add_argument("--target-distance", type=float, default=DEFAULT_TARGET_DISTANCE)
    parser.add_argument("--target-angle-deg", type=float, default=DEFAULT_TARGET_ANGLE_DEG)
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
    parser.add_argument("--capture-every", type=int, default=8)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--close-hold-steps", type=int, default=180)
    parser.add_argument("--lift-steps", type=int, default=260)
    parser.add_argument("--hold-steps", type=int, default=220)
    parser.add_argument("--transport-steps", type=int, default=1600)
    parser.add_argument("--transport-hold-steps", type=int, default=300)
    parser.add_argument("--descend-steps", type=int, default=760)
    parser.add_argument("--pre-release-settle-steps", type=int, default=900)
    parser.add_argument("--pre-release-z-drop", type=float, default=0.02)
    parser.add_argument("--release-steps", type=int, default=900)
    parser.add_argument("--post-release-clear-steps", type=int, default=0)
    parser.add_argument("--settle-steps", type=int, default=1400)
    parser.add_argument("--retreat-after-success", action="store_true")
    parser.add_argument("--retreat-steps", type=int, default=500)
    parser.add_argument("--settle-after-retreat-steps", type=int, default=1200)
    args = parser.parse_args()

    payload = run_demo(args)
    write_outputs(payload, args.report, args.metadata)
    print(f"Status: {payload['status']} / {payload['terminal_reason']}")
    print(f"Initial-to-target XY: {payload['target_distance_from_initial_xy']:.6f} m")
    print(f"Final target XY: {payload['final_metrics']['target_distance_xy']:.6f} m")
    print(f"Video: {payload['video']}")
    print(f"Contact sheet: {payload['contact_sheet']}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
