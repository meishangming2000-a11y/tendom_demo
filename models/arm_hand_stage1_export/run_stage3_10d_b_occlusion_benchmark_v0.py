#!/usr/bin/env python3
"""Stage3.10D-B expanded robustness benchmark with explicit vision stress."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
EVAL_SCRIPT = ROOT / "eval_stage3_10c_safety_act_cvae_policy_v0.py"


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    title_zh: str
    random_offset_std: float
    final_verification_mode: str
    initial_vision_stress_scenario: str = "none"
    final_vision_stress_scenario: str = "none"


CASES = [
    BenchmarkCase(
        case_id="pose008_strictvision",
        title_zh="8mm 位姿噪声 + 严格最终视觉",
        random_offset_std=0.008,
        final_verification_mode="strict_vision",
    ),
    BenchmarkCase(
        case_id="pose010_corroborated",
        title_zh="10mm 位姿噪声 + 视觉/触觉终验",
        random_offset_std=0.010,
        final_verification_mode="vision_tactile_corroborated",
    ),
    BenchmarkCase(
        case_id="initial_maskdrop30_pose005",
        title_zh="初始视觉 mask dropout 30% + 5mm 位姿噪声",
        random_offset_std=0.005,
        final_verification_mode="strict_vision",
        initial_vision_stress_scenario="mask_dropout_30",
    ),
    BenchmarkCase(
        case_id="final_maskdrop55_occlusionaware_pose005",
        title_zh="最终视觉 mask dropout 55% + occlusion-aware 融合验收",
        random_offset_std=0.005,
        final_verification_mode="vision_tactile_occlusion_aware",
        final_vision_stress_scenario="mask_dropout_55",
    ),
    BenchmarkCase(
        case_id="final_occluder45_occlusionaware_pose008",
        title_zh="最终视觉 synthetic occluder 45% + occlusion-aware 融合验收",
        random_offset_std=0.008,
        final_verification_mode="vision_tactile_occlusion_aware",
        final_vision_stress_scenario="synthetic_occluder_45",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_values(results: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in results:
        value = row.get("summary", {}).get(key)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            values.append(numeric)
    return values


def stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    return {
        "mean": float(sum(values) / len(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def count_values(results: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in results:
        value = str(row.get("summary", {}).get(key, "none"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_eval_command(
    case: BenchmarkCase,
    metadata: Path,
    report: Path,
    episodes_per_skill: int,
    *,
    initial_vision_stress_samples: int,
    final_vision_stress_samples: int,
    policy_vision_quality_mode: str,
    pinch_repair_mode: str,
    pinch_repair_phases: str,
    pinch_repair_expert_alpha: float,
    pinch_repair_preclose_delta: float,
    pinch_repair_close_max: float,
) -> list[str]:
    return [
        sys.executable,
        str(EVAL_SCRIPT),
        "--skills",
        "full_hand_gentle_grasp,thumb_index_middle_pinch",
        "--trials",
        "cycle",
        "--episodes-per-skill",
        str(int(episodes_per_skill)),
        "--execution-mode",
        "scripted_arm_predicted_hand",
        "--replan-interval",
        "16",
        "--full-hand-control-mode",
        "stage3_7d_fallback",
        "--pinch-final-verification-mode",
        case.final_verification_mode,
        "--pinch-repair-mode",
        str(pinch_repair_mode),
        "--pinch-repair-phases",
        str(pinch_repair_phases),
        "--pinch-repair-expert-alpha",
        f"{float(pinch_repair_expert_alpha):.3f}",
        "--pinch-repair-preclose-delta",
        f"{float(pinch_repair_preclose_delta):.3f}",
        "--pinch-repair-close-max",
        f"{float(pinch_repair_close_max):.3f}",
        "--random-offset-std",
        f"{case.random_offset_std:.3f}",
        "--initial-vision-stress-scenario",
        case.initial_vision_stress_scenario,
        "--final-vision-stress-scenario",
        case.final_vision_stress_scenario,
        "--initial-vision-stress-samples",
        str(int(initial_vision_stress_samples)),
        "--final-vision-stress-samples",
        str(int(final_vision_stress_samples)),
        "--policy-vision-quality-mode",
        str(policy_vision_quality_mode),
        "--metadata",
        str(metadata),
        "--report",
        str(report),
    ]


def case_paths(case: BenchmarkCase, episodes_per_skill: int, suffix: str = "") -> tuple[Path, Path]:
    clean_suffix = str(suffix or "")
    stem = f"stage3_10d_b_{case.case_id}_cycle{int(episodes_per_skill) * 2}{clean_suffix}"
    return META / f"{stem}.json", DOCS / f"{stem}_report.md"


def summarize_case(case: BenchmarkCase, metadata: Path, report: Path, returncode: int | None) -> dict[str, Any]:
    if not metadata.exists():
        return {
            "case_id": case.case_id,
            "title_zh": case.title_zh,
            "status": "MISSING",
            "episodes": 0,
            "success_count": 0,
            "returncode": returncode,
            "metadata": str(metadata),
            "report": str(report),
            "failure_reason_counts": {"missing_metadata": 1},
        }
    payload = read_json(metadata)
    summary = payload.get("summary", {})
    results = payload.get("results", [])
    return {
        "case_id": case.case_id,
        "title_zh": case.title_zh,
        "status": str(summary.get("status", "UNKNOWN")),
        "episodes": int(summary.get("episodes", 0)),
        "success_count": int(summary.get("success_count", 0)),
        "returncode": returncode,
        "random_offset_std": case.random_offset_std,
        "final_verification_mode": case.final_verification_mode,
        "initial_vision_stress_scenario": case.initial_vision_stress_scenario,
        "final_vision_stress_scenario": case.final_vision_stress_scenario,
        "initial_vision_stress_samples": int(payload.get("args", {}).get("initial_vision_stress_samples", 1)),
        "final_vision_stress_samples": int(payload.get("args", {}).get("final_vision_stress_samples", 1)),
        "policy_vision_quality_mode": str(payload.get("args", {}).get("policy_vision_quality_mode", "raw")),
        "pinch_repair_mode": str(payload.get("args", {}).get("pinch_repair_mode", "unknown")),
        "pinch_repair_phases": str(payload.get("args", {}).get("pinch_repair_phases", "unknown")),
        "pinch_repair_expert_alpha": float(payload.get("args", {}).get("pinch_repair_expert_alpha", 0.0)),
        "pinch_repair_preclose_delta": float(payload.get("args", {}).get("pinch_repair_preclose_delta", 0.0)),
        "pinch_repair_close_max": float(payload.get("args", {}).get("pinch_repair_close_max", 0.0)),
        "metadata": str(metadata),
        "report": str(report),
        "terminal_reason_counts": summary.get("terminal_reason_counts", {}),
        "failure_reason_counts": summary.get("failure_reason_counts", {}),
        "risk_flag_counts": summary.get("risk_flag_counts", {}),
        "accepted_by_counts": count_values(results, "final_vision_accepted_by"),
        "final_vision_stress_counts": count_values(results, "final_vision_stress_scenario"),
        "true_lift_height_m": stats(finite_values(results, "true_lift_height_m") + finite_values(results, "final_lift_height_m")),
        "hold_max_slip_score": stats(finite_values(results, "hold_max_slip_score")),
        "final_vision_confidence": stats(finite_values(results, "final_vision_confidence")),
        "by_skill": summary.get("by_skill", {}),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3.10D-B Occlusion Benchmark Closeout\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{payload['status']}`\n",
        f"- 总成功：`{payload['total_success']} / {payload['total_episodes']}`\n",
        "- 执行模式：`scripted_arm_predicted_hand`\n",
        "- 边界：这不是 full-action 26 actuator ACT/DP，也不是硬件或真实摄像头集成。\n\n",
        "## 这一步做了什么\n\n",
        "Stage3.10D-B 在 10D-A 的基础上扩大样本，并加入显式视觉压力：初始 noisy-mask、最终 noisy-mask、最终 synthetic occluder，以及 occlusion-aware 视觉/触觉融合验收。\n\n",
        "## Case 汇总\n\n",
        "| case | 含义 | 成功 | 视觉压力 | final accepted_by | 主要风险 |\n",
        "| --- | --- | ---: | --- | --- | --- |\n",
    ]
    for case in payload["cases"]:
        stress = (
            f"initial={case['initial_vision_stress_scenario']} x{case.get('initial_vision_stress_samples', 1)}, "
            f"final={case['final_vision_stress_scenario']} x{case.get('final_vision_stress_samples', 1)}, "
            f"policy_quality={case.get('policy_vision_quality_mode', 'raw')}"
        )
        lines.append(
            f"| `{case['case_id']}` | {case['title_zh']} | {case['success_count']} / {case['episodes']} | "
            f"`{stress}` | `{case.get('accepted_by_counts', {})}` | `{case.get('risk_flag_counts', {})}` |\n"
        )
    lines.extend(
        [
            "\n## 关键观察\n\n",
            f"- D-B 合计 `{payload['total_success']} / {payload['total_episodes']}`。\n",
            "- `strict_vision` case 用来检查最终视觉能否独立验收；`vision_tactile_occlusion_aware` case 用来检查最终视觉被污染但仍有 mask 证据时，触觉稳定持握能否作为融合兜底。\n",
            "- 如果 occlusion-aware 通过，它不是“纯视觉量到了 lift”，而是“低置信视觉仍看到目标局部 + 触觉持握稳定 + 无地面接触”的传感器融合判定。\n",
            "- 仍需要继续报告 `early_contact_in_approach`、`transient_slip_high`、hold slip、crush 和 penetration；不能因为最终验收过了就忽略过程风险。\n\n",
            "## 如果成功\n\n",
            "下一步可以进入 Stage3.10D-C：把失败/边界 case 纳入 safety-labeled 数据，训练或评估一个显式 occlusion-aware safety head，或者开始 staged full-action repair。\n\n",
            "## 如果失败\n\n",
            "先按失败来源拆：初始视觉污染导致接近误差、最终视觉完全不可见、触觉 hold 实际失败，还是 occlusion-aware 判定条件太松/太紧。不要放宽 slip、crush、penetration 阈值。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-per-skill", type=int, default=10)
    parser.add_argument("--cases", default="all", help="Comma-separated case ids, or all.")
    parser.add_argument("--initial-vision-stress-samples", type=int, default=1)
    parser.add_argument("--final-vision-stress-samples", type=int, default=1)
    parser.add_argument("--policy-vision-quality-mode", choices=["raw", "accepted_nominal"], default="raw")
    parser.add_argument("--pinch-repair-mode", default="inactive_anchor_slip_close")
    parser.add_argument("--pinch-repair-phases", default="slow_lift,hold")
    parser.add_argument("--pinch-repair-expert-alpha", type=float, default=0.20)
    parser.add_argument("--pinch-repair-preclose-delta", type=float, default=0.10)
    parser.add_argument("--pinch-repair-close-max", type=float, default=0.18)
    parser.add_argument("--case-stem-suffix", default="")
    parser.add_argument("--aggregate-existing", action="store_true")
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--metadata", type=Path, default=META / "stage3_10d_b_occlusion_benchmark_v0.json")
    parser.add_argument("--report", type=Path, default=DOCS / "stage3_10d_b_occlusion_benchmark_v0_closeout.md")
    args = parser.parse_args()

    case_by_id = {case.case_id: case for case in CASES}
    if str(args.cases).strip().lower() in {"all", "*"}:
        selected = list(CASES)
    else:
        requested = [item.strip() for item in str(args.cases).split(",") if item.strip()]
        missing = [item for item in requested if item not in case_by_id]
        if missing:
            raise SystemExit(f"Unknown cases {missing}; choose from {sorted(case_by_id)}")
        selected = [case_by_id[item] for item in requested]

    cases_out: list[dict[str, Any]] = []
    status = 0
    for case in selected:
        metadata, report = case_paths(case, int(args.episodes_per_skill), str(args.case_stem_suffix))
        returncode: int | None = None
        if not args.aggregate_existing:
            command = build_eval_command(
                case,
                metadata,
                report,
                int(args.episodes_per_skill),
                initial_vision_stress_samples=int(args.initial_vision_stress_samples),
                final_vision_stress_samples=int(args.final_vision_stress_samples),
                policy_vision_quality_mode=str(args.policy_vision_quality_mode),
                pinch_repair_mode=str(args.pinch_repair_mode),
                pinch_repair_phases=str(args.pinch_repair_phases),
                pinch_repair_expert_alpha=float(args.pinch_repair_expert_alpha),
                pinch_repair_preclose_delta=float(args.pinch_repair_preclose_delta),
                pinch_repair_close_max=float(args.pinch_repair_close_max),
            )
            print(f"Running {case.case_id}: {' '.join(command)}", flush=True)
            completed = subprocess.run(command, cwd=str(ROOT), check=False)
            returncode = int(completed.returncode)
            if returncode != 0:
                status = returncode
        cases_out.append(summarize_case(case, metadata, report, returncode))
        if status != 0 and args.stop_on_fail:
            break

    total_episodes = sum(int(case.get("episodes", 0)) for case in cases_out)
    total_success = sum(int(case.get("success_count", 0)) for case in cases_out)
    aggregate_status = "PASS" if total_episodes > 0 and total_success == total_episodes and all(case.get("status") == "PASS" for case in cases_out) else "BLOCKED"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": aggregate_status,
        "total_episodes": total_episodes,
        "total_success": total_success,
        "episodes_per_skill": int(args.episodes_per_skill),
        "initial_vision_stress_samples": int(args.initial_vision_stress_samples),
        "final_vision_stress_samples": int(args.final_vision_stress_samples),
        "policy_vision_quality_mode": str(args.policy_vision_quality_mode),
        "pinch_repair_mode": str(args.pinch_repair_mode),
        "pinch_repair_phases": str(args.pinch_repair_phases),
        "pinch_repair_expert_alpha": float(args.pinch_repair_expert_alpha),
        "pinch_repair_preclose_delta": float(args.pinch_repair_preclose_delta),
        "pinch_repair_close_max": float(args.pinch_repair_close_max),
        "cases": cases_out,
        "boundary": {
            "full_action_act_dp_promoted": False,
            "hardware_integration": False,
            "real_camera": False,
        },
        "next": "Stage3.10D-C safety-head/occlusion-aware training data or staged full-action repair.",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, payload)
    print(json.dumps({"status": aggregate_status, "total_success": total_success, "total_episodes": total_episodes}, indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return status if status != 0 else (0 if aggregate_status == "PASS" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
