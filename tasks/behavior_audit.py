"""Behavior-audit helpers for temporary scripted stable_grasp evaluation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List
import time

import numpy as np


def _serialize_value(value: Any) -> Any:
    """Convert numpy-heavy values into JSON-friendly payloads."""
    if isinstance(value, np.ndarray):
        return value.astype(np.float32).tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    return value


def _numeric_summary(values: Iterable[float]) -> Dict[str, Any]:
    """Summarize numeric audit values compactly."""
    resolved = [float(item) for item in values]
    if not resolved:
        return {"count": 0}
    array = np.asarray(resolved, dtype=np.float32)
    return {
        "count": int(array.size),
        "mean": float(np.mean(array)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
    }


def _bool_summary(values: Iterable[bool]) -> Dict[str, Any]:
    """Summarize boolean audit values with explicit true/false counts."""
    resolved = [bool(item) for item in values]
    total = int(len(resolved))
    true_count = int(sum(resolved))
    false_count = int(total - true_count)
    return {
        "count": total,
        "true_count": true_count,
        "false_count": false_count,
        "true_rate": float(true_count / total) if total else 0.0,
    }


@dataclass
class TemporaryStableGraspCollectionGate:
    """
    Temporary collection gate for scripted stable_grasp rollouts.

    This gate is intentionally stricter than a generic "interesting episode" filter and should
    be read only as a temporary data-collection readiness test. It is not the official task
    success definition and not a benchmark threshold.
    """

    require_transition_reached: bool = True
    require_stable_grasp_entered: bool = True
    min_hold_steps: int = 1
    min_support_region_count: int = 2
    min_closure_metric: float = 0.10
    max_object_displacement_from_entry: float = 0.08
    max_object_vertical_drop_from_entry: float = 0.05

    def to_dict(self) -> Dict[str, Any]:
        return {
            "require_transition_reached": bool(self.require_transition_reached),
            "require_stable_grasp_entered": bool(self.require_stable_grasp_entered),
            "min_hold_steps": int(self.min_hold_steps),
            "min_support_region_count": int(self.min_support_region_count),
            "min_closure_metric": float(self.min_closure_metric),
            "max_object_displacement_from_entry": float(self.max_object_displacement_from_entry),
            "max_object_vertical_drop_from_entry": float(self.max_object_vertical_drop_from_entry),
            "notes": (
                "Temporary collection gate for scripted stable_grasp episodes. Not the official "
                "task success contract and not a benchmark threshold."
            ),
        }


def classify_stable_grasp_failure_mode(episode_artifact: Dict[str, Any]) -> str:
    """Attribute a coarse failure mode using existing transition/checker outputs."""
    transition_info = dict(episode_artifact.get("transition_decision", {}) or {})
    transition_ready = bool(transition_info.get("ready", False))
    blocked_reason = str(transition_info.get("blocked_reason") or "")
    if not transition_ready and not blocked_reason:
        blocked_reason = str(transition_info.get("reason") or "")
    if not transition_ready and blocked_reason:
        return "transition_not_reached"

    episode_result = episode_artifact["episode_result"]
    terminal_reason = str(getattr(episode_result, "terminal_reason", "") or "")
    official_metrics = dict(getattr(episode_result, "official_metrics", {}) or {})
    support_region_count = int(official_metrics.get("support_region_count", 0) or 0)
    sustained_contact_steps = int(official_metrics.get("sustained_contact_steps", 0) or 0)
    closure_metric = float(official_metrics.get("closure_metric", 0.0) or 0.0)

    if terminal_reason in {
        "object_on_floor",
        "object_exited_workspace",
        "object_displacement_limit_exceeded",
        "object_vertical_drop_limit_exceeded",
        "workspace_retention_not_ready",
    }:
        return "object_escaped_or_displaced"
    if terminal_reason == "closure_not_ready":
        return "insufficient_closure"
    if terminal_reason == "contact_support_not_ready":
        return "insufficient_sustained_contact"
    if terminal_reason in {"building_required_hold_steps", "episode_timeout", "episode_incomplete"}:
        if closure_metric < 0.10:
            return "insufficient_closure"
        if support_region_count < 2 or sustained_contact_steps <= 0:
            return "insufficient_sustained_contact"
        return "timeout_or_incomplete_hold"
    if getattr(episode_result, "episode_status", "") in {"timeout", "incomplete"}:
        if support_region_count < 2 or sustained_contact_steps <= 0:
            return "insufficient_sustained_contact"
        if closure_metric < 0.10:
            return "insufficient_closure"
        return "timeout_or_incomplete_hold"
    return "fallback_or_unclear"


def audit_temporary_collection_readiness(
    episode_artifact: Dict[str, Any],
    readiness_gate: TemporaryStableGraspCollectionGate,
) -> Dict[str, Any]:
    """Evaluate whether one episode is usable as a temporary scripted data candidate."""
    episode_result = episode_artifact["episode_result"]
    transition_reached = bool(episode_artifact.get("transition_decision", {}).get("ready", False))
    stable_phase_debug = dict(episode_artifact.get("phase_debug", {}).get("stable_grasp", {}) or {})
    stable_grasp_entered = bool(stable_phase_debug.get("executed_steps", 0) > 0)
    official_metrics = dict(getattr(episode_result, "official_metrics", {}) or {})

    checks = {
        "transition_reached": (
            (not readiness_gate.require_transition_reached) or transition_reached
        ),
        "stable_grasp_entered": (
            (not readiness_gate.require_stable_grasp_entered) or stable_grasp_entered
        ),
        "minimum_hold_steps": (
            int(official_metrics.get("hold_steps", 0) or 0) >= readiness_gate.min_hold_steps
        ),
        "minimum_support_regions": (
            int(official_metrics.get("support_region_count", 0) or 0)
            >= readiness_gate.min_support_region_count
        ),
        "minimum_closure_metric": (
            float(official_metrics.get("closure_metric", 0.0) or 0.0)
            >= readiness_gate.min_closure_metric
        ),
        "displacement_within_gate": (
            float(official_metrics.get("object_displacement_from_entry", np.inf) or np.inf)
            <= readiness_gate.max_object_displacement_from_entry
        ),
        "vertical_drop_within_gate": (
            float(official_metrics.get("object_vertical_drop_from_entry", np.inf) or np.inf)
            <= readiness_gate.max_object_vertical_drop_from_entry
        ),
    }
    unmet = [name for name, passed in checks.items() if not passed]
    return {
        "is_candidate": bool(not unmet),
        "checks": checks,
        "unmet_checks": unmet,
        "notes": (
            "Temporary collection gate only. Candidate episodes are provisional data-source "
            "candidates, not official stable_grasp successes."
        ),
    }


def _extract_behavior_progress(stable_phase_debug: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize closure/contact progression during stable_grasp execution."""
    metric_history = list(stable_phase_debug.get("official_metric_history", []) or [])
    if not metric_history:
        return {
            "closure_start": 0.0,
            "closure_end": 0.0,
            "closure_delta": 0.0,
            "support_region_count_start": 0,
            "support_region_count_end": 0,
            "support_region_delta": 0,
            "max_hold_steps_observed": 0,
            "max_sustained_contact_steps_observed": 0,
            "any_contact_observed": False,
        }

    first = dict(metric_history[0] or {})
    last = dict(metric_history[-1] or {})
    return {
        "closure_start": float(first.get("closure_metric", 0.0) or 0.0),
        "closure_end": float(last.get("closure_metric", 0.0) or 0.0),
        "closure_delta": float(
            float(last.get("closure_metric", 0.0) or 0.0)
            - float(first.get("closure_metric", 0.0) or 0.0)
        ),
        "support_region_count_start": int(first.get("support_region_count", 0) or 0),
        "support_region_count_end": int(last.get("support_region_count", 0) or 0),
        "support_region_delta": int(
            int(last.get("support_region_count", 0) or 0)
            - int(first.get("support_region_count", 0) or 0)
        ),
        "max_hold_steps_observed": int(
            max(int(item.get("hold_steps", 0) or 0) for item in metric_history)
        ),
        "max_sustained_contact_steps_observed": int(
            max(int(item.get("sustained_contact_steps", 0) or 0) for item in metric_history)
        ),
        "any_contact_observed": bool(
            any(bool(dict(item.get("contact_summary", {}) or {}).get("has_contact", False)) for item in metric_history)
        ),
    }


def build_stable_grasp_behavior_audit(
    episode_artifacts: List[Dict[str, Any]],
    eval_mode: str,
    stable_grasp_phase_mode: str,
    include_debug: bool = False,
    readiness_gate: TemporaryStableGraspCollectionGate | None = None,
) -> Dict[str, Any]:
    """Build an analysis-only audit artifact next to the official batch report."""
    readiness_gate = readiness_gate or TemporaryStableGraspCollectionGate()
    collection_readiness_applicable = (
        str(stable_grasp_phase_mode) == "scripted_controller"
    )
    per_episode = []

    transition_reached_count = 0
    stable_grasp_entered_count = 0
    closure_deltas = []
    support_region_deltas = []
    hold_steps = []
    closure_metrics = []
    support_region_counts = []
    sustained_contact_steps = []
    contact_presence = []
    contact_region_labels = Counter()
    failure_mode_counts = Counter()
    readiness_candidate_count = 0
    status_counts = Counter()
    formation_signal_counts = Counter()

    for episode_index, artifact in enumerate(episode_artifacts):
        episode_result = artifact["episode_result"]
        transition_reached = bool(artifact.get("transition_decision", {}).get("ready", False))
        stable_phase_debug = dict(artifact.get("phase_debug", {}).get("stable_grasp", {}) or {})
        stable_grasp_entered = bool(stable_phase_debug.get("executed_steps", 0) > 0)
        official_metrics = dict(getattr(episode_result, "official_metrics", {}) or {})
        contact_summary = dict(official_metrics.get("contact_summary", {}) or {})
        closure_summary = dict(official_metrics.get("closure_summary", {}) or {})
        behavior_progress = _extract_behavior_progress(stable_phase_debug)
        failure_mode = classify_stable_grasp_failure_mode(artifact)
        readiness = audit_temporary_collection_readiness(artifact, readiness_gate)
        readiness_unmet_checks = list(readiness["unmet_checks"])
        readiness_candidate = bool(readiness["is_candidate"])
        if not collection_readiness_applicable:
            readiness_candidate = False
            if "phase_mode_not_collection_eligible" not in readiness_unmet_checks:
                readiness_unmet_checks.append("phase_mode_not_collection_eligible")
        transition_payload = dict(artifact.get("transition_decision", {}) or {})
        transition_blocked_reason = (
            ""
            if transition_reached
            else str(
                transition_payload.get("blocked_reason")
                or transition_payload.get("reason")
                or ""
            )
        )

        transition_reached_count += int(transition_reached)
        stable_grasp_entered_count += int(stable_grasp_entered)
        failure_mode_counts[failure_mode] += 1
        status_counts[str(getattr(episode_result, "episode_status", "incomplete"))] += 1
        readiness_candidate_count += int(readiness_candidate)

        hold_steps.append(int(official_metrics.get("hold_steps", 0) or 0))
        closure_metrics.append(float(official_metrics.get("closure_metric", 0.0) or 0.0))
        support_region_counts.append(int(official_metrics.get("support_region_count", 0) or 0))
        sustained_contact_steps.append(
            int(official_metrics.get("sustained_contact_steps", 0) or 0)
        )
        contact_presence.append(bool(contact_summary.get("has_contact", False)))
        contact_region_labels.update(
            str(label) for label in list(contact_summary.get("support_regions", []) or [])
        )
        closure_deltas.append(float(behavior_progress["closure_delta"]))
        support_region_deltas.append(int(behavior_progress["support_region_delta"]))

        formation_signal_counts["closure_increase_episodes"] += int(behavior_progress["closure_delta"] > 0.0)
        formation_signal_counts["support_region_gain_episodes"] += int(behavior_progress["support_region_delta"] > 0)
        formation_signal_counts["contact_observed_episodes"] += int(behavior_progress["any_contact_observed"])

        per_episode.append(
            {
                "episode_index": int(episode_index),
                "episode_status": str(getattr(episode_result, "episode_status", "incomplete")),
                "terminal_reason": str(getattr(episode_result, "terminal_reason", "")),
                "transition_blocked_reason": transition_blocked_reason,
                "transition_reached": bool(transition_reached),
                "stable_grasp_entered": bool(stable_grasp_entered),
                "failure_mode": failure_mode,
                "readiness_candidate": bool(readiness_candidate),
                "readiness_unmet_checks": readiness_unmet_checks,
                "hold_steps": int(official_metrics.get("hold_steps", 0) or 0),
                "contact_summary": contact_summary,
                "closure_metric": float(official_metrics.get("closure_metric", 0.0) or 0.0),
                "closure_summary": closure_summary,
                "support_region_count": int(official_metrics.get("support_region_count", 0) or 0),
                "behavior_progress": behavior_progress,
            }
        )

    total = len(episode_artifacts)
    transition_blocked_count = int(total - transition_reached_count)
    if not collection_readiness_applicable:
        diagnosis = (
            "Current stable_grasp phase mode is a compatibility or comparison path only. "
            "Treat it as execution diagnosis, not as a temporary expert-data source."
        )
    elif (
        total
        and formation_signal_counts["closure_increase_episodes"] > 0
        and readiness_candidate_count == 0
    ):
        diagnosis = (
            "Current scripted controller is executable and shows grasp-formation motion, but it "
            "does not yet satisfy the temporary collection gate."
        )
    elif readiness_candidate_count > 0:
        diagnosis = (
            "Current scripted controller produces some provisional candidate episodes, but it "
            "still remains a temporary executable backend."
        )
    else:
        diagnosis = (
            "Current scripted controller is running, but the audit does not yet show enough "
            "grasp-formation evidence for temporary expert collection."
        )

    audit_payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "analysis_layer": "stable_grasp_behavior_audit",
            "eval_mode": str(eval_mode),
            "stable_grasp_phase_mode": str(stable_grasp_phase_mode),
            "collection_readiness_applicable": bool(collection_readiness_applicable),
            "readiness_gate": readiness_gate.to_dict(),
        },
        "summary": {
            "total_episodes": int(total),
            "transition_reached_count": int(transition_reached_count),
            "transition_blocked_count": int(transition_blocked_count),
            "stable_grasp_entered_count": int(stable_grasp_entered_count),
            "success_count": int(status_counts.get("success", 0)),
            "failure_count": int(status_counts.get("failure", 0)),
            "timeout_count": int(status_counts.get("timeout", 0)),
            "incomplete_count": int(status_counts.get("incomplete", 0)),
            "failure_mode_counts": dict(sorted(failure_mode_counts.items())),
            "readiness_candidate_count": int(readiness_candidate_count),
            "readiness_candidate_rate": float(readiness_candidate_count / total) if total else 0.0,
            "hold_steps_distribution": _numeric_summary(hold_steps),
            "closure_metric_distribution": _numeric_summary(closure_metrics),
            "support_region_count_distribution": _numeric_summary(support_region_counts),
            "contact_summary_distribution": {
                "has_contact": _bool_summary(contact_presence),
                "support_region_count": _numeric_summary(support_region_counts),
                "sustained_contact_steps": _numeric_summary(sustained_contact_steps),
                "support_region_label_counts": dict(sorted(contact_region_labels.items())),
            },
            "closure_summary_distribution": {
                "closure_metric": _numeric_summary(closure_metrics),
            },
            "closure_delta_distribution": _numeric_summary(closure_deltas),
            "support_region_delta_distribution": _numeric_summary(support_region_deltas),
            "grasp_formation_signal_counts": {
                key: int(value) for key, value in sorted(formation_signal_counts.items())
            },
            "diagnosis": diagnosis,
        },
        "episodes": per_episode,
    }

    if include_debug:
        audit_payload["debug"] = {
            "episode_debug_available": True,
            "notes": (
                "Detailed controller step history remains in the batch-eval debug payload and is "
                "not copied into the audit artifact by default."
            ),
        }

    return _serialize_value(audit_payload)


__all__ = [
    "TemporaryStableGraspCollectionGate",
    "audit_temporary_collection_readiness",
    "build_stable_grasp_behavior_audit",
    "classify_stable_grasp_failure_mode",
]
