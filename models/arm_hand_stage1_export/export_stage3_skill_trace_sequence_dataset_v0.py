#!/usr/bin/env python3
"""Export Stage3.9B2 trace-level skill sequence rows.

The current Stage3.7D/3.8B metadata stores sparse trace samples, not full
obs/action rollouts. This exporter keeps that distinction explicit: it creates
a sequence dataset for temporal diagnostics, routing, and failure classification
prework, while marking the data as not yet low-level ACT/Diffusion-Policy ready.
"""

from __future__ import annotations

import argparse
import json
import math
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
DEFAULT_JSONL = DATA / "stage3_skill_trace_sequence_dataset_v0.jsonl"
DEFAULT_NPZ = DATA / "stage3_skill_trace_sequence_dataset_v0.npz"
DEFAULT_METADATA = META / "stage3_skill_trace_sequence_dataset_v0.json"
DEFAULT_REPORT = DOCS / "stage3_skill_trace_sequence_dataset_v0_report.md"

SCHEMA_VERSION = "stage3_skill_trace_sequence_row_v0"
SELECTED_PINCH_CANDIDATE = "thumb_index_middle_strong__higher_approach"

FEATURE_COLUMNS = [
    "raw_step",
    "step_norm",
    "phase_code",
    "progress",
    "control_progress",
    "lift_height_m",
    "contact",
    "stable",
    "pinch_contact",
    "learned_hand",
    "recovery_active",
    "slip",
    "crush",
    "penetration",
    "gate_window",
    "recovery_reason_count",
    "recovery_reason_slip_high",
    "region_thumb",
    "region_index",
    "region_middle",
    "region_ring",
    "region_palm",
    "region_support",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def f(value: Any, default: float = float("nan")) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def i(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def b(value: Any) -> float:
    return 1.0 if bool(value) else 0.0


def safe_number(value: float) -> float | None:
    if isinstance(value, (float, int)) and math.isfinite(float(value)):
        return float(value)
    return None


def json_sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return [json_sanitize(v) for v in value]
    if isinstance(value, float):
        return safe_number(value)
    return value


def full_hand_uid(row: dict[str, Any]) -> str:
    return f"stage3_7d_full_hand_{i(row.get('episode_id')):04d}"


def pinch_uid(row: dict[str, Any]) -> str:
    episode_id = i(row.get("episode_id"))
    stage = str(row.get("training_stage", "final"))
    candidate = str(row.get("candidate", "unknown"))
    return f"stage3_8b_{stage}_{candidate}_{episode_id:04d}"


def full_hand_sequence(source_path: Path, source: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    trace = list(row.get("trace", []))
    summary = row.get("summary", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "sequence_uid": full_hand_uid(row),
        "episode_uid": full_hand_uid(row),
        "episode_id": i(row.get("episode_id")),
        "skill_id": "full_hand_gentle_grasp",
        "skill_variant_id": "stage3_7d_recovery_microphase",
        "dataset_split": "canonical_training",
        "canonical_training": True,
        "diagnostic_only": False,
        "success": bool(row.get("success")),
        "terminal_reason": row.get("terminal_reason"),
        "failure_reasons": list(row.get("failure_reasons", [])),
        "risk_flags": list(row.get("risk_flags", [])),
        "scene_case_id": str(row.get("trial", "unknown")),
        "source": {
            "stage": "Stage3.7D",
            "source_file": str(source_path),
            "source_result_key": "results",
            "policy_scope": row.get("policy_scope", source.get("policy_scope")),
            "sample_every": i(source.get("args", {}).get("sample_every"), 200),
            "action_available": False,
            "action_note": "Sparse trace only; original low-level action vector is not stored in this metadata.",
        },
        "sequence_summary": {
            "trace_length": len(trace),
            "total_steps": i(summary.get("total_steps")),
            "hold_stable_fraction": f(summary.get("hold_stable_fraction")),
            "hold_max_slip_score": f(summary.get("hold_max_slip_score")),
            "max_slip_score": f(summary.get("max_slip_score")),
            "max_crush_risk": f(summary.get("max_crush_risk")),
            "max_penetration_m": f(summary.get("max_penetration_m")),
            "final_lift_height_m": f(summary.get("final_lift_height_m")),
            "recovery_steps": i(summary.get("recovery_steps")),
            "recovery_events": i(summary.get("recovery_events")),
        },
        "trace": trace,
    }


def pinch_sequence(
    source_path: Path,
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    selected_candidate: str,
    include_diagnostic: bool,
) -> dict[str, Any] | None:
    candidate = str(row.get("candidate", "unknown"))
    is_selected = candidate == selected_candidate
    if not is_selected and not include_diagnostic:
        return None
    trace = list(row.get("trace", []))
    summary = row.get("summary", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "sequence_uid": pinch_uid(row),
        "episode_uid": pinch_uid(row),
        "episode_id": i(row.get("episode_id")),
        "skill_id": "thumb_index_middle_pinch",
        "skill_variant_id": candidate,
        "dataset_split": "canonical_training" if is_selected else "diagnostic_variant",
        "canonical_training": is_selected,
        "diagnostic_only": not is_selected,
        "success": bool(row.get("success")),
        "terminal_reason": row.get("terminal_reason"),
        "failure_reasons": list(row.get("failure_reasons", [])),
        "risk_flags": list(row.get("risk_flags", [])),
        "scene_case_id": str(row.get("trial", "unknown")),
        "source": {
            "stage": "Stage3.8B",
            "source_file": str(source_path),
            "source_result_key": "final_results",
            "policy_scope": row.get("policy_scope", source.get("policy_scope")),
            "training_stage": row.get("training_stage"),
            "family": row.get("family"),
            "sample_every": i(source.get("args", {}).get("sample_every"), 240),
            "action_available": False,
            "action_note": "Sparse trace only; scripted pinch target/action vector is not stored at every step.",
        },
        "sequence_summary": {
            "trace_length": len(trace),
            "total_steps": i(summary.get("total_steps")),
            "hold_stable_fraction": f(summary.get("hold_stable_fraction")),
            "hold_pinch_fraction": f(summary.get("hold_pinch_fraction")),
            "hold_pinch_purity_mean": f(summary.get("hold_pinch_purity_mean")),
            "hold_max_slip_score": f(summary.get("hold_max_slip_score")),
            "max_slip_score": f(summary.get("max_slip_score")),
            "max_crush_risk": f(summary.get("max_crush_risk")),
            "max_penetration_m": f(summary.get("max_penetration_m")),
            "vision_lift_height_m": f(summary.get("vision_lift_height_m")),
            "true_lift_height_m": f(summary.get("true_lift_height_m")),
        },
        "trace": trace,
    }


def build_sequences(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    full_source = read_json(args.full_hand_metadata)
    pinch_source = read_json(args.pinch_metadata)
    selected = str(pinch_source.get("selected_candidate", {}).get("name", args.selected_pinch_candidate))
    sequences: list[dict[str, Any]] = []
    for row in full_source.get("results", []):
        sequences.append(full_hand_sequence(args.full_hand_metadata, full_source, row))
    for row in pinch_source.get("final_results", []):
        seq = pinch_sequence(
            args.pinch_metadata,
            pinch_source,
            row,
            selected_candidate=selected,
            include_diagnostic=bool(args.include_pinch_diagnostic),
        )
        if seq is not None:
            sequences.append(seq)
    return sequences, {
        "full_hand_source_rows": len(full_source.get("results", [])),
        "pinch_final_source_rows": len(pinch_source.get("final_results", [])),
        "selected_pinch_candidate": selected,
        "include_pinch_diagnostic": bool(args.include_pinch_diagnostic),
    }


def phase_vocab(sequences: list[dict[str, Any]]) -> dict[str, int]:
    phases = sorted({str(step.get("phase", "unknown")) for seq in sequences for step in seq.get("trace", [])})
    return {phase: idx for idx, phase in enumerate(phases)}


def trace_features(step: dict[str, Any], *, total_steps: int, phase_codes: dict[str, int]) -> list[float]:
    raw_step = f(step.get("step"), 0.0)
    progress = f(step.get("progress", step.get("nominal_progress")))
    control_progress = f(step.get("control_progress"), progress)
    lift = f(step.get("lift_height_m", step.get("true_lift_height_m")))
    phase = str(step.get("phase", "unknown"))
    recovery_reasons = [str(x) for x in step.get("recovery_reasons", [])] if isinstance(step.get("recovery_reasons"), list) else []
    regions = set(str(x) for x in step.get("regions", []) if x is not None) if isinstance(step.get("regions"), list) else set()
    return [
        raw_step,
        raw_step / max(1.0, float(total_steps)),
        float(phase_codes.get(phase, -1)),
        progress,
        control_progress,
        lift,
        b(step.get("contact")),
        b(step.get("stable")),
        b(step.get("pinch_contact")),
        b(step.get("learned_hand")),
        b(step.get("recovery_active")),
        f(step.get("slip")),
        f(step.get("crush")),
        f(step.get("penetration")),
        f(step.get("gate_window"), 0.0),
        float(len(recovery_reasons)),
        1.0 if "slip_high" in recovery_reasons else 0.0,
        1.0 if "thumb" in regions else 0.0,
        1.0 if "index" in regions else 0.0,
        1.0 if "middle" in regions else 0.0,
        1.0 if "ring" in regions else 0.0,
        1.0 if "palm" in regions else 0.0,
        1.0 if "support" in regions else 0.0,
    ]


def write_jsonl(path: Path, sequences: list[dict[str, Any]], phase_codes: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for seq in sequences:
            total = i(seq.get("sequence_summary", {}).get("total_steps"))
            out = {k: v for k, v in seq.items() if k != "trace"}
            out["trace_length"] = len(seq.get("trace", []))
            out["feature_columns"] = FEATURE_COLUMNS
            out["phase_vocab"] = phase_codes
            out["timesteps"] = []
            for idx, step in enumerate(seq.get("trace", [])):
                features = trace_features(step, total_steps=total, phase_codes=phase_codes)
                out["timesteps"].append(
                    {
                        "t": idx,
                        "raw": step,
                        "features": {col: safe_number(val) for col, val in zip(FEATURE_COLUMNS, features)},
                    }
                )
            handle.write(json.dumps(json_sanitize(json_ready(out)), ensure_ascii=False, sort_keys=True) + "\n")


def write_npz(path: Path, sequences: list[dict[str, Any]], phase_codes: dict[str, int]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    max_len = max(len(seq.get("trace", [])) for seq in sequences)
    skill_ids = sorted({str(seq["skill_id"]) for seq in sequences})
    skill_codes = {skill_id: idx for idx, skill_id in enumerate(skill_ids)}
    features = np.full((len(sequences), max_len, len(FEATURE_COLUMNS)), np.nan, dtype=np.float64)
    mask = np.zeros((len(sequences), max_len), dtype=np.float32)
    for seq_idx, seq in enumerate(sequences):
        total = i(seq.get("sequence_summary", {}).get("total_steps"))
        for t, step in enumerate(seq.get("trace", [])):
            features[seq_idx, t, :] = np.asarray(trace_features(step, total_steps=total, phase_codes=phase_codes))
            mask[seq_idx, t] = 1.0
    success = np.asarray([int(bool(seq["success"])) for seq in sequences], dtype=np.int64)
    canonical = np.asarray([int(bool(seq["canonical_training"])) for seq in sequences], dtype=np.int64)
    skill_code = np.asarray([skill_codes[str(seq["skill_id"])] for seq in sequences], dtype=np.int64)
    trace_length = np.asarray([len(seq.get("trace", [])) for seq in sequences], dtype=np.int64)
    np.savez_compressed(
        path,
        sequences=features,
        sequence_mask=mask,
        feature_columns=np.asarray(FEATURE_COLUMNS),
        phase_vocab_json=np.asarray([json.dumps(phase_codes, ensure_ascii=False)]),
        success=success,
        canonical_training=canonical,
        skill_code=skill_code,
        trace_length=trace_length,
        episode_uid=np.asarray([str(seq["episode_uid"]) for seq in sequences]),
        sequence_uid=np.asarray([str(seq["sequence_uid"]) for seq in sequences]),
        skill_id=np.asarray([str(seq["skill_id"]) for seq in sequences]),
        dataset_split=np.asarray([str(seq["dataset_split"]) for seq in sequences]),
    )
    return {
        "sequence_shape": list(features.shape),
        "mask_shape": list(mask.shape),
        "feature_columns": list(FEATURE_COLUMNS),
        "phase_vocab": phase_codes,
        "skill_codes": skill_codes,
    }


def validate_sequences(sequences: list[dict[str, Any]], registry: dict[str, Any]) -> None:
    skills = skill_by_id(registry)
    if not sequences:
        raise ValueError("No sequences exported")
    seen: set[str] = set()
    for seq in sequences:
        uid = str(seq.get("sequence_uid"))
        if uid in seen:
            raise ValueError(f"Duplicate sequence_uid: {uid}")
        seen.add(uid)
        skill_id = str(seq.get("skill_id"))
        if skill_id not in skills:
            raise ValueError(f"Unknown skill_id {skill_id!r} in {uid}")
        if not seq.get("trace"):
            raise ValueError(f"Sequence {uid} has empty trace")


def summarize(sequences: list[dict[str, Any]], source_summary: dict[str, Any], npz_summary: dict[str, Any]) -> dict[str, Any]:
    by_skill: dict[str, Counter[str]] = {}
    split_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    failure_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    trace_lengths = []
    for seq in sequences:
        skill_id = str(seq["skill_id"])
        by_skill.setdefault(skill_id, Counter())
        by_skill[skill_id]["sequences"] += 1
        by_skill[skill_id]["success"] += int(bool(seq["success"]))
        by_skill[skill_id]["canonical_training"] += int(bool(seq["canonical_training"]))
        split_counts[str(seq["dataset_split"])] += 1
        source_counts[str(seq.get("source", {}).get("stage", "unknown"))] += 1
        trace_lengths.append(len(seq.get("trace", [])))
        for risk in seq.get("risk_flags", []):
            risk_counts[str(risk)] += 1
        for reason in seq.get("failure_reasons", []):
            failure_counts[str(reason)] += 1
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "sequence_count": len(sequences),
        "canonical_training_count": sum(int(bool(seq["canonical_training"])) for seq in sequences),
        "success_count": sum(int(bool(seq["success"])) for seq in sequences),
        "timestep_count": int(sum(trace_lengths)),
        "trace_length_min": int(min(trace_lengths)),
        "trace_length_max": int(max(trace_lengths)),
        "trace_length_mean": float(sum(trace_lengths) / max(1, len(trace_lengths))),
        "dataset_split_counts": dict(sorted(split_counts.items())),
        "source_stage_counts": dict(sorted(source_counts.items())),
        "by_skill": {
            skill_id: {
                "sequences": int(counter["sequences"]),
                "success": int(counter["success"]),
                "canonical_training": int(counter["canonical_training"]),
                "success_rate": float(counter["success"] / max(1, counter["sequences"])),
            }
            for skill_id, counter in sorted(by_skill.items())
        },
        "failure_reason_counts": dict(sorted(failure_counts.items())),
        "risk_flag_counts": dict(sorted(risk_counts.items())),
        "source_summary": source_summary,
        "npz": npz_summary,
        "act_dp_ready": False,
        "act_dp_blocker": "Current traces are sparse state samples and do not contain full low-level obs/action vectors.",
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Stage3.9B2 Skill Trace Sequence Dataset v0 报告",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 状态：`{summary['status']}`",
        f"- JSONL：`{payload['outputs']['jsonl']}`",
        f"- NPZ：`{payload['outputs']['npz']}`",
        f"- metadata：`{payload['outputs']['metadata']}`",
        f"- sequence count：`{summary['sequence_count']}`",
        f"- canonical training sequences：`{summary['canonical_training_count']}`",
        f"- success sequences：`{summary['success_count']}`",
        f"- total sampled timesteps：`{summary['timestep_count']}`",
        f"- trace length：min `{summary['trace_length_min']}` / mean `{summary['trace_length_mean']:.2f}` / max `{summary['trace_length_max']}`",
        "",
        "## 重要边界",
        "",
        "这份数据是 `trace-level sequence dataset`，不是 ACT / Diffusion Policy 可直接训练的低层动作数据。",
        "",
        "原因：现有 Stage3.7D/3.8B metadata 只保存稀疏状态 trace，没有保存每一步完整 observation 和 actuator action。",
        "",
        "它现在适合做：时序失败分类、路由器边界分析、技能选择模型预备、后续数据管线 smoke。真正小模型训练还需要下一步 replay/重采集 obs-action sequence。",
        "",
        "## 技能分布",
        "",
        "| skill | sequences | success | canonical training | success rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for skill_id, info in summary["by_skill"].items():
        lines.append(
            f"| {skill_id} | {info['sequences']} | {info['success']} | {info['canonical_training']} | {info['success_rate']:.3f} |"
        )
    lines.extend(["", "## 数据集 split", "", "| split | sequences |", "| --- | --- |"])
    for key, value in summary["dataset_split_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## NPZ", ""])
    lines.append(f"- sequence tensor shape：`{summary['npz']['sequence_shape']}`")
    lines.append(f"- feature columns：`{', '.join(summary['npz']['feature_columns'])}`")
    lines.append(f"- phase vocab：`{summary['npz']['phase_vocab']}`")
    lines.extend(["", "## 失败和风险信号", "", "| type | name | count |", "| --- | --- | --- |"])
    for key, value in summary["failure_reason_counts"].items():
        lines.append(f"| failure | {key} | {value} |")
    for key, value in summary["risk_flag_counts"].items():
        lines.append(f"| risk | {key} | {value} |")
    lines.extend(
        [
            "",
            "## 如果成功",
            "",
            "下一步做 Stage3.9B3：用 replay 或重新评估脚本导出完整 observation/action 序列，形成真正 ACT/Diffusion Policy/LeRobot 可读的数据。",
            "",
            "## 如果失败",
            "",
            "先修 trace schema、phase vocab、feature columns 和源 metadata 对齐，不进入模型训练。",
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
    parser.add_argument("--selected-pinch-candidate", default=SELECTED_PINCH_CANDIDATE)
    parser.add_argument("--include-pinch-diagnostic", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--npz", type=Path, default=DEFAULT_NPZ)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    registry = load_registry(args.registry)
    sequences, source_summary = build_sequences(args)
    validate_sequences(sequences, registry)
    phases = phase_vocab(sequences)
    write_jsonl(args.jsonl, sequences, phases)
    npz_summary = write_npz(args.npz, sequences, phases)
    summary = summarize(sequences, source_summary, npz_summary)
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
    args.metadata.write_text(json.dumps(json_sanitize(json_ready(payload)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report, payload)
    print(
        "Stage3.9B2 skill trace sequence dataset: "
        f"status={summary['status']} "
        f"sequences={summary['sequence_count']} "
        f"canonical={summary['canonical_training_count']} "
        f"timesteps={summary['timestep_count']} "
        f"act_dp_ready={summary['act_dp_ready']}"
    )
    print(f"jsonl={args.jsonl}")
    print(f"npz={args.npz}")
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
