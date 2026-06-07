#!/usr/bin/env python3
"""Run the Stage3.9C SkillZoo rule router.

This command validates the Stage3.9 skill registry, routes compact scene
descriptors to skills, and optionally smoke-tests executable demo entrypoints.
It does not train a model and it does not use an LLM/VLA.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from arm_hand_stage1_task_api import json_ready
from stage3_skillzoo_v0 import (
    DEFAULT_REGISTRY,
    DEFAULT_SCENES,
    ROOT,
    load_registry,
    load_scene_cases,
    route_scene,
    smoke_command_for_skill,
    summarize_registry,
)


DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_REPORT = DOCS / "stage3_skill_router_v0_startup_report.md"
DEFAULT_METADATA = META / "stage3_skill_router_v0_startup.json"


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Stage3.9C Skill Router v0 启动报告",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- registry：`{payload['registry']}`",
        f"- scene_cases：`{payload['scene_cases']}`",
        f"- 状态：`{summary['status']}`",
        f"- 技能数量：`{summary['registry']['skill_count']}`",
        f"- 可执行技能数量：`{summary['registry']['executable_skill_count']}`",
        f"- 路由样例数量：`{summary['case_count']}`",
        f"- expectation 通过：`{summary['expectation_pass_count']} / {summary['expectation_checked_count']}`",
        "",
        "## 路由结果",
        "",
        "| case | selected skill | status | reason | confidence | expected | ok | executable |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["decisions"]:
        ok = row["matches_expectation"]
        ok_text = "n/a" if ok is None else ("PASS" if ok else "FAIL")
        lines.append(
            "| {case_id} | {selected_skill_id} | {selected_status} | {decision_reason} | {confidence:.4f} | {expected} | {ok} | {exe} |".format(
                case_id=row["case_id"],
                selected_skill_id=row["selected_skill_id"],
                selected_status=row["selected_status"],
                decision_reason=row["decision_reason"],
                confidence=float(row["confidence"]),
                expected=row.get("expected_skill_id") or "",
                ok=ok_text,
                exe="yes" if row["executable"] else "no",
            )
        )
    lines.extend(["", "## Smoke 测试", ""])
    if payload["smoke_results"]:
        lines.append("| skill | status | command | note |")
        lines.append("| --- | --- | --- | --- |")
        for row in payload["smoke_results"]:
            command = " ".join(row.get("command", []))
            tail = row.get("stdout_tail") or row.get("stderr_tail") or ""
            if isinstance(tail, list):
                note = "<br>".join(str(item) for item in tail)
            else:
                note = str(tail).replace("\n", "<br>")
            lines.append(f"| {row['skill_id']} | {row['status']} | `{command}` | {note} |")
    else:
        lines.append("本次没有运行 demo smoke。使用 `--run-smoke` 可以对已注册可执行技能做无窗口检查。")
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "这一步只证明 Stage3.9 的技能注册和规则路由入口已经可检查；它还不是 ACT/Diffusion Policy 训练，也不是 LLM/VLA 调度。",
            "",
            "如果成功：下一步进入 Stage3.9B，开始把 Stage3.7D 和 Stage3.8B episode 转成统一数据格式。",
            "",
            "如果失败：先修 registry、scene case、success gate 和 failure taxonomy，不扩大到模型训练。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_smoke(registry: dict[str, Any], skill_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for skill_id in skill_ids:
        command = smoke_command_for_skill(registry, skill_id)
        if not command:
            rows.append(
                {
                    "skill_id": skill_id,
                    "status": "SKIP",
                    "command": [],
                    "stdout_tail": "",
                    "stderr_tail": "no smoke command registered",
                }
            )
            continue
        full_command = [sys.executable, *command]
        completed = subprocess.run(
            full_command,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        rows.append(
            {
                "skill_id": skill_id,
                "status": "PASS" if completed.returncode == 0 else "FAIL",
                "returncode": completed.returncode,
                "command": full_command,
                "stdout_tail": completed.stdout.strip().splitlines()[-3:],
                "stderr_tail": completed.stderr.strip().splitlines()[-3:],
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--scene-cases", type=Path, default=DEFAULT_SCENES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--no-check-expectations", action="store_true")
    parser.add_argument("--run-smoke", action="store_true")
    parser.add_argument(
        "--smoke-skill",
        action="append",
        default=[],
        help="Skill id to smoke-test. Can be repeated. Defaults to selected executable skills.",
    )
    args = parser.parse_args()

    registry = load_registry(args.registry)
    cases = load_scene_cases(args.scene_cases)
    decisions = [route_scene(registry, case).to_dict() for case in cases]

    checked = [row for row in decisions if row["matches_expectation"] is not None]
    expectation_pass_count = sum(int(bool(row["matches_expectation"])) for row in checked)
    status = "PASS"
    if checked and expectation_pass_count != len(checked):
        status = "FAIL"

    smoke_results: list[dict[str, Any]] = []
    if args.run_smoke:
        smoke_ids = list(args.smoke_skill)
        if not smoke_ids:
            smoke_ids = sorted({row["selected_skill_id"] for row in decisions if row["executable"]})
        smoke_results = run_smoke(registry, smoke_ids)
        if any(row["status"] == "FAIL" for row in smoke_results):
            status = "FAIL"

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "registry": str(args.registry),
        "scene_cases": str(args.scene_cases),
        "summary": {
            "status": status,
            "registry": summarize_registry(registry),
            "case_count": len(cases),
            "expectation_checked_count": len(checked),
            "expectation_pass_count": expectation_pass_count,
            "smoke_count": len(smoke_results),
        },
        "decisions": decisions,
        "smoke_results": smoke_results,
    }

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report, payload)

    print(
        "Stage3.9C skill router: "
        f"status={status} "
        f"cases={len(cases)} "
        f"expectations={expectation_pass_count}/{len(checked)} "
        f"smoke={len(smoke_results)}"
    )
    print(f"report={args.report}")
    print(f"metadata={args.metadata}")
    if status != "PASS" and not args.no_check_expectations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
