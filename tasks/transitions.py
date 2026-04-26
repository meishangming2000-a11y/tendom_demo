"""Transition helpers for structured multi-stage manipulation tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

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


@dataclass
class TransitionDecision:
    """Machine-readable transition decision."""

    transition_name: str
    source_task: str
    target_task: str
    ready: bool
    reason: str
    implemented: bool = True
    preconditions: Dict[str, bool] = field(default_factory=dict)
    official_metrics: Dict[str, Any] = field(default_factory=dict)
    debug_metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    contract_name: str = "task_transition_contract"
    contract_version: str = "v1"

    @property
    def blocked_reason(self) -> str:
        """Return a ready/blocked reason with an explicit blocked interpretation."""
        return "" if self.ready else str(self.reason)

    @property
    def flags(self) -> Dict[str, bool]:
        """Backward-compatible alias for transition preconditions."""
        return self.preconditions

    @property
    def metrics(self) -> Dict[str, Any]:
        """Backward-compatible alias for official transition metrics."""
        return self.official_metrics

    def to_payload(self) -> Dict[str, Any]:
        """Return the structured transition payload."""
        return {
            "ready": bool(self.ready),
            "reason": str(self.reason),
            "blocked_reason": str(self.blocked_reason),
            "implemented": bool(self.implemented),
            "transition_name": str(self.transition_name),
            "source_task": str(self.source_task),
            "target_task": str(self.target_task),
            "notes": str(self.notes),
            "contract_name": str(self.contract_name),
            "contract_version": str(self.contract_version),
            "preconditions": _serialize_value(self.preconditions),
            "official_metrics": _serialize_value(self.official_metrics),
            "debug_metrics": _serialize_value(self.debug_metrics),
        }

    def to_dict(self, prefix: str) -> Dict[str, Any]:
        """Flatten the transition decision into an info payload."""
        structured_payload = self.to_payload()
        payload = {
            f"{prefix}_ready": structured_payload["ready"],
            f"{prefix}_reason": structured_payload["reason"],
            f"{prefix}_blocked_reason": structured_payload["blocked_reason"],
            f"{prefix}_implemented": structured_payload["implemented"],
            f"{prefix}_transition_name": structured_payload["transition_name"],
            f"{prefix}_source_task": structured_payload["source_task"],
            f"{prefix}_target_task": structured_payload["target_task"],
            f"{prefix}_notes": structured_payload["notes"],
            f"{prefix}_contract_name": structured_payload["contract_name"],
            f"{prefix}_contract_version": structured_payload["contract_version"],
            f"{prefix}_preconditions": structured_payload["preconditions"],
            f"{prefix}_official_metrics": structured_payload["official_metrics"],
            f"{prefix}_debug_metrics": structured_payload["debug_metrics"],
            f"{prefix}_flags": structured_payload["preconditions"],
            f"{prefix}_metrics": structured_payload["official_metrics"],
        }
        for key, value in sorted(self.preconditions.items()):
            payload[f"{prefix}_{key}"] = bool(value)
        for key, value in sorted(self.official_metrics.items()):
            payload[f"{prefix}_{key}"] = _serialize_value(value)
        return payload


@dataclass
class PreGraspToStableGraspTransitionSpec:
    """Thresholds for the first supported task transition."""

    max_entry_position_error: float = 0.035
    max_entry_orientation_error_rad: float = 0.40
    required_ready_steps: int = 5
    require_alignment_signal: bool = True
    require_source_task_not_failed: bool = True
    allow_contact_during_transition: bool = True
    reference_frame: str = "palm_object_relation"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_entry_position_error": float(self.max_entry_position_error),
            "max_entry_orientation_error_rad": float(self.max_entry_orientation_error_rad),
            "required_ready_steps": int(self.required_ready_steps),
            "require_alignment_signal": bool(self.require_alignment_signal),
            "require_source_task_not_failed": bool(self.require_source_task_not_failed),
            "allow_contact_during_transition": bool(self.allow_contact_during_transition),
            "reference_frame": str(self.reference_frame),
        }

    def get_contract(self) -> Dict[str, Any]:
        """Return the transition-contract description for docs and metadata."""
        return {
            "contract_name": "pre_grasp_to_stable_grasp_transition_contract",
            "contract_version": "v1",
            "source_task": "pre_grasp",
            "target_task": "stable_grasp",
            "required_preconditions": [
                "entry_position_within_tolerance",
                "entry_orientation_within_tolerance",
                "consecutive_ready_steps_met",
                "source_task_not_failed",
                "contact_allowed_for_transition",
                "alignment_signal_present",
            ],
            "official_metrics": [
                "entry_position_error",
                "entry_orientation_error_rad",
                "aligned_hold_steps",
                "required_ready_steps",
                "contact_present",
                "transition_reference_frame",
            ],
            "debug_metrics": [
                "source_success",
                "source_failure",
                "relative_palm_position",
                "target_offset",
                "transition_spec",
            ],
            "notes": (
                "This transition contract is independent from pre_grasp success. It may reuse "
                "pre_grasp output signals, but it is configured through its own entry tolerances "
                "and ready-step requirement."
            ),
        }


@dataclass
class PendingTransitionSpec:
    """Placeholder transition interface for future task-state machines."""

    transition_name: str
    source_task: str
    target_task: str
    notes: str


@dataclass
class TransitionEvaluationInput:
    """Input bundle used by transition evaluators."""

    transition_name: str
    source_task: str
    target_task: str
    source_info: Dict[str, Any]
    transition_spec: Dict[str, Any]
    source_task_config: Dict[str, Any]
    current_step: int


def build_pre_grasp_to_stable_grasp_input(task, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Build the task output consumed by the pre_grasp -> stable_grasp contract."""
    position_error = float(metrics["position_error"])
    orientation_error = float(metrics["orientation_error_rad"])
    aligned_hold_steps = int(getattr(task, "_hold_counter", 0))
    contact_present = bool(metrics.get("contact", False))
    source_success = bool(
        position_error <= float(task.position_tolerance)
        and orientation_error <= float(task.orientation_tolerance_rad)
        and aligned_hold_steps >= int(task.hold_steps)
    )
    source_failure = bool(
        position_error >= float(task.failure_distance)
        or (bool(task.contact_as_failure) and contact_present)
    )
    return {
        "position_error": position_error,
        "orientation_error_rad": orientation_error,
        "aligned_hold_steps": aligned_hold_steps,
        "contact_present": contact_present,
        "source_success": source_success,
        "source_failure": source_failure,
        "relative_palm_position": np.asarray(
            metrics["relative_palm_position"], dtype=np.float32
        ).tolist(),
        "target_offset": task.target_offset.astype(np.float32).tolist(),
        "task_reference_frame": "palm_object_relation",
    }


def evaluate_pre_grasp_to_stable_grasp(
    transition_input: TransitionEvaluationInput,
) -> TransitionDecision:
    """Evaluate the first supported task transition using the transition contract."""
    spec = PreGraspToStableGraspTransitionSpec(**dict(transition_input.transition_spec or {}))
    source_info = dict(transition_input.source_info or {})

    entry_position_error = float(source_info.get("position_error", np.inf))
    entry_orientation_error = float(source_info.get("orientation_error_rad", np.inf))
    aligned_hold_steps = int(source_info.get("aligned_hold_steps", 0))
    contact_present = bool(source_info.get("contact_present", False))
    source_success = bool(source_info.get("source_success", False))
    source_failure = bool(source_info.get("source_failure", False))

    alignment_ready = (
        entry_position_error <= spec.max_entry_position_error
        and entry_orientation_error <= spec.max_entry_orientation_error_rad
    )
    preconditions = {
        "entry_position_within_tolerance": bool(
            entry_position_error <= spec.max_entry_position_error
        ),
        "entry_orientation_within_tolerance": bool(
            entry_orientation_error <= spec.max_entry_orientation_error_rad
        ),
        "consecutive_ready_steps_met": bool(aligned_hold_steps >= spec.required_ready_steps),
        "contact_allowed_for_transition": bool(
            spec.allow_contact_during_transition or not contact_present
        ),
        "source_task_not_failed": bool(
            (not source_failure) if spec.require_source_task_not_failed else True
        ),
        "alignment_signal_present": bool(alignment_ready if spec.require_alignment_signal else True),
    }
    ready = all(preconditions.values())

    if ready:
        reason = "transition_ready"
    elif not preconditions["source_task_not_failed"]:
        reason = "source_task_failed"
    elif not preconditions["entry_position_within_tolerance"]:
        reason = "entry_position_not_ready"
    elif not preconditions["entry_orientation_within_tolerance"]:
        reason = "entry_orientation_not_ready"
    elif not preconditions["consecutive_ready_steps_met"]:
        reason = "ready_step_requirement_not_met"
    elif not preconditions["contact_allowed_for_transition"]:
        reason = "contact_not_allowed_for_transition"
    else:
        reason = "alignment_signal_not_ready"

    return TransitionDecision(
        transition_name=transition_input.transition_name,
        source_task=transition_input.source_task,
        target_task=transition_input.target_task,
        ready=bool(ready),
        reason=reason,
        implemented=True,
        preconditions=preconditions,
        official_metrics={
            "entry_position_error": entry_position_error,
            "entry_orientation_error_rad": entry_orientation_error,
            "aligned_hold_steps": aligned_hold_steps,
            "required_ready_steps": int(spec.required_ready_steps),
            "contact_present": bool(contact_present),
            "transition_reference_frame": str(spec.reference_frame),
        },
        debug_metrics={
            "source_success": bool(source_success),
            "source_failure": bool(source_failure),
            "relative_palm_position": source_info.get("relative_palm_position"),
            "target_offset": source_info.get("target_offset"),
            "transition_spec": spec.to_dict(),
            "source_task_config": dict(transition_input.source_task_config or {}),
            "current_step": int(transition_input.current_step),
        },
        notes=(
            "Independent transition contract. It consumes pre_grasp output signals but is not "
            "defined as an alias of pre_grasp success."
        ),
        contract_name="pre_grasp_to_stable_grasp_transition_contract",
        contract_version="v1",
    )


def pending_transition(spec: PendingTransitionSpec) -> TransitionDecision:
    """Return a placeholder transition decision without pretending it is complete."""
    return TransitionDecision(
        transition_name=spec.transition_name,
        source_task=spec.source_task,
        target_task=spec.target_task,
        ready=False,
        reason="pending_definition",
        implemented=False,
        preconditions={"pending_definition": True},
        official_metrics={},
        debug_metrics={},
        notes=spec.notes,
        contract_name="pending_transition_contract",
        contract_version="v1",
    )


__all__ = [
    "TransitionDecision",
    "TransitionEvaluationInput",
    "PreGraspToStableGraspTransitionSpec",
    "PendingTransitionSpec",
    "build_pre_grasp_to_stable_grasp_input",
    "evaluate_pre_grasp_to_stable_grasp",
    "pending_transition",
]
