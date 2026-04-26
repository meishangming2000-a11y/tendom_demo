"""Stage-2 stable-grasp task with a minimal evaluation contract and Shadow temporary backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from src.adapters.base_hand_adapter import BaseHandAdapter

from .base_task import BaseTask
from .checks import BaseTaskChecker, TaskCheckInput, TaskCheckResult
from .transitions import PendingTransitionSpec, pending_transition


def _remap_threshold_aliases(values: Optional[Dict[str, Any]], alias_map: Dict[str, str]) -> Dict[str, Any]:
    """Normalize historical threshold keys to the current task-level contract names."""
    normalized = dict(values or {})
    for legacy_key, contract_key in alias_map.items():
        if legacy_key in normalized and contract_key not in normalized:
            normalized[contract_key] = normalized.pop(legacy_key)
    return normalized


@dataclass
class StableGraspSuccessThresholds:
    """Task-level success thresholds for the stable_grasp evaluation contract."""

    required_hold_steps: int = 50
    min_support_regions: int = 3
    min_closure_metric: float = 0.45
    max_relative_palm_object_distance: float = 0.12
    max_object_displacement_from_entry: float = 0.10
    max_object_vertical_drop_from_entry: float = 0.06

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_hold_steps": int(self.required_hold_steps),
            "min_support_regions": int(self.min_support_regions),
            "min_closure_metric": float(self.min_closure_metric),
            "max_relative_palm_object_distance": float(
                self.max_relative_palm_object_distance
            ),
            "max_object_displacement_from_entry": float(
                self.max_object_displacement_from_entry
            ),
            "max_object_vertical_drop_from_entry": float(
                self.max_object_vertical_drop_from_entry
            ),
        }


@dataclass
class StableGraspFailureThresholds:
    """Task-level failure thresholds for the stable_grasp evaluation contract."""

    max_relative_palm_object_distance: float = 0.18
    max_object_displacement_from_entry: float = 0.16
    max_object_vertical_drop_from_entry: float = 0.10
    fail_on_object_floor_contact: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_relative_palm_object_distance": float(
                self.max_relative_palm_object_distance
            ),
            "max_object_displacement_from_entry": float(
                self.max_object_displacement_from_entry
            ),
            "max_object_vertical_drop_from_entry": float(
                self.max_object_vertical_drop_from_entry
            ),
            "fail_on_object_floor_contact": bool(self.fail_on_object_floor_contact),
        }


@dataclass
class StableGraspTransitionThresholds:
    """Reserved downstream transition thresholds for later task chaining."""

    ready_for_lift_hold_steps: int = 50
    fallback_on_failure: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready_for_lift_hold_steps": int(self.ready_for_lift_hold_steps),
            "fallback_on_failure": bool(self.fallback_on_failure),
        }


@dataclass
class StableGraspTaskSpec:
    """Config bundle for the stable_grasp task."""

    success_thresholds: StableGraspSuccessThresholds
    failure_thresholds: StableGraspFailureThresholds
    transition_thresholds: StableGraspTransitionThresholds
    backend_assumptions: Dict[str, Any]

    @classmethod
    def from_kwargs(
        cls,
        success_thresholds: Optional[Dict[str, Any]] = None,
        failure_thresholds: Optional[Dict[str, Any]] = None,
        transition_thresholds: Optional[Dict[str, Any]] = None,
        backend_assumptions: Optional[Dict[str, Any]] = None,
        required_contact_steps: Optional[int] = None,
    ) -> "StableGraspTaskSpec":
        success_aliases = {
            "min_finger_groups_with_contact": "min_support_regions",
            "max_palm_object_distance": "max_relative_palm_object_distance",
            "max_object_displacement": "max_object_displacement_from_entry",
            "max_object_vertical_drop": "max_object_vertical_drop_from_entry",
        }
        failure_aliases = {
            "max_palm_object_distance": "max_relative_palm_object_distance",
            "max_object_displacement": "max_object_displacement_from_entry",
            "max_object_vertical_drop": "max_object_vertical_drop_from_entry",
        }

        resolved_success = _remap_threshold_aliases(success_thresholds, success_aliases)
        resolved_failure = _remap_threshold_aliases(failure_thresholds, failure_aliases)
        if required_contact_steps is not None and "required_hold_steps" not in resolved_success:
            resolved_success["required_hold_steps"] = int(required_contact_steps)

        success = StableGraspSuccessThresholds(**resolved_success)
        transition = StableGraspTransitionThresholds(
            **(
                transition_thresholds
                or {"ready_for_lift_hold_steps": int(success.required_hold_steps)}
            )
        )
        failure = StableGraspFailureThresholds(**resolved_failure)
        assumptions = {
            "temporary_backend": True,
            "reference_frame": "palm_object_relation",
            "action_backend": "joint_level_temporary",
            "official_contract_scope": (
                "task-level success/failure uses abstract retention, contact-support, "
                "closure, and hold-step signals"
            ),
            "debug_backend_scope": (
                "thumb/palm contact detail, contact-body names, closure grouping, and joint "
                "labels remain backend-derived approximations"
            ),
            "notes": (
                "This stable_grasp v1 implementation uses a temporary Shadow backend for "
                "contact and closure approximations. Replace or recalibrate for other hands."
            ),
        }
        assumptions.update(dict(backend_assumptions or {}))
        return cls(
            success_thresholds=success,
            failure_thresholds=failure,
            transition_thresholds=transition,
            backend_assumptions=assumptions,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_thresholds": self.success_thresholds.to_dict(),
            "failure_thresholds": self.failure_thresholds.to_dict(),
            "transition_thresholds": self.transition_thresholds.to_dict(),
            "backend_assumptions": dict(self.backend_assumptions),
        }


@dataclass
class StableGraspEntrySnapshot:
    """Reference state captured at stable_grasp entry for episode-level evaluation."""

    object_pose: Dict[str, Any]
    palm_pose: Dict[str, Any]
    relative_palm_object_relation: Dict[str, Any]
    entry_step_index: int
    entry_time_seconds: float
    entry_source: str
    backend_type: str
    notes: str = ""
    fallback_created: bool = False

    @classmethod
    def capture(
        cls,
        adapter: BaseHandAdapter,
        step_index: int,
        control_timestep: float,
        entry_source: str,
        notes: str = "",
        fallback_created: bool = False,
    ) -> "StableGraspEntrySnapshot":
        """Capture the current backend state as a stable_grasp entry snapshot."""
        object_pose = adapter.get_object_pose().to_dict()
        palm_pose = adapter.get_palm_pose().to_dict()
        relative_relation = adapter.get_relative_palm_to_object().to_dict()
        return cls(
            object_pose=object_pose,
            palm_pose=palm_pose,
            relative_palm_object_relation=relative_relation,
            entry_step_index=int(step_index),
            entry_time_seconds=float(step_index * float(control_timestep)),
            entry_source=str(entry_source),
            backend_type=adapter.get_backend_type(),
            notes=str(notes),
            fallback_created=bool(fallback_created),
        )

    @property
    def object_position(self) -> np.ndarray:
        return np.asarray(self.object_pose.get("position", [0.0, 0.0, 0.0]), dtype=np.float32)

    @property
    def object_height(self) -> float:
        return float(self.object_position[2])

    @property
    def relative_distance(self) -> float:
        return float(self.relative_palm_object_relation.get("distance", 0.0))

    def to_payload(self) -> Dict[str, Any]:
        """Return the JSON-friendly entry-snapshot payload."""
        return {
            "object_pose": dict(self.object_pose),
            "palm_pose": dict(self.palm_pose),
            "relative_palm_object_relation": dict(self.relative_palm_object_relation),
            "entry_step_index": int(self.entry_step_index),
            "entry_time_seconds": float(self.entry_time_seconds),
            "entry_source": str(self.entry_source),
            "backend_type": str(self.backend_type),
            "notes": str(self.notes),
            "fallback_created": bool(self.fallback_created),
        }


def create_stable_grasp_entry_snapshot(
    adapter: BaseHandAdapter,
    step_index: int,
    control_timestep: float,
    entry_source: str,
    notes: str = "",
    fallback_created: bool = False,
) -> StableGraspEntrySnapshot:
    """
    Canonical helper for rollout-time stable_grasp entry snapshots.

    The intended owner is the rollout evaluator or task-handoff path after a
    transition becomes ready. Transition evaluators only decide readiness and
    should not mutate task state directly. The stable_grasp checker may call
    this helper only as a fallback when no explicit entry snapshot was attached.
    """
    return StableGraspEntrySnapshot.capture(
        adapter=adapter,
        step_index=int(step_index),
        control_timestep=float(control_timestep),
        entry_source=str(entry_source),
        notes=str(notes),
        fallback_created=bool(fallback_created),
    )


class ShadowStableGraspChecker(BaseTaskChecker):
    """Temporary Shadow backend checker for the stable_grasp task contract."""

    checker_name = "shadow_stable_grasp_checker_v1"

    def __init__(self, spec: StableGraspTaskSpec):
        self.spec = spec
        self._hold_counter = 0
        self._last_processed_step = -1
        self._entry_snapshot: Optional[StableGraspEntrySnapshot] = None

    def reset(
        self,
        adapter: BaseHandAdapter = None,
        entry_snapshot: Optional[StableGraspEntrySnapshot] = None,
    ) -> None:
        self._hold_counter = 0
        self._last_processed_step = -1
        self._entry_snapshot = entry_snapshot

    def set_entry_snapshot(self, entry_snapshot: Optional[StableGraspEntrySnapshot]) -> None:
        """Set the explicit stable_grasp entry snapshot for the current episode."""
        self._entry_snapshot = entry_snapshot

    def get_entry_snapshot(self) -> Optional[StableGraspEntrySnapshot]:
        """Return the active entry snapshot if one is available."""
        return self._entry_snapshot

    def _ensure_entry_snapshot(
        self,
        adapter: BaseHandAdapter,
        current_step: int,
        control_timestep: float,
    ) -> None:
        if self._entry_snapshot is not None:
            return
        self._entry_snapshot = create_stable_grasp_entry_snapshot(
            adapter=adapter,
            step_index=int(current_step),
            control_timestep=float(control_timestep),
            entry_source="first_stable_grasp_evaluation_step_fallback",
            notes=(
                "No explicit transition entry snapshot was provided. Using the first "
                "stable_grasp evaluation step as the fallback entry reference."
            ),
            fallback_created=True,
        )

    def evaluate(self, check_input: TaskCheckInput) -> TaskCheckResult:
        adapter = check_input.adapter
        control_timestep = float(check_input.base_info.get("control_timestep", 0.0) or 0.0)
        if control_timestep <= 0.0:
            control_timestep = 0.0
        self._ensure_entry_snapshot(
            adapter=adapter,
            current_step=int(check_input.current_step),
            control_timestep=control_timestep,
        )

        palm_pose = adapter.get_palm_pose()
        object_pose = adapter.get_object_pose()
        relative_pose = adapter.get_relative_palm_to_object()
        object_velocity = adapter.get_object_velocity()
        contact_summary = adapter.get_contact_summary()
        closure_summary = adapter.get_hand_closure()
        joint_state = adapter.get_task_joint_state()
        entry_snapshot = self._entry_snapshot

        object_displacement = float(
            np.linalg.norm(object_pose.position - entry_snapshot.object_position)
        )
        object_vertical_drop = float(
            max(0.0, float(entry_snapshot.object_height) - float(object_pose.position[2]))
        )
        object_velocity_norm = float(np.linalg.norm(object_velocity))
        base_info = dict(check_input.base_info or {})

        retained_in_workspace = (
            relative_pose.distance
            <= self.spec.success_thresholds.max_relative_palm_object_distance
            and not bool(base_info.get("object_on_floor", False))
        )
        contact_support_ready = (
            contact_summary.has_contact
            and contact_summary.support_region_count
            >= self.spec.success_thresholds.min_support_regions
        )
        closure_ready = (
            closure_summary.closure_metric >= self.spec.success_thresholds.min_closure_metric
        )
        stable_step = (
            retained_in_workspace
            and contact_support_ready
            and closure_ready
            and object_displacement
            <= self.spec.success_thresholds.max_object_displacement_from_entry
            and object_vertical_drop
            <= self.spec.success_thresholds.max_object_vertical_drop_from_entry
        )

        if check_input.current_step != self._last_processed_step:
            self._hold_counter = self._hold_counter + 1 if stable_step else 0
            self._last_processed_step = check_input.current_step

        object_on_floor = bool(base_info.get("object_on_floor", False))
        distance_limit_exceeded = (
            relative_pose.distance
            > self.spec.failure_thresholds.max_relative_palm_object_distance
        )
        displacement_limit_exceeded = (
            object_displacement
            > self.spec.failure_thresholds.max_object_displacement_from_entry
        )
        vertical_drop_limit_exceeded = (
            object_vertical_drop
            > self.spec.failure_thresholds.max_object_vertical_drop_from_entry
        )
        retention_failure = bool(
            distance_limit_exceeded
            or displacement_limit_exceeded
            or vertical_drop_limit_exceeded
        )
        failure = bool(
            (
                self.spec.failure_thresholds.fail_on_object_floor_contact
                and object_on_floor
            )
            or retention_failure
        )
        hold_requirement_met = (
            self._hold_counter >= self.spec.success_thresholds.required_hold_steps
        )
        success = bool(not failure and stable_step and hold_requirement_met)

        if success:
            reason = "stable_grasp_ready_for_lift_transition"
        elif failure:
            if object_on_floor:
                reason = "object_on_floor"
            elif distance_limit_exceeded:
                reason = "object_exited_workspace"
            elif vertical_drop_limit_exceeded:
                reason = "object_vertical_drop_limit_exceeded"
            else:
                reason = "object_displacement_limit_exceeded"
        elif not retained_in_workspace:
            reason = "workspace_retention_not_ready"
        elif not contact_support_ready:
            reason = "contact_support_not_ready"
        elif not closure_ready:
            reason = "closure_not_ready"
        else:
            reason = "building_required_hold_steps"

        official_flags = {
            "retained_in_workspace": bool(retained_in_workspace),
            "contact_support_ready": bool(contact_support_ready),
            "closure_ready": bool(closure_ready),
            "stable_step": bool(stable_step),
            "hold_requirement_met": bool(hold_requirement_met),
            "object_on_floor": bool(object_on_floor),
            "retention_failure": bool(retention_failure),
            "lift_not_required": True,
        }
        official_metrics = {
            "hold_steps": int(self._hold_counter),
            "required_hold_steps": int(self.spec.success_thresholds.required_hold_steps),
            "support_region_count": int(contact_summary.support_region_count),
            "support_regions": list(contact_summary.support_regions),
            "sustained_contact_steps": int(contact_summary.sustained_contact_steps),
            "closure_metric": float(closure_summary.closure_metric),
            "relative_palm_object_distance": float(relative_pose.distance),
            "relative_palm_object_position": relative_pose.position.astype(np.float32),
            "relative_palm_object_distance_at_entry": float(entry_snapshot.relative_distance),
            "object_displacement_from_entry": float(object_displacement),
            "object_vertical_drop_from_entry": float(object_vertical_drop),
            "contact_summary": contact_summary.to_task_dict(),
            "closure_summary": closure_summary.to_task_dict(),
            "relative_palm_object_relation": relative_pose.to_dict(),
        }
        debug_metrics = {
            "backend_contact_summary": contact_summary.to_debug_dict(),
            "backend_closure_summary": closure_summary.to_debug_dict(),
            "joint_state_task": joint_state.to_task_dict(),
            "joint_state_debug": joint_state.to_debug_dict(),
            "palm_pose": palm_pose.to_dict(),
            "object_pose": object_pose.to_dict(),
            "object_velocity": object_velocity.astype(np.float32),
            "object_velocity_norm": float(object_velocity_norm),
            "backend_contact_support_approximation": {
                "backend_has_palm_contact": bool(contact_summary.backend_has_palm_contact),
                "backend_has_thumb_contact": bool(contact_summary.backend_has_thumb_contact),
                "backend_is_grasp_contact": bool(contact_summary.backend_is_grasp_contact),
            },
            "entry_snapshot": entry_snapshot.to_payload(),
        }

        return TaskCheckResult(
            success=bool(success),
            failure=bool(failure),
            reason=reason,
            official_flags=official_flags,
            official_metrics=official_metrics,
            debug_metrics=debug_metrics,
            backend_type=adapter.get_backend_type(),
            checker_name=self.checker_name,
            notes=(
                "Temporary Shadow backend implementation. Official contract fields are task-level; "
                "backend debug fields still rely on Shadow contact and closure approximations."
            ),
            contract_name="stable_grasp_evaluation_contract",
            contract_version="v1",
        )


class StableGraspTask(BaseTask):
    """Form a lift-ready grasp and keep it stable without requiring lift yet."""

    task_name = "stable_grasp"

    def __init__(
        self,
        success_thresholds: Optional[Dict[str, Any]] = None,
        failure_thresholds: Optional[Dict[str, Any]] = None,
        transition_thresholds: Optional[Dict[str, Any]] = None,
        backend_assumptions: Optional[Dict[str, Any]] = None,
        required_contact_steps: Optional[int] = None,
        observation_mode: Optional[str] = None,
    ):
        super().__init__(observation_mode=observation_mode)
        self.spec = StableGraspTaskSpec.from_kwargs(
            success_thresholds=success_thresholds,
            failure_thresholds=failure_thresholds,
            transition_thresholds=transition_thresholds,
            backend_assumptions=backend_assumptions,
            required_contact_steps=required_contact_steps,
        )
        self.checker = ShadowStableGraspChecker(self.spec)
        self._last_result: Optional[TaskCheckResult] = None
        self._last_result_step = -1
        self._pending_entry_snapshot: Optional[StableGraspEntrySnapshot] = None

    def reset_task(self, env) -> None:
        self._last_result = None
        self._last_result_step = -1
        self.checker.reset(
            adapter=env.get_hand_adapter(),
            entry_snapshot=self._pending_entry_snapshot,
        )
        self._pending_entry_snapshot = None

    def set_entry_snapshot(self, entry_snapshot: Optional[StableGraspEntrySnapshot]) -> None:
        """Attach an explicit entry snapshot before stable_grasp evaluation starts."""
        self._pending_entry_snapshot = entry_snapshot
        self.checker.set_entry_snapshot(entry_snapshot)

    def get_entry_snapshot(self) -> Optional[StableGraspEntrySnapshot]:
        """Return the entry snapshot currently attached to the task."""
        return self.checker.get_entry_snapshot()

    def get_action_spec(self, env) -> Dict[str, Any]:
        return {
            "control_level": "joint",
            "shape": (env.nu,),
            "normalized": True,
            "range": [-1.0, 1.0],
            "notes": (
                "Temporary joint-level action interface for structure validation. Future "
                "backends may replace this with tendon-level or motor-level actions."
            ),
        }

    def get_task_config(self) -> Dict[str, Any]:
        return self.spec.to_dict()

    def get_evaluation_contract(self) -> Dict[str, Any]:
        return {
            "contract_name": "stable_grasp_evaluation_contract",
            "contract_version": "v1",
            "task_goal": "form_lift_ready_grasp_and_hold_without_lift",
            "official_success_criteria": [
                "retained_in_workspace",
                "contact_support_ready",
                "closure_ready",
                "stable_step_for_required_hold_steps",
            ],
            "official_failure_criteria": [
                "object_on_floor",
                "retention_failure",
            ],
            "official_metrics": [
                "hold_steps",
                "required_hold_steps",
                "support_region_count",
                "support_regions",
                "sustained_contact_steps",
                "closure_metric",
                "relative_palm_object_distance",
                "relative_palm_object_distance_at_entry",
                "relative_palm_object_position",
                "object_displacement_from_entry",
                "object_vertical_drop_from_entry",
                "contact_summary",
                "closure_summary",
                "relative_palm_object_relation",
            ],
            "debug_metrics": [
                "backend_contact_summary",
                "backend_closure_summary",
                "joint_state_task",
                "joint_state_debug",
                "palm_pose",
                "object_pose",
                "object_velocity",
                "object_velocity_norm",
                "backend_contact_support_approximation",
            ],
            "backend_note": (
                "This is a task-level contract. The current checker is a temporary Shadow "
                "backend implementation and should not be mistaken for a real-hand definition."
            ),
            "entry_snapshot_contract": self.get_entry_snapshot_contract(),
        }

    def get_entry_snapshot_contract(self) -> Dict[str, Any]:
        """Describe how stable_grasp reference-state metrics are anchored."""
        return {
            "contract_name": "stable_grasp_entry_snapshot_contract",
            "contract_version": "v1",
            "canonical_owner": "rollout_evaluator_or_pipeline_handoff",
            "fallback_owner": "stable_grasp_checker",
            "entry_time_definition": (
                "Canonical creation happens in the rollout evaluator or pipeline handoff layer at "
                "the pre_grasp -> stable_grasp transition-ready moment, before the first "
                "stable_grasp evaluation step. The stable_grasp checker only creates a fallback "
                "snapshot if no explicit entry snapshot was attached, and marks "
                "fallback_created=true."
            ),
            "reference_state_usage": {
                "object_displacement_from_entry": "current object position minus entry object position",
                "object_vertical_drop_from_entry": "entry object height minus current object height",
                "relative_palm_object_distance": "instantaneous current task metric",
                "relative_palm_object_distance_at_entry": "entry snapshot context metric",
            },
            "entry_source_values": [
                "pre_grasp_to_stable_grasp_transition_ready",
                "first_stable_grasp_evaluation_step_fallback",
            ],
            "required_fields": [
                "object_pose",
                "palm_pose",
                "relative_palm_object_relation",
                "entry_step_index",
                "entry_time_seconds",
                "entry_source",
                "backend_type",
            ],
        }

    def get_task_spec(self) -> Dict[str, Any]:
        return {
            **self.spec.to_dict(),
            "task_goal": "form_lift_ready_grasp_and_hold_without_lift",
            "temporary_backend": "shadow_backend",
            "evaluation_contract": self.get_evaluation_contract(),
            "entry_snapshot_contract": self.get_entry_snapshot_contract(),
        }

    def evaluate_state(self, env, info: Optional[Dict[str, Any]] = None):
        if self._last_result is not None and env.current_step == self._last_result_step:
            return self._last_result

        result = self.checker.evaluate(
            TaskCheckInput(
                task_name=self.get_name(),
                observation=self.get_observation(env),
                base_info=dict(info or env._build_base_info()),
                task_config=self.get_task_config(),
                adapter=env.get_hand_adapter(),
                current_step=int(env.current_step),
            )
        )
        self._last_result = result
        self._last_result_step = int(env.current_step)
        return result

    def check_success(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        return bool(self.evaluate_state(env, info=info).success)

    def check_failure(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        return bool(self.evaluate_state(env, info=info).failure)

    def get_reward(self, env, action: np.ndarray, info: Optional[Dict[str, Any]] = None) -> float:
        result = self.evaluate_state(env, info=info)
        reward = float(env.compute_default_reward(action, info=info))
        if result.flags.get("contact_support_ready", False):
            reward += 0.5
        if result.flags.get("closure_ready", False):
            reward += 0.5
        reward += 0.05 * float(result.metrics.get("hold_steps", 0))
        if result.failure:
            reward -= 2.0
        return float(reward)

    def get_info(self, env, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = self.evaluate_state(env, info=info)
        lift_transition = pending_transition(
            PendingTransitionSpec(
                transition_name="stable_grasp_to_lift_and_hold",
                source_task="stable_grasp",
                target_task="lift_and_hold",
                notes=(
                    "Reserved interface only. Full stable_grasp -> lift_and_hold transition "
                    "still needs a dedicated task definition and lift-aware checks."
                ),
            )
        )
        fallback_transition = pending_transition(
            PendingTransitionSpec(
                transition_name="stable_grasp_to_fallback_or_reset",
                source_task="stable_grasp",
                target_task="fallback_or_reset",
                notes=(
                    "Reserved interface only. Failure recovery policy is not yet promoted into "
                    "a maintained state machine."
                ),
            )
        )

        return {
            "task_reference_frame": "palm_object_relation",
            "task_control_level": "joint",
            "task_goal": "form_lift_ready_grasp_and_hold_without_lift",
            "stable_grasp_task_config": self.get_task_config(),
            "stable_grasp_task_spec": self.get_task_spec(),
            "stable_grasp_evaluation_contract": self.get_evaluation_contract(),
            "stable_grasp_entry_snapshot_contract": self.get_entry_snapshot_contract(),
            "stable_grasp_entry_snapshot": (
                self.get_entry_snapshot().to_payload() if self.get_entry_snapshot() else {}
            ),
            "stable_grasp_hand_adapter_semantic_contract": (
                env.get_hand_adapter().get_semantic_contract()
            ),
            "stable_grasp_backend_metadata": env.get_hand_adapter().get_backend_metadata(),
            "stable_grasp_evaluation": result.to_payload(),
            "stable_to_lift_transition": lift_transition.to_payload(),
            "stable_to_fallback_transition": fallback_transition.to_payload(),
            "task_status": "stable_grasp_eval_contract_v1_shadow_backend_temporary",
            **result.to_dict(prefix="stable_grasp"),
            **lift_transition.to_dict(prefix="stable_to_lift_transition"),
            **fallback_transition.to_dict(prefix="stable_to_fallback_transition"),
        }
