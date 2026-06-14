#!/usr/bin/env python3
"""Export Stage3.11C trace-frame safety labels from Stage3.10C/3.11B metadata.

This is a MuJoCo-only data engineering step. It does not train a policy, change
control actions, promote full-action ACT/DP, or connect hardware. The exporter
turns evaluator trace samples into frame-level labels for noisy vision,
occlusion, tactile handoff, repair, recovery, and physical risk.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from stage3_sensor_aware_gentle_grasp_hold_task_api import Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"
META = ROOT / "metadata"

DEFAULT_CLEAN_SOURCE = META / "stage3_10c_safety_act_cvae_policy_v0_closed_loop_cycle50.json"
DEFAULT_SHADOW_AGGREGATE = META / "stage3_11b_online_safety_head_shadow_v0.json"
DEFAULT_DATASET = DATA / "stage3_11c_frame_safety_labels_v0.npz"
DEFAULT_JSONL = DATA / "stage3_11c_frame_safety_labels_v0.jsonl"
DEFAULT_METADATA = META / "stage3_11c_frame_safety_labels_v0.json"
DEFAULT_REPORT = DOCS / "stage3_11c_frame_safety_labels_v0_closeout.md"

LABEL_NAMES = [
    "vision_degraded",
    "vision_freeze",
    "initial_quality_adapter_required",
    "final_occlusion_aware_required",
    "tactile_handoff",
    "repair_configured",
    "repair_active",
    "recovery_active",
    "safety_intervention_active",
    "risk_slip_high",
    "risk_crush_high",
    "risk_penetration_high",
    "physical_risk_any",
    "hold_safe",
    "failure_or_blocked",
    "floor_or_hold_failure",
    "risk_any",
]

LABEL_DEFINITIONS = {
    "vision_degraded": "Vision is low-quality, occluded, stressed, or failed for the current early/final phase window.",
    "vision_freeze": "Vision should be treated as frozen/adapter-selected instead of trusted as a fresh clean observation.",
    "initial_quality_adapter_required": "Initial vision was accepted but needed quality adaptation; initial hard failure is not counted here.",
    "final_occlusion_aware_required": "Final verification depends on occlusion-aware or non-strict final vision handling.",
    "tactile_handoff": "Final or late-phase evidence should rely on tactile hold/contact rather than strict vision alone.",
    "repair_configured": "A pinch repair mode is configured for this episode, regardless of whether it actually fired.",
    "repair_active": "A sampled trace frame actually executed pinch repair.",
    "recovery_active": "A sampled trace frame actually executed full-hand recovery.",
    "safety_intervention_active": "Repair, recovery, or tactile handoff is active/relevant at this trace frame.",
    "risk_slip_high": "Sampled slip is above the Stage3 success slip threshold.",
    "risk_crush_high": "Sampled crush risk is above the Stage3 success crush threshold.",
    "risk_penetration_high": "Sampled penetration is above the Stage3 success penetration threshold.",
    "physical_risk_any": "Any sampled physical risk primitive is high.",
    "hold_safe": "Episode-level safety head or outcome says hold was safe, applied to hold/late successful frames.",
    "failure_or_blocked": "Episode failed or was intentionally blocked/rejected.",
    "floor_or_hold_failure": "Episode-level failure includes floor/hold failure or equivalent failed hold boundary.",
    "risk_any": "Union of physical risk, failure/blocker, unsafe shadow, repair/recovery, or tactile-handoff state.",
}

INITIAL_PHASES = {
    "approach",
    "preshape",
    "gentle_close_fingers",
    "gentle_close_thumb",
    "pinch_close",
    "contact_settle",
    "initial_vision_failed",
}
FINAL_PHASES = {"slow_lift", "hold", "final_verification", "initial_vision_failed"}
REPAIR_PHASES = {"pinch_close", "contact_settle", "slow_lift", "hold"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


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


def source_bucket_from_case(case_id: str, suite: str) -> str:
    text = f"{suite}:{case_id}".lower()
    if "clean" in text or "cycle50" in text:
        return "clean"
    if "combinedhard" in text:
        return "combined_hard"
    if "depthnoise" in text:
        return "depth_noise"
    if "falseblob" in text:
        return "false_positive"
    if "maskdrop" in text:
        return "mask_dropout"
    if "occluder" in text or "occlusion" in text:
        return "occlusion"
    if "pose008" in text or "pose010" in text or "pose005" in text:
        return "pose_noise"
    return "unknown"


def shadow_dict(row: dict[str, Any]) -> dict[str, Any]:
    shadow = row.get("safety_head_shadow", {})
    return shadow if isinstance(shadow, dict) else {}


def shadow_true(row: dict[str, Any], name: str, default: bool = False) -> bool:
    shadow = shadow_dict(row)
    labels = shadow.get("true_labels", {})
    if not isinstance(labels, dict):
        labels = {}
    return as_bool(labels.get(name), default)


def shadow_pred(row: dict[str, Any], name: str, default: bool = False) -> bool:
    shadow = shadow_dict(row)
    labels = shadow.get("predicted_labels", {})
    if not isinstance(labels, dict):
        labels = {}
    return as_bool(labels.get(name), default)


def feature(row: dict[str, Any], name: str, default: float = 0.0) -> float:
    shadow = shadow_dict(row)
    values = shadow.get("feature_values", {})
    if not isinstance(values, dict):
        values = {}
    return as_float(values.get(name), default)


def shadow_probabilities(row: dict[str, Any], names: list[str]) -> list[float]:
    shadow = shadow_dict(row)
    probs = shadow.get("probabilities", {})
    if not isinstance(probs, dict):
        probs = {}
    return [as_float(probs.get(name), 0.0) for name in names]


def episode_context(
    *,
    source_kind: str,
    suite: str,
    case_id: str,
    expected_boundary: bool,
    row: dict[str, Any],
) -> dict[str, Any]:
    summary = row.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    skill_id = str(row.get("skill_id", "unknown"))
    terminal_reason = str(row.get("terminal_reason", "unknown"))
    success = bool(row.get("success", False))
    initial_accepted = feature(row, "initial_vision_accepted", 1.0) > 0.5
    initial_samples = feature(row, "initial_stress_samples", as_float(summary.get("initial_vision_stress_samples", 1.0), 1.0))
    initial_conf = feature(row, "initial_vision_confidence", as_float(summary.get("initial_vision_confidence", 1.0), 1.0))
    initial_retention = feature(row, "initial_vision_mask_retention_ratio", as_float(summary.get("initial_vision_mask_retention_ratio", 1.0), 1.0))
    initial_visibility = feature(row, "initial_vision_visibility_fraction", as_float(summary.get("initial_vision_visibility_fraction", 1.0), 1.0))
    initial_stress_named = str(summary.get("initial_vision_stress_scenario", "none")).lower() not in {"", "none"}
    initial_shadow_quality = shadow_true(row, "initial_quality_adapter_required", False)
    initial_hard_failed = terminal_reason == "initial_vision_failed" or not initial_accepted
    initial_degraded = bool(
        initial_shadow_quality
        or initial_hard_failed
        or initial_samples > 1.0
        or initial_conf < 0.75
        or initial_retention < 0.70
        or initial_visibility < 0.035
        or initial_stress_named
    )
    initial_adapter_required = bool(initial_accepted and not initial_hard_failed and initial_degraded)

    final_primary_accepted = feature(row, "final_vision_primary_accepted", 1.0) > 0.5
    final_accepted = feature(row, "final_vision_accepted", 1.0) > 0.5
    final_conf = feature(row, "final_vision_confidence", as_float(summary.get("final_vision_confidence", 1.0), 1.0))
    final_retention = feature(row, "final_vision_mask_retention_ratio", as_float(summary.get("final_vision_mask_retention_ratio", 1.0), 1.0))
    final_visibility = feature(row, "final_vision_visibility_fraction", as_float(summary.get("final_vision_visibility_fraction", 1.0), 1.0))
    final_samples = feature(row, "final_stress_samples", 1.0)
    final_handoff = bool(
        shadow_true(row, "final_tactile_handoff_required", False)
        or (not final_primary_accepted and final_accepted and feature(row, "final_tactile_hold_ok", 0.0) > 0.5)
    )
    final_occlusion_aware = bool(
        shadow_true(row, "final_occlusion_aware_required", False)
        or (not final_primary_accepted and final_accepted and final_samples > 1.0)
    )
    final_degraded = bool(
        final_handoff
        or final_occlusion_aware
        or not final_primary_accepted
        or not final_accepted
        or final_conf < 0.30
        or final_retention < 0.70
        or final_visibility < 0.035
        or final_samples > 1.0
    )

    repair_mode = str(summary.get("repair_mode", "none"))
    repair_configured = bool(
        skill_id == "thumb_index_middle_pinch"
        and (feature(row, "pinch_repair_mode_all", 0.0) > 0.5 or repair_mode not in {"", "none", "None"})
    )
    repair_event_count = feature(row, "pinch_repair_event_count", 0.0)
    if repair_event_count <= 0.0 and isinstance(summary.get("repair_event_counts"), dict):
        repair_event_count = float(sum(as_float(v) for v in summary.get("repair_event_counts", {}).values()))

    return {
        "source_kind": str(source_kind),
        "suite": str(suite),
        "case_id": str(case_id),
        "bucket": source_bucket_from_case(case_id, suite),
        "expected_boundary": bool(expected_boundary),
        "skill_id": skill_id,
        "trial": str(row.get("trial", "unknown")),
        "terminal_reason": terminal_reason,
        "success": success,
        "initial_degraded": initial_degraded,
        "initial_freeze": bool(initial_hard_failed or (initial_degraded and initial_samples > 1.0)),
        "initial_quality_adapter_required": initial_adapter_required,
        "final_degraded": final_degraded,
        "final_freeze": bool(final_degraded and (not final_primary_accepted or final_samples > 1.0)),
        "final_tactile_handoff_required": final_handoff,
        "final_occlusion_aware_required": final_occlusion_aware,
        "repair_configured": repair_configured,
        "repair_event_count": float(repair_event_count),
        "hold_safe": bool(shadow_true(row, "hold_safe", success) or (success and "hold" in terminal_reason)),
        "failure_or_blocked": bool(shadow_true(row, "failure_or_blocked", not success) or not success),
        "floor_or_hold_failure": bool(shadow_true(row, "floor_or_hold_failure", False) or ("hold" in terminal_reason and not success)),
        "unsafe_shadow": bool(shadow_pred(row, "hold_safe", False) and not shadow_true(row, "hold_safe", success)),
    }


def normalized_trace(row: dict[str, Any], ctx: dict[str, Any], sample_every: int) -> list[dict[str, Any]]:
    trace = row.get("trace", [])
    if isinstance(trace, list) and trace:
        return [dict(item) for item in trace if isinstance(item, dict)]
    return [
        {
            "step": 0,
            "phase": "initial_vision_failed" if ctx["failure_or_blocked"] else "missing_trace",
            "progress": 0.0,
            "lift_height_m": 0.0,
            "true_lift_height_m": 0.0,
            "contact": False,
            "pinch_contact": False,
            "stable": False,
            "slip": 0.0,
            "crush": 0.0,
            "penetration": 0.0,
            "repair_active": False,
            "recovery_active": False,
            "synthetic_trace": True,
            "frame_span_steps": int(max(1, sample_every)),
        }
    ]


def frame_span(trace: list[dict[str, Any]], idx: int, total_steps: int, sample_every: int) -> int:
    step = int(as_float(trace[idx].get("step"), 0.0))
    if idx + 1 < len(trace):
        next_step = int(as_float(trace[idx + 1].get("step"), step + sample_every))
        return int(max(1, next_step - step))
    return int(max(1, total_steps - step)) if total_steps > step else int(max(1, sample_every))


def labels_for_trace(trace_row: dict[str, Any], ctx: dict[str, Any], thresholds: Stage3Thresholds) -> dict[str, bool]:
    phase = str(trace_row.get("phase", "unknown"))
    early = phase in INITIAL_PHASES
    late = phase in FINAL_PHASES
    contact = as_bool(trace_row.get("contact"), False)
    stable = as_bool(trace_row.get("stable"), False)
    slip = as_float(trace_row.get("slip"), 0.0)
    crush = as_float(trace_row.get("crush"), 0.0)
    penetration = as_float(trace_row.get("penetration"), 0.0)
    risk_slip = slip > float(thresholds.success_max_slip_score)
    risk_crush = crush > float(thresholds.success_max_crush_risk)
    risk_penetration = penetration > float(thresholds.success_max_penetration_m)
    physical_risk = bool(risk_slip or risk_crush or risk_penetration)
    repair_active = as_bool(trace_row.get("repair_active"), False)
    recovery_active = as_bool(trace_row.get("recovery_active"), False)
    tactile_handoff = bool(ctx["final_tactile_handoff_required"] and late and (contact or stable or phase == "initial_vision_failed"))
    vision_degraded = bool((ctx["initial_degraded"] and early) or (ctx["final_degraded"] and late))
    vision_freeze = bool((ctx["initial_freeze"] and early) or (ctx["final_freeze"] and late))
    safety_active = bool(repair_active or recovery_active or tactile_handoff)
    hold_safe = bool(ctx["hold_safe"] and late and not ctx["failure_or_blocked"])
    risk_any = bool(physical_risk or ctx["failure_or_blocked"] or ctx["unsafe_shadow"] or safety_active)
    return {
        "vision_degraded": vision_degraded,
        "vision_freeze": vision_freeze,
        "initial_quality_adapter_required": bool(ctx["initial_quality_adapter_required"] and early),
        "final_occlusion_aware_required": bool(ctx["final_occlusion_aware_required"] and late),
        "tactile_handoff": tactile_handoff,
        "repair_configured": bool(ctx["repair_configured"]),
        "repair_active": repair_active,
        "recovery_active": recovery_active,
        "safety_intervention_active": safety_active,
        "risk_slip_high": risk_slip,
        "risk_crush_high": risk_crush,
        "risk_penetration_high": risk_penetration,
        "physical_risk_any": physical_risk,
        "hold_safe": hold_safe,
        "failure_or_blocked": bool(ctx["failure_or_blocked"]),
        "floor_or_hold_failure": bool(ctx["floor_or_hold_failure"]),
        "risk_any": risk_any,
    }


def source_specs_from_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    if not bool(args.no_clean_source) and Path(args.clean_source).exists():
        specs.append(
            {
                "metadata": Path(args.clean_source),
                "source_kind": "stage3_10c_clean_cycle50",
                "suite": "clean",
                "case_id": "clean_cycle50",
                "expected_boundary": False,
            }
        )
    aggregate = Path(args.shadow_aggregate)
    if aggregate.exists():
        payload = read_json(aggregate)
        for case in payload.get("cases", []):
            metadata = Path(str(case.get("metadata", "")))
            if not metadata.exists():
                metadata = ROOT / "metadata" / metadata.name
            specs.append(
                {
                    "metadata": metadata,
                    "source_kind": "stage3_11b_shadow",
                    "suite": str(case.get("suite", "shadow")),
                    "case_id": str(case.get("case_id", metadata.stem)),
                    "expected_boundary": bool(case.get("expected_boundary", False)),
                }
            )
    for item in args.extra_metadata:
        path = Path(item)
        specs.append(
            {
                "metadata": path,
                "source_kind": "extra",
                "suite": "extra",
                "case_id": path.stem,
                "expected_boundary": False,
            }
        )
    return specs


def export_labels(args: argparse.Namespace) -> dict[str, Any]:
    thresholds = Stage3Thresholds()
    phase_table: list[str] = []
    skill_table: list[str] = []
    suite_table: list[str] = []
    case_table: list[str] = []
    bucket_table: list[str] = []
    terminal_table: list[str] = []
    source_table: list[str] = []
    shadow_label_table: list[str] = []

    rows_for_jsonl: list[dict[str, Any]] = []
    label_rows: list[list[float]] = []
    shadow_prob_rows: list[list[float]] = []
    arrays: dict[str, list[Any]] = {
        "global_frame_ids": [],
        "global_episode_ids": [],
        "source_episode_ids": [],
        "trace_row_ids": [],
        "step_ids": [],
        "frame_span_steps": [],
        "phase_ids": [],
        "skill_ids": [],
        "suite_ids": [],
        "case_ids": [],
        "bucket_ids": [],
        "source_kind_ids": [],
        "terminal_reason_ids": [],
        "successes": [],
        "expected_boundary": [],
        "synthetic_trace": [],
        "contact": [],
        "stable": [],
        "pinch_contact": [],
        "slip": [],
        "crush": [],
        "penetration": [],
        "lift_height_m": [],
        "progress": [],
        "repair_close_delta": [],
        "repair_expert_alpha": [],
        "repair_inactive_alpha": [],
    }
    source_summaries: list[dict[str, Any]] = []
    global_frame = 0
    global_episode = 0

    specs = source_specs_from_args(args)
    if not specs:
        raise SystemExit("No source metadata found for Stage3.11C export.")

    for spec in specs:
        metadata = Path(spec["metadata"])
        if not metadata.exists():
            source_summaries.append({"metadata": str(metadata), "status": "missing"})
            continue
        payload = read_json(metadata)
        results = payload.get("results", [])
        if bool(args.quick):
            results = results[: min(len(results), int(args.quick_episodes))]
        source_frame_start = global_frame
        source_episode_start = global_episode
        for source_row in results:
            if not isinstance(source_row, dict):
                continue
            ctx = episode_context(
                source_kind=str(spec["source_kind"]),
                suite=str(spec["suite"]),
                case_id=str(spec["case_id"]),
                expected_boundary=bool(spec["expected_boundary"]),
                row=source_row,
            )
            trace = normalized_trace(source_row, ctx, int(args.sample_every))
            summary = source_row.get("summary", {})
            if not isinstance(summary, dict):
                summary = {}
            total_steps = int(as_float(summary.get("total_steps"), 0.0))
            shadow = shadow_dict(source_row)
            shadow_names = [str(item) for item in shadow.get("label_names", [])] if isinstance(shadow.get("label_names", []), list) else []
            for name in shadow_names:
                table_id(shadow_label_table, name)
            for trace_idx, trace_row in enumerate(trace):
                phase = str(trace_row.get("phase", "unknown"))
                labels = labels_for_trace(trace_row, ctx, thresholds)
                label_values = [1.0 if labels[name] else 0.0 for name in LABEL_NAMES]
                span = int(trace_row.get("frame_span_steps", frame_span(trace, trace_idx, total_steps, int(args.sample_every))))
                phase_id = table_id(phase_table, phase)
                skill_id = table_id(skill_table, ctx["skill_id"])
                suite_id = table_id(suite_table, ctx["suite"])
                case_id = table_id(case_table, ctx["case_id"])
                bucket_id = table_id(bucket_table, ctx["bucket"])
                source_id = table_id(source_table, ctx["source_kind"])
                terminal_id = table_id(terminal_table, ctx["terminal_reason"])
                arrays["global_frame_ids"].append(global_frame)
                arrays["global_episode_ids"].append(global_episode)
                arrays["source_episode_ids"].append(int(source_row.get("episode_id", -1)))
                arrays["trace_row_ids"].append(trace_idx)
                arrays["step_ids"].append(int(as_float(trace_row.get("step"), 0.0)))
                arrays["frame_span_steps"].append(span)
                arrays["phase_ids"].append(phase_id)
                arrays["skill_ids"].append(skill_id)
                arrays["suite_ids"].append(suite_id)
                arrays["case_ids"].append(case_id)
                arrays["bucket_ids"].append(bucket_id)
                arrays["source_kind_ids"].append(source_id)
                arrays["terminal_reason_ids"].append(terminal_id)
                arrays["successes"].append(bool(ctx["success"]))
                arrays["expected_boundary"].append(bool(ctx["expected_boundary"]))
                arrays["synthetic_trace"].append(bool(trace_row.get("synthetic_trace", False)))
                arrays["contact"].append(as_bool(trace_row.get("contact"), False))
                arrays["stable"].append(as_bool(trace_row.get("stable"), False))
                arrays["pinch_contact"].append(as_bool(trace_row.get("pinch_contact"), False))
                arrays["slip"].append(as_float(trace_row.get("slip"), 0.0))
                arrays["crush"].append(as_float(trace_row.get("crush"), 0.0))
                arrays["penetration"].append(as_float(trace_row.get("penetration"), 0.0))
                arrays["lift_height_m"].append(as_float(trace_row.get("true_lift_height_m", trace_row.get("lift_height_m", 0.0)), 0.0))
                arrays["progress"].append(as_float(trace_row.get("progress", trace_row.get("nominal_progress", 0.0)), 0.0))
                arrays["repair_close_delta"].append(as_float(trace_row.get("repair_close_delta"), 0.0))
                arrays["repair_expert_alpha"].append(as_float(trace_row.get("repair_expert_alpha"), 0.0))
                arrays["repair_inactive_alpha"].append(as_float(trace_row.get("repair_inactive_alpha"), 0.0))
                label_rows.append(label_values)
                shadow_prob_rows.append(shadow_probabilities(source_row, shadow_label_table))
                row_record = {
                    "global_frame_id": int(global_frame),
                    "global_episode_id": int(global_episode),
                    "source_episode_id": int(source_row.get("episode_id", -1)),
                    "source_kind": ctx["source_kind"],
                    "suite": ctx["suite"],
                    "case_id": ctx["case_id"],
                    "bucket": ctx["bucket"],
                    "skill_id": ctx["skill_id"],
                    "trial": ctx["trial"],
                    "phase": phase,
                    "step": int(as_float(trace_row.get("step"), 0.0)),
                    "frame_span_steps": int(span),
                    "success": bool(ctx["success"]),
                    "terminal_reason": ctx["terminal_reason"],
                    "expected_boundary": bool(ctx["expected_boundary"]),
                    "labels": {name: bool(labels[name]) for name in LABEL_NAMES},
                    "signals": {
                        "slip": as_float(trace_row.get("slip"), 0.0),
                        "crush": as_float(trace_row.get("crush"), 0.0),
                        "penetration": as_float(trace_row.get("penetration"), 0.0),
                        "contact": as_bool(trace_row.get("contact"), False),
                        "stable": as_bool(trace_row.get("stable"), False),
                    },
                }
                rows_for_jsonl.append(row_record)
                global_frame += 1
            global_episode += 1
        source_summaries.append(
            {
                "metadata": str(metadata),
                "source_kind": str(spec["source_kind"]),
                "suite": str(spec["suite"]),
                "case_id": str(spec["case_id"]),
                "bucket": source_bucket_from_case(str(spec["case_id"]), str(spec["suite"])),
                "episodes": int(global_episode - source_episode_start),
                "frames": int(global_frame - source_frame_start),
                "expected_boundary": bool(spec["expected_boundary"]),
            }
        )

    label_array = np.asarray(label_rows, dtype=np.float32)
    if not shadow_label_table:
        shadow_label_table = []
    max_shadow = max((len(row) for row in shadow_prob_rows), default=0)
    shadow_probs = np.zeros((len(shadow_prob_rows), max_shadow), dtype=np.float32)
    for idx, row in enumerate(shadow_prob_rows):
        if row:
            shadow_probs[idx, : len(row)] = np.asarray(row, dtype=np.float32)

    np_arrays: dict[str, np.ndarray] = {
        "labels": label_array,
        "label_names": np.asarray(LABEL_NAMES, dtype=str),
        "phase_table": np.asarray(phase_table, dtype=str),
        "skill_table": np.asarray(skill_table, dtype=str),
        "suite_table": np.asarray(suite_table, dtype=str),
        "case_table": np.asarray(case_table, dtype=str),
        "bucket_table": np.asarray(bucket_table, dtype=str),
        "source_kind_table": np.asarray(source_table, dtype=str),
        "terminal_reason_table": np.asarray(terminal_table, dtype=str),
        "shadow_label_table": np.asarray(shadow_label_table, dtype=str),
        "shadow_probabilities": shadow_probs,
    }
    int_keys = {
        "global_frame_ids",
        "global_episode_ids",
        "source_episode_ids",
        "trace_row_ids",
        "step_ids",
        "frame_span_steps",
        "phase_ids",
        "skill_ids",
        "suite_ids",
        "case_ids",
        "bucket_ids",
        "source_kind_ids",
        "terminal_reason_ids",
    }
    bool_keys = {"successes", "expected_boundary", "synthetic_trace", "contact", "stable", "pinch_contact"}
    for key, values in arrays.items():
        if key in int_keys:
            np_arrays[key] = np.asarray(values, dtype=np.int32)
        elif key in bool_keys:
            np_arrays[key] = np.asarray(values, dtype=np.bool_)
        else:
            np_arrays[key] = np.asarray(values, dtype=np.float32)

    label_counts = {name: int(label_array[:, idx].sum()) for idx, name in enumerate(LABEL_NAMES)}
    weighted_label_counts = {
        name: int(np.asarray(arrays["frame_span_steps"], dtype=np.int64)[label_array[:, idx] > 0.5].sum())
        for idx, name in enumerate(LABEL_NAMES)
    }
    bucket_counts = dict(Counter(source_bucket_from_case(item["case_id"], item["suite"]) for item in source_summaries if item.get("status") != "missing"))
    bucket_frame_counts: dict[str, int] = {}
    for source in source_summaries:
        bucket = str(source.get("bucket", "unknown"))
        bucket_frame_counts[bucket] = bucket_frame_counts.get(bucket, 0) + int(source.get("frames", 0))
    required_buckets = ["clean", "pose_noise", "mask_dropout", "occlusion", "depth_noise", "false_positive", "combined_hard"]
    missing_buckets = [name for name in required_buckets if bucket_frame_counts.get(name, 0) <= 0]

    split_repair_ok = bool(label_counts.get("repair_configured", 0) > label_counts.get("repair_active", 0) > 0)
    positive_required = [
        "vision_degraded",
        "vision_freeze",
        "tactile_handoff",
        "repair_configured",
        "repair_active",
        "risk_any",
    ]
    positive_missing = [name for name in positive_required if label_counts.get(name, 0) <= 0]
    checks = {
        "row_count": int(label_array.shape[0]),
        "episode_count": int(global_episode),
        "label_shape": list(label_array.shape),
        "positive_required_missing": positive_missing,
        "missing_required_buckets": missing_buckets,
        "split_repair_configured_vs_active_ok": split_repair_ok,
        "has_synthetic_boundary_trace": bool(np.asarray(arrays["synthetic_trace"], dtype=np.bool_).any()),
    }
    checks["stage3_11c_ready"] = bool(
        checks["row_count"] > 0
        and checks["episode_count"] > 0
        and not positive_missing
        and not missing_buckets
        and split_repair_ok
        and label_array.shape[1] == len(LABEL_NAMES)
    )
    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11C",
        "status": "PASS" if checks["stage3_11c_ready"] else "NEEDS_REPAIR",
        "granularity": "trace_frame_sampled_from_evaluator",
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "label_names": LABEL_NAMES,
        "label_definitions": LABEL_DEFINITIONS,
        "thresholds": {
            "success_max_slip_score": float(thresholds.success_max_slip_score),
            "success_max_crush_risk": float(thresholds.success_max_crush_risk),
            "success_max_penetration_m": float(thresholds.success_max_penetration_m),
        },
        "sources": source_summaries,
        "label_counts": label_counts,
        "weighted_label_counts_by_span_steps": weighted_label_counts,
        "bucket_counts": bucket_counts,
        "bucket_frame_counts": bucket_frame_counts,
        "checks": checks,
        "boundary": {
            "mujoco_only": True,
            "trace_frame_level_not_dense_obs_action": True,
            "full_action_act_dp_promoted": False,
            "hardware_runtime": False,
            "real_camera": False,
            "real_tactile": False,
            "ultrasound_runtime": False,
        },
        "next": "Stage3.11D safety-conditioned hand/residual policy only after reviewing Stage3.11C labels; dense obs/action alignment can be a Stage3.11C2 follow-up if needed.",
    }
    return {"metadata": metadata, "arrays": np_arrays, "jsonl_rows": rows_for_jsonl}


def write_outputs(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    dataset = Path(args.dataset)
    jsonl_path = Path(args.jsonl)
    metadata_path = Path(args.metadata)
    report_path = Path(args.report)
    dataset.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    arrays = dict(payload["arrays"])
    arrays["metadata_json"] = np.asarray([json.dumps(json_ready(payload["metadata"]), ensure_ascii=False)], dtype=str)
    np.savez_compressed(dataset, **arrays)
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in payload["jsonl_rows"]:
            fh.write(json.dumps(json_ready(row), ensure_ascii=False, sort_keys=True) + "\n")
    metadata_path.write_text(json.dumps(json_ready(payload["metadata"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(report_path, payload["metadata"])


def write_report(path: Path, metadata: dict[str, Any]) -> None:
    checks = metadata["checks"]
    lines = [
        "# Stage3.11C Frame-Level Safety Labels v0 Closeout\n\n",
        f"- 生成时间：`{metadata['generated_at']}`\n",
        f"- 状态：`{metadata['status']}`\n",
        f"- 粒度：`{metadata['granularity']}`\n",
        f"- 数据集：`{metadata['dataset']}`\n",
        f"- JSONL：`{metadata['jsonl']}`\n",
        "- 边界：MuJoCo-only；不是 full-action ACT/DP promotion；不是真实摄像头、真实触觉、超声或硬件 runtime。\n\n",
        "## 做了什么\n\n",
        "Stage3.11C 把 Stage3.10C clean evaluator trace 和 Stage3.11B shadow evaluator trace 导出成逐 trace-frame 标签。每一行保留 source/case/episode/skill/phase/step，并给出视觉退化、视觉冻结、触觉接管、repair 配置、repair 实际激活、recovery、物理风险和失败边界标签。\n\n",
        "这版先解决 Stage3.11B 暴露出的标签定义问题：`repair_configured` 和 `repair_active` 被拆成两个标签。前者表示这个 episode 配置了 repair，后者只在 trace frame 里真的触发 repair 时为 1。\n\n",
        "## 总结果\n\n",
        f"- trace frames：`{checks['row_count']}`\n",
        f"- episodes：`{checks['episode_count']}`\n",
        f"- label shape：`{checks['label_shape']}`\n",
        f"- 缺失的必需正样本：`{checks['positive_required_missing']}`\n",
        f"- 缺失的必需覆盖桶：`{checks['missing_required_buckets']}`\n",
        f"- repair 配置/激活拆分检查：`{checks['split_repair_configured_vs_active_ok']}`\n\n",
        "## Label 正样本计数\n\n",
        "| label | trace-frame count | span-weighted step count |\n",
        "| --- | ---: | ---: |\n",
    ]
    for name in metadata["label_names"]:
        lines.append(
            f"| `{name}` | {metadata['label_counts'].get(name, 0)} | "
            f"{metadata['weighted_label_counts_by_span_steps'].get(name, 0)} |\n"
        )
    lines.extend(
        [
            "\n## 覆盖范围\n\n",
            "| bucket | source count | trace frames |\n",
            "| --- | ---: | ---: |\n",
        ]
    )
    for bucket in sorted(metadata["bucket_frame_counts"]):
        lines.append(
            f"| `{bucket}` | {metadata['bucket_counts'].get(bucket, 0)} | "
            f"{metadata['bucket_frame_counts'].get(bucket, 0)} |\n"
        )
    lines.extend(
        [
            "\n## 发现的问题\n\n",
        ]
    )
    if metadata["status"] == "PASS":
        lines.extend(
            [
                "- Stage3.11C v0 通过数据门槛：必需标签都有正样本，clean / pose-noise / mask dropout / occlusion / depth-noise / false-positive / combined_hard 覆盖齐全。\n",
                "- 当前粒度是 evaluator trace-frame，不是 dense obs/action 每步数据；这适合先验收标签定义和覆盖率，后续如果要直接训练 ACT/DP 可做 Stage3.11C2 dense capture。\n",
                "- `repair_configured` 明显多于 `repair_active`，说明 B 中的问题已经被结构性拆开，不再把配置当成真实触发。\n",
                "- `risk_crush_high` 和 `risk_penetration_high` 为 0 不是失败：当前通过/边界数据没有超过 crush 或 penetration 阈值的帧，不能为了凑正样本伪造危险标签。\n",
            ]
        )
    else:
        lines.extend(
            [
                "- Stage3.11C v0 没过数据门槛。优先看缺失正样本和缺失覆盖桶，不要进入 residual/full-action 训练。\n",
                "- 若缺 clean，补 Stage3.10C clean source；若缺 tactile/repair，检查 3.11B shadow case 是否加载完整；若缺 risk，检查阈值或 trace 采样。\n",
            ]
        )
    lines.extend(
        [
            "\n## 如果成功\n\n",
            "进入 Stage3.11D：先训练或评估 safety-conditioned hand/residual policy，并与 Stage3.10E/Stage3.11B baseline 同场景对比。\n\n",
            "## 如果失败\n\n",
            "先修 label definition、source coverage、trace/frame 对齐或 dense capture，不把不可靠标签喂给策略训练。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-source", type=Path, default=DEFAULT_CLEAN_SOURCE)
    parser.add_argument("--shadow-aggregate", type=Path, default=DEFAULT_SHADOW_AGGREGATE)
    parser.add_argument("--extra-metadata", nargs="*", default=[])
    parser.add_argument("--no-clean-source", action="store_true")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-every", type=int, default=240)
    parser.add_argument("--quick", action="store_true", help="Use only a small prefix of each source for smoke checks.")
    parser.add_argument("--quick-episodes", type=int, default=4)
    args = parser.parse_args()
    payload = export_labels(args)
    write_outputs(args, payload)
    summary = {
        "status": payload["metadata"]["status"],
        "rows": payload["metadata"]["checks"]["row_count"],
        "episodes": payload["metadata"]["checks"]["episode_count"],
        "label_shape": payload["metadata"]["checks"]["label_shape"],
        "missing_labels": payload["metadata"]["checks"]["positive_required_missing"],
        "missing_buckets": payload["metadata"]["checks"]["missing_required_buckets"],
        "split_repair_ok": payload["metadata"]["checks"]["split_repair_configured_vs_active_ok"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved dataset: {Path(args.dataset).resolve()}")
    print(f"Saved jsonl: {Path(args.jsonl).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")
    print(f"Saved report: {Path(args.report).resolve()}")
    return 0 if payload["metadata"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
