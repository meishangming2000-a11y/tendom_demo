#!/usr/bin/env python3
"""Test collision-proxy v2 with free-ball, scripted-close, and local ball sweep."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np

from arm_hand_stage1_task_api import json_ready


ROOT = Path(__file__).resolve().parent
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_collision_proxy_v2_ball.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_arm_hand_collision_proxy_v2"
REPORT = DOCS / "arm_hand_collision_proxy_v2_smoke_report.md"
META_OUT = META / "arm_hand_collision_proxy_v2_smoke.json"

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

THUMB_SMOKE_TARGETS = {
    "thumb_cmc_abd_joint": -0.30,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}

PHASES = [
    ("open_hand", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close_four_fingers", LONG_FINGER_TARGETS),
    ("close_thumb_smoke", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
]

TIP_SITES = ["index_tip_site", "middle_tip_site", "ring_tip_site", "little_tip_site", "thumb_tip_site"]


def name_or(model, mujoco, objtype, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, objtype, idx) or fallback


def load(scene: Path):
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return mujoco, model, data


def ball_joint(model, mujoco) -> tuple[int | None, int | None, int]:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    if bid < 0:
        return None, None, bid
    for jid in range(model.njnt):
        if int(model.jnt_bodyid[jid]) == bid and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE:
            return int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid]), bid
    return None, None, bid


def contact_summary(model, data, mujoco) -> dict[str, Any]:
    rows = []
    max_pen = 0.0
    ball_hand = 0
    for i in range(data.ncon):
        c = data.contact[i]
        g1, g2 = int(c.geom1), int(c.geom2)
        b1, b2 = int(model.geom_bodyid[g1]), int(model.geom_bodyid[g2])
        geom1 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, g1, f"geom_{g1}")
        geom2 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, g2, f"geom_{g2}")
        body1 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, b1, f"body_{b1}")
        body2 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, b2, f"body_{b2}")
        names = [geom1, geom2, body1, body2]
        pen = max(0.0, -float(c.dist))
        max_pen = max(max_pen, pen)
        if any("ball" in n for n in names) and any(("palm" in n or "finger" in n or "thumb" in n or "distal" in n or "proximal" in n or "wrist" in n or "mcp" in n) for n in names):
            ball_hand += 1
        rows.append({"geom1": geom1, "geom2": geom2, "body1": body1, "body2": body2, "dist": float(c.dist), "penetration": pen, "pos": np.asarray(c.pos).copy()})
    rows.sort(key=lambda row: row["penetration"], reverse=True)
    return {"contact_count": int(data.ncon), "max_penetration": float(max_pen), "ball_hand_contact_count": int(ball_hand), "top_contacts": rows[:12]}


def ctrl_from_targets(model, mujoco, targets: dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu)
    for aid in range(model.nu):
        aname = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR, aid, f"actuator_{aid}")
        jname = aname[:-4] if aname.endswith("_pos") else aname
        if aname.startswith("a_"):
            jname = aname[2:]
        value = float(targets.get(jname, 0.0))
        if bool(model.actuator_ctrllimited[aid]):
            lo, hi = model.actuator_ctrlrange[aid]
            value = float(np.clip(value, lo, hi))
        ctrl[aid] = value
    return ctrl


def render(model, data, mujoco, path: Path) -> str:
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = data.xpos[palm_id].copy() if palm_id >= 0 else np.array([0.0, 0.0, 0.4])
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = 0.86
        cam.azimuth = 205
        cam.elevation = -22
        renderer.update_scene(data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, img)
    return str(path)


def tip_distances(model, data, mujoco) -> dict[str, float]:
    _, _, bid = ball_joint(model, mujoco)
    ball = data.xpos[bid].copy() if bid >= 0 else np.full(3, np.nan)
    out = {}
    for site in TIP_SITES:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site)
        out[site] = float(np.linalg.norm(data.site_xpos[sid] - ball)) if sid >= 0 and not np.isnan(ball).any() else float("nan")
    return out


def set_ball_to_palm_local(model, data, mujoco, local_xyz: np.ndarray) -> np.ndarray:
    qadr, dadr, _ = ball_joint(model, mujoco)
    palm = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    mujoco.mj_forward(model, data)
    palm_pos = data.xpos[palm].copy()
    palm_mat = data.xmat[palm].reshape(3, 3).copy()
    world = palm_pos + palm_mat @ np.asarray(local_xyz, dtype=np.float64)
    if qadr is not None and dadr is not None:
        data.qpos[qadr : qadr + 3] = world
        data.qpos[qadr + 3 : qadr + 7] = [1, 0, 0, 0]
        data.qvel[dadr : dadr + 6] = 0
    mujoco.mj_forward(model, data)
    return world


def run_scripted_pinned_metrics(model, data, mujoco, steps: int) -> dict[str, Any]:
    qadr, dadr, bid = ball_joint(model, mujoco)
    ball_start = data.xpos[bid].copy()
    finite = True
    stages = []
    for phase, targets in PHASES:
        start_ctrl = data.ctrl.copy()
        target = ctrl_from_targets(model, mujoco, targets)
        for i in range(steps):
            alpha = i / max(1, steps - 1)
            data.ctrl[:] = (1 - alpha) * start_ctrl + alpha * target
            if qadr is not None and dadr is not None:
                data.qpos[qadr : qadr + 3] = ball_start
                data.qpos[qadr + 3 : qadr + 7] = [1, 0, 0, 0]
                data.qvel[dadr : dadr + 6] = 0
            mujoco.mj_step(model, data)
            finite = finite and bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
        stages.append({"phase": phase, "contact": contact_summary(model, data, mujoco), "tip_distances": tip_distances(model, data, mujoco)})
    return {"finite": finite, "stages": stages}


def run_local_ball_sweep(model, mujoco, free_steps: int, phase_steps: int) -> list[dict[str, Any]]:
    rows = []
    offsets = [
        np.array([x, 0.12, z], dtype=np.float64)
        for x in [0.035, 0.04, 0.045]
        for z in [-0.03, -0.02, -0.01]
    ]
    for local in offsets:
        data = mujoco.MjData(model)
        world = set_ball_to_palm_local(model, data, mujoco, local)
        start = data.xpos[ball_joint(model, mujoco)[2]].copy()
        start_contact = contact_summary(model, data, mujoco)
        finite = True
        for _ in range(free_steps):
            mujoco.mj_step(model, data)
            finite = finite and bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
        end = data.xpos[ball_joint(model, mujoco)[2]].copy()

        data_hold = mujoco.MjData(model)
        set_ball_to_palm_local(model, data_hold, mujoco, local)
        scripted = run_scripted_pinned_metrics(model, data_hold, mujoco, phase_steps)
        hold = scripted["stages"][-1]
        four = [hold["tip_distances"][site] for site in TIP_SITES if site != "thumb_tip_site"]
        row = {
            "ball_local": local,
            "ball_world": world,
            "finite": bool(finite and scripted["finite"]),
            "start_ball_hand_contacts": start_contact["ball_hand_contact_count"],
            "start_max_penetration": start_contact["max_penetration"],
            "free_displacement": float(np.linalg.norm(end - start)),
            "free_vertical_drop": float(start[2] - end[2]),
            "free_end_contacts": contact_summary(model, data, mujoco)["ball_hand_contact_count"],
            "hold_contacts": hold["contact"]["contact_count"],
            "hold_ball_hand_contacts": hold["contact"]["ball_hand_contact_count"],
            "hold_max_penetration": hold["contact"]["max_penetration"],
            "hold_four_finger_avg_tip_ball_distance": float(np.mean(four)),
            "hold_thumb_ball_distance": hold["tip_distances"]["thumb_tip_site"],
        }
        row["pass_smoke"] = bool(
            row["finite"]
            and row["start_max_penetration"] <= 0.006
            and row["hold_ball_hand_contacts"] >= 1
            and row["hold_max_penetration"] <= 0.010
        )
        rows.append(row)
    return rows


def run_free_ball_open(model, data, mujoco, steps: int) -> dict[str, Any]:
    _, _, bid = ball_joint(model, mujoco)
    start = data.xpos[bid].copy()
    screenshots = {"start": render(model, data, mujoco, VIS / "v2_free_ball_start.png")}
    start_contact = contact_summary(model, data, mujoco)
    finite = True
    for _ in range(steps):
        mujoco.mj_step(model, data)
        finite = finite and bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all() and np.isfinite(data.xpos).all())
    end = data.xpos[bid].copy()
    screenshots["end"] = render(model, data, mujoco, VIS / "v2_free_ball_after_open.png")
    return {
        "finite": finite,
        "steps": steps,
        "start_ball": start,
        "end_ball": end,
        "ball_displacement": float(np.linalg.norm(end - start)),
        "vertical_drop": float(start[2] - end[2]),
        "start_contact": start_contact,
        "end_contact": contact_summary(model, data, mujoco),
        "screenshots": screenshots,
    }


def run_scripted_pinned(model, data, mujoco, steps: int) -> dict[str, Any]:
    qadr, dadr, bid = ball_joint(model, mujoco)
    ball_start = data.xpos[bid].copy()
    stages = []
    screenshots = {}
    finite = True
    for phase_idx, (phase, targets) in enumerate(PHASES):
        start_ctrl = data.ctrl.copy()
        target = ctrl_from_targets(model, mujoco, targets)
        for i in range(steps):
            alpha = i / max(1, steps - 1)
            data.ctrl[:] = (1 - alpha) * start_ctrl + alpha * target
            if qadr is not None and dadr is not None:
                data.qpos[qadr : qadr + 3] = ball_start
                data.qpos[qadr + 3 : qadr + 7] = [1, 0, 0, 0]
                data.qvel[dadr : dadr + 6] = 0
            mujoco.mj_step(model, data)
            finite = finite and bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
        stages.append({"phase": phase, "contact": contact_summary(model, data, mujoco), "tip_distances": tip_distances(model, data, mujoco)})
        screenshots[phase] = render(model, data, mujoco, VIS / f"v2_scripted_{phase}.png")
    return {"finite": finite, "ball_start": ball_start, "stages": stages, "screenshots": screenshots}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--free-steps", type=int, default=300)
    parser.add_argument("--phase-steps", type=int, default=70)
    parser.add_argument("--sweep-free-steps", type=int, default=150)
    args = parser.parse_args()

    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    VIS.mkdir(parents=True, exist_ok=True)

    scene = Path(args.scene).resolve()
    mujoco, model, data = load(scene)
    free_result = run_free_ball_open(model, data, mujoco, args.free_steps)

    mujoco, model, data = load(scene)
    scripted = run_scripted_pinned(model, data, mujoco, args.phase_steps)
    hold = scripted["stages"][-1]
    four = [hold["tip_distances"][site] for site in TIP_SITES if site != "thumb_tip_site"]
    sweep = run_local_ball_sweep(model, mujoco, args.sweep_free_steps, args.phase_steps)
    sweep_pass_count = sum(1 for row in sweep if row["pass_smoke"])

    status = "PASS"
    issues = []
    if not free_result["finite"] or not scripted["finite"]:
        status = "FAIL"
        issues.append("non-finite simulation")
    if free_result["start_contact"]["ball_hand_contact_count"] < 1:
        status = "PARTIAL"
        issues.append("free ball does not initially contact hand")
    if free_result["start_contact"]["max_penetration"] > 0.006:
        status = "PARTIAL"
        issues.append("initial free-ball penetration exceeds 6mm")
    if hold["contact"]["max_penetration"] > 0.01:
        status = "PARTIAL"
        issues.append("scripted hold penetration exceeds 10mm")

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": scene,
        "model_summary": {"nbody": model.nbody, "njnt": model.njnt, "nu": model.nu, "ngeom": model.ngeom, "nsite": model.nsite, "nmesh": model.nmesh},
        "free_ball_open": free_result,
        "scripted_pinned": scripted,
        "hold_metrics": {
            "contact_count": hold["contact"]["contact_count"],
            "ball_hand_contact_count": hold["contact"]["ball_hand_contact_count"],
            "max_penetration": hold["contact"]["max_penetration"],
            "four_finger_avg_tip_ball_distance": float(np.mean(four)),
            "thumb_ball_distance": hold["tip_distances"]["thumb_tip_site"],
        },
        "local_ball_sweep": sweep,
        "local_ball_sweep_pass_count": sweep_pass_count,
        "local_ball_sweep_total": len(sweep),
        "status": status,
        "issues": issues,
        "training_ready": False,
    }
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Collision Proxy V2 Smoke Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{scene}`\n",
        f"- Status: **{status}**\n",
        f"- Model summary: `{json_ready(payload['model_summary'])}`\n",
        f"- Free ball start contacts: `{free_result['start_contact']['contact_count']}`\n",
        f"- Free ball start ball-hand contacts: `{free_result['start_contact']['ball_hand_contact_count']}`\n",
        f"- Free ball start max penetration: `{free_result['start_contact']['max_penetration']:.6f} m`\n",
        f"- Free ball displacement after `{args.free_steps}` open steps: `{free_result['ball_displacement']:.6f} m`\n",
        f"- Free ball vertical drop after open steps: `{free_result['vertical_drop']:.6f} m`\n",
        f"- Scripted hold contacts: `{hold['contact']['contact_count']}`\n",
        f"- Scripted hold ball-hand contacts: `{hold['contact']['ball_hand_contact_count']}`\n",
        f"- Scripted hold max penetration: `{hold['contact']['max_penetration']:.6f} m`\n",
        f"- Four-finger avg tip-ball distance: `{payload['hold_metrics']['four_finger_avg_tip_ball_distance']:.6f} m`\n",
        f"- Thumb-ball distance: `{payload['hold_metrics']['thumb_ball_distance']:.6f} m`\n\n",
        f"- Local ball sweep PASS: `{sweep_pass_count} / {len(sweep)}`\n\n",
        "## Interpretation\n\n",
        "- v2 keeps the v1 palm contact idea but adds a shallow local `-Z` palm rail based on measured free-ball slide direction.\n",
        "- If free-ball displacement is still large, that means the palm is tilted and the ball rolls/slides; pinned scripted close remains the repeatable contact smoke.\n",
        "- Training remains blocked; this is still a smoke proxy.\n\n",
        "## Local Ball Sweep\n\n",
        "| local xyz | start contact | start pen | free disp | free drop | hold contacts | hold pen | four avg | thumb-ball | pass |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in sweep:
        lines.append(
            f"| `{np.round(row['ball_local'], 4).tolist()}` | {row['start_ball_hand_contacts']} | "
            f"{row['start_max_penetration']:.6f} | {row['free_displacement']:.4f} | "
            f"{row['free_vertical_drop']:.4f} | {row['hold_ball_hand_contacts']} | "
            f"{row['hold_max_penetration']:.6f} | {row['hold_four_finger_avg_tip_ball_distance']:.4f} | "
            f"{row['hold_thumb_ball_distance']:.4f} | {int(row['pass_smoke'])} |\n"
        )
    lines.extend([
        "\n",
        "## Screenshots\n\n",
    ])
    for key, path in {**free_result["screenshots"], **scripted["screenshots"]}.items():
        lines.append(f"- `{key}`: `{path}`\n")
    if issues:
        lines.append("\n## Issues\n\n")
        for issue in issues:
            lines.append(f"- {issue}\n")
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Status: {status}")
    print(f"Report: {REPORT}")
    print(f"Metadata: {META_OUT}")


if __name__ == "__main__":
    main()
