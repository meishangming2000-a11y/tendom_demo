#!/usr/bin/env python3
"""Interactive MuJoCo viewer for the trained Stage3.8B pinch grasp.

This demo uses the selected candidate produced by
`train_stage3_pinch_grasp_candidates_v0.py`. It stays MuJoCo-only:

- green marker/ray: virtual-camera egg pose estimate
- colored dots: synthetic tactile contact regions
- bright finger-tip halos: the trained pinch fingers
- red halo: slip risk
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
META = ROOT / "metadata"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import demo_stage3_sensor_fusion_viewer as fusion
import eval_stage3_pinch_grasp_v0 as pinch
import run_stage3_visual_guided_grasp_sweep as sweep
from eval_stage3_tactile_phase_gate_v0 import gate_condition_reasons
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_SELECTED = META / "stage3_pinch_grasp_training_v0_selected.json"
PINCH_RGBA = np.array([1.0, 0.95, 0.05, 0.85], dtype=np.float32)
PASS_RGBA = np.array([0.05, 1.0, 0.25, 0.82], dtype=np.float32)


def candidate_from_json(path: Path) -> pinch.PinchCandidate:
    raw = json.loads(path.read_text(encoding="utf-8"))
    candidate_raw = raw.get("selected_candidate", raw)
    return pinch.PinchCandidate(
        name=str(candidate_raw["name"]),
        active_fingers=tuple(str(x) for x in candidate_raw["active_fingers"]),
        thumb_cmc_abd=float(candidate_raw["thumb_cmc_abd"]),
        thumb_cmc=float(candidate_raw["thumb_cmc"]),
        thumb_mcp=float(candidate_raw["thumb_mcp"]),
        thumb_ip=float(candidate_raw["thumb_ip"]),
        active_mcp_flex=float(candidate_raw["active_mcp_flex"]),
        active_mcp_abd=float(candidate_raw["active_mcp_abd"]),
        active_pip=float(candidate_raw["active_pip"]),
        active_dip=float(candidate_raw["active_dip"]),
        inactive_scale=float(candidate_raw["inactive_scale"]),
        approach_z_bias_delta=float(candidate_raw.get("approach_z_bias_delta", 0.0)),
        lift_delta_scale=float(candidate_raw.get("lift_delta_scale", 1.0)),
    )


def load_candidate(args: argparse.Namespace) -> pinch.PinchCandidate:
    path = Path(args.candidate_config)
    if path.exists():
        return candidate_from_json(path)
    if str(args.candidate) in pinch.PINCH_CANDIDATES:
        return pinch.PINCH_CANDIDATES[str(args.candidate)]
    raise FileNotFoundError(f"Candidate config not found and fallback candidate is unknown: {path}")


def selected_trial(name: str) -> sweep.TrialConfig:
    trials = {trial.name: trial for trial in sweep.trial_configs()}
    if name not in trials:
        raise ValueError(f"Unknown trial {name!r}; valid={sorted(trials)}")
    return trials[name]


def acquire_initial_vision(model, data, mujoco, args: argparse.Namespace) -> dict[str, Any]:
    sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=str(args.camera), width=int(args.width), height=int(args.height)),
    )
    estimate = sensor.estimate(data, label=f"stage3_pinch_viewer_{args.trial}_initial")
    estimate["accepted"] = pinch.accepted_estimate(estimate, float(args.min_vision_confidence))
    estimate.setdefault("camera", str(args.camera))
    if not bool(estimate["accepted"]):
        raise RuntimeError(f"Virtual camera acquisition failed: {estimate}")
    return estimate


def build_demo_plan(model, data, mujoco, candidate: pinch.PinchCandidate, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], np.ndarray, sweep.TrialConfig]:
    trial = selected_trial(str(args.trial))
    mujoco.mj_forward(model, data)
    base_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg + np.asarray(trial.offset_xyz, dtype=np.float64)
    rng = np.random.default_rng(int(args.seed))
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)
    initial_vision = acquire_initial_vision(model, data, mujoco, args)
    plan = pinch.build_pinch_plan(
        model,
        data,
        mujoco,
        trial=trial,
        candidate=candidate,
        egg_position=egg_position,
        vision_estimate=initial_vision,
        args=args,
    )
    return plan, initial_vision, egg_position, trial


def setup_viewer_camera(model, data, mujoco, viewer) -> None:
    fusion.setup_viewer_camera(model, data, mujoco, viewer)
    viewer.cam.distance = 0.38
    viewer.cam.azimuth = 176.0
    viewer.cam.elevation = -22.0


def add_active_finger_halos(model, data, mujoco, scn, candidate: pinch.PinchCandidate) -> None:
    for region in ("thumb", *candidate.active_fingers):
        site_name = fusion.TIP_SITES.get(region)
        if not site_name:
            continue
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        if sid < 0:
            continue
        color = fusion.REGION_COLORS.get(region, PINCH_RGBA).copy()
        color[3] = 0.95
        fusion.add_user_geom(scn, mujoco, mujoco.mjtGeom.mjGEOM_SPHERE, [0.010, 0.010, 0.010], data.site_xpos[sid].copy(), color)

    thumb_site = fusion.TIP_SITES.get("thumb")
    thumb_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, thumb_site) if thumb_site else -1
    if thumb_id < 0:
        return
    thumb_pos = data.site_xpos[thumb_id].copy()
    for region in candidate.active_fingers:
        site_name = fusion.TIP_SITES.get(region)
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name) if site_name else -1
        if sid >= 0:
            fusion.add_user_line(scn, mujoco, thumb_pos, data.site_xpos[sid].copy(), PINCH_RGBA, width=4.5)


def update_pinch_overlays(
    model,
    data,
    mujoco,
    viewer,
    plan_view: SimpleNamespace,
    candidate: pinch.PinchCandidate,
    tactile_sensor: MujocoTactileSlipSensor,
    tactile: dict[str, Any],
    *,
    phase_name: str,
    phase_step: int,
    phase_steps: int,
    thresholds: Stage3Thresholds,
    hold_steps: int,
    hold_stable_steps: int,
    hold_pinch_steps: int,
    max_slip: float,
) -> list[tuple[Any, Any, str, str]]:
    fusion.update_visual_overlays(
        model,
        data,
        mujoco,
        viewer,
        plan_view,
        tactile_sensor,
        tactile,
        phase_name=phase_name,
        phase_step=phase_step,
        phase_steps=phase_steps,
        thresholds=thresholds,
    )
    scn = viewer.user_scn
    add_active_finger_halos(model, data, mujoco, scn, candidate)
    egg_pos = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    lift = float(egg_pos[2] - plan_view.initial_egg[2])
    if lift >= float(plan_view.min_vision_lift_height):
        fusion.add_user_geom(
            scn,
            mujoco,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            [0.014, 0.014, 0.014],
            egg_pos + np.array([0.0, 0.0, 0.070]),
            PASS_RGBA,
        )
    regions = ",".join(str(region) for region in tactile.get("contact_regions", [])) or "none"
    active = "+".join(("thumb", *candidate.active_fingers))
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
    hold_pinch_fraction = float(hold_pinch_steps / max(1, hold_steps))
    left_text = "\n".join(
        [
            "Stage3.8B pinch demo",
            f"candidate {candidate.name}",
            f"trial {plan_view.trial.name}",
            f"phase {phase_name} {phase_step + 1}/{max(1, phase_steps)}",
            "",
            "VISION",
            f"{plan_view.vision_estimate.get('camera')} conf {float(plan_view.vision_estimate.get('confidence', 0.0)):.3f}",
            f"mask {int(plan_view.vision_estimate.get('mask_pixels', 0))}",
            "",
            "PINCH",
            f"active {active}",
            f"contact {pinch.pinch_contact_ok(tactile, candidate)}",
            f"regions {regions}",
            f"lift {lift:.4f} m",
            "",
            "TACTILE HOLD",
            f"stable {hold_stable_fraction:.3f}",
            f"pinch {hold_pinch_fraction:.3f}",
            f"slip {float(tactile['slip_score']):.3f} max {max_slip:.3f}",
            f"crush {float(tactile['crush_risk']):.3f}",
            f"pen {float(tactile.get('max_penetration', 0.0)):.5f}",
        ]
    )
    right_text = "\n".join(
        [
            "Legend",
            "green = virtual vision pose",
            "colored dots = tactile regions",
            "bright halos = pinch fingers",
            "yellow lines = pinch span",
            "red halo = slip risk",
            "green halo above egg = lifted",
            "",
            "Goal",
            "vision-confirmed lift",
            "thumb + active fingers",
            "stable low-slip hold",
        ]
    )
    return [
        (mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_TOPLEFT, left_text, ""),
        (mujoco.mjtFontScale.mjFONTSCALE_100, mujoco.mjtGridPos.mjGRID_TOPRIGHT, right_text, ""),
    ]


def run_viewer_episode(model, data, mujoco, candidate: pinch.PinchCandidate, args: argparse.Namespace, viewer=None) -> dict[str, Any]:
    plan, initial_vision, _egg_position, trial = build_demo_plan(model, data, mujoco, candidate, args)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    plan_view = SimpleNamespace(
        trial=trial,
        vision_estimate=initial_vision,
        initial_egg=initial_egg,
        min_vision_lift_height=float(args.min_vision_lift_height),
    )
    if viewer is not None:
        setup_viewer_camera(model, data, mujoco, viewer)

    hold_steps = 0
    hold_stable_steps = 0
    hold_pinch_steps = 0
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    final_tactile: dict[str, Any] | None = None
    gate_min_steps = max(0, int(args.min_contact_settle_steps))
    gate_max_steps = max(1, int(args.max_contact_settle_steps))
    if gate_max_steps < gate_min_steps:
        gate_max_steps = gate_min_steps
    gate_stable_window = 0
    actuator_names = plan["actuator_names"]

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = gate_max_steps if phase_name == "contact_settle" else max(1, int(steps))
        local_step = 0
        while local_step < phase_steps:
            progress = local_step / max(1, phase_steps - 1)
            targets = sweep.blend_targets(start, end, progress)
            data.ctrl[:] = collect.clip_action(model, sweep.actuator_targets(model, mujoco, actuator_names, targets))
            mujoco.mj_step(model, data)
            tactile = tactile_sensor.sample(data)
            final_tactile = tactile
            max_slip = max(max_slip, float(tactile["slip_score"]))
            max_crush = max(max_crush, float(tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(tactile.get("max_penetration", 0.0)))

            if phase_name == "contact_settle":
                gate_reasons = gate_condition_reasons(tactile, args, thresholds)
                if gate_reasons:
                    gate_stable_window = 0
                else:
                    gate_stable_window += 1
                if local_step + 1 >= gate_min_steps and gate_stable_window >= int(args.settle_stable_window_steps):
                    break

            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(tactile["grip_stable"]))
                hold_pinch_steps += int(bool(pinch.pinch_contact_ok(tactile, candidate)))

            if viewer is not None:
                with viewer.lock():
                    texts = update_pinch_overlays(
                        model,
                        data,
                        mujoco,
                        viewer,
                        plan_view,
                        candidate,
                        tactile_sensor,
                        tactile,
                        phase_name=phase_name,
                        phase_step=local_step,
                        phase_steps=phase_steps,
                        thresholds=thresholds,
                        hold_steps=hold_steps,
                        hold_stable_steps=hold_stable_steps,
                        hold_pinch_steps=hold_pinch_steps,
                        max_slip=max_slip,
                    )
                viewer.set_texts(texts)
                viewer.sync()
                if not viewer.is_running():
                    break
                time.sleep(float(model.opt.timestep) / max(float(args.speed), 1e-6))

            local_step += 1
        if viewer is not None and not viewer.is_running():
            break

    if final_tactile is None:
        final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    return {
        "candidate": candidate.name,
        "trial": trial.name,
        "vision_status": initial_vision.get("status"),
        "vision_confidence": float(initial_vision.get("confidence", 0.0)),
        "final_lift_height_m": float(final_egg[2] - initial_egg[2]),
        "hold_stable_fraction": float(hold_stable_steps / max(1, hold_steps)),
        "hold_pinch_fraction": float(hold_pinch_steps / max(1, hold_steps)),
        "final_grip_stable": bool(final_tactile["grip_stable"]),
        "final_slip_score": float(final_tactile["slip_score"]),
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open the trained Stage3.8B pinch-grasp MuJoCo viewer.")
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--candidate", default="tripod_support")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--debug-dir", type=Path, default=ROOT / "docs" / "visual_checks_stage3_pinch_viewer_v0")
    parser.add_argument("--trial", default="center_nominal")
    parser.add_argument("--seed", type=int, default=381)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--final-cameras", default="stage3_egg_closeup,stage3_egg_overview")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--min-final-vision-confidence", type=float, default=0.35)
    parser.add_argument("--min-vision-lift-height", type=float, default=0.045)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.60)
    parser.add_argument("--min-hold-pinch-fraction", type=float, default=0.55)
    parser.add_argument("--min-hold-pinch-purity", type=float, default=0.55)
    parser.add_argument("--approach-steps", type=int, default=300)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--pinch-close-steps", type=int, default=220)
    parser.add_argument("--min-contact-settle-steps", type=int, default=120)
    parser.add_argument("--max-contact-settle-steps", type=int, default=360)
    parser.add_argument("--settle-stable-window-steps", type=int, default=70)
    parser.add_argument("--gate-slip-threshold", type=float, default=0.22)
    parser.add_argument("--gate-crush-threshold", type=float, default=0.35)
    parser.add_argument("--gate-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--lift-steps", type=int, default=520)
    parser.add_argument("--hold-steps", type=int, default=900)
    parser.add_argument("--sample-every", type=int, default=240)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--loop", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--headless-smoke", action="store_true")
    parser.add_argument("--render-vision-debug", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    candidate = load_candidate(args)
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    if bool(args.headless_smoke):
        row = pinch.run_pinch_episode(model, mujoco, candidate=candidate, trial=selected_trial(str(args.trial)), episode_id=0, args=args)
        r = row.get("summary", {})
        print(
            "Stage3.8B pinch viewer smoke: "
            f"candidate={candidate.name} trial={args.trial} status={row['status']} reason={row['terminal_reason']} "
            f"vision_lift={r.get('vision_lift_height_m', float('nan')):.4f} "
            f"true_lift={r.get('true_lift_height_m', float('nan')):.4f} "
            f"pinch={r.get('hold_pinch_fraction', float('nan')):.3f} "
            f"stable={r.get('hold_stable_fraction', float('nan')):.3f} "
            f"hold_slip={r.get('hold_max_slip_score', float('nan')):.3f}"
        )
        return 0 if bool(row.get("success")) else 1

    import mujoco.viewer

    print("Opening Stage3.8B trained pinch viewer.")
    print(f"Candidate: {candidate.name}; active fingers: thumb + {', '.join(candidate.active_fingers)}")
    print("Green = virtual vision, colored dots = tactile regions, bright halos/lines = pinch fingers.")
    print("Close the MuJoCo viewer window to stop.")
    with mujoco.viewer.launch_passive(model, data, show_left_ui=False, show_right_ui=False) as viewer:
        while viewer.is_running():
            result = run_viewer_episode(model, data, mujoco, candidate, args, viewer=viewer)
            print(
                f"{result['candidate']} {result['trial']}: lift={result['final_lift_height_m']:.4f} "
                f"pinch={result['hold_pinch_fraction']:.3f} stable={result['hold_stable_fraction']:.3f} "
                f"hold_slip={result['final_slip_score']:.3f}"
            )
            if not bool(args.loop):
                while viewer.is_running():
                    viewer.sync()
                    time.sleep(0.05)
                break
            time.sleep(0.4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
