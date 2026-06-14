from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
THIS_DIR = Path(__file__).resolve().parent
DEFAULT_SELECTED = THIS_DIR / "metadata" / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_TRACE_CSV = ROOT / "artifacts" / "demo_review" / "realtime_force_feedback_trace_latest.csv"
DEFAULT_DESKTOP_DEMO_DIR = Path.home() / "Desktop" / "Demos"

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import export_stage4_force_feedback_packets_v0 as packet_export
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import train_stage3_11d_b_event_contact_gated_refine_v0 as event
from external_sensors.mujoco_motor_force_feedback_sensor import (
    MotorForceFeedbackConfig,
    MujocoMotorForceFeedbackSensor,
    summarize_motor_force_feedback_samples,
)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def make_event_args(args: argparse.Namespace) -> argparse.Namespace:
    ev = event.build_parser().parse_args([])
    ev.scene = Path(args.scene)
    ev.selected = Path(args.selected)
    ev.render_best = False
    ev.enable_motor_force_feedback = True
    ev.enable_force_feedback_lift_gate = bool(args.enable_force_feedback_lift_gate)
    ev.force_feedback_enable_preload = bool(args.force_feedback_enable_preload)
    ev.morphology_sample_every = max(1, int(args.morphology_sample_every))
    ev.motor_current_limit_a = float(args.motor_current_limit_a)
    ev.motor_bus_voltage_v = float(args.motor_bus_voltage_v)
    ev.motor_current_noise_a = float(args.motor_current_noise_a)
    ev.motor_feedback_seed = int(args.motor_feedback_seed)
    ev.force_feedback_min_slow_lift_pair_tension_n = float(args.force_feedback_min_slow_lift_pair_tension_n)
    ev.force_feedback_min_hold_pair_tension_n = float(args.force_feedback_min_hold_pair_tension_n)
    ev.force_feedback_min_pair_balance = float(args.force_feedback_min_pair_balance)
    ev.force_feedback_max_pair_iq_a = float(args.force_feedback_max_pair_iq_a)
    ev.capture_dense_sensor_trace = False
    ev.include_frame_state = False
    ev.max_actuators_per_packet = int(args.max_actuators_per_packet)
    ev.skill_id = packet_export.SKILL_ID
    return ev


def load_case(args: argparse.Namespace) -> event.RefineCase:
    case = robustness.selected_case_from_json(Path(args.selected).resolve())
    if args.override_lift_steps is not None:
        case = replace(case, candidate=replace(case.candidate, lift_steps=int(args.override_lift_steps)))
    if args.override_hold_steps is not None:
        case = replace(case, hold_steps=int(args.override_hold_steps))
    return case


def configure_free_camera(model, mujoco, camera, args: argparse.Namespace, initial_ball: np.ndarray) -> None:
    mujoco.mjv_defaultFreeCamera(model, camera)
    camera.lookat[:] = np.asarray(initial_ball, dtype=float) + np.array(
        [float(args.camera_lookat_dx), float(args.camera_lookat_dy), float(args.camera_lookat_dz)]
    )
    camera.distance = float(args.camera_distance)
    camera.azimuth = float(args.camera_azimuth)
    camera.elevation = float(args.camera_elevation)


def setup_viewer_camera(model, data, mujoco, viewer, args: argparse.Namespace, initial_ball: np.ndarray) -> None:
    configure_free_camera(model, mujoco, viewer.cam, args, initial_ball)


class RealtimeForceFeedbackEpisode:
    def __init__(
        self,
        model,
        mujoco,
        case: event.RefineCase,
        args: argparse.Namespace,
        ev_args: argparse.Namespace,
        data=None,
    ):
        self.model = model
        self.mujoco = mujoco
        self.case = case
        self.args = args
        self.ev_args = ev_args
        self.candidate = case.candidate
        self.data = data if data is not None else mujoco.MjData(model)
        self.sample_rate_hz = 1.0 / max(float(model.opt.timestep) * max(1, int(args.sensor_sample_every)), 1e-9)
        self.sequence_id = 0
        self.max_lift = 0.0
        self.max_pen = 0.0
        self.last_frame: dict[str, Any] | None = None
        self.last_packet: dict[str, Any] | None = None
        self.last_phase = "start"
        self.last_phase_step = 0
        self.last_phase_progress = 0.0
        self.packets: list[dict[str, Any]] = []
        self.trace_rows: list[dict[str, Any]] = []
        self.motor_feedback_samples: list[dict[str, Any]] = []
        self.motor_feedback_sensor = MujocoMotorForceFeedbackSensor(
            MotorForceFeedbackConfig(
                torque_constant_nm_per_a=float(ev_args.motor_torque_constant_nm_per_a),
                gear_ratio=float(ev_args.motor_gear_ratio),
                gear_efficiency=float(ev_args.motor_gear_efficiency),
                spool_radius_m=float(ev_args.motor_spool_radius_m),
                current_limit_a=float(ev_args.motor_current_limit_a),
                bus_voltage_v=float(ev_args.motor_bus_voltage_v),
                current_noise_a=float(ev_args.motor_current_noise_a),
                seed=int(ev_args.motor_feedback_seed),
            )
        )
        self._prepare_scene()

    def _prepare_scene(self) -> None:
        model = self.model
        data = self.data
        mujoco = self.mujoco
        self.run_args = event.run_args_for_case(self.ev_args, self.case)
        ball_config = event.broad.configure_ball_model(model, mujoco, self.run_args)
        mujoco.mj_forward(model, data)
        initial_ball = event.broad.ball_position(model, data, mujoco)
        if ball_config.get("configured"):
            initial_ball = initial_ball.copy()
            initial_ball[2] = float(ball_config["floor_z_m"]) + float(ball_config["radius_m"])
        initial_ball = initial_ball.copy()
        initial_ball[0] += float(self.case.ball_offset_x)
        initial_ball[1] += float(self.case.ball_offset_y)
        initial_ball[2] += float(self.case.ball_offset_z)
        data.qpos[:] = model.qpos0
        data.qvel[:] = 0.0
        event.broad.ball_demo.set_ball_pose(model, data, mujoco, initial_ball)
        mujoco.mj_forward(model, data)

        self.initial_ball = initial_ball
        self.names = event.broad.ball_demo.actuator_names(model, mujoco)
        self.default_targets = event.broad.actuated_joint_targets_from_qpos(model, data, mujoco, self.names)
        self.material_changes = event.broad.set_contact_materials(model, mujoco, self.candidate)
        self.ik = event.broad.solve_arm_for_tip_pair(model, mujoco, self.candidate, initial_ball, self.run_args)
        self.targets = event.broad.phase_targets(self.default_targets, self.ik["joints"], self.candidate)
        self.start_targets = copy.deepcopy(self.default_targets)
        if int(self.args.intro_steps) <= 0 and int(self.args.intro_hold_steps) <= 0:
            event.apply_targets(model, data, mujoco, self.names, self.targets["pre"])
        else:
            data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(model, mujoco, self.names, self.start_targets)
            event.broad.ball_demo.set_ball_pose(model, data, mujoco, initial_ball)
        mujoco.mj_forward(model, data)
        self.sample("start", force=True)

    def sample(
        self,
        label: str,
        *,
        phase_step: int = 0,
        phase_progress: float = 0.0,
        force: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not force and self.sequence_id > 0 and phase_step % max(1, int(self.args.sensor_sample_every)) != 0:
            return self.last_frame or {}, self.last_packet or {}
        model = self.model
        data = self.data
        mujoco = self.mujoco
        rows = event.broad.contact_rows(model, data, mujoco)
        morph = event.broad.frame_morphology(rows, self.candidate)
        ball = event.broad.ball_position(model, data, mujoco)
        lift = float(ball[2] - self.initial_ball[2])
        pen = float(max([float(row["penetration"]) for row in rows] + [0.0]))
        self.max_lift = max(self.max_lift, lift)
        self.max_pen = max(self.max_pen, pen)
        feedback = self.motor_feedback_sensor.observe(
            model,
            data,
            mujoco,
            phase=label,
            active_pair=("thumb", self.candidate.active_finger),
        )
        self.motor_feedback_samples.append(feedback)
        frame = {
            "dense_step_index": int(self.sequence_id),
            "label": label,
            "phase_step": int(phase_step),
            "phase_progress": float(phase_progress),
            "time_s": float(data.time),
            "initial_ball": self.initial_ball.copy(),
            "ball_position": ball,
            "lift_m": lift,
            "morphology": morph,
            "max_penetration_m": pen,
            "motor_force_feedback": feedback,
        }
        packet = packet_export.packet_from_frame(
            frame,
            sequence_id=self.sequence_id,
            sample_rate_hz=self.sample_rate_hz,
            case=self.case,
            args=self.ev_args,
        )
        self.packets.append(packet)
        self.trace_rows.append(self.trace_row(frame, packet))
        self.sequence_id += 1
        self.last_frame = frame
        self.last_packet = packet
        self.last_phase = label
        self.last_phase_step = int(phase_step)
        self.last_phase_progress = float(phase_progress)
        return frame, packet

    def trace_row(self, frame: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
        active = packet.get("active_pair", {})
        contact = packet.get("contact", {})
        safety = packet.get("safety", {})
        morph = frame.get("morphology", {})
        return {
            "sequence_id": int(packet.get("sequence_id", 0)),
            "time_s": float(frame.get("time_s", 0.0)),
            "phase": str(frame.get("label", "")),
            "phase_step": int(frame.get("phase_step", -1)),
            "phase_progress": float(frame.get("phase_progress", 0.0)),
            "lift_m": float(frame.get("lift_m", 0.0)),
            "pair_total_tension_n": float(active.get("total_tension_n", 0.0)),
            "pair_balance_ratio": float(active.get("balance_ratio", 0.0)),
            "max_abs_iq_a": float(active.get("max_abs_iq_a", 0.0)),
            "saturation_count": int(active.get("saturation_count", 0)),
            "contact_present": int(bool(contact.get("contact_present", False))),
            "contact_regions": ",".join(str(v) for v in contact.get("contact_regions", [])),
            "slip_risk": float(contact.get("slip_risk", 0.0)),
            "crush_risk": float(contact.get("crush_risk", 0.0)),
            "lift_quality_now": int(bool(contact.get("lift_quality_now", False))),
            "adjust_needed_now": int(bool(contact.get("adjust_needed_now", False))),
            "hold_safe_now": int(bool(contact.get("hold_safe_now", False))),
            "abort_required": int(bool(safety.get("abort_required", False))),
            "hand_contacts": int(as_float(morph.get("hand_contacts"), 0.0)),
            "floor_contacts": int(as_float(morph.get("floor_contacts"), 0.0)),
            "true_two_tip_pinch": int(bool(morph.get("true_two_tip_pinch", False))),
            "wrap_or_support": int(bool(morph.get("wrap_or_support", False))),
            "max_penetration_m": float(frame.get("max_penetration_m", 0.0)),
        }

    def overlay_texts(self, terminal_reason: str = "") -> list[tuple[Any, Any, str, str]]:
        mujoco = self.mujoco
        frame = self.last_frame or {}
        packet = self.last_packet or {}
        active = packet.get("active_pair", {})
        contact = packet.get("contact", {})
        safety = packet.get("safety", {})
        morph = frame.get("morphology", {})
        lift = float(frame.get("lift_m", 0.0))
        tension = float(active.get("total_tension_n", 0.0))
        balance = float(active.get("balance_ratio", 0.0))
        max_iq = float(active.get("max_abs_iq_a", 0.0))
        slip = float(contact.get("slip_risk", 0.0))
        crush = float(contact.get("crush_risk", 0.0))
        lift_goal = float(self.case.min_lift_height)
        lift_tension_threshold = float(self.ev_args.force_feedback_min_slow_lift_pair_tension_n)
        hold_tension_threshold = float(self.ev_args.force_feedback_min_hold_pair_tension_n)
        current_limit = float(self.ev_args.motor_current_limit_a)
        left = "\n".join(
            [
                "Stage3 force-feedback realtime demo",
                f"phase: {self.last_phase}  step: {self.last_phase_step}  sim: {float(self.data.time):.2f}s",
                f"case: {self.case.name[:48]}",
                f"active pair: thumb + {self.candidate.active_finger}",
                f"lift height: {lift:.4f} m  goal >= {lift_goal:.4f} m",
                f"pair tension: {tension:.2f} N  lift gate >= {lift_tension_threshold:.2f} N",
                f"hold tension gate: >= {hold_tension_threshold:.2f} N",
                f"pair balance: {balance:.3f}  gate >= {float(self.ev_args.force_feedback_min_pair_balance):.3f}",
                f"motor current: {max_iq:.2f} A  limit <= {current_limit:.2f} A",
            ]
        )
        right = "\n".join(
            [
                "Realtime sensor packet",
                f"seq: {int(packet.get('sequence_id', 0))}  rate: {float(packet.get('sample_rate_hz', 0.0)):.1f} Hz",
                f"contact: {bool(contact.get('contact_present', False))}  regions: {','.join(contact.get('contact_regions', [])) or '-'}",
                f"two_tip: {bool(morph.get('true_two_tip_pinch', False))}  floor: {int(as_float(morph.get('floor_contacts'), 0.0))}",
                f"slip risk: {slip:.2f}  crush risk: {crush:.2f}",
                f"pen: {float(frame.get('max_penetration_m', 0.0)):.5f} m",
                f"lift_ok: {bool(contact.get('lift_quality_now', False))}  hold_safe: {bool(contact.get('hold_safe_now', False))}",
                f"adjust_needed: {bool(contact.get('adjust_needed_now', False))}  current_fault: {bool(safety.get('fault_active', False))}",
                terminal_reason,
            ]
        )
        return [
            (mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_TOPLEFT, left, ""),
            (mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_TOPRIGHT, right, ""),
        ]

    def sync_viewer(
        self,
        viewer,
        *,
        phase: str,
        phase_step: int,
        phase_progress: float,
        terminal_reason: str = "",
        force_sample: bool = False,
    ) -> bool:
        already_sampled = self.last_phase == phase and self.last_phase_step == int(phase_step)
        if (force_sample or phase_step % max(1, int(self.args.sensor_sample_every)) == 0) and not already_sampled:
            self.sample(phase, phase_step=phase_step, phase_progress=phase_progress, force=True)
        if viewer is None:
            return True
        dashboard_update = getattr(viewer, "update_dashboard", None)
        if callable(dashboard_update):
            return bool(dashboard_update(self, terminal_reason=terminal_reason))
        if not viewer.is_running():
            return False
        viewer.set_texts(self.overlay_texts(terminal_reason))
        viewer.sync()
        if float(self.args.speed) > 0.0:
            time.sleep(float(self.model.opt.timestep) / max(float(self.args.speed), 1e-6))
        return viewer.is_running()

    def pair_force_ok(self, frame: dict[str, Any], phase: str) -> bool:
        if not bool(self.ev_args.enable_force_feedback_lift_gate):
            return True
        pair = frame.get("motor_force_feedback", {}).get("active_pair", {})
        min_tension = (
            float(self.ev_args.force_feedback_min_hold_pair_tension_n)
            if phase == "hold"
            else float(self.ev_args.force_feedback_min_slow_lift_pair_tension_n)
        )
        return bool(
            pair.get("configured", False)
            and float(pair.get("total_tendon_tension_n", 0.0)) >= min_tension
            and float(pair.get("balance_ratio", 0.0)) >= float(self.ev_args.force_feedback_min_pair_balance)
            and float(pair.get("max_abs_iq_a", 0.0)) <= float(self.ev_args.force_feedback_max_pair_iq_a)
            and int(pair.get("saturated_actuator_count", 0)) == 0
        )

    def step_fixed_phase(self, phase: str, start: dict[str, float], end: dict[str, float], steps: int, viewer) -> bool:
        for idx in range(max(1, int(steps))):
            alpha = idx / max(1, int(steps) - 1)
            event.step_toward(self.model, self.data, self.mujoco, self.names, start, end, alpha)
            if not self.sync_viewer(viewer, phase=phase, phase_step=idx, phase_progress=alpha):
                return False
        return True

    def run(self, viewer=None) -> dict[str, Any]:
        for idx in range(max(0, int(self.args.intro_hold_steps))):
            self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(
                self.model, self.mujoco, self.names, self.start_targets
            )
            self.mujoco.mj_step(self.model, self.data)
            progress = idx / max(1, int(self.args.intro_hold_steps) - 1)
            if not self.sync_viewer(viewer, phase="initial_vertical_hold", phase_step=idx, phase_progress=progress):
                return self.summary(False, "viewer_closed")

        for idx in range(max(0, int(self.args.intro_steps))):
            alpha = idx / max(1, int(self.args.intro_steps) - 1)
            event.step_toward(self.model, self.data, self.mujoco, self.names, self.start_targets, self.targets["pre"], alpha)
            if not self.sync_viewer(viewer, phase="initial_to_grasp_pose", phase_step=idx, phase_progress=alpha):
                return self.summary(False, "viewer_closed")

        fixed_phases = [
            ("approach", self.targets["pre"], self.targets["approach"], int(self.ev_args.approach_steps)),
            ("preshape", self.targets["approach"], self.targets["preshape"], int(self.ev_args.preshape_steps)),
            ("pinch_close", self.targets["preshape"], self.targets["close"], int(self.ev_args.close_steps)),
        ]
        for phase, start, end, steps in fixed_phases:
            if not self.step_fixed_phase(phase, start, end, steps, viewer):
                return self.summary(False, "viewer_closed")

        contact_gate_success = False
        contact_gate_step = None
        contact_gate_frames: list[dict[str, Any]] = []
        consecutive_contact_samples = 0
        for idx in range(max(1, int(self.ev_args.contact_gate_max_steps))):
            self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(
                self.model, self.mujoco, self.names, self.targets["close"]
            )
            self.mujoco.mj_step(self.model, self.data)
            progress = idx / max(1, int(self.ev_args.contact_gate_max_steps) - 1)
            force_sample = idx % max(1, int(self.ev_args.morphology_sample_every)) == 0
            if force_sample:
                frame, _packet = self.sample("contact_gate", phase_step=idx, phase_progress=progress, force=True)
                morph = frame["morphology"]
                contact_gate_frames.append(morph)
                consecutive_contact_samples = consecutive_contact_samples + 1 if bool(morph.get("true_two_tip_pinch", False)) else 0
                if consecutive_contact_samples >= int(self.ev_args.contact_gate_required_samples):
                    contact_gate_success = True
                    contact_gate_step = idx
                    if not self.sync_viewer(viewer, phase="contact_gate", phase_step=idx, phase_progress=progress):
                        return self.summary(False, "viewer_closed")
                    break
            if not self.sync_viewer(viewer, phase="contact_gate", phase_step=idx, phase_progress=progress):
                return self.summary(False, "viewer_closed")

        if contact_gate_success:
            for idx in range(max(0, int(self.ev_args.post_contact_settle_steps))):
                self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(
                    self.model, self.mujoco, self.names, self.targets["close"]
                )
                self.mujoco.mj_step(self.model, self.data)
                progress = idx / max(1, int(self.ev_args.post_contact_settle_steps) - 1)
                if not self.sync_viewer(viewer, phase="post_contact_settle", phase_step=idx, phase_progress=progress):
                    return self.summary(False, "viewer_closed")

        lift_frames: list[dict[str, Any]] = []
        lift_lifts: list[float] = []
        lift_break_reason = "not_started"
        last_lift_target = copy.deepcopy(self.targets["close"])
        consecutive_lifted_tip_samples = 0
        if contact_gate_success or not bool(self.ev_args.require_contact_gate):
            lift_break_reason = "lift_steps_exhausted"
            for idx in range(max(1, int(self.candidate.lift_steps))):
                alpha = idx / max(1, int(self.candidate.lift_steps) - 1)
                last_lift_target = event.step_toward(
                    self.model,
                    self.data,
                    self.mujoco,
                    self.names,
                    self.targets["close"],
                    self.targets["lift"],
                    alpha,
                )
                if idx % max(1, int(self.ev_args.morphology_sample_every)) == 0:
                    frame, _packet = self.sample("slow_lift", phase_step=idx, phase_progress=alpha, force=True)
                    morph = frame["morphology"]
                    lift_frames.append(morph)
                    lift_lifts.append(float(frame["lift_m"]))
                    lifted_tip = bool(
                        float(frame["lift_m"]) >= float(self.case.min_lift_height)
                        and bool(morph.get("true_two_tip_pinch", False))
                        and int(morph.get("floor_contacts", 0)) == 0
                        and self.pair_force_ok(frame, "slow_lift")
                    )
                    consecutive_lifted_tip_samples = consecutive_lifted_tip_samples + 1 if lifted_tip else 0
                    if (
                        idx >= int(self.ev_args.min_lift_steps_before_hold)
                        and consecutive_lifted_tip_samples >= int(self.ev_args.lifted_contact_required_samples)
                    ):
                        lift_break_reason = "lifted_tip_window_met"
                        if not self.sync_viewer(viewer, phase="slow_lift", phase_step=idx, phase_progress=alpha):
                            return self.summary(False, "viewer_closed")
                        break
                if not self.sync_viewer(viewer, phase="slow_lift", phase_step=idx, phase_progress=alpha):
                    return self.summary(False, "viewer_closed")

        hold_frames: list[dict[str, Any]] = []
        hold_lifts: list[float] = []
        hold_break_reason = "not_started"
        consecutive_hold_samples = 0
        if lift_break_reason != "not_started":
            hold_break_reason = "hold_steps_exhausted"
            for idx in range(max(1, int(self.case.hold_steps))):
                self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(self.model, self.mujoco, self.names, last_lift_target)
                self.mujoco.mj_step(self.model, self.data)
                progress = idx / max(1, int(self.case.hold_steps) - 1)
                if idx % max(1, int(self.ev_args.morphology_sample_every)) == 0:
                    frame, _packet = self.sample("hold", phase_step=idx, phase_progress=progress, force=True)
                    morph = frame["morphology"]
                    hold_frames.append(morph)
                    hold_lifts.append(float(frame["lift_m"]))
                    stable = bool(
                        float(frame["lift_m"]) >= float(self.case.min_lift_height)
                        and bool(morph.get("true_two_tip_pinch", False))
                        and int(morph.get("floor_contacts", 0)) == 0
                        and not bool(morph.get("wrap_or_support", False))
                        and self.pair_force_ok(frame, "hold")
                    )
                    consecutive_hold_samples = consecutive_hold_samples + 1 if stable else 0
                    if (
                        idx >= int(self.ev_args.min_hold_steps_before_release)
                        and consecutive_hold_samples >= int(self.ev_args.hold_release_required_samples)
                    ):
                        hold_break_reason = "stable_hold_window_met"
                        if not self.sync_viewer(viewer, phase="hold", phase_step=idx, phase_progress=progress):
                            return self.summary(False, "viewer_closed")
                        break
                if not self.sync_viewer(viewer, phase="hold", phase_step=idx, phase_progress=progress):
                    return self.summary(False, "viewer_closed")

        release_target = {**last_lift_target, **event.broad.hand_targets(self.candidate, open_hand=True)}
        for idx in range(max(1, int(self.ev_args.release_steps))):
            alpha = idx / max(1, int(self.ev_args.release_steps) - 1)
            event.step_toward(self.model, self.data, self.mujoco, self.names, last_lift_target, release_target, alpha)
            if not self.sync_viewer(viewer, phase="release_open", phase_step=idx, phase_progress=alpha):
                return self.summary(False, "viewer_closed")

        for idx in range(max(1, int(self.ev_args.release_settle_steps))):
            self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(self.model, self.mujoco, self.names, release_target)
            self.mujoco.mj_step(self.model, self.data)
            progress = idx / max(1, int(self.ev_args.release_settle_steps) - 1)
            if not self.sync_viewer(viewer, phase="release_settle", phase_step=idx, phase_progress=progress):
                return self.summary(False, "viewer_closed")

        final_frame, _packet = self.sample("final", force=True)
        final_rows = event.broad.contact_rows(self.model, self.data, self.mujoco)
        final_morph = event.broad.frame_morphology(final_rows, self.candidate)
        hold_summary = event.broad.summarize_frames(hold_frames)
        lift_summary = event.broad.summarize_frames(lift_frames)
        gate_summary = event.broad.summarize_frames(contact_gate_frames)
        final_ball = event.broad.ball_position(self.model, self.data, self.mujoco)
        hold_lift_max = float(max(hold_lifts) if hold_lifts else 0.0)
        release_success = bool(
            final_morph["floor_contacts"] > 0
            and final_morph["hand_contacts"] == 0
            and abs(float(final_ball[2] - self.initial_ball[2])) <= float(self.ev_args.final_height_tolerance)
        )
        lift_success = bool(
            hold_lift_max >= float(self.case.min_lift_height)
            and hold_summary["floor_contact_fraction"] <= float(self.ev_args.max_hold_floor_contact_fraction)
        )
        true_pinch_success = bool(
            contact_gate_success
            and lift_success
            and hold_summary["true_two_tip_pinch_fraction"] >= float(self.ev_args.min_true_pinch_fraction)
            and hold_summary["wrap_frame_fraction"] <= float(self.ev_args.max_wrap_fraction)
            and hold_summary["non_tip_contact_ratio_mean"] <= float(self.ev_args.max_non_tip_ratio)
        )
        success = bool(true_pinch_success and release_success)
        if success:
            terminal_reason = "success_event_contact_gated_true_pinch_release_ball"
        elif not contact_gate_success:
            terminal_reason = "contact_gate_failed"
        elif not lift_success:
            terminal_reason = "lift_gate_failed"
        elif not true_pinch_success:
            terminal_reason = "true_pinch_morphology_gate_failed"
        elif not release_success:
            terminal_reason = "release_gate_failed"
        else:
            terminal_reason = "unknown"
        if viewer is not None:
            end_time = time.time() + max(0.0, float(self.args.hold_final_seconds))
            dashboard_update = getattr(viewer, "update_dashboard", None)
            if callable(dashboard_update):
                while getattr(viewer, "running", False) and time.time() < end_time:
                    dashboard_update(self, terminal_reason=terminal_reason)
            else:
                while viewer.is_running() and time.time() < end_time:
                    viewer.set_texts(self.overlay_texts(terminal_reason))
                    viewer.sync()
                    time.sleep(0.05)
        return {
            "status": "PASS" if success else "FAIL",
            "success": bool(success),
            "terminal_reason": terminal_reason,
            "contact_gate_success": bool(contact_gate_success),
            "contact_gate_step": contact_gate_step,
            "lift_success": bool(lift_success),
            "true_pinch_success": bool(true_pinch_success),
            "release_success": bool(release_success),
            "lift_break_reason": lift_break_reason,
            "hold_break_reason": hold_break_reason,
            "max_lift_m": float(self.max_lift),
            "hold_lift_m_max": float(hold_lift_max),
            "max_penetration_m": float(self.max_pen),
            "contact_gate_morphology": gate_summary,
            "hold_morphology": hold_summary,
            "lift_morphology": lift_summary,
            "final_morphology": final_morph,
            "final_sample": final_frame,
            "final_ball": final_ball,
            "case": {
                "name": self.case.name,
                "candidate": asdict(self.candidate),
                "hold_steps": int(self.case.hold_steps),
                "min_lift_height": float(self.case.min_lift_height),
            },
            "motor_force_feedback_summary": summarize_motor_force_feedback_samples(self.motor_feedback_samples),
        }

    def summary(self, success: bool, terminal_reason: str) -> dict[str, Any]:
        return {
            "status": "PASS" if success else "FAIL",
            "success": bool(success),
            "terminal_reason": terminal_reason,
            "max_lift_m": float(self.max_lift),
            "max_penetration_m": float(self.max_pen),
            "case": {"name": self.case.name, "candidate": asdict(self.candidate)},
            "motor_force_feedback_summary": summarize_motor_force_feedback_samples(self.motor_feedback_samples),
        }


class RealtimeDashboard:
    def __init__(
        self,
        model,
        mujoco,
        args: argparse.Namespace,
        initial_ball: np.ndarray,
        *,
        show_window: bool = True,
        video_path: Path | None = None,
    ):
        import cv2

        self.cv2 = cv2
        self.model = model
        self.mujoco = mujoco
        self.args = args
        self.show_window = bool(show_window)
        self.width = int(args.dashboard_width)
        self.render_height = int(args.dashboard_render_height)
        self.plot_height = int(args.dashboard_plot_height)
        self.window_name = "Stage3 force-feedback realtime dashboard"
        self.renderer = mujoco.Renderer(model, width=self.width, height=self.render_height)
        self.camera = mujoco.MjvCamera()
        configure_free_camera(model, mujoco, self.camera, args, initial_ball)
        self.running = True
        self.tick = 0
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

    def update_dashboard(self, episode: RealtimeForceFeedbackEpisode, *, terminal_reason: str = "") -> bool:
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
            self.tick % max(1, int(self.args.dashboard_frame_every)) == 0 or bool(terminal_reason)
        )
        record_every = max(1, int(round(float(self.args.dashboard_frame_every) * float(self.args.video_speedup))))
        record_due = self.video_writer is not None and (
            self.tick % record_every == 0 or (bool(terminal_reason) and not self.terminal_recorded)
        )
        if not show_due and not record_due:
            return True

        self.renderer.update_scene(episode.data, camera=self.camera)
        render_rgb = self.renderer.render()
        render_bgr = self.cv2.cvtColor(render_rgb, self.cv2.COLOR_RGB2BGR)
        dashboard = self.compose_frame(episode, render_bgr, terminal_reason)
        if record_due and self.video_writer is not None:
            if terminal_reason and not self.terminal_recorded:
                final_frames = max(1, int(round(float(self.args.video_fps) * float(self.args.video_final_hold_seconds))))
                for _idx in range(final_frames):
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

    def compose_frame(
        self,
        episode: RealtimeForceFeedbackEpisode,
        render_bgr: np.ndarray,
        terminal_reason: str,
    ) -> np.ndarray:
        cv2 = self.cv2
        if render_bgr.shape[1] != self.width or render_bgr.shape[0] != self.render_height:
            render_bgr = cv2.resize(render_bgr, (self.width, self.render_height), interpolation=cv2.INTER_AREA)
        top = render_bgr.copy()
        self.draw_status_overlay(top, episode, terminal_reason)
        plot = np.full((self.plot_height, self.width, 3), (18, 18, 18), dtype=np.uint8)
        self.draw_curve_panel(plot, episode)
        return np.vstack([top, plot])

    def draw_status_overlay(
        self,
        image: np.ndarray,
        episode: RealtimeForceFeedbackEpisode,
        terminal_reason: str,
    ) -> None:
        cv2 = self.cv2
        frame = episode.last_frame or {}
        packet = episode.last_packet or {}
        active = packet.get("active_pair", {})
        contact = packet.get("contact", {})
        lines = [
            "MuJoCo realtime demo: initial posture -> grasp -> lift -> release",
            f"phase {episode.last_phase}   sim {float(episode.data.time):.2f}s   seq {int(packet.get('sequence_id', 0))}",
            f"lift {float(frame.get('lift_m', 0.0)):.4f} m / goal {float(episode.case.min_lift_height):.4f} m",
            f"pair tension {float(active.get('total_tension_n', 0.0)):.2f} N   current {float(active.get('max_abs_iq_a', 0.0)):.2f} A",
            f"contact {bool(contact.get('contact_present', False))}   lift_ok {bool(contact.get('lift_quality_now', False))}   hold_safe {bool(contact.get('hold_safe_now', False))}",
        ]
        if terminal_reason:
            lines.append(terminal_reason)
        x, y = 18, 30
        line_h = 26
        box_h = 16 + line_h * len(lines)
        overlay = image.copy()
        cv2.rectangle(overlay, (10, 10), (760, 10 + box_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.68, image, 0.32, 0.0, image)
        for idx, text in enumerate(lines):
            color = (255, 255, 255) if idx != 0 else (90, 220, 255)
            cv2.putText(image, text, (x, y + idx * line_h), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 1, cv2.LINE_AA)

    def draw_curve_panel(self, image: np.ndarray, episode: RealtimeForceFeedbackEpisode) -> None:
        rows = episode.trace_rows
        cv2 = self.cv2
        title = "Synchronized realtime sensor curves: same MuJoCo ticks as hand motion"
        cv2.putText(image, title, (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.66, (230, 230, 230), 1, cv2.LINE_AA)
        if len(rows) < 2:
            return
        now = float(rows[-1]["time_s"])
        span = max(0.5, float(self.args.plot_seconds))
        visible = [row for row in rows if float(row["time_s"]) >= now - span]
        if len(visible) < 2:
            visible = rows[-2:]
        lane_top = 45
        lane_h = max(48, (self.plot_height - lane_top - 12) // 4)
        lanes = [
            ("pair_total_tension_n", "pair tension", "N", (0, 210, 255), None, None),
            ("max_abs_iq_a", "motor current", "A", (255, 210, 0), 0.0, None),
            ("pair_balance_ratio", "pair balance", "", (80, 220, 120), 0.0, 1.0),
            ("lift_m", "lift height", "m", (120, 160, 255), 0.0, max(float(episode.case.min_lift_height) * 1.35, 0.02)),
        ]
        for lane_idx, (field, label, unit, color, ymin, ymax) in enumerate(lanes):
            top = lane_top + lane_idx * lane_h
            self.draw_lane(image, visible, field, label, unit, color, top, lane_h - 8, ymin, ymax)

    def draw_lane(
        self,
        image: np.ndarray,
        rows: list[dict[str, Any]],
        field: str,
        label: str,
        unit: str,
        color: tuple[int, int, int],
        top: int,
        height: int,
        ymin: float | None,
        ymax: float | None,
    ) -> None:
        cv2 = self.cv2
        left = 165
        right = self.width - 24
        bottom = top + height
        plot_h = max(8, height - 20)
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
        cv2.line(image, (left, bottom - 14), (right, bottom - 14), (80, 80, 80), 1)
        cv2.line(image, (left, top + 6), (left, bottom - 14), (80, 80, 80), 1)
        pts: list[tuple[int, int]] = []
        for t, value in zip(times, values):
            x = int(left + (t - t0) / (t1 - t0) * max(1, right - left))
            y = int((bottom - 14) - (value - ymin) / (ymax - ymin) * max(1, plot_h))
            pts.append((x, int(np.clip(y, top + 6, bottom - 14))))
        for a, b in zip(pts, pts[1:]):
            cv2.line(image, a, b, color, 2, cv2.LINE_AA)
        current = values[-1]
        phase = str(rows[-1].get("phase", ""))
        cv2.putText(
            image,
            f"{label}: {current:.3f} {unit}".strip(),
            (18, top + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            color,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            f"range {ymin:.2f}..{ymax:.2f}",
            (18, top + 44),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (165, 165, 165),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            phase[:28],
            (right - 220, top + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (185, 185, 185),
            1,
            cv2.LINE_AA,
        )


def write_trace_csv(path: Path | None, rows: list[dict[str, Any]]) -> None:
    if path is None or not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a MuJoCo-only Stage3 true-pinch demo with synchronized realtime force-feedback HUD."
    )
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--speed", type=float, default=0.75)
    parser.add_argument("--loop", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--dashboard-window", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--record-video", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DESKTOP_DEMO_DIR)
    parser.add_argument("--video-output", type=Path, default=None)
    parser.add_argument("--video-fps", type=float, default=30.0)
    parser.add_argument("--video-speedup", type=float, default=3.0)
    parser.add_argument("--video-final-hold-seconds", type=float, default=1.0)
    parser.add_argument("--headless-smoke", action="store_true")
    parser.add_argument("--show-ui", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--sensor-sample-every", type=int, default=5)
    parser.add_argument("--morphology-sample-every", type=int, default=5)
    parser.add_argument("--intro-hold-steps", type=int, default=80)
    parser.add_argument("--intro-steps", type=int, default=260)
    parser.add_argument("--hold-final-seconds", type=float, default=4.0)
    parser.add_argument("--trace-csv", type=Path, default=DEFAULT_TRACE_CSV)
    parser.add_argument("--no-trace-csv", action="store_true")
    parser.add_argument("--max-actuators-per-packet", type=int, default=8)
    parser.add_argument("--motor-current-limit-a", type=float, default=4.0)
    parser.add_argument("--motor-bus-voltage-v", type=float, default=24.0)
    parser.add_argument("--motor-current-noise-a", type=float, default=0.025)
    parser.add_argument("--motor-feedback-seed", type=int, default=20260611)
    parser.add_argument("--enable-force-feedback-lift-gate", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-enable-preload", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-min-slow-lift-pair-tension-n", type=float, default=4.0)
    parser.add_argument("--force-feedback-min-hold-pair-tension-n", type=float, default=2.0)
    parser.add_argument("--force-feedback-min-pair-balance", type=float, default=0.01)
    parser.add_argument("--force-feedback-max-pair-iq-a", type=float, default=4.0)
    parser.add_argument("--camera-distance", type=float, default=0.85)
    parser.add_argument("--camera-azimuth", type=float, default=160.0)
    parser.add_argument("--camera-elevation", type=float, default=-18.0)
    parser.add_argument("--camera-lookat-dx", type=float, default=0.00)
    parser.add_argument("--camera-lookat-dy", type=float, default=-0.01)
    parser.add_argument("--camera-lookat-dz", type=float, default=0.080)
    parser.add_argument("--dashboard-width", type=int, default=1280)
    parser.add_argument("--dashboard-render-height", type=int, default=720)
    parser.add_argument("--dashboard-plot-height", type=int, default=360)
    parser.add_argument("--dashboard-frame-every", type=int, default=3)
    parser.add_argument("--plot-seconds", type=float, default=4.0)
    parser.add_argument("--override-lift-steps", type=int, default=None)
    parser.add_argument("--override-hold-steps", type=int, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    args.selected = Path(args.selected).resolve()
    if not args.selected.exists():
        raise FileNotFoundError(args.selected)

    ev_args = make_event_args(args)
    case = load_case(args)
    args.output_dir = Path(args.output_dir).expanduser().resolve()
    if bool(args.record_video):
        args.output_dir.mkdir(parents=True, exist_ok=True)
        if args.video_output is None:
            speed_tag = str(float(args.video_speedup)).replace(".", "p")
            args.video_output = args.output_dir / f"stage3_force_feedback_realtime_dashboard_x{speed_tag}.mp4"
        else:
            args.video_output = Path(args.video_output).expanduser().resolve()
        if Path(args.trace_csv) == DEFAULT_TRACE_CSV:
            args.trace_csv = args.output_dir / "stage3_force_feedback_realtime_trace.csv"

    def run_one(viewer=None) -> tuple[RealtimeForceFeedbackEpisode, dict[str, Any]]:
        model = mujoco.MjModel.from_xml_path(str(scene))
        episode = RealtimeForceFeedbackEpisode(model, mujoco, case, args, ev_args)
        if viewer is not None:
            setup_viewer_camera(model, episode.data, mujoco, viewer, args, episode.initial_ball)
        result = episode.run(viewer=viewer)
        return episode, result

    if bool(args.headless_smoke):
        episode, result = run_one(viewer=None)
        trace_path = None if bool(args.no_trace_csv) else Path(args.trace_csv)
        write_trace_csv(trace_path, episode.trace_rows)
        active_pair_max_iq = max([float(row.get("max_abs_iq_a", 0.0)) for row in episode.trace_rows] + [0.0])
        active_pair_max_tension = max([float(row.get("pair_total_tension_n", 0.0)) for row in episode.trace_rows] + [0.0])
        print(
            "Stage3 realtime force-feedback viewer smoke: "
            f"status={result['status']} reason={result['terminal_reason']} "
            f"lift={float(result.get('hold_lift_m_max', result.get('max_lift_m', 0.0))):.4f} "
            f"release={bool(result.get('release_success', False))} "
            f"active_pair_max_iq={active_pair_max_iq:.3f} "
            f"active_pair_max_tension={active_pair_max_tension:.3f} "
            f"trace_csv={str(trace_path) if trace_path else 'disabled'}"
        )
        return 0 if bool(result.get("success")) else 1

    if bool(args.dashboard_window) or bool(args.record_video):
        if bool(args.record_video):
            print("Rendering Stage3 realtime force-feedback dashboard video.")
            print(f"Video output: {args.video_output}")
            print(f"Trace CSV: {args.trace_csv if not bool(args.no_trace_csv) else 'disabled'}")
        else:
            print("Opening Stage3 realtime force-feedback dashboard.")
        print(f"Scene: {scene}")
        print(f"Selected case: {args.selected}")
        if bool(args.dashboard_window):
            print("Top = MuJoCo render; bottom = live force-feedback curves. Press Q or Esc to stop.")
        else:
            print("Top = MuJoCo render; bottom = live force-feedback curves.")
        final_result: dict[str, Any] | None = None
        final_episode: RealtimeForceFeedbackEpisode | None = None
        model = mujoco.MjModel.from_xml_path(str(scene))
        data = mujoco.MjData(model)
        episode = RealtimeForceFeedbackEpisode(model, mujoco, case, args, ev_args, data=data)
        dashboard = RealtimeDashboard(
            model,
            mujoco,
            args,
            episode.initial_ball,
            show_window=bool(args.dashboard_window),
            video_path=Path(args.video_output) if bool(args.record_video) else None,
        )
        try:
            while dashboard.running:
                result = episode.run(viewer=dashboard)
                final_result = result
                final_episode = episode
                print(
                    f"{result['status']} {result['terminal_reason']} "
                    f"lift={float(result.get('hold_lift_m_max', 0.0)):.4f} "
                    f"release={bool(result.get('release_success', False))}"
                )
                if not bool(args.loop):
                    while dashboard.running:
                        dashboard.update_dashboard(episode, terminal_reason=result.get("terminal_reason", ""))
                    break
                episode = RealtimeForceFeedbackEpisode(model, mujoco, case, args, ev_args, data=data)
                time.sleep(0.4)
        finally:
            dashboard.close()
        if final_episode is not None:
            trace_path = None if bool(args.no_trace_csv) else Path(args.trace_csv)
            write_trace_csv(trace_path, final_episode.trace_rows)
            if final_result is not None and not bool(args.record_video):
                print(json.dumps(packet_export.json_ready(final_result), indent=2, ensure_ascii=False))
        if bool(args.record_video):
            print(f"Wrote video: {args.video_output}")
        return 0 if final_result is None or bool(final_result.get("success", False)) else 1

    import mujoco.viewer

    print("Opening Stage3 realtime force-feedback MuJoCo demo.")
    print(f"Scene: {scene}")
    print(f"Selected case: {args.selected}")
    print("HUD is sampled from the same MuJoCo ticks as the hand motion. Close the viewer to stop.")
    final_result: dict[str, Any] | None = None
    final_episode: RealtimeForceFeedbackEpisode | None = None
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    episode = RealtimeForceFeedbackEpisode(model, mujoco, case, args, ev_args, data=data)
    with mujoco.viewer.launch_passive(
        model,
        data,
        show_left_ui=bool(args.show_ui),
        show_right_ui=bool(args.show_ui),
    ) as viewer:
        while viewer.is_running():
            setup_viewer_camera(model, episode.data, mujoco, viewer, args, episode.initial_ball)
            result = episode.run(viewer=viewer)
            final_result = result
            final_episode = episode
            print(
                f"{result['status']} {result['terminal_reason']} "
                f"lift={float(result.get('hold_lift_m_max', 0.0)):.4f} "
                f"release={bool(result.get('release_success', False))}"
            )
            if not bool(args.loop):
                while viewer.is_running():
                    viewer.set_texts(episode.overlay_texts(result.get("terminal_reason", "")))
                    viewer.sync()
                    time.sleep(0.05)
                break
            episode = RealtimeForceFeedbackEpisode(model, mujoco, case, args, ev_args, data=data)
            time.sleep(0.4)

    if final_episode is not None:
        trace_path = None if bool(args.no_trace_csv) else Path(args.trace_csv)
        write_trace_csv(trace_path, final_episode.trace_rows)
        if final_result is not None:
            print(json.dumps(packet_export.json_ready(final_result), indent=2, ensure_ascii=False))
    return 0 if final_result is None or bool(final_result.get("success", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
