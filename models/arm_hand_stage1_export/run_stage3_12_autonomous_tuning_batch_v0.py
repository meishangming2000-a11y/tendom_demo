#!/usr/bin/env python3
"""Stage3.12 autonomous batch tuning scoreboard.

This script runs a bounded MuJoCo-only smoke batch around the frozen
Stage3.11D-I diagnostic candidate. It is an orchestrator around the existing
Stage3.11D-B event/contact-gated robustness runner; it does not change or
promote the controller.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DATA = ROOT / "data"

DEFAULT_SELECTED = META / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_REPORT = DOCS / "stage3_12_autotune_batch0_v0_report.md"
DEFAULT_METADATA = META / "stage3_12_autotune_batch0_v0.json"
DEFAULT_SUMMARY_CSV = DATA / "stage3_12_autotune_batch0_summary_v0.csv"
ROBUST_RUNNER = ROOT / "run_stage3_11d_b_event_contact_gated_robustness_v0.py"


@dataclass(frozen=True)
class Candidate:
    name: str
    family: str
    description: str
    overrides: dict[str, Any] = field(default_factory=dict)


def candidate_grid() -> list[Candidate]:
    return [
        Candidate(
            "baseline_di",
            "baseline",
            "Frozen D-I diagnostic candidate.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 480,
            },
        ),
        Candidate(
            "contact_gz0023",
            "contact_entry",
            "Slightly higher contact target to reduce contact-gate misses while staying close to D-I.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0023,
                "override_lift_steps": 480,
            },
        ),
        Candidate(
            "robust_gz0025_watch_nontip",
            "contact_entry",
            "D-H-like higher z robustness comparison; must be rejected if non-tip/wrap increases.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0025,
                "override_lift_steps": 480,
            },
        ),
        Candidate(
            "lift_ls460",
            "lift_continuation",
            "Slightly faster lift timing to test whether shorter lift reduces transition loss.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 460,
            },
        ),
        Candidate(
            "lift_ls500",
            "lift_continuation",
            "Slightly slower lift timing to test whether more lift samples improve hold evidence.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 500,
            },
        ),
        Candidate(
            "sep058",
            "morphology_clean",
            "Narrower tip-pair separation to test cleaner two-tip capture.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 480,
                "override_tip_pair_separation": 0.058,
            },
        ),
        Candidate(
            "sep062",
            "morphology_clean",
            "Wider tip-pair separation to test whether contact gate becomes less brittle.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 480,
                "override_tip_pair_separation": 0.062,
            },
        ),
        Candidate(
            "active_abd_m048",
            "morphology_clean",
            "Slightly less active-finger abduction to reduce side/nontip contact risk.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 480,
                "override_active_abd": -0.48,
            },
        ),
        Candidate(
            "ls460_sep058",
            "lift_morphology_combo",
            "Best lift timing from Batch1 plus narrower separation for cleaner true-tip morphology.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 460,
                "override_tip_pair_separation": 0.058,
            },
        ),
        Candidate(
            "ls460_sep062",
            "lift_morphology_combo",
            "Best lift timing from Batch1 plus wider separation for less brittle contact entry.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 460,
                "override_tip_pair_separation": 0.062,
            },
        ),
        Candidate(
            "ls460_active_abd_m048",
            "lift_morphology_combo",
            "Best lift timing plus slightly less active-finger abduction.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0022,
                "override_lift_steps": 460,
                "override_active_abd": -0.48,
            },
        ),
        Candidate(
            "ls460_gz0023",
            "lift_contact_combo",
            "Best lift timing plus slightly higher contact target.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0023,
                "override_lift_steps": 460,
            },
        ),
        Candidate(
            "ls460_gz0021",
            "lift_contact_combo",
            "Best lift timing plus slightly lower contact target to test morphology stability.",
            {
                "override_grasp_offset_x": -0.0014,
                "override_grasp_offset_z": 0.0021,
                "override_lift_steps": 460,
            },
        ),
    ]


def flag_to_cli(name: str) -> str:
    return "--" + name.replace("_", "-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Stage3.12 autonomous tuning batch 0.")
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--batch-id", default="stage3_12_autotune_batch0")
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260614)
    parser.add_argument("--max-candidates", type=int, default=0, help="0 means all candidates.")
    parser.add_argument("--candidate", action="append", default=None, help="Candidate name to run; repeatable.")
    parser.add_argument("--force", action="store_true", help="Rerun even when per-candidate metadata exists.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def per_candidate_paths(candidate: Candidate, args: argparse.Namespace) -> tuple[Path, Path]:
    report = DOCS / f"{args.batch_id}_{candidate.name}_report.md"
    metadata = META / f"{args.batch_id}_{candidate.name}.json"
    return report, metadata


def run_candidate(candidate: Candidate, args: argparse.Namespace) -> dict[str, Any]:
    report, metadata = per_candidate_paths(candidate, args)
    command = [
        sys.executable,
        str(ROBUST_RUNNER),
        "--selected",
        str(args.selected),
        "--trials",
        str(args.trials),
        "--seed",
        str(args.seed),
        "--report",
        str(report),
        "--metadata",
        str(metadata),
    ]
    for key, value in candidate.overrides.items():
        command.extend([flag_to_cli(key), str(value)])

    row: dict[str, Any] = {
        "name": candidate.name,
        "family": candidate.family,
        "description": candidate.description,
        "report": str(report),
        "metadata": str(metadata),
        "command": command,
    }
    if args.dry_run:
        row["status"] = "dry_run"
        return row
    if metadata.exists() and not args.force:
        payload = load_json(metadata)
        row["status"] = "cached"
    else:
        completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
        row["status"] = "ok" if completed.returncode == 0 else "failed"
        row["returncode"] = int(completed.returncode)
        row["stdout_tail"] = completed.stdout[-4000:]
        row["stderr_tail"] = completed.stderr[-4000:]
        if completed.returncode != 0:
            return row
        payload = load_json(metadata)

    summary = payload.get("summary", {})
    results = payload.get("results", [])
    row["summary"] = summary
    row["score"] = rank_score(summary, results)
    row["morphology"] = morphology_summary(results)
    return row


def morphology_summary(results: list[dict[str, Any]]) -> dict[str, float]:
    if not results:
        return {
            "hold_true_two_tip_mean": 0.0,
            "hold_wrap_fraction_mean": 1.0,
            "hold_non_tip_ratio_mean": 1.0,
            "hold_floor_contact_mean": 1.0,
            "max_penetration_m_max": 0.0,
        }
    hold = [row.get("hold_morphology", {}) for row in results]
    return {
        "hold_true_two_tip_mean": mean([item.get("true_two_tip_pinch_fraction", 0.0) for item in hold]),
        "hold_wrap_fraction_mean": mean([item.get("wrap_frame_fraction", 1.0) for item in hold]),
        "hold_non_tip_ratio_mean": mean([item.get("non_tip_contact_ratio_mean", 1.0) for item in hold]),
        "hold_floor_contact_mean": mean([item.get("floor_contact_fraction", 1.0) for item in hold]),
        "max_penetration_m_max": max([float(row.get("max_penetration_m", 0.0)) for row in results] + [0.0]),
    }


def mean(values: list[Any]) -> float:
    numbers = [float(value) for value in values]
    return float(sum(numbers) / len(numbers)) if numbers else 0.0


def rank_score(summary: dict[str, Any], results: list[dict[str, Any]]) -> list[float]:
    morphology = morphology_summary(results)
    return [
        float(summary.get("success_count", 0)),
        float(summary.get("true_pinch_success_count", 0)),
        float(summary.get("lift_success_count", 0)),
        float(summary.get("contact_gate_success_count", 0)),
        float(summary.get("release_success_count", 0)),
        float(morphology["hold_true_two_tip_mean"]),
        -float(morphology["hold_wrap_fraction_mean"]),
        -float(morphology["hold_non_tip_ratio_mean"]),
        -float(morphology["hold_floor_contact_mean"]),
        -float(summary.get("motor_feedback_saturation_trial_fraction", 0.0)),
    ]


def sort_key(row: dict[str, Any]) -> tuple[float, ...]:
    score = row.get("score")
    if not isinstance(score, list):
        return (-999.0,)
    return tuple(float(item) for item in score)


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "name",
        "family",
        "status",
        "success",
        "trials",
        "contact",
        "lift",
        "true_pinch",
        "release",
        "terminal_reasons",
        "hold_true_two_tip_mean",
        "hold_wrap_fraction_mean",
        "hold_non_tip_ratio_mean",
        "hold_floor_contact_mean",
        "motor_feedback_max_hand_iq_a",
        "metadata",
        "report",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            s = row.get("summary", {})
            m = row.get("morphology", {})
            writer.writerow(
                {
                    "rank": idx,
                    "name": row.get("name"),
                    "family": row.get("family"),
                    "status": row.get("status"),
                    "success": s.get("success_count", ""),
                    "trials": s.get("trials", ""),
                    "contact": s.get("contact_gate_success_count", ""),
                    "lift": s.get("lift_success_count", ""),
                    "true_pinch": s.get("true_pinch_success_count", ""),
                    "release": s.get("release_success_count", ""),
                    "terminal_reasons": json.dumps(s.get("terminal_reason_counts", {}), ensure_ascii=False),
                    "hold_true_two_tip_mean": f"{m.get('hold_true_two_tip_mean', 0.0):.6f}",
                    "hold_wrap_fraction_mean": f"{m.get('hold_wrap_fraction_mean', 0.0):.6f}",
                    "hold_non_tip_ratio_mean": f"{m.get('hold_non_tip_ratio_mean', 0.0):.6f}",
                    "hold_floor_contact_mean": f"{m.get('hold_floor_contact_mean', 0.0):.6f}",
                    "motor_feedback_max_hand_iq_a": f"{float(s.get('motor_feedback_max_hand_iq_a', 0.0)):.6f}",
                    "metadata": row.get("metadata"),
                    "report": row.get("report"),
                }
            )


def write_report(path: Path, payload: dict[str, Any]) -> None:
    rows = payload["ranked_results"]
    lines = [
        f"# Stage3.12 Autonomous Tuning {payload['args']['batch_id']} Report\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only smoke scoreboard around Stage3.11D-I.\n",
        "- Uses existing Stage3.11D-B event/contact-gated runner.\n",
        "- Simulated motor force feedback is logged as observation telemetry only.\n",
        "- No hardware runtime, real camera, direct force control, demo-gallery promotion, or full-action ACT/DP promotion.\n\n",
        "## Gate\n\n",
        f"- Trials per candidate: `{payload['args']['trials']}`\n",
        f"- Shared seed: `{payload['args']['seed']}`\n",
        "- Ranking priority: full success, true-pinch, lift, contact, release, clean hold morphology, safe force/current proxy.\n\n",
        "## Ranked Results\n\n",
        "| rank | candidate | family | success | contact | lift | true pinch | release | hold true-tip | hold non-tip | hold wrap | decision |\n",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    baseline = next((row for row in rows if row.get("name") == "baseline_di"), None)
    baseline_success = int((baseline or {}).get("summary", {}).get("success_count", -1))
    for idx, row in enumerate(rows, start=1):
        s = row.get("summary", {})
        m = row.get("morphology", {})
        success = int(s.get("success_count", 0) or 0)
        decision = candidate_decision(row, baseline_success)
        lines.append(
            f"| {idx} | `{row.get('name')}` | `{row.get('family')}` | "
            f"{success}/{s.get('trials', 0)} | "
            f"{s.get('contact_gate_success_count', 0)} | "
            f"{s.get('lift_success_count', 0)} | "
            f"{s.get('true_pinch_success_count', 0)} | "
            f"{s.get('release_success_count', 0)} | "
            f"{m.get('hold_true_two_tip_mean', 0.0):.3f} | "
            f"{m.get('hold_non_tip_ratio_mean', 0.0):.3f} | "
            f"{m.get('hold_wrap_fraction_mean', 0.0):.3f} | {decision} |\n"
        )
    lines.extend(
        [
            "\n## Next Action\n\n",
            next_action(rows, baseline_success),
            "\n\n## Artifacts\n\n",
            f"- Summary CSV: `{payload['summary_csv']}`\n",
            f"- Metadata: `{payload['metadata']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def candidate_decision(row: dict[str, Any], baseline_success: int) -> str:
    s = row.get("summary", {})
    m = row.get("morphology", {})
    success = int(s.get("success_count", 0) or 0)
    if row.get("status") not in {"ok", "cached"}:
        return "failed_run"
    if m.get("hold_wrap_fraction_mean", 1.0) > 0.05 or m.get("hold_non_tip_ratio_mean", 1.0) > 0.35:
        return "diagnostic_only_morphology_risk"
    if success > baseline_success:
        return "advance_to_final_validation"
    if success == baseline_success and row.get("name") != "baseline_di":
        return "keep_as_tie_candidate"
    return "reject_or_hold"


def next_action(rows: list[dict[str, Any]], baseline_success: int) -> str:
    trial_counts = [
        int(row.get("summary", {}).get("trials", 0) or 0)
        for row in rows
        if isinstance(row.get("summary"), dict)
    ]
    max_trials = max(trial_counts or [0])
    clear_advances = [
        row
        for row in rows
        if candidate_decision(row, baseline_success) == "advance_to_final_validation"
    ]
    clear_advances = [row for row in clear_advances if row.get("name") != "baseline_di"]
    if not clear_advances:
        return (
            "No candidate clearly beat the D-I anchor in this batch. Keep tie candidates as diagnostics, "
            "but do not automatically scale them; move to closeout, visual/morphology diagnosis, or label/residual data work."
        )
    names = ", ".join(f"`{row['name']}`" for row in clear_advances[:3])
    if max_trials >= 50:
        return (
            f"Advance {names} to multiseed validation only if the morphology risk is acceptable, "
            "then run visual thumb-side/oblique inspection before any demo-quality claim."
        )
    return f"Advance {names} to 50-trial validation against the same D-I anchor, then require visual morphology check."


def main() -> int:
    args = parse_args()
    selected_names = set(args.candidate or [])
    candidates = candidate_grid()
    if selected_names:
        candidates = [candidate for candidate in candidates if candidate.name in selected_names]
    if args.max_candidates and args.max_candidates > 0:
        candidates = candidates[: int(args.max_candidates)]
    if not candidates:
        raise SystemExit("No candidates selected.")

    rows = []
    for candidate in candidates:
        row = run_candidate(candidate, args)
        rows.append(row)
        s = row.get("summary", {})
        print(
            f"{candidate.name}: {row.get('status')} "
            f"success={s.get('success_count', '?')}/{s.get('trials', '?')} "
            f"contact={s.get('contact_gate_success_count', '?')} "
            f"lift={s.get('lift_success_count', '?')} "
            f"reason={s.get('terminal_reason_counts', {})}"
        )

    ranked = sorted(rows, key=sort_key, reverse=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.12",
        "status": "batch_completed" if not args.dry_run else "dry_run",
        "classification": "diagnostic_scoreboard",
        "args": {
            "batch_id": str(args.batch_id),
            "selected": str(args.selected),
            "trials": int(args.trials),
            "seed": int(args.seed),
            "force": bool(args.force),
            "dry_run": bool(args.dry_run),
        },
        "boundary": {
            "mujoco_only": True,
            "hardware_runtime": False,
            "real_camera": False,
            "direct_force_control_promoted": False,
            "full_action_act_dp_promoted": False,
        },
        "ranked_results": ranked,
        "summary_csv": str(args.summary_csv),
        "report": str(args.report),
        "metadata": str(args.metadata),
    }
    write_summary_csv(args.summary_csv, ranked)
    write_json(args.metadata, payload)
    write_report(args.report, payload)
    print(f"Saved summary: {args.summary_csv}")
    print(f"Saved metadata: {args.metadata}")
    print(f"Saved report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
