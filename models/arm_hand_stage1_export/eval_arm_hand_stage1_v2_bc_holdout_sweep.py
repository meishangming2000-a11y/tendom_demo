#!/usr/bin/env python3
"""Run an unseen-offset long-hold sweep for the experimental Stage2 BC policy."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import CURRENT_LIFT_SCENE, ArmHandStage1TaskAPI
from arm_hand_stage1_v2_bc_common import json_ready, load_policy
from eval_arm_hand_stage1_v2_bc_smoke import run_policy_episode


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_CHECKPOINT = CHECKPOINTS / "bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v2_bc_v0_4_holdout_sweep_report.md"
DEFAULT_META = META / "arm_hand_stage1_v2_bc_v0_4_holdout_sweep.json"
DEFAULT_EXCLUDE_DATASETS = [
    DATA / "arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz",
    DATA / "arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz",
]


def parse_values(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def offset_key(offset: np.ndarray) -> tuple[float, float, float]:
    return tuple(round(float(v), 6) for v in offset.tolist())


def dataset_offsets(path: Path) -> set[tuple[float, float, float]]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = np.load(path, allow_pickle=False)
    if "ball_offsets" not in data.files or "episode_ids" not in data.files:
        raise KeyError(f"{path} does not contain ball_offsets/episode_ids")
    episode_ids = data["episode_ids"].astype(np.int32)
    out: set[tuple[float, float, float]] = set()
    for episode_id in sorted(int(v) for v in np.unique(episode_ids)):
        idx = np.where(episode_ids == int(episode_id))[0][0]
        out.add(offset_key(data["ball_offsets"][idx].astype(np.float64)))
    return out


def build_offsets(args) -> tuple[list[np.ndarray], dict[str, Any]]:
    raw_offsets = [
        np.asarray([x, y, z], dtype=np.float64)
        for x in parse_values(args.x_values)
        for y in parse_values(args.y_values)
        for z in parse_values(args.z_values)
    ]
    seen: set[tuple[float, float, float]] = set()
    for dataset in args.exclude_seen_dataset:
        seen.update(dataset_offsets(Path(dataset)))
    selected = [offset for offset in raw_offsets if offset_key(offset) not in seen]
    return selected, {
        "x_values": parse_values(args.x_values),
        "y_values": parse_values(args.y_values),
        "z_values": parse_values(args.z_values),
        "raw_offset_count": len(raw_offsets),
        "excluded_seen_count": len(raw_offsets) - len(selected),
        "exclude_seen_datasets": [str(Path(item).resolve()) for item in args.exclude_seen_dataset],
        "selected_offsets": [offset.tolist() for offset in selected],
    }


def failure_bucket(result: dict[str, Any]) -> str:
    if result["success"]:
        return "passed"
    hold = result.get("hold_check", {})
    failure_reason = hold.get("failure_reason")
    if failure_reason:
        if failure_reason == "timeout" and hold.get("first_success_step") is None:
            return "no_lift_timeout"
        return str(failure_reason)
    reason = str(result.get("terminal_reason", "unknown"))
    if reason == "timeout" and hold.get("first_success_step") is None:
        return "no_lift_timeout"
    return reason


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    terminal_reasons = Counter(str(row["terminal_reason"]) for row in results)
    buckets = Counter(failure_bucket(row) for row in results)
    final_lifts = [float(row["final_metrics"]["ball_lift_height"]) for row in results]
    hold_mins = [
        float(row["hold_check"]["min_lift_height_after_success"])
        for row in results
        if row.get("hold_check", {}).get("min_lift_height_after_success") is not None
    ]
    status = "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL")
    return {
        "status": status,
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": dict(terminal_reasons),
        "failure_bucket_counts": dict(buckets),
        "final_lift_min": float(np.min(final_lifts)) if final_lifts else float("nan"),
        "final_lift_max": float(np.max(final_lifts)) if final_lifts else float("nan"),
        "final_lift_mean": float(np.mean(final_lifts)) if final_lifts else float("nan"),
        "hold_min_lift_min": float(np.min(hold_mins)) if hold_mins else None,
        "hold_min_lift_max": float(np.max(hold_mins)) if hold_mins else None,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Arm-Hand Stage1 V2 BC V0.4 Holdout Sweep Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{summary['status']}**\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{summary['episodes']}`\n",
        f"- Success count: `{summary['success_count']} / {summary['episodes']}`\n",
        f"- Terminal reasons: `{summary['terminal_reason_counts']}`\n",
        f"- Failure buckets: `{summary['failure_bucket_counts']}`\n",
        f"- Final lift range: `{summary['final_lift_min']:.6f} m` to `{summary['final_lift_max']:.6f} m`\n",
        f"- Final lift mean: `{summary['final_lift_mean']:.6f} m`\n",
        f"- Hold min lift range: `{summary['hold_min_lift_min']}` to `{summary['hold_min_lift_max']}`\n",
        f"- Offset grid: `{payload['grid']}`\n",
        f"- Action smoothing: `{payload['action_smoothing']}`\n",
        f"- Hold after success steps: `{payload['hold_after_success_steps']}`\n",
        f"- Hold settle steps: `{payload['hold_settle_steps']}`\n",
        f"- Freeze after settle: `{payload['freeze_action_after_settle']}`\n",
        "- Training ready: **No, experimental BC smoke only**\n\n",
        "## Episode Results\n\n",
        "| ep | offset xyz | status | reason | bucket | steps | first success | hold steps | hold min m | final lift m | floor-after | no-contact-after | max pen after |\n",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        hold = row.get("hold_check", {})
        hold_min = hold.get("min_lift_height_after_success")
        hold_min_text = "n/a" if hold_min is None else f"{float(hold_min):.6f}"
        first = hold.get("first_success_step")
        first_text = "n/a" if first is None else str(first)
        lines.append(
            f"| {row['episode_id']} | `{np.round(row['ball_offset'], 6).tolist()}` | {row['status']} | "
            f"{row['terminal_reason']} | {failure_bucket(row)} | {row['steps']} | {first_text} | "
            f"{hold.get('consecutive_hold_steps', 0)} | {hold_min_text} | "
            f"{row['final_metrics']['ball_lift_height']:.6f} | "
            f"{hold.get('floor_contact_steps_after_success', 0)} | "
            f"{hold.get('no_hand_contact_steps_after_success', 0)} | "
            f"{hold.get('max_penetration_after_success', 0.0):.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This sweep uses unseen offset midpoints between the accepted v0.1/v0.2 reset grid points.\n",
            "- PASS here is a promotion gate candidate, not a final maintained baseline by itself.\n",
            "- If any episode fails, collect targeted diagnostics before RL warm-start.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an unseen-offset long-hold sweep for Stage2 BC smoke.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_LIFT_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    parser.add_argument("--x-values", default="0.0125,0.015,0.0175")
    parser.add_argument("--y-values", default="0.005,0.0075,0.0125,0.0175")
    parser.add_argument("--z-values", default="0.0")
    parser.add_argument("--exclude-seen-dataset", action="append", default=[str(path) for path in DEFAULT_EXCLUDE_DATASETS])
    parser.add_argument("--max-steps", type=int, default=3000)
    parser.add_argument("--sample-every", type=int, default=200)
    parser.add_argument("--action-smoothing", type=float, default=0.5)
    parser.add_argument("--hold-after-success-steps", type=int, default=900)
    parser.add_argument("--hold-lift-height-min", type=float, default=0.070)
    parser.add_argument("--hold-settle-steps", type=int, default=180)
    parser.add_argument("--freeze-action-after-settle", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable; using CPU.")
        args.device = "cpu"
    device = torch.device(args.device)
    offsets, grid = build_offsets(args)
    if not offsets:
        raise RuntimeError("Holdout grid is empty after excluding seen offsets.")

    model, checkpoint = load_policy(args.checkpoint, device)
    api = ArmHandStage1TaskAPI(args.scene)
    base_ball = api.get_ball_pose()["position"].copy()
    results = []
    for episode_id, offset in enumerate(offsets):
        result = run_policy_episode(
            api=api,
            model=model,
            checkpoint=checkpoint,
            device=device,
            episode_id=episode_id,
            initial_ball=base_ball + offset,
            ball_offset=offset,
            max_steps=args.max_steps,
            clip_to_train_range=not args.no_train_range_clip,
            action_smoothing=args.action_smoothing,
            hold_after_success_steps=args.hold_after_success_steps,
            hold_lift_height_min=args.hold_lift_height_min,
            hold_settle_steps=args.hold_settle_steps,
            freeze_action_after_settle=args.freeze_action_after_settle,
            sample_every=args.sample_every,
        )
        results.append(result)
        print(
            f"ep={episode_id:02d} offset={np.round(offset, 6).tolist()} "
            f"{result['terminal_reason']} success={result['success']}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(args.checkpoint.resolve()),
        "scene": str(args.scene.resolve()),
        "device": str(device),
        "base_ball": base_ball,
        "grid": grid,
        "max_steps": int(args.max_steps),
        "sample_every": int(args.sample_every),
        "clip_to_train_range": not args.no_train_range_clip,
        "action_smoothing": float(args.action_smoothing),
        "hold_after_success_steps": int(args.hold_after_success_steps),
        "hold_lift_height_min": float(args.hold_lift_height_min),
        "hold_settle_steps": int(args.hold_settle_steps),
        "freeze_action_after_settle": bool(args.freeze_action_after_settle),
        "checkpoint_status": checkpoint.get("status"),
        "summary": summarize(results),
        "results": results,
        "training_ready": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
