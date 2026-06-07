#!/usr/bin/env python3
"""Replay QA for Stage3 sensor-fusion expert datasets."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, DEFAULT_GOAL_LIFT_DELTA, DEFAULT_OBJECT_SHAPE, PHASES


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DATASET = ROOT / "data" / "stage3_sensor_fusion_expert_dataset_v0.npz"
REPORT = DOCS / "stage3_sensor_fusion_expert_dataset_v0_replay_report.md"
META_OUT = META / "stage3_sensor_fusion_expert_dataset_v0_replay.json"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


def compare_vectors(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return float("inf")
    return float(np.max(np.abs(a - b))) if a.size else 0.0


def vision_from_dataset(data, idx: int) -> dict[str, Any]:
    pose = np.asarray(data["vision_pose_estimates"][idx], dtype=np.float64)
    scalars = np.asarray(data["vision_scalars"][idx], dtype=np.float64)
    return {
        "object_pose_xyz_est": pose,
        "object_axis_est": np.array([0.0, 0.0, 1.0], dtype=np.float64),
        "object_shape_params_est": DEFAULT_OBJECT_SHAPE.copy(),
        "goal_pose_xyz_est": pose + DEFAULT_GOAL_LIFT_DELTA,
        "object_to_goal_est": DEFAULT_GOAL_LIFT_DELTA.copy(),
        "confidence": float(scalars[0]),
        "occlusion": float(scalars[1]),
        "latency_steps": int(round(float(scalars[2]))),
        "noise_std": float(scalars[3]),
        "mask_pixels": int(round(float(scalars[4]))),
        "visibility_fraction": float(scalars[5]),
        "fit_residual_rms": float(scalars[6]),
    }


def progress_from_obs(data, idx: int) -> float:
    nq = int(data["nq"][0])
    nv = int(data["nv"][0])
    nu = int(data["nu"][0])
    return float(data["obs"][idx][nq + nv + nu + len(PHASES)])


def replay_episode(model, mujoco, data, episode_id: int, *, max_error_warn: float) -> dict[str, Any]:
    episode_ids = data["episode_ids"].astype(np.int32)
    idxs = np.where(episode_ids == int(episode_id))[0]
    if idxs.size == 0:
        raise ValueError(f"Episode {episode_id} not found")
    d = mujoco.MjData(model)
    first = int(idxs[0])
    d.qpos[:] = data["initial_qpos"][first]
    d.qvel[:] = data["initial_qvel"][first]
    d.ctrl[:] = data["initial_ctrl"][first]
    mujoco.mj_forward(model, d)
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco)
    tactile_sensor.reset(d)
    expert_phase_table = [str(item) for item in data["expert_phase_table"]]
    terminal_reasons = [str(item) for item in data["terminal_reason_table"]]
    max_obs_error = 0.0
    max_next_obs_error = 0.0
    max_qpos_error = 0.0
    max_gt_object_error = 0.0
    failures: list[str] = []
    terminal_reason = "running"
    terminal_idx = None

    for idx in idxs:
        idx = int(idx)
        phase_name = expert_phase_table[int(data["phase_ids"][idx])]
        progress = progress_from_obs(data, idx)
        vision = vision_from_dataset(data, idx)
        tactile = tactile_sensor.sample(d)
        obs_replay = collect.observation_vector(model, d, vision, tactile, phase_name=phase_name, progress=progress)
        max_obs_error = max(max_obs_error, compare_vectors(obs_replay, data["obs"][idx]))

        d.ctrl[:] = np.asarray(data["actions"][idx], dtype=np.float64)
        mujoco.mj_step(model, d)
        next_tactile = tactile_sensor.sample(d)
        next_replay = collect.observation_vector(model, d, vision, next_tactile, phase_name=phase_name, progress=progress)
        max_next_obs_error = max(max_next_obs_error, compare_vectors(next_replay, data["next_obs"][idx]))
        gt_pos = d.xpos[sweep.egg_body_id(model, mujoco)].copy()
        max_gt_object_error = max(max_gt_object_error, compare_vectors(gt_pos, data["gt_object_positions"][idx]))
        nq = int(data["nq"][0])
        max_qpos_error = max(max_qpos_error, compare_vectors(next_replay[:nq], data["next_obs"][idx][:nq]))
        if bool(data["dones"][idx]):
            terminal_idx = idx
            terminal_reason = terminal_reasons[int(data["terminal_reason_ids"][idx])]
            break

    if terminal_idx is None:
        failures.append("missing_terminal_done")
    if max_obs_error > max_error_warn:
        failures.append(f"obs_error {max_obs_error:.3e} > {max_error_warn:.3e}")
    if max_next_obs_error > max_error_warn:
        failures.append(f"next_obs_error {max_next_obs_error:.3e} > {max_error_warn:.3e}")
    if max_gt_object_error > max_error_warn:
        failures.append(f"gt_object_error {max_gt_object_error:.3e} > {max_error_warn:.3e}")
    if terminal_reason != "success_gentle_grasp_hold":
        failures.append(f"terminal_reason={terminal_reason}")

    return {
        "episode_id": int(episode_id),
        "frames": int(idxs.size),
        "terminal_dataset_index": terminal_idx,
        "terminal_reason": terminal_reason,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "max_obs_error": float(max_obs_error),
        "max_next_obs_error": float(max_next_obs_error),
        "max_qpos_error": float(max_qpos_error),
        "max_gt_object_error": float(max_gt_object_error),
        "final_lift_height_m": float(data["gt_object_lift_heights"][idxs[-1]]),
    }


def write_outputs(payload: dict[str, Any], report_path: Path, metadata_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Stage3 Sensor Fusion Dataset Replay QA Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes checked: `{payload['episodes_checked']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Shape status: `{payload['shape_status']}`\n",
        f"- Replay status: `{payload['replay_status']}`\n",
        f"- Max obs error: `{payload['max_obs_error']:.3e}`\n",
        f"- Max next_obs error: `{payload['max_next_obs_error']:.3e}`\n",
        f"- Max object position error: `{payload['max_gt_object_error']:.3e}`\n",
        f"- Success replay count: `{payload['success_replay_count']} / {payload['episodes_checked']}`\n",
        f"- Training ready: **{payload['training_ready']}**\n\n",
        "## Shape Check\n\n",
    ]
    for key, value in payload["shape_check"].items():
        lines.append(f"- {key}: `{value}`\n")
    lines.extend(
        [
            "\n## Episode Replay\n\n",
            "| ep | status | reason | frames | obs err | next err | object err | failures |\n",
            "|---:|---|---|---:|---:|---:|---:|---|\n",
        ]
    )
    for item in payload["episode_results"]:
        lines.append(
            f"| {item['episode_id']} | {item['status']} | {item['terminal_reason']} | {item['frames']} | "
            f"{item['max_obs_error']:.3e} | {item['max_next_obs_error']:.3e} | "
            f"{item['max_gt_object_error']:.3e} | {'; '.join(item['failures']) or '-'} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- PASS means the saved action sequence deterministically reproduces the saved sensor observations and object trajectory.\n",
            "- This gate must pass before using the dataset for BC or residual-policy training.\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay QA for Stage3 sensor-fusion datasets.")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--metadata", type=Path, default=META_OUT)
    parser.add_argument("--all-episodes", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--episode-id", type=int, default=0)
    parser.add_argument("--max-error-warn", type=float, default=1e-9)
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(dataset_path)
    import mujoco

    with np.load(dataset_path, allow_pickle=False) as raw:
        data = {key: raw[key] for key in raw.files}
    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    obs = data["obs"]
    actions = data["actions"]
    next_obs = data["next_obs"]
    episode_ids = data["episode_ids"].astype(np.int32)
    available = sorted(int(v) for v in np.unique(episode_ids))
    selected = available if bool(args.all_episodes) else [int(args.episode_id)]
    nq = int(data["nq"][0])
    nv = int(data["nv"][0])
    nu = int(data["nu"][0])
    expected_obs_dim = nq + nv + nu + len(PHASES) + 1 + 3 + 3 + 3 + 3 + 3 + 4 + 8
    shape_check = {
        "obs_dim_matches": obs.ndim == 2 and obs.shape[1] == expected_obs_dim,
        "next_obs_dim_matches": next_obs.ndim == 2 and next_obs.shape[1] == expected_obs_dim,
        "action_dim_matches": actions.ndim == 2 and actions.shape[1] == nu,
        "row_counts_match": len(obs) == len(actions) == len(next_obs) == len(episode_ids),
        "nq_matches_model": nq == model.nq,
        "nv_matches_model": nv == model.nv,
        "nu_matches_model": nu == model.nu,
    }
    episode_results = [replay_episode(model, mujoco, data, ep, max_error_warn=float(args.max_error_warn)) for ep in selected]
    shape_status = "PASS" if all(shape_check.values()) else "FAIL"
    replay_status = "PASS" if all(item["status"] == "PASS" for item in episode_results) else "FAIL"
    status = "PASS" if shape_status == "PASS" and replay_status == "PASS" else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(dataset_path),
        "scene": str(Path(args.scene).resolve()),
        "episodes_checked": len(episode_results),
        "available_episodes": available,
        "shape_check": shape_check,
        "shape_status": shape_status,
        "replay_status": replay_status,
        "status": status,
        "success_replay_count": int(sum(1 for item in episode_results if item["terminal_reason"] == "success_gentle_grasp_hold" and item["status"] == "PASS")),
        "max_obs_error": max(item["max_obs_error"] for item in episode_results) if episode_results else float("nan"),
        "max_next_obs_error": max(item["max_next_obs_error"] for item in episode_results) if episode_results else float("nan"),
        "max_gt_object_error": max(item["max_gt_object_error"] for item in episode_results) if episode_results else float("nan"),
        "episode_results": episode_results,
        "training_ready": status == "PASS",
    }
    write_outputs(payload, Path(args.report), Path(args.metadata))
    print(f"Replay QA status: {status}")
    print(f"Success replay count: {payload['success_replay_count']}/{len(episode_results)}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
