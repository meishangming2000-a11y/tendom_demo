#!/usr/bin/env python3
"""Check and optionally smoke-test the frozen Stage3.10A safety layer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "configs" / "stage3_10a_skillzoo_safety_layer_v0.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_root(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def check_metadata(path: Path, expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    data = read_json(path)
    summary = data.get("summary", {})
    for key in ("status", "episodes", "success_count"):
        if key in expected and summary.get(key) != expected[key]:
            errors.append(f"{path}: summary.{key}={summary.get(key)!r}, expected {expected[key]!r}")
    per_skill_expected = expected.get("per_skill_success", {})
    by_skill = summary.get("by_skill", {})
    for skill_id, expected_text in per_skill_expected.items():
        skill_summary = by_skill.get(skill_id, {})
        actual_text = f"{skill_summary.get('success_count')}/{skill_summary.get('episodes')}"
        if actual_text != expected_text:
            errors.append(f"{path}: {skill_id} success={actual_text}, expected {expected_text}")
    return errors


def check_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    checked: list[str] = []

    required_refs = [
        config["canonical_eval"]["script"],
        config["canonical_eval"]["checkpoint"],
        config["canonical_eval"]["selected_pinch_config"],
        config["canonical_eval"]["metadata"],
        config["canonical_eval"]["report"],
        config["pinch_final_vision_check"]["metadata"],
        config["pinch_final_vision_check"]["report"],
        config["control_stack"]["full_hand_gentle_grasp"]["checkpoint"],
    ]
    for ref in required_refs:
        path = resolve_root(ref)
        checked.append(str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path))
        if not path.exists():
            errors.append(f"missing referenced file: {ref}")

    canonical_meta = resolve_root(config["canonical_eval"]["metadata"])
    if canonical_meta.exists():
        errors.extend(check_metadata(canonical_meta, config["canonical_eval"]["expected"]))
    pinch_meta = resolve_root(config["pinch_final_vision_check"]["metadata"])
    if pinch_meta.exists():
        errors.extend(check_metadata(pinch_meta, config["pinch_final_vision_check"]["expected"]))

    if config.get("boundary", {}).get("full_action_act_dp_promoted") is not False:
        errors.append("boundary.full_action_act_dp_promoted must remain false in Stage3.10A")
    if config.get("boundary", {}).get("hardware_integration") is not False:
        errors.append("boundary.hardware_integration must remain false in Stage3.10A")

    return errors, checked


def build_eval_command(config: dict[str, Any], *, smoke: bool) -> list[str]:
    block = config["smoke_eval"] if smoke else config["canonical_eval"]
    args = [
        sys.executable,
        str(ROOT / config["canonical_eval"]["script"]),
        "--checkpoint",
        config["canonical_eval"]["checkpoint"],
        "--selected-pinch-config",
        config["canonical_eval"]["selected_pinch_config"],
        "--metadata",
        block["metadata"],
        "--report",
        block["report"],
    ]
    args.extend(str(item) for item in block["args"])
    return args


def run_smoke(config: dict[str, Any]) -> int:
    command = build_eval_command(config, smoke=True)
    print("Running Stage3.10A smoke eval:")
    print(" ".join(command), flush=True)
    completed = subprocess.run(command, cwd=str(ROOT), text=True, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--check", action="store_true", help="Validate referenced files and frozen evidence.")
    parser.add_argument("--print-command", action="store_true", help="Print the canonical 100-episode eval command.")
    parser.add_argument("--run-smoke", action="store_true", help="Run a 4-episode smoke check using the frozen safety layer.")
    args = parser.parse_args()

    config_path = args.config if args.config.is_absolute() else (Path.cwd() / args.config)
    config = read_json(config_path)

    status = 0
    if args.check or not (args.print_command or args.run_smoke):
        errors, checked = check_config(config)
        print(f"Stage3.10A safety layer: {config['status']} ({config['version']})")
        print(f"checked_refs={len(checked)}")
        for ref in checked:
            print(f"  ok: {ref}")
        if errors:
            print("CHECK FAIL")
            for error in errors:
                print(f"  {error}")
            status = 1
        else:
            print("CHECK PASS")

    if args.print_command:
        print("Canonical eval command:")
        print(" ".join(build_eval_command(config, smoke=False)))

    if args.run_smoke:
        smoke_status = run_smoke(config)
        if smoke_status != 0:
            status = smoke_status

    return status


if __name__ == "__main__":
    raise SystemExit(main())
