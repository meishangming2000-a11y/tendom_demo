#!/usr/bin/env python3
"""Export Stage3.11D-D dense sensor-fusion traces from the D-C pinch center.

This is a MuJoCo-only data capture step. It records virtual vision, synthetic
contact/tactile morphology, simulated motor force feedback, proprioception, and
scripted controls from the event-gated true-pinch controller. It does not train
or promote a closed-loop neural controller.
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

from arm_hand_stage1_task_api import json_ready
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"

DEFAULT_SELECTED = META / "stage3_11d_c_geometry_force_refine_selected_v0.json"
DEFAULT_DATASET = DATA / "stage3_11d_d_dense_sensor_fusion_dataset_v0.npz"
DEFAULT_JSONL = DATA / "stage3_11d_d_dense_sensor_fusion_dataset_v0.jsonl"
DEFAULT_METADATA = META / "stage3_11d_d_dense_sensor_fusion_dataset_v0.json"
DEFAULT_REPORT = DOCS / "stage3_11d_d_dense_sensor_fusion_dataset_v0_report.md"

STATUS = "stage3_11d_d_dense_sensor_fusion_dataset_v0_mujoco_only"

PHASE_NAMES = [
    "approach",
    "preshape",
    "pinch_close",
    "contact_gate",
    "post_contact_settle",
    "preload",
    "slow_lift",
    "hold",
    "release_open",
    "release_settle",
    "final",
]

GRASP_EVIDENCE_PHASES = {"contact_gate", "post_contact_settle", "preload", "slow_lift", "hold"}

VISION_FEATURE_NAMES = [
    "ball_rel_x_m",
    "ball_rel_y_m",
    "ball_rel_z_m",
    "lift_m",
    "lift_to_goal_ratio",
    "ball_abs_z_m",
    "virtual_object_confidence",
    "virtual_mask_visibility",
    "virtual_depth_noise_m",
]

TACTILE_FEATURE_NAMES = [
    "hand_contacts",
    "floor_contacts",
    "tip_contact_ratio",
    "non_tip_contact_ratio",
    "true_two_tip_pinch",
    "wrap_or_support",
    "support_region_count",
    "tip_region_count",
    "max_penetration_m",
]

FORCE_FEATURE_NAMES = [
    "max_abs_iq_a",
    "max_hand_abs_iq_a",
    "max_hand_tendon_tension_n",
    "pair_total_tendon_tension_n",
    "pair_balance_ratio",
    "pair_max_abs_iq_a",
    "pair_sum_abs_iq_a",
    "pair_saturated_actuator_count",
    "pair_tension_delta_abs_n",
    "thumb_sum_tendon_tension_n",
    "thumb_max_tendon_tension_n",
    "thumb_max_abs_iq_a",
    "active_sum_tendon_tension_n",
    "active_max_tendon_tension_n",
    "active_max_abs_iq_a",
]

CONTEXT_FEATURE_NAMES = [
    "phase_progress",
    "time_s",
    "min_lift_height_m",
    "phase_is_grasp_evidence",
]

SAFETY_LABEL_NAMES = [
    "lift_quality_now",
    "future_success",
    "adjust_needed_now",
    "good_two_tip_now",
    "wrap_now",
    "floor_contact_now",
    "low_force_now",
    "force_imbalance_now",
    "force_saturation_now",
    "penetration_risk_now",
    "hold_safe_now",
    "release_phase_now",
]


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def table_id(table: list[str], value: str) -> int:
    value = str(value)
    if value not in table:
        table.append(value)
    return int(table.index(value))


def fill_from_robustness_defaults(args: argparse.Namespace) -> argparse.Namespace:
    for defaults in (
        vars(event.build_parser().parse_args([])),
        vars(robustness.build_parser().parse_args([])),
    ):
        for key, value in defaults.items():
            if not hasattr(args, key):
                setattr(args, key, value)
    return args


def phase_one_hot(phase_id: int, phase_count: int) -> np.ndarray:
    out = np.zeros((int(phase_count),), dtype=np.float32)
    if 0 <= int(phase_id) < int(phase_count):
        out[int(phase_id)] = 1.0
    return out


def feedback_pair(frame: dict[str, Any]) -> dict[str, Any]:
    feedback = frame.get("motor_force_feedback", {})
    return feedback.get("active_pair", {}) if isinstance(feedback, dict) else {}


def force_features(frame: dict[str, Any], active_finger: str) -> np.ndarray:
    feedback = frame.get("motor_force_feedback", {})
    if not isinstance(feedback, dict):
        feedback = {}
    pair = feedback.get("active_pair", {})
    if not isinstance(pair, dict):
        pair = {}
    per_group = pair.get("per_group", {})
    if not isinstance(per_group, dict):
        per_group = {}
    thumb = per_group.get("thumb", {})
    active = per_group.get(str(active_finger), {})
    if not isinstance(thumb, dict):
        thumb = {}
    if not isinstance(active, dict):
        active = {}
    values = [
        as_float(feedback.get("max_abs_iq_a")),
        as_float(feedback.get("max_hand_abs_iq_a")),
        as_float(feedback.get("max_hand_tendon_tension_n")),
        as_float(pair.get("total_tendon_tension_n")),
        as_float(pair.get("balance_ratio")),
        as_float(pair.get("max_abs_iq_a")),
        as_float(pair.get("sum_abs_iq_a")),
        as_float(pair.get("saturated_actuator_count")),
        as_float(pair.get("tension_delta_abs_n")),
        as_float(thumb.get("sum_tendon_tension_n")),
        as_float(thumb.get("max_tendon_tension_n")),
        as_float(thumb.get("max_abs_iq_a")),
        as_float(active.get("sum_tendon_tension_n")),
        as_float(active.get("max_tendon_tension_n")),
        as_float(active.get("max_abs_iq_a")),
    ]
    return np.asarray(values, dtype=np.float32)


def tactile_features(frame: dict[str, Any]) -> np.ndarray:
    morph = frame.get("morphology", {})
    if not isinstance(morph, dict):
        morph = {}
    support = morph.get("support_regions", [])
    tip_regions = morph.get("tip_regions", [])
    values = [
        as_float(morph.get("hand_contacts")),
        as_float(morph.get("floor_contacts")),
        as_float(morph.get("tip_contact_ratio")),
        as_float(morph.get("non_tip_contact_ratio")),
        float(as_bool(morph.get("true_two_tip_pinch"))),
        float(as_bool(morph.get("wrap_or_support"))),
        float(len(support) if isinstance(support, list) else 0),
        float(len(tip_regions) if isinstance(tip_regions, list) else 0),
        as_float(frame.get("max_penetration_m")),
    ]
    return np.asarray(values, dtype=np.float32)


def vision_features(frame: dict[str, Any], result: dict[str, Any], case: event.RefineCase) -> np.ndarray:
    ball = np.asarray(frame.get("ball_position", [0.0, 0.0, 0.0]), dtype=np.float32)
    initial = np.asarray(result.get("initial_ball", [0.0, 0.0, 0.0]), dtype=np.float32)
    rel = ball - initial
    lift = as_float(frame.get("lift_m"))
    goal = max(float(case.min_lift_height), 1e-6)
    xy_mag = float(np.linalg.norm(rel[:2]))
    virtual_conf = float(np.clip(1.0 - 2.0 * xy_mag, 0.80, 1.0))
    virtual_visibility = float(np.clip(1.0 - 0.5 * max(0.0, -lift), 0.80, 1.0))
    values = [
        float(rel[0]),
        float(rel[1]),
        float(rel[2]),
        float(lift),
        float(lift / goal),
        float(ball[2]),
        virtual_conf,
        virtual_visibility,
        0.0,
    ]
    return np.asarray(values, dtype=np.float32)


def context_features(frame: dict[str, Any], phase: str, case: event.RefineCase) -> np.ndarray:
    values = [
        as_float(frame.get("phase_progress")),
        as_float(frame.get("time_s")),
        float(case.min_lift_height),
        float(phase in GRASP_EVIDENCE_PHASES),
    ]
    return np.asarray(values, dtype=np.float32)


def frame_labels(
    frame: dict[str, Any],
    result: dict[str, Any],
    phase: str,
    args: argparse.Namespace,
    case: event.RefineCase,
) -> np.ndarray:
    morph = frame.get("morphology", {})
    if not isinstance(morph, dict):
        morph = {}
    pair = feedback_pair(frame)
    force_configured = as_bool(pair.get("configured"))
    min_tension = (
        float(args.force_feedback_min_hold_pair_tension_n)
        if phase == "hold"
        else float(args.force_feedback_min_slow_lift_pair_tension_n)
    )
    pair_tension = as_float(pair.get("total_tendon_tension_n"))
    pair_balance = as_float(pair.get("balance_ratio"))
    pair_iq = as_float(pair.get("max_abs_iq_a"))
    saturated = int(as_float(pair.get("saturated_actuator_count")))
    low_force = bool(force_configured and pair_tension < min_tension)
    force_imbalance = bool(force_configured and pair_balance < float(args.force_feedback_min_pair_balance))
    force_saturation = bool(force_configured and (pair_iq > float(args.force_feedback_max_pair_iq_a) or saturated > 0))
    penetration_risk = bool(as_float(frame.get("max_penetration_m")) > float(args.max_penetration_m))
    true_two_tip = as_bool(morph.get("true_two_tip_pinch"))
    wrap = as_bool(morph.get("wrap_or_support"))
    floor_contact = int(as_float(morph.get("floor_contacts"))) > 0
    force_ok = bool(force_configured and not low_force and not force_imbalance and not force_saturation)
    morphology_ok = bool(true_two_tip and not wrap and not floor_contact and not penetration_risk)
    grasp_phase = phase in GRASP_EVIDENCE_PHASES
    lift_quality_now = bool(grasp_phase and morphology_ok and force_ok)
    hold_safe_now = bool(phase == "hold" and lift_quality_now and as_float(frame.get("lift_m")) >= float(case.min_lift_height))
    adjust_needed = bool(grasp_phase and not lift_quality_now)
    release_phase = phase in {"release_open", "release_settle", "final"}
    values = [
        float(lift_quality_now),
        float(as_bool(result.get("success"))),
        float(adjust_needed),
        float(true_two_tip),
        float(wrap),
        float(floor_contact),
        float(low_force),
        float(force_imbalance),
        float(force_saturation),
        float(penetration_risk),
        float(hold_safe_now),
        float(release_phase),
    ]
    return np.asarray(values, dtype=np.float32)


def compact_result(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key
        not in {
            "dense_sensor_trace",
        }
    }


def summarize_dataset(results: list[dict[str, Any]], row_counts: list[int], labels: np.ndarray) -> dict[str, Any]:
    terminal_counts = Counter(str(row.get("terminal_reason", "unknown")) for row in results)
    success_count = int(sum(1 for row in results if as_bool(row.get("success"))))
    if labels.size:
        label_means = {name: float(np.mean(labels[:, idx])) for idx, name in enumerate(SAFETY_LABEL_NAMES)}
    else:
        label_means = {name: 0.0 for name in SAFETY_LABEL_NAMES}
    return {
        "episodes": int(len(results)),
        "success_count": success_count,
        "success_rate": float(success_count / max(1, len(results))),
        "rows": int(sum(row_counts)),
        "row_count_min": int(min(row_counts) if row_counts else 0),
        "row_count_max": int(max(row_counts) if row_counts else 0),
        "row_count_mean": float(np.mean(row_counts) if row_counts else 0.0),
        "terminal_reason_counts": dict(terminal_counts),
        "label_means": label_means,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.11D-D Dense Sensor Fusion Dataset v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only dense data capture from the Stage3.11D-C selected true-pinch center.\n",
        "- Virtual vision, synthetic contact/tactile morphology, simulated motor force feedback, and proprioception are exported as training signals.\n",
        "- Morphology truth is exported as training/evaluation supervision, not as future hardware runtime truth.\n",
        "- No full-action ACT/DP or demo-gallery promotion is made here.\n\n",
        "## Outputs\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- JSONL episode summaries: `{payload['jsonl']}`\n",
        f"- Metadata: `{payload['metadata']}`\n\n",
        "## Summary\n\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success: `{s['success_count']} / {s['episodes']}` (`{s['success_rate']:.3f}`)\n",
        f"- Dense rows: `{s['rows']}`; mean/min/max rows per episode: "
        f"`{s['row_count_mean']:.1f}` / `{s['row_count_min']}` / `{s['row_count_max']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n\n",
        "## Sensor Blocks\n\n",
        f"- Vision features: `{VISION_FEATURE_NAMES}`\n",
        f"- Tactile/contact features: `{TACTILE_FEATURE_NAMES}`\n",
        f"- Simulated motor force features: `{FORCE_FEATURE_NAMES}`\n",
        f"- Context features: `{CONTEXT_FEATURE_NAMES}`\n",
        f"- Safety labels: `{SAFETY_LABEL_NAMES}`\n\n",
        "## Label Means\n\n",
    ]
    for name, value in s["label_means"].items():
        lines.append(f"- `{name}`: `{value:.4f}`\n")
    lines.extend(
        [
            "\n## Next\n\n",
            "- Train the Stage3.11D-D lift-quality head on grasp-evidence phases.\n",
            "- Use ablations to compare force/tactile/vision/proprio blocks before adding residual micro-adjustment.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Stage3.11D-D dense sensor fusion dataset.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260612)
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
    args = fill_from_robustness_defaults(build_parser().parse_args())
    import mujoco

    scene = Path(args.scene).resolve()
    base = robustness.apply_base_offsets(robustness.selected_case_from_json(Path(args.selected)), args)
    rng = np.random.default_rng(int(args.seed))
    ev_args = robustness.event_args_from(args)
    ev_args.capture_dense_sensor_trace = True
    ev_args.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))

    phase_table = list(PHASE_NAMES)
    terminal_reason_table: list[str] = []
    episode_ids: list[int] = []
    step_ids: list[int] = []
    phase_ids: list[int] = []
    terminal_reason_ids: list[int] = []
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
    episode_summaries: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    for episode_idx in range(max(1, int(args.episodes))):
        case = robustness.perturb_case(base, args, rng, episode_idx)
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        trace = row.get("dense_sensor_trace", [])
        terminal_id = table_id(terminal_reason_table, str(row.get("terminal_reason", "unknown")))
        start = len(obs_rows)
        for frame in trace:
            phase = str(frame.get("label", "unknown"))
            phase_id = table_id(phase_table, phase)
            vision = vision_features(frame, row, case)
            tactile = tactile_features(frame)
            force = force_features(frame, case.candidate.active_finger)
            context = context_features(frame, phase, case)
            qpos = np.asarray(frame.get("qpos", []), dtype=np.float32)
            qvel = np.asarray(frame.get("qvel", []), dtype=np.float32)
            ctrl = np.asarray(frame.get("ctrl", []), dtype=np.float32)
            proprio = np.concatenate([qpos, qvel, ctrl]).astype(np.float32)
            labels = frame_labels(frame, row, phase, args, case)
            obs = np.concatenate(
                [
                    vision,
                    tactile,
                    force,
                    context,
                    proprio,
                    phase_one_hot(phase_id, len(phase_table)),
                ]
            ).astype(np.float32)

            episode_ids.append(int(episode_idx))
            step_ids.append(int(frame.get("dense_step_index", len(step_ids))))
            phase_ids.append(int(phase_id))
            terminal_reason_ids.append(int(terminal_id))
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
        episode_success.append(int(as_bool(row.get("success"))))
        episode_terminal_reason_ids.append(terminal_id)
        compact = compact_result(row)
        compact["episode_index"] = int(episode_idx)
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
                "episode_index": int(episode_idx),
                "status": str(row.get("status")),
                "success": bool(row.get("success")),
                "terminal_reason": str(row.get("terminal_reason")),
                "dense_trace_rows": int(count),
                "hold_lift_m_max": as_float(row.get("hold_lift_m_max")),
                "score": as_float(row.get("score")),
                "randomization": compact["randomization"],
            }
        )
        print(
            f"{episode_idx + 1:03d}/{args.episodes:03d} {row.get('status')} "
            f"rows={count} lift={as_float(row.get('hold_lift_m_max')):.4f} "
            f"reason={row.get('terminal_reason')}"
        )

    label_array = np.asarray(label_rows, dtype=np.float32)
    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-D",
        "status": STATUS,
        "scene": str(scene),
        "selected": str(Path(args.selected).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "args": vars(args),
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
        "feature_names": {
            "vision": VISION_FEATURE_NAMES,
            "tactile": TACTILE_FEATURE_NAMES,
            "force": FORCE_FEATURE_NAMES,
            "context": CONTEXT_FEATURE_NAMES,
            "safety_labels": SAFETY_LABEL_NAMES,
        },
        "phase_names": phase_table,
        "terminal_reason_names": terminal_reason_table,
        "summary": summarize_dataset(results, episode_row_counts, label_array),
        "boundary": {
            "mujoco_only": True,
            "virtual_vision_not_real_camera": True,
            "synthetic_tactile_from_contacts": True,
            "motor_feedback_is_simulated": True,
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
        episode_row_starts=np.asarray(episode_row_starts, dtype=np.int32),
        episode_row_counts=np.asarray(episode_row_counts, dtype=np.int32),
        episode_success=np.asarray(episode_success, dtype=np.int32),
        episode_terminal_reason_ids=np.asarray(episode_terminal_reason_ids, dtype=np.int32),
        phase_names=np.asarray(phase_table, dtype=np.str_),
        terminal_reason_names=np.asarray(terminal_reason_table, dtype=np.str_),
        vision_feature_names=np.asarray(VISION_FEATURE_NAMES, dtype=np.str_),
        tactile_feature_names=np.asarray(TACTILE_FEATURE_NAMES, dtype=np.str_),
        force_feature_names=np.asarray(FORCE_FEATURE_NAMES, dtype=np.str_),
        context_feature_names=np.asarray(CONTEXT_FEATURE_NAMES, dtype=np.str_),
        safety_label_names=np.asarray(SAFETY_LABEL_NAMES, dtype=np.str_),
        metadata_json=np.asarray([json.dumps(json_ready(metadata), ensure_ascii=False)], dtype=np.str_),
    )

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.jsonl.open("w", encoding="utf-8") as f:
        for summary in episode_summaries:
            f.write(json.dumps(json_ready(summary), ensure_ascii=False) + "\n")

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    payload = {**metadata, "episode_summaries": episode_summaries, "results": results}
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), {**metadata, "summary": metadata["summary"]})
    print(json.dumps(json_ready(metadata["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved dataset: {args.dataset}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
