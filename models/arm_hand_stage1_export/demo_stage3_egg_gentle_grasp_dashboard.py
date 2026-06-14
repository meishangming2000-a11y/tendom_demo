from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
THIS_DIR = Path(__file__).resolve().parent
SENSOR_ROOT = THIS_DIR / "external_sensors"
DEFAULT_OUTPUT_DIR = Path.home() / "Desktop" / "Demos"

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import demo_stage3_sensor_fusion_viewer as fusion
import run_stage3_visual_guided_grasp_sweep as sweep
from demo_arm_hand_lift_ball_from_default import actuated_joint_targets_from_qpos
from external_sensors.mujoco_motor_force_feedback_sensor import (
    MotorForceFeedbackConfig,
    MujocoMotorForceFeedbackSensor,
)
from external_sensors.mujoco_tactile_slip_sensor import MujocoTactileSlipSensor
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def configure_camera(model, data, mujoco, camera, args: argparse.Namespace, egg_pos: np.ndarray) -> None:
    mujoco.mjv_defaultFreeCamera(model, camera)
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = np.asarray(egg_pos, dtype=float).copy()
    if palm_id >= 0:
        lookat = 0.55 * lookat + 0.45 * data.xpos[palm_id].copy()
    camera.lookat[:] = lookat + np.array(
        [float(args.camera_lookat_dx), float(args.camera_lookat_dy), float(args.camera_lookat_dz)]
    )
    camera.distance = float(args.camera_distance)
    camera.azimuth = float(args.camera_azimuth)
    camera.elevation = float(args.camera_elevation)


class EggGentleGraspEpisode:
    def __init__(self, model, data, mujoco, args: argparse.Namespace):
        self.model = model
        self.data = data
        self.mujoco = mujoco
        self.args = args
        self.thresholds = Stage3Thresholds()
        self.plan = fusion.build_demo_plan(model, data, mujoco, args)
        self.actuator_names = sweep.base.actuator_names(model, mujoco)
        self.pre_arm = dict(self.plan.phases[0][1])

        sweep.reset_episode(model, data, mujoco, self.plan.egg_position)
        self.default_targets = actuated_joint_targets_from_qpos(model, data, mujoco, self.actuator_names)
        self.pre_targets = {**self.default_targets, **self.pre_arm}
        data.ctrl[:] = sweep.actuator_targets(model, mujoco, self.actuator_names, self.default_targets)
        mujoco.mj_forward(model, data)

        self.tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=self.thresholds)
        self.tactile_sensor.reset(data)
        self.motor_sensor = MujocoMotorForceFeedbackSensor(
            MotorForceFeedbackConfig(
                current_limit_a=float(args.motor_current_limit_a),
                bus_voltage_v=float(args.motor_bus_voltage_v),
                current_noise_a=float(args.motor_current_noise_a),
                seed=int(args.motor_feedback_seed),
            )
        )
        self.trace_rows: list[dict[str, Any]] = []
        self.sequence_id = 0
        self.last_row: dict[str, Any] | None = None
        self.max_slip = 0.0
        self.max_crush = 0.0
        self.max_pen = 0.0
        self.max_hand_tension = 0.0
        self.max_hand_current = 0.0
        self.hold_steps = 0
        self.hold_stable_steps = 0
        self.hold_max_slip = 0.0
        self.sample("start", 0, 0.0)

    def sample(self, phase: str, phase_step: int, phase_progress: float) -> dict[str, Any]:
        tactile = self.tactile_sensor.sample(self.data)
        motor = self.motor_sensor.observe(
            self.model,
            self.data,
            self.mujoco,
            phase=phase,
            active_pair=("thumb", "middle"),
        )
        egg_pos = self.data.xpos[sweep.egg_body_id(self.model, self.mujoco)].copy()
        lift = float(egg_pos[2] - self.plan.initial_egg[2])
        hand_tension = float(motor.get("max_hand_tendon_tension_n", 0.0))
        hand_current = float(motor.get("max_hand_abs_iq_a", 0.0))
        max_pen = float(tactile.get("max_penetration", 0.0))
        slip = float(tactile.get("slip_score", 0.0))
        crush = float(tactile.get("crush_risk", 0.0))
        regions = tactile.get("contact_regions", [])
        if not isinstance(regions, list):
            regions = []
        row = {
            "sequence_id": int(self.sequence_id),
            "time_s": float(self.data.time),
            "phase": str(phase),
            "phase_step": int(phase_step),
            "phase_progress": float(phase_progress),
            "vision_status": str(self.plan.vision_estimate.get("status", "")),
            "vision_confidence": float(self.plan.vision_estimate.get("confidence", 0.0)),
            "vision_mask_pixels": int(self.plan.vision_estimate.get("mask_pixels", 0)),
            "lift_m": float(lift),
            "contact_present": int(bool(tactile.get("contact_present", False))),
            "grip_stable": int(bool(tactile.get("grip_stable", False))),
            "contact_persistence": int(tactile.get("contact_persistence", 0)),
            "egg_hand_contact_count": int(tactile.get("egg_hand_contact_count", 0)),
            "egg_floor_contact_count": int(tactile.get("egg_floor_contact_count", 0)),
            "contact_regions": ",".join(str(region) for region in regions),
            "slip_score": float(slip),
            "crush_risk": float(crush),
            "max_penetration_m": float(max_pen),
            "object_velocity_norm": float(np.linalg.norm(np.asarray(tactile.get("object_velocity_world", [0, 0, 0])))),
            "hand_tendon_tension_n": float(hand_tension),
            "hand_motor_current_a": float(hand_current),
            "active_pair_total_tension_n": float(
                motor.get("active_pair", {}).get("total_tendon_tension_n", 0.0)
                if isinstance(motor.get("active_pair", {}), dict)
                else 0.0
            ),
            "active_pair_max_iq_a": float(
                motor.get("active_pair", {}).get("max_abs_iq_a", 0.0)
                if isinstance(motor.get("active_pair", {}), dict)
                else 0.0
            ),
        }
        self.trace_rows.append(row)
        self.last_row = row
        self.sequence_id += 1
        self.max_slip = max(self.max_slip, slip)
        self.max_crush = max(self.max_crush, crush)
        self.max_pen = max(self.max_pen, max_pen)
        self.max_hand_tension = max(self.max_hand_tension, hand_tension)
        self.max_hand_current = max(self.max_hand_current, hand_current)
        if phase == "hold":
            self.hold_steps += 1
            self.hold_stable_steps += int(bool(tactile.get("grip_stable", False)))
            self.hold_max_slip = max(self.hold_max_slip, slip)
        return row

    def keep_egg_fixed(self) -> None:
        sweep.set_freejoint_pose(
            self.model,
            self.data,
            self.mujoco,
            sweep.EGG_JOINT,
            self.plan.egg_position,
            sweep.DEFAULT_EGG_QUAT,
        )
        self.mujoco.mj_forward(self.model, self.data)

    def reset_to_clean_pregrasp(self) -> None:
        sweep.reset_episode(self.model, self.data, self.mujoco, self.plan.egg_position)
        for joint, value in self.pre_arm.items():
            qadr = sweep.base.joint_qadr(self.model, self.mujoco, joint)
            self.data.qpos[qadr] = float(value)
        self.data.ctrl[:] = sweep.actuator_targets(self.model, self.mujoco, self.actuator_names, self.pre_targets)
        self.mujoco.mj_forward(self.model, self.data)
        self.tactile_sensor.reset(self.data)

    def step_targets(
        self,
        targets: dict[str, float],
        phase: str,
        phase_step: int,
        phase_progress: float,
        *,
        hold_egg_fixed: bool = False,
    ) -> dict[str, Any]:
        self.data.ctrl[:] = sweep.actuator_targets(self.model, self.mujoco, self.actuator_names, targets)
        self.mujoco.mj_step(self.model, self.data)
        if hold_egg_fixed:
            self.keep_egg_fixed()
        return self.sample(phase, phase_step, phase_progress)

    def run(self, dashboard=None) -> dict[str, Any]:
        for idx in range(max(0, int(self.args.intro_hold_steps))):
            progress = idx / max(1, int(self.args.intro_hold_steps) - 1)
            self.step_targets(self.default_targets, "initial_vertical_hold", idx, progress, hold_egg_fixed=True)
            if dashboard is not None and not dashboard.update(self):
                return self.summary("viewer_closed")

        for idx in range(max(0, int(self.args.intro_steps))):
            alpha = idx / max(1, int(self.args.intro_steps) - 1)
            targets = sweep.blend_targets(self.default_targets, self.pre_targets, alpha)
            self.step_targets(targets, "initial_to_grasp_pose", idx, alpha, hold_egg_fixed=True)
            if dashboard is not None and not dashboard.update(self):
                return self.summary("viewer_closed")

        self.reset_to_clean_pregrasp()
        self.sample("pre_grasp_ready", 0, 1.0)
        if dashboard is not None and not dashboard.update(self, force=True):
            return self.summary("viewer_closed")

        for phase_name, start, end, steps in self.plan.phases:
            start_targets = {**self.default_targets, **start}
            end_targets = {**self.default_targets, **end}
            for idx in range(max(1, int(steps))):
                alpha = idx / max(1, int(steps) - 1)
                targets = sweep.blend_targets(start_targets, end_targets, alpha)
                self.step_targets(targets, phase_name, idx, alpha)
                if dashboard is not None and not dashboard.update(self):
                    return self.summary("viewer_closed")

        result = self.summary("success_gentle_grasp_hold" if self.success else "not_success")
        if dashboard is not None:
            dashboard.update(self, terminal_reason=result["terminal_reason"], force=True)
        return result

    @property
    def success(self) -> bool:
        row = self.last_row or {}
        hold_stable_fraction = float(self.hold_stable_steps / max(1, self.hold_steps))
        return bool(
            float(row.get("lift_m", 0.0)) >= float(self.thresholds.success_lift_height_m)
            and hold_stable_fraction >= float(self.args.min_hold_stable_fraction)
            and float(self.hold_max_slip) <= float(self.thresholds.success_max_slip_score)
            and float(self.max_crush) <= float(self.thresholds.success_max_crush_risk)
            and float(self.max_pen) <= float(self.thresholds.failure_max_penetration_m)
        )

    def summary(self, terminal_reason: str) -> dict[str, Any]:
        row = self.last_row or {}
        return {
            "status": "PASS" if self.success else "FAIL",
            "success": bool(self.success),
            "terminal_reason": terminal_reason,
            "trial": str(self.plan.trial.name),
            "vision_status": str(self.plan.vision_estimate.get("status", "")),
            "vision_confidence": float(self.plan.vision_estimate.get("confidence", 0.0)),
            "final_lift_height_m": float(row.get("lift_m", 0.0)),
            "final_grip_stable": bool(int(row.get("grip_stable", 0))),
            "final_slip_score": float(row.get("slip_score", 0.0)),
            "hold_stable_fraction": float(self.hold_stable_steps / max(1, self.hold_steps)),
            "hold_max_slip_score": float(self.hold_max_slip),
            "max_slip_score": float(self.max_slip),
            "max_crush_risk": float(self.max_crush),
            "max_penetration_m": float(self.max_pen),
            "max_hand_tendon_tension_n": float(self.max_hand_tension),
            "max_hand_motor_current_a": float(self.max_hand_current),
            "samples": int(len(self.trace_rows)),
        }


class EggDashboard:
    def __init__(
        self,
        model,
        data,
        mujoco,
        args: argparse.Namespace,
        egg_pos: np.ndarray,
        *,
        video_path: Path | None = None,
        show_window: bool = False,
    ):
        import cv2

        self.cv2 = cv2
        self.model = model
        self.data = data
        self.mujoco = mujoco
        self.args = args
        self.show_window = bool(show_window)
        self.width = int(args.dashboard_width)
        self.render_height = int(args.dashboard_render_height)
        self.plot_height = int(args.dashboard_plot_height)
        self.window_name = "Stage3 egg gentle grasp dashboard"
        self.renderer = mujoco.Renderer(model, width=self.width, height=self.render_height)
        self.camera = mujoco.MjvCamera()
        configure_camera(model, data, mujoco, self.camera, args, egg_pos)
        self.tick = 0
        self.running = True
        self.video_path = Path(video_path) if video_path is not None else None
        self.video_writer = None
        self.terminal_recorded = False
        if self.show_window:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.width, self.render_height + self.plot_height)
        if self.video_path is not None:
            self.video_path.parent.mkdir(parents=True, exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(
                str(self.video_path),
                fourcc,
                float(args.video_fps),
                (self.width, self.render_height + self.plot_height),
            )
            if not self.video_writer.isOpened():
                raise RuntimeError(f"Could not open video writer for {self.video_path}")

    def close(self) -> None:
        try:
            self.renderer.close()
            if self.video_writer is not None:
                self.video_writer.release()
        finally:
            if self.show_window:
                self.cv2.destroyWindow(self.window_name)

    def update(self, episode: EggGentleGraspEpisode, *, terminal_reason: str = "", force: bool = False) -> bool:
        if not self.running:
            return False
        if self.show_window and float(self.args.speed) > 0.0:
            time.sleep(float(episode.model.opt.timestep) / max(float(self.args.speed), 1e-6))
        self.tick += 1
        if self.show_window:
            key = self.cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                self.running = False
                return False
        show_due = self.show_window and (
            force or self.tick % max(1, int(self.args.dashboard_frame_every)) == 0 or bool(terminal_reason)
        )
        record_every = max(1, int(round(float(self.args.dashboard_frame_every) * float(self.args.video_speedup))))
        record_due = self.video_writer is not None and (
            force
            or self.tick % record_every == 0
            or (bool(terminal_reason) and not self.terminal_recorded)
        )
        if not show_due and not record_due:
            return True
        self.renderer.update_scene(episode.data, camera=self.camera)
        rgb = self.renderer.render()
        frame = self.cv2.cvtColor(rgb, self.cv2.COLOR_RGB2BGR)
        dashboard = self.compose(episode, frame, terminal_reason)
        if record_due and self.video_writer is not None:
            if terminal_reason and not self.terminal_recorded:
                for _idx in range(max(1, int(round(float(self.args.video_fps) * float(self.args.video_final_hold_seconds))))):
                    self.video_writer.write(dashboard)
                self.terminal_recorded = True
                if not self.show_window and not bool(self.args.loop):
                    self.running = False
            else:
                self.video_writer.write(dashboard)
        if show_due:
            self.cv2.imshow(self.window_name, dashboard)
            if self.cv2.getWindowProperty(self.window_name, self.cv2.WND_PROP_VISIBLE) < 1:
                self.running = False
        return self.running

    def compose(self, episode: EggGentleGraspEpisode, render_bgr: np.ndarray, terminal_reason: str) -> np.ndarray:
        cv2 = self.cv2
        top = render_bgr.copy()
        self.draw_overlay(top, episode, terminal_reason)
        plot = np.full((self.plot_height, self.width, 3), (18, 18, 18), dtype=np.uint8)
        self.draw_curves(plot, episode)
        return np.vstack([top, plot])

    def draw_overlay(self, image: np.ndarray, episode: EggGentleGraspEpisode, terminal_reason: str) -> None:
        cv2 = self.cv2
        row = episode.last_row or {}
        lines = [
            "Stage3 egg gentle grasp: vision + tactile/slip + force feedback",
            f"phase {row.get('phase', '-')}   sim {float(row.get('time_s', 0.0)):.2f}s   seq {int(row.get('sequence_id', 0))}",
            f"vision {row.get('vision_status', '-')}   confidence {float(row.get('vision_confidence', 0.0)):.3f}",
            f"lift {float(row.get('lift_m', 0.0)):.4f} m / goal {episode.thresholds.success_lift_height_m:.4f} m",
            f"contact {bool(int(row.get('contact_present', 0)))}   stable {bool(int(row.get('grip_stable', 0)))}   regions {row.get('contact_regions', '-') or '-'}",
            f"slip {float(row.get('slip_score', 0.0)):.3f}   crush {float(row.get('crush_risk', 0.0)):.3f}   penetration {float(row.get('max_penetration_m', 0.0)):.5f} m",
            f"hand tension {float(row.get('hand_tendon_tension_n', 0.0)):.2f} N   hand current {float(row.get('hand_motor_current_a', 0.0)):.2f} A",
        ]
        if terminal_reason:
            lines.append(terminal_reason)
        box_w = 900
        line_h = 27
        overlay = image.copy()
        self.cv2.rectangle(overlay, (10, 10), (box_w, 28 + line_h * len(lines)), (20, 20, 20), -1)
        self.cv2.addWeighted(overlay, 0.67, image, 0.33, 0.0, image)
        for idx, text in enumerate(lines):
            color = (255, 255, 255) if idx else (90, 220, 255)
            cv2.putText(image, text, (20, 36 + idx * line_h), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 1, cv2.LINE_AA)

    def draw_curves(self, image: np.ndarray, episode: EggGentleGraspEpisode) -> None:
        cv2 = self.cv2
        rows = episode.trace_rows
        cv2.putText(
            image,
            "Synchronized curves from the same MuJoCo ticks",
            (18, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.66,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        if len(rows) < 2:
            return
        now = float(rows[-1]["time_s"])
        span = max(0.5, float(self.args.plot_seconds))
        visible = [row for row in rows if float(row["time_s"]) >= now - span]
        if len(visible) < 2:
            visible = rows[-2:]
        lane_top = 45
        lane_h = max(44, (self.plot_height - lane_top - 10) // 5)
        lanes = [
            ("hand_tendon_tension_n", "hand tendon tension", "N", (0, 210, 255), 0.0, None),
            ("hand_motor_current_a", "hand motor current", "A", (255, 210, 0), 0.0, None),
            ("slip_score", "slip risk", "", (70, 180, 255), 0.0, 1.0),
            ("crush_risk", "crush risk", "", (80, 220, 120), 0.0, 1.0),
            ("lift_m", "lift height", "m", (150, 130, 255), 0.0, 0.13),
        ]
        for idx, lane in enumerate(lanes):
            self.draw_lane(image, visible, lane, lane_top + idx * lane_h, lane_h - 8)

    def draw_lane(
        self,
        image: np.ndarray,
        rows: list[dict[str, Any]],
        lane: tuple[str, str, str, tuple[int, int, int], float | None, float | None],
        top: int,
        height: int,
    ) -> None:
        cv2 = self.cv2
        field, label, unit, color, ymin, ymax = lane
        left = 190
        right = self.width - 24
        bottom = top + height
        values = [float(row.get(field, 0.0)) for row in rows]
        times = [float(row.get("time_s", 0.0)) for row in rows]
        if ymin is None:
            ymin = min(values + [0.0])
        if ymax is None:
            ymax = max(values + [1.0])
        if ymax <= ymin:
            ymax = ymin + 1.0
        pad = 0.05 * (ymax - ymin)
        ymin -= pad
        ymax += pad
        t0, t1 = min(times), max(times)
        if t1 <= t0:
            t1 = t0 + 1.0
        axis_y = bottom - 14
        cv2.line(image, (left, axis_y), (right, axis_y), (80, 80, 80), 1)
        cv2.line(image, (left, top + 6), (left, axis_y), (80, 80, 80), 1)
        pts: list[tuple[int, int]] = []
        for t, value in zip(times, values):
            x = int(left + (t - t0) / (t1 - t0) * max(1, right - left))
            y = int(axis_y - (value - ymin) / (ymax - ymin) * max(1, height - 22))
            pts.append((x, int(np.clip(y, top + 6, axis_y))))
        for a, b in zip(pts, pts[1:]):
            cv2.line(image, a, b, color, 2, cv2.LINE_AA)
        cv2.putText(
            image,
            f"{label}: {values[-1]:.3f} {unit}".strip(),
            (18, top + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.53,
            color,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            f"range {ymin:.2f}..{ymax:.2f}",
            (18, top + 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.39,
            (165, 165, 165),
            1,
            cv2.LINE_AA,
        )
        phase = str(rows[-1].get("phase", ""))
        cv2.putText(image, phase[:30], (right - 230, top + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (185, 185, 185), 1, cv2.LINE_AA)


def write_trace_csv(path: Path | None, rows: list[dict[str, Any]]) -> None:
    if path is None or not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a Stage3 egg gentle-grasp dashboard video.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--trial", default="center_nominal")
    parser.add_argument("--perception-camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=720)
    parser.add_argument("--intro-hold-steps", type=int, default=80)
    parser.add_argument("--intro-steps", type=int, default=260)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.80)
    parser.add_argument("--record-video", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--dashboard-window", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--loop", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--headless-smoke", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--video-output", type=Path, default=None)
    parser.add_argument("--trace-csv", type=Path, default=None)
    parser.add_argument("--no-trace-csv", action="store_true")
    parser.add_argument("--video-fps", type=float, default=30.0)
    parser.add_argument("--video-speedup", type=float, default=3.0)
    parser.add_argument("--video-final-hold-seconds", type=float, default=1.0)
    parser.add_argument("--speed", type=float, default=0.75)
    parser.add_argument("--dashboard-width", type=int, default=1280)
    parser.add_argument("--dashboard-render-height", type=int, default=720)
    parser.add_argument("--dashboard-plot-height", type=int, default=360)
    parser.add_argument("--dashboard-frame-every", type=int, default=3)
    parser.add_argument("--plot-seconds", type=float, default=4.0)
    parser.add_argument("--camera-distance", type=float, default=0.88)
    parser.add_argument("--camera-azimuth", type=float, default=170.0)
    parser.add_argument("--camera-elevation", type=float, default=-19.0)
    parser.add_argument("--camera-lookat-dx", type=float, default=0.0)
    parser.add_argument("--camera-lookat-dy", type=float, default=-0.01)
    parser.add_argument("--camera-lookat-dz", type=float, default=0.08)
    parser.add_argument("--motor-current-limit-a", type=float, default=4.0)
    parser.add_argument("--motor-bus-voltage-v", type=float, default=24.0)
    parser.add_argument("--motor-current-noise-a", type=float, default=0.025)
    parser.add_argument("--motor-feedback-seed", type=int, default=20260611)
    return parser


def output_paths(args: argparse.Namespace) -> tuple[Path | None, Path | None]:
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = None
    if bool(args.record_video):
        if args.video_output is None:
            speed_tag = str(float(args.video_speedup)).replace(".", "p")
            video_path = out_dir / f"stage3_egg_gentle_grasp_dashboard_x{speed_tag}.mp4"
        else:
            video_path = Path(args.video_output).expanduser().resolve()
    trace_path = None
    if not bool(args.no_trace_csv):
        trace_path = Path(args.trace_csv).expanduser().resolve() if args.trace_csv is not None else out_dir / "stage3_egg_gentle_grasp_trace.csv"
    return video_path, trace_path


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    video_path, trace_path = output_paths(args)
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    episode = EggGentleGraspEpisode(model, data, mujoco, args)

    if bool(args.headless_smoke):
        result = episode.run(dashboard=None)
        write_trace_csv(trace_path, episode.trace_rows)
        print(
            "Stage3 egg dashboard smoke: "
            f"status={result['status']} reason={result['terminal_reason']} "
            f"vision={result['vision_status']} conf={result['vision_confidence']:.3f} "
            f"lift={result['final_lift_height_m']:.4f} stable={result['final_grip_stable']} "
            f"hold_stable={result['hold_stable_fraction']:.3f} "
            f"hold_slip={result['hold_max_slip_score']:.3f} "
            f"max_crush={result['max_crush_risk']:.3f} trace_csv={trace_path if trace_path else 'disabled'}"
        )
        return 0 if bool(result["success"]) else 1

    dashboard = EggDashboard(
        model,
        data,
        mujoco,
        args,
        episode.plan.initial_egg,
        video_path=video_path,
        show_window=bool(args.dashboard_window),
    )
    final_result: dict[str, Any] | None = None
    try:
        while dashboard.running:
            final_result = episode.run(dashboard=dashboard)
            print(
                f"{final_result['status']} {final_result['terminal_reason']} "
                f"lift={final_result['final_lift_height_m']:.4f} "
                f"stable={final_result['final_grip_stable']} "
                f"hold_slip={final_result['hold_max_slip_score']:.3f}"
            )
            if not bool(args.loop):
                while bool(args.dashboard_window) and dashboard.running:
                    dashboard.update(episode, terminal_reason=final_result["terminal_reason"], force=True)
                break
            episode = EggGentleGraspEpisode(model, data, mujoco, args)
            time.sleep(0.4)
    finally:
        dashboard.close()
    write_trace_csv(trace_path, episode.trace_rows)
    if video_path is not None:
        print(f"Wrote video: {video_path}")
    if trace_path is not None:
        print(f"Wrote trace: {trace_path}")
    return 0 if final_result is None or bool(final_result.get("success", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
