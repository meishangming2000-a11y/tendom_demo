#!/usr/bin/env python3
"""Search bounded residual micro-adjust settings for Stage3.11D true pinch.

This MuJoCo-only runner keeps the event/contact-gated controller structure and
turns on a small, bounded residual during low-quality slow-lift windows. It is a
teacher/probe for residual data generation, not a full-action policy promotion.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"

DEFAULT_SELECTED = META / "stage3_11d_c_geometry_force_refine_selected_v0.json"
DEFAULT_REPORT = DOCS / "stage3_11d_f_bounded_residual_micro_adjust_v0_report.md"
DEFAULT_METADATA = META / "stage3_11d_f_bounded_residual_micro_adjust_v0.json"

STATUS = "stage3_11d_f_bounded_residual_micro_adjust_v0_mujoco_only_probe"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class ResidualVariant:
    name: str
    enable: bool
    check_after: int = 80
    required_samples: int = 1
    max_wait: int = 160
    close_delta: float = 0.006
    max_close_delta: float = 0.030
    grasp_x_delta: float = 0.0
    max_grasp_x_delta: float = 0.0
    enable_prelift: bool = False
    prelift_steps: int = 40
    prelift_grasp_x_delta: float = 0.0
    prelift_max_grasp_x_delta: float = 0.0
    progress_drop_steps: int = 0
    allow_wrap: bool = False


def variant_grid(args: argparse.Namespace) -> list[ResidualVariant]:
    variants = [
        ResidualVariant("baseline_off", enable=False, max_wait=0, close_delta=0.0, max_close_delta=0.0),
        ResidualVariant("wait_q80_w120", enable=True, check_after=80, max_wait=120, close_delta=0.0, max_close_delta=0.0),
        ResidualVariant("close_s004_m020_q80_w120", enable=True, check_after=80, max_wait=120, close_delta=0.004, max_close_delta=0.020),
        ResidualVariant("close_s006_m030_q80_w160", enable=True, check_after=80, max_wait=160, close_delta=0.006, max_close_delta=0.030),
        ResidualVariant("close_s008_m032_q100_w160", enable=True, check_after=100, max_wait=160, close_delta=0.008, max_close_delta=0.032),
        ResidualVariant(
            "xneg_s0004_m0012_q80_w160",
            enable=True,
            check_after=80,
            max_wait=160,
            close_delta=0.0,
            max_close_delta=0.0,
            grasp_x_delta=-0.0004,
            max_grasp_x_delta=0.0012,
        ),
        ResidualVariant(
            "xneg_s0006_m0018_q80_w180",
            enable=True,
            check_after=80,
            max_wait=180,
            close_delta=0.0,
            max_close_delta=0.0,
            grasp_x_delta=-0.0006,
            max_grasp_x_delta=0.0018,
        ),
        ResidualVariant(
            "xneg_close_s0004_c004_m0012_q80_w160",
            enable=True,
            check_after=80,
            max_wait=160,
            close_delta=0.004,
            max_close_delta=0.020,
            grasp_x_delta=-0.0004,
            max_grasp_x_delta=0.0012,
        ),
        ResidualVariant(
            "prelift_xneg_s0004_m0008_steps40",
            enable=True,
            close_delta=0.0,
            max_close_delta=0.0,
            enable_prelift=True,
            prelift_steps=40,
            prelift_grasp_x_delta=-0.0004,
            prelift_max_grasp_x_delta=0.0008,
        ),
        ResidualVariant(
            "prelift_xneg_s0006_m0012_steps60",
            enable=True,
            close_delta=0.0,
            max_close_delta=0.0,
            enable_prelift=True,
            prelift_steps=60,
            prelift_grasp_x_delta=-0.0006,
            prelift_max_grasp_x_delta=0.0012,
        ),
        ResidualVariant(
            "prelift_xneg_close_s0004_c004_m0012_steps60",
            enable=True,
            close_delta=0.004,
            max_close_delta=0.020,
            enable_prelift=True,
            prelift_steps=60,
            prelift_grasp_x_delta=-0.0004,
            prelift_max_grasp_x_delta=0.0012,
        ),
        ResidualVariant(
            "prelift_xpos_s0004_m0008_steps40",
            enable=True,
            close_delta=0.0,
            max_close_delta=0.0,
            enable_prelift=True,
            prelift_steps=40,
            prelift_grasp_x_delta=0.0004,
            prelift_max_grasp_x_delta=0.0008,
        ),
        ResidualVariant(
            "prelift_xpos_s0006_m0012_steps60",
            enable=True,
            close_delta=0.0,
            max_close_delta=0.0,
            enable_prelift=True,
            prelift_steps=60,
            prelift_grasp_x_delta=0.0006,
            prelift_max_grasp_x_delta=0.0012,
        ),
        ResidualVariant(
            "close_s006_m030_q80_w180_drop5",
            enable=True,
            check_after=80,
            max_wait=180,
            close_delta=0.006,
            max_close_delta=0.030,
            progress_drop_steps=5,
        ),
    ]
    if args.variant:
        requested = {str(item).strip() for item in args.variant.split(",") if str(item).strip()}
        variants = [variant for variant in variants if variant.name in requested]
        if not variants:
            raise ValueError(f"No requested variants matched: {sorted(requested)}")
    return variants


def apply_variant(ev_args: argparse.Namespace, variant: ResidualVariant) -> argparse.Namespace:
    ev_args.enable_residual_micro_adjust = bool(variant.enable)
    ev_args.residual_micro_adjust_check_after_lift_steps = int(variant.check_after)
    ev_args.residual_micro_adjust_required_samples = int(variant.required_samples)
    ev_args.residual_micro_adjust_max_wait_steps = int(variant.max_wait)
    ev_args.residual_micro_adjust_close_delta = float(variant.close_delta)
    ev_args.residual_micro_adjust_max_close_delta = float(variant.max_close_delta)
    ev_args.residual_micro_adjust_grasp_x_delta = float(variant.grasp_x_delta)
    ev_args.residual_micro_adjust_max_grasp_x_delta = float(variant.max_grasp_x_delta)
    ev_args.residual_micro_adjust_enable_prelift = bool(variant.enable_prelift)
    ev_args.residual_micro_adjust_prelift_steps = int(variant.prelift_steps)
    ev_args.residual_micro_adjust_prelift_grasp_x_delta = float(variant.prelift_grasp_x_delta)
    ev_args.residual_micro_adjust_prelift_max_grasp_x_delta = float(variant.prelift_max_grasp_x_delta)
    ev_args.residual_micro_adjust_progress_drop_steps = int(variant.progress_drop_steps)
    ev_args.residual_micro_adjust_allow_wrap = bool(variant.allow_wrap)
    return ev_args


def run_variant(
    *,
    scene: Path,
    mujoco: Any,
    base: event.RefineCase,
    args: argparse.Namespace,
    variant: ResidualVariant,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    rb_args = argparse.Namespace(**vars(args))
    rb_args.seed = int(seed)
    ev_args = robustness.event_args_from(rb_args)
    apply_variant(ev_args, variant)
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, Any]] = []
    for idx in range(max(1, int(trials))):
        case = robustness.perturb_case(base, rb_args, rng, idx)
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        row["trial_index"] = int(idx)
        row["variant"] = variant.name
        row["randomization"] = {
            "ball_offset_x": case.ball_offset_x,
            "ball_offset_y": case.ball_offset_y,
            "grasp_offset_x": case.grasp_offset_x,
            "grasp_offset_y": case.grasp_offset_y,
            "grasp_offset_z": case.grasp_offset_z,
            "ball_radius": case.ball_radius,
            "ball_mass": case.ball_mass,
            "tip_mu": case.candidate.tip_sliding_mu,
            "ball_mu": case.candidate.ball_sliding_mu,
            "non_tip_mu": case.candidate.non_tip_sliding_mu,
        }
        rows.append(row)
    summary = robustness.summarize(rows)
    residual_rows = [row.get("residual_micro_adjust", {}) for row in rows]
    summary.update(
        {
            "variant": variant.name,
            "residual_enabled": bool(variant.enable),
            "residual_quality_bad_samples_total": int(
                sum(int(item.get("quality_bad_samples", 0)) for item in residual_rows)
            ),
            "residual_events_total": int(sum(int(item.get("events", 0)) for item in residual_rows)),
            "residual_close_events_total": int(sum(int(item.get("close_events", 0)) for item in residual_rows)),
            "residual_wait_steps_total": int(sum(int(item.get("wait_steps", 0)) for item in residual_rows)),
            "residual_prelift_events_total": int(sum(int(item.get("prelift_events", 0)) for item in residual_rows)),
            "residual_ik_solves_total": int(sum(int(item.get("ik_solves", 0)) for item in residual_rows)),
            "residual_abs_grasp_x_delta_mean": float(
                np.mean([abs(float(item.get("grasp_x_delta_total", 0.0))) for item in residual_rows])
            )
            if residual_rows
            else 0.0,
            "residual_trial_fraction": float(
                np.mean([int(item.get("events", 0)) > 0 for item in residual_rows])
            )
            if residual_rows
            else 0.0,
        }
    )
    return {
        "variant": variant.__dict__,
        "seed": int(seed),
        "trials": int(trials),
        "summary": summary,
        "terminal_reason_counts": dict(Counter(str(row.get("terminal_reason", "unknown")) for row in rows)),
        "results": [{key: value for key, value in row.items() if key != "dense_sensor_trace"} for row in rows],
    }


def rank_item(item: dict[str, Any]) -> tuple[int, int, int, int, float, float]:
    s = item["summary"]
    return (
        int(s.get("success_count", 0)),
        int(s.get("true_pinch_success_count", 0)),
        int(s.get("lift_success_count", 0)),
        int(s.get("contact_gate_success_count", 0)),
        float(s.get("success_hold_lift_mean_m", 0.0)),
        -float(s.get("residual_events_total", 0.0)),
    )


def write_report(path: Path, payload: dict[str, Any]) -> None:
    selected = payload.get("selected", {})
    lines = [
        "# Stage3.11D-F Bounded Residual Micro-Adjust v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only bounded residual teacher/probe.\n",
        "- Keeps the event/contact-gated controller; residual is small, slow-lift-only, and bounded.\n",
        "- Uses simulated contact/tactile morphology and simulated motor force feedback from MuJoCo loads.\n",
        "- Not demo-gallery promotion, full-action ACT/DP, hardware runtime, real camera, or real tactile integration.\n\n",
        "## Inputs\n\n",
        f"- Selected center: `{payload['selected_path']}`\n",
        f"- Smoke seed/trials: `{payload['args']['seed']}` / `{payload['args']['smoke_trials']}`\n",
        f"- Final seed/trials: `{payload['args']['final_seed']}` / `{payload['args']['final_trials']}`\n\n",
        "## Smoke Ranking\n\n",
        "| rank | variant | success | contact | lift | true pinch | release | residual events | reasons |\n",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for idx, item in enumerate(payload["smoke_results"], start=1):
        s = item["summary"]
        lines.append(
            f"| {idx} | `{item['variant']['name']}` | {s['success_count']} / {s['trials']} | "
            f"{s['contact_gate_success_count']} | {s['lift_success_count']} | "
            f"{s['true_pinch_success_count']} | {s['release_success_count']} | "
            f"{s['residual_events_total']} | `{s['terminal_reason_counts']}` |\n"
        )
    lines.extend(
        [
            "\n## Final Ranking\n\n",
            "| rank | variant | success | contact | lift | true pinch | release | residual events | reasons |\n",
            "|---:|---|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for idx, item in enumerate(payload["final_results"], start=1):
        s = item["summary"]
        lines.append(
            f"| {idx} | `{item['variant']['name']}` | {s['success_count']} / {s['trials']} | "
            f"{s['contact_gate_success_count']} | {s['lift_success_count']} | "
            f"{s['true_pinch_success_count']} | {s['release_success_count']} | "
            f"{s['residual_events_total']} | `{s['terminal_reason_counts']}` |\n"
        )
    if selected:
        s = selected["summary"]
        lines.extend(
            [
                "\n## Selected Diagnostic Candidate\n\n",
                f"- Variant: `{selected['variant']['name']}`\n",
                f"- Final success: `{s['success_count']} / {s['trials']}`\n",
                f"- Contact/lift/true-pinch/release: `{s['contact_gate_success_count']}` / "
                f"`{s['lift_success_count']}` / `{s['true_pinch_success_count']}` / "
                f"`{s['release_success_count']}`\n",
                f"- Residual events total: `{s['residual_events_total']}`\n",
                f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
            ]
        )
    lines.extend(
        [
            "\n## Next\n\n",
            "- If a residual variant beats the no-residual baseline on the same final seed, rerun it on the D-D capture seed and create residual teacher rows.\n",
            "- If no residual variant improves robustness, keep D-E shadow as diagnostic and return to geometry/material/phase-timing repair.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parent = robustness.build_parser()
    parser = argparse.ArgumentParser(
        description="Stage3.11D-F bounded residual micro-adjust probe.",
        parents=[parent],
        add_help=False,
        conflict_handler="resolve",
    )
    parser.set_defaults(
        selected=DEFAULT_SELECTED,
        report=DEFAULT_REPORT,
        metadata=DEFAULT_METADATA,
        seed=20260612,
    )
    parser.add_argument("--smoke-trials", type=int, default=12)
    parser.add_argument("--final-trials", type=int, default=50)
    parser.add_argument("--final-seed", type=int, default=20265612)
    parser.add_argument("--final-candidates", type=int, default=2)
    parser.add_argument("--include-baseline-final", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--variant", default=None, help="Optional comma-separated variant names to run.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    selected_path = Path(args.selected).resolve()
    base = robustness.apply_base_offsets(robustness.selected_case_from_json(selected_path), args)
    variants = variant_grid(args)

    smoke_results = []
    for idx, variant in enumerate(variants, start=1):
        item = run_variant(
            scene=scene,
            mujoco=mujoco,
            base=base,
            args=args,
            variant=variant,
            trials=int(args.smoke_trials),
            seed=int(args.seed),
        )
        smoke_results.append(item)
        s = item["summary"]
        print(
            f"smoke {idx:02d}/{len(variants):02d} {variant.name} "
            f"{s['success_count']}/{s['trials']} lift={s['lift_success_count']} "
            f"residual_events={s['residual_events_total']} reasons={s['terminal_reason_counts']}"
        )
    smoke_results.sort(key=rank_item, reverse=True)

    final_plan = smoke_results[: max(1, int(args.final_candidates))]
    if bool(args.include_baseline_final) and not any(item["variant"]["name"] == "baseline_off" for item in final_plan):
        baseline = next((item for item in smoke_results if item["variant"]["name"] == "baseline_off"), None)
        if baseline is not None:
            final_plan.append(baseline)

    final_results = []
    for idx, item in enumerate(final_plan, start=1):
        variant = ResidualVariant(**item["variant"])
        final = run_variant(
            scene=scene,
            mujoco=mujoco,
            base=base,
            args=args,
            variant=variant,
            trials=int(args.final_trials),
            seed=int(args.final_seed),
        )
        final_results.append(final)
        s = final["summary"]
        print(
            f"final {idx:02d}/{len(final_plan):02d} {variant.name} "
            f"{s['success_count']}/{s['trials']} lift={s['lift_success_count']} "
            f"residual_events={s['residual_events_total']} reasons={s['terminal_reason_counts']}"
        )
    final_results.sort(key=rank_item, reverse=True)
    selected = final_results[0] if final_results else {}
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-F",
        "status": STATUS,
        "scene": str(scene),
        "selected_path": str(selected_path),
        "report": str(Path(args.report).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "args": vars(args),
        "base_case": {
            "name": base.name,
            "candidate": base.candidate.__dict__,
            "tip_pair_separation_target": base.tip_pair_separation_target,
            "grasp_offset_x": base.grasp_offset_x,
            "grasp_offset_y": base.grasp_offset_y,
            "grasp_offset_z": base.grasp_offset_z,
            "ball_radius": base.ball_radius,
            "ball_mass": base.ball_mass,
            "hold_steps": base.hold_steps,
            "min_lift_height": base.min_lift_height,
            "ball_offset_x": base.ball_offset_x,
            "ball_offset_y": base.ball_offset_y,
            "ball_offset_z": base.ball_offset_z,
        },
        "smoke_results": smoke_results,
        "final_results": final_results,
        "selected": selected,
        "boundary": {
            "mujoco_only": True,
            "bounded_residual_probe_only": True,
            "full_action_policy": False,
            "hardware_runtime": False,
            "demo_gallery_promotion": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    if selected:
        print(json.dumps(json_ready(selected["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
