#!/usr/bin/env python3
"""Online rollout evaluation for the experimental Stage2 BC smoke policy."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch

from arm_hand_stage1_task_api import CURRENT_LIFT_SCENE, DEFAULT_TASK_THRESHOLDS, ArmHandStage1TaskAPI
from arm_hand_stage1_v2_bc_common import (
    DEFAULT_CHECKPOINT,
    DEFAULT_DATASET,
    DEFAULT_EVAL_META,
    DEFAULT_EVAL_REPORT,
    json_ready,
    load_dataset,
    load_policy,
    predict_action,
)


FrameCallback = Callable[[ArmHandStage1TaskAPI, int, dict[str, Any] | None], None]


def available_episode_ids(data) -> list[int]:
    return sorted(int(v) for v in np.unique(data["episode_ids"].astype(np.int32)))


def episode_initial_ball(data, episode_id: int) -> np.ndarray:
    idxs = np.where(data["episode_ids"].astype(np.int32) == int(episode_id))[0]
    if len(idxs) == 0:
        raise KeyError(f"Episode {episode_id} not in dataset")
    return data["initial_ball_positions"][idxs[0]].astype(np.float64)


def episode_offset(data, episode_id: int) -> np.ndarray:
    idxs = np.where(data["episode_ids"].astype(np.int32) == int(episode_id))[0]
    if len(idxs) == 0:
        raise KeyError(f"Episode {episode_id} not in dataset")
    return data["ball_offsets"][idxs[0]].astype(np.float64)


def run_policy_episode(
    *,
    api: ArmHandStage1TaskAPI,
    model,
    checkpoint: dict[str, Any],
    device: torch.device,
    episode_id: int,
    initial_ball: np.ndarray,
    ball_offset: np.ndarray,
    max_steps: int,
    clip_to_train_range: bool,
    action_smoothing: float = 0.0,
    sample_every: int = 50,
    frame_callback: FrameCallback | None = None,
) -> dict[str, Any]:
    api.reset_hand_open(ball_position=initial_ball)
    lifted_once = False
    threshold_for_lifted_once = DEFAULT_TASK_THRESHOLDS["dropped_after_lift_height_m"]
    prev_action: np.ndarray | None = None
    trace = []
    final_eval: dict[str, Any] | None = None
    action_l2_sum = 0.0
    action_delta_l2_sum = 0.0
    max_action_abs = 0.0

    if frame_callback is not None:
        frame_callback(api, 0, None)

    for step_id in range(max_steps):
        obs = api.get_observation()
        action, pred_norm = predict_action(
            model,
            checkpoint,
            obs["vector"],
            step_id=step_id,
            ball_offset=ball_offset,
            device=device,
            clip_to_train_range=clip_to_train_range,
        )
        if prev_action is not None and action_smoothing > 0.0:
            smoothing = float(np.clip(action_smoothing, 0.0, 0.99))
            action = smoothing * prev_action + (1.0 - smoothing) * action
        if prev_action is not None:
            action_delta_l2_sum += float(np.linalg.norm(action - prev_action))
        prev_action = action.copy()
        action_l2_sum += float(np.linalg.norm(action))
        max_action_abs = max(max_action_abs, float(np.max(np.abs(action))))

        api.step_action(action, n=1, pin_ball=False)
        metrics = api.compute_task_metrics(initial_ball)
        lifted_once = lifted_once or metrics["ball_lift_height"] >= threshold_for_lifted_once
        evaluation = api.evaluate_lift_task_state(
            initial_ball,
            step_count=step_id + 1,
            max_episode_steps=max_steps,
            lifted_once=lifted_once,
        )
        final_eval = evaluation
        if step_id % max(1, sample_every) == 0 or evaluation["done"]:
            contact = metrics["contact"]
            trace.append(
                {
                    "step": int(step_id + 1),
                    "status": evaluation["episode_status"],
                    "reason": evaluation["terminal_reason"],
                    "lift_height": float(metrics["ball_lift_height"]),
                    "reward": float(evaluation["reward"]["total"]),
                    "ball_hand_contacts": int(contact["ball_hand_contact_count"]),
                    "ball_floor_contacts": int(contact.get("ball_floor_contact_count", 0)),
                    "max_penetration": float(contact["max_penetration"]),
                    "action_norm_l2": float(np.linalg.norm(action)),
                    "pred_norm_l2": float(np.linalg.norm(pred_norm)),
                }
            )
        if frame_callback is not None:
            frame_callback(api, step_id + 1, evaluation)
        if evaluation["done"]:
            break

    if final_eval is None:
        final_eval = api.evaluate_lift_task_state(initial_ball, step_count=0, max_episode_steps=max_steps)
    final_metrics = final_eval["official_metrics"]
    steps = max(1, int(final_eval["step_count"]))
    return {
        "episode_id": int(episode_id),
        "initial_ball": initial_ball,
        "ball_offset": ball_offset,
        "status": final_eval["episode_status"],
        "terminal_reason": final_eval["terminal_reason"],
        "success": bool(final_eval["success"]),
        "failure": bool(final_eval["failure"]),
        "done": bool(final_eval["done"]),
        "steps": int(final_eval["step_count"]),
        "reward": float(final_eval["reward"]["total"]),
        "final_metrics": final_metrics,
        "action_l2_mean": float(action_l2_sum / steps),
        "action_delta_l2_mean": float(action_delta_l2_sum / steps),
        "max_action_abs": float(max_action_abs),
        "trace": trace,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    reasons: dict[str, int] = {}
    for row in results:
        reasons[row["terminal_reason"]] = reasons.get(row["terminal_reason"], 0) + 1
    lifts = [float(row["final_metrics"]["ball_lift_height"]) for row in results]
    rewards = [float(row["reward"]) for row in results]
    status = "PASS" if success_count == len(results) else ("PARTIAL" if success_count > 0 else "FAIL")
    return {
        "status": status,
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": reasons,
        "lift_min": float(np.min(lifts)) if lifts else float("nan"),
        "lift_max": float(np.max(lifts)) if lifts else float("nan"),
        "lift_mean": float(np.mean(lifts)) if lifts else float("nan"),
        "reward_mean": float(np.mean(rewards)) if rewards else float("nan"),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Arm-Hand Stage1 V2 BC Smoke Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{payload['summary']['status']}**\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{payload['summary']['episodes']}`\n",
        f"- Success count: `{payload['summary']['success_count']} / {payload['summary']['episodes']}`\n",
        f"- Terminal reasons: `{payload['summary']['terminal_reason_counts']}`\n",
        f"- Lift range: `{payload['summary']['lift_min']:.6f} m` to `{payload['summary']['lift_max']:.6f} m`\n",
        f"- Mean lift: `{payload['summary']['lift_mean']:.6f} m`\n",
        f"- Max steps: `{payload['max_steps']}`\n",
        f"- Action clipping: `{payload['clip_to_train_range']}`\n",
        f"- Action smoothing: `{payload['action_smoothing']}`\n",
        f"- Training ready: **No, experimental BC smoke only**\n\n",
        "## Episode Results\n\n",
        "| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |\n",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        metrics = row["final_metrics"]
        contact = metrics["contact"]
        lines.append(
            f"| {row['episode_id']} | {row['status']} | {row['terminal_reason']} | {row['steps']} | "
            f"{metrics['ball_lift_height']:.6f} | {row['reward']:.6f} | "
            f"{contact['ball_hand_contact_count']} | {contact.get('ball_floor_contact_count', 0)} | "
            f"{contact['max_penetration']:.6f} | {row['action_l2_mean']:.6f} | {row['action_delta_l2_mean']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is the online rollout gate for the first BC smoke checkpoint.\n",
            "- PASS/PARTIAL here still does not promote the model to the maintained project baseline.\n",
            "- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate experimental arm-hand Stage2 BC smoke policy online.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_LIFT_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_EVAL_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_EVAL_META)
    parser.add_argument("--all-episodes", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--episode-id", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=1230)
    parser.add_argument("--sample-every", type=int, default=50)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable; using CPU.")
        args.device = "cpu"
    device = torch.device(args.device)
    data = load_dataset(args.dataset)
    model, checkpoint = load_policy(args.checkpoint, device)
    selected = available_episode_ids(data) if args.all_episodes else [int(args.episode_id)]
    api = ArmHandStage1TaskAPI(args.scene)
    results = [
        run_policy_episode(
            api=api,
            model=model,
            checkpoint=checkpoint,
            device=device,
            episode_id=episode_id,
            initial_ball=episode_initial_ball(data, episode_id),
            ball_offset=episode_offset(data, episode_id),
            max_steps=args.max_steps,
            clip_to_train_range=not args.no_train_range_clip,
            action_smoothing=args.action_smoothing,
            sample_every=args.sample_every,
        )
        for episode_id in selected
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(args.checkpoint.resolve()),
        "dataset": str(args.dataset.resolve()),
        "scene": str(args.scene.resolve()),
        "device": str(device),
        "max_steps": int(args.max_steps),
        "clip_to_train_range": not args.no_train_range_clip,
        "action_smoothing": float(args.action_smoothing),
        "checkpoint_status": checkpoint.get("status"),
        "checkpoint_final_val_loss": float(checkpoint.get("final_val_loss", float("nan"))),
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
