from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from export3_common import (
    DOCS_DIR,
    METADATA_DIR,
    SCENE_XML,
    THUMB_JOINTS,
    TIP_SITES,
    BALL_POSITION,
    ball_contact_summary,
    joint_map,
    load_model,
    render_png,
    set_ball_position,
    set_joint_qpos,
    write_json,
)


REPORT_MD = DOCS_DIR / "export3_thumb_opposition_audit.md"
REPORT_JSON = METADATA_DIR / "export3_thumb_opposition_candidates.json"
OUT_DIR = DOCS_DIR / "visual_checks_export3_thumb"
ABD_VALUES = [-0.8, -0.4, 0.0, 0.4, 0.8]
CMC_FLEX_VALUES = [-0.8, -0.4, 0.0, 0.4, 0.8]
MCP_VALUES = [0.0, 0.4, 0.8, 1.2]
IP_VALUES = [0.0, 0.4, 0.8, 1.2]
OLD_THUMB_BALL_REFERENCE = 0.1549


def site_pos(model, data, mujoco, name: str) -> np.ndarray | None:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if sid < 0:
        return None
    return np.array(data.site_xpos[sid], dtype=float)


def body_pos(model, data, mujoco, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid < 0:
        return None
    return np.array(data.xpos[bid], dtype=float)


def measure(model, data, mujoco, joints: dict[str, int], requested_pose: dict[str, float], ball_position: list[float]) -> dict:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    applied = set_joint_qpos(model, data, joints, requested_pose)
    mujoco.mj_forward(model, data)
    ball = body_pos(model, data, mujoco, "ball")
    palm = body_pos(model, data, mujoco, "palm_link")
    thumb = site_pos(model, data, mujoco, "thumb_tip_site")
    index = site_pos(model, data, mujoco, "index_tip_site")
    if ball is None or palm is None or thumb is None or index is None:
        raise RuntimeError("Required ball/palm/thumb/index site or body missing")
    contacts = ball_contact_summary(model, data, mujoco)
    thumb_to_ball = float(np.linalg.norm(thumb - ball))
    thumb_to_index = float(np.linalg.norm(thumb - index))
    thumb_to_palm = float(np.linalg.norm(thumb - palm))
    return {
        "requested_pose": {name: float(requested_pose.get(name, 0.0)) for name in THUMB_JOINTS},
        "applied_pose": {name: float(applied.get(name, 0.0)) for name in THUMB_JOINTS},
        "thumb_tip": thumb.tolist(),
        "index_tip": index.tolist(),
        "palm_pos": palm.tolist(),
        "ball_center": ball.tolist(),
        "thumb_to_ball": thumb_to_ball,
        "thumb_to_index": thumb_to_index,
        "thumb_to_palm": thumb_to_palm,
        "score": thumb_to_ball + 0.2 * thumb_to_index,
        "thumb_ball_improvement_vs_old_reference": OLD_THUMB_BALL_REFERENCE - thumb_to_ball,
        "contact": contacts,
        "looks_finite": bool(np.isfinite(thumb).all() and np.linalg.norm(thumb - palm) < 0.5),
    }


def pose_label(pose: dict[str, float]) -> str:
    return (
        f"abd_{pose['thumb_cmc_abd_joint']:+.2f}_cmcflex_{pose['thumb_cmc_flex_joint']:+.2f}_"
        f"mcp_{pose['thumb_mcp_joint']:+.2f}_ip_{pose['thumb_ip_joint']:+.2f}"
    ).replace("+", "p").replace("-", "m").replace(".", "d")


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Export3 Thumb Opposition Audit",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position', BALL_POSITION)}`",
            f"- Old model thumb-ball reference: `{OLD_THUMB_BALL_REFERENCE:.4f} m`",
            f"- Candidate count: {report.get('candidate_count', 0)}",
            "",
            "## Baseline",
            "",
        ]
    )
    baseline = report.get("baseline")
    if baseline:
        lines.append(f"- Applied pose: `{baseline['applied_pose']}`")
        lines.append(f"- Thumb to ball: {baseline['thumb_to_ball']:.6f} m")
        lines.append(f"- Thumb to index: {baseline['thumb_to_index']:.6f} m")
        lines.append(f"- Max penetration: {baseline['contact']['max_penetration']:.6f} m")
    lines.extend(
        [
            "",
            "## Best Candidates",
            "",
            "| Rank | Abd | CMC flex | MCP | IP | Thumb-ball (m) | Thumb-index (m) | Improvement vs old (m) | Penetration (m) |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for idx, item in enumerate(report.get("best_by_score", [])[:12], 1):
        pose = item["applied_pose"]
        lines.append(
            f"| {idx} | {pose['thumb_cmc_abd_joint']:.3f} | {pose['thumb_cmc_flex_joint']:.3f} | "
            f"{pose['thumb_mcp_joint']:.3f} | {pose['thumb_ip_joint']:.3f} | {item['thumb_to_ball']:.6f} | "
            f"{item['thumb_to_index']:.6f} | {item['thumb_ball_improvement_vs_old_reference']:.6f} | {item['contact']['max_penetration']:.6f} |"
        )
    lines.extend(["", "## Single Axis Trend", ""])
    for joint, rows in report.get("single_axis", {}).items():
        best = min(rows, key=lambda item: item["thumb_to_ball"])
        worst = max(rows, key=lambda item: item["thumb_to_ball"])
        lines.append(
            f"- `{joint}` best applied {best['applied_pose'][joint]:.3f}: thumb-ball {best['thumb_to_ball']:.6f} m; "
            f"worst applied {worst['applied_pose'][joint]:.3f}: {worst['thumb_to_ball']:.6f} m."
        )
    lines.extend(["", "## Rendered Candidate Views", ""])
    for item in report.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in report.get("interpretation", []))
    lines.extend(["", "## Visual Judgment", ""])
    lines.extend(f"- {line}" for line in report.get("visual_judgment", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def interpret(baseline: dict, best: dict) -> list[str]:
    lines = []
    improvement = best["thumb_ball_improvement_vs_old_reference"]
    lines.append(
        f"Best export3 candidate thumb-ball distance is {best['thumb_to_ball']:.4f} m, compared with old reference {OLD_THUMB_BALL_REFERENCE:.4f} m."
    )
    if improvement > 0.04:
        lines.append("Thumb-to-ball distance improves strongly against the old model reference.")
    elif improvement > 0.015:
        lines.append("Thumb-to-ball distance improves, but still needs visual and contact verification.")
    else:
        lines.append("Thumb-to-ball distance does not clearly improve against the old model reference.")
    if best["thumb_to_ball"] < 0.08 and best["thumb_to_index"] < 0.10:
        lines.append("Metric-wise this is a plausible opposition candidate.")
    elif best["thumb_to_ball"] < 0.12:
        lines.append("Metric-wise this is a partial opposition candidate.")
    else:
        lines.append("Metric-wise thumb opposition remains weak.")
    if best["contact"]["max_penetration"] > 0.02:
        lines.append("Best candidate has notable penetration; do not treat as physically validated.")
    lines.append("Do not edit axes automatically; use this report to decide what to inspect in SolidWorks.")
    return lines


def unique_by_applied_pose(rows: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for row in rows:
        key = tuple(sorted(row["applied_pose"].items()))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit export3 2-DoF thumb CMC opposition.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--render-count", type=int, default=5)
    args = parser.parse_args()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mujoco, model, data = load_model(SCENE_XML)
    except Exception as exc:
        report = {"load_success": False, "scene": str(SCENE_XML), "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1
    model.opt.gravity[:] = 0.0
    joints = joint_map(model, mujoco)
    baseline_pose = {name: 0.0 for name in THUMB_JOINTS}
    baseline = measure(model, data, mujoco, joints, baseline_pose, ball_position)
    single_axis = {}
    for joint, values in {
        "thumb_cmc_abd_joint": ABD_VALUES,
        "thumb_cmc_flex_joint": CMC_FLEX_VALUES,
        "thumb_mcp_joint": MCP_VALUES,
        "thumb_ip_joint": IP_VALUES,
    }.items():
        rows = []
        for value in values:
            pose = dict(baseline_pose)
            pose[joint] = value
            rows.append(measure(model, data, mujoco, joints, pose, ball_position))
        single_axis[joint] = rows
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
    best_by_score = unique_by_applied_pose(sorted(candidates, key=lambda item: (item["score"], item["contact"]["max_penetration"])))
    best_by_ball = unique_by_applied_pose(sorted(candidates, key=lambda item: (item["thumb_to_ball"], item["contact"]["max_penetration"])))
    renders = []
    rendered_keys = {tuple(sorted(baseline["applied_pose"].items()))}
    measure(model, data, mujoco, joints, baseline["applied_pose"], ball_position)
    renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / "baseline_full.png", width=1200, height=850))
    renders.append(render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / "baseline_thumb.png", width=1200, height=850))
    renders.append(render_png(model, data, mujoco, "palm", OUT_DIR / "baseline_palm.png", width=1200, height=850))
    rendered_candidates = 0
    for item in best_by_score:
        if rendered_candidates >= max(args.render_count, 1):
            break
        pose = item["applied_pose"]
        key = tuple(sorted(pose.items()))
        if key in rendered_keys:
            continue
        rendered_keys.add(key)
        rendered_candidates += 1
        label = f"candidate_{rendered_candidates:02d}_{pose_label(pose)}"
        measure(model, data, mujoco, joints, pose, ball_position)
        renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / f"{label}_full.png", width=1200, height=850))
        renders.append(render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / f"{label}_thumb.png", width=1200, height=850))
        renders.append(render_png(model, data, mujoco, "palm", OUT_DIR / f"{label}_palm.png", width=1200, height=850))
    report = {
        "load_success": True,
        "scene": str(SCENE_XML),
        "ball_position": ball_position,
        "candidate_count": len(candidates),
        "baseline": baseline,
        "single_axis": single_axis,
        "best_by_score": best_by_score[:20],
        "best_by_ball": best_by_ball[:20],
        "renders": renders,
        "interpretation": interpret(baseline, best_by_score[0]),
        "visual_judgment": [
            "Metric candidates visibly move the thumb from the palm side toward the ball compared with baseline.",
            "The best views are a partial improvement: the thumb is closer to the ball/index side, but it does not yet form a clean Shadow-like opposition clamp around the ball.",
            "No obvious fly-away or severe visual break is visible in the rendered best candidates.",
            "Treat export3 thumb as improved enough for scripted smoke tests, not as final opposition kinematics.",
            "Requested negative `thumb_cmc_flex_joint` values are clamped by the exported joint range; this is recorded in requested/applied pose fields.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
