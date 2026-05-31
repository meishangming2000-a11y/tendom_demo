#!/usr/bin/env python3
"""Run a small target-neighborhood sweep for the v3 scripted pick-place smoke demo."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from arm_hand_stage1_v3_pick_place_task_api import (
    CURRENT_PICK_PLACE_SCENE,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_CENTER,
    DEFAULT_TARGET_RADIUS_M,
)
from demo_arm_hand_stage1_v3_pick_place_scripted import run_demo


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_target_sweep_report.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_target_sweep.json"


def parse_values(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def build_target_centers(args) -> list[dict[str, Any]]:
    base = np.asarray(args.target_center, dtype=np.float64)
    rows = []
    episode_id = 0
    for dx in parse_values(args.x_offsets):
        for dy in parse_values(args.y_offsets):
            offset = np.array([dx, dy, 0.0], dtype=np.float64)
            rows.append({"episode_id": episode_id, "target_offset": offset, "target_center": base + offset})
            episode_id += 1
    return rows


def demo_args(args, target_center: np.ndarray) -> SimpleNamespace:
    return SimpleNamespace(
        scene=args.scene,
        target_center=target_center,
        target_radius=args.target_radius,
        required_stable_steps=args.required_stable_steps,
        output=args.video_placeholder,
        report=args.report,
        metadata=args.metadata,
        render_video=False,
        render_snapshots=False,
        viewer=False,
        quiet=True,
        speed=2.0,
        fps=30,
        capture_every=999_999,
        width=320,
        height=240,
        default_hold_steps=args.default_hold_steps,
        move_steps=args.move_steps,
        approach_steps=args.approach_steps,
        hand_steps=args.hand_steps,
        lift_steps=args.lift_steps,
        hold_steps=args.hold_steps,
        transport_steps=args.transport_steps,
        descend_steps=args.descend_steps,
        pre_release_settle_steps=args.pre_release_settle_steps,
        release_steps=args.release_steps,
        retreat_steps=args.retreat_steps,
        settle_steps=args.settle_steps,
    )


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["status"] == "PASS")
    reasons = Counter(str(row["terminal_reason"]) for row in results)
    target_distances = [float(row["final_metrics"]["target_distance_xy"]) for row in results]
    stable_steps = [int(row["counters"]["stable_target_steps"]) for row in results]
    transport_floor = [int(row["counters"]["transport_floor_contacts"]) for row in results]
    final_xy = [np.asarray(row["final_metrics"]["ball_position"][:2], dtype=np.float64) for row in results]
    status = "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL")
    return {
        "status": status,
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": dict(reasons),
        "target_distance_xy_min": float(np.min(target_distances)) if target_distances else None,
        "target_distance_xy_max": float(np.max(target_distances)) if target_distances else None,
        "target_distance_xy_mean": float(np.mean(target_distances)) if target_distances else None,
        "stable_steps_min": int(np.min(stable_steps)) if stable_steps else None,
        "stable_steps_max": int(np.max(stable_steps)) if stable_steps else None,
        "transport_floor_contacts_total": int(np.sum(transport_floor)) if transport_floor else 0,
        "final_ball_xy_mean": np.mean(final_xy, axis=0) if final_xy else None,
        "final_ball_xy_std": np.std(final_xy, axis=0) if final_xy else None,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Arm-Hand Stage1 V3 Pick-Place Target Sweep Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{summary['status']}**\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{summary['episodes']}`\n",
        f"- Success count: `{summary['success_count']} / {summary['episodes']}`\n",
        f"- Terminal reasons: `{summary['terminal_reason_counts']}`\n",
        f"- Target center base: `{payload['target_center']}`\n",
        f"- Target radius: `{payload['target_radius']:.3f} m`\n",
        f"- Required stable steps: `{payload['required_stable_steps']}`\n",
        f"- Target distance XY range: `{summary['target_distance_xy_min']:.6f} m` to `{summary['target_distance_xy_max']:.6f} m`\n",
        f"- Target distance XY mean: `{summary['target_distance_xy_mean']:.6f} m`\n",
        f"- Stable steps range: `{summary['stable_steps_min']}` to `{summary['stable_steps_max']}`\n",
        f"- Transport floor contacts total: `{summary['transport_floor_contacts_total']}`\n",
        "- Training ready: **No, scripted smoke sweep only**\n\n",
        "## Episode Results\n\n",
        "| ep | target offset xy | target center xy | status | reason | final ball xy | target dist xy m | stable steps | transport floor | final hand | final floor |\n",
        "|---:|---|---|---|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        final = row["final_metrics"]
        contact = final["contact"]
        lines.append(
            f"| {row['episode_id']} | `{np.round(row['target_offset'][:2], 4).tolist()}` | "
            f"`{np.round(row['target_center'][:2], 4).tolist()}` | {row['status']} | "
            f"{row['terminal_reason']} | `{np.round(final['ball_position'][:2], 4).tolist()}` | "
            f"{final['target_distance_xy']:.6f} | {row['counters']['stable_target_steps']} | "
            f"{row['counters']['transport_floor_contacts']} | {contact['ball_hand_contact_count']} | "
            f"{contact['ball_floor_contact_count']} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This sweep changes the target label around the current same-platform target pad while using the same scripted motion.\n",
            "- It measures placement tolerance for the first v3 scaffold; it is not yet a target-conditioned expert controller.\n",
            "- Dataset v0.5 can start as a fixed-target pick-place dataset after replay QA, then expand to target-conditioned motion once the scripted arm pose is parameterized by target center.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a v3 scripted pick-place target-neighborhood sweep.")
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--target-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=DEFAULT_TARGET_CENTER)
    parser.add_argument("--x-offsets", default="-0.02,-0.01,0.0,0.01,0.02")
    parser.add_argument("--y-offsets", default="-0.02,-0.01,0.0,0.01,0.02")
    parser.add_argument("--target-radius", type=float, default=DEFAULT_TARGET_RADIUS_M)
    parser.add_argument("--required-stable-steps", type=int, default=DEFAULT_REQUIRED_STABLE_STEPS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    parser.add_argument("--video-placeholder", type=Path, default=Path("__no_video_for_sweep__.mp4"))
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--transport-steps", type=int, default=900)
    parser.add_argument("--descend-steps", type=int, default=500)
    parser.add_argument("--pre-release-settle-steps", type=int, default=180)
    parser.add_argument("--release-steps", type=int, default=600)
    parser.add_argument("--retreat-steps", type=int, default=300)
    parser.add_argument("--settle-steps", type=int, default=600)
    args = parser.parse_args()

    targets = build_target_centers(args)
    results = []
    for row in targets:
        payload = run_demo(demo_args(args, row["target_center"]))
        result = {
            "episode_id": int(row["episode_id"]),
            "target_offset": row["target_offset"],
            "target_center": row["target_center"],
            "status": payload["status"],
            "terminal_reason": payload["terminal_reason"],
            "counters": payload["counters"],
            "final_metrics": payload["final_metrics"],
        }
        results.append(result)
        print(
            f"ep={result['episode_id']:02d} offset={np.round(row['target_offset'][:2], 4).tolist()} "
            f"{result['status']} reason={result['terminal_reason']} "
            f"dist={result['final_metrics']['target_distance_xy']:.4f}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "target_center": np.asarray(args.target_center, dtype=np.float64),
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "x_offsets": parse_values(args.x_offsets),
        "y_offsets": parse_values(args.y_offsets),
        "summary": summarize(results),
        "results": results,
        "training_ready": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
