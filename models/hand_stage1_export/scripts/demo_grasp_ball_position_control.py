from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from clean_mesh_common import render_png, set_ball_position, write_json
from demo_grasp_ball_primitive import STAGE_ORDER, STAGE_TARGETS as BASE_STAGE_TARGETS


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball_visual_clean_collision_proxy.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
OUT_DIR = DOCS_DIR / "visual_checks_position_control_grasp"
REPORT_MD = DOCS_DIR / "position_control_grasp_ball_report.md"
REPORT_JSON = METADATA_DIR / "position_control_grasp_ball.json"
BALL_POSITION = [0.0, -0.1, 0.195]
BALL_RADIUS = 0.025
CONTROLLED_JOINTS = [
    "wrist_1_joint",
    "wrist_2_joint",
    "index_mcp_flex_joint",
    "index_mcp_abd_joint",
    "index_pip_joint",
    "index_dip_joint",
    "middle_mcp_flex_joint",
    "middle_mcp_abd_joint",
    "middle_pip_joint",
    "middle_dip_joint",
    "ring_mcp_flex_joint",
    "ring_mcp_abd_joint",
    "ring_pip_joint",
    "ring_dip_joint",
    "little_mcp_flex_joint",
    "little_mcp_abd_joint",
    "little_pip_joint",
    "little_dip_joint",
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]
TIP_SITES = [
    "index_tip_site",
    "middle_tip_site",
    "ring_tip_site",
    "little_tip_site",
    "thumb_tip_site",
]
STAGE_TO_FILE = {
    "open_hand": "open_hand.png",
    "approach_pre_shape": "preshape.png",
    "close_four_fingers": "four_fingers_closed.png",
    "close_thumb": "thumb_closed.png",
    "hold": "hold.png",
}


def full_stage_targets(stage_name: str) -> dict[str, float]:
    targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    targets.update(BASE_STAGE_TARGETS[stage_name])
    return targets


def blend(start: dict[str, float], end: dict[str, float], fraction: float) -> dict[str, float]:
    names = sorted(set(start) | set(end))
    return {name: float(start.get(name, 0.0)) + (float(end.get(name, 0.0)) - float(start.get(name, 0.0))) * fraction for name in names}


def load_model():
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def actuator_map(model, mujoco) -> dict[str, int]:
    mapping = {}
    for aid in range(model.nu):
        actuator_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
        if actuator_name and actuator_name.endswith("_pos"):
            mapping[actuator_name[: -len("_pos")]] = aid
    return mapping


def joint_map(model, mujoco) -> dict[str, int]:
    return {
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid): jid
        for jid in range(model.njnt)
        if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
    }


def set_ctrl(model, data, targets: dict[str, float], act_map: dict[str, int]) -> dict[str, float]:
    applied = {}
    for name, target in targets.items():
        aid = act_map.get(name)
        if aid is None:
            continue
        low, high = [float(value) for value in model.actuator_ctrlrange[aid]]
        value = min(max(float(target), low), high)
        data.ctrl[aid] = value
        applied[name] = value
    return applied


def actual_qpos(model, data, joints: dict[str, int]) -> dict[str, float]:
    values = {}
    for name in CONTROLLED_JOINTS:
        jid = joints.get(name)
        if jid is None:
            continue
        values[name] = float(data.qpos[int(model.jnt_qposadr[jid])])
    return values


def ball_contact_summary(model, data, mujoco) -> dict:
    ball_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
    contacts = []
    for cid in range(data.ncon):
        con = data.contact[cid]
        if int(con.geom1) != ball_geom and int(con.geom2) != ball_geom:
            continue
        other = int(con.geom2) if int(con.geom1) == ball_geom else int(con.geom1)
        contacts.append(
            {
                "dist": float(con.dist),
                "other_geom": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, other) or f"geom_{other}",
            }
        )
    min_dist = min((item["dist"] for item in contacts), default=0.0)
    return {"ball_contact_count": len(contacts), "max_penetration": float(max(0.0, -min_dist)), "ball_contacts": contacts}


def fingertip_distances(model, data, mujoco) -> dict:
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    center = np.array(data.xpos[ball_body], dtype=float)
    distances = {}
    for site in TIP_SITES:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site)
        if sid < 0:
            distances[site] = None
        else:
            distances[site] = float(np.linalg.norm(np.array(data.site_xpos[sid], dtype=float) - center))
    four = [distances[name] for name in TIP_SITES[:4] if distances[name] is not None]
    all_tips = [value for value in distances.values() if value is not None]
    return {
        "ball_center": center.tolist(),
        "distances": distances,
        "mean_four_tip_distance": float(np.mean(four)) if four else None,
        "mean_all_tip_distance": float(np.mean(all_tips)) if all_tips else None,
    }


def stage_summary(model, data, mujoco, joints: dict[str, int], targets: dict[str, float], applied: dict[str, float]) -> dict:
    summary = {}
    summary.update(ball_contact_summary(model, data, mujoco))
    summary.update(fingertip_distances(model, data, mujoco))
    summary["target_angles"] = dict(targets)
    summary["ctrl_applied"] = dict(applied)
    summary["qpos_actual"] = actual_qpos(model, data, joints)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Position-actuator controlled clean visual/collision proxy ball grasp demo.")
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--speed", type=float, default=1.0, help="Stage speed multiplier; larger is faster.")
    parser.add_argument("--hold-steps", type=int, default=300)
    parser.add_argument("--gravity", action="store_true", help="Enable model gravity. Default is zero gravity for ball-placement smoke test.")
    parser.add_argument("--pin-ball", action="store_true", help="Keep the ball fixed at the requested pose during the demo.")
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ball_position = [args.ball_x, args.ball_y, args.ball_z]

    try:
        mujoco, model, data = load_model()
    except Exception as exc:
        report = {"load_success": False, "scene": str(SCENE_XML), "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    if not args.gravity:
        model.opt.gravity[:] = 0.0

    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    missing_actuators = sorted(set(CONTROLLED_JOINTS) - set(act_map))
    set_ball_position(model, data, mujoco, ball_position)
    set_ctrl(model, data, full_stage_targets("open_hand"), act_map)
    mujoco.mj_forward(model, data)

    viewer = None
    if args.viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(model, data)
        except Exception as exc:
            print(f"Viewer launch failed; continuing headless. Reason: {type(exc).__name__}: {exc}")

    stage_steps = max(20, int(400 / max(args.speed, 0.05)))
    previous_targets = full_stage_targets("open_hand")
    stage_reports = {}
    renders = []
    for stage_name in STAGE_ORDER:
        targets = full_stage_targets(stage_name)
        steps = args.hold_steps if stage_name == "hold" else stage_steps
        applied = {}
        print(f"\n[{stage_name}] target joint angles (rad)")
        for name in CONTROLLED_JOINTS:
            print(f"  {name}: {targets.get(name, 0.0): .4f}")
        for step in range(steps):
            fraction = (step + 1) / max(steps, 1)
            command = blend(previous_targets, targets, fraction)
            applied = set_ctrl(model, data, command, act_map)
            if args.pin_ball:
                set_ball_position(model, data, mujoco, ball_position)
            mujoco.mj_step(model, data)
            if viewer is not None:
                viewer.sync()
                time.sleep(0.002)
        mujoco.mj_forward(model, data)
        stage_reports[stage_name] = stage_summary(model, data, mujoco, joints, targets, applied)
        if not args.no_screenshots:
            renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / STAGE_TO_FILE[stage_name], width=1200, height=850))
        previous_targets = targets

    if viewer is not None:
        print("Position-control demo reached hold stage. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(0.01)
        viewer.close()

    report = {
        "load_success": True,
        "scene": str(SCENE_XML),
        "ball_position_requested": ball_position,
        "gravity_enabled": bool(args.gravity),
        "pin_ball": bool(args.pin_ball),
        "speed": args.speed,
        "stage_steps": stage_steps,
        "hold_steps": args.hold_steps,
        "actuator_count": int(model.nu),
        "missing_actuators": missing_actuators,
        "stage_order": STAGE_ORDER,
        "stage_reports": stage_reports,
        "renders": renders,
        "notes": [
            "Hand joints are controlled through position actuators via data.ctrl; hand qpos is not directly written during the demo.",
            "Default runtime gravity is zero so the ball-placement smoke test does not immediately drop the ball.",
            "Clean STL geoms remain visual-only; simplified primitive geoms provide collision proxy contacts.",
            "Thumb opposition remains a separate audit item and is not corrected here.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Position Control Grasp Ball Report",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position requested: `{report.get('ball_position_requested', BALL_POSITION)}`",
            f"- Gravity enabled: {report.get('gravity_enabled')}",
            f"- Pin ball: {report.get('pin_ball')}",
            f"- Actuator count: {report.get('actuator_count', 'unknown')}",
            f"- Missing actuators: {', '.join(report.get('missing_actuators', [])) if report.get('missing_actuators') else 'None'}",
            "",
            "## Stage Summary",
            "",
            "| Stage | Ball contacts | Max penetration (m) | Mean 4-tip distance (m) | Thumb distance (m) |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for stage in report.get("stage_order", []):
        item = report.get("stage_reports", {}).get(stage, {})
        thumb = item.get("distances", {}).get("thumb_tip_site")
        lines.append(
            f"| {stage} | {item.get('ball_contact_count', 'N/A')} | {item.get('max_penetration', 0.0):.6f} | "
            f"{item.get('mean_four_tip_distance', 0.0):.6f} | {thumb if thumb is not None else 'N/A'} |"
        )
    lines.extend(["", "## Renders", ""])
    for item in report.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
