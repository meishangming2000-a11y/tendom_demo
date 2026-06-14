#!/usr/bin/env python3
"""Motor force-feedback proxy for MuJoCo Stage3 experiments.

The real hand will not measure fingertip force from the motor directly. A motor
drive usually exposes current, encoder state, estimated torque, limits, and
faults. This helper turns MuJoCo actuator force into that driver-side signal
surface so Stage3 controllers can start using force-like feedback without
claiming hardware integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MotorForceFeedbackConfig:
    torque_constant_nm_per_a: float = 0.035
    gear_ratio: float = 30.0
    gear_efficiency: float = 0.72
    spool_radius_m: float = 0.008
    current_limit_a: float = 4.0
    bus_voltage_v: float = 24.0
    current_noise_a: float = 0.025
    seed: int = 20260611


def _name_for(model, mujoco, obj_type, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, obj_type, int(idx)) or fallback


class MujocoMotorForceFeedbackSensor:
    """Convert MuJoCo actuator load into motor-driver force-feedback signals."""

    def __init__(self, config: MotorForceFeedbackConfig | None = None) -> None:
        self.config = config or MotorForceFeedbackConfig()
        self._rng = np.random.default_rng(self.config.seed)

    def observe(self, model, data, mujoco, *, phase: str = "", active_pair: tuple[str, str] | None = None) -> dict[str, Any]:
        actuators = []
        max_abs_iq = 0.0
        max_abs_output_torque = 0.0
        max_tendon_tension = 0.0
        max_bus_current = 0.0
        max_hand_abs_iq = 0.0
        max_hand_tendon_tension = 0.0
        saturated = 0

        for act_id in range(model.nu):
            row = self._actuator_feedback(model, data, mujoco, act_id)
            actuators.append(row)
            max_abs_iq = max(max_abs_iq, abs(float(row["iq_measured_a"])))
            max_abs_output_torque = max(max_abs_output_torque, abs(float(row["output_torque_nm"])))
            max_tendon_tension = max(max_tendon_tension, float(row["tendon_tension_n"]))
            max_bus_current = max(max_bus_current, float(row["bus_current_a"]))
            if bool(row["is_hand_actuator"]):
                max_hand_abs_iq = max(max_hand_abs_iq, abs(float(row["iq_measured_a"])))
                max_hand_tendon_tension = max(max_hand_tendon_tension, float(row["tendon_tension_n"]))
            saturated += int(bool(row["current_saturated"]))

        top = sorted(actuators, key=lambda row: float(row["tendon_tension_n"]), reverse=True)[:6]
        top_hand = sorted(
            [row for row in actuators if bool(row["is_hand_actuator"])],
            key=lambda row: float(row["tendon_tension_n"]),
            reverse=True,
        )[:6]
        group_summaries = _summarize_groups(actuators)
        active_pair_summary = _summarize_active_pair(group_summaries, active_pair)
        return {
            "phase": phase,
            "actuator_count": int(len(actuators)),
            "max_abs_iq_a": float(max_abs_iq),
            "max_abs_output_torque_nm": float(max_abs_output_torque),
            "max_tendon_tension_n": float(max_tendon_tension),
            "max_bus_current_a": float(max_bus_current),
            "max_hand_abs_iq_a": float(max_hand_abs_iq),
            "max_hand_tendon_tension_n": float(max_hand_tendon_tension),
            "saturated_actuator_count": int(saturated),
            "top_actuators_by_tension": top,
            "top_hand_actuators_by_tension": top_hand,
            "group_summaries": group_summaries,
            "active_pair": active_pair_summary,
        }

    def _actuator_feedback(self, model, data, mujoco, act_id: int) -> dict[str, Any]:
        cfg = self.config
        name = _name_for(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR, act_id, f"actuator_{act_id}")
        output_torque = float(data.actuator_force[act_id]) if hasattr(data, "actuator_force") else 0.0
        output_torque_abs = abs(output_torque)
        motor_torque = output_torque / max(cfg.gear_ratio * cfg.gear_efficiency, 1e-9)
        iq_cmd = motor_torque / max(cfg.torque_constant_nm_per_a, 1e-9)
        iq_limited = float(np.clip(iq_cmd, -cfg.current_limit_a, cfg.current_limit_a))
        iq_measured = iq_limited + float(self._rng.normal(0.0, max(0.0, cfg.current_noise_a)))
        current_saturated = abs(iq_cmd) > cfg.current_limit_a
        tendon_tension = output_torque_abs / max(cfg.spool_radius_m, 1e-9)
        bus_current = min(
            max(0.0, abs(iq_measured)) * 0.35 + output_torque_abs * 0.02 / max(cfg.bus_voltage_v, 1e-9),
            cfg.current_limit_a * 1.4,
        )

        joint_name = ""
        joint_position = 0.0
        joint_velocity = 0.0
        motor_position = 0.0
        motor_velocity = 0.0
        joint_id = int(model.actuator_trnid[act_id, 0]) if hasattr(model, "actuator_trnid") else -1
        if 0 <= joint_id < model.njnt:
            joint_name = _name_for(model, mujoco, mujoco.mjtObj.mjOBJ_JOINT, joint_id, f"joint_{joint_id}")
            qadr = int(model.jnt_qposadr[joint_id])
            dadr = int(model.jnt_dofadr[joint_id])
            joint_position = float(data.qpos[qadr])
            joint_velocity = float(data.qvel[dadr])
            motor_position = joint_position * cfg.gear_ratio
            motor_velocity = joint_velocity * cfg.gear_ratio
        actuator_group = _actuator_group(f"{name} {joint_name}".lower())

        return {
            "actuator": name,
            "joint": joint_name,
            "group": actuator_group,
            "is_hand_actuator": bool(actuator_group in {"thumb", "index", "middle", "ring", "little"}),
            "output_torque_nm": float(output_torque),
            "motor_torque_nm": float(motor_torque),
            "iq_cmd_a": float(iq_cmd),
            "iq_measured_a": float(iq_measured),
            "bus_current_a": float(bus_current),
            "current_saturated": bool(current_saturated),
            "encoder_position_rad": float(motor_position),
            "encoder_velocity_rad_s": float(motor_velocity),
            "joint_position_rad": float(joint_position),
            "joint_velocity_rad_s": float(joint_velocity),
            "tendon_tension_n": float(tendon_tension),
        }


def _actuator_group(joined_name: str) -> str:
    for group in ("thumb", "index", "middle", "ring", "little"):
        if group in joined_name:
            return group
    if "wrist" in joined_name:
        return "wrist"
    if joined_name.startswith("a_j") or " j1" in joined_name or " j2" in joined_name or " j3" in joined_name or " j4" in joined_name:
        return "arm"
    return "other"


def _summarize_groups(actuators: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in actuators:
        groups.setdefault(str(row.get("group", "other")), []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for group, rows in groups.items():
        tensions = [float(row.get("tendon_tension_n", 0.0)) for row in rows]
        abs_iq = [abs(float(row.get("iq_measured_a", 0.0))) for row in rows]
        abs_torque = [abs(float(row.get("output_torque_nm", 0.0))) for row in rows]
        top = max(rows, key=lambda row: float(row.get("tendon_tension_n", 0.0))) if rows else {}
        out[group] = {
            "actuator_count": int(len(rows)),
            "sum_tendon_tension_n": float(np.sum(tensions)) if tensions else 0.0,
            "max_tendon_tension_n": float(max(tensions)) if tensions else 0.0,
            "mean_tendon_tension_n": float(np.mean(tensions)) if tensions else 0.0,
            "max_abs_iq_a": float(max(abs_iq)) if abs_iq else 0.0,
            "sum_abs_iq_a": float(np.sum(abs_iq)) if abs_iq else 0.0,
            "max_abs_output_torque_nm": float(max(abs_torque)) if abs_torque else 0.0,
            "saturated_actuator_count": int(sum(1 for row in rows if bool(row.get("current_saturated", False)))),
            "top_actuator": top,
        }
    return out


def _summarize_active_pair(
    group_summaries: dict[str, dict[str, Any]],
    active_pair: tuple[str, str] | None,
) -> dict[str, Any]:
    if not active_pair:
        return {"configured": False}
    groups = [str(group).lower() for group in active_pair]
    per_group = {group: group_summaries.get(group, {}) for group in groups}
    tensions = [float(per_group[group].get("sum_tendon_tension_n", 0.0)) for group in groups]
    max_group_tension = max(tensions) if tensions else 0.0
    min_group_tension = min(tensions) if tensions else 0.0
    balance = min_group_tension / max(max_group_tension, 1e-9)
    return {
        "configured": True,
        "groups": groups,
        "per_group": per_group,
        "total_tendon_tension_n": float(np.sum(tensions)),
        "max_group_tendon_tension_n": float(max_group_tension),
        "min_group_tendon_tension_n": float(min_group_tension),
        "balance_ratio": float(balance),
        "tension_delta_abs_n": float(abs(max_group_tension - min_group_tension)),
        "max_abs_iq_a": float(max([float(per_group[group].get("max_abs_iq_a", 0.0)) for group in groups] + [0.0])),
        "sum_abs_iq_a": float(np.sum([float(per_group[group].get("sum_abs_iq_a", 0.0)) for group in groups])),
        "saturated_actuator_count": int(
            sum(int(per_group[group].get("saturated_actuator_count", 0)) for group in groups)
        ),
    }


def summarize_motor_force_feedback_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        return {"samples": 0}
    top_by_actuator: dict[str, dict[str, Any]] = {}
    top_hand_by_actuator: dict[str, dict[str, Any]] = {}
    for sample in samples:
        for row in sample.get("top_actuators_by_tension", []):
            name = str(row.get("actuator", ""))
            if not name:
                continue
            prev = top_by_actuator.get(name)
            if prev is None or float(row.get("tendon_tension_n", 0.0)) > float(prev.get("tendon_tension_n", 0.0)):
                top_by_actuator[name] = row
        for row in sample.get("top_hand_actuators_by_tension", []):
            name = str(row.get("actuator", ""))
            if not name:
                continue
            prev = top_hand_by_actuator.get(name)
            if prev is None or float(row.get("tendon_tension_n", 0.0)) > float(prev.get("tendon_tension_n", 0.0)):
                top_hand_by_actuator[name] = row
    phase_summaries: dict[str, dict[str, Any]] = {}
    for phase in sorted({str(sample.get("phase", "")) for sample in samples}):
        subset = [sample for sample in samples if str(sample.get("phase", "")) == phase]
        pair_subset = [sample.get("active_pair", {}) for sample in subset if sample.get("active_pair", {}).get("configured")]
        pair_tensions = [float(row.get("total_tendon_tension_n", 0.0)) for row in pair_subset]
        pair_balances = [float(row.get("balance_ratio", 0.0)) for row in pair_subset]
        pair_iq = [float(row.get("max_abs_iq_a", 0.0)) for row in pair_subset]
        pair_tension_delta_mean = (
            float(np.mean([abs(pair_tensions[idx] - pair_tensions[idx - 1]) for idx in range(1, len(pair_tensions))]))
            if len(pair_tensions) > 1
            else 0.0
        )
        phase_summaries[phase] = {
            "samples": int(len(subset)),
            "max_hand_abs_iq_a": float(max(float(s.get("max_hand_abs_iq_a", 0.0)) for s in subset)),
            "mean_hand_abs_iq_a": float(np.mean([float(s.get("max_hand_abs_iq_a", 0.0)) for s in subset])),
            "max_hand_tendon_tension_n": float(max(float(s.get("max_hand_tendon_tension_n", 0.0)) for s in subset)),
            "mean_hand_tendon_tension_n": float(
                np.mean([float(s.get("max_hand_tendon_tension_n", 0.0)) for s in subset])
            ),
            "pair_samples": int(len(pair_subset)),
            "pair_total_tension_mean_n": float(np.mean(pair_tensions)) if pair_tensions else 0.0,
            "pair_total_tension_min_n": float(min(pair_tensions)) if pair_tensions else 0.0,
            "pair_total_tension_max_n": float(max(pair_tensions)) if pair_tensions else 0.0,
            "pair_balance_mean": float(np.mean(pair_balances)) if pair_balances else 0.0,
            "pair_balance_min": float(min(pair_balances)) if pair_balances else 0.0,
            "pair_max_abs_iq_mean_a": float(np.mean(pair_iq)) if pair_iq else 0.0,
            "pair_max_abs_iq_max_a": float(max(pair_iq)) if pair_iq else 0.0,
            "pair_tension_delta_mean_abs_n": pair_tension_delta_mean,
            "pair_saturation_fraction": float(
                np.mean([int(float(row.get("saturated_actuator_count", 0)) > 0) for row in pair_subset])
            )
            if pair_subset
            else 0.0,
        }
    active_pair_samples = [sample.get("active_pair", {}) for sample in samples if sample.get("active_pair", {}).get("configured")]
    active_pair_tensions = [float(row.get("total_tendon_tension_n", 0.0)) for row in active_pair_samples]
    active_pair_balances = [float(row.get("balance_ratio", 0.0)) for row in active_pair_samples]
    return {
        "samples": int(len(samples)),
        "max_abs_iq_a": float(max(float(s.get("max_abs_iq_a", 0.0)) for s in samples)),
        "mean_abs_iq_a": float(np.mean([float(s.get("max_abs_iq_a", 0.0)) for s in samples])),
        "max_abs_output_torque_nm": float(max(float(s.get("max_abs_output_torque_nm", 0.0)) for s in samples)),
        "max_tendon_tension_n": float(max(float(s.get("max_tendon_tension_n", 0.0)) for s in samples)),
        "max_bus_current_a": float(max(float(s.get("max_bus_current_a", 0.0)) for s in samples)),
        "max_hand_abs_iq_a": float(max(float(s.get("max_hand_abs_iq_a", 0.0)) for s in samples)),
        "mean_hand_abs_iq_a": float(np.mean([float(s.get("max_hand_abs_iq_a", 0.0)) for s in samples])),
        "max_hand_tendon_tension_n": float(max(float(s.get("max_hand_tendon_tension_n", 0.0)) for s in samples)),
        "active_pair_samples": int(len(active_pair_samples)),
        "active_pair_total_tension_mean_n": float(np.mean(active_pair_tensions)) if active_pair_tensions else 0.0,
        "active_pair_total_tension_max_n": float(max(active_pair_tensions)) if active_pair_tensions else 0.0,
        "active_pair_balance_mean": float(np.mean(active_pair_balances)) if active_pair_balances else 0.0,
        "active_pair_balance_min": float(min(active_pair_balances)) if active_pair_balances else 0.0,
        "saturation_sample_fraction": float(
            np.mean([int(float(s.get("saturated_actuator_count", 0)) > 0) for s in samples])
        ),
        "top_actuators_by_tension": sorted(
            top_by_actuator.values(),
            key=lambda row: float(row.get("tendon_tension_n", 0.0)),
            reverse=True,
        )[:8],
        "top_hand_actuators_by_tension": sorted(
            top_hand_by_actuator.values(),
            key=lambda row: float(row.get("tendon_tension_n", 0.0)),
            reverse=True,
        )[:8],
        "phase_summaries": phase_summaries,
    }
