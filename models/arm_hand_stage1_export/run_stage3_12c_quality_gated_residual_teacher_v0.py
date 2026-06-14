#!/usr/bin/env python3
"""Stage3.12C quality-gated bounded residual teacher search.

This runner turns the Stage3.12B morphology-quality head into a guarded
intervention trigger for tiny residual teacher probes. It keeps the existing
event/contact-gated small-ball controller, compares every candidate against the
frozen D-I anchor, and does not promote full-action control.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
import export_stage3_11d_d_dense_sensor_fusion_dataset_v0 as dense
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import run_stage3_12_autonomous_tuning_batch_v0 as autotune
import run_stage3_12b_morphology_quality_shadow_v0 as shadow_eval
import train_stage3_11d_b_event_contact_gated_refine_v0 as event
from train_stage3_12b_morphology_quality_head_v0 import GRASP_EVIDENCE_PHASES


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DATA = ROOT / "data"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_SELECTED = META / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_12b_morphology_quality_head_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_12c_quality_gated_residual_teacher_v0_report.md"
DEFAULT_METADATA = META / "stage3_12c_quality_gated_residual_teacher_v0.json"
DEFAULT_SUMMARY_CSV = DATA / "stage3_12c_quality_gated_residual_teacher_v0_summary.csv"

STATUS = "stage3_12c_quality_gated_residual_teacher_v0_mujoco_only_probe"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class ResidualVariant:
    name: str
    family: str
    candidate_name: str
    description: str
    residual_enabled: bool = False
    use_quality_head: bool = False
    check_after: int = 100
    required_samples: int = 2
    max_wait: int = 0
    close_delta: float = 0.0
    max_close_delta: float = 0.0
    grasp_x_delta: float = 0.0
    max_grasp_x_delta: float = 0.0
    enable_prelift: bool = False
    prelift_steps: int = 0
    prelift_grasp_x_delta: float = 0.0
    prelift_max_grasp_x_delta: float = 0.0
    progress_drop_steps: int = 0
    force_gate: bool = False
    force_preload: bool = False
    force_max_wait: int = 0
    force_lift_wait_close_delta: float = 0.0
    force_max_preload_delta: float = 0.035
    contact_gate_max_steps: int | None = None
    post_contact_settle_steps: int | None = None
    grasp_x_min: float | None = None
    grasp_x_max: float | None = None


def candidate_map() -> dict[str, autotune.Candidate]:
    return {candidate.name: candidate for candidate in autotune.candidate_grid()}


def variant_grid(args: argparse.Namespace) -> list[ResidualVariant]:
    variants = [
        ResidualVariant(
            name="baseline_di_off",
            family="anchor",
            candidate_name="baseline_di",
            description="Frozen D-I anchor, no residual.",
        ),
        ResidualVariant(
            name="lift_ls460_off",
            family="diagnostic_static",
            candidate_name="lift_ls460",
            description="Stage3.12A lift timing diagnostic, no residual.",
        ),
        ResidualVariant(
            name="ls460_gz0021_off",
            family="diagnostic_static",
            candidate_name="ls460_gz0021",
            description="Stage3.12 batch3 best smoke candidate, no residual.",
        ),
        ResidualVariant(
            name="ls460_gz0021_qhead_close_s002_m010",
            family="static_plus_quality_close",
            candidate_name="ls460_gz0021",
            description="Batch3 best smoke candidate plus quality-head tiny close residual.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=95,
            required_samples=2,
            max_wait=100,
            close_delta=0.002,
            max_close_delta=0.010,
        ),
        ResidualVariant(
            name="di_directional_gx_clamp_m0025_p0000",
            family="vision_directional_teacher",
            candidate_name="baseline_di",
            description="Clamp noisy vision/grasp x into a safer D-I corridor before IK.",
            grasp_x_min=-0.0025,
            grasp_x_max=0.0,
        ),
        ResidualVariant(
            name="di_directional_gx_clamp_m0023_m0002",
            family="vision_directional_teacher",
            candidate_name="baseline_di",
            description="Tighter x corridor learned from contact/lift failure windows.",
            grasp_x_min=-0.0023,
            grasp_x_max=-0.0002,
        ),
        ResidualVariant(
            name="di_directional_gx_clamp_qhead_close",
            family="vision_directional_plus_quality_close",
            candidate_name="baseline_di",
            description="Directional x clamp plus quality-head tiny close residual.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=95,
            required_samples=2,
            max_wait=100,
            close_delta=0.002,
            max_close_delta=0.010,
            grasp_x_min=-0.0025,
            grasp_x_max=0.0,
        ),
        ResidualVariant(
            name="di_contact_gate260",
            family="contact_reacquire",
            candidate_name="baseline_di",
            description="Bounded contact gate extension for late true-tip contact.",
            contact_gate_max_steps=260,
        ),
        ResidualVariant(
            name="di_contact_gate300_settle60",
            family="contact_reacquire",
            candidate_name="baseline_di",
            description="Larger bounded contact gate plus slightly longer post-contact settle.",
            contact_gate_max_steps=300,
            post_contact_settle_steps=60,
        ),
        ResidualVariant(
            name="di_contact260_qhead_close_s002_m010",
            family="contact_plus_quality_close",
            candidate_name="baseline_di",
            description="Contact gate extension plus quality-head tiny close residual.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=95,
            required_samples=2,
            max_wait=100,
            close_delta=0.002,
            max_close_delta=0.010,
            contact_gate_max_steps=260,
        ),
        ResidualVariant(
            name="di_qhead_wait_w120",
            family="quality_wait",
            candidate_name="baseline_di",
            description="Quality-head low-quality trigger holds lift progress only.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=100,
            required_samples=2,
            max_wait=120,
        ),
        ResidualVariant(
            name="di_qhead_close_s002_m010_w100",
            family="quality_close",
            candidate_name="baseline_di",
            description="Quality-head trigger adds very small pair close preload.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=95,
            required_samples=2,
            max_wait=100,
            close_delta=0.002,
            max_close_delta=0.010,
        ),
        ResidualVariant(
            name="di_qhead_close_s003_m012_w120",
            family="quality_close",
            candidate_name="baseline_di",
            description="Quality-head trigger adds small pair close preload.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=90,
            required_samples=2,
            max_wait=120,
            close_delta=0.003,
            max_close_delta=0.012,
        ),
        ResidualVariant(
            name="di_qhead_prelift_xneg_s0003_m0006",
            family="quality_retarget",
            candidate_name="baseline_di",
            description="Quality-head pre-lift bad window retargets grasp x slightly negative.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=100,
            required_samples=2,
            max_wait=0,
            enable_prelift=True,
            prelift_steps=35,
            prelift_grasp_x_delta=-0.0003,
            prelift_max_grasp_x_delta=0.0006,
        ),
        ResidualVariant(
            name="di_qhead_pid_close_s002_w100",
            family="quality_pid_like",
            candidate_name="baseline_di",
            description="Quality-head trigger plus force-feedback wait/preload ramp.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=95,
            required_samples=2,
            max_wait=100,
            close_delta=0.002,
            max_close_delta=0.010,
            force_gate=True,
            force_preload=True,
            force_max_wait=80,
            force_lift_wait_close_delta=0.004,
            force_max_preload_delta=0.035,
        ),
        ResidualVariant(
            name="ls460_qhead_close_s002_m010_w100",
            family="lift_plus_quality_close",
            candidate_name="lift_ls460",
            description="Stage3.12A lift timing plus quality-head tiny close residual.",
            residual_enabled=True,
            use_quality_head=True,
            check_after=95,
            required_samples=2,
            max_wait=100,
            close_delta=0.002,
            max_close_delta=0.010,
        ),
    ]
    if args.variant:
        requested = {item.strip() for item in args.variant.split(",") if item.strip()}
        variants = [variant for variant in variants if variant.name in requested]
        if not variants:
            raise ValueError(f"No requested variants matched: {sorted(requested)}")
    return variants


class QualityPredictor:
    def __init__(self, checkpoint: Path) -> None:
        self.shadow = shadow_eval.load_shadow(checkpoint)
        self.target_names = [str(name) for name in self.shadow["target_names"]]

    def _predict_one(self, frame: dict[str, Any], phase: str, case: event.RefineCase) -> dict[str, float]:
        row_context = {"initial_ball": frame.get("initial_ball", [0.0, 0.0, 0.0])}
        obs = shadow_eval.frame_feature(frame, row_context, case, phase, self.shadow["phase_names"])
        if obs.shape[0] != int(self.shadow["input_dim"]):
            raise ValueError(f"Quality feature dim mismatch: {obs.shape[0]} vs {self.shadow['input_dim']}")
        x = ((obs.reshape(1, -1) - self.shadow["obs_mean"].reshape(1, -1)) / self.shadow["obs_std"].reshape(1, -1)).astype(
            np.float32
        )
        with torch.no_grad():
            probs = shadow_eval.sigmoid_np(self.shadow["model"](torch.from_numpy(x)).cpu().numpy())[0]
        return {name: float(probs[idx]) for idx, name in enumerate(self.target_names)}

    def __call__(
        self,
        *,
        frame: dict[str, Any],
        phase: str,
        case: event.RefineCase,
        run_args: argparse.Namespace,
    ) -> dict[str, float]:
        return self._predict_one(frame, phase, case)

    def score_trace(
        self,
        trace: list[dict[str, Any]],
        row: dict[str, Any],
        case: event.RefineCase,
        args: argparse.Namespace,
        *,
        candidate_name: str,
        trial_index: int,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        features: list[np.ndarray] = []
        frames: list[dict[str, Any]] = []
        for frame in trace:
            phase = str(frame.get("label", "unknown"))
            if phase not in GRASP_EVIDENCE_PHASES:
                continue
            row_context = {"initial_ball": row.get("initial_ball", frame.get("initial_ball", [0.0, 0.0, 0.0]))}
            obs = shadow_eval.frame_feature(frame, row_context, case, phase, self.shadow["phase_names"])
            if obs.shape[0] != int(self.shadow["input_dim"]):
                raise ValueError(f"Quality feature dim mismatch: {obs.shape[0]} vs {self.shadow['input_dim']}")
            features.append(obs)
            frames.append(frame)
        if not features:
            return records
        x = np.asarray(features, dtype=np.float32)
        x_norm = ((x - self.shadow["obs_mean"].reshape(1, -1)) / self.shadow["obs_std"].reshape(1, -1)).astype(np.float32)
        with torch.no_grad():
            probs = shadow_eval.sigmoid_np(self.shadow["model"](torch.from_numpy(x_norm)).cpu().numpy())
        for idx, frame in enumerate(frames):
            phase = str(frame.get("label", "unknown"))
            truth = shadow_eval.frame_targets(frame, row, phase, args, case)
            prob = {name: float(probs[idx, name_idx]) for name_idx, name in enumerate(self.target_names)}
            truth_map = {name: bool(truth[name_idx] >= 0.5) for name_idx, name in enumerate(self.target_names)}
            records.append(
                {
                    "candidate_name": candidate_name,
                    "trial_index": int(trial_index),
                    "phase": phase,
                    "phase_step": int(frame.get("phase_step", -1)),
                    "phase_progress": float(frame.get("phase_progress", 0.0)),
                    "lift_m": float(frame.get("lift_m", 0.0)),
                    "terminal_reason": str(row.get("terminal_reason", "unknown")),
                    "prob": prob,
                    "truth": truth_map,
                    "morphology": frame.get("morphology", {}),
                }
            )
        return records


def build_run_args(args: argparse.Namespace, variant: ResidualVariant, *, seed: int) -> argparse.Namespace:
    candidates = candidate_map()
    if variant.candidate_name not in candidates:
        raise ValueError(f"Unknown Stage3.12 candidate: {variant.candidate_name}")
    rb_args = robustness.build_parser().parse_args([])
    rb_args.scene = Path(args.scene)
    rb_args.selected = Path(args.selected)
    rb_args.seed = int(seed)
    rb_args.trials = int(args.smoke_trials)
    rb_args.object_pose_noise_xy_m = float(args.object_pose_noise_xy_m)
    rb_args.grasp_target_noise_xy_m = float(args.grasp_target_noise_xy_m)
    rb_args.grasp_target_noise_z_m = float(args.grasp_target_noise_z_m)
    rb_args.radius_jitter_m = float(args.radius_jitter_m)
    rb_args.mass_jitter_kg = float(args.mass_jitter_kg)
    rb_args.friction_scale_jitter = float(args.friction_scale_jitter)
    rb_args.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))
    for key, value in candidates[variant.candidate_name].overrides.items():
        setattr(rb_args, key, value)
    return dense.fill_from_robustness_defaults(rb_args)


def apply_variant(ev_args: argparse.Namespace, variant: ResidualVariant, predictor: QualityPredictor, args: argparse.Namespace) -> None:
    ev_args.enable_residual_micro_adjust = bool(variant.residual_enabled)
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
    ev_args.enable_force_feedback_lift_gate = bool(variant.force_gate)
    ev_args.force_feedback_enable_preload = bool(variant.force_preload)
    ev_args.force_feedback_max_lift_wait_steps = int(variant.force_max_wait)
    ev_args.force_feedback_lift_wait_close_delta = float(variant.force_lift_wait_close_delta)
    ev_args.force_feedback_max_preload_delta = float(variant.force_max_preload_delta)
    if variant.contact_gate_max_steps is not None:
        ev_args.contact_gate_max_steps = int(variant.contact_gate_max_steps)
    if variant.post_contact_settle_steps is not None:
        ev_args.post_contact_settle_steps = int(variant.post_contact_settle_steps)
    if variant.use_quality_head:
        ev_args.residual_quality_predictor = predictor
        ev_args.residual_quality_predictor_threshold = float(args.quality_threshold)
        ev_args.residual_quality_predictor_risk_threshold = float(args.risk_threshold)
        ev_args.residual_quality_predictor_requires_rule_ok = True
        ev_args.include_frame_state = True


def apply_case_teacher(case: event.RefineCase, variant: ResidualVariant) -> event.RefineCase:
    grasp_x = float(case.grasp_offset_x)
    updated_x = grasp_x
    if variant.grasp_x_min is not None:
        updated_x = max(updated_x, float(variant.grasp_x_min))
    if variant.grasp_x_max is not None:
        updated_x = min(updated_x, float(variant.grasp_x_max))
    if updated_x == grasp_x:
        return case
    return replace(
        case,
        name=f"{case.name}_gxclamp{updated_x:+.4f}".replace("+", "p").replace("-", "m").replace(".", "p"),
        grasp_offset_x=float(updated_x),
    )


def strip_trace(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "dense_sensor_trace"}


def morphology_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    holds = [row.get("hold_morphology", {}) for row in rows]

    def mean(key: str) -> float:
        values = [float(item.get(key, 0.0)) for item in holds if isinstance(item, dict)]
        return float(np.mean(values)) if values else 0.0

    return {
        "hold_true_two_tip_mean": mean("true_two_tip_pinch_fraction"),
        "hold_non_tip_ratio_mean": mean("non_tip_contact_ratio_mean"),
        "hold_wrap_fraction_mean": mean("wrap_frame_fraction"),
        "hold_floor_contact_fraction_mean": mean("floor_contact_fraction"),
        "max_penetration_m_max": float(max([float(row.get("max_penetration_m", 0.0)) for row in rows] + [0.0])),
    }


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    residual = [row.get("residual_micro_adjust", {}) for row in rows]
    force = [row.get("force_feedback_gate", {}) for row in rows]
    return {
        "residual_events_total": int(sum(int(item.get("events", 0)) for item in residual)),
        "residual_quality_bad_samples_total": int(sum(int(item.get("quality_bad_samples", 0)) for item in residual)),
        "residual_close_events_total": int(sum(int(item.get("close_events", 0)) for item in residual)),
        "residual_prelift_events_total": int(sum(int(item.get("prelift_events", 0)) for item in residual)),
        "residual_wait_steps_total": int(sum(int(item.get("wait_steps", 0)) for item in residual)),
        "residual_progress_drop_steps_total": int(sum(int(item.get("progress_drop_steps", 0)) for item in residual)),
        "residual_ik_solves_total": int(sum(int(item.get("ik_solves", 0)) for item in residual)),
        "residual_trial_fraction": float(np.mean([int(item.get("events", 0)) > 0 for item in residual]))
        if residual
        else 0.0,
        "force_gate_low_force_samples_total": int(sum(int(item.get("lift_low_force_samples", 0)) for item in force)),
        "force_gate_lift_wait_steps_total": int(sum(int(item.get("lift_wait_steps", 0)) for item in force)),
    }


def low_quality(record: dict[str, Any], args: argparse.Namespace) -> bool:
    prob = record.get("prob", {})
    return bool(
        float(prob.get("morphology_clean_now", 1.0)) < float(args.quality_threshold)
        or float(prob.get("lift_quality_now", 1.0)) < float(args.quality_threshold)
        or float(prob.get("wrap_now", 0.0)) > float(args.risk_threshold)
        or float(prob.get("floor_contact_now", 0.0)) > float(args.risk_threshold)
    )


def summarize_quality_records(records: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    phase_counts = Counter(str(row["phase"]) for row in records)
    low_rows = [row for row in records if low_quality(row, args)]
    low_phase_counts = Counter(str(row["phase"]) for row in low_rows)
    low_reason_counts = Counter(str(row["terminal_reason"]) for row in low_rows)
    by_candidate: dict[str, dict[str, Any]] = {}
    for candidate in sorted({str(row["candidate_name"]) for row in records}):
        subset = [row for row in records if row["candidate_name"] == candidate]
        subset_low = [row for row in subset if low_quality(row, args)]
        by_candidate[candidate] = {
            "frames": int(len(subset)),
            "low_quality_frames": int(len(subset_low)),
            "low_quality_fraction": float(len(subset_low) / max(1, len(subset))),
            "low_phase_counts": dict(Counter(str(row["phase"]) for row in subset_low)),
            "low_terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in subset_low)),
        }
    return {
        "frames": int(len(records)),
        "low_quality_frames": int(len(low_rows)),
        "low_quality_fraction": float(len(low_rows) / max(1, len(records))),
        "phase_counts": dict(phase_counts),
        "low_phase_counts": dict(low_phase_counts),
        "low_terminal_reason_counts": dict(low_reason_counts),
        "candidate_summary": by_candidate,
    }


def run_variant(
    *,
    scene: Path,
    mujoco: Any,
    args: argparse.Namespace,
    variant: ResidualVariant,
    predictor: QualityPredictor,
    trials: int,
    seed: int,
    capture_trace: bool,
) -> dict[str, Any]:
    rb_args = build_run_args(args, variant, seed=seed)
    rb_args.trials = int(trials)
    base = robustness.apply_base_offsets(robustness.selected_case_from_json(Path(rb_args.selected)), rb_args)
    ev_args = robustness.event_args_from(rb_args)
    apply_variant(ev_args, variant, predictor, args)
    ev_args.capture_dense_sensor_trace = bool(capture_trace)
    ev_args.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, Any]] = []
    quality_records: list[dict[str, Any]] = []
    for trial in range(max(1, int(trials))):
        case = robustness.perturb_case(base, rb_args, rng, trial)
        case = apply_case_teacher(case, variant)
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        trace = row.get("dense_sensor_trace", [])
        if capture_trace and trace:
            quality_records.extend(
                predictor.score_trace(
                    trace,
                    row,
                    case,
                    rb_args,
                    candidate_name=variant.candidate_name,
                    trial_index=trial,
                )
            )
        row["trial_index"] = int(trial)
        row["variant"] = variant.name
        row["variant_family"] = variant.family
        rows.append(row)
    summary = robustness.summarize(rows)
    summary.update(morphology_summary(rows))
    summary.update(residual_summary(rows))
    if capture_trace:
        summary["quality_windows"] = summarize_quality_records(quality_records, args)
    return {
        "variant": variant.__dict__,
        "seed": int(seed),
        "trials": int(trials),
        "summary": summary,
        "results": [strip_trace(row) for row in rows],
        "quality_records_sample": quality_records[: min(80, len(quality_records))],
    }


def rank_item(item: dict[str, Any]) -> tuple[Any, ...]:
    s = item["summary"]
    return (
        int(s.get("success_count", 0)),
        int(s.get("true_pinch_success_count", 0)),
        -int(s.get("terminal_reason_counts", {}).get("true_pinch_morphology_gate_failed", 0)),
        int(s.get("lift_success_count", 0)),
        int(s.get("contact_gate_success_count", 0)),
        int(s.get("release_success_count", 0)),
        -float(s.get("hold_non_tip_ratio_mean", 0.0)),
        -float(s.get("hold_wrap_fraction_mean", 0.0)),
        -int(s.get("residual_events_total", 0)),
    )


def decision(item: dict[str, Any], baseline: dict[str, Any] | None) -> str:
    if baseline is None:
        return "diagnostic"
    s = item["summary"]
    b = baseline["summary"]
    if item["variant"]["name"] == baseline["variant"]["name"]:
        return "frozen_anchor"
    success_gain = int(s.get("success_count", 0)) - int(b.get("success_count", 0))
    true_pinch_ok = int(s.get("true_pinch_success_count", 0)) >= int(b.get("true_pinch_success_count", 0))
    release_ok = int(s.get("release_success_count", 0)) >= max(0, int(b.get("release_success_count", 0)) - 1)
    morph_fail = int(s.get("terminal_reason_counts", {}).get("true_pinch_morphology_gate_failed", 0))
    base_morph_fail = int(b.get("terminal_reason_counts", {}).get("true_pinch_morphology_gate_failed", 0))
    if success_gain > 0 and true_pinch_ok and release_ok and morph_fail <= base_morph_fail:
        return "advance_candidate"
    if success_gain == 0 and true_pinch_ok and morph_fail <= base_morph_fail:
        return "tie_diagnostic"
    return "reject_or_keep_diagnostic"


def write_summary_csv(path: Path, rows: list[dict[str, Any]], stage_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "stage",
        "rank",
        "variant",
        "family",
        "candidate",
        "success",
        "trials",
        "contact",
        "lift",
        "true_pinch",
        "release",
        "residual_events",
        "hold_true_tip",
        "hold_non_tip",
        "hold_wrap",
        "terminal_reasons",
        "decision",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        baseline = next((row for row in rows if row["variant"]["name"] == "baseline_di_off"), None)
        for rank, row in enumerate(rows, start=1):
            s = row["summary"]
            writer.writerow(
                {
                    "stage": stage_name,
                    "rank": rank,
                    "variant": row["variant"]["name"],
                    "family": row["variant"]["family"],
                    "candidate": row["variant"]["candidate_name"],
                    "success": s.get("success_count", ""),
                    "trials": s.get("trials", ""),
                    "contact": s.get("contact_gate_success_count", ""),
                    "lift": s.get("lift_success_count", ""),
                    "true_pinch": s.get("true_pinch_success_count", ""),
                    "release": s.get("release_success_count", ""),
                    "residual_events": s.get("residual_events_total", ""),
                    "hold_true_tip": s.get("hold_true_two_tip_mean", ""),
                    "hold_non_tip": s.get("hold_non_tip_ratio_mean", ""),
                    "hold_wrap": s.get("hold_wrap_fraction_mean", ""),
                    "terminal_reasons": json.dumps(s.get("terminal_reason_counts", {}), ensure_ascii=False),
                    "decision": decision(row, baseline),
                }
            )


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mining = payload.get("mining", {}).get("summary", {})
    lines = [
        "# Stage3.12C Quality-Gated Residual Teacher v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only bounded residual teacher/search.\n",
        "- Uses Stage3.12B morphology-quality head as an intervention trigger for tiny residual probes.\n",
        "- Keeps scripted/event-gated controller and compares against frozen D-I.\n",
        "- No full-action ACT/DP, hardware runtime, real camera, real tactile, or demo-gallery promotion.\n\n",
        "## Failure Window Mining\n\n",
        f"- Mining variants: `{payload['mining'].get('variant_names', [])}`\n",
        f"- Evidence frames: `{mining.get('frames', 0)}`\n",
        f"- Low-quality frames: `{mining.get('low_quality_frames', 0)}` "
        f"(`{mining.get('low_quality_fraction', 0.0):.3f}`)\n",
        f"- Low-quality phases: `{mining.get('low_phase_counts', {})}`\n",
        f"- Low-quality terminal reasons: `{mining.get('low_terminal_reason_counts', {})}`\n\n",
        "## Smoke Ranking\n\n",
        "| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |\n",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|\n",
    ]
    smoke_baseline = next((row for row in payload["smoke_results"] if row["variant"]["name"] == "baseline_di_off"), None)
    for idx, item in enumerate(payload["smoke_results"], start=1):
        s = item["summary"]
        lines.append(
            f"| {idx} | `{item['variant']['name']}` | {s['success_count']} / {s['trials']} | "
            f"{s['contact_gate_success_count']} | {s['lift_success_count']} | {s['true_pinch_success_count']} | "
            f"{s['release_success_count']} | {s['residual_events_total']} | "
            f"{s['hold_true_two_tip_mean']:.3f} | {s['hold_non_tip_ratio_mean']:.3f} | "
            f"`{s['terminal_reason_counts']}` | `{decision(item, smoke_baseline)}` |\n"
        )
    lines.extend(
        [
            "\n## Validation Ranking\n\n",
            "| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |\n",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|\n",
        ]
    )
    validation_baseline = next(
        (row for row in payload["validation_results"] if row["variant"]["name"] == "baseline_di_off"), None
    )
    for idx, item in enumerate(payload["validation_results"], start=1):
        s = item["summary"]
        lines.append(
            f"| {idx} | `{item['variant']['name']}` | {s['success_count']} / {s['trials']} | "
            f"{s['contact_gate_success_count']} | {s['lift_success_count']} | {s['true_pinch_success_count']} | "
            f"{s['release_success_count']} | {s['residual_events_total']} | "
            f"{s['hold_true_two_tip_mean']:.3f} | {s['hold_non_tip_ratio_mean']:.3f} | "
            f"`{s['terminal_reason_counts']}` | `{decision(item, validation_baseline)}` |\n"
        )
    selected = payload.get("selected", {})
    if selected:
        s = selected["summary"]
        lines.extend(
            [
                "\n## Selected Diagnostic Outcome\n\n",
                f"- Variant: `{selected['variant']['name']}`\n",
                f"- Candidate family: `{selected['variant']['family']}`\n",
                f"- Validation success: `{s['success_count']} / {s['trials']}`\n",
                f"- Contact/lift/true-pinch/release: `{s['contact_gate_success_count']}` / "
                f"`{s['lift_success_count']}` / `{s['true_pinch_success_count']}` / "
                f"`{s['release_success_count']}`\n",
                f"- Residual events: `{s['residual_events_total']}`\n",
                f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
            ]
        )
    lines.extend(
        [
            "\n## Decision\n\n",
            f"{payload.get('decision_summary', 'TBD')}\n\n",
            "## Next\n\n",
            "- If validation beats frozen D-I without morphology regression, run the multiseed 150-trial gate.\n",
            "- If residuals only trade lift/contact/morphology failures, keep D-I frozen and move to contact geometry or richer residual-policy data.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage3.12C quality-gated residual teacher probe.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--seed", type=int, default=20260618)
    parser.add_argument("--validation-seed", type=int, default=20265612)
    parser.add_argument("--mining-trials", type=int, default=8)
    parser.add_argument("--smoke-trials", type=int, default=8)
    parser.add_argument("--validation-trials", type=int, default=50)
    parser.add_argument("--final-candidates", type=int, default=2)
    parser.add_argument("--skip-validation", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--variant", default=None, help="Optional comma-separated variant names.")
    parser.add_argument("--quality-threshold", type=float, default=0.55)
    parser.add_argument("--risk-threshold", type=float, default=0.45)
    parser.add_argument("--dense-trace-sample-every", type=int, default=5)
    parser.add_argument("--object-pose-noise-xy-m", type=float, default=0.003)
    parser.add_argument("--grasp-target-noise-xy-m", type=float, default=0.002)
    parser.add_argument("--grasp-target-noise-z-m", type=float, default=0.001)
    parser.add_argument("--radius-jitter-m", type=float, default=0.001)
    parser.add_argument("--mass-jitter-kg", type=float, default=0.002)
    parser.add_argument("--friction-scale-jitter", type=float, default=0.08)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    predictor = QualityPredictor(Path(args.checkpoint))
    variants = variant_grid(args)
    baseline = next((variant for variant in variants if variant.name == "baseline_di_off"), None)
    if baseline is None:
        raise ValueError("baseline_di_off must be included for comparable ranking.")

    mining_variants = [
        variant
        for variant in variants
        if variant.name in {"baseline_di_off", "lift_ls460_off"}
    ]
    mining_records: list[dict[str, Any]] = []
    mining_items: list[dict[str, Any]] = []
    for idx, variant in enumerate(mining_variants, start=1):
        item = run_variant(
            scene=scene,
            mujoco=mujoco,
            args=args,
            variant=variant,
            predictor=predictor,
            trials=int(args.mining_trials),
            seed=int(args.seed) + idx * 1000,
            capture_trace=True,
        )
        mining_items.append(item)
        for record in item.get("quality_records_sample", []):
            mining_records.append(record)
        q = item["summary"].get("quality_windows", {})
        print(
            f"mine {idx:02d}/{len(mining_variants):02d} {variant.name} "
            f"success={item['summary']['success_count']}/{item['summary']['trials']} "
            f"low_quality={q.get('low_quality_frames', 0)}/{q.get('frames', 0)}"
        )

    smoke_results: list[dict[str, Any]] = []
    for idx, variant in enumerate(variants, start=1):
        item = run_variant(
            scene=scene,
            mujoco=mujoco,
            args=args,
            variant=variant,
            predictor=predictor,
            trials=int(args.smoke_trials),
            seed=int(args.seed),
            capture_trace=False,
        )
        smoke_results.append(item)
        s = item["summary"]
        print(
            f"smoke {idx:02d}/{len(variants):02d} {variant.name} "
            f"{s['success_count']}/{s['trials']} contact={s['contact_gate_success_count']} "
            f"lift={s['lift_success_count']} residual={s['residual_events_total']} "
            f"reasons={s['terminal_reason_counts']}"
        )
    smoke_results.sort(key=rank_item, reverse=True)

    validation_results: list[dict[str, Any]] = []
    if not bool(args.skip_validation):
        final_plan = smoke_results[: max(1, int(args.final_candidates))]
        if not any(item["variant"]["name"] == "baseline_di_off" for item in final_plan):
            baseline_item = next((item for item in smoke_results if item["variant"]["name"] == "baseline_di_off"), None)
            if baseline_item is not None:
                final_plan.append(baseline_item)
        seen = set()
        final_variants: list[ResidualVariant] = []
        for item in final_plan:
            name = item["variant"]["name"]
            if name in seen:
                continue
            seen.add(name)
            final_variants.append(ResidualVariant(**item["variant"]))
        for idx, variant in enumerate(final_variants, start=1):
            item = run_variant(
                scene=scene,
                mujoco=mujoco,
                args=args,
                variant=variant,
                predictor=predictor,
                trials=int(args.validation_trials),
                seed=int(args.validation_seed),
                capture_trace=False,
            )
            validation_results.append(item)
            s = item["summary"]
            print(
                f"validation {idx:02d}/{len(final_variants):02d} {variant.name} "
                f"{s['success_count']}/{s['trials']} contact={s['contact_gate_success_count']} "
                f"lift={s['lift_success_count']} residual={s['residual_events_total']} "
                f"reasons={s['terminal_reason_counts']}"
            )
        validation_results.sort(key=rank_item, reverse=True)

    validation_baseline = next((row for row in validation_results if row["variant"]["name"] == "baseline_di_off"), None)
    selected = validation_results[0] if validation_results else smoke_results[0]
    selected_decision = decision(selected, validation_baseline or next((row for row in smoke_results if row["variant"]["name"] == "baseline_di_off"), None))
    if selected_decision == "advance_candidate":
        decision_summary = (
            "Selected candidate beat the frozen D-I anchor on the matched validation gate without a true-pinch "
            "morphology regression. It should advance to the 150-trial multiseed gate, not direct promotion yet."
        )
    elif selected_decision == "tie_diagnostic":
        decision_summary = (
            "Best candidate tied D-I on matched validation. Keep it as diagnostic only; do not promote without "
            "a multiseed gain."
        )
    else:
        decision_summary = (
            "No residual candidate clearly beat frozen D-I on this gate. Keep D-I frozen and use the mined "
            "windows to guide the next contact-geometry or richer residual-policy step."
        )

    mining_summary = {
        "variant_names": [variant.name for variant in mining_variants],
        "summary": {
            "frames": int(sum(item["summary"].get("quality_windows", {}).get("frames", 0) for item in mining_items)),
            "low_quality_frames": int(
                sum(item["summary"].get("quality_windows", {}).get("low_quality_frames", 0) for item in mining_items)
            ),
            "low_quality_fraction": float(
                sum(item["summary"].get("quality_windows", {}).get("low_quality_frames", 0) for item in mining_items)
                / max(1, sum(item["summary"].get("quality_windows", {}).get("frames", 0) for item in mining_items))
            ),
            "low_phase_counts": dict(
                sum(
                    (
                        Counter(item["summary"].get("quality_windows", {}).get("low_phase_counts", {}))
                        for item in mining_items
                    ),
                    Counter(),
                )
            ),
            "low_terminal_reason_counts": dict(
                sum(
                    (
                        Counter(item["summary"].get("quality_windows", {}).get("low_terminal_reason_counts", {}))
                        for item in mining_items
                    ),
                    Counter(),
                )
            ),
        },
        "items": mining_items,
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.12C",
        "status": STATUS,
        "scene": str(scene),
        "selected_path": str(Path(args.selected).resolve()),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "report": str(Path(args.report).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "summary_csv": str(Path(args.summary_csv).resolve()),
        "args": vars(args),
        "mining": mining_summary,
        "smoke_results": smoke_results,
        "validation_results": validation_results,
        "selected": selected,
        "selected_decision": selected_decision,
        "decision_summary": decision_summary,
        "boundary": {
            "mujoco_only": True,
            "uses_stage3_12b_quality_head": True,
            "bounded_residual_teacher_probe_only": True,
            "full_action_policy": False,
            "hardware_runtime": False,
            "controller_promoted": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    write_summary_csv(Path(args.summary_csv), validation_results or smoke_results, "validation" if validation_results else "smoke")
    print(json.dumps(json_ready({"selected": selected["variant"]["name"], "decision": selected_decision, "summary": selected["summary"]}), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    print(f"Saved summary CSV: {args.summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
