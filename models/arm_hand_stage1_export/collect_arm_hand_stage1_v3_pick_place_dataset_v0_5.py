#!/usr/bin/env python3
"""Collect the first fixed-target pick-place dataset for Stage2 v0.5.

Rows keep `actions` as the behavior actually applied in MuJoCo and
`expert_actions` as the clean scripted target for later BC training. The
observation vector is the base arm-hand observation plus target-center and
ball-to-target features. Phase ids remain separate so training can append
phase features explicitly.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

import demo_arm_hand_lift_ball_scripted as lift_base
from arm_hand_stage1_task_api import ArmHandStage1TaskAPI, json_ready
from arm_hand_stage1_v3_pick_place_task_api import (
    CURRENT_PICK_PLACE_SCENE,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_CENTER,
    DEFAULT_TARGET_RADIUS_M,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
    build_contract,
    evaluate_pick_place_state,
)
from demo_arm_hand_stage1_v3_pick_place_scripted import DESCEND_ARM, RETREAT_ARM, TRANSPORT_ARM, is_stable_on_target
from demo_arm_hand_stage1_v3_pick_place_target_conditioned import conditioned_arm_targets
from collect_arm_hand_stage1_v2_dataset_v0 import concatenate_rows, reason_code


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
RUNS = ROOT / "runs"

DATASET_VERSION = "v0.5"
DEFAULT_DATASET_NAME = "arm_hand_stage1_v3_pick_place_dataset_v0_5.npz"
DEFAULT_DATASET = DATA / DEFAULT_DATASET_NAME
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_dataset_v0_5_report.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_dataset_v0_5.json"


def version_tag(version: str) -> str:
    return str(version).replace(".", "_").replace("-", "_")


@dataclass(frozen=True)
class PickPlaceProfile:
    name: str
    timing_scale: float
    action_noise_abs: float
    action_lag: float
    seed_offset: int


PROFILES = [
    PickPlaceProfile("clean_nominal", 1.0, 0.0, 0.0, 0),
    PickPlaceProfile("timing_fast_clean", 0.96, 0.0, 0.0, 1000),
    PickPlaceProfile("timing_slow_clean", 1.04, 0.0, 0.0, 2000),
]


def terminal_reason_table() -> list[str]:
    return [
        "running",
        "success_pick_place_ball",
        "non_finite_state",
        "excessive_penetration",
        "transport_drop_before_release",
        "target_miss",
        "release_contact_remaining",
        "placement_not_stable",
        "timeout",
    ]


def parse_profiles(raw: str) -> list[PickPlaceProfile]:
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    by_name = {profile.name: profile for profile in PROFILES}
    missing = [name for name in requested if name not in by_name]
    if missing:
        raise ValueError(f"Unknown profiles {missing}; available={sorted(by_name)}")
    return [by_name[name] for name in requested]


def parse_values(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def parse_target_centers(raw: str) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        values = parse_values(chunk)
        if len(values) not in {3, 4, 5}:
            raise ValueError(f"target center must contain x,y,z[,pre_release_z_drop[,hover_z_lift]]; got {chunk!r}")
        spec = {"target_center": np.asarray(values[:3], dtype=np.float64)}
        if len(values) >= 4:
            spec["pre_release_z_drop"] = float(values[3])
        if len(values) == 5:
            spec["hover_z_lift"] = float(values[4])
        specs.append(spec)
    if not specs:
        raise ValueError("--target-centers was provided but no valid centers were parsed")
    return specs


def build_target_centers(args) -> list[dict[str, Any]]:
    base = np.asarray(args.target_center, dtype=np.float64)
    if getattr(args, "target_centers", ""):
        return [
            {
                "target_id": int(target_id),
                "target_offset": spec["target_center"] - base,
                "target_center": spec["target_center"],
                "pre_release_z_drop": float(spec.get("pre_release_z_drop", args.pre_release_z_drop)),
                "hover_z_lift": float(spec.get("hover_z_lift", args.hover_z_lift)),
            }
            for target_id, spec in enumerate(parse_target_centers(args.target_centers))
        ]

    rows = []
    episode_target_id = 0
    for dx in parse_values(args.x_offsets):
        for dy in parse_values(args.y_offsets):
            offset = np.array([dx, dy, 0.0], dtype=np.float64)
            rows.append(
                {
                    "target_id": int(episode_target_id),
                    "target_offset": offset,
                    "target_center": base + offset,
                    "pre_release_z_drop": float(args.pre_release_z_drop),
                    "hover_z_lift": float(args.hover_z_lift),
                }
            )
            episode_target_id += 1
    return rows


def clip_action(api: ArmHandStage1TaskAPI, action: np.ndarray) -> np.ndarray:
    clipped = np.asarray(action, dtype=np.float64).copy()
    for aid in range(api.model.nu):
        if bool(api.model.actuator_ctrllimited[aid]):
            low, high = api.model.actuator_ctrlrange[aid]
            clipped[aid] = np.clip(clipped[aid], low, high)
    return clipped


def make_behavior_action(
    api: ArmHandStage1TaskAPI,
    expert_action: np.ndarray,
    previous_behavior_action: np.ndarray | None,
    rng: np.random.Generator,
    profile: PickPlaceProfile,
) -> np.ndarray:
    behavior = np.asarray(expert_action, dtype=np.float64).copy()
    if previous_behavior_action is not None and profile.action_lag > 0.0:
        lag = float(np.clip(profile.action_lag, 0.0, 0.95))
        behavior = (1.0 - lag) * behavior + lag * previous_behavior_action
    if profile.action_noise_abs > 0.0:
        behavior = behavior + rng.normal(0.0, profile.action_noise_abs, size=behavior.shape)
    return clip_action(api, behavior)


def scaled_steps(args, profile: PickPlaceProfile, name: str) -> int:
    return max(1, int(round(float(getattr(args, name)) * profile.timing_scale)))


def phase_id_table(phases: list[tuple[str, dict[str, float], dict[str, float], int]]) -> list[str]:
    return [name for name, _, _, _ in phases]


def build_pick_place_phases(
    default_targets: dict[str, float],
    args,
    profile: PickPlaceProfile,
    api: ArmHandStage1TaskAPI | None = None,
    target_center: np.ndarray | None = None,
    pre_release_z_drop: float | None = None,
    hover_z_lift: float | None = None,
) -> list[tuple[str, dict[str, float], dict[str, float], int]]:
    pre_approach = {**default_targets, **lift_base.ARM_PRE_APPROACH}
    approach = {**default_targets, **lift_base.ARM_APPROACH}
    preshape = {**approach, **lift_base.PRESHAPE_TARGETS}
    close_fingers = {**approach, **lift_base.LONG_FINGER_TARGETS}
    close_thumb = {**close_fingers, **lift_base.THUMB_SMOKE_TARGETS}
    lift = {**close_thumb, **lift_base.ARM_LIFT}
    if bool(getattr(args, "target_conditioned", False)):
        if api is None or target_center is None:
            raise ValueError("target-conditioned collection requires api and target_center")
        arm = conditioned_arm_targets(
            api.model,
            api.mujoco,
            np.asarray(target_center, dtype=np.float64),
            pre_release_z_drop=float(
                getattr(args, "pre_release_z_drop", 0.02) if pre_release_z_drop is None else pre_release_z_drop
            ),
            hover_z_lift=float(getattr(args, "hover_z_lift", 0.0) if hover_z_lift is None else hover_z_lift),
        )
        transport_arm = arm["transport"]
        descend_arm = arm["hover"]
        place_arm = arm["place"]
        if bool(getattr(args, "retreat_after_success", False)):
            retreat_arm = arm["retreat"]
        elif int(getattr(args, "post_release_clear_steps", 0)) > 0:
            retreat_arm = arm["hover"]
        else:
            retreat_arm = arm["place"]
        transport = {**close_thumb, **transport_arm}
        descend = {**close_thumb, **descend_arm}
        pre_release_end = {**close_thumb, **place_arm}
        release_open = dict(place_arm)
        release_clear = dict(descend_arm)
        retreat = dict(retreat_arm)
    else:
        transport = {**close_thumb, **TRANSPORT_ARM}
        descend = {**close_thumb, **DESCEND_ARM}
        pre_release_end = descend
        release_open = dict(DESCEND_ARM)
        release_clear = release_open
        retreat = dict(RETREAT_ARM)
    phases = [
        ("default_hold", default_targets, default_targets, scaled_steps(args, profile, "default_hold_steps")),
        ("move_to_pre_approach", default_targets, pre_approach, scaled_steps(args, profile, "move_steps")),
        ("approach_ball", pre_approach, approach, scaled_steps(args, profile, "approach_steps")),
        ("preshape", approach, preshape, scaled_steps(args, profile, "hand_steps")),
        ("close_four_fingers", preshape, close_fingers, scaled_steps(args, profile, "hand_steps")),
        ("close_thumb", close_fingers, close_thumb, scaled_steps(args, profile, "close_thumb_steps")),
    ]
    if int(getattr(args, "close_hold_steps", 0)) > 0:
        phases.append(("close_hold", close_thumb, close_thumb, scaled_steps(args, profile, "close_hold_steps")))
    phases.extend(
        [
            ("lift", close_thumb, lift, scaled_steps(args, profile, "lift_steps")),
            ("hold_lift", lift, lift, scaled_steps(args, profile, "hold_steps")),
            ("transport", lift, transport, scaled_steps(args, profile, "transport_steps")),
        ]
    )
    if int(getattr(args, "transport_hold_steps", 0)) > 0:
        phases.append(("transport_hold", transport, transport, scaled_steps(args, profile, "transport_hold_steps")))
    phases.extend(
        [
            ("descend_to_target", transport, descend, scaled_steps(args, profile, "descend_steps")),
            ("pre_release_settle", descend, pre_release_end, scaled_steps(args, profile, "pre_release_settle_steps")),
            ("release", pre_release_end, release_open, scaled_steps(args, profile, "release_steps")),
        ]
    )
    settle_start = release_open
    if int(getattr(args, "post_release_clear_steps", 0)) > 0:
        phases.append(
            (
                "post_release_clear",
                release_open,
                release_clear,
                scaled_steps(args, profile, "post_release_clear_steps"),
            )
        )
        settle_start = release_clear
    phases.extend(
        [
            ("retreat", settle_start, retreat, scaled_steps(args, profile, "retreat_steps")),
            ("settle_on_target", retreat, retreat, scaled_steps(args, profile, "settle_steps")),
        ]
    )
    return phases


def extended_observation(api: ArmHandStage1TaskAPI, target_center: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    base = api.get_observation()["vector"]
    ball = api.get_ball_pose()["position"]
    ball_to_target = target_center - ball
    return np.concatenate([base, target_center, ball_to_target]), base


def update_counters(
    api: ArmHandStage1TaskAPI,
    initial_ball: np.ndarray,
    target_center: np.ndarray,
    phase_name: str,
    counters: dict[str, Any],
    target_radius: float,
) -> dict[str, Any]:
    metrics = api.compute_task_metrics(initial_ball)
    ball = np.asarray(metrics["ball_position"], dtype=np.float64)
    target_delta = ball - target_center
    metrics.update(
        {
            "target_center": target_center,
            "target_delta_xyz": target_delta,
            "target_distance_xy": float(np.linalg.norm(target_delta[:2])),
            "target_distance_xyz": float(np.linalg.norm(target_delta)),
            "target_height_error": float(target_delta[2]),
            "ball_velocity_norm": float(np.linalg.norm(api.get_ball_pose()["velocity"])),
        }
    )
    contact = metrics["contact"]
    if (
        metrics["ball_lift_height"] >= 0.08
        and contact["ball_hand_contact_count"] >= 1
        and contact.get("ball_floor_contact_count", 0) == 0
    ):
        counters["lifted_once"] = True
    if phase_name in {"release", "retreat", "settle_on_target"}:
        counters["release_started"] = True
    if counters["lifted_once"] and not counters["release_started"] and phase_name in {"transport", "transport_hold", "descend_to_target"}:
        counters["transport_floor_contacts"] += int(contact.get("ball_floor_contact_count", 0) > 0)
    if counters["release_started"] and is_stable_on_target(metrics, target_radius):
        counters["stable_target_steps"] += 1
    elif counters["release_started"]:
        counters["stable_target_steps"] = 0
    counters["step_count"] += 1
    return metrics


def pick_place_reward(metrics: dict[str, Any], counters: dict[str, Any], success: bool, failure: bool) -> float:
    contact = metrics["contact"]
    reward = 5.0 * max(0.0, min(float(metrics["ball_lift_height"]), 0.12))
    if contact["ball_hand_contact_count"] >= 1 and not counters["release_started"]:
        reward += 0.5
    if counters["release_started"]:
        reward -= 2.0 * float(metrics["target_distance_xy"])
        reward -= 0.25 * max(0, int(contact["ball_hand_contact_count"]))
    reward -= 5.0 * max(0, int(counters["transport_floor_contacts"]))
    reward += 10.0 if success else 0.0
    reward -= 10.0 if failure else 0.0
    return float(reward)


def collect_episode(
    api: ArmHandStage1TaskAPI,
    episode_id: int,
    target_row: dict[str, Any],
    profile: PickPlaceProfile,
    args,
) -> dict[str, Any]:
    rng = np.random.default_rng(args.seed + profile.seed_offset + episode_id)
    target_center = np.asarray(target_row["target_center"], dtype=np.float64)
    target_offset = np.asarray(target_row["target_offset"], dtype=np.float64)
    pre_release_z_drop = float(target_row.get("pre_release_z_drop", getattr(args, "pre_release_z_drop", 0.02)))
    hover_z_lift = float(target_row.get("hover_z_lift", getattr(args, "hover_z_lift", 0.0)))
    api.reset_hand_open()
    initial_ball = api.get_ball_pose()["position"].copy()
    default_targets = api.targets_from_current_qpos()
    phases = build_pick_place_phases(
        default_targets,
        args,
        profile,
        api=api,
        target_center=target_center,
        pre_release_z_drop=pre_release_z_drop,
        hover_z_lift=hover_z_lift,
    )
    phase_names = phase_id_table(phases)
    terminal_reasons = terminal_reason_table()
    max_episode_steps = sum(steps for _, _, _, steps in phases)
    rows = {
        "obs": [],
        "base_obs": [],
        "actions": [],
        "expert_actions": [],
        "next_obs": [],
        "base_next_obs": [],
        "rewards": [],
        "dones": [],
        "successes": [],
        "failures": [],
        "terminal_reason_ids": [],
        "episode_ids": [],
        "step_ids": [],
        "phase_ids": [],
        "phase_step_ids": [],
        "initial_ball_positions": [],
        "target_centers": [],
        "target_offsets": [],
        "pre_release_z_drops": [],
        "hover_z_lifts": [],
        "behavior_profile_ids": [],
        "timing_scales": [],
        "action_noise_abs": [],
        "action_lag": [],
        "stable_target_steps": [],
        "transport_floor_contacts": [],
    }
    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    previous_behavior_action: np.ndarray | None = None
    final_eval: dict[str, Any] | None = None
    terminal_phase = "none"
    phase_summaries = []

    for phase_id, (phase_name, start_targets, end_targets, steps) in enumerate(phases):
        phase_start = int(counters["step_count"])
        for local_step in range(max(1, int(steps))):
            obs_ext, obs_base = extended_observation(api, target_center)
            alpha = local_step / max(1, int(steps) - 1)
            targets = lift_base.blend_targets(start_targets, end_targets, alpha)
            expert_action = api.action_from_targets(targets)
            behavior_action = make_behavior_action(api, expert_action, previous_behavior_action, rng, profile)
            previous_behavior_action = behavior_action.copy()
            api.step_action(behavior_action, n=1, pin_ball=False)
            metrics = update_counters(api, initial_ball, target_center, phase_name, counters, args.target_radius)
            evaluation = evaluate_pick_place_state(
                api,
                initial_ball,
                target_center=target_center,
                step_count=int(counters["step_count"]),
                max_episode_steps=max_episode_steps,
                lifted_once=bool(counters["lifted_once"]),
                release_started=bool(counters["release_started"]),
                stable_target_steps=int(counters["stable_target_steps"]),
                transport_floor_contacts=int(counters["transport_floor_contacts"]),
                target_radius_m=float(args.target_radius),
                required_stable_steps=int(args.required_stable_steps),
            )
            next_ext, next_base = extended_observation(api, target_center)
            reward = pick_place_reward(metrics, counters, bool(evaluation["success"]), bool(evaluation["failure"]))
            rows["obs"].append(obs_ext)
            rows["base_obs"].append(obs_base)
            rows["actions"].append(behavior_action)
            rows["expert_actions"].append(expert_action)
            rows["next_obs"].append(next_ext)
            rows["base_next_obs"].append(next_base)
            rows["rewards"].append(reward)
            rows["dones"].append(evaluation["done"])
            rows["successes"].append(evaluation["success"])
            rows["failures"].append(evaluation["failure"])
            rows["terminal_reason_ids"].append(reason_code(evaluation["terminal_reason"], terminal_reasons))
            rows["episode_ids"].append(episode_id)
            rows["step_ids"].append(int(counters["step_count"]) - 1)
            rows["phase_ids"].append(phase_id)
            rows["phase_step_ids"].append(local_step)
            rows["initial_ball_positions"].append(initial_ball.copy())
            rows["target_centers"].append(target_center.copy())
            rows["target_offsets"].append(target_offset.copy())
            rows["pre_release_z_drops"].append(pre_release_z_drop)
            rows["hover_z_lifts"].append(hover_z_lift)
            rows["behavior_profile_ids"].append(args.profile_names.index(profile.name))
            rows["timing_scales"].append(profile.timing_scale)
            rows["action_noise_abs"].append(profile.action_noise_abs)
            rows["action_lag"].append(profile.action_lag)
            rows["stable_target_steps"].append(int(counters["stable_target_steps"]))
            rows["transport_floor_contacts"].append(int(counters["transport_floor_contacts"]))
            final_eval = evaluation
            if evaluation["done"]:
                terminal_phase = phase_name
                break
        phase_eval = evaluate_pick_place_state(
            api,
            initial_ball,
            target_center=target_center,
            step_count=int(counters["step_count"]),
            max_episode_steps=max_episode_steps,
            lifted_once=bool(counters["lifted_once"]),
            release_started=bool(counters["release_started"]),
            stable_target_steps=int(counters["stable_target_steps"]),
            transport_floor_contacts=int(counters["transport_floor_contacts"]),
            target_radius_m=float(args.target_radius),
            required_stable_steps=int(args.required_stable_steps),
        )
        phase_summaries.append(
            {
                "phase": phase_name,
                "start_step": phase_start,
                "end_step": int(counters["step_count"]),
                "status": phase_eval["episode_status"],
                "terminal_reason": phase_eval["terminal_reason"],
                "stable_target_steps": int(counters["stable_target_steps"]),
                "transport_floor_contacts": int(counters["transport_floor_contacts"]),
                "metrics": phase_eval["official_metrics"],
            }
        )
        if final_eval is not None and final_eval["done"]:
            break

    if final_eval is None:
        final_eval = evaluate_pick_place_state(
            api,
            initial_ball,
            target_center=target_center,
            step_count=int(counters["step_count"]),
            max_episode_steps=max_episode_steps,
            lifted_once=bool(counters["lifted_once"]),
            release_started=bool(counters["release_started"]),
            stable_target_steps=int(counters["stable_target_steps"]),
            transport_floor_contacts=int(counters["transport_floor_contacts"]),
            target_radius_m=float(args.target_radius),
            required_stable_steps=int(args.required_stable_steps),
        )
    return {
        "episode_id": int(episode_id),
        "profile": profile,
        "target_id": int(target_row["target_id"]),
        "target_center": target_center,
        "target_offset": target_offset,
        "pre_release_z_drop": pre_release_z_drop,
        "hover_z_lift": hover_z_lift,
        "initial_ball": initial_ball,
        "step_count": int(counters["step_count"]),
        "terminal_phase": terminal_phase,
        "terminal_eval": final_eval,
        "phase_summaries": phase_summaries,
        "counters": counters,
        "rows": rows,
        "phase_name_table": phase_names,
        "terminal_reason_table": terminal_reasons,
    }


def write_dataset(dataset_path: Path, episodes: list[dict[str, Any]], api: ArmHandStage1TaskAPI, contract: dict[str, Any], args) -> None:
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    phase_names = episodes[0]["phase_name_table"]
    terminal_reasons = episodes[0]["terminal_reason_table"]
    np.savez_compressed(
        dataset_path,
        obs=concatenate_rows(episodes, "obs", np.float64),
        base_obs=concatenate_rows(episodes, "base_obs", np.float64),
        actions=concatenate_rows(episodes, "actions", np.float64),
        expert_actions=concatenate_rows(episodes, "expert_actions", np.float64),
        next_obs=concatenate_rows(episodes, "next_obs", np.float64),
        base_next_obs=concatenate_rows(episodes, "base_next_obs", np.float64),
        rewards=concatenate_rows(episodes, "rewards", np.float64),
        dones=concatenate_rows(episodes, "dones", np.bool_),
        successes=concatenate_rows(episodes, "successes", np.bool_),
        failures=concatenate_rows(episodes, "failures", np.bool_),
        terminal_reason_ids=concatenate_rows(episodes, "terminal_reason_ids", np.int32),
        episode_ids=concatenate_rows(episodes, "episode_ids", np.int32),
        step_ids=concatenate_rows(episodes, "step_ids", np.int32),
        phase_ids=concatenate_rows(episodes, "phase_ids", np.int32),
        phase_step_ids=concatenate_rows(episodes, "phase_step_ids", np.int32),
        initial_ball_positions=concatenate_rows(episodes, "initial_ball_positions", np.float64),
        target_centers=concatenate_rows(episodes, "target_centers", np.float64),
        target_offsets=concatenate_rows(episodes, "target_offsets", np.float64),
        pre_release_z_drops=concatenate_rows(episodes, "pre_release_z_drops", np.float64),
        hover_z_lifts=concatenate_rows(episodes, "hover_z_lifts", np.float64),
        behavior_profile_ids=concatenate_rows(episodes, "behavior_profile_ids", np.int32),
        timing_scales=concatenate_rows(episodes, "timing_scales", np.float64),
        action_noise_abs=concatenate_rows(episodes, "action_noise_abs", np.float64),
        action_lag=concatenate_rows(episodes, "action_lag", np.float64),
        stable_target_steps=concatenate_rows(episodes, "stable_target_steps", np.int32),
        transport_floor_contacts=concatenate_rows(episodes, "transport_floor_contacts", np.int32),
        joint_names=np.asarray(api.get_joint_names(), dtype=str),
        actuator_names=np.asarray(api.get_actuator_names(), dtype=str),
        phase_name_table=np.asarray(phase_names, dtype=str),
        terminal_reason_table=np.asarray(terminal_reasons, dtype=str),
        behavior_profile_table=np.asarray(args.profile_names, dtype=str),
        task_name=np.asarray([TASK_NAME], dtype=str),
        contract_version=np.asarray([TASK_CONTRACT_VERSION], dtype=str),
        dataset_version=np.asarray([str(getattr(args, "dataset_version", DATASET_VERSION))], dtype=str),
        scene=np.asarray([str(api.scene_path)], dtype=str),
        target_radius=np.asarray([float(args.target_radius)], dtype=np.float64),
        required_stable_steps=np.asarray([int(args.required_stable_steps)], dtype=np.int32),
        observation_feature_mode=np.asarray(["base_obs_target"], dtype=str),
        bc_feature_mode=np.asarray(["obs_phase_target"], dtype=str),
        repair_focus=np.asarray(getattr(args, "repair_focus", ""), dtype=str),
        contract_json=np.asarray([json.dumps(json_ready(contract), ensure_ascii=False)], dtype=str),
        phase_step_config_json=np.asarray([json.dumps(json_ready(phase_step_config(args)), ensure_ascii=False)], dtype=str),
    )


def phase_step_config(args) -> dict[str, int]:
    names = [
        "default_hold_steps",
        "move_steps",
        "approach_steps",
        "hand_steps",
        "close_thumb_steps",
        "close_hold_steps",
        "lift_steps",
        "hold_steps",
        "transport_steps",
        "transport_hold_steps",
        "descend_steps",
        "pre_release_settle_steps",
        "release_steps",
        "post_release_clear_steps",
        "retreat_steps",
        "settle_steps",
    ]
    return {name: int(getattr(args, name, 0)) for name in names}


def summarize_payload(dataset_path: Path, episodes: list[dict[str, Any]], api: ArmHandStage1TaskAPI, args) -> dict[str, Any]:
    obs = concatenate_rows(episodes, "obs", np.float64)
    base_obs = concatenate_rows(episodes, "base_obs", np.float64)
    actions = concatenate_rows(episodes, "actions", np.float64)
    expert_actions = concatenate_rows(episodes, "expert_actions", np.float64)
    success_count = sum(1 for ep in episodes if ep["terminal_eval"]["success"])
    terminal_counts: dict[str, int] = {}
    profile_counts: dict[str, int] = {}
    for ep in episodes:
        reason = ep["terminal_eval"]["terminal_reason"]
        terminal_counts[reason] = terminal_counts.get(reason, 0) + 1
        profile_counts[ep["profile"].name] = profile_counts.get(ep["profile"].name, 0) + 1
    target_distances = [float(ep["terminal_eval"]["official_metrics"]["target_distance_xy"]) for ep in episodes]
    stable_steps = [int(ep["terminal_eval"]["stable_target_steps"]) for ep in episodes]
    transport_floor = [int(ep["terminal_eval"]["transport_floor_contacts"]) for ep in episodes]
    release_hand = [int(ep["terminal_eval"]["official_metrics"]["contact"]["ball_hand_contact_count"]) for ep in episodes]
    pre_release_z_drops = [float(ep["pre_release_z_drop"]) for ep in episodes]
    hover_z_lifts = [float(ep["hover_z_lift"]) for ep in episodes]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "dataset_version": str(getattr(args, "dataset_version", DATASET_VERSION)),
        "scene": str(api.scene_path),
        "dataset": str(dataset_path),
        "episodes": len(episodes),
        "total_rows": int(obs.shape[0]),
        "obs_shape": list(obs.shape),
        "base_obs_shape": list(base_obs.shape),
        "actions_shape": list(actions.shape),
        "expert_actions_shape": list(expert_actions.shape),
        "success_count": int(success_count),
        "terminal_reason_counts": terminal_counts,
        "profile_counts": profile_counts,
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "target_distance_xy_range": [float(np.min(target_distances)), float(np.max(target_distances))],
        "target_distance_xy_mean": float(np.mean(target_distances)),
        "stable_target_steps_range": [int(np.min(stable_steps)), int(np.max(stable_steps))],
        "transport_floor_contacts_total": int(np.sum(transport_floor)),
        "release_hand_contacts_max": int(np.max(release_hand)),
        "target_offsets_xy": {
            "x_offsets": parse_values(args.x_offsets),
            "y_offsets": parse_values(args.y_offsets),
        },
        "phase_step_config": phase_step_config(args),
        "repair_focus": str(getattr(args, "repair_focus", "")),
        "target_conditioned": bool(getattr(args, "target_conditioned", False)),
        "pre_release_z_drop": float(getattr(args, "pre_release_z_drop", 0.0)),
        "pre_release_z_drop_range": [float(np.min(pre_release_z_drops)), float(np.max(pre_release_z_drops))],
        "hover_z_lift": float(getattr(args, "hover_z_lift", 0.0)),
        "hover_z_lift_range": [float(np.min(hover_z_lifts)), float(np.max(hover_z_lifts))],
        "profiles": [profile.__dict__ for profile in PROFILES if profile.name in args.profile_names],
        "episode_summaries": [
            {
                "episode_id": ep["episode_id"],
                "profile": ep["profile"].name,
                "target_id": ep["target_id"],
                "target_center": ep["target_center"],
                "target_offset": ep["target_offset"],
                "pre_release_z_drop": ep["pre_release_z_drop"],
                "hover_z_lift": ep["hover_z_lift"],
                "initial_ball": ep["initial_ball"],
                "step_count": ep["step_count"],
                "terminal_phase": ep["terminal_phase"],
                "terminal_eval": ep["terminal_eval"],
                "phase_summaries": ep["phase_summaries"],
            }
            for ep in episodes
        ],
        "training_ready": False,
        "bc_target_field": "expert_actions",
        "replay_action_field": "actions",
        "v0_6_needed_now": False,
        "notes": [
            f"Dataset {getattr(args, 'dataset_version', DATASET_VERSION)} is intentionally fixed-target first unless target offsets are provided.",
            "`actions` are applied behavior actions for deterministic replay.",
            "`expert_actions` are the clean scripted BC labels.",
            "`obs` is base observation plus target_center_xyz and ball_to_target_xyz.",
            "Target-conditioned transport is included only when `target_conditioned` is true.",
        ],
    }


def write_report(payload: dict[str, Any], report_path: Path, meta_path: Path, run_dir: Path | None) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    if run_dir:
        (run_dir / "eval" / "collection_summary.json").write_text(
            json.dumps(json_ready(payload), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    lines = [
        f"# Arm-Hand Stage1 V3 Pick-Place Dataset {payload['dataset_version'].upper()} Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Total rows: `{payload['total_rows']}`\n",
        f"- obs shape: `{payload['obs_shape']}`\n",
        f"- base obs shape: `{payload['base_obs_shape']}`\n",
        f"- behavior actions shape: `{payload['actions_shape']}`\n",
        f"- expert actions shape: `{payload['expert_actions_shape']}`\n",
        f"- Success count: `{payload['success_count']} / {payload['episodes']}`\n",
        f"- Terminal reasons: `{payload['terminal_reason_counts']}`\n",
        f"- Profile counts: `{payload['profile_counts']}`\n",
        f"- Repair focus: `{payload['repair_focus']}`\n",
        f"- Target conditioned: `{payload['target_conditioned']}`\n",
        f"- Pre-release z drop: `{payload['pre_release_z_drop']}`\n",
        f"- Pre-release z drop range: `{payload['pre_release_z_drop_range'][0]}` to `{payload['pre_release_z_drop_range'][1]}`\n",
        f"- Hover z lift: `{payload['hover_z_lift']}`\n",
        f"- Hover z lift range: `{payload['hover_z_lift_range'][0]}` to `{payload['hover_z_lift_range'][1]}`\n",
        f"- Phase step config: `{payload['phase_step_config']}`\n",
        f"- Target distance XY range: `{payload['target_distance_xy_range'][0]:.6f} m` to `{payload['target_distance_xy_range'][1]:.6f} m`\n",
        f"- Stable target steps range: `{payload['stable_target_steps_range'][0]}` to `{payload['stable_target_steps_range'][1]}`\n",
        f"- Transport floor contacts total: `{payload['transport_floor_contacts_total']}`\n",
        f"- Release hand contacts max: `{payload['release_hand_contacts_max']}`\n",
        f"- BC target field: `{payload['bc_target_field']}`\n",
        f"- Training ready: **No, replay QA still required**\n\n",
        "## Episode Summary\n\n",
        "| ep | profile | target offset xy | drop m | hover lift m | rows | terminal phase | status | reason | target xy m | stable steps | transport floor | final hand |\n",
        "|---:|---|---|---:|---:|---:|---|---|---|---:|---:|---:|---:|\n",
    ]
    for ep in payload["episode_summaries"]:
        final = ep["terminal_eval"]
        metrics = final["official_metrics"]
        contact = metrics["contact"]
        lines.append(
            f"| {ep['episode_id']} | {ep['profile']} | `{np.round(ep['target_offset'][:2], 5).tolist()}` | "
            f"{ep['pre_release_z_drop']:.3f} | {ep['hover_z_lift']:.3f} | {ep['step_count']} | {ep['terminal_phase']} | {final['episode_status']} | "
            f"{final['terminal_reason']} | {metrics['target_distance_xy']:.6f} | "
            f"{final['stable_target_steps']} | {final['transport_floor_contacts']} | "
            f"{contact['ball_hand_contact_count']} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            f"- This is a fixed-target first dataset for pick-place BC smoke/recovery attempt `{payload['dataset_version']}`.\n",
            "- Replay QA is the next gate. Do not train from this dataset until replay QA passes.\n",
            "- If replay QA or online eval fails, collect the next repair dataset with a narrower diagnosis rather than promoting this checkpoint.\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def resolve_outputs(args) -> tuple[Path, Path, Path, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    dataset = args.dataset
    report = args.report
    metadata = args.metadata
    tag = version_tag(getattr(args, "dataset_version", DATASET_VERSION))
    default_dataset_name = f"arm_hand_stage1_v3_pick_place_dataset_{tag}.npz"
    if run_dir:
        (run_dir / "datasets").mkdir(parents=True, exist_ok=True)
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        dataset = dataset or (run_dir / "datasets" / default_dataset_name)
        report = report or (run_dir / "eval" / f"dataset_{tag}_collection_report.md")
        metadata = metadata or (run_dir / "eval" / f"dataset_{tag}_collection_summary.json")
    else:
        dataset = dataset or (DATA / default_dataset_name)
        report = report or (DOCS / f"arm_hand_stage1_v3_pick_place_dataset_{tag}_report.md")
        metadata = metadata or (META / f"arm_hand_stage1_v3_pick_place_dataset_{tag}.json")
    return Path(dataset), Path(report), Path(metadata), run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Stage2 pick-place dataset v0.5.")
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--dataset-version", default=DATASET_VERSION)
    parser.add_argument("--repair-focus", default="")
    parser.add_argument("--target-conditioned", action="store_true")
    parser.add_argument("--pre-release-z-drop", type=float, default=0.02)
    parser.add_argument("--hover-z-lift", type=float, default=0.0)
    parser.add_argument("--retreat-after-success", action="store_true")
    parser.add_argument("--target-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=DEFAULT_TARGET_CENTER)
    parser.add_argument(
        "--target-centers",
        default="",
        help="Optional semicolon-separated x,y,z[,pre_release_z_drop[,hover_z_lift]] target centers; overrides x/y offset grid.",
    )
    parser.add_argument("--x-offsets", default="0.0")
    parser.add_argument("--y-offsets", default="0.0")
    parser.add_argument("--target-radius", type=float, default=DEFAULT_TARGET_RADIUS_M)
    parser.add_argument("--required-stable-steps", type=int, default=DEFAULT_REQUIRED_STABLE_STEPS)
    parser.add_argument("--profiles", default="clean_nominal,timing_fast_clean,timing_slow_clean")
    parser.add_argument("--seed", type=int, default=51)
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--close-thumb-steps", type=int, default=120)
    parser.add_argument("--close-hold-steps", type=int, default=0)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--transport-steps", type=int, default=900)
    parser.add_argument("--transport-hold-steps", type=int, default=0)
    parser.add_argument("--descend-steps", type=int, default=500)
    parser.add_argument("--pre-release-settle-steps", type=int, default=180)
    parser.add_argument("--release-steps", type=int, default=600)
    parser.add_argument("--post-release-clear-steps", type=int, default=0)
    parser.add_argument("--retreat-steps", type=int, default=300)
    parser.add_argument("--settle-steps", type=int, default=600)
    args = parser.parse_args()

    dataset_path, report_path, meta_path, run_dir = resolve_outputs(args)
    selected_profiles = parse_profiles(args.profiles)
    args.profile_names = [profile.name for profile in selected_profiles]

    api = ArmHandStage1TaskAPI(args.scene)
    contract = build_contract(args.scene)
    target_rows = build_target_centers(args)
    episodes: list[dict[str, Any]] = []
    episode_id = 0
    for profile in selected_profiles:
        for target_row in target_rows:
            ep = collect_episode(api, episode_id, target_row, profile, args)
            episodes.append(ep)
            print(
                f"ep={episode_id:02d} profile={profile.name} "
                f"target_offset={np.round(target_row['target_offset'][:2], 4).tolist()} "
                f"{ep['terminal_eval']['episode_status']} reason={ep['terminal_eval']['terminal_reason']} "
                f"rows={ep['step_count']}"
            )
            episode_id += 1

    write_dataset(dataset_path.resolve(), episodes, api, contract, args)
    payload = summarize_payload(dataset_path.resolve(), episodes, api, args)
    write_report(payload, report_path, meta_path, run_dir)
    print(f"Dataset {payload['dataset_version']} status: {payload['success_count']}/{payload['episodes']} success")
    print(f"Saved dataset: {dataset_path.resolve()}")
    print(f"Saved report: {report_path}")
    print(f"Saved metadata: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
