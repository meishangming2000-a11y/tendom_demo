#!/usr/bin/env python3
"""Pinned-ball scripted grasp smoke on the body-connected export4 scene."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_proxy.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connected_grasp"
REPORT = DOCS / "body_connected_grasp_smoke_report.md"
META = ROOT / "metadata" / "body_connected_grasp_smoke.json"

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

THUMB_TARGETS = {
    "thumb_cmc_abd_joint": -0.30,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}

PHASES = [
    ("open", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close", {**LONG_FINGER_TARGETS, **THUMB_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_TARGETS}),
]

TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def name_id(model, objtype, name: str) -> int:
    return mujoco.mj_name2id(model, objtype, name)


def actuator_map(model) -> dict[str, int]:
    out: dict[str, int] = {}
    for aid in range(model.nu):
        if model.actuator_trntype[aid] != mujoco.mjtTrn.mjTRN_JOINT:
            continue
        jid = int(model.actuator_trnid[aid, 0])
        joint = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        if joint:
            out[joint] = aid
    return out


def apply_targets(model, data, amap: dict[str, int], targets: dict[str, float], steps: int, *, pin_ball: bool, ball_qadr: int | None, ball_pos: np.ndarray) -> None:
    start = data.ctrl.copy()
    goal = data.ctrl.copy()
    for joint, target in targets.items():
        aid = amap.get(joint)
        if aid is not None:
            goal[aid] = target
    for i in range(max(1, steps)):
        alpha = i / max(1, steps - 1)
        data.ctrl[:] = (1.0 - alpha) * start + alpha * goal
        if pin_ball and ball_qadr is not None:
            data.qpos[ball_qadr : ball_qadr + 3] = ball_pos
            data.qpos[ball_qadr + 3 : ball_qadr + 7] = [1.0, 0.0, 0.0, 0.0]
        mujoco.mj_step(model, data)


def contact_summary(model, data) -> dict[str, Any]:
    max_pen = 0.0
    ball_contacts = 0
    body_contacts = 0
    for i in range(data.ncon):
        con = data.contact[i]
        depth = max(0.0, -float(con.dist))
        max_pen = max(max_pen, depth)
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(con.geom1)) or ""
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(con.geom2)) or ""
        names = f"{g1} {g2}"
        if "ball" in names and ("finger" in names or "thumb" in names or "palm" in names or "hand" in names):
            ball_contacts += 1
        if "rough_body_support" in names:
            body_contacts += 1
    return {"contact_count": int(data.ncon), "ball_hand_contact_count": int(ball_contacts), "body_contact_count": int(body_contacts), "max_penetration": float(max_pen)}


def site_pos(model, data, name: str) -> np.ndarray | None:
    sid = name_id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    return data.site_xpos[sid].copy() if sid >= 0 else None


def body_pos(model, data, name: str) -> np.ndarray | None:
    bid = name_id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def metrics(model, data, ball_start: np.ndarray) -> dict[str, Any]:
    ball = body_pos(model, data, "ball")
    distances = {}
    if ball is not None:
        for key, site in TIP_SITES.items():
            p = site_pos(model, data, site)
            distances[key] = float(np.linalg.norm(p - ball)) if p is not None else None
    four = [v for k, v in distances.items() if k in ("index", "middle", "ring", "little") and v is not None]
    ball_disp = float(np.linalg.norm(ball - ball_start)) if ball is not None else None
    return {
        "contact": contact_summary(model, data),
        "ball_position": ball,
        "ball_displacement": ball_disp,
        "tip_ball_distances": distances,
        "four_finger_avg_tip_ball_distance": float(np.mean(four)) if four else None,
        "thumb_ball_distance": distances.get("thumb"),
    }


def render(model, data, path: Path, *, azimuth: float = 205, elevation: float = -22, distance: float = 0.8) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    pts = []
    for name in ("rough_body_support_link", "palm_link", "ball"):
        p = body_pos(model, data, name)
        if p is not None:
            pts.append(p)
    lookat = np.mean(np.asarray(pts), axis=0) if pts else np.array([0.0, 0.0, 0.25])
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = distance
        cam.azimuth = azimuth
        cam.elevation = elevation
        renderer.update_scene(data, camera=cam)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(path, image)
    return {"file": str(path), "mean_pixel": float(image.mean()), "min_pixel": int(image.min()), "max_pixel": int(image.max())}


def run(scene: Path, phase_steps: int, hold_steps: int, pin_ball: bool) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    amap = actuator_map(model)
    ball_jid = name_id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
    ball_qadr = int(model.jnt_qposadr[ball_jid]) if ball_jid >= 0 else None
    ball_start = body_pos(model, data, "ball")
    if ball_start is None:
        ball_start = np.zeros(3)
    phase_results = []
    screenshots = {}
    for idx, (phase, targets) in enumerate(PHASES):
        steps = hold_steps if phase == "hold" else phase_steps
        apply_targets(model, data, amap, targets, steps, pin_ball=pin_ball, ball_qadr=ball_qadr, ball_pos=ball_start)
        phase_metrics = metrics(model, data, ball_start)
        shot = render(model, data, VIS / f"{idx:02d}_{phase}.png")
        screenshots[phase] = shot
        phase_results.append({"phase": phase, "metrics": phase_metrics, "screenshot": shot})
    open_m = phase_results[0]["metrics"]
    hold_m = phase_results[-1]["metrics"]
    body_interferes = any(r["metrics"]["contact"]["body_contact_count"] > 0 for r in phase_results)
    failures = []
    if hold_m["contact"]["ball_hand_contact_count"] < 1:
        failures.append("no ball-hand contact at hold")
    if hold_m["contact"]["max_penetration"] > 0.012:
        failures.append("hold max penetration > 12mm")
    if body_interferes:
        failures.append("body proxy/contact interfered with grasp")
    if hold_m["ball_displacement"] is not None and pin_ball and hold_m["ball_displacement"] > 1e-6:
        failures.append("pinned ball unexpectedly moved")
    status = "PASS" if not failures else "PARTIAL"
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": scene,
        "pin_ball": pin_ball,
        "model_summary": {"nbody": int(model.nbody), "njnt": int(model.njnt), "nu": int(model.nu), "ngeom": int(model.ngeom), "nmesh": int(model.nmesh)},
        "status": status,
        "failure_reasons": failures,
        "open_contact_count": open_m["contact"]["contact_count"],
        "open_max_penetration": open_m["contact"]["max_penetration"],
        "hold_contact_count": hold_m["contact"]["contact_count"],
        "hold_ball_hand_contact_count": hold_m["contact"]["ball_hand_contact_count"],
        "hold_max_penetration": hold_m["contact"]["max_penetration"],
        "ball_displacement": hold_m["ball_displacement"],
        "fingertip_distances": hold_m["tip_ball_distances"],
        "body_proxy_interfered": body_interferes,
        "phase_results": phase_results,
        "screenshots": screenshots,
    }


def write_report(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.parent.mkdir(parents=True, exist_ok=True)
    write_json(META, payload)
    lines = [
        "# Body Connected Grasp Smoke Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Pinned ball: `{payload['pin_ball']}`\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Open contact count: `{payload['open_contact_count']}`\n",
        f"- Open max penetration: `{payload['open_max_penetration']:.6f} m`\n",
        f"- Hold contact count: `{payload['hold_contact_count']}`\n",
        f"- Hold ball-hand contact count: `{payload['hold_ball_hand_contact_count']}`\n",
        f"- Hold max penetration: `{payload['hold_max_penetration']:.6f} m`\n",
        f"- Ball displacement: `{payload['ball_displacement']}`\n",
        f"- Body proxy interfered: `{payload['body_proxy_interfered']}`\n\n",
        "## Failure Reasons\n\n",
    ]
    if payload["failure_reasons"]:
        for reason in payload["failure_reasons"]:
            lines.append(f"- {reason}\n")
    else:
        lines.append("- None.\n")
    lines.extend(["\n## Fingertip Distances At Hold\n\n"])
    for name, dist in payload["fingertip_distances"].items():
        lines.append(f"- `{name}`: `{dist}` m\n")
    lines.extend(["\n## Screenshots\n\n"])
    for phase, shot in payload["screenshots"].items():
        lines.append(f"- `{phase}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is a pinned-ball scripted smoke consistent with the previous arm-hand Stage1 smoke style; it validates that adding the body did not break actuator control or the existing grasp smoke path.\n",
            "- Because the body proxy contact is disabled in this first pass, this test does not validate load-bearing body collision.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--phase-steps", type=int, default=80)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--free-ball", action="store_true", help="Do not pin the ball during the scripted smoke.")
    args = parser.parse_args()
    payload = run(Path(args.scene), args.phase_steps, args.hold_steps, pin_ball=not args.free_ball)
    write_report(payload)
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    print(f"Status: {payload['status']}")


if __name__ == "__main__":
    main()
