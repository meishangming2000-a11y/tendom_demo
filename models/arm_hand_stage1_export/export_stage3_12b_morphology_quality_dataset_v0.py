#!/usr/bin/env python3
"""Export Stage3.12B morphology-quality dense traces.

This MuJoCo-only exporter captures the frozen D-I anchor and selected
diagnostic candidates with the same dense sensor-fusion schema used by
Stage3.11D-D. It is training data for quality/morphology heads, not a
controller promotion.
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

from arm_hand_stage1_task_api import json_ready
import export_stage3_11d_d_dense_sensor_fusion_dataset_v0 as dense
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import run_stage3_12_autonomous_tuning_batch_v0 as autotune
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"

DEFAULT_SELECTED = META / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_DATASET = DATA / "stage3_12b_morphology_quality_dataset_v0.npz"
DEFAULT_JSONL = DATA / "stage3_12b_morphology_quality_dataset_v0.jsonl"
DEFAULT_METADATA = META / "stage3_12b_morphology_quality_dataset_v0.json"
DEFAULT_REPORT = DOCS / "stage3_12b_morphology_quality_dataset_v0_report.md"

STATUS = "stage3_12b_morphology_quality_dataset_v0_mujoco_only"
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


def table_id(table: list[str], value: str) -> int:
    value = str(value)
    if value not in table:
        table.append(value)
    return int(table.index(value))


def summarize_by_candidate(results: list[dict[str, Any]], row_counts: list[int]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_rows: dict[str, list[int]] = defaultdict(list)
    for row, count in zip(results, row_counts):
        name = str(row.get("candidate_name", "unknown"))
        grouped[name].append(row)
        grouped_rows[name].append(int(count))

    out: dict[str, Any] = {}
    for name, rows in grouped.items():
        reasons = Counter(str(row.get("terminal_reason", "unknown")) for row in rows)
        hold = [row.get("hold_morphology", {}) for row in rows]
        out[name] = {
            "episodes": int(len(rows)),
            "rows": int(sum(grouped_rows[name])),
            "success_count": int(sum(1 for row in rows if dense.as_bool(row.get("success")))),
            "contact_gate_success_count": int(sum(1 for row in rows if row.get("contact_gate_success"))),
            "lift_success_count": int(sum(1 for row in rows if row.get("lift_success"))),
            "true_pinch_success_count": int(sum(1 for row in rows if row.get("true_pinch_success"))),
            "release_success_count": int(sum(1 for row in rows if row.get("release_success"))),
            "terminal_reason_counts": dict(reasons),
            "hold_true_two_tip_mean": float(
                np.mean([float(item.get("true_two_tip_pinch_fraction", 0.0)) for item in hold])
            )
            if hold
            else 0.0,
            "hold_wrap_fraction_mean": float(
                np.mean([float(item.get("wrap_frame_fraction", 0.0)) for item in hold])
            )
            if hold
            else 0.0,
            "hold_non_tip_ratio_mean": float(
                np.mean([float(item.get("non_tip_contact_ratio_mean", 0.0)) for item in hold])
            )
            if hold
            else 0.0,
        }
    return out


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.12B Morphology Quality Dataset v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only dense data capture for morphology/quality labels.\n",
        "- Captures virtual vision, synthetic contact/tactile morphology, simulated motor force feedback, proprioception, actions, phase, and outcome labels.\n",
        "- Morphology truth is supervision for simulation training/evaluation, not a real hardware sensor claim.\n",
        "- No controller, demo-gallery, full-action ACT/DP, or hardware-runtime promotion is made here.\n\n",
        "## Outputs\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- JSONL episode summaries: `{payload['jsonl']}`\n",
        f"- Metadata: `{payload['metadata']}`\n\n",
        "## Summary\n\n",
        f"- Candidates: `{payload['candidate_names']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success: `{s['success_count']} / {s['episodes']}` (`{s['success_rate']:.3f}`)\n",
        f"- Dense rows: `{s['rows']}`; mean/min/max rows per episode: "
        f"`{s['row_count_mean']:.1f}` / `{s['row_count_min']}` / `{s['row_count_max']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n\n",
        "## Candidate Breakdown\n\n",
        "| candidate | episodes | rows | success | contact | lift | true pinch | release | hold two-tip | hold non-tip | hold wrap | reasons |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for name, row in payload["candidate_summary"].items():
        lines.append(
            f"| `{name}` | {row['episodes']} | {row['rows']} | "
            f"{row['success_count']} | {row['contact_gate_success_count']} | "
            f"{row['lift_success_count']} | {row['true_pinch_success_count']} | "
            f"{row['release_success_count']} | {row['hold_true_two_tip_mean']:.3f} | "
            f"{row['hold_non_tip_ratio_mean']:.3f} | {row['hold_wrap_fraction_mean']:.3f} | "
            f"`{row['terminal_reason_counts']}` |\n"
        )
    lines.extend(
        [
            "\n## Label Means\n\n",
        ]
    )
    for name, value in s["label_means"].items():
        lines.append(f"- `{name}`: `{value:.4f}`\n")
    lines.extend(
        [
            "\n## Next\n\n",
            "- Train the Stage3.12B morphology-quality head on grasp-evidence phases.\n",
            "- Use the trained head as a shadow quality scorer before any bounded residual intervention.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Stage3.12B morphology-quality dataset.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--episodes-per-candidate", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--candidate", action="append", default=None, help="Candidate name; repeatable.")
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

    candidates = candidate_map()
    requested = args.candidate or DEFAULT_CANDIDATES
    missing = [name for name in requested if name not in candidates]
    if missing:
        raise ValueError(f"Unknown Stage3.12 candidate(s): {missing}")
    selected_candidates = [candidates[name] for name in requested]

    scene = Path(args.scene).resolve()
    phase_table = list(dense.PHASE_NAMES)
    terminal_reason_table: list[str] = []
    candidate_names = [candidate.name for candidate in selected_candidates]

    episode_ids: list[int] = []
    step_ids: list[int] = []
    phase_ids: list[int] = []
    terminal_reason_ids: list[int] = []
    candidate_ids: list[int] = []
    vision_rows: list[np.ndarray] = []
    tactile_rows: list[np.ndarray] = []
    force_rows: list[np.ndarray] = []
    context_rows: list[np.ndarray] = []
    proprio_rows: list[np.ndarray] = []
    action_rows: list[np.ndarray] = []
    obs_rows: list[np.ndarray] = []
    label_rows: list[np.ndarray] = []
    episode_row_starts: list[int] = []
    episode_row_counts: list[int] = []
    episode_success: list[int] = []
    episode_terminal_reason_ids: list[int] = []
    episode_candidate_ids: list[int] = []
    episode_summaries: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    global_episode = 0
    for candidate_idx, candidate in enumerate(selected_candidates):
        run_args = apply_candidate(args, candidate)
        base = robustness.apply_base_offsets(robustness.selected_case_from_json(Path(run_args.selected)), run_args)
        ev_args = robustness.event_args_from(run_args)
        ev_args.capture_dense_sensor_trace = True
        ev_args.dense_trace_sample_every = max(1, int(run_args.dense_trace_sample_every))
        rng = np.random.default_rng(int(args.seed) + candidate_idx * 10000)

        for local_episode in range(max(1, int(args.episodes_per_candidate))):
            case = robustness.perturb_case(base, run_args, rng, local_episode)
            model = mujoco.MjModel.from_xml_path(str(scene))
            row = event.run_event_candidate(model, mujoco, case, ev_args)
            trace = row.get("dense_sensor_trace", [])
            terminal_id = table_id(terminal_reason_table, str(row.get("terminal_reason", "unknown")))
            start = len(obs_rows)

            for frame in trace:
                phase = str(frame.get("label", "unknown"))
                phase_id = table_id(phase_table, phase)
                vision = dense.vision_features(frame, row, case)
                tactile = dense.tactile_features(frame)
                force = dense.force_features(frame, case.candidate.active_finger)
                context = dense.context_features(frame, phase, case)
                qpos = np.asarray(frame.get("qpos", []), dtype=np.float32)
                qvel = np.asarray(frame.get("qvel", []), dtype=np.float32)
                ctrl = np.asarray(frame.get("ctrl", []), dtype=np.float32)
                proprio = np.concatenate([qpos, qvel, ctrl]).astype(np.float32)
                labels = dense.frame_labels(frame, row, phase, run_args, case)
                obs = np.concatenate(
                    [
                        vision,
                        tactile,
                        force,
                        context,
                        proprio,
                        dense.phase_one_hot(phase_id, len(phase_table)),
                    ]
                ).astype(np.float32)

                episode_ids.append(int(global_episode))
                step_ids.append(int(frame.get("dense_step_index", len(step_ids))))
                phase_ids.append(int(phase_id))
                terminal_reason_ids.append(int(terminal_id))
                candidate_ids.append(int(candidate_idx))
                vision_rows.append(vision)
                tactile_rows.append(tactile)
                force_rows.append(force)
                context_rows.append(context)
                proprio_rows.append(proprio)
                action_rows.append(ctrl)
                obs_rows.append(obs)
                label_rows.append(labels)

            count = len(obs_rows) - start
            episode_row_starts.append(start)
            episode_row_counts.append(count)
            episode_success.append(int(dense.as_bool(row.get("success"))))
            episode_terminal_reason_ids.append(terminal_id)
            episode_candidate_ids.append(candidate_idx)
            compact = dense.compact_result(row)
            compact["episode_index"] = int(global_episode)
            compact["local_episode_index"] = int(local_episode)
            compact["candidate_name"] = candidate.name
            compact["candidate_family"] = candidate.family
            compact["candidate_overrides"] = candidate.overrides
            compact["dense_trace_rows"] = int(count)
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
                    "episode_index": int(global_episode),
                    "local_episode_index": int(local_episode),
                    "candidate_name": candidate.name,
                    "status": str(row.get("status")),
                    "success": bool(row.get("success")),
                    "terminal_reason": str(row.get("terminal_reason")),
                    "dense_trace_rows": int(count),
                    "hold_lift_m_max": dense.as_float(row.get("hold_lift_m_max")),
                    "score": dense.as_float(row.get("score")),
                    "randomization": compact["randomization"],
                }
            )
            print(
                f"{global_episode + 1:03d} {candidate.name} {row.get('status')} "
                f"rows={count} lift={dense.as_float(row.get('hold_lift_m_max')):.4f} "
                f"reason={row.get('terminal_reason')}"
            )
            global_episode += 1

    label_array = np.asarray(label_rows, dtype=np.float32)
    summary = dense.summarize_dataset(results, episode_row_counts, label_array)
    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.12B",
        "status": STATUS,
        "scene": str(scene),
        "selected": str(Path(args.selected).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "args": vars(args),
        "candidate_names": candidate_names,
        "candidate_descriptions": {
            candidate.name: {
                "family": candidate.family,
                "description": candidate.description,
                "overrides": candidate.overrides,
            }
            for candidate in selected_candidates
        },
        "feature_names": {
            "vision": dense.VISION_FEATURE_NAMES,
            "tactile": dense.TACTILE_FEATURE_NAMES,
            "force": dense.FORCE_FEATURE_NAMES,
            "context": dense.CONTEXT_FEATURE_NAMES,
            "safety_labels": dense.SAFETY_LABEL_NAMES,
        },
        "phase_names": phase_table,
        "terminal_reason_names": terminal_reason_table,
        "summary": summary,
        "candidate_summary": summarize_by_candidate(results, episode_row_counts),
        "boundary": {
            "mujoco_only": True,
            "virtual_vision_not_real_camera": True,
            "synthetic_tactile_from_contacts": True,
            "motor_feedback_is_simulated": bool(args.enable_motor_force_feedback),
            "morphology_truth_is_supervision_not_runtime_sensor": True,
            "hardware_runtime": False,
            "controller_promoted": False,
        },
    }

    args.dataset.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.dataset,
        obs=np.asarray(obs_rows, dtype=np.float32),
        vision_features=np.asarray(vision_rows, dtype=np.float32),
        tactile_features=np.asarray(tactile_rows, dtype=np.float32),
        force_features=np.asarray(force_rows, dtype=np.float32),
        context_features=np.asarray(context_rows, dtype=np.float32),
        proprio_features=np.asarray(proprio_rows, dtype=np.float32),
        actions=np.asarray(action_rows, dtype=np.float32),
        safety_labels=label_array,
        lift_quality_label=label_array[:, 0].astype(np.float32) if label_array.size else np.zeros((0,), dtype=np.float32),
        future_success_label=label_array[:, 1].astype(np.float32) if label_array.size else np.zeros((0,), dtype=np.float32),
        episode_ids=np.asarray(episode_ids, dtype=np.int32),
        step_ids=np.asarray(step_ids, dtype=np.int32),
        phase_ids=np.asarray(phase_ids, dtype=np.int32),
        terminal_reason_ids=np.asarray(terminal_reason_ids, dtype=np.int32),
        candidate_ids=np.asarray(candidate_ids, dtype=np.int32),
        episode_row_starts=np.asarray(episode_row_starts, dtype=np.int32),
        episode_row_counts=np.asarray(episode_row_counts, dtype=np.int32),
        episode_success=np.asarray(episode_success, dtype=np.int32),
        episode_terminal_reason_ids=np.asarray(episode_terminal_reason_ids, dtype=np.int32),
        episode_candidate_ids=np.asarray(episode_candidate_ids, dtype=np.int32),
        phase_names=np.asarray(phase_table, dtype=np.str_),
        terminal_reason_names=np.asarray(terminal_reason_table, dtype=np.str_),
        candidate_names=np.asarray(candidate_names, dtype=np.str_),
        vision_feature_names=np.asarray(dense.VISION_FEATURE_NAMES, dtype=np.str_),
        tactile_feature_names=np.asarray(dense.TACTILE_FEATURE_NAMES, dtype=np.str_),
        force_feature_names=np.asarray(dense.FORCE_FEATURE_NAMES, dtype=np.str_),
        context_feature_names=np.asarray(dense.CONTEXT_FEATURE_NAMES, dtype=np.str_),
        safety_label_names=np.asarray(dense.SAFETY_LABEL_NAMES, dtype=np.str_),
        metadata_json=np.asarray([json.dumps(json_ready(metadata), ensure_ascii=False)], dtype=np.str_),
    )

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.jsonl.open("w", encoding="utf-8") as f:
        for summary_row in episode_summaries:
            f.write(json.dumps(json_ready(summary_row), ensure_ascii=False) + "\n")

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    payload = {**metadata, "episode_summaries": episode_summaries, "results": results}
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), {**metadata, "summary": summary})
    print(json.dumps(json_ready(summary), indent=2, ensure_ascii=False))
    print(f"Saved dataset: {args.dataset}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
