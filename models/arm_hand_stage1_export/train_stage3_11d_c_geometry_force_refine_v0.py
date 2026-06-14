#!/usr/bin/env python3
"""Stage3.11D-C geometry + force-feedback local refinement.

This is MuJoCo-only diagnostic training/search. It centers the search around
the Stage3.11D-B `gx -0.0008 m` finding, keeps active-pair force feedback as an
observation/gate signal, and selects the best candidate through randomized
robustness smoke/final probes.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robust
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_SELECTED = META / "stage3_11d_b_event_contact_gated_refine_highlift_selected_v0.json"
DEFAULT_REPORT = DOCS / "stage3_11d_c_geometry_force_refine_v0_report.md"
DEFAULT_METADATA = META / "stage3_11d_c_geometry_force_refine_v0.json"
DEFAULT_SELECTED_OUT = META / "stage3_11d_c_geometry_force_refine_selected_v0.json"
DEFAULT_VISUAL_DIR = DOCS / "stage3_11d_c_geometry_force_refine_vis"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def token(value: float, digits: int = 4) -> str:
    return f"{value:+.{digits}f}".replace("+", "p").replace("-", "m").replace(".", "p")


def load_base_case(path: Path) -> event.RefineCase:
    return robust.selected_case_from_json(path)


def case_distance(case: event.RefineCase, center: event.RefineCase) -> float:
    candidate = case.candidate
    center_candidate = center.candidate
    scales = {
        "gx": 0.00035,
        "gz": 0.00045,
        "sep": 0.004,
        "thumb_mcp": 0.025,
        "active_abd": 0.025,
        "active_pip": 0.045,
    }
    values = {
        "gx": case.grasp_offset_x - center.grasp_offset_x,
        "gz": case.grasp_offset_z - center.grasp_offset_z,
        "sep": case.tip_pair_separation_target - center.tip_pair_separation_target,
        "thumb_mcp": candidate.thumb_mcp - center_candidate.thumb_mcp,
        "active_abd": candidate.active_mcp_abd - center_candidate.active_mcp_abd,
        "active_pip": candidate.active_pip - center_candidate.active_pip,
    }
    return float(np.sqrt(sum((values[key] / scales[key]) ** 2 for key in values)))


def case_name(candidate: event.broad.BallPinchCandidate, gx: float, gz: float, sep: float) -> str:
    return (
        f"s311dc_thumb_{candidate.active_finger}"
        f"_gx{token(gx)}"
        f"_gz{token(gz)}"
        f"_sep{sep:.3f}"
        f"_tmcp{token(candidate.thumb_mcp, 3)}"
        f"_aabd{token(candidate.active_mcp_abd, 3)}"
        f"_apip{token(candidate.active_pip, 3)}"
    ).replace(".", "p")


def generate_cases(base: event.RefineCase, args: argparse.Namespace) -> list[event.RefineCase]:
    center_candidate = base.candidate
    center = replace(
        base,
        grasp_offset_x=float(args.center_grasp_offset_x),
        grasp_offset_z=float(args.center_grasp_offset_z),
        tip_pair_separation_target=float(args.center_tip_pair_separation),
    )
    raw: list[event.RefineCase] = []
    for gx in parse_float_list(args.grasp_offset_x_values):
        for gz in parse_float_list(args.grasp_offset_z_values):
            for sep in parse_float_list(args.tip_pair_separation_values):
                for thumb_mcp in parse_float_list(args.thumb_mcp_values):
                    for active_abd in parse_float_list(args.active_abd_values):
                        for active_pip in parse_float_list(args.active_pip_values):
                            candidate = replace(
                                center_candidate,
                                thumb_mcp=float(thumb_mcp),
                                active_mcp_abd=float(active_abd),
                                active_pip=float(active_pip),
                                active_dip=float(active_pip * 0.45),
                            )
                            candidate = replace(
                                candidate,
                                name=case_name(candidate, gx, gz, sep),
                            )
                            raw.append(
                                replace(
                                    base,
                                    name=candidate.name,
                                    candidate=candidate,
                                    grasp_offset_x=float(gx),
                                    grasp_offset_z=float(gz),
                                    tip_pair_separation_target=float(sep),
                                )
                            )
    raw.sort(key=lambda case: (case_distance(case, center), case.name))
    return raw[: max(1, int(args.max_cases))]


def center_case(base: event.RefineCase, args: argparse.Namespace) -> event.RefineCase:
    candidate = replace(
        base.candidate,
        name=case_name(
            base.candidate,
            float(args.center_grasp_offset_x),
            float(args.center_grasp_offset_z),
            float(args.center_tip_pair_separation),
        ),
    )
    return replace(
        base,
        name=candidate.name,
        candidate=candidate,
        grasp_offset_x=float(args.center_grasp_offset_x),
        grasp_offset_z=float(args.center_grasp_offset_z),
        tip_pair_separation_target=float(args.center_tip_pair_separation),
    )


def event_args_from(args: argparse.Namespace) -> argparse.Namespace:
    ev = event.build_parser().parse_args([])
    ev.scene = Path(args.scene)
    ev.min_lift_steps_before_hold = int(args.min_lift_steps_before_hold)
    ev.hold_release_required_samples = int(args.hold_release_required_samples)
    ev.demo_lift_goal = float(args.demo_lift_goal)
    ev.morphology_sample_every = int(args.morphology_sample_every)
    ev.enable_motor_force_feedback = bool(args.enable_motor_force_feedback)
    ev.motor_feedback_seed = int(args.seed)
    ev.enable_force_feedback_lift_gate = bool(args.enable_force_feedback_lift_gate)
    ev.force_feedback_enable_preload = bool(args.force_feedback_enable_preload)
    ev.force_feedback_min_slow_lift_pair_tension_n = float(args.force_feedback_min_slow_lift_pair_tension_n)
    ev.force_feedback_min_hold_pair_tension_n = float(args.force_feedback_min_hold_pair_tension_n)
    return ev


def robustness_args_from(args: argparse.Namespace, *, trials: int, seed: int) -> argparse.Namespace:
    rb = robust.build_parser().parse_args([])
    rb.scene = Path(args.scene)
    rb.trials = int(trials)
    rb.seed = int(seed)
    rb.object_pose_noise_xy_m = float(args.object_pose_noise_xy_m)
    rb.grasp_target_noise_xy_m = float(args.grasp_target_noise_xy_m)
    rb.grasp_target_noise_z_m = float(args.grasp_target_noise_z_m)
    rb.radius_jitter_m = float(args.radius_jitter_m)
    rb.mass_jitter_kg = float(args.mass_jitter_kg)
    rb.friction_scale_jitter = float(args.friction_scale_jitter)
    rb.min_lift_steps_before_hold = int(args.min_lift_steps_before_hold)
    rb.hold_release_required_samples = int(args.hold_release_required_samples)
    rb.demo_lift_goal = float(args.demo_lift_goal)
    rb.morphology_sample_every = int(args.morphology_sample_every)
    rb.enable_motor_force_feedback = bool(args.enable_motor_force_feedback)
    rb.enable_force_feedback_lift_gate = bool(args.enable_force_feedback_lift_gate)
    rb.force_feedback_enable_preload = bool(args.force_feedback_enable_preload)
    rb.force_feedback_min_slow_lift_pair_tension_n = float(args.force_feedback_min_slow_lift_pair_tension_n)
    rb.force_feedback_min_hold_pair_tension_n = float(args.force_feedback_min_hold_pair_tension_n)
    return rb


def run_local_case(model_path: Path, mujoco, case: event.RefineCase, args: argparse.Namespace) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(model_path))
    return event.run_event_candidate(model, mujoco, case, event_args_from(args))


def run_robustness_case(
    model_path: Path,
    mujoco,
    case: event.RefineCase,
    args: argparse.Namespace,
    *,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    rb_args = robustness_args_from(args, trials=trials, seed=seed)
    ev_args = robust.event_args_from(rb_args)
    rng = np.random.default_rng(int(seed))
    rows = []
    for idx in range(max(1, int(trials))):
        trial_case = robust.perturb_case(case, rb_args, rng, idx)
        model = mujoco.MjModel.from_xml_path(str(model_path))
        row = event.run_event_candidate(model, mujoco, trial_case, ev_args)
        row["trial_index"] = idx
        row["randomization"] = {
            "ball_offset_x": trial_case.ball_offset_x,
            "ball_offset_y": trial_case.ball_offset_y,
            "grasp_offset_x": trial_case.grasp_offset_x,
            "grasp_offset_y": trial_case.grasp_offset_y,
            "grasp_offset_z": trial_case.grasp_offset_z,
            "ball_radius": trial_case.ball_radius,
            "ball_mass": trial_case.ball_mass,
            "tip_mu": trial_case.candidate.tip_sliding_mu,
            "ball_mu": trial_case.candidate.ball_sliding_mu,
            "non_tip_mu": trial_case.candidate.non_tip_sliding_mu,
        }
        rows.append(row)
    summary = robust.summarize(rows)
    return {
        "case": case_to_json(case),
        "trials": int(trials),
        "seed": int(seed),
        "summary": summary,
        "results": rows,
    }


def case_to_json(case: event.RefineCase) -> dict[str, Any]:
    return {
        "name": case.name,
        "candidate": case.candidate.__dict__,
        "tip_pair_separation_target": case.tip_pair_separation_target,
        "grasp_offset_x": case.grasp_offset_x,
        "grasp_offset_y": case.grasp_offset_y,
        "grasp_offset_z": case.grasp_offset_z,
        "ball_radius": case.ball_radius,
        "ball_mass": case.ball_mass,
        "ball_offset_x": case.ball_offset_x,
        "ball_offset_y": case.ball_offset_y,
        "ball_offset_z": case.ball_offset_z,
        "hold_steps": case.hold_steps,
        "min_lift_height": case.min_lift_height,
    }


def restore_case(raw: dict[str, Any]) -> event.RefineCase:
    return event.RefineCase(
        name=str(raw["name"]),
        candidate=event.broad.BallPinchCandidate(**raw["candidate"]),
        tip_pair_separation_target=float(raw["tip_pair_separation_target"]),
        grasp_offset_x=float(raw["grasp_offset_x"]),
        grasp_offset_y=float(raw.get("grasp_offset_y", 0.0)),
        grasp_offset_z=float(raw["grasp_offset_z"]),
        ball_radius=float(raw["ball_radius"]),
        ball_mass=float(raw["ball_mass"]),
        ball_offset_x=float(raw.get("ball_offset_x", 0.0)),
        ball_offset_y=float(raw.get("ball_offset_y", 0.0)),
        ball_offset_z=float(raw.get("ball_offset_z", 0.0)),
        hold_steps=int(raw["hold_steps"]),
        min_lift_height=float(raw["min_lift_height"]),
    )


def rank_local(row: dict[str, Any]) -> tuple[float, float, float]:
    return (
        1.0 if row.get("success") else 0.0,
        float(row.get("score", 0.0)),
        float(row.get("hold_lift_m_max", 0.0)),
    )


def rank_robustness(item: dict[str, Any]) -> tuple[int, int, int, float, int]:
    s = item["summary"]
    return (
        int(s["success_count"]),
        int(s["lift_success_count"]),
        int(s["contact_gate_success_count"]),
        float(s.get("success_hold_lift_mean_m", 0.0)),
        -int(s["terminal_reason_counts"].get("contact_gate_failed", 0)),
    )


def summarize_local(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cases": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row.get("success"))),
        "contact_gate_success_count": int(sum(1 for row in rows if row.get("contact_gate_success"))),
        "lift_success_count": int(sum(1 for row in rows if row.get("lift_success"))),
        "true_pinch_success_count": int(sum(1 for row in rows if row.get("true_pinch_success"))),
        "release_success_count": int(sum(1 for row in rows if row.get("release_success"))),
        "terminal_reason_counts": dict(Counter(str(row.get("terminal_reason")) for row in rows)),
    }


def render_selected(model_path: Path, mujoco, case: event.RefineCase, args: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    model = mujoco.MjModel.from_xml_path(str(model_path))
    render_dir = Path(args.visual_dir) / event.safe_case_dir_name(case.name)
    rendered = event.run_event_candidate(model, mujoco, case, event_args_from(args), render_dir=render_dir)
    contact_sheet = event.broad.write_contact_sheet(
        rendered.get("snapshots", {}),
        Path(args.visual_dir) / f"{case.name}_contact_sheet.png",
    )
    return rendered, str(contact_sheet)


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = payload.get("selected", {})
    local = payload["local_summary"]
    lines = [
        "# Stage3.11D-C Geometry + Force-Feedback Refine v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only diagnostic training/search.\n",
        "- Geometry and force-feedback-aware evaluation, not neural-network training yet.\n",
        "- No real hardware, camera, tactile hardware, ultrasound, demo-gallery promotion, or full-action ACT/DP promotion.\n\n",
        "## Local Search Summary\n\n",
        f"- Cases evaluated: `{local['cases']}`\n",
        f"- Local event true-pinch-release success: `{local['success_count']} / {local['cases']}`\n",
        f"- Contact gate: `{local['contact_gate_success_count']} / {local['cases']}`\n",
        f"- Lift gate: `{local['lift_success_count']} / {local['cases']}`\n",
        f"- True-pinch gate: `{local['true_pinch_success_count']} / {local['cases']}`\n",
        f"- Release: `{local['release_success_count']} / {local['cases']}`\n",
        f"- Terminal reasons: `{local['terminal_reason_counts']}`\n\n",
        "## Robustness Probes\n\n",
        "| rank | candidate | smoke success | final success | contact | lift | true pinch | release | reasons |\n",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    final_by_name = {item["case"]["name"]: item for item in payload["final_robustness"]}
    for idx, item in enumerate(payload["smoke_robustness"], start=1):
        case_name = item["case"]["name"]
        smoke = item["summary"]
        final = final_by_name.get(case_name, {}).get("summary", {})
        lines.append(
            f"| {idx} | `{case_name}` | {smoke['success_count']} / {smoke['trials']} | "
            f"{final.get('success_count', '-')} / {final.get('trials', '-')} | "
            f"{final.get('contact_gate_success_count', '-')} | "
            f"{final.get('lift_success_count', '-')} | "
            f"{final.get('true_pinch_success_count', '-')} | "
            f"{final.get('release_success_count', '-')} | "
            f"`{final.get('terminal_reason_counts', smoke['terminal_reason_counts'])}` |\n"
        )
    if selected:
        s = selected.get("final_summary", {})
        lines.extend(
            [
                "\n## Selected Candidate\n\n",
                f"- Name: `{selected['case']['name']}`\n",
                f"- Final robustness: `{s.get('success_count')} / {s.get('trials')}`\n",
                f"- Contact / lift / true-pinch / release: "
                f"`{s.get('contact_gate_success_count')}` / `{s.get('lift_success_count')}` / "
                f"`{s.get('true_pinch_success_count')}` / `{s.get('release_success_count')}`\n",
                f"- Terminal reasons: `{s.get('terminal_reason_counts')}`\n",
                f"- Hold lift mean/min/max: `{s.get('success_hold_lift_mean_m', 0.0):.5f}` / "
                f"`{s.get('success_hold_lift_min_m', 0.0):.5f}` / "
                f"`{s.get('success_hold_lift_max_m', 0.0):.5f} m`\n",
                f"- Mean slow-lift pair tension: `{s.get('motor_feedback_slow_lift_pair_tension_mean_n', 0.0):.4f} N`\n",
                f"- Mean hold pair tension: `{s.get('motor_feedback_hold_pair_tension_mean_n', 0.0):.4f} N`\n",
                f"- Contact sheet: `{selected.get('contact_sheet')}`\n\n",
            ]
        )
    lines.extend(
        [
            "## Interpretation\n\n",
            "- This stage keeps force feedback as an observation/gate/label signal.\n",
            "- Direct preload remains opt-in and is not the default path.\n",
            "- If the selected candidate beats the prior `34 / 50` probe, it becomes the next dense-capture center.\n",
            "- If it does not beat `34 / 50`, keep the previous `gx -0.0008 m` candidate as the search center and widen geometry/material modeling next.\n\n",
            "## Next\n\n",
            "1. Use the selected candidate as Stage3.11D-C dense-capture center if final robustness improves.\n",
            "2. Export dense per-step obs/action/force/morphology labels for LiftQualityHead and residual micro-adjust training.\n",
            "3. Keep Stage3 MuJoCo-only boundaries and do not promote to demo gallery before close-up visual review.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage3.11D-C geometry + force-feedback local refine.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--selected-out", type=Path, default=DEFAULT_SELECTED_OUT)
    parser.add_argument("--visual-dir", type=Path, default=DEFAULT_VISUAL_DIR)
    parser.add_argument("--seed", type=int, default=20260612)
    parser.add_argument("--max-cases", type=int, default=36)
    parser.add_argument("--smoke-candidates", type=int, default=10)
    parser.add_argument("--smoke-trials", type=int, default=12)
    parser.add_argument("--final-candidates", type=int, default=2)
    parser.add_argument("--final-trials", type=int, default=50)
    parser.add_argument("--include-center-final-control", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--center-grasp-offset-x", type=float, default=-0.0008)
    parser.add_argument("--center-grasp-offset-z", type=float, default=0.0020)
    parser.add_argument("--center-tip-pair-separation", type=float, default=0.060)
    parser.add_argument("--grasp-offset-x-values", default="-0.0006,-0.0008,-0.0010")
    parser.add_argument("--grasp-offset-z-values", default="0.0015,0.0020,0.0025")
    parser.add_argument("--tip-pair-separation-values", default="0.056,0.060,0.064")
    parser.add_argument("--thumb-mcp-values", default="0.26,0.28,0.30")
    parser.add_argument("--active-abd-values", default="-0.47,-0.50,-0.53")
    parser.add_argument("--active-pip-values", default="-0.70")
    parser.add_argument("--object-pose-noise-xy-m", type=float, default=0.003)
    parser.add_argument("--grasp-target-noise-xy-m", type=float, default=0.002)
    parser.add_argument("--grasp-target-noise-z-m", type=float, default=0.001)
    parser.add_argument("--radius-jitter-m", type=float, default=0.001)
    parser.add_argument("--mass-jitter-kg", type=float, default=0.002)
    parser.add_argument("--friction-scale-jitter", type=float, default=0.08)
    parser.add_argument("--min-lift-steps-before-hold", type=int, default=300)
    parser.add_argument("--hold-release-required-samples", type=int, default=8)
    parser.add_argument("--demo-lift-goal", type=float, default=0.11)
    parser.add_argument("--morphology-sample-every", type=int, default=5)
    parser.add_argument("--enable-motor-force-feedback", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-force-feedback-lift-gate", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-enable-preload", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-min-slow-lift-pair-tension-n", type=float, default=3.0)
    parser.add_argument("--force-feedback-min-hold-pair-tension-n", type=float, default=1.5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    base = load_base_case(Path(args.selected))
    cases = generate_cases(base, args)

    local_rows: list[dict[str, Any]] = []
    print(f"Stage3.11D-C local cases: {len(cases)}")
    for idx, case in enumerate(cases, start=1):
        row = run_local_case(scene, mujoco, case, args)
        row["local_case_index"] = idx - 1
        local_rows.append(row)
        hm = row.get("hold_morphology", {})
        print(
            f"local {idx:03d}/{len(cases):03d} {row['status']} score={row['score']:.3f} "
            f"lift={row.get('hold_lift_m_max', 0.0):.4f} "
            f"two_tip={hm.get('true_two_tip_pinch_fraction', 0.0):.3f} "
            f"reason={row['terminal_reason']} {case.name}"
        )

    local_rows.sort(key=rank_local, reverse=True)
    smoke_cases = [restore_case(row["case"]) for row in local_rows[: max(1, int(args.smoke_candidates))]]

    smoke_robustness = []
    for idx, case in enumerate(smoke_cases, start=1):
        seed = int(args.seed) + 1000 + idx
        item = run_robustness_case(scene, mujoco, case, args, trials=int(args.smoke_trials), seed=seed)
        smoke_robustness.append(item)
        s = item["summary"]
        print(
            f"smoke {idx:02d}/{len(smoke_cases):02d} {s['success_count']}/{s['trials']} "
            f"contact={s['contact_gate_success_count']} lift={s['lift_success_count']} {case.name}"
        )
    smoke_robustness.sort(key=rank_robustness, reverse=True)

    final_robustness = []
    final_plan = list(smoke_robustness[: max(1, int(args.final_candidates))])
    if bool(args.include_center_final_control):
        center = center_case(base, args)
        if not any(item["case"]["name"] == center.name for item in final_plan):
            final_plan.append({"case": case_to_json(center), "summary": {"source": "center_control"}})
    final_seed = int(args.seed) + 5000
    for idx, item in enumerate(final_plan, start=1):
        case = restore_case(item["case"])
        final = run_robustness_case(scene, mujoco, case, args, trials=int(args.final_trials), seed=final_seed)
        final_robustness.append(final)
        s = final["summary"]
        print(
            f"final {idx:02d}/{len(final_plan):02d} {s['success_count']}/{s['trials']} "
            f"contact={s['contact_gate_success_count']} lift={s['lift_success_count']} "
            f"true={s['true_pinch_success_count']} release={s['release_success_count']} {case.name}"
        )
    final_robustness.sort(key=rank_robustness, reverse=True)

    selected = {}
    if final_robustness:
        best_final = final_robustness[0]
        best_case = restore_case(best_final["case"])
        rendered, contact_sheet = render_selected(scene, mujoco, best_case, args)
        selected = {
            "case": best_final["case"],
            "final_summary": best_final["summary"],
            "contact_sheet": contact_sheet,
            "rendered_result": rendered,
        }

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-C",
        "scene": str(scene),
        "args": vars(args),
        "base_case": case_to_json(base),
        "local_summary": summarize_local(local_rows),
        "local_results": local_rows,
        "smoke_robustness": smoke_robustness,
        "final_robustness": final_robustness,
        "selected": selected,
        "boundary": {
            "mujoco_only": True,
            "geometry_force_feedback_search": True,
            "neural_network_training": False,
            "hardware_runtime": False,
            "demo_gallery_promoted": False,
            "full_action_act_dp_promoted": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    if selected:
        args.selected_out.parent.mkdir(parents=True, exist_ok=True)
        args.selected_out.write_text(
            json.dumps(
                json_ready(
                    {
                        "selected_case": selected["case"],
                        "selected_final_summary": selected["final_summary"],
                        "source_metadata": str(args.metadata),
                        "contact_sheet": selected.get("contact_sheet"),
                    }
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    print(json.dumps(json_ready(payload["local_summary"]), indent=2, ensure_ascii=False))
    if selected:
        print(json.dumps(json_ready(selected["final_summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    print(f"Saved selected: {args.selected_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
