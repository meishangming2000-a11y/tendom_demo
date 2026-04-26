"""Episode-level evaluation and report helpers for structured task rollouts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
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


def resolve_episode_status(success: bool, failure: bool, reached_time_limit: bool) -> str:
    """Resolve the canonical episode status label."""
    if success:
        return "success"
    if failure:
        return "failure"
    if reached_time_limit:
        return "timeout"
    return "incomplete"


def _sanitize_transition_info(transition_info: Dict[str, Any], include_debug: bool) -> Dict[str, Any]:
    """Keep transition debug metrics out of the default report payload."""
    payload = dict(_serialize_value(transition_info or {}))
    if not include_debug:
        payload.pop("debug_metrics", None)
    return payload


def _aggregate_numeric(values: List[float]) -> Dict[str, Any]:
    """Aggregate scalar numeric metrics in a report-friendly way."""
    array = np.asarray(values, dtype=np.float32)
    if array.size == 0:
        return {"count": 0}
    return {
        "count": int(array.size),
        "mean": float(np.mean(array)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
    }


def _aggregate_boolean(values: List[bool]) -> Dict[str, Any]:
    """Aggregate boolean metrics with explicit true/false counts."""
    total = int(len(values))
    true_count = int(sum(bool(item) for item in values))
    false_count = int(total - true_count)
    return {
        "count": total,
        "true_count": true_count,
        "false_count": false_count,
        "true_rate": float(true_count / total) if total else 0.0,
    }


def _aggregate_string_list(values: List[str]) -> Dict[str, Any]:
    """Aggregate categorical string values as stable counts."""
    counts = Counter(str(item) for item in values)
    return {
        "count": int(sum(counts.values())),
        "value_counts": dict(sorted(counts.items())),
        "unique_values": sorted(counts.keys()),
    }


def _aggregate_sequence(values: List[Any]) -> Dict[str, Any]:
    """Aggregate list/array metrics while preserving their structure when possible."""
    serialized_values = [_serialize_value(item) for item in values]
    lengths = {len(item) for item in serialized_values if isinstance(item, list)}
    flattened = [
        element
        for item in serialized_values
        if isinstance(item, list)
        for element in item
    ]

    if serialized_values and lengths == {0}:
        return {
            "count": int(len(serialized_values)),
            "value_counts": {},
            "unique_values": [],
        }

    if (
        serialized_values
        and len(lengths) == 1
        and flattened
        and all(isinstance(element, (int, float)) and not isinstance(element, bool) for element in flattened)
    ):
        array = np.asarray(serialized_values, dtype=np.float32)
        return {
            "count": int(len(serialized_values)),
            "mean": _serialize_value(np.mean(array, axis=0)),
            "min": _serialize_value(np.min(array, axis=0)),
            "max": _serialize_value(np.max(array, axis=0)),
        }

    if flattened and all(isinstance(element, str) for element in flattened):
        counts = Counter()
        for item in serialized_values:
            counts.update(str(element) for element in item)
        return {
            "count": int(len(serialized_values)),
            "value_counts": dict(sorted(counts.items())),
            "unique_values": sorted(counts.keys()),
        }

    return {
        "count": int(len(serialized_values)),
        "samples": serialized_values[:3],
    }


def _aggregate_metric_values(values: List[Any]) -> Dict[str, Any]:
    """Aggregate official metrics without mixing in backend debug detail."""
    serialized_values = [_serialize_value(item) for item in values if item is not None]
    if not serialized_values:
        return {}

    if all(isinstance(item, bool) for item in serialized_values):
        return _aggregate_boolean([bool(item) for item in serialized_values])

    if all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in serialized_values):
        return _aggregate_numeric([float(item) for item in serialized_values])

    if all(isinstance(item, str) for item in serialized_values):
        return _aggregate_string_list([str(item) for item in serialized_values])

    if all(isinstance(item, dict) for item in serialized_values):
        keys = sorted({key for item in serialized_values for key in item.keys()})
        return {
            key: _aggregate_metric_values([item.get(key) for item in serialized_values if key in item])
            for key in keys
        }

    if all(isinstance(item, list) for item in serialized_values):
        return _aggregate_sequence(serialized_values)

    return {
        "count": int(len(serialized_values)),
        "samples": serialized_values[:3],
    }


def summarize_official_metrics(
    episode_results: Iterable["EpisodeEvaluationResult"],
) -> Dict[str, Any]:
    """Aggregate official per-episode metrics for batch reporting."""
    results = list(episode_results)
    metric_keys = sorted(
        {
            key
            for item in results
            for key in dict(item.official_metrics or {}).keys()
        }
    )
    return {
        key: _aggregate_metric_values(
            [
                dict(item.official_metrics or {}).get(key)
                for item in results
                if key in dict(item.official_metrics or {})
            ]
        )
        for key in metric_keys
    }


@dataclass
class EpisodeEvaluationResult:
    """Unified episode-level task result for labeling, evaluation, and report output."""

    task_name: str
    episode_status: str
    terminal_reason: str
    success: bool
    failure: bool
    step_count: int
    transition_info: Dict[str, Any] = field(default_factory=dict)
    official_metrics: Dict[str, Any] = field(default_factory=dict)
    debug_metrics: Dict[str, Any] = field(default_factory=dict)
    backend_info: Dict[str, Any] = field(default_factory=dict)
    entry_snapshot: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    @classmethod
    def from_task_info(
        cls,
        task_name: str,
        info: Dict[str, Any],
        step_count: int,
        max_steps: int,
        transition_info: Dict[str, Any] | None = None,
        entry_snapshot: Dict[str, Any] | None = None,
        notes: str = "",
        reached_time_limit: bool = False,
    ) -> "EpisodeEvaluationResult":
        """Build an episode result from task info without assuming a specific backend."""
        info = dict(info or {})
        task_prefix = str(task_name)
        evaluation = dict(info.get(f"{task_prefix}_evaluation", {}) or {})

        success = bool(evaluation.get("success", info.get("success", False)))
        failure = bool(evaluation.get("failure", info.get("failure", False)))
        terminal_reason = str(
            evaluation.get("reason")
            or info.get(f"{task_prefix}_reason")
            or (
                "episode_success"
                if success
                else "episode_failure"
                if failure
                else "episode_timeout"
                if reached_time_limit or step_count >= max_steps
                else "episode_incomplete"
            )
        )

        backend_info = dict(info.get(f"{task_prefix}_backend_metadata", {}) or {})
        if "backend_type" not in backend_info and info.get(f"{task_prefix}_backend_type"):
            backend_info["backend_type"] = info.get(f"{task_prefix}_backend_type")
        if "backend_type" not in backend_info and info.get("backend_type"):
            backend_info["backend_type"] = info.get("backend_type")
        if "model_family" not in backend_info and info.get("model_family"):
            backend_info["model_family"] = info.get("model_family")

        return cls(
            task_name=task_prefix,
            episode_status=resolve_episode_status(
                success=success,
                failure=failure,
                reached_time_limit=bool(reached_time_limit or step_count >= max_steps),
            ),
            terminal_reason=terminal_reason,
            success=success,
            failure=failure,
            step_count=int(step_count),
            transition_info=dict(transition_info or {}),
            official_metrics=dict(
                evaluation.get("official_metrics", info.get(f"{task_prefix}_official_metrics", {}))
                or {}
            ),
            debug_metrics=dict(
                evaluation.get("debug_metrics", info.get(f"{task_prefix}_debug_metrics", {}))
                or {}
            ),
            backend_info=backend_info,
            entry_snapshot=dict(entry_snapshot or {}),
            notes=str(notes or evaluation.get("notes", "")),
        )

    @classmethod
    def from_transition_blocked(
        cls,
        task_name: str,
        transition_info: Dict[str, Any],
        step_count: int,
        max_steps: int,
        backend_info: Dict[str, Any] | None = None,
        notes: str = "",
        reached_time_limit: bool = False,
    ) -> "EpisodeEvaluationResult":
        """Build an episode result when a transition gate prevented task entry."""
        transition_payload = dict(_serialize_value(transition_info or {}))
        blocked_reason = str(
            transition_payload.get("blocked_reason")
            or transition_payload.get("reason")
            or (
                "episode_timeout"
                if reached_time_limit or step_count >= max_steps
                else "transition_not_ready"
            )
        )
        preconditions = dict(transition_payload.get("preconditions", {}) or {})
        source_task_failed = bool(
            preconditions.get("source_task_not_failed") is False
            or blocked_reason == "source_task_failed"
        )
        return cls(
            task_name=str(task_name),
            episode_status=resolve_episode_status(
                success=False,
                failure=bool(source_task_failed),
                reached_time_limit=bool(reached_time_limit or step_count >= max_steps),
            ),
            terminal_reason=blocked_reason,
            success=False,
            failure=bool(source_task_failed),
            step_count=int(step_count),
            transition_info=transition_payload,
            official_metrics={},
            debug_metrics={},
            backend_info=dict(_serialize_value(backend_info or {})),
            entry_snapshot={},
            notes=str(notes),
        )

    def to_payload(self, include_debug: bool = False) -> Dict[str, Any]:
        """Return the episode payload, keeping debug fields optional."""
        payload = {
            "task_name": str(self.task_name),
            "episode_status": str(self.episode_status),
            "terminal_reason": str(self.terminal_reason),
            "success": bool(self.success),
            "failure": bool(self.failure),
            "step_count": int(self.step_count),
            "transition_info": _sanitize_transition_info(
                self.transition_info,
                include_debug=include_debug,
            ),
            "official_metrics": _serialize_value(self.official_metrics),
            "backend_info": _serialize_value(self.backend_info),
            "entry_snapshot": _serialize_value(self.entry_snapshot),
            "notes": str(self.notes),
        }
        if include_debug:
            payload["debug_metrics"] = _serialize_value(self.debug_metrics)
        return payload

    def to_report_payload(self, include_debug: bool = False) -> Dict[str, Any]:
        """Return the JSON-friendly report payload for this episode."""
        return self.to_payload(include_debug=include_debug)


def summarize_episode_evaluations(
    episode_results: Iterable[EpisodeEvaluationResult],
) -> Dict[str, Any]:
    """Build a compact cross-episode summary compatible with JSON reports."""
    results: List[EpisodeEvaluationResult] = list(episode_results)
    status_breakdown = {
        status: sum(1 for item in results if item.episode_status == status)
        for status in ("success", "failure", "timeout", "incomplete")
    }
    backend_types = sorted(
        {
            str(item.backend_info.get("backend_type"))
            for item in results
            if item.backend_info.get("backend_type")
        }
    )
    task_names = sorted({str(item.task_name) for item in results})
    terminal_reason_counts = dict(
        sorted(Counter(str(item.terminal_reason) for item in results).items())
    )
    return {
        "episodes": len(results),
        "total_episodes": len(results),
        "task_names": task_names,
        "backend_types": backend_types,
        "status_breakdown": status_breakdown,
        "success_count": status_breakdown["success"],
        "failure_count": status_breakdown["failure"],
        "timeout_count": status_breakdown["timeout"],
        "incomplete_count": status_breakdown["incomplete"],
        "terminal_reason_counts": terminal_reason_counts,
        "success_rate": (
            status_breakdown["success"] / len(results) if results else 0.0
        ),
        "avg_step_count": (
            float(np.mean([item.step_count for item in results])) if results else 0.0
        ),
        "official_metric_summary": summarize_official_metrics(results),
    }


def build_report_payload(
    config: Dict[str, Any],
    episode_results: Iterable[EpisodeEvaluationResult],
    include_debug: bool = False,
) -> Dict[str, Any]:
    """Build the minimal JSON report payload used by diagnostics and future eval paths."""
    results: List[EpisodeEvaluationResult] = list(episode_results)
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": _serialize_value(config),
        "summary": summarize_episode_evaluations(results),
        "episodes": [
            item.to_report_payload(include_debug=include_debug) for item in results
        ],
    }


__all__ = [
    "EpisodeEvaluationResult",
    "build_report_payload",
    "resolve_episode_status",
    "summarize_episode_evaluations",
]
