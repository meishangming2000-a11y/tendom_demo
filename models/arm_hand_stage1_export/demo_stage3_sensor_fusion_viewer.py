#!/usr/bin/env python3
"""Interactive MuJoCo viewer demo for Stage3 virtual vision + tactile/slip.

This demo stays inside MuJoCo. It reuses the Stage3.5 scripted expert and adds
viewer markers:

- green marker/ray: virtual-camera egg pose estimate
- colored dots: contact-derived tactile regions
- red halo: slip risk above the Stage3 gate
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import HAND_KEYWORDS, MujocoTactileSlipSensor, classify_region


REGION_COLORS = {
    "thumb": np.array([0.05, 0.75, 1.00, 1.0], dtype=np.float32),
    "index": np.array([1.00, 0.82, 0.10, 1.0], dtype=np.float32),
    "middle": np.array([0.58, 0.35, 1.00, 1.0], dtype=np.float32),
    "ring": np.array([1.00, 0.45, 0.05, 1.0], dtype=np.float32),
    "little": np.array([0.30, 1.00, 0.42, 1.0], dtype=np.float32),
    "palm": np.array([1.00, 0.10, 0.75, 1.0], dtype=np.float32),
    "support": np.array([0.70, 0.70, 0.70, 0.8], dtype=np.float32),
    "arm": np.array([0.90, 0.90, 0.90, 0.8], dtype=np.float32),
    "unknown": np.array([1.00, 1.00, 1.00, 0.8], dtype=np.float32),
}
VISION_RGBA = np.array([0.00, 1.00, 0.25, 0.85], dtype=np.float32)
VISION_FAINT_RGBA = np.array([0.00, 0.80, 0.20, 0.35], dtype=np.float32)
SLIP_RGBA = np.array([1.00, 0.04, 0.02, 0.70], dtype=np.float32)
IDENTITY = np.eye(3, dtype=np.float64).reshape(9)

TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}


@dataclass
class DemoPlan:
    trial: sweep.TrialConfig
    egg_position: np.ndarray
    vision_estimate: dict[str, Any]
    target_position: np.ndarray
    initial_egg: np.ndarray
    phases: list[tuple[str, dict[str, float], dict[str, float], int]]


def select_trial(name: str) -> sweep.TrialConfig:
    trials = {trial.name: trial for trial in sweep.trial_configs()}
    if name not in trials:
        valid = ", ".join(sorted(trials))
        raise ValueError(f"Unknown trial {name!r}. Valid trials: {valid}")
    return trials[name]


def accepted_virtual_camera_estimate(estimate: dict[str, Any], min_confidence: float) -> bool:
    return estimate.get("status") == "ok" and float(estimate.get("confidence", 0.0)) >= float(min_confidence)


def build_demo_plan(model, data, mujoco, args: argparse.Namespace) -> DemoPlan:
    trial = select_trial(str(args.trial))
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    sweep.reset_episode(model, data, mujoco, egg_position)

    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.perception_camera, width=int(args.width), height=int(args.height)),
    )
    vision_estimate = vision_sensor.estimate(data, label=f"{trial.name}_viewer_acquire")
    if not accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence)):
        raise RuntimeError(
            "Virtual camera acquisition failed: "
            f"status={vision_estimate.get('status')} confidence={vision_estimate.get('confidence')} "
            f"mask_pixels={vision_estimate.get('mask_pixels')}"
        )

    target_position = np.asarray(vision_estimate["position_world_est"], dtype=np.float64).copy()
    grasp_local = sweep.DEFAULT_GRASP_LOCAL.copy()
    solver = sweep.ArmProxyIkSolver(model, mujoco, grasp_local)
    approach_target = target_position.copy()
    approach_target[2] += float(trial.grasp_z_bias_m)
    lift_target = approach_target.copy()
    lift_target[2] += float(trial.lift_delta_m)
    approach_arm = sweep.arm_dict(solver.solve(approach_target, z_weight=10.0))
    lift_arm = sweep.arm_dict(solver.solve(lift_target, z_weight=6.0))
    pre_arm = dict(approach_arm)
    pre_arm["j2"] = float(np.clip(pre_arm["j2"] + float(trial.pre_j2_delta), -1.5708, 1.5708))

    sweep.reset_episode(model, data, mujoco, egg_position)
    for joint, value in pre_arm.items():
        data.qpos[sweep.base.joint_qadr(model, mujoco, joint)] = float(value)
    actuator_names = sweep.base.actuator_names(model, mujoco)
    data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()

    hand_targets = {
        "preshape": {**approach_arm, **sweep.base.PRESHAPE_TARGETS},
        "close_fingers": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS},
        "close_thumb": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
        "lift": {**lift_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
    }
    phases = [
        ("approach", pre_arm, approach_arm, int(args.approach_steps)),
        ("preshape", approach_arm, hand_targets["preshape"], int(args.hand_steps)),
        ("gentle_close_fingers", hand_targets["preshape"], hand_targets["close_fingers"], int(args.close_fingers_steps)),
        ("gentle_close_thumb", hand_targets["close_fingers"], hand_targets["close_thumb"], int(args.close_thumb_steps)),
        ("contact_settle", hand_targets["close_thumb"], hand_targets["close_thumb"], int(args.contact_settle_steps)),
        ("slow_lift", hand_targets["close_thumb"], hand_targets["lift"], int(args.lift_steps)),
        ("hold", hand_targets["lift"], hand_targets["lift"], int(args.hold_steps)),
    ]
    return DemoPlan(
        trial=trial,
        egg_position=egg_position,
        vision_estimate=vision_estimate,
        target_position=target_position,
        initial_egg=initial_egg,
        phases=phases,
    )


def set_start_pose(model, data, mujoco, plan: DemoPlan) -> None:
    # The first phase start dict is the pre-approach arm pose.
    pre_arm = plan.phases[0][1]
    sweep.reset_episode(model, data, mujoco, plan.egg_position)
    for joint, value in pre_arm.items():
        data.qpos[sweep.base.joint_qadr(model, mujoco, joint)] = float(value)
    actuator_names = sweep.base.actuator_names(model, mujoco)
    data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)


def add_user_geom(scn, mujoco, geom_type, size, pos, rgba) -> None:
    if scn is None or int(scn.ngeom) >= len(scn.geoms):
        return
    geom = scn.geoms[int(scn.ngeom)]
    mujoco.mjv_initGeom(
        geom,
        int(geom_type),
        np.asarray(size, dtype=np.float64),
        np.asarray(pos, dtype=np.float64),
        IDENTITY,
        np.asarray(rgba, dtype=np.float32),
    )
    scn.ngeom += 1


def add_user_line(scn, mujoco, start, end, rgba, *, width: float = 3.0) -> None:
    if scn is None or int(scn.ngeom) >= len(scn.geoms):
        return
    geom = scn.geoms[int(scn.ngeom)]
    mujoco.mjv_initGeom(
        geom,
        int(mujoco.mjtGeom.mjGEOM_LINE),
        np.zeros(3, dtype=np.float64),
        np.zeros(3, dtype=np.float64),
        IDENTITY,
        np.asarray(rgba, dtype=np.float32),
    )
    mujoco.mjv_connector(
        geom,
        int(mujoco.mjtGeom.mjGEOM_LINE),
        float(width),
        np.asarray(start, dtype=np.float64),
        np.asarray(end, dtype=np.float64),
    )
    scn.ngeom += 1


def contact_rows_for_egg(tactile_sensor: MujocoTactileSlipSensor, data) -> list[dict[str, Any]]:
    rows = []
    summary = tactile_sensor.contact_summary(data)
    for row in summary["top_contacts"]:
        if not bool(row.get("has_egg")):
            continue
        names = list(row.get("names", []))
        joined = " ".join(str(name).lower() for name in names)
        if "floor" in joined:
            region = "support"
        elif any(key in joined for key in HAND_KEYWORDS):
            region = classify_region(names)
        else:
            region = "unknown"
        rows.append({**row, "region": region})
    return rows


def add_region_anchor_markers(model, data, mujoco, scn, contact_counts: dict[str, int]) -> None:
    for region, site_name in TIP_SITES.items():
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        if sid < 0:
            continue
        active = int(contact_counts.get(region, 0)) > 0
        color = REGION_COLORS[region].copy()
        color[3] = 0.80 if active else 0.22
        radius = 0.0065 if active else 0.0035
        add_user_geom(scn, mujoco, mujoco.mjtGeom.mjGEOM_SPHERE, [radius, radius, radius], data.site_xpos[sid].copy(), color)

    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if palm_id >= 0:
        active = int(contact_counts.get("palm", 0)) > 0
        color = REGION_COLORS["palm"].copy()
        color[3] = 0.70 if active else 0.18
        radius = 0.007 if active else 0.004
        add_user_geom(scn, mujoco, mujoco.mjtGeom.mjGEOM_SPHERE, [radius, radius, radius], data.xpos[palm_id].copy(), color)


def update_visual_overlays(
    model,
    data,
    mujoco,
    viewer,
    plan: DemoPlan,
    tactile_sensor: MujocoTactileSlipSensor,
    tactile: dict[str, Any],
    *,
    phase_name: str,
    phase_step: int,
    phase_steps: int,
    thresholds: Stage3Thresholds,
) -> list[tuple[Any, Any, str, str]]:
    scn = viewer.user_scn
    if scn is not None:
        scn.ngeom = 0

    vision_pos = np.asarray(plan.vision_estimate["position_world_est"], dtype=np.float64)
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, plan.vision_estimate.get("camera", "stage3_egg_closeup"))
    if cam_id >= 0:
        camera_pos = data.cam_xpos[cam_id].copy()
        add_user_geom(scn, mujoco, mujoco.mjtGeom.mjGEOM_SPHERE, [0.006, 0.006, 0.006], camera_pos, VISION_FAINT_RGBA)
        add_user_line(scn, mujoco, camera_pos, vision_pos, VISION_RGBA, width=3.0)

    add_user_geom(scn, mujoco, mujoco.mjtGeom.mjGEOM_SPHERE, [0.010, 0.010, 0.010], vision_pos, VISION_RGBA)
    add_user_line(scn, mujoco, vision_pos + np.array([-0.020, 0.0, 0.0]), vision_pos + np.array([0.020, 0.0, 0.0]), VISION_RGBA)
    add_user_line(scn, mujoco, vision_pos + np.array([0.0, -0.020, 0.0]), vision_pos + np.array([0.0, 0.020, 0.0]), VISION_RGBA)
    add_user_line(scn, mujoco, vision_pos + np.array([0.0, 0.0, -0.020]), vision_pos + np.array([0.0, 0.0, 0.020]), VISION_RGBA)

    contact_counts = dict(tactile.get("egg_contact_region_counts", {}))
    add_region_anchor_markers(model, data, mujoco, scn, contact_counts)

    for row in contact_rows_for_egg(tactile_sensor, data):
        region = str(row.get("region", "unknown"))
        color = REGION_COLORS.get(region, REGION_COLORS["unknown"]).copy()
        if float(tactile["slip_score"]) > float(thresholds.success_max_slip_score) and region not in {"support"}:
            color = 0.55 * color + 0.45 * SLIP_RGBA
            color[3] = 1.0
        pos = np.asarray(row["pos"], dtype=np.float64)
        pen = float(row.get("penetration", 0.0))
        radius = float(np.clip(0.005 + 2.5 * pen, 0.005, 0.012))
        add_user_geom(scn, mujoco, mujoco.mjtGeom.mjGEOM_SPHERE, [radius, radius, radius], pos, color)
        add_user_line(scn, mujoco, pos, pos + np.array([0.0, 0.0, 0.025]), color, width=4.0)

    egg_pos = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    lift = float(egg_pos[2] - plan.initial_egg[2])
    if float(tactile["slip_score"]) > float(thresholds.success_max_slip_score):
        add_user_geom(
            scn,
            mujoco,
            mujoco.mjtGeom.mjGEOM_SPHERE,
            [0.017, 0.017, 0.017],
            egg_pos + np.array([0.0, 0.0, 0.055]),
            SLIP_RGBA,
        )

    regions = ",".join(str(region) for region in tactile.get("contact_regions", [])) or "none"
    left_text = "\n".join(
        [
            "Stage3 sensor fusion demo",
            f"trial: {plan.trial.name}",
            f"phase: {phase_name}  {phase_step + 1}/{max(1, phase_steps)}",
            "",
            "VISION",
            f"camera: {plan.vision_estimate.get('camera')}",
            f"status: {plan.vision_estimate.get('status')}  conf: {float(plan.vision_estimate.get('confidence', 0.0)):.3f}",
            f"mask pixels: {int(plan.vision_estimate.get('mask_pixels', 0))}",
            "",
            "TACTILE",
            f"contact: {bool(tactile['contact_present'])}  regions: {regions}",
            f"stable: {bool(tactile['grip_stable'])}  persistence: {int(tactile['contact_persistence'])}",
            f"slip: {float(tactile['slip_score']):.3f}  crush: {float(tactile['crush_risk']):.3f}",
            f"penetration: {float(tactile.get('max_penetration', 0.0)):.5f} m",
            f"lift: {lift:.4f} m",
        ]
    )
    right_text = "\n".join(
        [
            "Legend",
            "green sphere/ray = virtual vision pose",
            "colored dots = tactile contact regions",
            "red halo = slip risk",
            "",
            "thumb cyan",
            "index yellow",
            "middle purple",
            "ring orange",
            "little green",
            "palm magenta",
            "floor/support gray",
        ]
    )
    return [
        (mujoco.mjtFontScale.mjFONTSCALE_150, mujoco.mjtGridPos.mjGRID_TOPLEFT, left_text, ""),
        (mujoco.mjtFontScale.mjFONTSCALE_150, mujoco.mjtGridPos.mjGRID_TOPRIGHT, right_text, ""),
    ]


def setup_viewer_camera(model, data, mujoco, viewer) -> None:
    mujoco.mjv_defaultFreeCamera(model, viewer.cam)
    egg_id = sweep.egg_body_id(model, mujoco)
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = data.xpos[egg_id].copy()
    if palm_id >= 0:
        lookat = 0.55 * data.xpos[egg_id].copy() + 0.45 * data.xpos[palm_id].copy()
    viewer.cam.lookat[:] = lookat
    viewer.cam.distance = 0.46
    viewer.cam.azimuth = 180.0
    viewer.cam.elevation = -18.0


def run_one_episode(model, data, mujoco, args: argparse.Namespace, viewer=None) -> dict[str, Any]:
    plan = build_demo_plan(model, data, mujoco, args)
    set_start_pose(model, data, mujoco, plan)
    thresholds = Stage3Thresholds()
    actuator_names = sweep.base.actuator_names(model, mujoco)
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    final_tactile: dict[str, Any] | None = None
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0

    if viewer is not None:
        setup_viewer_camera(model, data, mujoco, viewer)

    for phase_name, start, end, steps in plan.phases:
        for idx in range(max(1, int(steps))):
            alpha = idx / max(1, int(steps) - 1)
            targets = sweep.blend_targets(start, end, alpha)
            data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, targets)
            mujoco.mj_step(model, data)
            tactile = tactile_sensor.sample(data)
            final_tactile = tactile
            max_slip = max(max_slip, float(tactile["slip_score"]))
            max_crush = max(max_crush, float(tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(tactile.get("max_penetration", 0.0)))
            if viewer is not None:
                with viewer.lock():
                    texts = update_visual_overlays(
                        model,
                        data,
                        mujoco,
                        viewer,
                        plan,
                        tactile_sensor,
                        tactile,
                        phase_name=phase_name,
                        phase_step=idx,
                        phase_steps=int(steps),
                        thresholds=thresholds,
                    )
                viewer.set_texts(texts)
                viewer.sync()
                if not viewer.is_running():
                    break
                time.sleep(float(model.opt.timestep) / max(float(args.speed), 1e-6))
        if viewer is not None and not viewer.is_running():
            break

    assert final_tactile is not None
    egg_pos = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    lift = float(egg_pos[2] - plan.initial_egg[2])
    return {
        "trial": plan.trial.name,
        "vision_status": plan.vision_estimate.get("status"),
        "vision_confidence": float(plan.vision_estimate.get("confidence", 0.0)),
        "mask_pixels": int(plan.vision_estimate.get("mask_pixels", 0)),
        "final_lift_height_m": lift,
        "final_contact_present": bool(final_tactile["contact_present"]),
        "final_grip_stable": bool(final_tactile["grip_stable"]),
        "final_slip_score": float(final_tactile["slip_score"]),
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open a Stage3 MuJoCo virtual vision + tactile/slip viewer demo.")
    parser.add_argument("--scene", default=str(CURRENT_STAGE3_SCENE))
    parser.add_argument("--trial", default="center_nominal")
    parser.add_argument("--perception-camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--speed", type=float, default=1.0, help="Viewer playback speed multiplier.")
    parser.add_argument("--loop", action=argparse.BooleanOptionalAction, default=True, help="Replay the demo until the viewer closes.")
    parser.add_argument("--headless-smoke", action="store_true", help="Run one episode without opening the MuJoCo viewer.")
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=1500)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    if args.headless_smoke:
        result = run_one_episode(model, data, mujoco, args, viewer=None)
        print(
            "Stage3 sensor fusion headless smoke: "
            f"trial={result['trial']} vision={result['vision_status']} conf={result['vision_confidence']:.3f} "
            f"lift={result['final_lift_height_m']:.4f} stable={result['final_grip_stable']} "
            f"final_slip={result['final_slip_score']:.3f} max_slip={result['max_slip_score']:.3f} "
            f"max_crush={result['max_crush_risk']:.3f} max_pen={result['max_penetration_m']:.6f}"
        )
        return 0

    import mujoco.viewer

    print("Opening Stage3 sensor fusion viewer.")
    print("Green marker/ray = virtual camera pose estimate.")
    print("Colored contact dots = tactile contact regions. Red halo = slip risk.")
    print("Close the MuJoCo viewer window to stop.")
    with mujoco.viewer.launch_passive(model, data, show_left_ui=True, show_right_ui=True) as viewer:
        while viewer.is_running():
            result = run_one_episode(model, data, mujoco, args, viewer=viewer)
            print(
                f"{result['trial']}: lift={result['final_lift_height_m']:.4f} "
                f"stable={result['final_grip_stable']} final_slip={result['final_slip_score']:.3f}"
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
