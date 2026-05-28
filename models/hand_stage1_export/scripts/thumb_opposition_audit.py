from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from clean_mesh_common import render_png, set_ball_position, write_json


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball_visual_clean_collision_proxy.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
OUT_DIR = DOCS_DIR / "visual_checks_thumb_opposition"
REPORT_MD = DOCS_DIR / "thumb_opposition_audit.md"
REPORT_JSON = METADATA_DIR / "thumb_opposition_candidates.json"
BALL_POSITION = [0.0, -0.1, 0.195]
THUMB_JOINTS = ["thumb_cmc_joint", "thumb_mcp_joint", "thumb_ip_joint"]
CMC_VALUES = [-0.8, -0.4, 0.0, 0.4, 0.8]
MCP_VALUES = [0.0, 0.4, 0.8, 1.2]
IP_VALUES = [0.0, 0.4, 0.8, 1.2]


def load_model():
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def joint_map(model, mujoco) -> dict[str, int]:
    return {
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid): jid
        for jid in range(model.njnt)
        if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
    }


def set_joint_qpos(model, data, joints: dict[str, int], targets: dict[str, float]) -> None:
    for name, value in targets.items():
        jid = joints.get(name)
        if jid is None:
            continue
        adr = int(model.jnt_qposadr[jid])
        low, high = [float(v) for v in model.jnt_range[jid]]
        data.qpos[adr] = min(max(float(value), low), high)


def measure(model, data, mujoco, joints: dict[str, int], pose: dict[str, float], ball_position: list[float]) -> dict:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    set_joint_qpos(model, data, joints, pose)
    mujoco.mj_forward(model, data)

    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    thumb_site = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "thumb_tip_site")
    index_site = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "index_tip_site")
    palm_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    ball_center = np.array(data.xpos[ball_body], dtype=float)
    thumb_pos = np.array(data.site_xpos[thumb_site], dtype=float)
    index_pos = np.array(data.site_xpos[index_site], dtype=float)
    palm_pos = np.array(data.xpos[palm_body], dtype=float)

    return {
        "pose": {name: float(pose.get(name, 0.0)) for name in THUMB_JOINTS},
        "thumb_tip": thumb_pos.tolist(),
        "index_tip": index_pos.tolist(),
        "ball_center": ball_center.tolist(),
        "palm_pos": palm_pos.tolist(),
        "thumb_to_ball": float(np.linalg.norm(thumb_pos - ball_center)),
        "thumb_to_index": float(np.linalg.norm(thumb_pos - index_pos)),
        "thumb_to_palm": float(np.linalg.norm(thumb_pos - palm_pos)),
        "thumb_ball_vector": (ball_center - thumb_pos).tolist(),
    }


def pose_label(pose: dict[str, float]) -> str:
    return f"cmc_{pose['thumb_cmc_joint']:+.2f}_mcp_{pose['thumb_mcp_joint']:+.2f}_ip_{pose['thumb_ip_joint']:+.2f}".replace("+", "p").replace("-", "m").replace(".", "d")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit thumb CMC/MCP/IP opposition directions without editing joint axes.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--render-count", type=int, default=8)
    args = parser.parse_args()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        mujoco, model, data = load_model()
    except Exception as exc:
        report = {"load_success": False, "scene": str(SCENE_XML), "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    joints = joint_map(model, mujoco)
    baseline_pose = {name: 0.0 for name in THUMB_JOINTS}
    baseline = measure(model, data, mujoco, joints, baseline_pose, ball_position)

    single_axis = {}
    for joint_name, values in {
        "thumb_cmc_joint": CMC_VALUES,
        "thumb_mcp_joint": MCP_VALUES,
        "thumb_ip_joint": IP_VALUES,
    }.items():
        rows = []
        for value in values:
            pose = dict(baseline_pose)
            pose[joint_name] = value
            item = measure(model, data, mujoco, joints, pose, ball_position)
            rows.append(item)
        single_axis[joint_name] = rows

    combinations = []
    for cmc in CMC_VALUES:
        for mcp in MCP_VALUES:
            for ip in IP_VALUES:
                pose = {"thumb_cmc_joint": cmc, "thumb_mcp_joint": mcp, "thumb_ip_joint": ip}
                item = measure(model, data, mujoco, joints, pose, ball_position)
                item["score"] = item["thumb_to_ball"] + 0.25 * item["thumb_to_index"]
                combinations.append(item)
    best_by_ball = sorted(combinations, key=lambda item: item["thumb_to_ball"])
    best_by_index = sorted(combinations, key=lambda item: item["thumb_to_index"])
    best_by_score = sorted(combinations, key=lambda item: item["score"])

    renders = []
    render_items = [baseline] + best_by_score[: max(args.render_count, 1)]
    seen = set()
    for idx, item in enumerate(render_items):
        label = "baseline" if idx == 0 else f"candidate_{idx:02d}_{pose_label(item['pose'])}"
        key = tuple(item["pose"].items())
        if key in seen:
            continue
        seen.add(key)
        measure(model, data, mujoco, joints, item["pose"], ball_position)
        renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / f"{label}_full.png", width=1200, height=850))
        renders.append(render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / f"{label}_thumb.png", width=1200, height=850))

    report = {
        "load_success": True,
        "scene": str(SCENE_XML),
        "ball_position": ball_position,
        "baseline": baseline,
        "single_axis": single_axis,
        "best_by_ball": best_by_ball[:12],
        "best_by_index": best_by_index[:12],
        "best_by_score": best_by_score[:12],
        "renders": renders,
        "interpretation": interpret(baseline, single_axis, best_by_score[0]),
        "notes": [
            "This is a static kinematic audit using direct qpos only for measurement; it does not edit joint axes or names.",
            "Four long fingers are held open to isolate thumb CMC/MCP/IP motion.",
            "A small thumb-to-ball improvement without crossing the palm is not sufficient evidence to change axes automatically.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def interpret(baseline: dict, single_axis: dict, best: dict) -> list[str]:
    lines = []
    base_ball = baseline["thumb_to_ball"]
    best_ball = best["thumb_to_ball"]
    if best_ball < base_ball:
        lines.append(f"Best scanned thumb pose reduces thumb-to-ball distance from {base_ball:.4f} m to {best_ball:.4f} m.")
    else:
        lines.append(f"No scanned thumb pose improves thumb-to-ball distance below the baseline {base_ball:.4f} m.")

    for joint_name, rows in single_axis.items():
        best_row = min(rows, key=lambda item: item["thumb_to_ball"])
        worst_row = max(rows, key=lambda item: item["thumb_to_ball"])
        lines.append(
            f"{joint_name}: best single-axis value {best_row['pose'][joint_name]:.3f} gives thumb-to-ball {best_row['thumb_to_ball']:.4f} m; "
            f"worst value {worst_row['pose'][joint_name]:.3f} gives {worst_row['thumb_to_ball']:.4f} m."
        )

    if best_ball > 0.12:
        lines.append("Even the best scanned pose leaves the thumb tip far from the ball; thumb opposition is not solved in the current joint frame/axis setup.")
        lines.append("Recommendation: manually inspect thumb_cmc_axis, thumb_mcp_axis, and thumb_ip_axis in SolidWorks/URDF before changing MJCF axes.")
    else:
        lines.append("A candidate pose reaches a plausible opposition distance; verify visually before changing any defaults.")
    return lines


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Thumb Opposition Audit",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position', BALL_POSITION)}`",
            "",
            "## Baseline",
            "",
        ]
    )
    baseline = report.get("baseline", {})
    if baseline:
        lines.append(f"- Pose: `{baseline['pose']}`")
        lines.append(f"- Thumb to ball: {baseline['thumb_to_ball']:.6f} m")
        lines.append(f"- Thumb to index: {baseline['thumb_to_index']:.6f} m")
    lines.extend(["", "## Single Axis Sweep", ""])
    for joint_name, rows in report.get("single_axis", {}).items():
        lines.append(f"### {joint_name}")
        lines.append("")
        lines.append("| Value | Thumb to ball (m) | Thumb to index (m) |")
        lines.append("|---:|---:|---:|")
        for row in rows:
            lines.append(f"| {row['pose'][joint_name]:.3f} | {row['thumb_to_ball']:.6f} | {row['thumb_to_index']:.6f} |")
        lines.append("")
    lines.extend(["## Best Combined Candidates", "", "| Rank | CMC | MCP | IP | Thumb-ball (m) | Thumb-index (m) | Score |", "|---:|---:|---:|---:|---:|---:|---:|"])
    for idx, row in enumerate(report.get("best_by_score", [])[:12], 1):
        pose = row["pose"]
        lines.append(
            f"| {idx} | {pose['thumb_cmc_joint']:.3f} | {pose['thumb_mcp_joint']:.3f} | {pose['thumb_ip_joint']:.3f} | "
            f"{row['thumb_to_ball']:.6f} | {row['thumb_to_index']:.6f} | {row['score']:.6f} |"
        )
    lines.extend(["", "## Rendered Candidate Views", ""])
    for item in report.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in report.get("interpretation", []))
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
