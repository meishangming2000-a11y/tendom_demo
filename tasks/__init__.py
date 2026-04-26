"""Task-oriented interfaces for structured manipulation stages."""

from .base_task import BaseTask
from .behavior_audit import (
    TemporaryStableGraspCollectionGate,
    audit_temporary_collection_readiness,
    build_stable_grasp_behavior_audit,
    classify_stable_grasp_failure_mode,
)
from .checks import BaseTaskChecker, TaskCheckInput, TaskCheckResult
from .episode_evaluation import EpisodeEvaluationResult, build_report_payload
from .lift_and_hold import LiftAndHoldTask
from .pre_grasp import PreGraspTask
from .stable_grasp import (
    StableGraspEntrySnapshot,
    StableGraspTask,
    create_stable_grasp_entry_snapshot,
)
from .transitions import (
    TransitionDecision,
    TransitionEvaluationInput,
    build_pre_grasp_to_stable_grasp_input,
)


TASK_REGISTRY = {
    "pre_grasp": PreGraspTask,
    "stable_grasp": StableGraspTask,
    "lift_and_hold": LiftAndHoldTask,
}


def create_task(task_name, **kwargs):
    """Create a task instance by name."""
    if task_name is None:
        return None

    normalized_name = str(task_name).strip().lower()
    if normalized_name not in TASK_REGISTRY:
        raise ValueError(
            f"Unknown task '{task_name}'. Available tasks: {sorted(TASK_REGISTRY.keys())}"
        )
    return TASK_REGISTRY[normalized_name](**kwargs)


__all__ = [
    "BaseTask",
    "TemporaryStableGraspCollectionGate",
    "audit_temporary_collection_readiness",
    "build_stable_grasp_behavior_audit",
    "classify_stable_grasp_failure_mode",
    "PreGraspTask",
    "StableGraspTask",
    "StableGraspEntrySnapshot",
    "create_stable_grasp_entry_snapshot",
    "LiftAndHoldTask",
    "BaseTaskChecker",
    "TaskCheckInput",
    "TaskCheckResult",
    "EpisodeEvaluationResult",
    "TransitionDecision",
    "TransitionEvaluationInput",
    "build_pre_grasp_to_stable_grasp_input",
    "build_report_payload",
    "TASK_REGISTRY",
    "create_task",
]
