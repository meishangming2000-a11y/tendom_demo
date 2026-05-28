from __future__ import annotations

import argparse
import json
from pathlib import Path

from demo_grasp_ball_primitive import (
    BALL_POSITION,
    BALL_RADIUS,
    SCENE_XML,
    STAGE_ORDER,
    STAGE_TARGETS,
    apply_targets,
    get_joint_map,
    set_ball_position,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
TIP_SITES = [
    "index_tip_site",
    "middle_tip_site",
    "ring_tip_site",
    "little_tip_site",
    "thumb_tip_site",
]


def distance(a, b) -> float:
    return float(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)) ** 0.5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze primitive fingertip-to-ball distances by scripted stage.")
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

    joint_map = get_joint_map(model, mujoco)
    site_ids = {name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name) for name in TIP_SITES}
    missing_sites = sorted(name for name, sid in site_ids.items() if sid < 0)
    ball_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")

    stages = []
    for stage_name in STAGE_ORDER:
        data.qpos[:] = 0
        set_ball_position(model, data, mujoco, ball_position)
        applied = apply_targets(model, data, joint_map, STAGE_TARGETS[stage_name])
        mujoco.mj_forward(model, data)
        ball_center = data.xpos[ball_body_id].tolist()
        distances = {}
        clearance_to_surface = {}
        for site_name, site_id in site_ids.items():
            if site_id < 0:
                continue
            value = distance(data.site_xpos[site_id], ball_center)
            distances[site_name] = value
            clearance_to_surface[site_name] = value - BALL_RADIUS
        stages.append(
            {
                "stage": stage_name,
                "applied_targets": applied,
                "ball_center": ball_center,
                "distances": distances,
                "clearance_to_ball_surface": clearance_to_surface,
                "min_distance": min(distances.values()) if distances else None,
            }
        )

    report = {
        "scene": str(SCENE_XML),
        "load_success": True,
        "ball_position": ball_position,
        "ball_radius": BALL_RADIUS,
        "tip_sites": TIP_SITES,
        "missing_sites": missing_sites,
        "stages": stages,
        "notes": [
            "Distances are computed on primitive fingertip sites, not CAD fingertip geometry.",
            "Negative clearance means the site is inside the ideal ball radius; this is allowed for this qpos-only scripted smoke test.",
            "TODO: use these numbers to tune ball position and scripted target signs after visual inspection.",
        ],
    }
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_report(report: dict) -> None:
    (METADATA_DIR / "fingertip_ball_distance.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Fingertip Ball Distance Report",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position', BALL_POSITION)}`",
            f"- Ball radius: {report.get('ball_radius', BALL_RADIUS)} m",
            f"- Missing sites: {', '.join(report.get('missing_sites', [])) if report.get('missing_sites') else 'None'}",
            "",
            "## Stage Distances",
            "",
        ]
    )
    for stage in report.get("stages", []):
        lines.append(f"### {stage['stage']}")
        lines.append("")
        lines.append(f"- Ball center: `{stage['ball_center']}`")
        lines.append(f"- Min fingertip distance: {stage['min_distance']:.5f} m")
        for site_name, value in sorted(stage["distances"].items()):
            clearance = stage["clearance_to_ball_surface"][site_name]
            lines.append(f"- `{site_name}`: distance={value:.5f} m, clearance={clearance:.5f} m")
        lines.append("")
    lines.extend(["## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    (DOCS_DIR / "fingertip_ball_distance_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
