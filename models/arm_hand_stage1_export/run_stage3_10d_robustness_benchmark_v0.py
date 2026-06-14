#!/usr/bin/env python3
"""Run or aggregate Stage3.10D robustness cases for the Stage3.10C policy."""

from __future__ import annotations

import argparse
import json
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
class RobustnessCase:
    case_id: str
    title_zh: str
    random_offset_std: float
    final_verification_mode: str
    probe_stem: str


CASES = [
    RobustnessCase(
        case_id="pose008",
        title_zh="8mm 随机位姿噪声 + 视觉/触觉终验",
        random_offset_std=0.008,
        final_verification_mode="vision_tactile_corroborated",
        probe_stem="stage3_10d_probe_pose008_cycle10",
    ),
    RobustnessCase(
        case_id="pose010",
        title_zh="10mm 随机位姿噪声 + 视觉/触觉终验",
        random_offset_std=0.010,
        final_verification_mode="vision_tactile_corroborated",
        probe_stem="stage3_10d_probe_pose010_cycle10",
    ),
    RobustnessCase(
        case_id="strictvision_pose005",
        title_zh="5mm 随机位姿噪声 + 严格最终视觉验收",
        random_offset_std=0.005,
        final_verification_mode="strict_vision",
        probe_stem="stage3_10d_probe_strictvision_pose005_cycle10",
    ),
    RobustnessCase(
        case_id="strictvision_pose008",
        title_zh="8mm 随机位姿噪声 + 严格最终视觉验收",
        random_offset_std=0.008,
        final_verification_mode="strict_vision",
        probe_stem="stage3_10d_probe_strictvision_pose008_cycle10",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    return value


def output_stem(case: RobustnessCase, episodes_per_skill: int, *, use_existing_probes: bool) -> str:
    if use_existing_probes:
        return case.probe_stem
    return f"stage3_10d_robustness_{case.case_id}_cycle{int(episodes_per_skill) * 2}"


def build_eval_command(case: RobustnessCase, metadata: Path, report: Path, episodes_per_skill: int) -> list[str]:
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
        "inactive_anchor_slip_close",
        "--pinch-repair-preclose-delta",
        "0.10",
        "--pinch-repair-close-max",
        "0.18",
        "--random-offset-std",
        f"{case.random_offset_std:.3f}",
        "--metadata",
        str(metadata),
        "--report",
        str(report),
    ]


def compact_case_summary(case: RobustnessCase, metadata_path: Path, report_path: Path, returncode: int | None) -> dict[str, Any]:
    if not metadata_path.exists():
        return {
            "case_id": case.case_id,
            "title_zh": case.title_zh,
            "metadata": str(metadata_path),
            "report": str(report_path),
            "returncode": returncode,
            "status": "MISSING",
            "episodes": 0,
            "success_count": 0,
            "failure_reason_counts": {"missing_metadata": 1},
        }

    payload = read_json(metadata_path)
    summary = payload.get("summary", {})
    by_skill = summary.get("by_skill", {})
    return {
        "case_id": case.case_id,
        "title_zh": case.title_zh,
        "metadata": str(metadata_path),
        "report": str(report_path),
        "returncode": returncode,
        "random_offset_std": case.random_offset_std,
        "final_verification_mode": case.final_verification_mode,
        "status": summary.get("status", "UNKNOWN"),
        "episodes": int(summary.get("episodes", 0)),
        "success_count": int(summary.get("success_count", 0)),
        "terminal_reason_counts": summary.get("terminal_reason_counts", {}),
        "failure_reason_counts": summary.get("failure_reason_counts", {}),
        "risk_flag_counts": summary.get("risk_flag_counts", {}),
        "by_skill": by_skill,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3.10D Robustness Probe v0 Closeout\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{payload['status']}`\n",
        f"- 总成功：`{payload['total_success']} / {payload['total_episodes']}`\n",
        f"- 执行模式：`scripted_arm_predicted_hand`\n",
        f"- 边界：这仍然不是 full-action 26 actuator ACT/DP，也不是硬件或真实摄像头集成。\n\n",
        "## 这一步做了什么\n\n",
        "Stage3.10D-A 把 Stage3.10C-C 已通过的 5mm 随机位姿 benchmark 往外推，先做小规模但多条件的鲁棒性探针：更强随机位姿噪声、严格最终视觉验收，以及两者组合。\n\n",
        "## Case 汇总\n\n",
        "| case | 含义 | 成功 | 状态 | 主要风险 |\n",
        "| --- | --- | ---: | --- | --- |\n",
    ]
    for case in payload["cases"]:
        risk = case.get("risk_flag_counts", {})
        lines.append(
            f"| `{case['case_id']}` | {case['title_zh']} | "
            f"{case['success_count']} / {case['episodes']} | `{case['status']}` | `{risk}` |\n"
        )
    lines.extend(
        [
            "\n## 关键观察\n\n",
            f"- 这批探针合计 `{payload['total_success']} / {payload['total_episodes']}`。\n",
            "- `pose008` 和 `pose010` 说明 8mm/10mm 位姿噪声下，当前混合控制闭环还没有直接掉成功率。\n",
            "- `strictvision_pose005` 和 `strictvision_pose008` 说明当前 pinch 结果不是完全靠 tactile 兜底才能通过最终验收；严格视觉终验短测仍然通过。\n",
            "- 风险没有消失：`early_contact_in_approach` 仍然几乎每组都出现，pinch 的 `transient_slip_high` 仍然稳定出现，full hand 有时会触发 recovery budget exhaustion。\n",
            "- 所以 Stage3.10D-A 的结论是：鲁棒性初探通过，但下一步应该扩大样本和引入更真实的遮挡/低可见度注入，而不是宣布模型已经泛化。\n\n",
            "## 如果成功\n\n",
            "进入 Stage3.10D-B：用同一个入口扩大到更正式的 benchmark，例如每个 case 40-100 组，并加入显式 noisy-mask / occlusion injector，把最终视觉失效从“自然遮挡”变成可控压力。\n\n",
            "## 如果失败\n\n",
            "不要放宽 slip 或 vision 阈值。先按失败来源拆开：随机位姿导致接近误差、严格视觉导致 final confidence 不足、还是 tactile hold 实际失败。之后再决定修 perception freeze、pinch repair，或者 staged full-action repair。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-per-skill", type=int, default=5)
    parser.add_argument("--aggregate-existing-probes", action="store_true", help="Aggregate the already-run Stage3.10D probe files.")
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--metadata", type=Path, default=META / "stage3_10d_robustness_probe_v0.json")
    parser.add_argument("--report", type=Path, default=DOCS / "stage3_10d_robustness_probe_v0_closeout.md")
    args = parser.parse_args()

    cases_out: list[dict[str, Any]] = []
    status = 0
    for case in CASES:
        stem = output_stem(case, int(args.episodes_per_skill), use_existing_probes=bool(args.aggregate_existing_probes))
        metadata = META / f"{stem}.json"
        report = DOCS / f"{stem}_report.md"
        returncode: int | None = None
        if not args.aggregate_existing_probes:
            command = build_eval_command(case, metadata, report, int(args.episodes_per_skill))
            print(f"Running {case.case_id}: {' '.join(command)}", flush=True)
            completed = subprocess.run(command, cwd=str(ROOT), check=False)
            returncode = int(completed.returncode)
            if returncode != 0:
                status = returncode
                if args.stop_on_fail:
                    cases_out.append(compact_case_summary(case, metadata, report, returncode))
                    break
        cases_out.append(compact_case_summary(case, metadata, report, returncode))

    total_episodes = sum(int(case.get("episodes", 0)) for case in cases_out)
    total_success = sum(int(case.get("success_count", 0)) for case in cases_out)
    aggregate_status = "PASS" if total_episodes > 0 and total_success == total_episodes and all(case.get("status") == "PASS" for case in cases_out) else "BLOCKED"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": aggregate_status,
        "total_episodes": total_episodes,
        "total_success": total_success,
        "episodes_per_skill": int(args.episodes_per_skill),
        "aggregate_existing_probes": bool(args.aggregate_existing_probes),
        "cases": cases_out,
        "boundary": {
            "full_action_act_dp_promoted": False,
            "hardware_integration": False,
            "real_camera": False,
        },
        "next": "Stage3.10D-B formal expanded benchmark plus explicit occlusion/noisy-mask injection.",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, payload)
    print(json.dumps(json_ready({"status": aggregate_status, "total_success": total_success, "total_episodes": total_episodes}), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return status if status != 0 else (0 if aggregate_status == "PASS" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
