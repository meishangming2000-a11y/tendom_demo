from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from clean_mesh_common import set_ball_position, write_json  # noqa: E402
from demo_grasp_ball_position_control import (  # noqa: E402
    CONTROLLED_JOINTS,
    SCENE_XML,
    actuator_map,
    ball_contact_summary,
    blend,
    fingertip_distances,
    full_stage_targets,
    joint_map,
    set_ctrl,
)


DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
REPORT_MD = DOCS_DIR / "four_finger_grasp_sweep_report.md"
REPORT_JSON = METADATA_DIR / "four_finger_grasp_sweep.json"
BALL_X_VALUES = [-0.02, 0.0, 0.02]
BALL_Y_VALUES = [-0.08, -0.10, -0.12]
BALL_Z_VALUES = [0.18, 0.195, 0.21]
THUMB_JOINTS = ["thumb_cmc_joint", "thumb_mcp_joint", "thumb_ip_joint"]


def four_finger_targets(stage: str) -> dict[str, float]:
    targets = full_stage_targets(stage)
    for joint in THUMB_JOINTS:
        targets[joint] = 0.0
    return targets


def model_load():
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def reset_hand_and_ball(mujoco, model, data, ball_position: list[float], act_map: dict[str, int]) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    set_ctrl(model, data, four_finger_targets("open_hand"), act_map)
    mujoco.mj_forward(model, data)


def advance_stage(
    mujoco,
    model,
    data,
    act_map: dict[str, int],
    start_targets: dict[str, float],
    end_targets: dict[str, float],
    ball_position: list[float],
    steps: int,
) -> dict[str, float]:
    applied = {}
    for step in range(max(steps, 1)):
        fraction = (step + 1) / max(steps, 1)
        command = blend(start_targets, end_targets, fraction)
        applied = set_ctrl(model, data, command, act_map)
        set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_step(model, data)
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    return applied


def evaluate_pose(mujoco, model, data) -> dict:
    summary = {}
    summary.update(ball_contact_summary(model, data, mujoco))
    summary.update(fingertip_distances(model, data, mujoco))
    four_distances = [
        summary["distances"][name]
        for name in ("index_tip_site", "middle_tip_site", "ring_tip_site", "little_tip_site")
        if summary["distances"].get(name) is not None
    ]
    summary["min_four_tip_distance"] = float(np.min(four_distances)) if four_distances else None
    summary["max_four_tip_distance"] = float(np.max(four_distances)) if four_distances else None
    return summary


def classify(open_summary: dict, hold_summary: dict) -> str:
    open_contacts = int(open_summary.get("ball_contact_count", 0))
    hold_contacts = int(hold_summary.get("ball_contact_count", 0))
    penetration = float(hold_summary.get("max_penetration", 0.0))
    mean_four = hold_summary.get("mean_four_tip_distance")
    if open_contacts == 0 and hold_contacts >= 1 and mean_four is not None and mean_four <= 0.05 and penetration <= 0.012:
        return "PASS"
    if open_contacts == 0 and mean_four is not None and mean_four <= 0.065 and penetration <= 0.018:
        return "PARTIAL"
    return "FAIL"


def score_result(result: dict) -> float:
    hold = result["hold"]
    mean_four = hold.get("mean_four_tip_distance")
    if mean_four is None:
        mean_four = 1.0
    contact_bonus = min(int(hold.get("ball_contact_count", 0)), 4) * 0.005
    penetration_penalty = float(hold.get("max_penetration", 0.0)) * 2.0
    open_penalty = int(result["open"].get("ball_contact_count", 0)) * 0.05
    return float(mean_four - contact_bonus + penetration_penalty + open_penalty)


def run_sweep(steps: int) -> dict:
    mujoco, model, data = model_load()
    model.opt.gravity[:] = 0.0
    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    missing = sorted(set(CONTROLLED_JOINTS) - set(act_map))
    open_targets = four_finger_targets("open_hand")
    preshape_targets = four_finger_targets("approach_pre_shape")
    close_targets = four_finger_targets("close_four_fingers")
    hold_targets = dict(close_targets)
    results = []

    for x in BALL_X_VALUES:
        for y in BALL_Y_VALUES:
            for z in BALL_Z_VALUES:
                ball_position = [x, y, z]
                reset_hand_and_ball(mujoco, model, data, ball_position, act_map)
                open_summary = evaluate_pose(mujoco, model, data)
                advance_stage(mujoco, model, data, act_map, open_targets, preshape_targets, ball_position, steps)
                advance_stage(mujoco, model, data, act_map, preshape_targets, close_targets, ball_position, steps)
                applied = advance_stage(mujoco, model, data, act_map, close_targets, hold_targets, ball_position, steps)
                hold_summary = evaluate_pose(mujoco, model, data)
                result = {
                    "ball_position": ball_position,
                    "open": open_summary,
                    "hold": hold_summary,
                    "target_angles": hold_targets,
                    "ctrl_applied": applied,
                    "classification": classify(open_summary, hold_summary),
                }
                result["score"] = score_result(result)
                results.append(result)

    results.sort(key=lambda item: item["score"])
    return {
        "scene": str(SCENE_XML),
        "load_success": True,
        "body_count": int(model.nbody),
        "joint_count": int(model.njnt),
        "actuator_count": int(model.nu),
        "geom_count": int(model.ngeom),
        "site_count": int(model.nsite),
        "missing_actuators": missing,
        "sweep_grid": {"x": BALL_X_VALUES, "y": BALL_Y_VALUES, "z": BALL_Z_VALUES},
        "thumb_policy": "thumb kept open at 0 rad for all thumb joints",
        "gravity_enabled": False,
        "ball_pinned": True,
        "steps_per_stage": steps,
        "results": results,
        "best_result": results[0] if results else None,
        "counts": {
            "PASS": sum(1 for item in results if item["classification"] == "PASS"),
            "PARTIAL": sum(1 for item in results if item["classification"] == "PARTIAL"),
            "FAIL": sum(1 for item in results if item["classification"] == "FAIL"),
        },
        "notes": [
            "This sweep only tests four long fingers through position actuators.",
            "Thumb joints are held open at zero to isolate four-finger behavior.",
            "The ball is pinned and gravity is disabled, so this is a smoke test, not a stable free-object grasp.",
            "Collision uses simplified proxy geoms; clean STL remains visual-only.",
        ],
    }


def write_report(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Four Finger Grasp Ball Sweep Report",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
        f"- Bodies / joints / actuators / geoms / sites: {report.get('body_count')} / {report.get('joint_count')} / {report.get('actuator_count')} / {report.get('geom_count')} / {report.get('site_count')}",
        f"- Sweep grid: x={report.get('sweep_grid', {}).get('x')}, y={report.get('sweep_grid', {}).get('y')}, z={report.get('sweep_grid', {}).get('z')}",
        f"- Thumb policy: {report.get('thumb_policy')}",
        f"- Gravity enabled: {report.get('gravity_enabled')}",
        f"- Ball pinned: {report.get('ball_pinned')}",
        f"- Steps per stage: {report.get('steps_per_stage')}",
        f"- Missing actuators: {', '.join(report.get('missing_actuators', [])) if report.get('missing_actuators') else 'None'}",
        "",
        "## Summary Counts",
        "",
    ]
    for key in ("PASS", "PARTIAL", "FAIL"):
        lines.append(f"- {key}: {report.get('counts', {}).get(key, 0)}")

    best = report.get("best_result")
    if best:
        hold = best["hold"]
        lines.extend(
            [
                "",
                "## Best Position",
                "",
                f"- Ball position: `{best['ball_position']}`",
                f"- Classification: {best['classification']}",
                f"- Hold contacts: {hold.get('ball_contact_count')}",
                f"- Hold max penetration: {hold.get('max_penetration', 0.0):.6f} m",
                f"- Hold mean four-tip distance: {hold.get('mean_four_tip_distance', 0.0):.6f} m",
                f"- Hold distances: `{json.dumps(hold.get('distances', {}), ensure_ascii=False)}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Sweep Table",
            "",
            "| Ball position | Class | Open contacts | Hold contacts | Hold max penetration (m) | Mean 4-tip distance (m) | Index | Middle | Ring | Little |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report.get("results", []):
        hold = item["hold"]
        d = hold.get("distances", {})
        lines.append(
            f"| {item['ball_position']} | {item['classification']} | "
            f"{item['open'].get('ball_contact_count', 0)} | {hold.get('ball_contact_count', 0)} | "
            f"{hold.get('max_penetration', 0.0):.6f} | {hold.get('mean_four_tip_distance', 0.0):.6f} | "
            f"{d.get('index_tip_site', 0.0):.6f} | {d.get('middle_tip_site', 0.0):.6f} | "
            f"{d.get('ring_tip_site', 0.0):.6f} | {d.get('little_tip_site', 0.0):.6f} |"
        )

    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep four-finger position-control ball grasp smoke test.")
    parser.add_argument("--steps", type=int, default=220, help="Position-control steps per stage for each ball pose.")
    args = parser.parse_args()
    try:
        report = run_sweep(max(20, args.steps))
    except Exception as exc:
        report = {
            "scene": str(SCENE_XML),
            "load_success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "notes": ["Sweep failed before completion; inspect the error and scene XML."],
        }
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
