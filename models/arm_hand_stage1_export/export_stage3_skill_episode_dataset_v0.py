#!/usr/bin/env python3
"""Export Stage3.9B unified skill episode rows.

This converts existing Stage3.7D and Stage3.8B result metadata into a compact
episode-level SkillZoo dataset. It does not replay MuJoCo and it does not train
a model; the output is a bridge toward ACT/Diffusion Policy datasets.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_skillzoo_v0 import DEFAULT_REGISTRY, load_registry, skill_by_id


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DATA = ROOT / "data"

DEFAULT_FULL_HAND_METADATA = META / "stage3_contact_transition_recovery_v0_randomized30.json"
DEFAULT_PINCH_METADATA = META / "stage3_pinch_grasp_training_v0.json"
DEFAULT_JSONL = DATA / "stage3_skill_episode_dataset_v0.jsonl"
DEFAULT_NPZ = DATA / "stage3_skill_episode_dataset_v0.npz"
DEFAULT_METADATA = META / "stage3_skill_episode_dataset_v0.json"
DEFAULT_REPORT = DOCS / "stage3_skill_episode_dataset_v0_report.md"

SCHEMA_VERSION = "stage3_skill_episode_row_v0"
SELECTED_PINCH_SKILL = "thumb_index_middle_pinch"
FULL_HAND_SKILL = "full_hand_gentle_grasp"

FEATURE_COLUMNS = [
    "skill_code",
    "canonical_training",
    "success",
    "vision_confidence_initial",
    "vision_confidence_final",
    "pose_error_m",
    "vision_lift_height_m",
    "true_lift_height_m",
    "vision_true_lift_error_m",
    "hold_stable_fraction",
    "hold_pinch_fraction",
    "hold_pinch_purity_mean",
    "hold_max_slip_score",
    "hold_final_slip_score",
    "max_slip_score",
    "pre_lift_max_slip_score",
    "post_lift_max_slip_score",
    "max_crush_risk",
    "max_penetration_m",
    "final_floor_contacts",
    "contact_settle_steps_actual",
    "recovery_steps",
    "recovery_events",
    "total_steps",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def as_float(value: Any, default: float = float("nan")) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_bool(value: Any) -> bool:
    return bool(value)


def compact_counter(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    return {str(key): int(value) for key, value in raw.items()}


def full_hand_row(source_path: Path, source: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    summary = row.get("summary", {})
    episode_id = as_int(row.get("episode_id"))
    trial = str(row.get("trial", "unknown"))
    final_lift = as_float(summary.get("final_lift_height_m"))
    hold_stable = as_float(summary.get("hold_stable_fraction"))
    hold_slip = as_float(summary.get("hold_max_slip_score"))
    max_slip = as_float(summary.get("max_slip_score"))
    max_crush = as_float(summary.get("max_crush_risk"))
    max_penetration = as_float(summary.get("max_penetration_m"))
    floor_contacts = as_int(summary.get("final_floor_contacts"))
    pose_error = as_float(summary.get("approach_true_proxy_error_m"))
    success = as_bool(row.get("success"))

    return {
        "schema_version": SCHEMA_VERSION,
        "episode_uid": f"stage3_7d_full_hand_{episode_id:04d}",
        "episode_id": episode_id,
        "skill_id": FULL_HAND_SKILL,
        "skill_variant_id": "stage3_7d_recovery_microphase",
        "task_goal": "lift_and_hold_fragile_egg",
        "scene_case_id": trial,
        "dataset_split": "canonical_training",
        "canonical_training": True,
        "diagnostic_only": False,
        "source": {
            "stage": "Stage3.7D",
            "source_file": str(source_path),
            "source_result_key": "results",
            "policy_scope": row.get("policy_scope", source.get("policy_scope")),
            "source_generated_at": source.get("generated_at"),
        },
        "route_context": {
            "desired_grasp_style": "gentle",
            "workspace": {"clearance": "unknown", "pinch_eligible": False},
            "router_expected_skill_id": FULL_HAND_SKILL,
        },
        "vision": {
            "initial_accepted": as_bool(summary.get("vision_accepted")),
            "initial_status": "accepted" if as_bool(summary.get("vision_accepted")) else "not_accepted",
            "initial_confidence": None,
            "final_accepted": None,
            "final_confidence": None,
            "pose_error_m": pose_error,
            "vision_lift_height_m": None,
            "true_lift_height_m": final_lift,
            "vision_true_lift_error_m": None,
        },
        "tactile": {
            "contact_acquired": as_bool(summary.get("contact_acquired")),
            "grip_stable_before_lift": as_bool(summary.get("grip_stable_before_lift")),
            "first_contact_phase": summary.get("first_contact_phase"),
            "hold_stable_fraction": hold_stable,
            "hold_pinch_fraction": None,
            "hold_pinch_purity_mean": None,
            "hold_max_slip_score": hold_slip,
            "hold_final_slip_score": as_float(summary.get("hold_final_slip_score")),
            "max_slip_score": max_slip,
            "pre_lift_max_slip_score": as_float(summary.get("pre_lift_max_slip_score")),
            "post_lift_max_slip_score": as_float(summary.get("post_lift_max_slip_score")),
            "max_crush_risk": max_crush,
            "max_penetration_m": max_penetration,
            "final_floor_contacts": floor_contacts,
        },
        "action_summary": {
            "controller_type": "scripted_arm_wrist_plus_learned_hand_plus_tactile_recovery",
            "learned_control_steps": as_int(summary.get("learned_control_steps")),
            "contact_settle_steps_actual": as_int(summary.get("contact_settle_steps_actual")),
            "gate_opened_before_lift": as_bool(summary.get("gate_opened_before_lift")),
            "gate_release_reason": summary.get("gate_release_reason"),
            "recovery_steps": as_int(summary.get("recovery_steps")),
            "recovery_events": as_int(summary.get("recovery_events")),
            "recovery_counts": compact_counter(summary.get("recovery_counts")),
            "recovery_budget_exhausted_counts": compact_counter(summary.get("recovery_budget_exhausted_counts")),
            "total_steps": as_int(summary.get("total_steps")),
        },
        "success": success,
        "status": row.get("status"),
        "terminal_reason": row.get("terminal_reason"),
        "failure_reasons": list(row.get("failure_reasons", [])),
        "risk_flags": list(row.get("risk_flags", [])),
        "training_labels": {
            "success_label": int(success),
            "usable_for_skill_training": bool(success),
            "needs_failure_replay": bool(row.get("failure_reasons")),
        },
        "metrics": {
            "lift_height_m": final_lift,
            "hold_stable_fraction": hold_stable,
            "hold_max_slip_score": hold_slip,
            "max_slip_score": max_slip,
            "max_crush_risk": max_crush,
            "max_penetration_m": max_penetration,
            "pose_error_m": pose_error,
        },
    }


def pinch_row(
    source_path: Path,
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    selected_candidate: str,
    include_all_final_candidates: bool,
) -> dict[str, Any] | None:
    candidate = str(row.get("candidate", "unknown"))
    is_selected = candidate == selected_candidate
    if not is_selected and not include_all_final_candidates:
        return None

    summary = row.get("summary", {})
    episode_id = as_int(row.get("episode_id"))
    trial = str(row.get("trial", "unknown"))
    training_stage = str(row.get("training_stage", "final"))
    success = as_bool(row.get("success"))
    dataset_split = "canonical_training" if is_selected else "diagnostic_variant"
    config = row.get("candidate_config") if isinstance(row.get("candidate_config"), dict) else {}

    return {
        "schema_version": SCHEMA_VERSION,
        "episode_uid": f"stage3_8b_{training_stage}_{candidate}_{episode_id:04d}",
        "episode_id": episode_id,
        "skill_id": SELECTED_PINCH_SKILL,
        "skill_variant_id": candidate,
        "task_goal": "lift_and_hold_fragile_egg",
        "scene_case_id": trial,
        "dataset_split": dataset_split,
        "canonical_training": is_selected,
        "diagnostic_only": not is_selected,
        "source": {
            "stage": "Stage3.8B",
            "source_file": str(source_path),
            "source_result_key": "final_results",
            "policy_scope": row.get("policy_scope", source.get("policy_scope")),
            "training_stage": training_stage,
            "family": row.get("family"),
            "source_generated_at": source.get("generated_at"),
        },
        "route_context": {
            "desired_grasp_style": "pinch",
            "workspace": {"clearance": "high", "pinch_eligible": True},
            "router_expected_skill_id": SELECTED_PINCH_SKILL,
        },
        "vision": {
            "initial_accepted": as_bool(summary.get("initial_vision_accepted")),
            "initial_status": summary.get("initial_vision_status"),
            "initial_confidence": as_float(summary.get("initial_vision_confidence")),
            "final_accepted": as_bool(summary.get("final_vision_accepted")),
            "final_camera": summary.get("final_vision_camera"),
            "final_status": summary.get("final_vision_status"),
            "final_confidence": as_float(summary.get("final_vision_confidence")),
            "pose_error_m": as_float(summary.get("approach_true_proxy_error_m")),
            "vision_lift_height_m": as_float(summary.get("vision_lift_height_m")),
            "true_lift_height_m": as_float(summary.get("true_lift_height_m")),
            "vision_true_lift_error_m": as_float(summary.get("vision_true_lift_error_m")),
        },
        "tactile": {
            "contact_acquired": as_bool(summary.get("contact_acquired")),
            "grip_stable_before_lift": as_bool(summary.get("pinch_contact_before_lift")),
            "first_contact_phase": summary.get("first_contact_phase"),
            "hold_stable_fraction": as_float(summary.get("hold_stable_fraction")),
            "hold_pinch_fraction": as_float(summary.get("hold_pinch_fraction")),
            "hold_pinch_purity_mean": as_float(summary.get("hold_pinch_purity_mean")),
            "hold_max_slip_score": as_float(summary.get("hold_max_slip_score")),
            "hold_final_slip_score": as_float(summary.get("hold_final_slip_score")),
            "max_slip_score": as_float(summary.get("max_slip_score")),
            "pre_lift_max_slip_score": None,
            "post_lift_max_slip_score": None,
            "max_crush_risk": as_float(summary.get("max_crush_risk")),
            "max_penetration_m": as_float(summary.get("max_penetration_m")),
            "final_floor_contacts": as_int(summary.get("final_floor_contacts")),
            "final_contact_regions": summary.get("final_contact_regions", []),
            "region_counts_total": summary.get("region_counts_total", {}),
        },
        "action_summary": {
            "controller_type": "scripted_pinch_candidate",
            "candidate": candidate,
            "active_fingers": list(config.get("active_fingers", [])),
            "candidate_config": config,
            "contact_settle_steps_actual": as_int(summary.get("contact_settle_steps_actual")),
            "gate_release_reason": summary.get("gate_release_reason"),
            "total_steps": as_int(summary.get("total_steps")),
        },
        "success": success,
        "status": row.get("status"),
        "terminal_reason": row.get("terminal_reason"),
        "failure_reasons": list(row.get("failure_reasons", [])),
        "risk_flags": list(row.get("risk_flags", [])),
        "training_labels": {
            "success_label": int(success),
            "usable_for_skill_training": bool(is_selected and success),
            "needs_failure_replay": bool(row.get("failure_reasons")),
        },
        "metrics": {
            "vision_lift_height_m": as_float(summary.get("vision_lift_height_m")),
            "true_lift_height_m": as_float(summary.get("true_lift_height_m")),
            "vision_true_lift_error_m": as_float(summary.get("vision_true_lift_error_m")),
            "hold_stable_fraction": as_float(summary.get("hold_stable_fraction")),
            "hold_pinch_fraction": as_float(summary.get("hold_pinch_fraction")),
            "hold_pinch_purity_mean": as_float(summary.get("hold_pinch_purity_mean")),
            "hold_max_slip_score": as_float(summary.get("hold_max_slip_score")),
            "max_slip_score": as_float(summary.get("max_slip_score")),
            "max_crush_risk": as_float(summary.get("max_crush_risk")),
            "max_penetration_m": as_float(summary.get("max_penetration_m")),
            "pose_error_m": as_float(summary.get("approach_true_proxy_error_m")),
        },
    }


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    full_hand = read_json(args.full_hand_metadata)
    pinch = read_json(args.pinch_metadata)
    selected_candidate = str(pinch.get("selected_candidate", {}).get("name", args.selected_pinch_candidate))

    rows: list[dict[str, Any]] = []
    for source_row in full_hand.get("results", []):
        rows.append(full_hand_row(args.full_hand_metadata, full_hand, source_row))

    for source_row in pinch.get("final_results", []):
        item = pinch_row(
            args.pinch_metadata,
            pinch,
            source_row,
            selected_candidate=selected_candidate,
            include_all_final_candidates=bool(args.include_pinch_diagnostic),
        )
        if item is not None:
            rows.append(item)

    source_summary = {
        "full_hand_source_rows": len(full_hand.get("results", [])),
        "pinch_final_source_rows": len(pinch.get("final_results", [])),
        "selected_pinch_candidate": selected_candidate,
        "include_pinch_diagnostic": bool(args.include_pinch_diagnostic),
    }
    return rows, source_summary


def validate_rows(rows: list[dict[str, Any]], registry: dict[str, Any]) -> None:
    skills = skill_by_id(registry)
    required = registry.get("episode_schema", {}).get("required_fields", [])
    if not rows:
        raise ValueError("No rows exported")
    seen: set[str] = set()
    for row in rows:
        missing = [field for field in required if field not in row]
        if missing:
            raise ValueError(f"Row {row.get('episode_uid')} missing required fields: {missing}")
        skill_id = str(row["skill_id"])
        if skill_id not in skills:
            raise ValueError(f"Row {row.get('episode_uid')} references unknown skill_id {skill_id!r}")
        uid = str(row["episode_uid"])
        if uid in seen:
            raise ValueError(f"Duplicate episode_uid: {uid}")
        seen.add(uid)


def feature_value(row: dict[str, Any], column: str, skill_codes: dict[str, int]) -> float:
    if column == "skill_code":
        return float(skill_codes[row["skill_id"]])
    if column == "canonical_training":
        return float(int(bool(row.get("canonical_training"))))
    if column == "success":
        return float(int(bool(row.get("success"))))
    vision = row.get("vision", {})
    tactile = row.get("tactile", {})
    action = row.get("action_summary", {})
    mapping = {
        "vision_confidence_initial": vision.get("initial_confidence"),
        "vision_confidence_final": vision.get("final_confidence"),
        "pose_error_m": vision.get("pose_error_m"),
        "vision_lift_height_m": vision.get("vision_lift_height_m"),
        "true_lift_height_m": vision.get("true_lift_height_m"),
        "vision_true_lift_error_m": vision.get("vision_true_lift_error_m"),
        "hold_stable_fraction": tactile.get("hold_stable_fraction"),
        "hold_pinch_fraction": tactile.get("hold_pinch_fraction"),
        "hold_pinch_purity_mean": tactile.get("hold_pinch_purity_mean"),
        "hold_max_slip_score": tactile.get("hold_max_slip_score"),
        "hold_final_slip_score": tactile.get("hold_final_slip_score"),
        "max_slip_score": tactile.get("max_slip_score"),
        "pre_lift_max_slip_score": tactile.get("pre_lift_max_slip_score"),
        "post_lift_max_slip_score": tactile.get("post_lift_max_slip_score"),
        "max_crush_risk": tactile.get("max_crush_risk"),
        "max_penetration_m": tactile.get("max_penetration_m"),
        "final_floor_contacts": tactile.get("final_floor_contacts"),
        "contact_settle_steps_actual": action.get("contact_settle_steps_actual"),
        "recovery_steps": action.get("recovery_steps"),
        "recovery_events": action.get("recovery_events"),
        "total_steps": action.get("total_steps"),
    }
    return as_float(mapping.get(column))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(json_ready(row), ensure_ascii=False, sort_keys=True) + "\n")


def write_npz(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    skill_ids = sorted({str(row["skill_id"]) for row in rows})
    skill_codes = {skill_id: idx for idx, skill_id in enumerate(skill_ids)}
    features = np.asarray(
        [[feature_value(row, column, skill_codes) for column in FEATURE_COLUMNS] for row in rows],
        dtype=np.float64,
    )
    success = np.asarray([int(bool(row["success"])) for row in rows], dtype=np.int64)
    canonical = np.asarray([int(bool(row["canonical_training"])) for row in rows], dtype=np.int64)
    episode_uid = np.asarray([str(row["episode_uid"]) for row in rows])
    skill_id = np.asarray([str(row["skill_id"]) for row in rows])
    dataset_split = np.asarray([str(row["dataset_split"]) for row in rows])
    np.savez_compressed(
        path,
        features=features,
        feature_columns=np.asarray(FEATURE_COLUMNS),
        success=success,
        canonical_training=canonical,
        episode_uid=episode_uid,
        skill_id=skill_id,
        dataset_split=dataset_split,
    )
    return {
        "feature_shape": list(features.shape),
        "feature_columns": list(FEATURE_COLUMNS),
        "skill_codes": skill_codes,
    }


def summarize(rows: list[dict[str, Any]], source_summary: dict[str, Any], npz_summary: dict[str, Any]) -> dict[str, Any]:
    by_skill: dict[str, Counter[str]] = {}
    failure_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    source_stage_counts: Counter[str] = Counter()
    for row in rows:
        skill_id = str(row["skill_id"])
        by_skill.setdefault(skill_id, Counter())
        by_skill[skill_id]["episodes"] += 1
        by_skill[skill_id]["success"] += int(bool(row["success"]))
        by_skill[skill_id]["canonical_training"] += int(bool(row["canonical_training"]))
        split_counts[str(row["dataset_split"])] += 1
        source_stage_counts[str(row.get("source", {}).get("stage", "unknown"))] += 1
        for reason in row.get("failure_reasons", []):
            failure_counts[str(reason)] += 1
        for risk in row.get("risk_flags", []):
            risk_counts[str(risk)] += 1
    by_skill_ready = {
        skill_id: {
            "episodes": int(counter["episodes"]),
            "success": int(counter["success"]),
            "canonical_training": int(counter["canonical_training"]),
            "success_rate": float(counter["success"] / max(1, counter["episodes"])),
        }
        for skill_id, counter in sorted(by_skill.items())
    }
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "episode_count": len(rows),
        "canonical_training_count": sum(int(bool(row["canonical_training"])) for row in rows),
        "success_count": sum(int(bool(row["success"])) for row in rows),
        "dataset_split_counts": dict(sorted(split_counts.items())),
        "source_stage_counts": dict(sorted(source_stage_counts.items())),
        "by_skill": by_skill_ready,
        "failure_reason_counts": dict(sorted(failure_counts.items())),
        "risk_flag_counts": dict(sorted(risk_counts.items())),
        "source_summary": source_summary,
        "npz": npz_summary,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Stage3.9B Skill Episode Dataset v0 报告",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 状态：`{summary['status']}`",
        f"- JSONL：`{payload['outputs']['jsonl']}`",
        f"- NPZ：`{payload['outputs']['npz']}`",
        f"- metadata：`{payload['outputs']['metadata']}`",
        f"- episode rows：`{summary['episode_count']}`",
        f"- canonical training rows：`{summary['canonical_training_count']}`",
        f"- success rows：`{summary['success_count']}`",
        "",
        "## 技能分布",
        "",
        "| skill | episodes | success | canonical training | success rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for skill_id, info in summary["by_skill"].items():
        lines.append(
            f"| {skill_id} | {info['episodes']} | {info['success']} | {info['canonical_training']} | {info['success_rate']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 数据来源",
            "",
            "| source stage | rows |",
            "| --- | --- |",
        ]
    )
    for key, value in summary["source_stage_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 数据集 split",
            "",
            "| split | rows |",
            "| --- | --- |",
        ]
    )
    for key, value in summary["dataset_split_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 失败和风险信号",
            "",
            "| type | name | count |",
            "| --- | --- | --- |",
        ]
    )
    for key, value in summary["failure_reason_counts"].items():
        lines.append(f"| failure | {key} | {value} |")
    for key, value in summary["risk_flag_counts"].items():
        lines.append(f"| risk | {key} | {value} |")
    lines.extend(
        [
            "",
            "## NPZ 特征",
            "",
            f"- shape：`{summary['npz']['feature_shape']}`",
            f"- columns：`{', '.join(summary['npz']['feature_columns'])}`",
            "",
            "## 结论",
            "",
            "Stage3.9B 已经把 Stage3.7D/3.8B 的 episode 结果统一成 skill episode rows。这个数据集是 episode-level 中间层，适合做路由器、失败分类、训练集筛选和下一步 LeRobot/ACT/Diffusion Policy 转换准备；它还不是低层逐时间步 action dataset。",
            "",
            "如果成功：下一步可以做 Stage3.9B2，把 canonical rows 反查到 trace 或原始 action/obs，生成真正的小模型训练序列。",
            "",
            "如果失败：先修 schema 映射和 failure taxonomy，不进入模型训练。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--full-hand-metadata", type=Path, default=DEFAULT_FULL_HAND_METADATA)
    parser.add_argument("--pinch-metadata", type=Path, default=DEFAULT_PINCH_METADATA)
    parser.add_argument("--selected-pinch-candidate", default="thumb_index_middle_strong__higher_approach")
    parser.add_argument("--include-pinch-diagnostic", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--npz", type=Path, default=DEFAULT_NPZ)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    registry = load_registry(args.registry)
    rows, source_summary = build_rows(args)
    validate_rows(rows, registry)
    write_jsonl(args.jsonl, rows)
    npz_summary = write_npz(args.npz, rows)
    summary = summarize(rows, source_summary, npz_summary)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "registry": str(args.registry),
        "sources": {
            "full_hand_metadata": str(args.full_hand_metadata),
            "pinch_metadata": str(args.pinch_metadata),
        },
        "outputs": {
            "jsonl": str(args.jsonl),
            "npz": str(args.npz),
            "metadata": str(args.metadata),
            "report": str(args.report),
        },
        "summary": summary,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report, payload)
    print(
        "Stage3.9B skill episode dataset: "
        f"status={summary['status']} "
        f"rows={summary['episode_count']} "
        f"canonical={summary['canonical_training_count']} "
        f"success={summary['success_count']}"
    )
    print(f"jsonl={args.jsonl}")
    print(f"npz={args.npz}")
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
