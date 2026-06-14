#!/usr/bin/env python3
"""Run the Stage3.11D-D lift-quality head as an online shadow evaluator.

This is a MuJoCo-only validation step. It loads the offline Stage3.11D-D
LiftQualityHead checkpoint, replays randomized event-gated pinch trials, and
scores model predictions on dense trace frames without changing controller
actions.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
import export_stage3_11d_d_dense_sensor_fusion_dataset_v0 as dense
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import train_stage3_11d_b_event_contact_gated_refine_v0 as event
from train_stage3_11d_d_lift_quality_head_v0 import LiftQualityHead


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_SELECTED = META / "stage3_11d_c_geometry_force_refine_selected_v0.json"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_11d_d_lift_quality_head_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_11d_e_lift_quality_shadow_v0_report.md"
DEFAULT_METADATA = META / "stage3_11d_e_lift_quality_shadow_v0.json"

STATUS = "stage3_11d_e_lift_quality_shadow_v0_mujoco_only_not_control_promoted"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sigmoid_np(logits: np.ndarray) -> np.ndarray:
    clipped = np.clip(logits.astype(np.float32), -60.0, 60.0)
    return (1.0 / (1.0 + np.exp(-clipped))).astype(np.float32)


def metric_from_counts(counts: dict[str, int], positives: int, total: int) -> dict[str, Any]:
    tp = int(counts.get("tp", 0))
    tn = int(counts.get("tn", 0))
    fp = int(counts.get("fp", 0))
    fn = int(counts.get("fn", 0))
    precision = float(tp / max(1, tp + fp))
    recall = float(tp / max(1, tp + fn))
    f1 = float(2.0 * precision * recall / max(1e-9, precision + recall))
    return {
        "accuracy": float((tp + tn) / max(1, total)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "positive_fraction": float(positives / max(1, total)),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total": int(total),
    }


def empty_counts() -> dict[str, int]:
    return {"tp": 0, "tn": 0, "fp": 0, "fn": 0}


def update_counts(counts: dict[str, int], pred: bool, truth: bool) -> None:
    if pred and truth:
        counts["tp"] += 1
    elif pred and not truth:
        counts["fp"] += 1
    elif not pred and truth:
        counts["fn"] += 1
    else:
        counts["tn"] += 1


def compact_result(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "dense_sensor_trace"}


def load_shadow_model(checkpoint: Path) -> dict[str, Any]:
    checkpoint = Path(checkpoint).resolve()
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    target_names = [str(name) for name in payload["target_names"]]
    model = LiftQualityHead(
        int(payload["input_dim"]),
        len(target_names),
        int(payload["hidden_dim"]),
        float(payload["dropout"]),
    )
    model.load_state_dict(payload["model_state_dict"])
    model.eval()
    obs_mean = np.asarray(payload["obs_mean"], dtype=np.float32)
    obs_std = np.asarray(payload["obs_std"], dtype=np.float32)
    obs_std = np.maximum(obs_std, 1e-6).astype(np.float32)
    dataset_metadata = payload.get("dataset_metadata") or {}
    phase_names = [str(name) for name in dataset_metadata.get("phase_names", dense.PHASE_NAMES)]
    return {
        "checkpoint": str(checkpoint),
        "payload": payload,
        "model": model,
        "input_dim": int(payload["input_dim"]),
        "target_names": target_names,
        "feature_names": [str(name) for name in payload.get("feature_names", [])],
        "obs_mean": obs_mean,
        "obs_std": obs_std,
        "phase_names": phase_names,
    }


def fixed_phase_id(phase_names: list[str], phase: str) -> int:
    try:
        return int(phase_names.index(str(phase)))
    except ValueError:
        return -1


def frame_feature(
    frame: dict[str, Any],
    row: dict[str, Any],
    case: event.RefineCase,
    phase_names: list[str],
) -> tuple[np.ndarray, str, int]:
    phase = str(frame.get("label", "unknown"))
    phase_id = fixed_phase_id(phase_names, phase)
    vision = dense.vision_features(frame, row, case)
    tactile = dense.tactile_features(frame)
    force = dense.force_features(frame, case.candidate.active_finger)
    context = dense.context_features(frame, phase, case)
    qpos = np.asarray(frame.get("qpos", []), dtype=np.float32)
    qvel = np.asarray(frame.get("qvel", []), dtype=np.float32)
    ctrl = np.asarray(frame.get("ctrl", []), dtype=np.float32)
    proprio = np.concatenate([qpos, qvel, ctrl]).astype(np.float32)
    obs = np.concatenate(
        [
            vision,
            tactile,
            force,
            context,
            proprio,
            dense.phase_one_hot(phase_id, len(phase_names)),
        ]
    ).astype(np.float32)
    return obs, phase, phase_id


def frame_targets(
    frame: dict[str, Any],
    row: dict[str, Any],
    phase: str,
    args: argparse.Namespace,
    case: event.RefineCase,
    target_names: list[str],
) -> np.ndarray:
    labels = dense.frame_labels(frame, row, phase, args, case)
    indices = [dense.SAFETY_LABEL_NAMES.index(name) for name in target_names]
    return labels[indices].astype(np.float32)


def predict_trace(
    shadow: dict[str, Any],
    trace: list[dict[str, Any]],
    row: dict[str, Any],
    case: event.RefineCase,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    features: list[np.ndarray] = []
    records: list[dict[str, Any]] = []
    phase_names = shadow["phase_names"]
    input_dim = int(shadow["input_dim"])
    for frame in trace:
        obs, phase, phase_id = frame_feature(frame, row, case, phase_names)
        if obs.shape[0] != input_dim:
            raise ValueError(
                f"Feature dim mismatch for phase {phase}: got {obs.shape[0]}, expected {input_dim}. "
                "Check D-D checkpoint/dataset feature schema."
            )
        truth = frame_targets(frame, row, phase, args, case, shadow["target_names"])
        features.append(obs)
        records.append(
            {
                "frame": frame,
                "phase": phase,
                "phase_id": int(phase_id),
                "truth": truth,
                "is_grasp_evidence": bool(phase in dense.GRASP_EVIDENCE_PHASES),
            }
        )
    if not features:
        return []
    x = np.asarray(features, dtype=np.float32)
    x_norm = ((x - shadow["obs_mean"].reshape(1, -1)) / shadow["obs_std"].reshape(1, -1)).astype(np.float32)
    with torch.no_grad():
        logits = shadow["model"](torch.from_numpy(x_norm)).cpu().numpy()
    probs = sigmoid_np(logits)
    for idx, record in enumerate(records):
        record["prob"] = probs[idx].astype(np.float32)
    return records


def close_window(active: dict[str, Any], windows: list[dict[str, Any]]) -> None:
    if not active:
        return
    count = max(1, int(active["row_count"]))
    windows.append(
        {
            "episode_index": int(active["episode_index"]),
            "label": str(active["label"]),
            "error_type": str(active["error_type"]),
            "terminal_reason": str(active["terminal_reason"]),
            "start_dense_step_index": int(active["start_dense_step_index"]),
            "end_dense_step_index": int(active["end_dense_step_index"]),
            "row_count": int(active["row_count"]),
            "start_phase": str(active["start_phase"]),
            "end_phase": str(active["end_phase"]),
            "prob_mean": float(active["prob_sum"] / count),
            "prob_min": float(active["prob_min"]),
            "prob_max": float(active["prob_max"]),
        }
    )


def update_windows(
    active_by_label: dict[str, dict[str, Any]],
    windows: list[dict[str, Any]],
    *,
    episode_index: int,
    terminal_reason: str,
    target_names: list[str],
    record: dict[str, Any],
    pred: np.ndarray,
    truth: np.ndarray,
) -> None:
    frame = record["frame"]
    phase = str(record["phase"])
    step = int(frame.get("dense_step_index", -1))
    for idx, name in enumerate(target_names):
        error_type = ""
        if bool(pred[idx]) and not bool(truth[idx]):
            error_type = "fp"
        elif not bool(pred[idx]) and bool(truth[idx]):
            error_type = "fn"
        active = active_by_label.get(name)
        if not error_type:
            if active:
                close_window(active, windows)
                active_by_label.pop(name, None)
            continue
        prob = float(record["prob"][idx])
        if active and active.get("error_type") == error_type:
            active["end_dense_step_index"] = step
            active["end_phase"] = phase
            active["row_count"] += 1
            active["prob_sum"] += prob
            active["prob_min"] = min(float(active["prob_min"]), prob)
            active["prob_max"] = max(float(active["prob_max"]), prob)
            continue
        if active:
            close_window(active, windows)
        active_by_label[name] = {
            "episode_index": int(episode_index),
            "label": name,
            "error_type": error_type,
            "terminal_reason": terminal_reason,
            "start_dense_step_index": step,
            "end_dense_step_index": step,
            "row_count": 1,
            "start_phase": phase,
            "end_phase": phase,
            "prob_sum": prob,
            "prob_min": prob,
            "prob_max": prob,
        }


def summarize_shadow(
    *,
    args: argparse.Namespace,
    results: list[dict[str, Any]],
    episode_summaries: list[dict[str, Any]],
    target_names: list[str],
    evidence_stats: dict[str, dict[str, int]],
    evidence_positives: dict[str, int],
    all_stats: dict[str, dict[str, int]],
    all_positives: dict[str, int],
    evidence_total: int,
    all_total: int,
    false_windows: list[dict[str, Any]],
) -> dict[str, Any]:
    terminal_counts = Counter(str(row.get("terminal_reason", "unknown")) for row in results)
    success_count = int(sum(1 for row in results if dense.as_bool(row.get("success"))))
    evidence_metrics = {
        name: metric_from_counts(evidence_stats[name], evidence_positives[name], evidence_total) for name in target_names
    }
    all_metrics = {name: metric_from_counts(all_stats[name], all_positives[name], all_total) for name in target_names}
    false_window_counts = Counter(
        (
            str(row["label"]),
            str(row["error_type"]),
            str(row["start_phase"]),
            str(row["terminal_reason"]),
        )
        for row in false_windows
    )
    failed = [row for row in episode_summaries if not bool(row["success"])]
    passed = bool(
        evidence_total > 0
        and all(float(evidence_metrics[name]["f1"]) >= float(args.min_label_f1) for name in target_names)
    )
    return {
        "trials": int(len(results)),
        "success_count": success_count,
        "success_rate": float(success_count / max(1, len(results))),
        "terminal_reason_counts": dict(terminal_counts),
        "total_trace_rows": int(all_total),
        "evidence_trace_rows": int(evidence_total),
        "evidence_metrics": evidence_metrics,
        "all_phase_metrics": all_metrics,
        "false_window_count": int(len(false_windows)),
        "false_window_top_counts": [
            {
                "label": label,
                "error_type": error_type,
                "phase": phase,
                "terminal_reason": reason,
                "count": int(count),
            }
            for (label, error_type, phase, reason), count in false_window_counts.most_common(16)
        ],
        "failed_episodes": int(len(failed)),
        "failed_episode_adjust_predicted_count": int(
            sum(1 for row in failed if int(row.get("pred_adjust_needed_evidence_frames", 0)) > 0)
        ),
        "failed_episode_no_adjust_predicted_count": int(
            sum(1 for row in failed if int(row.get("pred_adjust_needed_evidence_frames", 0)) <= 0)
        ),
        "successful_episode_hold_safe_predicted_count": int(
            sum(
                1
                for row in episode_summaries
                if bool(row["success"]) and int(row.get("pred_hold_safe_evidence_frames", 0)) > 0
            )
        ),
        "shadow_gate_passed": passed,
        "shadow_gate_min_label_f1": float(args.min_label_f1),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.11D-E Lift Quality Shadow v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only online shadow evaluation.\n",
        "- Loads the Stage3.11D-D LiftQualityHead checkpoint and predicts on dense event-runner trace frames.\n",
        "- The shadow head does not change actions, timing, force gates, or release logic.\n",
        "- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.\n",
        "- No full-action ACT/DP, hardware runtime, or demo-gallery promotion is made here.\n\n",
        "## Inputs\n\n",
        f"- Selected center: `{payload['selected']}`\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Trials: `{s['trials']}`\n",
        f"- Dense trace sample every: `{payload['args']['dense_trace_sample_every']}`\n\n",
        "## Online Trial Summary\n\n",
        f"- Event controller success: `{s['success_count']} / {s['trials']}` (`{s['success_rate']:.3f}`)\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Trace rows all/evidence: `{s['total_trace_rows']}` / `{s['evidence_trace_rows']}`\n",
        f"- Shadow gate passed: `{s['shadow_gate_passed']}` "
        f"(min label F1 `{s['shadow_gate_min_label_f1']:.3f}`)\n\n",
        "## Evidence-Phase Shadow Metrics\n\n",
        "| label | accuracy | precision | recall | F1 | positives | tp | fp | fn |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for name, metric in s["evidence_metrics"].items():
        lines.append(
            f"| `{name}` | {metric['accuracy']:.4f} | {metric['precision']:.4f} | "
            f"{metric['recall']:.4f} | {metric['f1']:.4f} | {metric['positive_fraction']:.4f} | "
            f"{metric['tp']} | {metric['fp']} | {metric['fn']} |\n"
        )
    lines.extend(
        [
            "\n## Failure Detection Diagnostics\n\n",
            f"- Failed episodes: `{s['failed_episodes']}`\n",
            f"- Failed episodes with predicted `adjust_needed_now`: "
            f"`{s['failed_episode_adjust_predicted_count']} / {max(1, s['failed_episodes'])}`\n",
            f"- Failed episodes without predicted `adjust_needed_now`: "
            f"`{s['failed_episode_no_adjust_predicted_count']} / {max(1, s['failed_episodes'])}`\n",
            f"- Successful episodes with predicted `hold_safe_now`: "
            f"`{s['successful_episode_hold_safe_predicted_count']} / {max(1, s['success_count'])}`\n\n",
            "## False Windows\n\n",
        ]
    )
    if s["false_window_top_counts"]:
        lines.extend(["| label | type | phase | terminal reason | windows |\n", "|---|---|---|---|---:|\n"])
        for row in s["false_window_top_counts"]:
            lines.append(
                f"| `{row['label']}` | `{row['error_type']}` | `{row['phase']}` | "
                f"`{row['terminal_reason']}` | {row['count']} |\n"
            )
    else:
        lines.append("- No false-positive or false-negative windows on evidence phases.\n")
    top_windows = payload.get("false_windows_top", [])
    if top_windows:
        lines.extend(
            [
                "\n## Largest False Windows\n\n",
                "| episode | label | type | steps | rows | phases | prob mean | terminal reason |\n",
                "|---:|---|---|---|---:|---|---:|---|\n",
            ]
        )
        for row in top_windows[:12]:
            lines.append(
                f"| {row['episode_index']} | `{row['label']}` | `{row['error_type']}` | "
                f"{row['start_dense_step_index']}-{row['end_dense_step_index']} | {row['row_count']} | "
                f"`{row['start_phase']}->{row['end_phase']}` | {row['prob_mean']:.4f} | "
                f"`{row['terminal_reason']}` |\n"
            )
    lines.extend(
        [
            "\n## Next\n\n",
            "- If this shadow pass is clean, use the same online frames to build a bounded residual micro-adjust teacher.\n",
            "- If false windows cluster in one phase, fix labels/features or add targeted data before allowing the head to affect control.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parent = robustness.build_parser()
    parser = argparse.ArgumentParser(
        description="Stage3.11D-E lift-quality online shadow evaluator.",
        parents=[parent],
        add_help=False,
        conflict_handler="resolve",
    )
    parser.set_defaults(
        selected=DEFAULT_SELECTED,
        report=DEFAULT_REPORT,
        metadata=DEFAULT_METADATA,
        trials=50,
        seed=20260612,
    )
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--dense-trace-sample-every", type=int, default=1)
    parser.add_argument("--decision-threshold", type=float, default=0.5)
    parser.add_argument("--min-label-f1", type=float, default=0.995)
    return parser


def main() -> int:
    args = dense.fill_from_robustness_defaults(build_parser().parse_args())
    import mujoco

    shadow = load_shadow_model(Path(args.checkpoint))
    scene = Path(args.scene).resolve()
    selected = Path(args.selected).resolve()
    base = robustness.apply_base_offsets(robustness.selected_case_from_json(selected), args)
    rng = np.random.default_rng(int(args.seed))
    ev_args = robustness.event_args_from(args)
    ev_args.capture_dense_sensor_trace = True
    ev_args.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))

    target_names = list(shadow["target_names"])
    evidence_stats = defaultdict(empty_counts)
    all_stats = defaultdict(empty_counts)
    evidence_positives = defaultdict(int)
    all_positives = defaultdict(int)
    evidence_total = 0
    all_total = 0
    false_windows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    episode_summaries: list[dict[str, Any]] = []
    threshold = float(args.decision_threshold)

    for idx in range(max(1, int(args.trials))):
        case = robustness.perturb_case(base, args, rng, idx)
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        records = predict_trace(shadow, list(row.get("dense_sensor_trace", [])), row, case, args)
        terminal_reason = str(row.get("terminal_reason", "unknown"))
        active_windows: dict[str, dict[str, Any]] = {}
        episode_counts = {
            "trace_rows": int(len(records)),
            "evidence_rows": 0,
            "pred_adjust_needed_evidence_frames": 0,
            "true_adjust_needed_evidence_frames": 0,
            "pred_hold_safe_evidence_frames": 0,
            "true_hold_safe_evidence_frames": 0,
        }
        for record in records:
            prob = np.asarray(record["prob"], dtype=np.float32)
            truth = np.asarray(record["truth"], dtype=np.float32) >= 0.5
            pred = prob >= threshold
            all_total += 1
            for label_idx, name in enumerate(target_names):
                update_counts(all_stats[name], bool(pred[label_idx]), bool(truth[label_idx]))
                all_positives[name] += int(bool(truth[label_idx]))
            if not bool(record["is_grasp_evidence"]):
                continue
            evidence_total += 1
            episode_counts["evidence_rows"] += 1
            for label_idx, name in enumerate(target_names):
                update_counts(evidence_stats[name], bool(pred[label_idx]), bool(truth[label_idx]))
                evidence_positives[name] += int(bool(truth[label_idx]))
            if "adjust_needed_now" in target_names:
                adjust_idx = target_names.index("adjust_needed_now")
                episode_counts["pred_adjust_needed_evidence_frames"] += int(bool(pred[adjust_idx]))
                episode_counts["true_adjust_needed_evidence_frames"] += int(bool(truth[adjust_idx]))
            if "hold_safe_now" in target_names:
                hold_idx = target_names.index("hold_safe_now")
                episode_counts["pred_hold_safe_evidence_frames"] += int(bool(pred[hold_idx]))
                episode_counts["true_hold_safe_evidence_frames"] += int(bool(truth[hold_idx]))
            update_windows(
                active_windows,
                false_windows,
                episode_index=idx,
                terminal_reason=terminal_reason,
                target_names=target_names,
                record=record,
                pred=pred,
                truth=truth,
            )
        for active in list(active_windows.values()):
            close_window(active, false_windows)

        compact = compact_result(row)
        compact["trial_index"] = int(idx)
        compact["dense_trace_rows"] = int(len(records))
        compact["evidence_trace_rows"] = int(episode_counts["evidence_rows"])
        compact["randomization"] = {
            "ball_offset_x": case.ball_offset_x,
            "ball_offset_y": case.ball_offset_y,
            "grasp_offset_x": case.grasp_offset_x,
            "grasp_offset_y": case.grasp_offset_y,
            "grasp_offset_z": case.grasp_offset_z,
            "ball_radius": case.ball_radius,
            "ball_mass": case.ball_mass,
            "tip_mu": case.candidate.tip_sliding_mu,
            "ball_mu": case.candidate.ball_sliding_mu,
            "non_tip_mu": case.candidate.non_tip_sliding_mu,
        }
        results.append(compact)
        episode_summaries.append(
            {
                "episode_index": int(idx),
                "success": bool(dense.as_bool(row.get("success"))),
                "status": str(row.get("status")),
                "terminal_reason": terminal_reason,
                "hold_lift_m_max": dense.as_float(row.get("hold_lift_m_max")),
                "score": dense.as_float(row.get("score")),
                **episode_counts,
            }
        )
        print(
            f"{idx + 1:03d}/{args.trials:03d} {row.get('status')} "
            f"rows={episode_counts['trace_rows']} evidence={episode_counts['evidence_rows']} "
            f"lift={dense.as_float(row.get('hold_lift_m_max')):.4f} reason={terminal_reason}"
        )

    false_windows_top = sorted(false_windows, key=lambda item: int(item["row_count"]), reverse=True)[:24]
    summary = summarize_shadow(
        args=args,
        results=results,
        episode_summaries=episode_summaries,
        target_names=target_names,
        evidence_stats=evidence_stats,
        evidence_positives=evidence_positives,
        all_stats=all_stats,
        all_positives=all_positives,
        evidence_total=evidence_total,
        all_total=all_total,
        false_windows=false_windows,
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-E",
        "status": STATUS,
        "scene": str(scene),
        "selected": str(selected),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "args": vars(args),
        "model": {
            "input_dim": int(shadow["input_dim"]),
            "target_names": target_names,
            "feature_count": int(len(shadow["feature_names"])),
            "phase_names": shadow["phase_names"],
            "checkpoint_status": str(shadow["payload"].get("status", "")),
            "checkpoint_config": str(shadow["payload"].get("config_name", "")),
        },
        "base_case": {
            "name": base.name,
            "candidate": base.candidate.__dict__,
            "tip_pair_separation_target": base.tip_pair_separation_target,
            "grasp_offset_x": base.grasp_offset_x,
            "grasp_offset_y": base.grasp_offset_y,
            "grasp_offset_z": base.grasp_offset_z,
            "ball_radius": base.ball_radius,
            "ball_mass": base.ball_mass,
            "hold_steps": base.hold_steps,
            "min_lift_height": base.min_lift_height,
            "ball_offset_x": base.ball_offset_x,
            "ball_offset_y": base.ball_offset_y,
            "ball_offset_z": base.ball_offset_z,
        },
        "summary": summary,
        "episode_summaries": episode_summaries,
        "false_windows_top": false_windows_top,
        "results": results,
        "boundary": {
            "mujoco_only": True,
            "online_shadow_only": True,
            "controller_actions_unchanged": True,
            "motor_feedback_is_simulated": bool(args.enable_motor_force_feedback),
            "virtual_vision_not_real_camera": True,
            "synthetic_tactile_from_contacts": True,
            "hardware_runtime": False,
            "controller_promoted": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    print(json.dumps(json_ready(summary), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
