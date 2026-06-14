#!/usr/bin/env python3
"""Replay Stage4 packets as a fake hardware bench logger.

This F2 tool takes the F1 MuJoCo packet stream, rewrites it as a bench-replay
stream, injects timing and driver-like faults, and verifies that the packet
contract remains usable before real hardware exists.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from arm_hand_stage1_task_api import json_ready


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[2]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"

DEFAULT_INPUT_JSONL = DATA / "stage4_force_feedback_packets_v0.jsonl"
DEFAULT_SCHEMA = PROJECT_ROOT / "docs" / "stage4_force_feedback_data_contract_v0.schema.json"
DEFAULT_JSONL = DATA / "stage4_fake_bench_replay_v0.jsonl"
DEFAULT_CSV = DATA / "stage4_fake_bench_replay_v0_summary.csv"
DEFAULT_METADATA = META / "stage4_fake_bench_replay_v0.json"
DEFAULT_REPORT = DOCS / "stage4_fake_bench_replay_v0_report.md"

FAULT_TYPES = [
    "drop_packet",
    "delay_spike",
    "current_saturation",
    "encoder_freeze",
    "bus_voltage_sag",
    "tension_dropout",
    "driver_fault",
    "e_stop",
]


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                packets.append(json.loads(line))
    if not packets:
        raise ValueError(f"No packets found in {path}")
    return packets


def append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def add_safety_fault(packet: dict[str, Any], flag: str) -> None:
    safety = packet["safety"]
    safety["fault_active"] = True
    append_unique(safety["fault_flags"], flag)


def add_actuator_fault(actuator: dict[str, Any], flag: str) -> None:
    actuator["current_saturated"] = bool(actuator["current_saturated"] or flag == "current_saturation_injected")
    append_unique(actuator["fault_flags"], flag)


def inject_current_saturation(packet: dict[str, Any], args: argparse.Namespace) -> None:
    limit = float(args.current_limit_a)
    packet["active_pair"]["max_abs_iq_a"] = max(packet["active_pair"]["max_abs_iq_a"], limit * 1.08)
    packet["active_pair"]["saturation_count"] = int(packet["active_pair"]["saturation_count"]) + 1
    for actuator in packet["actuators"][: max(1, int(args.saturate_actuator_count))]:
        sign = 1.0 if as_float(actuator.get("iq_measured_a")) >= 0 else -1.0
        actuator["iq_measured_a"] = sign * limit * 1.08
        actuator["iq_command_a"] = sign * limit * 1.10
        add_actuator_fault(actuator, "current_saturation_injected")
    add_safety_fault(packet, "current_saturation_injected")


def inject_encoder_freeze(packet: dict[str, Any], previous_positions: dict[str, float]) -> None:
    for actuator in packet["actuators"]:
        actuator_id = str(actuator.get("actuator_id", ""))
        if actuator_id in previous_positions:
            actuator["encoder_position_rad"] = previous_positions[actuator_id]
        actuator["encoder_velocity_rad_s"] = 0.0
        add_actuator_fault(actuator, "encoder_freeze_injected")
    add_safety_fault(packet, "encoder_freeze_injected")


def inject_bus_voltage_sag(packet: dict[str, Any], args: argparse.Namespace) -> None:
    sag_voltage = max(0.0, float(args.nominal_bus_voltage_v) * float(args.bus_sag_fraction))
    for actuator in packet["actuators"]:
        actuator["bus_voltage_v"] = sag_voltage
        actuator["bus_current_a"] = max(0.0, as_float(actuator.get("bus_current_a")) * 1.15)
        add_actuator_fault(actuator, "bus_voltage_sag_injected")
    add_safety_fault(packet, "bus_voltage_sag_injected")


def inject_tension_dropout(packet: dict[str, Any]) -> None:
    packet["active_pair"]["total_tension_n"] = 0.0
    packet["active_pair"]["balance_ratio"] = 0.0
    packet["active_pair"]["tension_delta_abs_n"] = 0.0
    for actuator in packet["actuators"]:
        actuator["tendon_tension_n"] = 0.0
        actuator["slack_estimate"] = True
        add_actuator_fault(actuator, "tension_dropout_injected")
    packet["contact"]["adjust_needed_now"] = True
    packet["contact"]["hold_safe_now"] = False
    add_safety_fault(packet, "tension_dropout_injected")


def inject_driver_fault(packet: dict[str, Any]) -> None:
    add_safety_fault(packet, "driver_fault_injected")


def inject_estop(packet: dict[str, Any]) -> None:
    packet["safety"]["e_stop"] = True
    packet["safety"]["abort_required"] = True
    add_safety_fault(packet, "e_stop_injected")


def make_replay_packet(
    source: dict[str, Any],
    *,
    slot: int,
    timestamp_ns: int,
    args: argparse.Namespace,
    previous_positions: dict[str, float],
) -> tuple[dict[str, Any], set[str]]:
    packet = copy.deepcopy(source)
    packet["source"] = "bench_replay"
    packet["sequence_id"] = int(slot)
    packet["control_tick"] = int(slot)
    packet["timestamp_ns"] = int(timestamp_ns)
    packet["sample_rate_hz"] = float(args.sample_rate_hz)
    packet["safety"]["current_limit_a"] = float(args.current_limit_a)
    injected: set[str] = set()

    if slot > 0 and int(args.current_saturation_every) > 0 and slot % int(args.current_saturation_every) == 0:
        inject_current_saturation(packet, args)
        injected.add("current_saturation")
    if slot > 0 and int(args.encoder_freeze_every) > 0 and slot % int(args.encoder_freeze_every) == 0:
        inject_encoder_freeze(packet, previous_positions)
        injected.add("encoder_freeze")
    if slot > 0 and int(args.bus_sag_every) > 0 and slot % int(args.bus_sag_every) == 0:
        inject_bus_voltage_sag(packet, args)
        injected.add("bus_voltage_sag")
    if slot > 0 and int(args.tension_dropout_every) > 0 and slot % int(args.tension_dropout_every) == 0:
        inject_tension_dropout(packet)
        injected.add("tension_dropout")
    if slot > 0 and int(args.driver_fault_every) > 0 and slot % int(args.driver_fault_every) == 0:
        inject_driver_fault(packet)
        injected.add("driver_fault")
    if int(args.e_stop_at) >= 0 and slot == int(args.e_stop_at):
        inject_estop(packet)
        injected.add("e_stop")

    for actuator in packet["actuators"]:
        previous_positions[str(actuator.get("actuator_id", ""))] = as_float(actuator.get("encoder_position_rad"))
    return packet, injected


def fault_flags(packet: dict[str, Any]) -> set[str]:
    flags = set(str(flag) for flag in packet["safety"].get("fault_flags", []))
    for actuator in packet.get("actuators", []):
        flags.update(str(flag) for flag in actuator.get("fault_flags", []))
    return flags


def detect_packet_faults(packet: dict[str, Any], args: argparse.Namespace) -> set[str]:
    flags = fault_flags(packet)
    detected: set[str] = set()
    if any(actuator.get("current_saturated", False) for actuator in packet["actuators"]):
        detected.add("current_saturation")
    if packet["active_pair"].get("saturation_count", 0) > 0:
        detected.add("current_saturation")
    if "current_saturation_injected" in flags:
        detected.add("current_saturation")
    if "encoder_freeze_injected" in flags:
        detected.add("encoder_freeze")
    if any(as_float(actuator.get("bus_voltage_v")) < float(args.nominal_bus_voltage_v) * 0.85 for actuator in packet["actuators"]):
        detected.add("bus_voltage_sag")
    if "bus_voltage_sag_injected" in flags:
        detected.add("bus_voltage_sag")
    if "tension_dropout_injected" in flags:
        detected.add("tension_dropout")
    if "driver_fault_injected" in flags:
        detected.add("driver_fault")
    if bool(packet["safety"].get("e_stop", False)) or "e_stop_injected" in flags:
        detected.add("e_stop")
    return detected


def validate_packets(schema_path: Path, packets: list[dict[str, Any]]) -> tuple[bool, str]:
    try:
        import jsonschema
    except ImportError as exc:
        return False, f"jsonschema is not installed: {exc}"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for idx, packet in enumerate(packets):
        errors = sorted(validator.iter_errors(packet), key=lambda err: err.path)
        if errors:
            first = errors[0]
            return False, f"packet {idx} schema error at {list(first.path)}: {first.message}"
    return True, "schema validation OK"


def replay_packets(source_packets: list[dict[str, Any]], args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    expected_step_ns = int(round(1_000_000_000.0 / float(args.sample_rate_hz)))
    cumulative_delay_ns = 0
    previous_positions: dict[str, float] = {}
    injected_counts = Counter({fault: 0 for fault in FAULT_TYPES})
    injected_by_sequence: dict[int, list[str]] = {}

    for slot in range(max(1, int(args.source_slots))):
        if slot > 0 and int(args.drop_every) > 0 and slot % int(args.drop_every) == 0:
            injected_counts["drop_packet"] += 1
            injected_by_sequence[slot] = ["drop_packet"]
            continue
        if slot > 0 and int(args.delay_every) > 0 and slot % int(args.delay_every) == 0:
            cumulative_delay_ns += int(round(float(args.delay_extra_ms) * 1_000_000.0))
        timestamp_ns = int(slot * expected_step_ns + cumulative_delay_ns)
        source = source_packets[slot % len(source_packets)]
        packet, injected = make_replay_packet(
            source,
            slot=slot,
            timestamp_ns=timestamp_ns,
            args=args,
            previous_positions=previous_positions,
        )
        if slot > 0 and int(args.delay_every) > 0 and slot % int(args.delay_every) == 0:
            injected.add("delay_spike")
        for fault in injected:
            injected_counts[fault] += 1
        if injected:
            injected_by_sequence[slot] = sorted(injected)
        packets.append(packet)

    return packets, {
        "expected_step_ns": expected_step_ns,
        "injected_counts": dict(injected_counts),
        "injected_by_sequence": {str(k): v for k, v in injected_by_sequence.items()},
    }


def analyze_replay(
    packets: list[dict[str, Any]],
    replay_info: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    sequences = [int(packet["sequence_id"]) for packet in packets]
    timestamps = [int(packet["timestamp_ns"]) for packet in packets]
    dropped_detected = sum(max(0, b - a - 1) for a, b in zip(sequences, sequences[1:]))
    timestamp_monotonic = all(b > a for a, b in zip(timestamps, timestamps[1:]))
    expected_step_ns = int(replay_info["expected_step_ns"])
    normalized_intervals = []
    delay_detected = 0
    for prev, curr in zip(packets, packets[1:]):
        seq_delta = max(1, int(curr["sequence_id"]) - int(prev["sequence_id"]))
        interval = int(curr["timestamp_ns"]) - int(prev["timestamp_ns"])
        normalized = interval / seq_delta
        normalized_intervals.append(normalized)
        if normalized > expected_step_ns * (1.0 + float(args.delay_detect_ratio)):
            delay_detected += 1

    detected_counts = Counter({fault: 0 for fault in FAULT_TYPES})
    detected_counts["drop_packet"] = int(dropped_detected)
    detected_counts["delay_spike"] = int(delay_detected)
    for packet in packets:
        for fault in detect_packet_faults(packet, args):
            detected_counts[fault] += 1

    injected_counts = {fault: int(replay_info["injected_counts"].get(fault, 0)) for fault in FAULT_TYPES}
    detection_rates = {}
    for fault in FAULT_TYPES:
        injected = int(injected_counts.get(fault, 0))
        detected = int(detected_counts.get(fault, 0))
        detection_rates[fault] = float(detected / injected) if injected > 0 else 1.0

    median_step_ns = statistics.median(normalized_intervals) if normalized_intervals else float(expected_step_ns)
    observed_rate_hz = 1_000_000_000.0 / max(float(median_step_ns), 1.0)
    rate_error_fraction = abs(observed_rate_hz - float(args.sample_rate_hz)) / max(float(args.sample_rate_hz), 1e-9)

    phases = Counter(str(packet.get("phase_id", "unknown")) for packet in packets)
    fault_active_packets = sum(1 for packet in packets if bool(packet["safety"].get("fault_active", False)))
    return {
        "source_slots": int(args.source_slots),
        "emitted_packets": int(len(packets)),
        "schema_packets_expected_min": int(args.min_emitted_packets),
        "sequence_start": int(sequences[0]) if sequences else 0,
        "sequence_end": int(sequences[-1]) if sequences else 0,
        "dropped_sequence_ids_detected": int(dropped_detected),
        "timestamp_monotonic": bool(timestamp_monotonic),
        "target_sample_rate_hz": float(args.sample_rate_hz),
        "observed_sample_rate_hz": float(observed_rate_hz),
        "rate_error_fraction": float(rate_error_fraction),
        "median_step_ns": float(median_step_ns),
        "expected_step_ns": int(expected_step_ns),
        "phase_counts": dict(phases),
        "fault_active_packets": int(fault_active_packets),
        "injected_fault_counts": injected_counts,
        "detected_fault_counts": {fault: int(detected_counts.get(fault, 0)) for fault in FAULT_TYPES},
        "fault_detection_rates": detection_rates,
        "gate": {
            "packet_count_ok": bool(len(packets) >= int(args.min_emitted_packets)),
            "timestamp_monotonic_ok": bool(timestamp_monotonic),
            "drop_count_ok": bool(dropped_detected == injected_counts["drop_packet"]),
            "sample_rate_ok": bool(rate_error_fraction <= float(args.max_rate_error_fraction)),
            "fault_detection_ok": bool(
                all(detection_rates[fault] >= float(args.min_fault_detection_rate) for fault in FAULT_TYPES)
            ),
        },
    }


def write_jsonl(path: Path, packets: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for packet in packets:
            f.write(json.dumps(json_ready(packet), ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, packets: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "sequence_id",
        "timestamp_ns",
        "phase_id",
        "fault_active",
        "fault_flags",
        "e_stop",
        "abort_required",
        "active_pair_total_tension_n",
        "active_pair_balance_ratio",
        "active_pair_max_abs_iq_a",
        "active_pair_saturation_count",
        "min_bus_voltage_v",
        "max_abs_iq_a",
        "contact_present",
        "lift_quality_now",
        "adjust_needed_now",
        "hold_safe_now",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for packet in packets:
            actuators = packet["actuators"]
            flags = sorted(fault_flags(packet))
            writer.writerow(
                {
                    "sequence_id": packet["sequence_id"],
                    "timestamp_ns": packet["timestamp_ns"],
                    "phase_id": packet["phase_id"],
                    "fault_active": packet["safety"]["fault_active"],
                    "fault_flags": ";".join(flags),
                    "e_stop": packet["safety"]["e_stop"],
                    "abort_required": packet["safety"]["abort_required"],
                    "active_pair_total_tension_n": packet["active_pair"]["total_tension_n"],
                    "active_pair_balance_ratio": packet["active_pair"]["balance_ratio"],
                    "active_pair_max_abs_iq_a": packet["active_pair"]["max_abs_iq_a"],
                    "active_pair_saturation_count": packet["active_pair"]["saturation_count"],
                    "min_bus_voltage_v": min([as_float(row.get("bus_voltage_v")) for row in actuators] + [0.0]),
                    "max_abs_iq_a": max([abs(as_float(row.get("iq_measured_a"))) for row in actuators] + [0.0]),
                    "contact_present": packet["contact"]["contact_present"],
                    "lift_quality_now": packet["contact"]["lift_quality_now"],
                    "adjust_needed_now": packet["contact"]["adjust_needed_now"],
                    "hold_safe_now": packet["contact"]["hold_safe_now"],
                }
            )


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    gate = s["gate"]
    lines = [
        "# Stage4 Fake Bench Replay v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- Fake bench/logger replay only.\n",
        "- Input is F1 MuJoCo force-feedback packet data.\n",
        "- Output source is `bench_replay`, not real hardware.\n",
        "- No motor, sensor, or controller hardware runtime is claimed.\n\n",
        "## Outputs\n\n",
        f"- Input JSONL: `{payload['input_jsonl']}`\n",
        f"- Replay JSONL: `{payload['outputs']['jsonl']}`\n",
        f"- CSV summary: `{payload['outputs']['csv']}`\n",
        f"- Metadata: `{payload['outputs']['metadata']}`\n\n",
        "## Summary\n\n",
        f"- Source slots: `{s['source_slots']}`\n",
        f"- Emitted packets: `{s['emitted_packets']}`\n",
        f"- Sequence range: `{s['sequence_start']}..{s['sequence_end']}`\n",
        f"- Dropped sequence IDs detected: `{s['dropped_sequence_ids_detected']}`\n",
        f"- Timestamp monotonic: `{s['timestamp_monotonic']}`\n",
        f"- Target / observed sample rate: `{s['target_sample_rate_hz']:.3f}` / "
        f"`{s['observed_sample_rate_hz']:.3f} Hz`\n",
        f"- Rate error fraction: `{s['rate_error_fraction']:.6f}`\n",
        f"- Fault-active packets: `{s['fault_active_packets']}`\n",
        f"- Phase counts: `{s['phase_counts']}`\n",
        f"- Schema validation: `{payload['validation']['message']}`\n\n",
        "## Fault Injection\n\n",
        "| fault | injected | detected | detection rate |\n",
        "|---|---:|---:|---:|\n",
    ]
    for fault in FAULT_TYPES:
        lines.append(
            f"| `{fault}` | {s['injected_fault_counts'][fault]} | "
            f"{s['detected_fault_counts'][fault]} | {s['fault_detection_rates'][fault]:.3f} |\n"
        )
    lines.extend(
        [
            "\n## Gate F2\n\n",
            f"- Packet count >= `{s['schema_packets_expected_min']}`: `{gate['packet_count_ok']}`\n",
            f"- Timestamp monotonic: `{gate['timestamp_monotonic_ok']}`\n",
            f"- Dropped sequence IDs counted correctly: `{gate['drop_count_ok']}`\n",
            f"- Sample-rate median stable: `{gate['sample_rate_ok']}`\n",
            f"- Fault detection: `{gate['fault_detection_ok']}`\n\n",
            "F2 passes only if every item above is `True` and schema validation is OK.\n\n",
            "## Next\n\n",
            "- F3 signal coverage / calibration matrix.\n",
            "- Keep residual-policy reopening closed until F0/F1/F2/F3 are all documented.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay Stage4 packets as a fake hardware bench logger.")
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--source-slots", type=int, default=1200)
    parser.add_argument("--min-emitted-packets", type=int, default=1000)
    parser.add_argument("--sample-rate-hz", type=float, default=200.0)
    parser.add_argument("--current-limit-a", type=float, default=4.0)
    parser.add_argument("--nominal-bus-voltage-v", type=float, default=24.0)
    parser.add_argument("--bus-sag-fraction", type=float, default=0.62)
    parser.add_argument("--drop-every", type=int, default=97)
    parser.add_argument("--delay-every", type=int, default=83)
    parser.add_argument("--delay-extra-ms", type=float, default=12.0)
    parser.add_argument("--delay-detect-ratio", type=float, default=0.60)
    parser.add_argument("--current-saturation-every", type=int, default=149)
    parser.add_argument("--saturate-actuator-count", type=int, default=2)
    parser.add_argument("--encoder-freeze-every", type=int, default=173)
    parser.add_argument("--bus-sag-every", type=int, default=211)
    parser.add_argument("--tension-dropout-every", type=int, default=193)
    parser.add_argument("--driver-fault-every", type=int, default=127)
    parser.add_argument("--e-stop-at", type=int, default=1000)
    parser.add_argument("--max-rate-error-fraction", type=float, default=0.02)
    parser.add_argument("--min-fault-detection-rate", type=float, default=1.0)
    parser.add_argument("--validate-schema", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_packets = load_jsonl(Path(args.input_jsonl))
    packets, replay_info = replay_packets(source_packets, args)
    validation_ok = True
    validation_message = "schema validation skipped"
    if bool(args.validate_schema):
        validation_ok, validation_message = validate_packets(Path(args.schema), packets)
        if not validation_ok:
            raise RuntimeError(validation_message)

    summary = analyze_replay(packets, replay_info, args)
    summary["gate"]["schema_ok"] = bool(validation_ok)
    summary["gate"]["f2_pass"] = bool(validation_ok and all(summary["gate"].values()))
    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage4.0-F2",
        "status": "stage4_fake_bench_replay_v0",
        "input_jsonl": str(Path(args.input_jsonl).resolve()),
        "schema": str(Path(args.schema).resolve()),
        "outputs": {
            "jsonl": str(Path(args.jsonl).resolve()),
            "csv": str(Path(args.csv).resolve()),
            "metadata": str(Path(args.metadata).resolve()),
            "report": str(Path(args.report).resolve()),
        },
        "args": vars(args),
        "summary": summary,
        "injected_by_sequence": replay_info["injected_by_sequence"],
        "validation": {
            "schema_checked": bool(args.validate_schema),
            "ok": bool(validation_ok),
            "message": validation_message,
        },
        "boundary": {
            "source_packets_are_mujoco": True,
            "output_is_fake_bench_replay": True,
            "hardware_runtime": False,
            "real_motor": False,
            "real_encoder": False,
            "real_tactile": False,
            "direct_force_control_promoted": False,
        },
    }
    write_jsonl(Path(args.jsonl), packets)
    write_csv(Path(args.csv), packets)
    Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metadata).write_text(json.dumps(json_ready(metadata), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(
        Path(args.report),
        {
            "generated_at": metadata["generated_at"],
            "input_jsonl": metadata["input_jsonl"],
            "outputs": metadata["outputs"],
            "summary": summary,
            "validation": metadata["validation"],
        },
    )
    print(f"wrote {len(packets)} bench replay packets -> {Path(args.jsonl).resolve()}")
    print(validation_message)
    print(f"F2 pass: {summary['gate']['f2_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
