#!/usr/bin/env python3
"""Run a minimal batch evaluation harness for stable_grasp episode summaries."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tasks import build_report_payload  # noqa: E402
from tasks.behavior_audit import build_stable_grasp_behavior_audit  # noqa: E402
from scripts.diagnostics.structured_rollout_eval import (  # noqa: E402
    CANONICAL_ENTRY_SNAPSHOT_OWNER,
    ROLLOUT_MODE_DIAGNOSTIC_SEEDED,
    ROLLOUT_MODE_ENVIRONMENT_ONLY,
    run_pre_grasp_to_stable_grasp_episode,
)
from scripts.common.grasp_workflow import (  # noqa: E402
    STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
    STABLE_GRASP_PHASE_MODE_ZERO_ACTION,
)


def _serialize_value(value):
    """Convert numpy-heavy debug payloads into JSON-friendly values."""
    if isinstance(value, np.ndarray):
        return value.astype(np.float32).tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    return value


def run_batch_eval(
    eval_mode: str,
    num_episodes: int,
    pre_grasp_steps: int,
    stable_grasp_steps: int,
    max_steps: int,
    include_debug: bool,
    stable_grasp_phase_mode: str,
):
    """Run a small batch of structured episodes and emit official plus audit artifacts."""
    episode_artifacts = []
    episode_results = []
    for episode_index in range(int(num_episodes)):
        artifact = run_pre_grasp_to_stable_grasp_episode(
            rollout_mode=eval_mode,
            pre_grasp_steps=pre_grasp_steps,
            stable_grasp_steps=stable_grasp_steps,
            max_steps=max_steps,
            include_debug=include_debug,
            stable_grasp_phase_mode=stable_grasp_phase_mode,
        )
        episode_artifacts.append(artifact)
        episode_results.append(artifact["episode_result"])

    official_report = build_report_payload(
        config={
            "script": "scripts/diagnostics/batch_eval_stable_grasp.py",
            "task_name": "stable_grasp",
            "eval_mode": eval_mode,
            "official_eval_eligible": bool(eval_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY),
            "entry_snapshot_owner": CANONICAL_ENTRY_SNAPSHOT_OWNER,
            "entry_snapshot_fallback_owner": "stable_grasp_checker",
            "backend_type": "shadow_backend",
            "backend_note": (
                "Temporary Shadow backend. Environment-driven mode is the official harness path; "
                "diagnostic seeded mode is preserved for protocol verification only."
            ),
            "num_episodes": int(num_episodes),
            "pre_grasp_steps": int(pre_grasp_steps),
            "stable_grasp_steps": int(stable_grasp_steps),
            "stable_grasp_phase_mode": str(stable_grasp_phase_mode),
            "max_steps": int(max_steps),
        },
        episode_results=episode_results,
        include_debug=False,
    )

    behavior_audit = build_stable_grasp_behavior_audit(
        episode_artifacts=episode_artifacts,
        eval_mode=eval_mode,
        stable_grasp_phase_mode=stable_grasp_phase_mode,
        include_debug=include_debug,
    )

    batch_payload = {
        "official_report": official_report,
        "behavior_audit": behavior_audit,
        "notes": (
            "official_report keeps only official task metrics and terminal fields. "
            "behavior_audit is an analysis-only layer for scripted-controller behavior quality, "
            "failure attribution, and temporary data-collection readiness."
        ),
    }

    if include_debug:
        batch_payload["debug"] = {
            "episode_diagnostics": [
                {
                    "episode_index": int(index),
                    "rollout_mode": artifact["rollout_mode"],
                    "state_preparation": _serialize_value(artifact["state_preparation"]),
                    "stable_grasp_phase_mode": artifact["stable_grasp_phase_mode"],
                    "phase_debug": _serialize_value(artifact["phase_debug"]),
                    "transition_decision": _serialize_value(artifact["transition_decision"]),
                    "entry_snapshot": _serialize_value(artifact["entry_snapshot"]),
                }
                for index, artifact in enumerate(episode_artifacts)
            ],
            "notes": (
                "Detailed rollout and controller traces remain debug-only. They are not folded "
                "into the official report or the default audit artifact."
            ),
        }

    return _serialize_value(batch_payload)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Minimal batch evaluation harness for stable_grasp. "
            "Use environment_only for the official batch-eval path shape; "
            "diagnostic_seeded remains a protocol verification mode only."
        )
    )
    parser.add_argument(
        "--eval-mode",
        type=str,
        default=ROLLOUT_MODE_ENVIRONMENT_ONLY,
        choices=[ROLLOUT_MODE_ENVIRONMENT_ONLY, ROLLOUT_MODE_DIAGNOSTIC_SEEDED],
        help="Episode rollout mode",
    )
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=2,
        help="Number of episodes to evaluate",
    )
    parser.add_argument(
        "--pre-grasp-steps",
        type=int,
        default=40,
        help="Maximum pre_grasp phase steps per episode",
    )
    parser.add_argument(
        "--stable-grasp-steps",
        type=int,
        default=12,
        help="Maximum stable_grasp phase steps per episode",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=64,
        help="Environment max_steps per episode",
    )
    parser.add_argument(
        "--stable-grasp-phase-mode",
        type=str,
        default=STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
        choices=[
            STABLE_GRASP_PHASE_MODE_ZERO_ACTION,
            STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
        ],
        help="Stable_grasp continuation mode",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="",
        help="Optional JSON output path for the combined official-report plus audit artifact",
    )
    parser.add_argument(
        "--official-report",
        type=str,
        default="",
        help="Optional JSON output path for the official report only",
    )
    parser.add_argument(
        "--audit-report",
        type=str,
        default="",
        help="Optional JSON output path for the behavior-audit artifact only",
    )
    parser.add_argument(
        "--include-debug",
        action="store_true",
        help="Include debug traces in the top-level debug section without changing official_report",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent level",
    )
    args = parser.parse_args()

    batch_payload = run_batch_eval(
        eval_mode=args.eval_mode,
        num_episodes=args.num_episodes,
        pre_grasp_steps=args.pre_grasp_steps,
        stable_grasp_steps=args.stable_grasp_steps,
        max_steps=args.max_steps,
        include_debug=args.include_debug,
        stable_grasp_phase_mode=args.stable_grasp_phase_mode,
    )

    text = json.dumps(batch_payload, indent=args.indent, ensure_ascii=False)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text + "\n", encoding="utf-8")
    if args.official_report:
        report_path = Path(args.official_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_text = json.dumps(
            batch_payload["official_report"],
            indent=args.indent,
            ensure_ascii=False,
        )
        report_path.write_text(report_text + "\n", encoding="utf-8")
    if args.audit_report:
        report_path = Path(args.audit_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_text = json.dumps(
            batch_payload["behavior_audit"],
            indent=args.indent,
            ensure_ascii=False,
        )
        report_path.write_text(report_text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
