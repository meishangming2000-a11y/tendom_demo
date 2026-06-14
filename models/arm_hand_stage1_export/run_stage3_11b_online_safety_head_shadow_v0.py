#!/usr/bin/env python3
"""Stage3.11B online safety-head shadow-mode benchmark.

This runner wires the Stage3.10D-C safety head into the closed-loop evaluator
as a shadow signal. It never changes actions. The only goal is to log what the
safety head would have predicted during each MuJoCo episode and compare that
with the episode outcome.

It is MuJoCo-only, not full-action ACT/DP promotion, and not hardware runtime.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_HEAD = CHECKPOINTS / "stage3_10d_c_occlusion_safety_head_v0.npz"
DEFAULT_METADATA = META / "stage3_11b_online_safety_head_shadow_v0.json"
DEFAULT_REPORT = DOCS / "stage3_11b_online_safety_head_shadow_v0_closeout.md"

from run_stage3_10d_b_occlusion_benchmark_v0 import (  # noqa: E402
    CASES as DB_V1_CASES,
    BenchmarkCase,
    build_eval_command as build_db_eval_command,
)
from run_stage3_10d_d_safety_head_rescan_v0 import (  # noqa: E402
    STRESS_CASES as DD_STRESS_CASES,
    StressCase,
    eval_command as build_stress_eval_command,
)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def db_shadow_paths(case: BenchmarkCase, episodes_per_skill: int) -> tuple[Path, Path]:
    stem = f"stage3_11b_shadow_dbv1_{case.case_id}_cycle{int(episodes_per_skill) * 2}"
    return META / f"{stem}.json", DOCS / f"{stem}_report.md"


def stress_shadow_paths(case: StressCase) -> tuple[Path, Path]:
    episodes = int(case.episodes_per_skill) * 2
    stem = f"stage3_11b_shadow_{case.case_id}_cycle{episodes}"
    return META / f"{stem}.json", DOCS / f"{stem}_report.md"


def selected_cases(raw: str, cases: list[Any]) -> list[Any]:
    if str(raw).strip().lower() in {"all", "*"}:
        return list(cases)
    by_id = {str(case.case_id): case for case in cases}
    requested = [item.strip() for item in str(raw).split(",") if item.strip()]
    missing = [item for item in requested if item not in by_id]
    if missing:
        raise SystemExit(f"Unknown case ids {missing}; choose from {sorted(by_id)}")
    return [by_id[item] for item in requested]


def command_with_shadow(command: list[str], *, head: Path, case_id: str, threshold: float) -> list[str]:
    return command + [
        "--safety-head-shadow-checkpoint",
        str(Path(head)),
        "--safety-head-shadow-threshold",
        f"{float(threshold):.3f}",
        "--safety-head-shadow-case-id",
        str(case_id),
    ]


def shadow_totals(summary: dict[str, Any]) -> dict[str, int]:
    shadow = summary.get("shadow", {})
    return {
        "records": int(shadow.get("records", 0)),
        "false_failure_on_hold_safe": int(shadow.get("false_failure_on_hold_safe", 0)),
        "missed_failure_or_blocked": int(shadow.get("missed_failure_or_blocked", 0)),
        "unsafe_predicted_hold_safe": int(shadow.get("unsafe_predicted_hold_safe", 0)),
        "unsafe_hold_safe_prediction": int(shadow.get("unsafe_hold_safe_prediction", 0)),
        "missed_tactile_handoff": int(shadow.get("missed_tactile_handoff", 0)),
        "total_label_mismatches": int(shadow.get("total_label_mismatches", 0)),
    }


def summarize_metadata(
    *,
    suite: str,
    case_id: str,
    title_zh: str,
    metadata: Path,
    report: Path,
    returncode: int | None,
    expected_boundary: bool = False,
) -> dict[str, Any]:
    if not metadata.exists():
        return {
            "suite": suite,
            "case_id": case_id,
            "title_zh": title_zh,
            "status": "MISSING",
            "episodes": 0,
            "success_count": 0,
            "returncode": returncode,
            "metadata": str(metadata),
            "report": str(report),
            "expected_boundary": bool(expected_boundary),
            "shadow": {"enabled": False, "records": 0},
            "failure_reason_counts": {"missing_metadata": 1},
        }
    payload = read_json(metadata)
    eval_summary = payload.get("summary", {})
    shadow = payload.get("safety_head_shadow", {})
    mismatch_label_counts: dict[str, int] = {}
    mismatch_examples: list[dict[str, Any]] = []
    for row in payload.get("results", []):
        row_shadow = row.get("safety_head_shadow", {})
        labels = [str(item) for item in row_shadow.get("mismatch_labels", [])]
        for label in labels:
            mismatch_label_counts[label] = mismatch_label_counts.get(label, 0) + 1
        if labels and len(mismatch_examples) < 8:
            mismatch_examples.append(
                {
                    "episode_id": int(row.get("episode_id", -1)),
                    "skill_id": str(row.get("skill_id", "unknown")),
                    "success": bool(row.get("success", False)),
                    "terminal_reason": str(row.get("terminal_reason", "unknown")),
                    "mismatch_labels": labels,
                }
            )
    return {
        "suite": suite,
        "case_id": case_id,
        "title_zh": title_zh,
        "status": str(eval_summary.get("status", "UNKNOWN")),
        "episodes": int(eval_summary.get("episodes", 0)),
        "success_count": int(eval_summary.get("success_count", 0)),
        "returncode": returncode,
        "metadata": str(metadata),
        "report": str(report),
        "expected_boundary": bool(expected_boundary),
        "terminal_reason_counts": eval_summary.get("terminal_reason_counts", {}),
        "failure_reason_counts": eval_summary.get("failure_reason_counts", {}),
        "risk_flag_counts": eval_summary.get("risk_flag_counts", {}),
        "by_skill": eval_summary.get("by_skill", {}),
        "shadow": shadow,
        "mismatch_label_counts": mismatch_label_counts,
        "mismatch_examples": mismatch_examples,
    }


def case_action_ok(case: dict[str, Any]) -> bool:
    if bool(case.get("expected_boundary")):
        return int(case.get("success_count", 0)) < int(case.get("episodes", 0))
    return int(case.get("episodes", 0)) > 0 and int(case.get("success_count", 0)) == int(case.get("episodes", 0))


def case_shadow_ok(case: dict[str, Any]) -> bool:
    totals = shadow_totals(case)
    return (
        totals["records"] == int(case.get("episodes", 0))
        and totals["false_failure_on_hold_safe"] == 0
        and totals["missed_failure_or_blocked"] == 0
        and totals["unsafe_predicted_hold_safe"] == 0
    )


def aggregate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "episodes": int(sum(int(case.get("episodes", 0)) for case in cases)),
        "success_count": int(sum(int(case.get("success_count", 0)) for case in cases)),
        "shadow_records": 0,
        "false_failure_on_hold_safe": 0,
        "missed_failure_or_blocked": 0,
        "unsafe_predicted_hold_safe": 0,
        "unsafe_hold_safe_prediction": 0,
        "missed_tactile_handoff": 0,
        "total_label_mismatches": 0,
    }
    for case in cases:
        shadow = shadow_totals(case)
        for key in [
            "records",
            "false_failure_on_hold_safe",
            "missed_failure_or_blocked",
            "unsafe_predicted_hold_safe",
            "unsafe_hold_safe_prediction",
            "missed_tactile_handoff",
            "total_label_mismatches",
        ]:
            target_key = "shadow_records" if key == "records" else key
            totals[target_key] += int(shadow[key])
    totals["action_ok"] = bool(all(case_action_ok(case) for case in cases))
    totals["shadow_ok"] = bool(all(case_shadow_ok(case) for case in cases))
    return totals


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3.11B Online Safety-Head Shadow Mode v0 Closeout\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{payload['status']}`\n",
        f"- safety head：`{payload['head']}`\n",
        "- 模式：shadow only；只记录预测，不改变 MuJoCo 控制动作。\n",
        "- 边界：MuJoCo-only；不是 full-action ACT/DP promotion；不是真实摄像头、真实触觉、超声或硬件 runtime。\n\n",
        "## 做了什么\n\n",
        "Stage3.11B 把 Stage3.10D-C 的 episode-level safety head 接到 Stage3.10C/D evaluator 里。每个 episode 结束后，metadata 会多出 `safety_head_shadow`：包括预测标签、真实标签、概率、mismatch，以及 false failure / missed failure / unsafe hold-safe 计数。这个 head 没有参与动作控制，所以它是旁路观察器，不是上线控制器。\n\n",
        "## 总结果\n\n",
        "| suite | episodes | success | shadow records | false failure | missed failure | unsafe hold-safe | label mismatch |\n",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n",
    ]
    for suite_name in ["db_v1", "stress"]:
        row = payload[f"{suite_name}_summary"]
        lines.append(
            f"| `{suite_name}` | {row['episodes']} | {row['success_count']} | {row['shadow_records']} | "
            f"{row['false_failure_on_hold_safe']} | {row['missed_failure_or_blocked']} | "
            f"{row['unsafe_predicted_hold_safe']} | {row['total_label_mismatches']} |\n"
        )
    lines.extend(
        [
            "\n## Case 明细\n\n",
            "| suite | case | status | success | false failure | missed failure | unsafe hold-safe | mismatch | 风险标记 |\n",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n",
        ]
    )
    for case in payload["cases"]:
        shadow = shadow_totals(case)
        lines.append(
            f"| `{case['suite']}` | `{case['case_id']}` | `{case['status']}` | "
            f"{case['success_count']} / {case['episodes']} | "
            f"{shadow['false_failure_on_hold_safe']} | {shadow['missed_failure_or_blocked']} | "
            f"{shadow['unsafe_predicted_hold_safe']} | {shadow['total_label_mismatches']} | "
            f"`{case.get('risk_flag_counts', {})}` |\n"
        )
    mismatch_cases = [case for case in payload["cases"] if case.get("mismatch_label_counts")]
    if mismatch_cases:
        lines.extend(
            [
                "\n## 非危险 label mismatch\n\n",
                "| case | mismatch labels | examples |\n",
                "| --- | --- | --- |\n",
            ]
        )
        for case in mismatch_cases:
            lines.append(
                f"| `{case['case_id']}` | `{case.get('mismatch_label_counts', {})}` | "
                f"`{case.get('mismatch_examples', [])}` |\n"
            )
    lines.extend(
        [
            "\n## 发现的问题\n\n",
        ]
    )
    if payload["status"] == "PASS":
        lines.extend(
            [
                "- 这次没有发现 hard blocker：D-B v1 与新增 stress 在 shadow mode 下保持通过，且没有 false failure、missed failure 或 unsafe hold-safe prediction。\n",
                "- 仍然有过程风险需要继续记录：`early_contact_in_approach`、`transient_slip_high` 和 `recovery_budget_exhausted` 仍会出现；shadow head 目前只是 episode-level，不能替代逐帧风险标签。\n",
                "- `combined_hard` 仍作为合理拒绝边界：这里的目标不是强行抓，而是确认 safety head 能看到失败/拒绝，不把失败预测成 hold-safe。\n",
            ]
        )
    else:
        lines.extend(
            [
                "- 出现了 Stage3.11B blocker。优先看 case 明细里的 false failure / missed failure / unsafe hold-safe，再回到 metadata 检查特征输入、checkpoint 加载和标签定义。\n",
                "- 不要通过放宽 slip/crush/penetration/final-vision 阈值修复 B；先修 shadow 输入和数据定义。\n",
            ]
        )
    lines.extend(
        [
            "\n## 如果成功\n\n",
            "进入 Stage3.11C：把 shadow mode 里确认过的 safety/vision/tactile 状态展开成逐帧 noisy/occlusion labels，例如 `vision_degraded`、`vision_freeze`、`tactile_handoff`、`repair_active` 和 `risk_any`。\n\n",
            "## 如果失败\n\n",
            "先拆四类原因：feature alignment、checkpoint loading、label definition、online/offline distribution shift。修完 B 后再进入 C，不把错误标签喂给 residual/full-action 训练。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head", type=Path, default=DEFAULT_HEAD)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--db-cases", default="all")
    parser.add_argument("--stress-cases", default="all")
    parser.add_argument("--episodes-per-skill", type=int, default=10)
    parser.add_argument("--stress-episodes-per-skill", type=int, default=None)
    parser.add_argument("--shadow-threshold", type=float, default=0.5)
    parser.add_argument("--quick", action="store_true", help="Run a small 1 episode/skill smoke version of every case.")
    parser.add_argument("--aggregate-existing", action="store_true", help="Read existing Stage3.11B metadata without running MuJoCo.")
    parser.add_argument("--stop-on-fail", action="store_true")
    args = parser.parse_args()

    if bool(args.quick):
        args.episodes_per_skill = 1
        args.stress_episodes_per_skill = 1

    db_cases = selected_cases(str(args.db_cases), list(DB_V1_CASES))
    stress_cases_raw = selected_cases(str(args.stress_cases), list(DD_STRESS_CASES))
    stress_cases: list[StressCase] = []
    for case in stress_cases_raw:
        if args.stress_episodes_per_skill is None:
            stress_cases.append(case)
        else:
            stress_cases.append(replace(case, episodes_per_skill=int(args.stress_episodes_per_skill)))

    cases_out: list[dict[str, Any]] = []
    status_code = 0

    for case in db_cases:
        metadata, report = db_shadow_paths(case, int(args.episodes_per_skill))
        returncode: int | None = None
        if not bool(args.aggregate_existing):
            command = build_db_eval_command(
                case,
                metadata,
                report,
                int(args.episodes_per_skill),
                initial_vision_stress_samples=3,
                final_vision_stress_samples=5,
                policy_vision_quality_mode="accepted_nominal",
                pinch_repair_mode="all",
                pinch_repair_phases="pinch_close,contact_settle,slow_lift,hold",
                pinch_repair_expert_alpha=0.35,
                pinch_repair_preclose_delta=0.10,
                pinch_repair_close_max=0.18,
            )
            command = command_with_shadow(
                command,
                head=Path(args.head),
                case_id=f"dbv1_{case.case_id}",
                threshold=float(args.shadow_threshold),
            )
            print(f"Running Stage3.11B D-B v1 shadow {case.case_id}: {' '.join(command)}", flush=True)
            completed = subprocess.run(command, cwd=str(ROOT), check=False)
            returncode = int(completed.returncode)
            if returncode != 0:
                status_code = returncode
        cases_out.append(
            summarize_metadata(
                suite="db_v1",
                case_id=case.case_id,
                title_zh=case.title_zh,
                metadata=metadata,
                report=report,
                returncode=returncode,
                expected_boundary=False,
            )
        )
        if status_code != 0 and bool(args.stop_on_fail):
            break

    if status_code == 0 or not bool(args.stop_on_fail):
        for case in stress_cases:
            metadata, report = stress_shadow_paths(case)
            returncode = None
            if not bool(args.aggregate_existing):
                command = build_stress_eval_command(case, metadata, report)
                command = command_with_shadow(
                    command,
                    head=Path(args.head),
                    case_id=f"stress_{case.case_id}",
                    threshold=float(args.shadow_threshold),
                )
                print(f"Running Stage3.11B stress shadow {case.case_id}: {' '.join(command)}", flush=True)
                completed = subprocess.run(command, cwd=str(ROOT), check=False)
                returncode = int(completed.returncode)
                if returncode != 0 and not bool(case.expected_boundary):
                    status_code = returncode
            cases_out.append(
                summarize_metadata(
                    suite="stress",
                    case_id=case.case_id,
                    title_zh=case.title_zh,
                    metadata=metadata,
                    report=report,
                    returncode=returncode,
                    expected_boundary=bool(case.expected_boundary),
                )
            )
            if status_code != 0 and bool(args.stop_on_fail):
                break

    db_summary = aggregate_cases([case for case in cases_out if case["suite"] == "db_v1"])
    stress_summary = aggregate_cases([case for case in cases_out if case["suite"] == "stress"])
    action_ok = bool(db_summary["action_ok"] and stress_summary["action_ok"])
    shadow_ok = bool(db_summary["shadow_ok"] and stress_summary["shadow_ok"])
    status = "PASS" if action_ok and shadow_ok else "NEEDS_REPAIR"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11B",
        "status": status,
        "head": str(Path(args.head).resolve()),
        "shadow_threshold": float(args.shadow_threshold),
        "mode": "online_evaluator_shadow_no_action_effect",
        "db_v1_summary": db_summary,
        "stress_summary": stress_summary,
        "cases": cases_out,
        "stage3_11b_ready_for_c": bool(status == "PASS"),
        "boundary": {
            "mujoco_only": True,
            "full_action_act_dp_promoted": False,
            "hardware_runtime": False,
            "real_camera": False,
            "real_tactile": False,
            "ultrasound_runtime": False,
            "combined_hard_initial_vision_boundary": True,
        },
        "next": "Stage3.11C frame-level noisy/occlusion safety labels if PASS; otherwise repair shadow feature/label alignment.",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(Path(args.report), payload)
    print(json.dumps({"status": status, "db_v1": db_summary, "stress": stress_summary}, ensure_ascii=False, indent=2))
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")
    return status_code if status_code != 0 else (0 if status == "PASS" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
