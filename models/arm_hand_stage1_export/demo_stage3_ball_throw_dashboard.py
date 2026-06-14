from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import demo_stage3_force_feedback_realtime_viewer as base

event = base.event
packet_export = base.packet_export
summarize_motor_force_feedback_samples = base.summarize_motor_force_feedback_samples

DEFAULT_TRACE_CSV = base.ROOT / "artifacts" / "demo_review" / "stage3_ball_throw_trace_latest.csv"


class BallThrowEpisode(base.RealtimeForceFeedbackEpisode):
    def __init__(self, *args, **kwargs):
        self.release_ball_position: np.ndarray | None = None
        self.release_time_s: float | None = None
        self.max_ball_xy_distance_m = 0.0
        self.max_ball_speed_mps = 0.0
        self.max_post_release_xy_distance_m = 0.0
        self.max_post_release_height_gain_m = 0.0
        self.showcase_impulse_applied = False
        super().__init__(*args, **kwargs)

    def ball_velocity(self) -> np.ndarray:
        jid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
        if jid < 0:
            return np.zeros(3, dtype=float)
        dadr = int(self.model.jnt_dofadr[jid])
        return np.asarray(self.data.qvel[dadr : dadr + 3], dtype=float).copy()

    def clamp_joint_target(self, joint: str, value: float) -> float:
        jid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, joint)
        if jid < 0:
            return float(value)
        lo, hi = (float(v) for v in self.model.jnt_range[jid])
        return float(np.clip(float(value), lo, hi))

    def target_with_arm_deltas(self, target: dict[str, float], deltas: dict[str, float]) -> dict[str, float]:
        out = copy.deepcopy(target)
        for joint, delta in deltas.items():
            out[joint] = self.clamp_joint_target(joint, float(out.get(joint, 0.0)) + float(delta))
        return out

    def trace_row(self, frame: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
        row = super().trace_row(frame, packet)
        ball = np.asarray(frame.get("ball_position", self.initial_ball), dtype=float)
        initial = np.asarray(frame.get("initial_ball", self.initial_ball), dtype=float)
        velocity = self.ball_velocity()
        xy_distance = float(np.linalg.norm(ball[:2] - initial[:2]))
        speed = float(np.linalg.norm(velocity))
        self.max_ball_xy_distance_m = max(self.max_ball_xy_distance_m, xy_distance)
        self.max_ball_speed_mps = max(self.max_ball_speed_mps, speed)
        post_release_xy = 0.0
        post_release_height_gain = 0.0
        if self.release_ball_position is not None:
            rel = np.asarray(self.release_ball_position, dtype=float)
            post_release_xy = float(np.linalg.norm(ball[:2] - rel[:2]))
            post_release_height_gain = float(ball[2] - rel[2])
            self.max_post_release_xy_distance_m = max(self.max_post_release_xy_distance_m, post_release_xy)
            self.max_post_release_height_gain_m = max(self.max_post_release_height_gain_m, post_release_height_gain)
        row.update(
            {
                "ball_x_m": float(ball[0]),
                "ball_y_m": float(ball[1]),
                "ball_z_m": float(ball[2]),
                "ball_vx_mps": float(velocity[0]),
                "ball_vy_mps": float(velocity[1]),
                "ball_vz_mps": float(velocity[2]),
                "ball_speed_mps": speed,
                "ball_xy_distance_m": xy_distance,
                "post_release_xy_distance_m": post_release_xy,
                "post_release_height_gain_m": post_release_height_gain,
                "showcase_impulse_applied": int(bool(self.showcase_impulse_applied)),
            }
        )
        return row

    def mark_release(self) -> None:
        if self.release_ball_position is None:
            self.release_ball_position = event.broad.ball_position(self.model, self.data, self.mujoco)
            self.release_time_s = float(self.data.time)

    def apply_showcase_impulse_once(self) -> None:
        if self.showcase_impulse_applied or not bool(self.args.showcase_impulse):
            return
        jid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
        if jid < 0:
            return
        dadr = int(self.model.jnt_dofadr[jid])
        self.data.qvel[dadr : dadr + 3] += np.asarray(
            [float(self.args.throw_impulse_vx), float(self.args.throw_impulse_vy), float(self.args.throw_impulse_vz)],
            dtype=float,
        )
        self.showcase_impulse_applied = True

    def run_throw_swing(self, start: dict[str, float], end: dict[str, float], viewer) -> bool:
        open_hand = event.broad.hand_targets(self.candidate, open_hand=True)
        close_hand = event.broad.hand_targets(self.candidate, open_hand=False)
        steps = max(1, int(self.args.throw_swing_steps))
        release_fraction = float(np.clip(float(self.args.throw_release_fraction), 0.0, 0.95))
        impulse_open_alpha = float(np.clip(float(self.args.showcase_impulse_open_alpha), 0.0, 1.0))
        for idx in range(steps):
            alpha = idx / max(1, steps - 1)
            target = event.broad.ball_demo.blend_targets(start, end, alpha)
            if alpha >= release_fraction:
                hand_alpha = (alpha - release_fraction) / max(1e-6, 1.0 - release_fraction)
                hand = event.broad.ball_demo.blend_targets(close_hand, open_hand, hand_alpha)
                target.update(hand)
                self.mark_release()
                if hand_alpha >= impulse_open_alpha:
                    self.apply_showcase_impulse_once()
            self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(self.model, self.mujoco, self.names, target)
            self.mujoco.mj_step(self.model, self.data)
            if not self.sync_viewer(viewer, phase="throw_swing_release", phase_step=idx, phase_progress=alpha):
                return False
        self.mark_release()
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

        windup_target = self.target_with_arm_deltas(
            last_lift_target,
            {
                "j1": float(self.args.throw_windup_j1_delta),
                "j2": float(self.args.throw_windup_j2_delta),
                "j3": float(self.args.throw_windup_j3_delta),
                "j4": float(self.args.throw_windup_j4_delta),
            },
        )
        swing_target = self.target_with_arm_deltas(
            last_lift_target,
            {
                "j1": float(self.args.throw_swing_j1_delta),
                "j2": float(self.args.throw_swing_j2_delta),
                "j3": float(self.args.throw_swing_j3_delta),
                "j4": float(self.args.throw_swing_j4_delta),
            },
        )
        if not self.step_fixed_phase("throw_windup", last_lift_target, windup_target, int(self.args.throw_windup_steps), viewer):
            return self.summary(False, "viewer_closed")
        if not self.run_throw_swing(windup_target, swing_target, viewer):
            return self.summary(False, "viewer_closed")

        open_throw_target = {**swing_target, **event.broad.hand_targets(self.candidate, open_hand=True)}
        for idx in range(max(1, int(self.args.throw_follow_through_steps))):
            self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(self.model, self.mujoco, self.names, open_throw_target)
            self.mujoco.mj_step(self.model, self.data)
            progress = idx / max(1, int(self.args.throw_follow_through_steps) - 1)
            if not self.sync_viewer(viewer, phase="throw_follow_through", phase_step=idx, phase_progress=progress):
                return self.summary(False, "viewer_closed")

        for idx in range(max(1, int(self.args.ball_flight_steps))):
            self.data.ctrl[:] = event.broad.ball_demo.ctrl_from_targets(self.model, self.mujoco, self.names, open_throw_target)
            self.mujoco.mj_step(self.model, self.data)
            progress = idx / max(1, int(self.args.ball_flight_steps) - 1)
            if not self.sync_viewer(viewer, phase="ball_flight", phase_step=idx, phase_progress=progress):
                return self.summary(False, "viewer_closed")

        final_frame, _packet = self.sample("final", force=True)
        final_rows = event.broad.contact_rows(self.model, self.data, self.mujoco)
        final_morph = event.broad.frame_morphology(final_rows, self.candidate)
        hold_summary = event.broad.summarize_frames(hold_frames)
        lift_summary = event.broad.summarize_frames(lift_frames)
        gate_summary = event.broad.summarize_frames(contact_gate_frames)
        final_ball = event.broad.ball_position(self.model, self.data, self.mujoco)
        hold_lift_max = float(max(hold_lifts) if hold_lifts else 0.0)
        release_lost_hand = bool(final_morph["hand_contacts"] == 0)
        throw_distance = float(self.max_post_release_xy_distance_m)
        throw_success = bool(
            release_lost_hand
            and throw_distance >= float(self.args.min_throw_distance_m)
            and self.max_ball_speed_mps >= float(self.args.min_throw_speed_mps)
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
        success = bool(true_pinch_success and throw_success)
        if success:
            terminal_reason = "success_true_pinch_lift_throw_ball"
        elif not contact_gate_success:
            terminal_reason = "contact_gate_failed"
        elif not lift_success:
            terminal_reason = "lift_gate_failed"
        elif not true_pinch_success:
            terminal_reason = "true_pinch_morphology_gate_failed"
        elif not release_lost_hand:
            terminal_reason = "throw_release_still_touching_hand"
        elif throw_distance < float(self.args.min_throw_distance_m):
            terminal_reason = "throw_distance_too_short"
        else:
            terminal_reason = "throw_gate_failed"
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
            "throw_success": bool(throw_success),
            "release_lost_hand": bool(release_lost_hand),
            "showcase_impulse_applied": bool(self.showcase_impulse_applied),
            "lift_break_reason": lift_break_reason,
            "hold_break_reason": hold_break_reason,
            "max_lift_m": float(self.max_lift),
            "hold_lift_m_max": float(hold_lift_max),
            "max_penetration_m": float(self.max_pen),
            "max_ball_speed_mps": float(self.max_ball_speed_mps),
            "max_ball_xy_distance_m": float(self.max_ball_xy_distance_m),
            "throw_distance_m": float(throw_distance),
            "max_post_release_height_gain_m": float(self.max_post_release_height_gain_m),
            "contact_gate_morphology": gate_summary,
            "hold_morphology": hold_summary,
            "lift_morphology": lift_summary,
            "final_morphology": final_morph,
            "final_sample": final_frame,
            "final_ball": final_ball,
            "release_ball": self.release_ball_position,
            "case": {
                "name": self.case.name,
                "candidate": asdict(self.candidate),
                "hold_steps": int(self.case.hold_steps),
                "min_lift_height": float(self.case.min_lift_height),
            },
            "motor_force_feedback_summary": summarize_motor_force_feedback_samples(self.motor_feedback_samples),
        }


class BallThrowDashboard(base.RealtimeDashboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.show_window:
            self.window_name = "Stage3 ball throw dashboard"
        self.ball_trail: list[tuple[int, int]] = []

    def update_dashboard(self, episode: BallThrowEpisode, *, terminal_reason: str = "") -> bool:
        self.update_dynamic_camera(episode)
        return super().update_dashboard(episode, terminal_reason=terminal_reason)

    def update_dynamic_camera(self, episode: BallThrowEpisode) -> None:
        if not bool(getattr(self.args, "dynamic_camera", True)):
            return
        ball = event.broad.ball_position(episode.model, episode.data, episode.mujoco)
        initial = np.asarray(episode.initial_ball, dtype=float)
        phase = str(episode.last_phase)
        if phase == "initial_vertical_hold":
            lookat = initial + np.array([0.02, -0.04, 0.25])
            distance = 1.30
        elif phase in {"initial_to_grasp_pose", "approach", "preshape", "pinch_close", "contact_gate", "post_contact_settle"}:
            lookat = initial + np.array([0.015, -0.025, 0.105])
            distance = 0.82
        elif phase in {"slow_lift", "hold", "throw_windup", "throw_swing_release", "throw_follow_through"}:
            lookat = initial + np.array([0.07, -0.035, 0.12])
            distance = 0.90
        else:
            lookat = initial + np.array([0.20, -0.06, 0.10])
            distance = 1.16
        self.camera.lookat[:] = lookat
        self.camera.distance = float(distance)
        self.camera.azimuth = float(self.args.camera_azimuth)
        self.camera.elevation = float(self.args.camera_elevation)

    def compose_frame(
        self,
        episode: BallThrowEpisode,
        render_bgr: np.ndarray,
        terminal_reason: str,
    ) -> np.ndarray:
        cv2 = self.cv2
        if render_bgr.shape[1] != self.width or render_bgr.shape[0] != self.render_height:
            render_bgr = cv2.resize(render_bgr, (self.width, self.render_height), interpolation=cv2.INTER_AREA)
        top = render_bgr.copy()
        self.draw_ball_trail(top, episode)
        self.draw_status_overlay(top, episode, terminal_reason)
        plot = np.full((self.plot_height, self.width, 3), (18, 18, 18), dtype=np.uint8)
        self.draw_curve_panel(plot, episode)
        return np.vstack([top, plot])

    def draw_ball_trail(self, image: np.ndarray, episode: BallThrowEpisode) -> None:
        if not bool(getattr(self.args, "trail_overlay", True)):
            return
        flight_phase = str(episode.last_phase) in {"ball_flight", "final"}
        if int(episode.sequence_id) <= 4 or not flight_phase:
            self.ball_trail.clear()
        hsv = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2HSV)
        mask = self.cv2.inRange(hsv, np.array([4, 105, 115], dtype=np.uint8), np.array([28, 255, 255], dtype=np.uint8))
        mask = self.cv2.medianBlur(mask, 5)
        contours, _hier = self.cv2.findContours(mask, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE)
        point: tuple[int, int] | None = None
        if contours:
            candidates = []
            for contour in contours:
                area = float(self.cv2.contourArea(contour))
                if area < 20.0:
                    continue
                perimeter = float(self.cv2.arcLength(contour, True))
                circularity = float(4.0 * np.pi * area / max(perimeter * perimeter, 1e-6))
                x, y, w, h = self.cv2.boundingRect(contour)
                aspect = float(w / max(1, h))
                if circularity < 0.20 or aspect < 0.35 or aspect > 2.4:
                    continue
                candidates.append((area * circularity, contour))
            if candidates:
                contour = max(candidates, key=lambda item: item[0])[1]
                moments = self.cv2.moments(contour)
                if abs(float(moments.get("m00", 0.0))) > 1e-6:
                    cx = int(moments["m10"] / moments["m00"])
                    cy = int(moments["m01"] / moments["m00"])
                    point = (cx, cy)
                    if flight_phase and (
                        not self.ball_trail
                        or np.hypot(cx - self.ball_trail[-1][0], cy - self.ball_trail[-1][1]) > 2.0
                    ):
                        self.ball_trail.append((cx, cy))
                    self.ball_trail = self.ball_trail[-70:]
        trail = self.ball_trail
        if len(trail) >= 2:
            for idx, (a, b) in enumerate(zip(trail, trail[1:])):
                fade = (idx + 1) / max(1, len(trail) - 1)
                color = (0, int(115 + 95 * fade), 255)
                thickness = max(1, int(round(1 + 2 * fade)))
                self.cv2.line(image, a, b, color, thickness, self.cv2.LINE_AA)
        if point is not None:
            self.cv2.circle(image, point, 16, (0, 220, 255), 2, self.cv2.LINE_AA)

    def draw_status_overlay(self, image: np.ndarray, episode: BallThrowEpisode, terminal_reason: str) -> None:
        cv2 = self.cv2
        frame = episode.last_frame or {}
        packet = episode.last_packet or {}
        active = packet.get("active_pair", {})
        speed = float((episode.trace_rows[-1] if episode.trace_rows else {}).get("ball_speed_mps", 0.0))
        dist = float((episode.trace_rows[-1] if episode.trace_rows else {}).get("post_release_xy_distance_m", 0.0))
        lines = [
            "Stage3 ball throw",
            f"{episode.last_phase}  {float(episode.data.time):.2f}s",
            f"lift {float(frame.get('lift_m', 0.0)):.3f} m",
            f"force {float(active.get('total_tension_n', 0.0)):.1f} N  current {float(active.get('max_abs_iq_a', 0.0)):.2f} A",
            f"speed {speed:.2f} m/s  distance {dist:.3f} m",
        ]
        if terminal_reason:
            lines.append("PASS" if terminal_reason.startswith("success") else terminal_reason[:28])
        line_h = 20
        box_w = 400
        box_h = 18 + line_h * len(lines)
        x = self.width - box_w + 18
        y = 28
        overlay = image.copy()
        cv2.rectangle(overlay, (self.width - box_w, 10), (self.width - 14, 10 + box_h), (18, 18, 18), -1)
        cv2.addWeighted(overlay, 0.60, image, 0.40, 0.0, image)
        for idx, text in enumerate(lines):
            color = (255, 255, 255) if idx != 0 else (80, 230, 255)
            cv2.putText(image, text, (x, y + idx * line_h), cv2.FONT_HERSHEY_SIMPLEX, 0.50, color, 1, cv2.LINE_AA)

    def draw_curve_panel(self, image: np.ndarray, episode: BallThrowEpisode) -> None:
        rows = episode.trace_rows
        cv2 = self.cv2
        title = "Synchronized force feedback + ball flight curves from the same MuJoCo ticks"
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
            ("ball_speed_mps", "ball speed", "m/s", (80, 220, 120), 0.0, None),
            (
                "post_release_xy_distance_m",
                "throw distance",
                "m",
                (120, 160, 255),
                0.0,
                max(float(self.args.min_throw_distance_m) * 1.75, 0.12),
            ),
        ]
        for lane_idx, (field, label, unit, color, ymin, ymax) in enumerate(lanes):
            top = lane_top + lane_idx * lane_h
            self.draw_lane(image, visible, field, label, unit, color, top, lane_h - 8, ymin, ymax)


def build_parser() -> argparse.ArgumentParser:
    parser = base.build_parser()
    parser.description = "Run a MuJoCo-only Stage3 true-pinch ball throw dashboard demo."
    parser.set_defaults(
        trace_csv=DEFAULT_TRACE_CSV,
        camera_distance=1.08,
        camera_lookat_dx=0.14,
        camera_lookat_dy=-0.06,
        camera_lookat_dz=0.08,
        plot_seconds=4.5,
        dashboard_render_height=780,
        dashboard_plot_height=300,
    )
    parser.add_argument("--dynamic-camera", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--trail-overlay", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--throw-windup-steps", type=int, default=90)
    parser.add_argument("--throw-swing-steps", type=int, default=55)
    parser.add_argument("--throw-follow-through-steps", type=int, default=100)
    parser.add_argument("--ball-flight-steps", type=int, default=900)
    parser.add_argument("--throw-release-fraction", type=float, default=0.18)
    parser.add_argument("--throw-windup-j1-delta", type=float, default=-0.25)
    parser.add_argument("--throw-windup-j2-delta", type=float, default=-0.05)
    parser.add_argument("--throw-windup-j3-delta", type=float, default=0.10)
    parser.add_argument("--throw-windup-j4-delta", type=float, default=-0.25)
    parser.add_argument("--throw-swing-j1-delta", type=float, default=-0.95)
    parser.add_argument("--throw-swing-j2-delta", type=float, default=0.42)
    parser.add_argument("--throw-swing-j3-delta", type=float, default=-0.45)
    parser.add_argument("--throw-swing-j4-delta", type=float, default=0.85)
    parser.add_argument("--min-throw-distance-m", type=float, default=0.08)
    parser.add_argument("--min-throw-speed-mps", type=float, default=0.08)
    parser.add_argument("--showcase-impulse", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--showcase-impulse-open-alpha", type=float, default=0.18)
    parser.add_argument("--throw-impulse-vx", type=float, default=-0.25)
    parser.add_argument("--throw-impulse-vy", type=float, default=0.34)
    parser.add_argument("--throw-impulse-vz", type=float, default=0.42)
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

    ev_args = base.make_event_args(args)
    case = base.load_case(args)
    args.output_dir = Path(args.output_dir).expanduser().resolve()
    if bool(args.record_video):
        args.output_dir.mkdir(parents=True, exist_ok=True)
        if args.video_output is None:
            speed_tag = str(float(args.video_speedup)).replace(".", "p")
            impulse_tag = "_impulse" if bool(args.showcase_impulse) else ""
            args.video_output = args.output_dir / f"stage3_ball_throw_dashboard{impulse_tag}_x{speed_tag}.mp4"
        else:
            args.video_output = Path(args.video_output).expanduser().resolve()
        if Path(args.trace_csv) == DEFAULT_TRACE_CSV:
            impulse_tag = "_impulse" if bool(args.showcase_impulse) else ""
            args.trace_csv = args.output_dir / f"stage3_ball_throw_trace{impulse_tag}.csv"

    def run_one(viewer=None) -> tuple[BallThrowEpisode, dict[str, Any]]:
        model = mujoco.MjModel.from_xml_path(str(scene))
        episode = BallThrowEpisode(model, mujoco, case, args, ev_args)
        if viewer is not None:
            base.setup_viewer_camera(model, episode.data, mujoco, viewer, args, episode.initial_ball)
        result = episode.run(viewer=viewer)
        return episode, result

    if bool(args.headless_smoke):
        episode, result = run_one(viewer=None)
        trace_path = None if bool(args.no_trace_csv) else Path(args.trace_csv)
        base.write_trace_csv(trace_path, episode.trace_rows)
        print(
            "Stage3 ball throw dashboard smoke: "
            f"status={result['status']} reason={result['terminal_reason']} "
            f"lift={float(result.get('hold_lift_m_max', result.get('max_lift_m', 0.0))):.4f} "
            f"throw={float(result.get('throw_distance_m', 0.0)):.4f} "
            f"speed={float(result.get('max_ball_speed_mps', 0.0)):.3f} "
            f"impulse={bool(result.get('showcase_impulse_applied', False))} "
            f"trace_csv={str(trace_path) if trace_path else 'disabled'}"
        )
        return 0 if bool(result.get("success")) else 1

    if bool(args.dashboard_window) or bool(args.record_video):
        if bool(args.record_video):
            print("Rendering Stage3 ball throw dashboard video.")
            print(f"Video output: {args.video_output}")
            print(f"Trace CSV: {args.trace_csv if not bool(args.no_trace_csv) else 'disabled'}")
        else:
            print("Opening Stage3 ball throw dashboard.")
        print(f"Scene: {scene}")
        print(f"Selected case: {args.selected}")
        print("Top = MuJoCo render; bottom = force-feedback and ball-flight curves.")
        final_result: dict[str, Any] | None = None
        final_episode: BallThrowEpisode | None = None
        model = mujoco.MjModel.from_xml_path(str(scene))
        data = mujoco.MjData(model)
        episode = BallThrowEpisode(model, mujoco, case, args, ev_args, data=data)
        dashboard = BallThrowDashboard(
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
                    f"throw={float(result.get('throw_distance_m', 0.0)):.4f} "
                    f"speed={float(result.get('max_ball_speed_mps', 0.0)):.3f} "
                    f"impulse={bool(result.get('showcase_impulse_applied', False))}"
                )
                if not bool(args.loop):
                    while dashboard.running:
                        dashboard.update_dashboard(episode, terminal_reason=result.get("terminal_reason", ""))
                    break
                episode = BallThrowEpisode(model, mujoco, case, args, ev_args, data=data)
                time.sleep(0.4)
        finally:
            dashboard.close()
        if final_episode is not None:
            trace_path = None if bool(args.no_trace_csv) else Path(args.trace_csv)
            base.write_trace_csv(trace_path, final_episode.trace_rows)
            if final_result is not None and not bool(args.record_video):
                print(json.dumps(packet_export.json_ready(final_result), indent=2, ensure_ascii=False))
        if bool(args.record_video):
            print(f"Wrote video: {args.video_output}")
        return 0 if final_result is None or bool(final_result.get("success", False)) else 1

    import mujoco.viewer

    print("Opening Stage3 ball throw MuJoCo demo.")
    print(f"Scene: {scene}")
    print(f"Selected case: {args.selected}")
    final_result: dict[str, Any] | None = None
    final_episode: BallThrowEpisode | None = None
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    episode = BallThrowEpisode(model, mujoco, case, args, ev_args, data=data)
    with mujoco.viewer.launch_passive(
        model,
        data,
        show_left_ui=bool(args.show_ui),
        show_right_ui=bool(args.show_ui),
    ) as viewer:
        while viewer.is_running():
            base.setup_viewer_camera(model, episode.data, mujoco, viewer, args, episode.initial_ball)
            result = episode.run(viewer=viewer)
            final_result = result
            final_episode = episode
            print(
                f"{result['status']} {result['terminal_reason']} "
                f"lift={float(result.get('hold_lift_m_max', 0.0)):.4f} "
                f"throw={float(result.get('throw_distance_m', 0.0)):.4f} "
                f"speed={float(result.get('max_ball_speed_mps', 0.0)):.3f} "
                f"impulse={bool(result.get('showcase_impulse_applied', False))}"
            )
            if not bool(args.loop):
                while viewer.is_running():
                    viewer.set_texts(episode.overlay_texts(result.get("terminal_reason", "")))
                    viewer.sync()
                    time.sleep(0.05)
                break
            episode = BallThrowEpisode(model, mujoco, case, args, ev_args, data=data)
            time.sleep(0.4)

    if final_episode is not None:
        trace_path = None if bool(args.no_trace_csv) else Path(args.trace_csv)
        base.write_trace_csv(trace_path, final_episode.trace_rows)
        if final_result is not None:
            print(json.dumps(packet_export.json_ready(final_result), indent=2, ensure_ascii=False))
    return 0 if final_result is None or bool(final_result.get("success", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
