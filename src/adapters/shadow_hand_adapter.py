"""Temporary Shadow backend adapter for hand-agnostic task logic."""

from __future__ import annotations

from typing import Dict, List

import mujoco
import numpy as np

from .base_hand_adapter import (
    BaseHandAdapter,
    ContactSummary,
    HandClosureSummary,
    JointStateSummary,
    PoseState,
    RelativePoseState,
)


class ShadowHandAdapter(BaseHandAdapter):
    """Temporary Shadow backend used to validate task software structure."""

    backend_type = "shadow_backend"
    model_family = "shadow_hand"
    temporary_note = (
        "Temporary Shadow backend. Contact grouping, closure metrics, and thresholds are "
        "backend-specific approximations that should be recalibrated for other hands."
    )

    def __init__(self, env):
        self.env = env
        self._hand_joint_entries = self._collect_hand_joint_entries()
        self._closure_joint_groups = self._build_closure_joint_groups()

    def _collect_hand_joint_entries(self) -> List[Dict[str, object]]:
        """Collect scalar hand-joint entries without leaking them to task logic."""
        entries = []
        for joint_id in range(self.env.model.njnt):
            joint_name = mujoco.mj_id2name(self.env.model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
            if not joint_name or not joint_name.startswith("rh_"):
                continue

            qpos_adr = int(self.env.model.jnt_qposadr[joint_id])
            dof_adr = int(self.env.model.jnt_dofadr[joint_id])
            joint_range = self.env.model.jnt_range[joint_id].copy()
            entries.append(
                {
                    "joint_id": joint_id,
                    "joint_name": joint_name,
                    "qpos_adr": qpos_adr,
                    "dof_adr": dof_adr,
                    "range": joint_range,
                }
            )
        return entries

    def _build_closure_joint_groups(self) -> Dict[str, List[Dict[str, object]]]:
        """Map Shadow joints to temporary backend closure components."""
        suffix_map = {
            "thumb": ("THJ4", "THJ1"),
            "index": ("FFJ3", "FFJ2", "FFJ1"),
            "middle": ("MFJ3", "MFJ2", "MFJ1"),
            "ring": ("RFJ3", "RFJ2", "RFJ1"),
            "little": ("LFJ3", "LFJ2", "LFJ1"),
        }
        groups: Dict[str, List[Dict[str, object]]] = {name: [] for name in suffix_map}
        for entry in self._hand_joint_entries:
            joint_name = str(entry["joint_name"])
            for group_name, suffixes in suffix_map.items():
                if any(joint_name.endswith(suffix) for suffix in suffixes):
                    groups[group_name].append(entry)
        return groups

    @staticmethod
    def _normalized_joint_position(position: float, joint_range: np.ndarray) -> float:
        """Map a joint position into [0, 1] using the declared joint range."""
        lower = float(joint_range[0])
        upper = float(joint_range[1])
        if abs(upper - lower) < 1e-8:
            return 0.0
        normalized = (float(position) - lower) / (upper - lower)
        return float(np.clip(normalized, 0.0, 1.0))

    def get_backend_type(self) -> str:
        return self.backend_type

    def get_model_family(self) -> str:
        return self.model_family

    def get_palm_pose(self) -> PoseState:
        return PoseState(
            position=self.env._get_palm_reference_position().astype(np.float32),
            quaternion=self.env._get_hand_orientation().astype(np.float32),
        )

    def get_object_pose(self) -> PoseState:
        return PoseState(
            position=self.env._get_object_position().astype(np.float32),
            quaternion=self.env._get_object_orientation().astype(np.float32),
        )

    def get_relative_palm_to_object(self) -> RelativePoseState:
        palm_pose = self.get_palm_pose()
        object_pose = self.get_object_pose()
        relative_position = palm_pose.position - object_pose.position
        return RelativePoseState(
            position=relative_position.astype(np.float32),
            distance=float(np.linalg.norm(relative_position)),
        )

    def get_object_velocity(self) -> np.ndarray:
        return self.env._get_object_velocity().astype(np.float32)

    def get_contact_summary(self) -> ContactSummary:
        contact_state = self.env._get_contact_state()
        support_regions = list(contact_state["finger_groups"])
        return ContactSummary(
            has_contact=bool(contact_state["has_valid_contact"]),
            support_regions=support_regions,
            support_region_count=len(support_regions),
            sustained_contact_steps=int(getattr(self.env, "contact_duration", 0)),
            backend_has_palm_contact=bool(contact_state["has_palm_contact"]),
            backend_has_thumb_contact=bool(contact_state["has_thumb_contact"]),
            backend_contact_count=len(contact_state["contact_body_names"]),
            backend_contact_body_names=list(contact_state["contact_body_names"]),
            backend_group_labels=support_regions,
            backend_is_grasp_contact=bool(contact_state["is_grasp_contact"]),
            backend_grasp_contact_steps=int(getattr(self.env, "grasp_contact_duration", 0)),
            backend_note=(
                "Support regions are approximated from Shadow finger-group contacts. "
                "Replace this grouping for other backends."
            ),
        )

    def get_hand_closure(self) -> HandClosureSummary:
        per_group: Dict[str, float] = {}
        active_joint_names: List[str] = []

        for group_name, entries in self._closure_joint_groups.items():
            if not entries:
                per_group[group_name] = 0.0
                continue

            group_values = []
            for entry in entries:
                qpos_adr = int(entry["qpos_adr"])
                group_values.append(
                    self._normalized_joint_position(
                        self.env.data.qpos[qpos_adr],
                        np.asarray(entry["range"], dtype=np.float32),
                    )
                )
                active_joint_names.append(str(entry["joint_name"]))
            per_group[group_name] = float(np.mean(group_values))

        closure_metric = float(np.mean(list(per_group.values()))) if per_group else 0.0
        return HandClosureSummary(
            closure_metric=closure_metric,
            backend_component_metrics=per_group,
            backend_component_labels=sorted(per_group.keys()),
            backend_component_joint_names=active_joint_names,
            backend_note=(
                "Temporary Shadow closure metric uses normalized joint-range flexion across "
                "selected finger joints. Replace for non-Shadow embodiments."
            ),
        )

    def get_task_joint_state(self) -> JointStateSummary:
        positions = []
        velocities = []
        joint_names = []
        for entry in self._hand_joint_entries:
            joint_names.append(str(entry["joint_name"]))
            positions.append(float(self.env.data.qpos[int(entry["qpos_adr"])]))
            velocities.append(float(self.env.data.qvel[int(entry["dof_adr"])]))

        return JointStateSummary(
            positions=np.asarray(positions, dtype=np.float32),
            velocities=np.asarray(velocities, dtype=np.float32),
            backend_joint_names=joint_names,
            backend_note=(
                "Joint naming and ordering are backend-derived. Only positions/velocities are "
                "part of the abstract task-level quantity."
            ),
        )

    def get_backend_metadata(self) -> Dict[str, object]:
        metadata = super().get_backend_metadata()
        metadata.update(
            {
                "temporary_backend": True,
                "backend_note": self.temporary_note,
                "closure_groups": sorted(self._closure_joint_groups.keys()),
            }
        )
        return metadata


__all__ = ["ShadowHandAdapter"]
