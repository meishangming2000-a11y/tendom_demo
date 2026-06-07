#!/usr/bin/env python3
"""Interactive MuJoCo viewer for Stage3.7D contact-transition recovery.

This demo stays MuJoCo-only. It runs the same control stack as the selected
Stage3.7D candidate:

    scripted arm/wrist
    + Stage3.6 learned hand/finger policy
    + Stage3.7B tactile lift gate
    + Stage3.7D slow_lift recovery micro-phase

The viewer reuses the Stage3 sensor-fusion overlay and adds recovery-specific
signals:

- orange halo: recovery micro-phase is commanding a small progress rollback
- red halo: slip is above the Stage3 slip threshold
- recovery text panel: transition reasons, progress rollback, budget, and gate
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_v2_bc_common import load_policy
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
CHECKPOINTS = ROOT / "checkpoints"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import demo_stage3_sensor_fusion_viewer as fusion
import run_stage3_visual_guided_grasp_sweep as sweep
from eval_stage3_contact_transition_gate_v0 import parse_phase_set, transition_gate_reasons
from eval_stage3_phase_hand_policy_v0 import predict_hand_action
from eval_stage3_tactile_phase_gate_v0 import gate_condition_reasons, merge_phase_hand_action
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_phase_hand_policy_v0.pth"
RECOVERY_RGBA = np.array([1.00, 0.55, 0.02, 0.75], dtype=np.float32)
RECOVERY_FAINT_RGBA = np.array([1.00, 0.55, 0.02, 0.28], dtype=np.float32)
RECOVERY_EXHAUSTED_RGBA = np.array([1.00, 0.05, 0.02, 0.90], dtype=np.float32)
SAFE_RGBA = np.array([0.10, 1.00, 0.30, 0.95], dtype=np.float32)
BAR_BG_RGBA = np.array([0.15, 0.15, 0.15, 0.80], dtype=np.float32)


@dataclass
class RecoveryVisualState:
    phase_name: str
    phase_step: int
    phase_steps: int
    step_count: int
    nominal_progress: float
    control_progress: float
    recovery_commanded: bool
    recovery_active_after_step: bool
    recovery_events: int
    recovery_steps: int
    recovery_budget_used: int
    recovery_budget_limit: int
    recovery_stable_window: int
    recovery_budget_exhausted: bool
    transition_reasons: list[str]
    gate_reasons: list[str]
    gate_stable_window: int
    gate_release_reason: str
    used_learned_hand: bool
    max_slip: float
    hold_max_slip: float
    lift_height_m: float
    slip_threshold: float


def selected_trial(name: str) -> sweep.TrialConfig:
    trials = {trial.name: trial for trial in sweep.trial_configs()}
    if name not in trials:
        raise ValueError(f"Unknown trial {name!r}; valid={sorted(trials)}")
    return trials[name]


def add_budget_bar(model, data, mujoco, scn, state: RecoveryVisualState) -> None:
    egg_id = sweep.egg_body_id(model, mujoco)
    egg_pos = data.xpos[egg_id].copy()
    origin = egg_pos + np.array([0.085, -0.015, 0.030])
    length = 0.060
    ratio = float(np.clip(state.recovery_budget_used / max(1, state.recovery_budget_limit), 0.0, 1.0))
    start = origin.copy()
    end = origin + np.array([0.0, 0.0, length])
    fusion.add_user_line(scn, mujoco, start, end, BAR_BG_RGBA, width=6.0)
    if ratio > 0.0:
        color = RECOVERY_RGBA.copy()
        if ratio > 0.85:
            color = RECOVERY_EXHAUSTED_RGBA.copy()
        fill_end = origin + np.array([0.0, 0.0, length * ratio])
        fusion.add_user_line(scn, mujoco, start, fill_end, color, width=8.0)


def update_recovery_overlays(
    model,
    data,
    mujoco,
    viewer,
    plan_view: SimpleNamespace,
    tactile_sensor: MujocoTactileSlipSensor,
    tactile: dict[str, Any],
    state: RecoveryVisualState,
    thresholds: Stage3Thresholds,
) -> list[tuple[Any, Any, str, str]]:
    # Reuse vision, contact-region, and slip-risk markers first.
    fusion.update_visual_overlays(
        model,
        data,
        mujoco,
        viewer,
        plan_view,
        tactile_sensor,
        tactile,
        phase_name=state.phase_name,
        phase_step=state.phase_step,
        phase_steps=state.phase_steps,
        thresholds=thresholds,
    )
    scn = viewer.user_scn
    egg_id = sweep.egg_body_id(model, mujoco)
    egg_pos = data.xpos[egg_id].copy()

    if state.recovery_commanded:
        fusion.add_user_geom(
            scn,
            mujoco,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            [0.030, 0.030, 0.030],
            egg_pos + np.array([0.0, 0.0, 0.073]),
            RECOVERY_RGBA,
        )
        fusion.add_user_line(
            scn,
            mujoco,
            egg_pos + np.array([-0.035, 0.0, 0.073]),
            egg_pos + np.array([0.035, 0.0, 0.073]),
            RECOVERY_RGBA,
            width=5.0,
        )
    elif state.phase_name == "slow_lift":
        fusion.add_user_geom(
            scn,
            mujoco,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            [0.018, 0.018, 0.018],
            egg_pos + np.array([0.0, 0.0, 0.073]),
            RECOVERY_FAINT_RGBA,
        )

    if state.recovery_budget_exhausted:
        fusion.add_user_geom(
            scn,
            mujoco,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            [0.037, 0.037, 0.037],
            egg_pos + np.array([0.0, 0.0, 0.095]),
            RECOVERY_EXHAUSTED_RGBA,
        )

    add_budget_bar(model, data, mujoco, scn, state)

    regions = ",".join(str(region) for region in tactile.get("contact_regions", [])) or "none"
    reasons = ",".join(state.transition_reasons) or "clear"
    gate_reasons = ",".join(state.gate_reasons) or "clear"
    progress_drop = float(state.nominal_progress - state.control_progress)
    recovery_label = "YES" if state.recovery_commanded else "no"
    region_text = regions
    if len(region_text) > 34:
        region_text = region_text[:31] + "..."
    reason_text = reasons
    if len(reason_text) > 34:
        reason_text = reason_text[:31] + "..."
    gate_reason_text = gate_reasons
    if len(gate_reason_text) > 34:
        gate_reason_text = gate_reason_text[:31] + "..."
    left_text = "\n".join(
        [
            "Stage3.7D recovery",
            f"trial {plan_view.trial.name}",
            f"phase {state.phase_name} {state.phase_step + 1}/{max(1, state.phase_steps)}",
            f"step {state.step_count}",
            "",
            "VISION",
            f"{plan_view.vision_estimate.get('status')} conf {float(plan_view.vision_estimate.get('confidence', 0.0)):.3f}",
            f"mask {int(plan_view.vision_estimate.get('mask_pixels', 0))}",
            "",
            "TACTILE",
            f"contact {bool(tactile['contact_present'])} stable {bool(tactile['grip_stable'])}",
            f"regions {region_text}",
            f"slip {float(tactile['slip_score']):.3f}/{state.slip_threshold:.2f}",
            f"crush {float(tactile['crush_risk']):.3f} pen {float(tactile.get('max_penetration', 0.0)):.5f}",
            f"lift {state.lift_height_m:.4f} m",
            "",
            "RECOVERY",
            f"cmd {recovery_label} events {state.recovery_events} steps {state.recovery_steps}",
            f"budget {state.recovery_budget_used}/{state.recovery_budget_limit} win {state.recovery_stable_window}",
            f"prog {state.nominal_progress:.3f}->{state.control_progress:.3f} drop {progress_drop:.3f}",
            f"reasons {reason_text}",
            f"gate {state.gate_release_reason}",
            f"gate reasons {gate_reason_text}",
            f"max slip {state.max_slip:.3f} hold {state.hold_max_slip:.3f}",
        ]
    )
    right_text = "\n".join(
        [
            "Legend",
            "green = vision pose",
            "dots = tactile regions",
            "red = slip risk",
            "orange = recovery rollback",
            "bar = recovery budget",
            "",
            "Stage3.7D",
            "slow_lift only",
            "slip th 0.29",
            "budget 200",
            "drop 0.01",
            "",
            "Orange means:",
            "back off lift a little",
            "then retry.",
        ]
    )
    return [
        (mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_TOPLEFT, left_text, ""),
        (mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_BOTTOMRIGHT, right_text, ""),
    ]


def build_plan(model, data, mujoco, trial: sweep.TrialConfig, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], np.ndarray]:
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    rng = np.random.default_rng(int(args.seed))
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)

    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )
    vision_estimate = vision_sensor.estimate(data, label=f"stage3_7d_recovery_viewer_{trial.name}")
    if not collect.accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence)):
        raise RuntimeError(f"Virtual camera acquisition failed: {vision_estimate}")
    vision_estimate.setdefault("camera", str(args.camera))
    vision = collect.make_vision_fields(vision_estimate)
    profile = collect.Stage3DatasetProfile("viewer_clean_nominal", 1.0, 0.0, 0.0, 0)
    plan = collect.build_episode_plan(
        model,
        data,
        mujoco,
        trial=trial,
        egg_position=egg_position,
        vision_fields=vision,
        args=args,
        profile=profile,
    )
    return plan, vision_estimate, egg_position


def run_one_episode(model, data, mujoco, policy, checkpoint: dict[str, Any], args: argparse.Namespace, device: torch.device, viewer=None) -> dict[str, Any]:
    trial = selected_trial(str(args.trial))
    plan, vision_estimate, _egg_position = build_plan(model, data, mujoco, trial, args)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    plan_view = SimpleNamespace(trial=trial, vision_estimate=vision_estimate, initial_egg=initial_egg)

    if viewer is not None:
        fusion.setup_viewer_camera(model, data, mujoco, viewer)

    previous_action: np.ndarray | None = None
    actuator_names = plan["actuator_names"]
    learned_phases = set(str(name) for name in checkpoint.get("learned_phases", []))
    recovery_phases = parse_phase_set(args.transition_gate_phases)

    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    hold_steps = 0
    hold_stable_steps = 0
    hold_max_slip = 0.0
    recovery_active = False
    recovery_stable_window = 0
    recovery_steps = 0
    recovery_events = 0
    recovery_budget_exhausted = False
    gate_stable_window = 0
    gate_release_reason = "not_reached"
    step_count = 0
    final_tactile: dict[str, Any] | None = None

    gate_min_steps = max(0, int(args.min_contact_settle_steps))
    gate_max_steps = max(1, int(args.max_contact_settle_steps))
    if gate_max_steps < gate_min_steps:
        gate_max_steps = gate_min_steps

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = max(1, int(steps))
        if phase_name == "contact_settle":
            phase_steps = gate_max_steps
        local_step = 0
        phase_extra_steps = 0
        recovery_active = False
        recovery_stable_window = 0
        while local_step < phase_steps:
            nominal_progress = local_step / max(1, phase_steps - 1)
            tactile = tactile_sensor.sample(data)
            pre_reasons = transition_gate_reasons(tactile, phase_name=phase_name, transition_phases=recovery_phases, args=args)
            if pre_reasons and not recovery_active:
                recovery_active = True
                recovery_stable_window = 0
                recovery_events += 1

            recovery_commanded = bool(recovery_active and phase_name in recovery_phases)
            control_progress = nominal_progress
            if recovery_commanded:
                control_progress = max(0.0, nominal_progress - float(args.recovery_progress_drop))

            obs = collect.observation_vector(model, data, collect.make_vision_fields(vision_estimate), tactile, phase_name=phase_name, progress=control_progress)
            expert_targets = sweep.blend_targets(start, end, control_progress)
            expert_action = sweep.actuator_targets(model, mujoco, actuator_names, expert_targets)
            hand_action = predict_hand_action(
                policy,
                checkpoint,
                obs,
                device=device,
                clip_to_train_range=not bool(args.no_train_range_clip),
            )
            action, used_learned_hand = merge_phase_hand_action(
                expert_action,
                hand_action,
                checkpoint,
                phase_name=phase_name,
                learned_phases=learned_phases,
            )
            if previous_action is not None and float(args.action_smoothing) > 0.0:
                smoothing = float(np.clip(args.action_smoothing, 0.0, 0.99))
                action = smoothing * previous_action + (1.0 - smoothing) * action
            previous_action = action.copy()
            data.ctrl[:] = collect.clip_action(model, action)
            mujoco.mj_step(model, data)

            next_tactile = tactile_sensor.sample(data)
            final_tactile = next_tactile
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_egg[2])
            max_slip = max(max_slip, float(next_tactile["slip_score"]))
            max_crush = max(max_crush, float(next_tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(next_tactile.get("max_penetration", 0.0)))
            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(next_tactile["grip_stable"]))
                hold_max_slip = max(hold_max_slip, float(next_tactile["slip_score"]))

            gate_reasons = gate_condition_reasons(next_tactile, args, thresholds)
            post_reasons = transition_gate_reasons(next_tactile, phase_name=phase_name, transition_phases=recovery_phases, args=args)
            transition_reasons = sorted(set(pre_reasons + post_reasons))
            if transition_reasons and phase_name in recovery_phases and not recovery_active:
                recovery_active = True
                recovery_stable_window = 0
                recovery_events += 1

            if phase_name == "contact_settle":
                if gate_reasons:
                    gate_stable_window = 0
                else:
                    gate_stable_window += 1
                contact_settle_step = local_step + 1
                if contact_settle_step >= gate_min_steps and gate_stable_window >= int(args.settle_stable_window_steps):
                    gate_release_reason = "stable_window_met"
                elif contact_settle_step >= gate_max_steps:
                    gate_release_reason = "max_steps_reached_stable" if not gate_reasons else "max_steps_reached_unstable"

            extra_step_used = False
            if recovery_active and phase_name in recovery_phases:
                if transition_reasons:
                    recovery_stable_window = 0
                else:
                    recovery_stable_window += 1
                needs_more_recovery = bool(transition_reasons) or recovery_stable_window < int(args.recovery_stable_window_steps)
                budget_left = phase_extra_steps < int(args.max_transition_hold_steps_per_phase)
                if needs_more_recovery and budget_left:
                    phase_extra_steps += 1
                    recovery_steps += 1
                    extra_step_used = True
                elif needs_more_recovery and not budget_left:
                    recovery_budget_exhausted = True
                    recovery_active = False
                else:
                    recovery_active = False

            skip_render_for_focus = bool(
                viewer is not None
                and bool(args.demo_focus)
                and recovery_phases
                and phase_name not in recovery_phases
            )
            if viewer is not None and not skip_render_for_focus:
                state = RecoveryVisualState(
                    phase_name=phase_name,
                    phase_step=int(local_step),
                    phase_steps=int(phase_steps),
                    step_count=int(step_count),
                    nominal_progress=float(nominal_progress),
                    control_progress=float(control_progress),
                    recovery_commanded=bool(recovery_commanded),
                    recovery_active_after_step=bool(recovery_active),
                    recovery_events=int(recovery_events),
                    recovery_steps=int(recovery_steps),
                    recovery_budget_used=int(phase_extra_steps) if phase_name in recovery_phases else 0,
                    recovery_budget_limit=int(args.max_transition_hold_steps_per_phase),
                    recovery_stable_window=int(recovery_stable_window),
                    recovery_budget_exhausted=bool(recovery_budget_exhausted),
                    transition_reasons=transition_reasons,
                    gate_reasons=gate_reasons,
                    gate_stable_window=int(gate_stable_window),
                    gate_release_reason=gate_release_reason,
                    used_learned_hand=bool(used_learned_hand),
                    max_slip=float(max_slip),
                    hold_max_slip=float(hold_max_slip),
                    lift_height_m=float(lift_height),
                    slip_threshold=float(args.transition_slip_threshold),
                )
                with viewer.lock():
                    texts = update_recovery_overlays(
                        model,
                        data,
                        mujoco,
                        viewer,
                        plan_view,
                        tactile_sensor,
                        next_tactile,
                        state,
                        thresholds,
                    )
                viewer.set_texts(texts)
                viewer.sync()
                if not viewer.is_running():
                    break
                time.sleep(float(model.opt.timestep) / max(float(args.speed), 1e-6))
            elif viewer is not None and step_count % 250 == 0:
                viewer.sync()
                if not viewer.is_running():
                    break

            if not extra_step_used:
                local_step += 1
            step_count += 1
            if phase_name == "contact_settle" and gate_release_reason != "not_reached":
                break
        if viewer is not None and not viewer.is_running():
            break

    if final_tactile is None:
        final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    return {
        "trial": trial.name,
        "vision_status": vision_estimate.get("status"),
        "vision_confidence": float(vision_estimate.get("confidence", 0.0)),
        "final_lift_height_m": float(final_egg[2] - initial_egg[2]),
        "final_grip_stable": bool(final_tactile["grip_stable"]),
        "final_slip_score": float(final_tactile["slip_score"]),
        "hold_stable_fraction": float(hold_stable_steps / max(1, hold_steps)),
        "hold_max_slip_score": float(hold_max_slip),
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "recovery_events": int(recovery_events),
        "recovery_steps": int(recovery_steps),
        "recovery_budget_exhausted": bool(recovery_budget_exhausted),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open a Stage3.7D recovery-focused MuJoCo viewer.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--trial", default="center_nominal")
    parser.add_argument("--seed", type=int, default=170)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--functional-hit-threshold", type=float, default=0.015)
    parser.add_argument("--max-ik-dxy", type=float, default=0.006)
    parser.add_argument("--max-ik-dz", type=float, default=0.006)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.80)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--approach-steps", type=int, default=320)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--min-contact-settle-steps", type=int, default=2000)
    parser.add_argument("--max-contact-settle-steps", type=int, default=2000)
    parser.add_argument("--settle-stable-window-steps", type=int, default=300)
    parser.add_argument("--gate-slip-threshold", type=float, default=0.18)
    parser.add_argument("--gate-crush-threshold", type=float, default=0.35)
    parser.add_argument("--gate-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--transition-gate-phases", default="slow_lift")
    parser.add_argument("--transition-slip-threshold", type=float, default=0.29)
    parser.add_argument("--transition-crush-threshold", type=float, default=0.35)
    parser.add_argument("--transition-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--max-transition-hold-steps-per-phase", type=int, default=200)
    parser.add_argument("--recovery-progress-drop", type=float, default=0.01)
    parser.add_argument("--recovery-stable-window-steps", type=int, default=0)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=1500)
    parser.add_argument("--speed", type=float, default=1.0, help="Viewer playback speed multiplier.")
    parser.add_argument("--loop", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--demo-focus",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fast-forward non-recovery phases so the viewer opens near the recovery visualization.",
    )
    parser.add_argument("--show-ui", action="store_true", help="Show the standard MuJoCo side panels.")
    parser.add_argument("--headless-smoke", action="store_true")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    device = torch.device(args.device)

    import mujoco

    policy, checkpoint = load_policy(args.checkpoint, device)
    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    if args.headless_smoke:
        result = run_one_episode(model, data, mujoco, policy, checkpoint, args, device, viewer=None)
        print(
            "Stage3.7D recovery viewer smoke: "
            f"trial={result['trial']} vision={result['vision_status']} conf={result['vision_confidence']:.3f} "
            f"lift={result['final_lift_height_m']:.4f} stable={result['final_grip_stable']} "
            f"final_slip={result['final_slip_score']:.3f} max_slip={result['max_slip_score']:.3f} "
            f"hold_slip={result['hold_max_slip_score']:.3f} recovery_steps={result['recovery_steps']} "
            f"recovery_events={result['recovery_events']} budget_exhausted={result['recovery_budget_exhausted']}"
        )
        return 0

    import mujoco.viewer

    print("Opening Stage3.7D recovery viewer.")
    if bool(args.demo_focus):
        print("Demo focus is on: non-recovery phases are fast-forwarded before rendering.")
    print("Orange halo/bar = recovery micro-phase and budget.")
    print("Green = virtual-camera estimate. Colored dots = tactile regions. Red = slip risk.")
    with mujoco.viewer.launch_passive(
        model,
        data,
        show_left_ui=bool(args.show_ui),
        show_right_ui=bool(args.show_ui),
    ) as viewer:
        while viewer.is_running():
            result = run_one_episode(model, data, mujoco, policy, checkpoint, args, device, viewer=viewer)
            print(
                f"{result['trial']}: lift={result['final_lift_height_m']:.4f} "
                f"stable={result['final_grip_stable']} max_slip={result['max_slip_score']:.3f} "
                f"recovery_steps={result['recovery_steps']}"
            )
            if not bool(args.loop):
                while viewer.is_running():
                    viewer.sync()
                    time.sleep(0.05)
                break
            time.sleep(0.6)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
