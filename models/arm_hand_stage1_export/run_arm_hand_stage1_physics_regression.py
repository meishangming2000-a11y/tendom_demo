#!/usr/bin/env python3
"""Run the arm + export4 hand physics-v0 regression checks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_joint_limit_collision_proxy_ball.xml"
REPORT = DOCS / "arm_hand_stage1_physics_regression_report.md"
META_OUT = META / "arm_hand_stage1_physics_regression.json"
VIS = DOCS / "visual_checks_arm_hand_physics_regression"

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

STAGES = [
    ("open_hand", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close_four_fingers", LONG_FINGER_TARGETS),
    ("close_thumb_smoke", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
]

FINGERTIP_SITES = [
    "index_tip_site",
    "middle_tip_site",
    "ring_tip_site",
    "little_tip_site",
    "thumb_tip_site",
]


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def name_or(model, mujoco, objtype, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, objtype, idx) or fallback


def load(scene: Path):
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return mujoco, model, data


def model_summary(model) -> dict[str, int]:
    return {
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nu": int(model.nu),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "nmesh": int(model.nmesh),
        "nq": int(model.nq),
        "nv": int(model.nv),
    }


def contact_summary(model, data, mujoco) -> dict[str, Any]:
    rows = []
    max_pen = 0.0
    ball_hand = 0
    for i in range(data.ncon):
        c = data.contact[i]
        g1, g2 = int(c.geom1), int(c.geom2)
        b1, b2 = int(model.geom_bodyid[g1]), int(model.geom_bodyid[g2])
        names = [
            name_or(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, g1, f"geom_{g1}"),
            name_or(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, g2, f"geom_{g2}"),
            name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, b1, f"body_{b1}"),
            name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, b2, f"body_{b2}"),
        ]
        pen = max(0.0, -float(c.dist))
        max_pen = max(max_pen, pen)
        if any("ball" in n for n in names) and any(("palm" in n or "finger" in n or "thumb" in n or "distal" in n or "proximal" in n) for n in names):
            ball_hand += 1
        rows.append(
            {
                "geom1": names[0],
                "geom2": names[1],
                "body1": names[2],
                "body2": names[3],
                "dist": float(c.dist),
                "penetration": pen,
                "pos": np.array(c.pos).copy(),
            }
        )
    rows.sort(key=lambda row: row["penetration"], reverse=True)
    return {"count": int(data.ncon), "max_penetration": float(max_pen), "ball_hand_contact_count": ball_hand, "top_contacts": rows[:20]}


def fingertip_distances(model, data, mujoco) -> dict[str, float]:
    ball_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    if ball_id < 0:
        return {site: float("nan") for site in FINGERTIP_SITES}
    ball = data.xpos[ball_id].copy()
    distances = {}
    for site in FINGERTIP_SITES:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site)
        if sid < 0:
            distances[site] = float("nan")
        else:
            distances[site] = float(np.linalg.norm(data.site_xpos[sid] - ball))
    return distances


def qpos_target_for_joint(model, mujoco, jid: int, magnitude: float) -> float:
    if not bool(model.jnt_limited[jid]):
        return magnitude
    lo, hi = model.jnt_range[jid]
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or ""
    if name.endswith("_mcp_abd_joint") or name.endswith("_pip_joint") or name.endswith("_dip_joint") or name == "thumb_ip_joint":
        return float(np.clip(-abs(magnitude), lo, hi))
    return float(np.clip(magnitude, lo, hi))


def joint_kinematic_smoke(model, data, mujoco, magnitude: float) -> dict[str, Any]:
    base_qpos = data.qpos.copy()
    rows = []
    for jid in range(model.njnt):
        name = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_JOINT, jid, f"joint_{jid}")
        if model.jnt_type[jid] != mujoco.mjtJoint.mjJNT_HINGE:
            rows.append({"joint": name, "status": "SKIPPED", "reason": "not hinge"})
            continue
        qadr = int(model.jnt_qposadr[jid])
        body = int(model.jnt_bodyid[jid])
        target = qpos_target_for_joint(model, mujoco, jid, magnitude)
        data.qpos[:] = base_qpos
        data.qvel[:] = 0
        mujoco.mj_forward(model, data)
        before = data.xmat[body].copy()
        data.qpos[qadr] = target
        mujoco.mj_forward(model, data)
        rot_delta = float(np.linalg.norm(data.xmat[body] - before))
        finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.xpos).all())
        rows.append({"joint": name, "target": target, "rot_delta": rot_delta, "status": "PASS" if finite else "FAIL"})
    data.qpos[:] = base_qpos
    data.qvel[:] = 0
    mujoco.mj_forward(model, data)
    return {
        "total": len(rows),
        "pass": sum(1 for row in rows if row["status"] == "PASS"),
        "fail": sum(1 for row in rows if row["status"] == "FAIL"),
        "skipped": sum(1 for row in rows if row["status"] == "SKIPPED"),
        "rows": rows,
    }


def ctrl_from_targets(model, mujoco, targets: dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for aid in range(model.nu):
        aname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid) or ""
        jname = aname[:-4] if aname.endswith("_pos") else aname
        if aname.startswith("a_"):
            jname = aname[2:]
        value = float(targets.get(jname, 0.0))
        if bool(model.actuator_ctrllimited[aid]):
            lo, hi = model.actuator_ctrlrange[aid]
            value = float(np.clip(value, lo, hi))
        ctrl[aid] = value
    return ctrl


def find_ball_freejoint(model, mujoco) -> tuple[int | None, int | None, np.ndarray | None]:
    ball_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    if ball_id < 0:
        return None, None, None
    for jid in range(model.njnt):
        if int(model.jnt_bodyid[jid]) == ball_id and model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE:
            return int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid]), None
    return None, None, None


def run_staged_smoke(model, data, mujoco, phase_steps: int, hold_steps: int) -> dict[str, Any]:
    ball_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    ball_qadr, ball_dadr, _ = find_ball_freejoint(model, mujoco)
    ball_start = data.xpos[ball_id].copy() if ball_id >= 0 else None
    finite = True
    stages = []
    for stage_name, targets in STAGES:
        target_ctrl = ctrl_from_targets(model, mujoco, targets)
        start_ctrl = data.ctrl.copy()
        steps = hold_steps if stage_name == "hold" else phase_steps
        for i in range(max(1, steps)):
            alpha = i / max(1, steps - 1)
            data.ctrl[:] = (1 - alpha) * start_ctrl + alpha * target_ctrl
            if ball_qadr is not None and ball_dadr is not None and ball_start is not None:
                data.qpos[ball_qadr : ball_qadr + 3] = ball_start
                data.qpos[ball_qadr + 3 : ball_qadr + 7] = [1.0, 0.0, 0.0, 0.0]
                data.qvel[ball_dadr : ball_dadr + 6] = 0.0
            mujoco.mj_step(model, data)
            finite = finite and bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all() and np.isfinite(data.xpos).all())
        stages.append(
            {
                "name": stage_name,
                "contact": contact_summary(model, data, mujoco),
                "fingertip_ball_distances": fingertip_distances(model, data, mujoco),
            }
        )
    ball_disp = float(np.linalg.norm(data.xpos[ball_id] - ball_start)) if ball_id >= 0 and ball_start is not None else 0.0
    return {"finite": finite, "ball_displacement": ball_disp, "stages": stages}


def render(model, data, mujoco, path: Path, lookat: np.ndarray, distance=0.86, azimuth=205, elevation=-22) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = distance
        cam.azimuth = azimuth
        cam.elevation = elevation
        renderer.update_scene(data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(path, img)
    return str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--phase-steps", type=int, default=260)
    parser.add_argument("--hold-steps", type=int, default=360)
    parser.add_argument("--joint-magnitude", type=float, default=0.12)
    args = parser.parse_args()

    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)

    scene = Path(args.scene).resolve()
    tests = []
    try:
        mujoco, model, data = load(scene)
        tests.append({"name": "model_load", "status": "PASS", "detail": model_summary(model)})
    except Exception as exc:
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "scene": str(scene),
            "overall_status": "FAIL",
            "tests": [{"name": "model_load", "status": "FAIL", "detail": str(exc)}],
        }
        META_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        REPORT.write_text(f"# Arm-Hand Stage1 Physics Regression Report\n\nModel load failed:\n\n`{exc}`\n", encoding="utf-8")
        print(f"FAIL model load: {exc}")
        return

    joint_smoke = joint_kinematic_smoke(model, data, mujoco, args.joint_magnitude)
    tests.append({"name": "joint_kinematic_smoke", "status": "PASS" if joint_smoke["fail"] == 0 else "FAIL", "detail": {k: joint_smoke[k] for k in ["total", "pass", "fail", "skipped"]}})

    open_contact = contact_summary(model, data, mujoco)
    tests.append(
        {
            "name": "open_static_contact",
            "status": "PASS" if open_contact["max_penetration"] < 0.005 else "FAIL",
            "detail": {"count": open_contact["count"], "max_penetration": open_contact["max_penetration"]},
        }
    )

    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = data.xpos[palm_id].copy() if palm_id >= 0 else np.array([0.0, 0.0, 0.4])
    open_render = render(model, data, mujoco, VIS / "regression_open.png", lookat)

    staged = run_staged_smoke(model, data, mujoco, args.phase_steps, args.hold_steps)
    hold = staged["stages"][-1] if staged["stages"] else {"contact": {"count": 0, "max_penetration": 0.0}, "fingertip_ball_distances": {}}
    hold_distances = hold["fingertip_ball_distances"]
    four_values = [hold_distances.get(site, float("nan")) for site in FINGERTIP_SITES if site != "thumb_tip_site"]
    four_avg = float(np.nanmean(four_values)) if four_values else float("nan")
    staged_status = "PASS" if staged["finite"] and hold["contact"]["max_penetration"] < 0.02 else "FAIL"
    tests.append(
        {
            "name": "scripted_ball_contact_smoke",
            "status": staged_status,
            "detail": {
                "finite": staged["finite"],
                "hold_contacts": hold["contact"]["count"],
                "hold_max_penetration": hold["contact"]["max_penetration"],
                "ball_displacement": staged["ball_displacement"],
                "four_finger_avg_tip_ball_distance": four_avg,
                "thumb_ball_distance": hold_distances.get("thumb_tip_site", float("nan")),
            },
        }
    )
    hold_render = render(model, data, mujoco, VIS / "regression_hold.png", lookat)

    overall = "PASS" if all(row["status"] == "PASS" for row in tests) else "PARTIAL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "overall_status": overall,
        "model_summary": model_summary(model),
        "tests": tests,
        "joint_smoke": joint_smoke,
        "open_contact": open_contact,
        "staged_smoke": staged,
        "renders": {"open": open_render, "hold": hold_render},
        "training_ready": False,
        "dataset_v0_ready": overall in {"PASS", "PARTIAL"} and staged["finite"],
    }
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 Physics Regression Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{scene}`\n",
        f"- Overall status: **{overall}**\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Training ready: **No**\n",
        f"- Dataset v0 ready: **{'Yes, tiny smoke only' if payload['dataset_v0_ready'] else 'No'}**\n",
        f"- Open render: `{open_render}`\n",
        f"- Hold render: `{hold_render}`\n\n",
        "## Test Results\n\n",
        "| test | status | detail |\n",
        "|---|---|---|\n",
    ]
    for row in tests:
        lines.append(f"| {row['name']} | {row['status']} | `{json.dumps(json_ready(row['detail']), ensure_ascii=False)}` |\n")
    lines.extend(
        [
            "\n## Notes\n\n",
            "- This checks model load, hinge kinematics, static contact, and a pinned-ball scripted contact smoke.\n",
            "- The collision proxy is still v0 and should not be treated as final physics or training geometry.\n",
            "- If this report is PARTIAL, inspect the failing rows before collecting more data.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"{overall}: saved {REPORT}")
    print(f"Metadata: {META_OUT}")


if __name__ == "__main__":
    main()
