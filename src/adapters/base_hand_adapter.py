"""Hand-agnostic adapter interfaces for task logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

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
class PoseState:
    """Pose payload used by hand-agnostic task logic."""

    position: np.ndarray
    quaternion: np.ndarray

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": _serialize_value(self.position),
            "quaternion": _serialize_value(self.quaternion),
        }


@dataclass
class RelativePoseState:
    """Relative palm/object pose expressed in task space."""

    position: np.ndarray
    distance: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": _serialize_value(self.position),
            "distance": float(self.distance),
        }


@dataclass
class JointStateSummary:
    """
    Task-relevant joint state.

    `positions` and `velocities` are the abstract task-level quantities.
    `backend_joint_names` is backend-derived debugging metadata and should not be treated
    as part of a hand-agnostic task contract.
    """

    positions: np.ndarray
    velocities: np.ndarray
    backend_joint_names: List[str]
    backend_note: str = ""

    def to_task_dict(self) -> Dict[str, Any]:
        return {
            "positions": _serialize_value(self.positions),
            "velocities": _serialize_value(self.velocities),
        }

    def to_debug_dict(self) -> Dict[str, Any]:
        return {
            "backend_joint_names": list(self.backend_joint_names),
            "backend_note": str(self.backend_note),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_task_dict(),
            **self.to_debug_dict(),
        }


@dataclass
class ContactSummary:
    """
    Task-oriented contact summary.

    `support_regions`, `support_region_count`, and `sustained_contact_steps` are task-level
    abstract quantities. `backend_*` fields are backend-derived approximations and should not
    be promoted into a hand-agnostic task contract without an explicit replacement decision.
    """

    has_contact: bool
    support_regions: List[str]
    support_region_count: int
    sustained_contact_steps: int
    backend_has_palm_contact: bool = False
    backend_has_thumb_contact: bool = False
    backend_contact_count: int = 0
    backend_contact_body_names: List[str] = None
    backend_group_labels: List[str] = None
    backend_is_grasp_contact: bool = False
    backend_grasp_contact_steps: int = 0
    backend_note: str = ""

    def __post_init__(self) -> None:
        self.backend_contact_body_names = list(self.backend_contact_body_names or [])
        self.backend_group_labels = list(self.backend_group_labels or [])

    def to_task_dict(self) -> Dict[str, Any]:
        return {
            "has_contact": bool(self.has_contact),
            "support_regions": list(self.support_regions),
            "support_region_count": int(self.support_region_count),
            "sustained_contact_steps": int(self.sustained_contact_steps),
        }

    def to_debug_dict(self) -> Dict[str, Any]:
        return {
            "backend_has_palm_contact": bool(self.backend_has_palm_contact),
            "backend_has_thumb_contact": bool(self.backend_has_thumb_contact),
            "backend_contact_count": int(self.backend_contact_count),
            "backend_contact_body_names": list(self.backend_contact_body_names),
            "backend_group_labels": list(self.backend_group_labels),
            "backend_is_grasp_contact": bool(self.backend_is_grasp_contact),
            "backend_grasp_contact_steps": int(self.backend_grasp_contact_steps),
            "backend_note": str(self.backend_note),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_task_dict(),
            **self.to_debug_dict(),
        }


@dataclass
class HandClosureSummary:
    """
    Task-oriented closure summary.

    `closure_metric` is the abstract task-level quantity. `backend_component_*` fields are
    backend-derived approximations and should not be treated as a universal hand definition.
    """

    closure_metric: float
    backend_component_metrics: Dict[str, float]
    backend_component_labels: List[str]
    backend_component_joint_names: List[str]
    backend_note: str = ""

    def to_task_dict(self) -> Dict[str, Any]:
        return {
            "closure_metric": float(self.closure_metric),
        }

    def to_debug_dict(self) -> Dict[str, Any]:
        return {
            "backend_component_metrics": {
                key: float(value) for key, value in self.backend_component_metrics.items()
            },
            "backend_component_labels": list(self.backend_component_labels),
            "backend_component_joint_names": list(self.backend_component_joint_names),
            "backend_note": str(self.backend_note),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_task_dict(),
            **self.to_debug_dict(),
        }


class BaseHandAdapter(ABC):
    """Backend adapter used by hand-agnostic task logic."""

    @abstractmethod
    def get_backend_type(self) -> str:
        """Return the backend identifier, for example shadow_backend."""

    @abstractmethod
    def get_model_family(self) -> str:
        """Return the model-family label, for example shadow_hand."""

    @abstractmethod
    def get_palm_pose(self) -> PoseState:
        """Return the task-relevant palm pose."""

    @abstractmethod
    def get_object_pose(self) -> PoseState:
        """Return the current object pose."""

    @abstractmethod
    def get_relative_palm_to_object(self) -> RelativePoseState:
        """Return the palm pose relative to the object."""

    @abstractmethod
    def get_object_velocity(self) -> np.ndarray:
        """Return the current object linear velocity."""

    @abstractmethod
    def get_contact_summary(self) -> ContactSummary:
        """Return task-oriented contact information."""

    @abstractmethod
    def get_hand_closure(self) -> HandClosureSummary:
        """Return a backend-specific closure metric."""

    @abstractmethod
    def get_task_joint_state(self) -> JointStateSummary:
        """Return joint state relevant to task logic."""

    def get_backend_metadata(self) -> Dict[str, Any]:
        """Return backend metadata for reports and debugging."""
        return {
            "backend_type": self.get_backend_type(),
            "model_family": self.get_model_family(),
        }

    def get_semantic_contract(self) -> Dict[str, Any]:
        """Describe which adapter fields are task-level abstractions vs backend approximations."""
        return {
            "contact_summary": {
                "task_level_fields": [
                    "has_contact",
                    "support_regions",
                    "support_region_count",
                    "sustained_contact_steps",
                ],
                "backend_approximation_fields": [
                    "backend_has_palm_contact",
                    "backend_has_thumb_contact",
                    "backend_contact_count",
                    "backend_contact_body_names",
                    "backend_group_labels",
                    "backend_is_grasp_contact",
                    "backend_grasp_contact_steps",
                    "backend_note",
                ],
            },
            "hand_closure": {
                "task_level_fields": ["closure_metric"],
                "backend_approximation_fields": [
                    "backend_component_metrics",
                    "backend_component_labels",
                    "backend_component_joint_names",
                    "backend_note",
                ],
            },
            "task_joint_state": {
                "task_level_fields": ["positions", "velocities"],
                "backend_approximation_fields": [
                    "backend_joint_names",
                    "backend_note",
                ],
            },
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Return a backend snapshot with task-level and debug-level sections."""
        contact_summary = self.get_contact_summary()
        hand_closure = self.get_hand_closure()
        joint_state = self.get_task_joint_state()
        return {
            "backend": self.get_backend_metadata(),
            "semantic_contract": self.get_semantic_contract(),
            "palm_pose": self.get_palm_pose().to_dict(),
            "object_pose": self.get_object_pose().to_dict(),
            "relative_palm_to_object": self.get_relative_palm_to_object().to_dict(),
            "object_velocity": _serialize_value(self.get_object_velocity()),
            "contact_summary_task": contact_summary.to_task_dict(),
            "contact_summary_debug": contact_summary.to_debug_dict(),
            "hand_closure_task": hand_closure.to_task_dict(),
            "hand_closure_debug": hand_closure.to_debug_dict(),
            "joint_state_task": joint_state.to_task_dict(),
            "joint_state_debug": joint_state.to_debug_dict(),
        }


__all__ = [
    "BaseHandAdapter",
    "PoseState",
    "RelativePoseState",
    "JointStateSummary",
    "ContactSummary",
    "HandClosureSummary",
]
