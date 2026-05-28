from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np

from clean_mesh_common import apply_targets, load_model, render_png, set_ball_position, write_json
from demo_grasp_ball_primitive import STAGE_ORDER, STAGE_TARGETS


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
ARCHIVE_DIR = ROOT / "archive"
SOURCE_SCENE = MJCF_DIR / "scene_ball_clean_mesh_export2_draft.xml"
RETRY_SCENE = MJCF_DIR / "scene_ball_clean_mesh_export2_retry.xml"
VISUAL_ROOT = DOCS_DIR / "visual_checks_export2_retry"
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


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = ARCHIVE_DIR / f"export2_ballpos_retry_pre_{stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target_dir / path.name)


def fmt_vec(values: list[float]) -> str:
    return " ".join(f"{value:.6g}" for value in values)


def write_retry_scene(ball_position: list[float]) -> None:
    if not SOURCE_SCENE.exists():
        raise FileNotFoundError(SOURCE_SCENE)
    backup(RETRY_SCENE)
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", "hand_stage1_ball_scene_clean_mesh_export2_retry")
    ball_body = root.find(".//body[@name='ball']")
    if ball_body is None:
        raise RuntimeError("ball body not found in source scene")
    ball_body.set("pos", fmt_vec(ball_position))
    tree.write(RETRY_SCENE, encoding="utf-8", xml_declaration=True)


def contact_summary(model, data, mujoco, ball_position: list[float]) -> dict:
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)

    ball_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    ball_center = np.array(data.xpos[ball_body], dtype=float) if ball_body >= 0 else np.array(ball_position, dtype=float)

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

    distances = {}
    for site_name in TIP_SITES:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        if sid < 0:
            distances[site_name] = None
            continue
        distances[site_name] = float(np.linalg.norm(np.array(data.site_xpos[sid], dtype=float) - ball_center))

    four = [distances[name] for name in TIP_SITES[:4] if distances[name] is not None]
    all_tips = [value for value in distances.values() if value is not None]
    min_contact_dist = min((item["dist"] for item in contacts), default=0.0)
    return {
        "ball_contacts": contacts,
        "ball_ncon": len(contacts),
        "ball_min_contact_dist": float(min_contact_dist),
        "ball_penetration_depth": float(max(0.0, -min_contact_dist)),
        "tip_distances": distances,
        "mean_four_tip_dist": float(np.mean(four)) if four else None,
        "mean_all_tip_dist": float(np.mean(all_tips)) if all_tips else None,
    }


def run_stage(model, data, mujoco, stage_name: str, ball_position: list[float]) -> dict:
    applied = apply_targets(model, data, mujoco, STAGE_TARGETS[stage_name])
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    summary = contact_summary(model, data, mujoco, ball_position)
    summary["targets"] = dict(STAGE_TARGETS[stage_name])
    summary["applied"] = applied
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Retry export2 clean-mesh ball placement and render staged grasp frames.")
    parser.add_argument("--ball-x", type=float, default=0.0)
    parser.add_argument("--ball-y", type=float, default=-0.1)
    parser.add_argument("--ball-z", type=float, default=0.195)
    parser.add_argument("--tag", default="ballpos_retry")
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--height", type=int, default=850)
    args = parser.parse_args()

    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    write_retry_scene(ball_position)

    mujoco, model, data = load_model(RETRY_SCENE)
    out_dir = VISUAL_ROOT / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)

    stage_reports = {}
    renders = []
    for stage in STAGE_ORDER:
        stage_reports[stage] = run_stage(model, data, mujoco, stage, ball_position)
        renders.append(
            render_png(
                model,
                data,
                mujoco,
                "full_hand_with_ball",
                out_dir / STAGE_TO_FILE.get(stage, f"{stage}.png"),
                width=args.width,
                height=args.height,
            )
        )

    for camera in ["front", "side", "top", "palm", "thumb_root_closeup", "index_finger_closeup"]:
        renders.append(
            render_png(
                model,
                data,
                mujoco,
                camera,
                out_dir / f"hold_{camera}.png",
                width=args.width,
                height=args.height,
            )
        )

    report = {
        "scene": str(RETRY_SCENE),
        "source_scene": str(SOURCE_SCENE),
        "ball_position": ball_position,
        "stage_order": STAGE_ORDER,
        "stage_reports": stage_reports,
        "renders": renders,
        "notes": [
            "This retry keeps the export2 joint tree, joint names, and mesh mappings unchanged.",
            "The all-flexion-axis flip test was not reused because it increased fingertip-to-ball distance.",
            "Clean STL mesh geoms remain visual-only; ball contacts are against primitive collision geoms.",
            "The scripted demo directly sets qpos and ball qpos, so it is a visual/contact smoke test rather than a force-controlled grasp.",
        ],
    }

    json_path = METADATA_DIR / f"export2_ballpos_retry_{args.tag}.json"
    md_path = DOCS_DIR / f"export2_ballpos_retry_{args.tag}_report.md"
    backup(json_path)
    backup(md_path)
    write_json(json_path, report)
    write_markdown(md_path, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Export2 Ball Position Retry Report",
        "",
        f"- Scene: `{report['scene']}`",
        f"- Source scene: `{report['source_scene']}`",
        f"- Ball position: `{report['ball_position']}`",
        "- Axis handling: kept original export2 axes; rejected all-axis flip because fingertip distance became worse.",
        "- Collision note: clean STL geoms are visual-only; contacts below are from primitive collision geoms.",
        "",
        "## Stage Contact And Distance Summary",
        "",
        "| Stage | Ball contacts | Max penetration (m) | Mean 4-tip distance (m) | Thumb distance (m) |",
        "|---|---:|---:|---:|---:|",
    ]
    for stage in STAGE_ORDER:
        item = report["stage_reports"][stage]
        thumb = item["tip_distances"].get("thumb_tip_site")
        lines.append(
            f"| {stage} | {item['ball_ncon']} | {item['ball_penetration_depth']:.6f} | "
            f"{item['mean_four_tip_dist']:.6f} | {thumb:.6f} |"
        )

    lines.extend(["", "## Renders", ""])
    for item in report["renders"]:
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Initial open-hand contact should be zero or near zero; otherwise the ball is starting inside the hand/collision shell.",
            "- Hold-stage penetration is expected to be approximate because the script teleports qpos targets and does not run a contact-aware controller.",
            "- TODO: tune thumb opposition after joint-axis semantics are confirmed.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
