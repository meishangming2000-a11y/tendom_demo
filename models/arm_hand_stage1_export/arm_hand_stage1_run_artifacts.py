#!/usr/bin/env python3
"""Helpers for standardized arm-hand Stage1 experiment run folders."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SIM_ROOT = ROOT.parents[1]
PROJECT_ROOT = ROOT.parents[2]
RUNS_ROOT = ROOT / "runs"


RUN_SUBDIRS = ("logs", "checkpoints", "datasets", "eval", "traces", "visuals")


def timestamp_for_run(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def write_simple_yaml(path: Path, payload: dict[str, Any]) -> None:
    def emit(obj: Any, indent: int = 0) -> list[str]:
        pad = " " * indent
        lines: list[str] = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list, tuple)):
                    lines.append(f"{pad}{key}:")
                    lines.extend(emit(value, indent + 2))
                else:
                    lines.append(f"{pad}{key}: {yaml_scalar(value)}")
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                if isinstance(item, (dict, list, tuple)):
                    lines.append(f"{pad}-")
                    lines.extend(emit(item, indent + 2))
                else:
                    lines.append(f"{pad}- {yaml_scalar(item)}")
        else:
            lines.append(f"{pad}{yaml_scalar(obj)}")
        return lines

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(emit(json_ready(payload))) + "\n", encoding="utf-8")


def run_git(repo: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover - defensive metadata capture
        return f"<git command failed: {exc}>"
    text = (result.stdout or result.stderr).strip()
    return text if text else "<empty>"


def git_block(name: str, repo: Path) -> str:
    lines = [
        f"## {name}",
        f"path: {repo}",
        f"branch: {run_git(repo, ['branch', '--show-current'])}",
        f"head: {run_git(repo, ['rev-parse', '--short', 'HEAD'])}",
        "",
        "status:",
        run_git(repo, ["status", "--short", "--branch"]),
        "",
    ]
    return "\n".join(lines)


def capture_git_info() -> str:
    return "\n".join(
        [
            git_block("outer_repo", PROJECT_ROOT),
            git_block("simulations_repo", SIM_ROOT),
        ]
    )


def build_config_lock(
    *,
    task: str,
    seed: int,
    run_id: str,
    run_dir: Path,
    config_source: Path | None,
    notes: str,
) -> dict[str, Any]:
    return {
        "run": {
            "id": run_id,
            "task": task,
            "seed": seed,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "run_dir": str(run_dir),
            "notes": notes,
        },
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "simulations_root": str(SIM_ROOT),
            "workspace_root": str(ROOT),
            "config_source": str(config_source) if config_source else None,
            "logs": "logs/",
            "checkpoints": "checkpoints/",
            "datasets": "datasets/",
            "eval": "eval/",
            "traces": "traces/",
            "visuals": "visuals/",
        },
        "expected_outputs": {
            "required": [
                "config.lock.yaml",
                "command.txt",
                "git_info.txt",
                "report.md",
                "eval/summary.json",
                "eval/episodes.jsonl",
            ],
            "default_visuals": [
                "visuals/contact_sheet.png",
                "visuals/trajectory_topdown.png",
                "visuals/target_sweep_heatmap.png",
            ],
            "selected_mp4_only": True,
        },
        "gates": {
            "dataset_replay_qa_required": True,
            "offline_train_loss_is_not_success": True,
            "online_eval_required": True,
            "rl_blocked_until_reward_and_holdout_qa": True,
        },
    }


def write_report_template(run_dir: Path, *, task: str, run_id: str) -> None:
    report = run_dir / "report.md"
    lines = [
        f"# Arm-Hand Stage1 Run Report: {run_id}\n\n",
        f"- Task: `{task}`\n",
        "- Status: `initialized`\n",
        "- Dataset gate: `pending`\n",
        "- Training gate: `pending`\n",
        "- Evaluation gate: `pending`\n\n",
        "## Purpose\n\n",
        "This run folder is the source record for one training/evaluation attempt.\n",
        "Append dataset, training, evaluation, trace, and visualization outputs here.\n\n",
        "## Required Next Steps\n\n",
        "1. Collect or attach dataset outputs under `datasets/`.\n",
        "2. Run replay QA and write `eval/replay_qa_summary.json`.\n",
        "3. Train the first checkpoint under `checkpoints/`.\n",
        "4. Run fixed-target and narrow target-sweep eval.\n",
        "5. Generate contact sheet, top-down trajectory, and target heatmap.\n\n",
        "## Viewer / Video Policy\n\n",
        "- Use MuJoCo viewer for interactive inspection.\n",
        "- Render only selected MP4s: best, worst, and representative failures.\n",
        "- Keep replayable traces as the source of truth.\n\n",
        "## Current Pick-Place Scripted Viewer\n\n",
        "```powershell\n",
        "cd D:\\tendon_project\\simulations\n",
        "python .\\models\\arm_hand_stage1_export\\demo_arm_hand_stage1_v3_pick_place_scripted.py --viewer --no-render-video --no-render-snapshots\n",
        "```\n",
    ]
    report.write_text("".join(lines), encoding="utf-8")


def initialize_run(
    *,
    task: str,
    seed: int,
    config_source: Path | None,
    command_line: str,
    notes: str = "",
    run_id: str | None = None,
) -> Path:
    run_id = run_id or f"{timestamp_for_run()}_seed{seed:03d}"
    run_dir = RUNS_ROOT / task / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    for name in RUN_SUBDIRS:
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    lock = build_config_lock(
        task=task,
        seed=seed,
        run_id=run_id,
        run_dir=run_dir,
        config_source=config_source,
        notes=notes,
    )
    write_simple_yaml(run_dir / "config.lock.yaml", lock)
    (run_dir / "command.txt").write_text(command_line.strip() + "\n", encoding="utf-8")
    (run_dir / "git_info.txt").write_text(capture_git_info(), encoding="utf-8")
    if config_source:
        (run_dir / "config.source.yaml").write_text(config_source.read_text(encoding="utf-8"), encoding="utf-8")
    write_report_template(run_dir, task=task, run_id=run_id)
    return run_dir


def write_manifest(run_dir: Path) -> None:
    files = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file():
            files.append(str(path.relative_to(run_dir)))
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_dir": str(run_dir),
        "files": files,
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
