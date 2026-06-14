#!/usr/bin/env python3
"""Export Stage4 force-feedback packets from a Stage3.11 MuJoCo replay.

This is a bridge artifact: it converts simulated Stage3.11 motor force-feedback
telemetry into the Stage4 hardware-facing packet contract. It does not claim
real hardware, real tactile sensors, or direct force control.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[2]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"

DEFAULT_SELECTED = META / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_SCHEMA = PROJECT_ROOT / "docs" / "stage4_force_feedback_data_contract_v0.schema.json"
DEFAULT_JSONL = DATA / "stage4_force_feedback_packets_v0.jsonl"
DEFAULT_CSV = DATA / "stage4_force_feedback_packets_v0_summary.csv"
DEFAULT_METADATA = META / "stage4_force_feedback_packets_v0.json"
DEFAULT_REPORT = DOCS / "stage4_force_feedback_packet_export_v0_report.md"

SCHEMA_VERSION = "stage4_force_feedback_packet_v0"
SKILL_ID = "thumb_middle_small_ball_pinch_release"
GRASP_EVIDENCE_PHASES = {"contact_gate", "post_contact_settle", "preload", "slow_lift", "hold"}
FINGER_GROUPS = {"thumb", "index", "middle", "ring", "little", "wrist", "arm", "other"}


def as_float(value: Any, default: Any = 0.0) -> float:
    try:
        if value is None:
            if default is None:
                return None
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        if default is None:
            return None
        return float(default)


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def clamp01(value: float) -> float:
    return float(np.clip(float(value), 0.0, 1.0))


def robust_defaults_for_export(args: argparse.Namespace) -> argparse.Namespace:
    rb = robustness.build_parser().parse_args([])
    rb.scene = Path(args.scene)
    rb.selected = Path(args.selected)
    rb.seed = int(args.seed)
    rb.enable_motor_force_feedback = True
    rb.enable_force_feedback_lift_gate = bool(args.enable_force_feedback_lift_gate)
    rb.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))
    rb.morphology_sample_every = int(args.morphology_sample_every)
    rb.motor_feedback_seed = int(args.motor_feedback_seed)
    rb.motor_current_limit_a = float(args.motor_current_limit_a)
    rb.motor_bus_voltage_v = float(args.motor_bus_voltage_v)
    rb.motor_current_noise_a = float(args.motor_current_noise_a)
    if args.override_grasp_offset_x is not None:
        rb.override_grasp_offset_x = float(args.override_grasp_offset_x)
    if args.override_grasp_offset_y is not None:
        rb.override_grasp_offset_y = float(args.override_grasp_offset_y)
    if args.override_grasp_offset_z is not None:
        rb.override_grasp_offset_z = float(args.override_grasp_offset_z)
    if args.override_lift_steps is not None:
        rb.override_lift_steps = int(args.override_lift_steps)
    return rb


def packet_sample_rate(trace: list[dict[str, Any]], fallback_hz: float) -> float:
    times = [as_float(frame.get("time_s"), None) for frame in trace]
    times = [value for value in times if value is not None]
    deltas = [b - a for a, b in zip(times, times[1:]) if b > a]
    if deltas:
        return float(1.0 / np.median(deltas))
    return float(fallback_hz)


def infer_contact_regions(morph: dict[str, Any], active_finger: str) -> list[str]:
    regions: list[str] = []
    tip_regions = morph.get("tip_regions", [])
    support_regions = morph.get("support_regions", [])
    if isinstance(tip_regions, list):
        for region in tip_regions:
            text = str(region)
            if text and text not in regions:
                regions.append(text)
    if as_bool(morph.get("true_two_tip_pinch")):
        for region in ("thumb_tip", f"{active_finger}_tip"):
            if region not in regions:
                regions.append(region)
    if isinstance(support_regions, list):
        for region in support_regions:
            text = str(region)
            if text and text not in regions:
                regions.append(text)
    if not regions and int(as_float(morph.get("hand_contacts"))) > 0:
        regions.append("hand_contact_unknown")
    return regions


def contact_quality(frame: dict[str, Any], case: event.RefineCase, args: argparse.Namespace) -> dict[str, bool]:
    phase = str(frame.get("label", "unknown"))
    morph = frame.get("morphology", {})
    if not isinstance(morph, dict):
        morph = {}
    pair = frame.get("motor_force_feedback", {}).get("active_pair", {})
    if not isinstance(pair, dict):
        pair = {}
    min_tension = (
        float(args.force_feedback_min_hold_pair_tension_n)
        if phase == "hold"
        else float(args.force_feedback_min_slow_lift_pair_tension_n)
    )
    force_configured = as_bool(pair.get("configured"))
    low_force = bool(force_configured and as_float(pair.get("total_tendon_tension_n")) < min_tension)
    force_imbalance = bool(force_configured and as_float(pair.get("balance_ratio")) < float(args.force_feedback_min_pair_balance))
    force_saturation = bool(
        force_configured
        and (
            as_float(pair.get("max_abs_iq_a")) > float(args.force_feedback_max_pair_iq_a)
            or int(as_float(pair.get("saturated_actuator_count"))) > 0
        )
    )
    penetration_risk = bool(as_float(frame.get("max_penetration_m")) > float(args.max_penetration_m))
    true_two_tip = as_bool(morph.get("true_two_tip_pinch"))
    wrap = as_bool(morph.get("wrap_or_support"))
    floor_contact = int(as_float(morph.get("floor_contacts"))) > 0
    contact_present = int(as_float(morph.get("hand_contacts"))) > 0
    force_ok = bool(force_configured and not low_force and not force_imbalance and not force_saturation)
    morphology_ok = bool(true_two_tip and not wrap and not floor_contact and not penetration_risk)
    grasp_phase = phase in GRASP_EVIDENCE_PHASES
    lift_quality = bool(grasp_phase and morphology_ok and force_ok)
    hold_safe = bool(phase == "hold" and lift_quality and as_float(frame.get("lift_m")) >= float(case.min_lift_height))
    return {
        "low_force": low_force,
        "force_imbalance": force_imbalance,
        "force_saturation": force_saturation,
        "penetration_risk": penetration_risk,
        "lift_quality_now": lift_quality,
        "adjust_needed_now": bool(grasp_phase and not lift_quality),
        "hold_safe_now": hold_safe,
        "abort_required": bool(
            (floor_contact and contact_present and phase in {"slow_lift", "hold"})
            or (contact_present and penetration_risk)
            or force_saturation
        ),
    }


def actuator_packet(row: dict[str, Any], bus_voltage_v: float) -> dict[str, Any]:
    group = str(row.get("group", "other"))
    if group not in FINGER_GROUPS:
        group = "other"
    return {
        "actuator_id": str(row.get("actuator", "unknown_actuator")),
        "joint_id": str(row.get("joint", "")),
        "finger_group": group,
        "iq_command_a": as_float(row.get("iq_cmd_a")),
        "iq_measured_a": as_float(row.get("iq_measured_a")),
        "bus_voltage_v": float(bus_voltage_v),
        "bus_current_a": max(0.0, as_float(row.get("bus_current_a"))),
        "torque_estimate_nm": as_float(row.get("motor_torque_nm")),
        "encoder_position_rad": as_float(row.get("encoder_position_rad")),
        "encoder_velocity_rad_s": as_float(row.get("encoder_velocity_rad_s")),
        "tendon_tension_n": max(0.0, as_float(row.get("tendon_tension_n"))),
        "tendon_displacement_m": None,
        "slack_estimate": None,
        "temperature_c": None,
        "current_saturated": as_bool(row.get("current_saturated")),
        "fault_flags": ["current_saturation_proxy"] if as_bool(row.get("current_saturated")) else [],
    }


def selected_actuators(feedback: dict[str, Any], bus_voltage_v: float, max_actuators: int) -> list[dict[str, Any]]:
    rows = feedback.get("top_hand_actuators_by_tension") or feedback.get("top_actuators_by_tension") or []
    if not isinstance(rows, list):
        rows = []
    actuators = [actuator_packet(row, bus_voltage_v) for row in rows[: max(1, int(max_actuators))]]
    if not actuators:
        actuators.append(
            {
                "actuator_id": "no_feedback_available",
                "joint_id": "",
                "finger_group": "other",
                "iq_command_a": 0.0,
                "iq_measured_a": 0.0,
                "bus_voltage_v": float(bus_voltage_v),
                "bus_current_a": 0.0,
                "torque_estimate_nm": 0.0,
                "encoder_position_rad": 0.0,
                "encoder_velocity_rad_s": 0.0,
                "tendon_tension_n": 0.0,
                "tendon_displacement_m": None,
                "slack_estimate": None,
                "temperature_c": None,
                "current_saturated": False,
                "fault_flags": ["missing_sim_feedback"],
            }
        )
    return actuators


def packet_from_frame(
    frame: dict[str, Any],
    *,
    sequence_id: int,
    sample_rate_hz: float,
    case: event.RefineCase,
    args: argparse.Namespace,
) -> dict[str, Any]:
    feedback = frame.get("motor_force_feedback", {})
    if not isinstance(feedback, dict):
        feedback = {}
    pair = feedback.get("active_pair", {})
    if not isinstance(pair, dict):
        pair = {}
    morph = frame.get("morphology", {})
    if not isinstance(morph, dict):
        morph = {}
    quality = contact_quality(frame, case, args)
    actuators = selected_actuators(feedback, float(args.motor_bus_voltage_v), int(args.max_actuators_per_packet))
    saturated = sum(1 for row in actuators if row["current_saturated"])
    fault_flags = sorted({flag for row in actuators for flag in row.get("fault_flags", [])})
    timestamp_ns = int(round(as_float(frame.get("time_s")) * 1_000_000_000.0))
    contact_regions = infer_contact_regions(morph, case.candidate.active_finger)
    contact_present = bool(int(as_float(morph.get("hand_contacts"))) > 0)
    slip_risk = 0.0 if not contact_present else 0.05
    if contact_present and as_bool(morph.get("wrap_or_support")):
        slip_risk = 0.45
    elif contact_present and (quality["low_force"] or quality["force_imbalance"]):
        slip_risk = 0.35
    crush_risk = clamp01(as_float(frame.get("max_penetration_m")) / max(float(args.max_penetration_m), 1e-9))
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp_ns": timestamp_ns,
        "sequence_id": int(sequence_id),
        "source": "mujoco",
        "control_tick": int(frame.get("dense_step_index", sequence_id)),
        "sample_rate_hz": float(sample_rate_hz),
        "skill_id": str(args.skill_id),
        "phase_id": str(frame.get("label", "unknown")),
        "actuators": actuators,
        "active_pair": {
            "configured": as_bool(pair.get("configured")),
            "groups": [str(group) for group in pair.get("groups", []) if str(group) in {"thumb", "index", "middle", "ring", "little"}],
            "total_tension_n": max(0.0, as_float(pair.get("total_tendon_tension_n"))),
            "balance_ratio": max(0.0, as_float(pair.get("balance_ratio"))),
            "tension_delta_abs_n": max(0.0, as_float(pair.get("tension_delta_abs_n"))),
            "max_abs_iq_a": max(0.0, as_float(pair.get("max_abs_iq_a"))),
            "saturation_count": int(as_float(pair.get("saturated_actuator_count"))),
        },
        "contact": {
            "contact_present": contact_present,
            "contact_regions": contact_regions,
            "slip_risk": float(slip_risk),
            "crush_risk": float(crush_risk),
            "vision_quality": 1.0,
            "lift_quality_now": quality["lift_quality_now"],
            "adjust_needed_now": quality["adjust_needed_now"],
            "hold_safe_now": quality["hold_safe_now"],
        },
        "safety": {
            "e_stop": False,
            "abort_required": quality["abort_required"],
            "current_limit_a": float(args.motor_current_limit_a),
            "fault_active": bool(fault_flags),
            "fault_flags": fault_flags,
        },
    }


def write_jsonl(path: Path, packets: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for packet in packets:
            f.write(json.dumps(json_ready(packet), ensure_ascii=False, sort_keys=True) + "\n")


def write_csv_summary(path: Path, packets: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "sequence_id",
        "timestamp_ns",
        "control_tick",
        "phase_id",
        "contact_present",
        "contact_regions",
        "active_pair_total_tension_n",
        "active_pair_balance_ratio",
        "active_pair_max_abs_iq_a",
        "active_pair_saturation_count",
        "actuator_count",
        "max_actuator_tension_n",
        "max_actuator_abs_iq_a",
        "lift_quality_now",
        "adjust_needed_now",
        "hold_safe_now",
        "abort_required",
        "fault_active",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for packet in packets:
            actuators = packet["actuators"]
            writer.writerow(
                {
                    "sequence_id": packet["sequence_id"],
                    "timestamp_ns": packet["timestamp_ns"],
                    "control_tick": packet["control_tick"],
                    "phase_id": packet["phase_id"],
                    "contact_present": packet["contact"]["contact_present"],
                    "contact_regions": ";".join(packet["contact"]["contact_regions"]),
                    "active_pair_total_tension_n": packet["active_pair"]["total_tension_n"],
                    "active_pair_balance_ratio": packet["active_pair"]["balance_ratio"],
                    "active_pair_max_abs_iq_a": packet["active_pair"]["max_abs_iq_a"],
                    "active_pair_saturation_count": packet["active_pair"]["saturation_count"],
                    "actuator_count": len(actuators),
                    "max_actuator_tension_n": max([as_float(row.get("tendon_tension_n")) for row in actuators] + [0.0]),
                    "max_actuator_abs_iq_a": max([abs(as_float(row.get("iq_measured_a"))) for row in actuators] + [0.0]),
                    "lift_quality_now": packet["contact"]["lift_quality_now"],
                    "adjust_needed_now": packet["contact"]["adjust_needed_now"],
                    "hold_safe_now": packet["contact"]["hold_safe_now"],
                    "abort_required": packet["safety"]["abort_required"],
                    "fault_active": packet["safety"]["fault_active"],
                }
            )


def validate_packets(schema_path: Path, packets: list[dict[str, Any]]) -> tuple[bool, str]:
    try:
        import jsonschema
    except ImportError as exc:
        return False, f"jsonschema is not installed: {exc}"
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for idx, packet in enumerate(packets):
        errors = sorted(validator.iter_errors(packet), key=lambda err: err.path)
        if errors:
            first = errors[0]
            return False, f"packet {idx} schema error at {list(first.path)}: {first.message}"
    return True, "schema validation OK"


def summarize_packets(packets: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    phases = Counter(str(packet.get("phase_id", "unknown")) for packet in packets)
    timestamps = [int(packet["timestamp_ns"]) for packet in packets]
    sequence_ids = [int(packet["sequence_id"]) for packet in packets]
    dropped = 0
    if sequence_ids:
        dropped = sum(max(0, b - a - 1) for a, b in zip(sequence_ids, sequence_ids[1:]))
    pair_tensions = [packet["active_pair"]["total_tension_n"] for packet in packets]
    pair_balances = [packet["active_pair"]["balance_ratio"] for packet in packets]
    pair_iq = [packet["active_pair"]["max_abs_iq_a"] for packet in packets]
    return {
        "episodes": int(len(results)),
        "episode_success_count": int(sum(1 for row in results if as_bool(row.get("success")))),
        "packets": int(len(packets)),
        "phase_counts": dict(phases),
        "sequence_start": int(sequence_ids[0]) if sequence_ids else 0,
        "sequence_end": int(sequence_ids[-1]) if sequence_ids else 0,
        "dropped_sequence_ids": int(dropped),
        "timestamp_monotonic": bool(all(b >= a for a, b in zip(timestamps, timestamps[1:]))),
        "active_pair_total_tension_mean_n": float(np.mean(pair_tensions)) if pair_tensions else 0.0,
        "active_pair_total_tension_max_n": float(max(pair_tensions)) if pair_tensions else 0.0,
        "active_pair_balance_mean": float(np.mean(pair_balances)) if pair_balances else 0.0,
        "active_pair_balance_min": float(min(pair_balances)) if pair_balances else 0.0,
        "active_pair_max_abs_iq_a": float(max(pair_iq)) if pair_iq else 0.0,
        "lift_quality_true_packets": int(sum(1 for packet in packets if packet["contact"]["lift_quality_now"])),
        "adjust_needed_packets": int(sum(1 for packet in packets if packet["contact"]["adjust_needed_now"])),
        "hold_safe_packets": int(sum(1 for packet in packets if packet["contact"]["hold_safe_now"])),
        "abort_required_packets": int(sum(1 for packet in packets if packet["safety"]["abort_required"])),
        "fault_active_packets": int(sum(1 for packet in packets if packet["safety"]["fault_active"])),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage4 Force-Feedback Packet Export v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only replay from the frozen Stage3.11D-I demo-quality candidate.\n",
        "- Exports simulated motor force-feedback into the Stage4 packet contract.\n",
        "- Does not claim hardware runtime, real tactile sensors, real cameras, or direct force control.\n\n",
        "## Outputs\n\n",
        f"- JSONL packets: `{payload['outputs']['jsonl']}`\n",
        f"- CSV summary: `{payload['outputs']['csv']}`\n",
        f"- Metadata: `{payload['outputs']['metadata']}`\n",
        f"- Schema: `{payload['schema']}`\n\n",
        "## Summary\n\n",
        f"- Episodes: `{s['episode_success_count']} / {s['episodes']}` success in this export replay.\n",
        f"- Packets: `{s['packets']}`\n",
        f"- Phase counts: `{s['phase_counts']}`\n",
        f"- Sequence range: `{s['sequence_start']}..{s['sequence_end']}`, dropped IDs `{s['dropped_sequence_ids']}`\n",
        f"- Timestamp monotonic: `{s['timestamp_monotonic']}`\n",
        f"- Active-pair tension mean/max: `{s['active_pair_total_tension_mean_n']:.4f}` / "
        f"`{s['active_pair_total_tension_max_n']:.4f} N`\n",
        f"- Active-pair balance mean/min: `{s['active_pair_balance_mean']:.4f}` / "
        f"`{s['active_pair_balance_min']:.4f}`\n",
        f"- Active-pair max |Iq|: `{s['active_pair_max_abs_iq_a']:.4f} A`\n",
        f"- lift_quality packets: `{s['lift_quality_true_packets']}`\n",
        f"- adjust_needed packets: `{s['adjust_needed_packets']}`\n",
        f"- hold_safe packets: `{s['hold_safe_packets']}`\n",
        f"- abort_required packets: `{s['abort_required_packets']}`\n",
        f"- fault_active packets: `{s['fault_active_packets']}`\n",
        f"- Validation: `{payload['validation']['message']}`\n\n",
        "## Gate F1\n\n",
        "This run passes Gate F1 when packet count is nonzero, sequence IDs are contiguous, timestamps are monotonic, and schema validation passes.\n\n",
        "## Next\n\n",
        "- F2: add a fake bench logger/replay that emits the same packets with timing and fault injection.\n",
        "- Keep residual-policy work closed until F0/F1/F2 are all green.\n",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Stage4 force-feedback packets from Stage3.11 MuJoCo telemetry.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260613)
    parser.add_argument("--randomized", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--dense-trace-sample-every", type=int, default=20)
    parser.add_argument("--morphology-sample-every", type=int, default=5)
    parser.add_argument("--sample-rate-hz", type=float, default=0.0)
    parser.add_argument("--skill-id", default=SKILL_ID)
    parser.add_argument("--max-actuators-per-packet", type=int, default=6)
    parser.add_argument("--max-packets", type=int, default=0)
    parser.add_argument("--motor-current-limit-a", type=float, default=4.0)
    parser.add_argument("--motor-bus-voltage-v", type=float, default=24.0)
    parser.add_argument("--motor-current-noise-a", type=float, default=0.025)
    parser.add_argument("--motor-feedback-seed", type=int, default=20260613)
    parser.add_argument("--enable-force-feedback-lift-gate", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-min-slow-lift-pair-tension-n", type=float, default=4.0)
    parser.add_argument("--force-feedback-min-hold-pair-tension-n", type=float, default=2.0)
    parser.add_argument("--force-feedback-min-pair-balance", type=float, default=0.01)
    parser.add_argument("--force-feedback-max-pair-iq-a", type=float, default=4.0)
    parser.add_argument("--max-penetration-m", type=float, default=0.006)
    parser.add_argument("--override-grasp-offset-x", type=float, default=None)
    parser.add_argument("--override-grasp-offset-y", type=float, default=None)
    parser.add_argument("--override-grasp-offset-z", type=float, default=None)
    parser.add_argument("--override-lift-steps", type=int, default=None)
    parser.add_argument("--validate-schema", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    selected = Path(args.selected).resolve()
    if not selected.exists():
        raise FileNotFoundError(selected)

    rb_args = robust_defaults_for_export(args)
    base = robustness.apply_base_offsets(robustness.selected_case_from_json(selected), rb_args)
    ev_args = robustness.event_args_from(rb_args)
    ev_args.capture_dense_sensor_trace = True
    ev_args.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))
    ev_args.enable_motor_force_feedback = True
    rng = np.random.default_rng(int(args.seed))

    packets: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    sequence_id = 0
    last_timestamp_ns = -1
    for episode_idx in range(max(1, int(args.episodes))):
        case = robustness.perturb_case(base, rb_args, rng, episode_idx) if bool(args.randomized) else base
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        trace = row.get("dense_sensor_trace", [])
        if not isinstance(trace, list):
            trace = []
        sample_rate = float(args.sample_rate_hz) if float(args.sample_rate_hz) > 0.0 else packet_sample_rate(trace, 1.0)
        for frame in trace:
            packet = packet_from_frame(
                frame,
                sequence_id=sequence_id,
                sample_rate_hz=sample_rate,
                case=case,
                args=args,
            )
            if int(packet["timestamp_ns"]) <= last_timestamp_ns:
                step_ns = max(1, int(round(1_000_000_000.0 / max(sample_rate, 1e-9))))
                packet["timestamp_ns"] = int(last_timestamp_ns + step_ns)
            last_timestamp_ns = int(packet["timestamp_ns"])
            packets.append(packet)
            sequence_id += 1
            if int(args.max_packets) > 0 and len(packets) >= int(args.max_packets):
                break
        compact = {key: value for key, value in row.items() if key != "dense_sensor_trace"}
        compact["episode_index"] = int(episode_idx)
        compact["packet_rows"] = int(len(trace))
        compact["exported_packet_rows"] = int(min(len(trace), max(0, len(packets))))
        results.append(compact)
        print(
            f"{episode_idx + 1:03d}/{args.episodes:03d} {row.get('status')} "
            f"packets={len(trace)} exported_total={len(packets)} reason={row.get('terminal_reason')}"
        )
        if int(args.max_packets) > 0 and len(packets) >= int(args.max_packets):
            break

    if not packets:
        raise RuntimeError("No packets were exported; dense trace is empty.")

    validation_ok = True
    validation_message = "schema validation skipped"
    if bool(args.validate_schema):
        validation_ok, validation_message = validate_packets(Path(args.schema), packets)
        if not validation_ok:
            raise RuntimeError(validation_message)

    summary = summarize_packets(packets, results)
    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage4.0-F1",
        "status": "stage4_force_feedback_packet_export_v0_mujoco_only",
        "scene": str(scene),
        "selected": str(selected),
        "schema": str(Path(args.schema).resolve()),
        "outputs": {
            "jsonl": str(Path(args.jsonl).resolve()),
            "csv": str(Path(args.csv).resolve()),
            "metadata": str(Path(args.metadata).resolve()),
            "report": str(Path(args.report).resolve()),
        },
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
        "summary": summary,
        "validation": {
            "schema_checked": bool(args.validate_schema),
            "ok": bool(validation_ok),
            "message": validation_message,
        },
        "boundary": {
            "mujoco_only": True,
            "motor_feedback_is_simulated": True,
            "hardware_runtime": False,
            "real_camera": False,
            "real_tactile": False,
            "direct_force_control_promoted": False,
        },
        "results": results,
    }

    write_jsonl(Path(args.jsonl), packets)
    write_csv_summary(Path(args.csv), packets)
    Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metadata).write_text(json.dumps(json_ready(metadata), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(
        Path(args.report),
        {
            "generated_at": metadata["generated_at"],
            "outputs": metadata["outputs"],
            "schema": metadata["schema"],
            "summary": summary,
            "validation": metadata["validation"],
        },
    )
    print(f"wrote {len(packets)} packets -> {Path(args.jsonl).resolve()}")
    print(validation_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
