from __future__ import annotations

import argparse
import json
from pathlib import Path

from demo_grasp_ball_primitive import BALL_POSITION, SCENE_XML, set_ball_position


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
TIP_SITE_BY_PREFIX = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}


def norm(values) -> float:
    return float(sum(float(value) ** 2 for value in values) ** 0.5)


def distance(a, b) -> float:
    return norm([float(x) - float(y) for x, y in zip(a, b)])


def site_for_joint(joint_name: str) -> str | None:
    for prefix, site_name in TIP_SITE_BY_PREFIX.items():
        if joint_name.startswith(prefix):
            return site_name
    return None


def classify(joint_name: str, distance_delta: float | None, displacement_norm: float) -> str:
    if displacement_norm < 1e-5:
        return "no_visible_tip_motion_or_fixed_effect"
    if "mcp_flex" in joint_name or "mcp_abd" in joint_name:
        return "moves_tip_needs_mcp_semantic_review"
    if joint_name.startswith("thumb_"):
        return "moves_thumb_tip_needs_opposition_review"
    if distance_delta is None:
        return "moves_body_no_single_fingertip_site"
    if distance_delta < -0.002:
        return "positive_angle_moves_tip_toward_ball"
    if distance_delta > 0.002:
        return "positive_angle_moves_tip_away_from_ball_possible_reverse_or_pose_dependent"
    return "small_distance_change_check_axis_in_viewer"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit primitive joint positive-direction effects.")
    parser.add_argument("--angle", type=float, default=0.2, help="Small positive angle to apply to each hinge joint.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    args = parser.parse_args()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import mujoco
    except Exception as exc:
        report = {"load_success": False, "error": f"mujoco import failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    try:
        model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        data = mujoco.MjData(model)
    except Exception as exc:
        report = {"load_success": False, "error": f"scene load failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    ball_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    ball_center = data.xpos[ball_body_id].copy()
    neutral_site_xpos = {
        site_name: data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)].copy()
        for site_name in TIP_SITE_BY_PREFIX.values()
    }
    neutral_distances = {name: distance(pos, ball_center) for name, pos in neutral_site_xpos.items()}

    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    neutral_qpos = data.qpos.copy()
    results = []
    for jid in range(model.njnt):
        if int(model.jnt_type[jid]) != hinge_type:
            continue
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or f"joint_{jid}"
        data.qpos[:] = neutral_qpos
        adr = int(model.jnt_qposadr[jid])
        lower, upper = [float(value) for value in model.jnt_range[jid]]
        target = min(max(args.angle, lower), upper)
        data.qpos[adr] = target
        set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_forward(model, data)

        site_name = site_for_joint(joint_name)
        if site_name is None:
            displacements = {}
            for name, neutral_pos in neutral_site_xpos.items():
                moved = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)]
                displacements[name] = [float(v) for v in (moved - neutral_pos)]
            selected_site = "all_tip_sites"
            selected_displacement = max((norm(value) for value in displacements.values()), default=0.0)
            distance_delta = None
            vector = None
        else:
            site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
            moved = data.site_xpos[site_id]
            vector_values = [float(v) for v in (moved - neutral_site_xpos[site_name])]
            selected_site = site_name
            vector = vector_values
            selected_displacement = norm(vector_values)
            moved_distance = distance(moved, ball_center)
            distance_delta = moved_distance - neutral_distances[site_name]

        results.append(
            {
                "joint": joint_name,
                "test_angle": target,
                "range": [lower, upper],
                "selected_site": selected_site,
                "site_displacement_vector": vector,
                "site_displacement_norm": selected_displacement,
                "distance_delta_to_ball": distance_delta,
                "classification": classify(joint_name, distance_delta, selected_displacement),
            }
        )

    report = {
        "scene": str(SCENE_XML),
        "load_success": True,
        "positive_angle": args.angle,
        "ball_position": ball_position,
        "results": results,
        "notes": [
            "This audit applies a positive qpos offset to one hinge joint at a time in the primitive model.",
            "Classifications are heuristics for inspection, not mechanical truth.",
            "mcp_flex/mcp_abd names are intentionally not changed; semantic review remains TODO.",
            "A positive angle moving a fingertip away from the ball may be correct if the ball pose or open pose is not aligned with that joint axis.",
        ],
    }
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_report(report: dict) -> None:
    (METADATA_DIR / "joint_direction_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Joint Direction Audit",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Positive test angle: {report.get('positive_angle', 'unknown')} rad",
            f"- Ball position: `{report.get('ball_position', BALL_POSITION)}`",
            "",
            "## Results",
            "",
            "| Joint | Site | Displacement norm | Ball distance delta | Classification |",
            "|---|---|---:|---:|---|",
        ]
    )
    for item in report.get("results", []):
        delta = item["distance_delta_to_ball"]
        delta_text = "N/A" if delta is None else f"{delta:.5f}"
        lines.append(
            f"| `{item['joint']}` | `{item['selected_site']}` | "
            f"{item['site_displacement_norm']:.5f} | {delta_text} | {item['classification']} |"
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    (DOCS_DIR / "joint_direction_audit.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
