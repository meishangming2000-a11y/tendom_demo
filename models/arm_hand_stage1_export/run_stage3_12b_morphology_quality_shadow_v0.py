#!/usr/bin/env python3
"""Run Stage3.12B morphology-quality head in fresh MuJoCo shadow mode.

The model scores dense trace frames from new randomized D-I/lift candidates.
Controller actions are unchanged. This is a shadow evaluator before any
bounded residual teacher is considered.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
import export_stage3_11d_d_dense_sensor_fusion_dataset_v0 as dense
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import run_stage3_12_autonomous_tuning_batch_v0 as autotune
import train_stage3_11d_b_event_contact_gated_refine_v0 as event
from train_stage3_11d_d_lift_quality_head_v0 import LiftQualityHead
from train_stage3_12b_morphology_quality_head_v0 import GRASP_EVIDENCE_PHASES, TARGET_NAMES


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_SELECTED = META / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_12b_morphology_quality_head_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_12b_morphology_quality_shadow_v0_report.md"
DEFAULT_METADATA = META / "stage3_12b_morphology_quality_shadow_v0.json"

STATUS = "stage3_12b_morphology_quality_shadow_v0_mujoco_only_not_control_promoted"
DEFAULT_CANDIDATES = ["baseline_di", "lift_ls460"]


def candidate_map() -> dict[str, autotune.Candidate]:
    return {candidate.name: candidate for candidate in autotune.candidate_grid()}


def fill_defaults(args: argparse.Namespace) -> argparse.Namespace:
    return dense.fill_from_robustness_defaults(args)


def apply_candidate(args: argparse.Namespace, candidate: autotune.Candidate) -> argparse.Namespace:
    out = argparse.Namespace(**vars(args))
    for key, value in candidate.overrides.items():
        setattr(out, key, value)
    return fill_defaults(out)


def label_idx(name: str) -> int:
    return int(dense.SAFETY_LABEL_NAMES.index(name))


def tactile_idx(name: str) -> int:
    return int(dense.TACTILE_FEATURE_NAMES.index(name))


def frame_targets(frame: dict[str, Any], row: dict[str, Any], phase: str, args: argparse.Namespace, case: event.RefineCase) -> np.ndarray:
    labels = dense.frame_labels(frame, row, phase, args, case)
    tactile = dense.tactile_features(frame)
    good_two_tip = bool(labels[label_idx("good_two_tip_now")] >= 0.5)
    wrap = bool(labels[label_idx("wrap_now")] >= 0.5)
    floor = bool(labels[label_idx("floor_contact_now")] >= 0.5)
    penetration = bool(labels[label_idx("penetration_risk_now")] >= 0.5)
    lift_quality = bool(labels[label_idx("lift_quality_now")] >= 0.5)
    future_success = bool(labels[label_idx("future_success")] >= 0.5)
    non_tip = float(tactile[tactile_idx("non_tip_contact_ratio")])
    low_non_tip = non_tip <= float(args.max_non_tip_ratio)
    morphology_clean = bool(good_two_tip and low_non_tip and not wrap and not floor and not penetration)
    return np.asarray(
        [
            float(morphology_clean),
            float(good_two_tip),
            float(low_non_tip),
            float(wrap),
            float(floor),
            float(penetration),
            float(lift_quality),
            float(future_success),
        ],
        dtype=np.float32,
    )


def phase_id(phase_names: list[str], phase: str) -> int:
    try:
        return int(phase_names.index(str(phase)))
    except ValueError:
        return -1


def frame_feature(
    frame: dict[str, Any],
    row: dict[str, Any],
    case: event.RefineCase,
    phase: str,
    phase_names: list[str],
) -> np.ndarray:
    pid = phase_id(phase_names, phase)
    qpos = np.asarray(frame.get("qpos", []), dtype=np.float32)
    qvel = np.asarray(frame.get("qvel", []), dtype=np.float32)
    ctrl = np.asarray(frame.get("ctrl", []), dtype=np.float32)
    proprio = np.concatenate([qpos, qvel, ctrl]).astype(np.float32)
    return np.concatenate(
        [
            dense.vision_features(frame, row, case),
            dense.tactile_features(frame),
            dense.force_features(frame, case.candidate.active_finger),
            dense.context_features(frame, phase, case),
            proprio,
            dense.phase_one_hot(pid, len(phase_names)),
        ]
    ).astype(np.float32)


def load_shadow(checkpoint: Path) -> dict[str, Any]:
    payload = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
    target_names = [str(name) for name in payload["target_names"]]
    if target_names != TARGET_NAMES:
        raise ValueError(f"Unexpected target names: {target_names}")
    model = LiftQualityHead(
        int(payload["input_dim"]),
        len(target_names),
        int(payload["hidden_dim"]),
        float(payload["dropout"]),
    )
    model.load_state_dict(payload["model_state_dict"])
    model.eval()
    dataset_metadata = payload.get("dataset_metadata") or {}
    return {
        "payload": payload,
        "model": model,
        "target_names": target_names,
        "phase_names": [str(name) for name in dataset_metadata.get("phase_names", dense.PHASE_NAMES)],
        "obs_mean": np.asarray(payload["obs_mean"], dtype=np.float32),
        "obs_std": np.maximum(np.asarray(payload["obs_std"], dtype=np.float32), 1e-6),
        "input_dim": int(payload["input_dim"]),
    }


def sigmoid_np(logits: np.ndarray) -> np.ndarray:
    return (1.0 / (1.0 + np.exp(-np.clip(logits, -60.0, 60.0)))).astype(np.float32)


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


def update_counts(counts: dict[str, int], pred: bool, truth: bool) -> None:
    if pred and truth:
        counts["tp"] += 1
    elif pred and not truth:
        counts["fp"] += 1
    elif not pred and truth:
        counts["fn"] += 1
    else:
        counts["tn"] += 1


def summarize_predictions(records: list[dict[str, Any]], target_names: list[str]) -> dict[str, Any]:
    counts = {name: {"tp": 0, "tn": 0, "fp": 0, "fn": 0} for name in target_names}
    positives = Counter()
    for record in records:
        truth = np.asarray(record["truth"], dtype=np.float32) >= 0.5
        pred = np.asarray(record["pred"], dtype=np.float32)
        for idx, name in enumerate(target_names):
            positives[name] += int(truth[idx])
            update_counts(counts[name], bool(pred[idx]), bool(truth[idx]))
    return {
        name: metric_from_counts(counts[name], int(positives[name]), len(records))
        for name in target_names
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.12B Morphology Quality Shadow v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- Fresh MuJoCo-only shadow evaluation of the Stage3.12B morphology-quality head.\n",
        "- Controller actions are unchanged; model predictions are logged only.\n",
        "- No bounded residual, demo-gallery, full-action ACT/DP, or hardware-runtime promotion is made here.\n\n",
        "## Summary\n\n",
        f"- Candidates: `{payload['candidate_names']}`\n",
        f"- Trials per candidate: `{payload['args']['trials_per_candidate']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Shadow evidence frames: `{s['shadow_frames']}`\n\n",
        "## Shadow Metrics\n\n",
        "| label | accuracy | precision | recall | F1 | positive fraction | fp | fn |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for name, row in s["metrics"].items():
        lines.append(
            f"| `{name}` | {row['accuracy']:.4f} | {row['precision']:.4f} | {row['recall']:.4f} | "
            f"{row['f1']:.4f} | {row['positive_fraction']:.4f} | {row['fp']} | {row['fn']} |\n"
        )
    lines.extend(
        [
            "\n## Candidate Slices\n\n",
            "| candidate | episodes | success | morphology-clean F1 | future-success F1 | reasons |\n",
            "|---|---:|---:|---:|---:|---|\n",
        ]
    )
    for name, row in payload["candidate_summary"].items():
        lines.append(
            f"| `{name}` | {row['episodes']} | {row['success_count']} | "
            f"{row['metrics']['morphology_clean_now']['f1']:.4f} | "
            f"{row['metrics']['future_success']['f1']:.4f} | `{row['terminal_reason_counts']}` |\n"
        )
    lines.extend(
        [
            "\n## Next\n\n",
            "- Use high-confidence false/low morphology windows to design a bounded residual teacher.\n",
            "- Do not alter control until the residual branch beats frozen D-I on the same multiseed gate without morphology regression.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage3.12B morphology-quality shadow evaluator.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--trials-per-candidate", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--candidate", action="append", default=None)
    parser.add_argument("--max-non-tip-ratio", type=float, default=0.45)
    parser.add_argument("--dense-trace-sample-every", type=int, default=1)
    parser.add_argument("--object-pose-noise-xy-m", type=float, default=0.003)
    parser.add_argument("--grasp-target-noise-xy-m", type=float, default=0.002)
    parser.add_argument("--grasp-target-noise-z-m", type=float, default=0.001)
    parser.add_argument("--radius-jitter-m", type=float, default=0.001)
    parser.add_argument("--mass-jitter-kg", type=float, default=0.002)
    parser.add_argument("--friction-scale-jitter", type=float, default=0.08)
    parser.add_argument("--base-grasp-offset-x-delta", type=float, default=0.0)
    parser.add_argument("--base-grasp-offset-y-delta", type=float, default=0.0)
    parser.add_argument("--base-grasp-offset-z-delta", type=float, default=0.0)
    parser.add_argument("--base-ball-offset-x-delta", type=float, default=0.0)
    parser.add_argument("--base-ball-offset-y-delta", type=float, default=0.0)
    parser.add_argument("--min-lift-steps-before-hold", type=int, default=300)
    parser.add_argument("--hold-release-required-samples", type=int, default=8)
    parser.add_argument("--demo-lift-goal", type=float, default=0.11)
    parser.add_argument("--morphology-sample-every", type=int, default=5)
    parser.add_argument("--enable-motor-force-feedback", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
    args = fill_defaults(build_parser().parse_args())
    import mujoco

    shadow = load_shadow(Path(args.checkpoint))
    candidates = candidate_map()
    requested = args.candidate or DEFAULT_CANDIDATES
    missing = [name for name in requested if name not in candidates]
    if missing:
        raise ValueError(f"Unknown Stage3.12 candidate(s): {missing}")
    selected_candidates = [candidates[name] for name in requested]
    scene = Path(args.scene).resolve()
    records: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    candidate_records: dict[str, list[dict[str, Any]]] = {candidate.name: [] for candidate in selected_candidates}

    for candidate_idx, candidate in enumerate(selected_candidates):
        run_args = apply_candidate(args, candidate)
        base = robustness.apply_base_offsets(robustness.selected_case_from_json(Path(run_args.selected)), run_args)
        ev_args = robustness.event_args_from(run_args)
        ev_args.capture_dense_sensor_trace = True
        ev_args.dense_trace_sample_every = max(1, int(run_args.dense_trace_sample_every))
        rng = np.random.default_rng(int(args.seed) + candidate_idx * 10000)
        for trial in range(max(1, int(args.trials_per_candidate))):
            case = robustness.perturb_case(base, run_args, rng, trial)
            model = mujoco.MjModel.from_xml_path(str(scene))
            row = event.run_event_candidate(model, mujoco, case, ev_args)
            trace = row.get("dense_sensor_trace", [])
            features: list[np.ndarray] = []
            local_records: list[dict[str, Any]] = []
            for frame in trace:
                phase = str(frame.get("label", "unknown"))
                if phase not in GRASP_EVIDENCE_PHASES:
                    continue
                obs = frame_feature(frame, row, case, phase, shadow["phase_names"])
                if obs.shape[0] != int(shadow["input_dim"]):
                    raise ValueError(f"Feature dim mismatch: got {obs.shape[0]}, expected {shadow['input_dim']}")
                features.append(obs)
                local_records.append(
                    {
                        "candidate_name": candidate.name,
                        "trial_index": int(trial),
                        "phase": phase,
                        "truth": frame_targets(frame, row, phase, run_args, case),
                    }
                )
            if features:
                x = np.asarray(features, dtype=np.float32)
                x_norm = ((x - shadow["obs_mean"].reshape(1, -1)) / shadow["obs_std"].reshape(1, -1)).astype(np.float32)
                with torch.no_grad():
                    probs = sigmoid_np(shadow["model"](torch.from_numpy(x_norm)).cpu().numpy())
                preds = probs >= 0.5
                for idx, record in enumerate(local_records):
                    record["prob"] = probs[idx].astype(np.float32)
                    record["pred"] = preds[idx].astype(bool)
                    records.append(record)
                    candidate_records[candidate.name].append(record)
            episode_rows.append(
                {
                    "candidate_name": candidate.name,
                    "trial_index": int(trial),
                    "status": str(row.get("status")),
                    "success": bool(row.get("success")),
                    "terminal_reason": str(row.get("terminal_reason")),
                    "shadow_frames": int(len(local_records)),
                    "hold_lift_m_max": dense.as_float(row.get("hold_lift_m_max")),
                }
            )
            print(
                f"{candidate.name} {trial + 1:02d}/{args.trials_per_candidate:02d} "
                f"{row.get('status')} frames={len(local_records)} reason={row.get('terminal_reason')}"
            )

    overall_metrics = summarize_predictions(records, shadow["target_names"])
    terminal_counts = Counter(str(row["terminal_reason"]) for row in episode_rows)
    candidate_summary: dict[str, Any] = {}
    for candidate in selected_candidates:
        rows = [row for row in episode_rows if row["candidate_name"] == candidate.name]
        candidate_summary[candidate.name] = {
            "episodes": int(len(rows)),
            "success_count": int(sum(1 for row in rows if row["success"])),
            "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
            "shadow_frames": int(len(candidate_records[candidate.name])),
            "metrics": summarize_predictions(candidate_records[candidate.name], shadow["target_names"]),
        }
    summary = {
        "episodes": int(len(episode_rows)),
        "success_count": int(sum(1 for row in episode_rows if row["success"])),
        "terminal_reason_counts": dict(terminal_counts),
        "shadow_frames": int(len(records)),
        "metrics": overall_metrics,
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.12B",
        "status": STATUS,
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "report": str(Path(args.report).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "args": vars(args),
        "candidate_names": [candidate.name for candidate in selected_candidates],
        "summary": summary,
        "candidate_summary": candidate_summary,
        "episodes": episode_rows,
        "boundary": {
            "mujoco_only": True,
            "shadow_only": True,
            "controller_actions_changed": False,
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
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
