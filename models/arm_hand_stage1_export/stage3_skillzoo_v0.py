#!/usr/bin/env python3
"""Stage3.9 SkillZoo registry and rule-router helpers.

This module is intentionally lightweight: it does not run MuJoCo and it does
not train a model. Its job is to make Stage3 skills explicit, validate the
registry, and route a compact scene descriptor to one skill.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY = ROOT / "configs" / "stage3_skill_registry_v0.json"
DEFAULT_SCENES = ROOT / "metadata" / "stage3_skill_router_v0_sample_scenes.json"


class SkillZooError(ValueError):
    """Raised when the registry or a scene descriptor is invalid."""


@dataclass(frozen=True)
class RouteDecision:
    case_id: str
    selected_skill_id: str
    selected_status: str
    decision_reason: str
    fallback_skill_id: str | None
    confidence: float
    executable: bool
    expected_skill_id: str | None = None

    @property
    def matches_expectation(self) -> bool | None:
        if self.expected_skill_id is None:
            return None
        return self.expected_skill_id == self.selected_skill_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "selected_skill_id": self.selected_skill_id,
            "selected_status": self.selected_status,
            "decision_reason": self.decision_reason,
            "fallback_skill_id": self.fallback_skill_id,
            "confidence": self.confidence,
            "executable": self.executable,
            "expected_skill_id": self.expected_skill_id,
            "matches_expectation": self.matches_expectation,
        }


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SkillZooError(f"Invalid JSON in {path}: {exc}") from exc


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    registry = read_json(path)
    validate_registry(registry, base_dir=ROOT)
    return registry


def skill_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(skill["skill_id"]): skill for skill in registry.get("skills", [])}


def validate_registry(registry: dict[str, Any], *, base_dir: Path = ROOT) -> None:
    if registry.get("version") != "stage3_skill_registry_v0":
        raise SkillZooError("Registry version must be stage3_skill_registry_v0")
    skills = registry.get("skills")
    if not isinstance(skills, list) or not skills:
        raise SkillZooError("Registry must contain a non-empty skills list")

    required = {
        "skill_id",
        "display_name_zh",
        "status",
        "skill_type",
        "controller_type",
        "stage_source",
        "inputs",
        "outputs",
        "success_criteria",
        "entrypoints",
        "failure_reasons",
    }
    seen: set[str] = set()
    for skill in skills:
        missing = sorted(required - set(skill))
        if missing:
            raise SkillZooError(f"Skill {skill.get('skill_id', '<unknown>')} missing fields: {missing}")
        skill_id = str(skill["skill_id"])
        if skill_id in seen:
            raise SkillZooError(f"Duplicate skill_id: {skill_id}")
        seen.add(skill_id)
        if not isinstance(skill.get("inputs"), list) or not skill["inputs"]:
            raise SkillZooError(f"Skill {skill_id} must declare non-empty inputs")
        if not isinstance(skill.get("outputs"), list) or not skill["outputs"]:
            raise SkillZooError(f"Skill {skill_id} must declare non-empty outputs")
        if not isinstance(skill.get("failure_reasons"), list) or not skill["failure_reasons"]:
            raise SkillZooError(f"Skill {skill_id} must declare failure_reasons")

        if skill.get("status") == "registered_baseline":
            entrypoints = skill.get("entrypoints", {})
            for key in ("primary_report", "primary_metadata"):
                rel = entrypoints.get(key)
                if rel and not (base_dir / str(rel)).exists():
                    raise SkillZooError(f"Skill {skill_id} {key} not found: {rel}")
            smoke = entrypoints.get("smoke")
            if smoke:
                script = smoke.get("script")
                if not script or not (base_dir / str(script)).exists():
                    raise SkillZooError(f"Skill {skill_id} smoke script not found: {script}")


def load_scene_cases(path: Path = DEFAULT_SCENES) -> list[dict[str, Any]]:
    payload = read_json(path)
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SkillZooError(f"{path} must contain non-empty cases")
    for case in cases:
        validate_scene_case(case)
    return cases


def validate_scene_case(case: dict[str, Any]) -> None:
    for key in ("case_id", "task_goal", "vision", "workspace", "tactile"):
        if key not in case:
            raise SkillZooError(f"Scene case missing {key}: {case}")
    vision = case["vision"]
    tactile = case["tactile"]
    workspace = case["workspace"]
    for key in ("confidence", "estimated_pose_error_m", "occlusion"):
        if key not in vision:
            raise SkillZooError(f"Scene {case['case_id']} vision missing {key}")
    for key in ("contact_present", "slip_score", "crush_risk", "penetration_m"):
        if key not in tactile:
            raise SkillZooError(f"Scene {case['case_id']} tactile missing {key}")
    for key in ("clearance", "pinch_eligible"):
        if key not in workspace:
            raise SkillZooError(f"Scene {case['case_id']} workspace missing {key}")


def _thresholds(registry: dict[str, Any]) -> dict[str, float]:
    thresholds = registry.get("router_policy", {}).get("thresholds", {})
    return {
        "min_vision_confidence_for_action": float(thresholds.get("min_vision_confidence_for_action", 0.55)),
        "min_vision_confidence_for_reacquire": float(thresholds.get("min_vision_confidence_for_reacquire", 0.35)),
        "max_pose_error_for_pinch_m": float(thresholds.get("max_pose_error_for_pinch_m", 0.015)),
        "slip_recovery_threshold": float(thresholds.get("slip_recovery_threshold", 0.30)),
        "crush_abort_threshold": float(thresholds.get("crush_abort_threshold", 0.35)),
        "penetration_abort_threshold_m": float(thresholds.get("penetration_abort_threshold_m", 0.004)),
    }


def _is_executable(skill: dict[str, Any]) -> bool:
    entrypoints = skill.get("entrypoints", {})
    return bool(entrypoints.get("smoke") or entrypoints.get("eval_script") or entrypoints.get("demo_script"))


def route_scene(registry: dict[str, Any], case: dict[str, Any]) -> RouteDecision:
    validate_scene_case(case)
    skills = skill_by_id(registry)
    t = _thresholds(registry)

    vision = case["vision"]
    tactile = case["tactile"]
    workspace = case["workspace"]
    case_id = str(case["case_id"])
    expected = case.get("expected_skill_id")

    vision_conf = float(vision["confidence"])
    pose_error = float(vision["estimated_pose_error_m"])
    slip = float(tactile["slip_score"])
    crush = float(tactile["crush_risk"])
    penetration = float(tactile["penetration_m"])
    contact_present = bool(tactile["contact_present"])
    desired = str(case.get("desired_grasp_style", "auto")).lower()
    clearance = str(workspace.get("clearance", "medium")).lower()
    pinch_eligible = bool(workspace.get("pinch_eligible", False))
    occlusion = str(vision.get("occlusion", "medium")).lower()

    if crush >= t["crush_abort_threshold"] or penetration >= t["penetration_abort_threshold_m"]:
        selected = "release_or_abort"
        reason = "safety_metric_exceeded"
        fallback = None
        confidence = 0.95
    elif contact_present and slip >= t["slip_recovery_threshold"]:
        selected = "slip_recovery"
        reason = "contact_slip_high"
        fallback = "full_hand_gentle_grasp"
        confidence = min(1.0, 0.55 + slip)
    elif vision_conf < t["min_vision_confidence_for_reacquire"]:
        selected = "acquire_vision_pose"
        reason = "vision_confidence_too_low_for_action"
        fallback = "release_or_abort"
        confidence = 1.0 - vision_conf
    elif (
        desired in {"pinch", "auto"}
        and pinch_eligible
        and clearance in {"medium", "high"}
        and occlusion in {"none", "low", "medium"}
        and vision_conf >= t["min_vision_confidence_for_action"]
        and pose_error <= t["max_pose_error_for_pinch_m"]
    ):
        selected = "thumb_index_middle_pinch"
        reason = "pinch_clearance_and_vision_good"
        fallback = "full_hand_gentle_grasp"
        confidence = min(1.0, 0.50 + 0.35 * vision_conf + max(0.0, 0.015 - pose_error) * 4.0)
    else:
        selected = "full_hand_gentle_grasp"
        reason = "default_gentle_or_low_clearance_route"
        fallback = "thumb_index_middle_pinch" if pinch_eligible else None
        confidence = min(1.0, 0.60 + 0.20 * vision_conf)

    if selected not in skills:
        raise SkillZooError(f"Router selected unknown skill_id: {selected}")
    skill = skills[selected]
    return RouteDecision(
        case_id=case_id,
        selected_skill_id=selected,
        selected_status=str(skill.get("status", "unknown")),
        decision_reason=reason,
        fallback_skill_id=fallback,
        confidence=float(round(confidence, 4)),
        executable=_is_executable(skill),
        expected_skill_id=str(expected) if expected is not None else None,
    )


def summarize_registry(registry: dict[str, Any]) -> dict[str, Any]:
    skills = registry.get("skills", [])
    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    executable = 0
    for skill in skills:
        status = str(skill.get("status", "unknown"))
        skill_type = str(skill.get("skill_type", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        type_counts[skill_type] = type_counts.get(skill_type, 0) + 1
        executable += int(_is_executable(skill))
    return {
        "skill_count": len(skills),
        "executable_skill_count": executable,
        "status_counts": status_counts,
        "type_counts": type_counts,
    }


def smoke_command_for_skill(registry: dict[str, Any], skill_id: str) -> list[str] | None:
    skills = skill_by_id(registry)
    if skill_id not in skills:
        raise SkillZooError(f"Unknown skill_id: {skill_id}")
    smoke = skills[skill_id].get("entrypoints", {}).get("smoke")
    if not smoke:
        return None
    script = smoke.get("script")
    if not script:
        return None
    return [str(ROOT / str(script)), *[str(arg) for arg in smoke.get("args", [])]]
