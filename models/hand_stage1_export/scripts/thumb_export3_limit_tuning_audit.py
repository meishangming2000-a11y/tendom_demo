from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from clean_mesh_common import render_png, set_ball_position, write_json
from export3_common import (
    BALL_POSITION,
    DOCS_DIR,
    FOUR_FINGER_CLOSE_TARGETS,
    METADATA_DIR,
    THUMB_JOINTS,
    ball_contact_summary,
    joint_map,
    load_model,
    set_joint_qpos,
)


SCENE_XML = Path(__file__).resolve().parents[1] / "mjcf" / "scene_ball_export3_thumb_limit_tuned.xml"
REPORT_MD = DOCS_DIR / "export3_thumb_limit_tuning_audit.md"
REPORT_JSON = METADATA_DIR / "export3_thumb_limit_tuning_candidates.json"
OUT_DIR = DOCS_DIR / "visual_checks_export3_thumb_limit_tuning"

ABD_VALUES = [-1.2, -0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2]
CMC_FLEX_VALUES = [-1.2, -0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2]
MCP_VALUES = [-0.2, 0.0, 0.4, 0.8, 1.2, 1.4]
IP_VALUES = [-0.2, 0.0, 0.4, 0.8, 1.2]
OLD_EXPORT3_THUMB_BALL = 0.0858


def site_pos(model, data, mujoco, name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if sid < 0:
        raise RuntimeError(f"Missing site {name}")
    return np.array(data.site_xpos[sid], dtype=float)


def body_pos(model, data, mujoco, name: str) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid < 0:
        raise RuntimeError(f"Missing body {name}")
    return np.array(data.xpos[bid], dtype=float)


def pose_label(pose: dict[str, float]) -> str:
    return (
        f"abd_{pose['thumb_cmc_abd_joint']:+.2f}_cmcflex_{pose['thumb_cmc_flex_joint']:+.2f}_"
        f"mcp_{pose['thumb_mcp_joint']:+.2f}_ip_{pose['thumb_ip_joint']:+.2f}"
    ).replace("+", "p").replace("-", "m").replace(".", "d")


def unreasonable_penalty(metrics: dict) -> float:
    penalty = 0.0
    if not metrics["looks_finite"]:
        penalty += 10.0
    # Very large thumb-palm distance is a useful proxy for over-rotation or flip in this stage-1 skeleton.
    if metrics["thumb_to_palm"] > 0.22:
        penalty += (metrics["thumb_to_palm"] - 0.22) * 5.0
    # Avoid selecting a pose that only wins by driving thumb tip far past the index/middle pinch region.
    if metrics["thumb_to_index"] < 0.015 or metrics["thumb_to_middle"] < 0.015:
        penalty += 0.05
    return penalty


def score_candidate(metrics: dict) -> float:
    penetration = metrics["contact"]["max_penetration"]
    penetration_penalty = max(0.0, penetration - 0.012) * 20.0
    return (
        metrics["thumb_to_ball"]
        + 0.5 * metrics["thumb_to_index"]
        + 0.25 * metrics["thumb_to_middle"]
        + penetration_penalty
        + metrics["pose_unreasonable_penalty"]
    )


def reset_pose(model, data, mujoco, ball_position: list[float]) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)


def measure(model, data, mujoco, joints: dict[str, int], requested_thumb_pose: dict[str, float], ball_position: list[float]) -> dict:
    reset_pose(model, data, mujoco, ball_position)
    full_pose = dict(FOUR_FINGER_CLOSE_TARGETS)
    full_pose.update(requested_thumb_pose)
    applied = set_joint_qpos(model, data, joints, full_pose)
    mujoco.mj_forward(model, data)

    ball = body_pos(model, data, mujoco, "ball")
    palm = body_pos(model, data, mujoco, "palm_link")
    thumb = site_pos(model, data, mujoco, "thumb_tip_site")
    index = site_pos(model, data, mujoco, "index_tip_site")
    middle = site_pos(model, data, mujoco, "middle_tip_site")
    contact = ball_contact_summary(model, data, mujoco)
    row = {
        "requested_pose": {name: float(requested_thumb_pose.get(name, 0.0)) for name in THUMB_JOINTS},
        "applied_pose": {name: float(applied.get(name, 0.0)) for name in THUMB_JOINTS},
        "context_four_finger_targets": dict(FOUR_FINGER_CLOSE_TARGETS),
        "ball_center": ball.tolist(),
        "thumb_tip": thumb.tolist(),
        "index_tip": index.tolist(),
        "middle_tip": middle.tolist(),
        "palm_pos": palm.tolist(),
        "thumb_to_ball": float(np.linalg.norm(thumb - ball)),
        "thumb_to_index": float(np.linalg.norm(thumb - index)),
        "thumb_to_middle": float(np.linalg.norm(thumb - middle)),
        "thumb_to_palm": float(np.linalg.norm(thumb - palm)),
        "contact": contact,
        "looks_finite": bool(np.isfinite(thumb).all() and np.linalg.norm(thumb - palm) < 0.5),
    }
    row["pose_unreasonable_penalty"] = unreasonable_penalty(row)
    row["score"] = score_candidate(row)
    row["thumb_ball_improvement_vs_old_export3"] = OLD_EXPORT3_THUMB_BALL - row["thumb_to_ball"]
    row["enters_0p06m_thumb_ball"] = bool(row["thumb_to_ball"] < 0.06)
    return row


def single_axis_scan(model, data, mujoco, joints: dict[str, int], ball_position: list[float]) -> dict[str, list[dict]]:
    values = {
        "thumb_cmc_abd_joint": ABD_VALUES,
        "thumb_cmc_flex_joint": CMC_FLEX_VALUES,
        "thumb_mcp_joint": MCP_VALUES,
        "thumb_ip_joint": IP_VALUES,
    }
    rows = {}
    for joint, candidates in values.items():
        joint_rows = []
        for value in candidates:
            pose = {name: 0.0 for name in THUMB_JOINTS}
            pose[joint] = value
            joint_rows.append(measure(model, data, mujoco, joints, pose, ball_position))
        rows[joint] = joint_rows
    return rows


def render_candidates(model, data, mujoco, joints: dict[str, int], ball_position: list[float], rows: list[dict], render_count: int) -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    renders = []
    baseline = {name: 0.0 for name in THUMB_JOINTS}
    measure(model, data, mujoco, joints, baseline, ball_position)
    renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / "baseline_full.png", width=1200, height=850))
    renders.append(render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / "baseline_thumb.png", width=1200, height=850))
    renders.append(render_png(model, data, mujoco, "palm", OUT_DIR / "baseline_palm.png", width=1200, height=850))
    for index, row in enumerate(rows[:render_count], start=1):
        pose = row["applied_pose"]
        label = f"candidate_{index:02d}_{pose_label(pose)}"
        measure(model, data, mujoco, joints, pose, ball_position)
        renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / f"{label}_full.png", width=1200, height=850))
        renders.append(render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / f"{label}_thumb.png", width=1200, height=850))
        renders.append(render_png(model, data, mujoco, "palm", OUT_DIR / f"{label}_palm.png", width=1200, height=850))
    return renders


def write_report(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Export3 Thumb Limit Tuning Audit",
        "",
        "Status: experimental thumb-limit grid search. No CAD/STL/tree/name changes.",
        "",
        f"- Scene: `{report['scene']}`",
        f"- Ball position: `{report['ball_position']}`",
        f"- Candidate count: {report['candidate_count']}",
        f"- Old export3 best thumb-ball reference: `{OLD_EXPORT3_THUMB_BALL:.4f} m`",
        f"- Context: four long fingers held at scripted close pose while scanning thumb pose.",
        "",
        "## Best By Score",
        "",
        "| Rank | Abd | CMC flex | MCP | IP | Score | Thumb-ball | Thumb-index | Thumb-middle | Contacts | Penetration | Penalty |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, item in enumerate(report["best_by_score"][:20], start=1):
        pose = item["applied_pose"]
        lines.append(
            f"| {idx} | {pose['thumb_cmc_abd_joint']:.3f} | {pose['thumb_cmc_flex_joint']:.3f} | "
            f"{pose['thumb_mcp_joint']:.3f} | {pose['thumb_ip_joint']:.3f} | {item['score']:.6f} | "
            f"{item['thumb_to_ball']:.6f} | {item['thumb_to_index']:.6f} | {item['thumb_to_middle']:.6f} | "
            f"{item['contact']['ball_contact_count']} | {item['contact']['max_penetration']:.6f} | {item['pose_unreasonable_penalty']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Best By Thumb-Ball Distance",
            "",
            "| Rank | Abd | CMC flex | MCP | IP | Thumb-ball | Thumb-index | Thumb-middle | Score | Contacts | Penetration |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for idx, item in enumerate(report["best_by_thumb_ball"][:20], start=1):
        pose = item["applied_pose"]
        lines.append(
            f"| {idx} | {pose['thumb_cmc_abd_joint']:.3f} | {pose['thumb_cmc_flex_joint']:.3f} | "
            f"{pose['thumb_mcp_joint']:.3f} | {pose['thumb_ip_joint']:.3f} | {item['thumb_to_ball']:.6f} | "
            f"{item['thumb_to_index']:.6f} | {item['thumb_to_middle']:.6f} | {item['score']:.6f} | "
            f"{item['contact']['ball_contact_count']} | {item['contact']['max_penetration']:.6f} |"
        )
    lines.extend(["", "## Single Axis Trend", ""])
    for joint, rows in report["single_axis"].items():
        best = min(rows, key=lambda item: item["thumb_to_ball"])
        worst = max(rows, key=lambda item: item["thumb_to_ball"])
        lines.append(
            f"- `{joint}` best {best['applied_pose'][joint]:.3f}: thumb-ball {best['thumb_to_ball']:.6f} m; "
            f"worst {worst['applied_pose'][joint]:.3f}: {worst['thumb_to_ball']:.6f} m."
        )
    lines.extend(["", "## Renders", ""])
    for item in report["renders"]:
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in report["interpretation"])
    lines.extend(["", "## Visual Judgment", ""])
    lines.extend(f"- {line}" for line in report["visual_judgment"])
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def interpret(best_score: dict, best_ball: dict) -> list[str]:
    lines = []
    lines.append(
        f"Best score pose thumb-ball is {best_score['thumb_to_ball']:.4f} m and thumb-index is {best_score['thumb_to_index']:.4f} m."
    )
    lines.append(
        f"Best pure thumb-ball pose reaches {best_ball['thumb_to_ball']:.4f} m, compared with old export3 reference {OLD_EXPORT3_THUMB_BALL:.4f} m."
    )
    if best_ball["thumb_to_ball"] < 0.06:
        lines.append("The expanded limits found poses inside the 0.06 m thumb-ball target.")
    else:
        lines.append("The expanded limits did not reach the 0.06 m thumb-ball target.")
    if best_ball["thumb_to_ball"] < OLD_EXPORT3_THUMB_BALL - 0.015:
        lines.append("Thumb-ball distance improves materially against the old export3 best.")
    elif best_ball["thumb_to_ball"] < OLD_EXPORT3_THUMB_BALL:
        lines.append("Thumb-ball distance improves slightly against the old export3 best.")
    else:
        lines.append("Thumb-ball distance does not improve against the old export3 best.")
    if best_score["contact"]["max_penetration"] > 0.02:
        lines.append("Best score pose has high penetration, so do not treat it as physically validated.")
    lines.append("This is scripted pose search only; no learning or model-structure change was used.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Grid-search thumb limits for export3 tuned MJCF.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--render-count", type=int, default=10)
    args = parser.parse_args()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]

    mujoco, model, data = load_model(SCENE_XML)
    model.opt.gravity[:] = 0.0
    joints = joint_map(model, mujoco)
    single_axis = single_axis_scan(model, data, mujoco, joints, ball_position)
    candidates = []
    for abd in ABD_VALUES:
        for cmc_flex in CMC_FLEX_VALUES:
            for mcp in MCP_VALUES:
                for ip in IP_VALUES:
                    pose = {
                        "thumb_cmc_abd_joint": abd,
                        "thumb_cmc_flex_joint": cmc_flex,
                        "thumb_mcp_joint": mcp,
                        "thumb_ip_joint": ip,
                    }
                    candidates.append(measure(model, data, mujoco, joints, pose, ball_position))
    candidates_by_score = sorted(candidates, key=lambda item: (item["score"], item["contact"]["max_penetration"]))
    candidates_by_thumb_ball = sorted(candidates, key=lambda item: (item["thumb_to_ball"], item["score"]))
    renders = render_candidates(model, data, mujoco, joints, ball_position, candidates_by_score, args.render_count)
    report = {
        "load_success": True,
        "scene": str(SCENE_XML),
        "ball_position": ball_position,
        "candidate_count": len(candidates),
        "old_export3_thumb_ball_reference": OLD_EXPORT3_THUMB_BALL,
        "grid": {
            "thumb_cmc_abd_joint": ABD_VALUES,
            "thumb_cmc_flex_joint": CMC_FLEX_VALUES,
            "thumb_mcp_joint": MCP_VALUES,
            "thumb_ip_joint": IP_VALUES,
        },
        "single_axis": single_axis,
        "best_by_score": candidates_by_score[:40],
        "best_by_thumb_ball": candidates_by_thumb_ball[:40],
        "renders": renders,
        "interpretation": interpret(candidates_by_score[0], candidates_by_thumb_ball[0]),
        "visual_judgment": [
            "Pending manual/visual inspection of rendered candidates.",
            "Use the saved full, palm, and thumb closeup views to reject poses that only win numerically.",
        ],
    }
    write_report(report)
    print(json.dumps({"report": str(REPORT_MD), "metadata": str(REPORT_JSON), "best": candidates_by_score[0]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
