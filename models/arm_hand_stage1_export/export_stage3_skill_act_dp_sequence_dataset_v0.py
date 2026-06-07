#!/usr/bin/env python3
"""Export Stage3.9B3 dense obs/action sequences for ACT/DP training prep.

This script stops one step before model training. It re-runs the current
canonical SkillZoo grasp skills in MuJoCo and writes dense per-timestep
sensor-abstraction observations plus actuator actions:

    obs_t, action_t, next_obs_t, done_t, episode_id, skill_id, phase_id

The output is intended as the first directly trainable dataset surface for
ACT-style action chunking and Diffusion Policy-style sequence windows. It does
not train a model and it does not claim learned-policy success.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
from arm_hand_stage1_v2_bc_common import load_policy
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, TASK_CONTRACT_VERSION, TASK_NAME


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_phase_hand_policy_v0.pth"
DEFAULT_SELECTED_PINCH = META / "stage3_pinch_grasp_training_v0_selected.json"
DEFAULT_DATASET = DATA / "stage3_skill_act_dp_sequence_dataset_v0.npz"
DEFAULT_JSONL = DATA / "stage3_skill_act_dp_sequence_dataset_v0.jsonl"
DEFAULT_METADATA = META / "stage3_skill_act_dp_sequence_dataset_v0.json"
DEFAULT_REPORT = DOCS / "stage3_skill_act_dp_sequence_dataset_v0_report.md"
DEFAULT_READINESS_DOC = DOCS / "stage3_act_dp_readiness_definition_v0.md"

SKILL_TABLE = ("full_hand_gentle_grasp", "thumb_index_middle_pinch")
HORIZON_CANDIDATES = (8, 16, 32, 64, 128, 256)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import eval_stage3_contact_transition_recovery_v0 as recovery
import eval_stage3_pinch_grasp_v0 as pinch
import run_stage3_visual_guided_grasp_sweep as sweep


def write_readiness_definition(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3 ACT/DP 可训练就绪定义 v0\n\n",
        f"- 日期：`{datetime.now().date().isoformat()}`\n",
        "- 范围：只定义 MuJoCo Stage3 技能数据何时可以进入 ACT / Diffusion Policy 训练，不包含真实硬件、真实摄像头或真实触觉。\n\n",
        "## 一句话定义\n\n",
        "当每条 canonical 技能演示都能提供完整、有限、维度一致的 `obs_t -> action_t -> next_obs_t` 序列，并且这些演示全部通过当前视觉/触觉/抬升验收时，就可以进入 ACT/DP 训练。\n\n",
        "## 必须满足的门槛\n\n",
        "1. 数据必须是 dense sequence，不是稀疏 trace：每个 timestep 都有 `obs`、`action`、`next_obs`、`done`、`episode_id`、`skill_id`、`phase_id`。\n",
        "2. 观测必须来自 Stage3 sensor abstraction：虚拟视觉 + 合成触觉/滑移 + 本体状态；真值只能作为 QA/评估字段，不能作为默认 policy input。\n",
        "3. action 必须是实际送入 MuJoCo actuator 的控制目标，并且全部落在 actuator control range 内。\n",
        "4. canonical training episodes 至少 `40` 条：`30` 条全手温和抓取 + `10` 条 thumb/index/middle 捏持，并且成功率为 `40 / 40`。\n",
        "5. 每个 episode 必须只有一个 terminal `done=True`，且 terminal reason 是对应技能的成功原因。\n",
        "6. 数据集中必须包含 normalization statistics：`obs_mean/std`、`action_mean/std`、`action_min/max`。\n",
        "7. 数据必须能按 action chunk / sequence horizon 切窗口，至少通过 `16`、`32`、`64` 三种 horizon 的窗口数量检查。\n\n",
        "## 什么时候算还不能训练\n\n",
        "- 只有 episode summary 或稀疏 trace，缺少每步 action。\n",
        "- 捏持和全手抓取使用不同 obs/action schema，不能被同一个 dataloader 读取。\n",
        "- 部分 canonical episode 失败，但没有明确过滤或失败标签。\n",
        "- action 没有经过 range 检查，或者包含 NaN/Inf。\n",
        "- 没有 train/val 切分建议和 normalization statistics。\n\n",
        "## 如果成功\n\n",
        "下一步可以写 `train_stage3_act_dp_baseline_v0.py`，先做小规模 overfit/smoke，再做 closed-loop MuJoCo eval。\n\n",
        "## 如果失败\n\n",
        "不进入模型训练；先修数据采集器、技能重放、失败 episode 或 schema 对齐问题。\n",
    ]
    path.write_text("".join(lines), encoding="utf-8")


def load_selected_pinch_candidate(path: Path) -> pinch.PinchCandidate:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = dict(payload["selected_candidate"])
    fields = {
        "name",
        "active_fingers",
        "thumb_cmc_abd",
        "thumb_cmc",
        "thumb_mcp",
        "thumb_ip",
        "active_mcp_flex",
        "active_mcp_abd",
        "active_pip",
        "active_dip",
        "inactive_scale",
        "approach_z_bias_delta",
        "lift_delta_scale",
    }
    data = {key: raw[key] for key in fields if key in raw}
    data["active_fingers"] = tuple(data["active_fingers"])
    return pinch.PinchCandidate(**data)


def full_hand_args(args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        scene=Path(args.scene),
        checkpoint=Path(args.checkpoint),
        seed=int(args.seed),
        random_offset_std=float(args.full_hand_random_offset_std),
        camera=str(args.camera),
        width=int(args.width),
        height=int(args.height),
        min_vision_confidence=0.55,
        functional_hit_threshold=0.015,
        max_ik_dxy=0.006,
        max_ik_dz=0.006,
        min_hold_stable_fraction=0.80,
        action_smoothing=0.0,
        no_train_range_clip=False,
        sample_every=200,
        approach_steps=320,
        hand_steps=140,
        close_fingers_steps=180,
        close_thumb_steps=180,
        contact_settle_steps=180,
        min_contact_settle_steps=2000,
        max_contact_settle_steps=2000,
        settle_stable_window_steps=300,
        gate_slip_threshold=0.18,
        gate_crush_threshold=0.35,
        gate_penetration_threshold=0.004,
        stop_approach_on_contact=False,
        min_approach_steps_before_contact_stop=90,
        approach_contact_stop_error_m=0.014,
        transition_gate_phases="slow_lift",
        transition_slip_threshold=0.29,
        transition_crush_threshold=0.35,
        transition_penetration_threshold=0.004,
        max_transition_hold_steps_per_phase=200,
        recovery_progress_drop=0.01,
        recovery_stable_window_steps=0,
        lift_steps=700,
        hold_steps=1500,
        device=str(args.device),
        capture_sequence=True,
    )


def pinch_args(args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        scene=Path(args.scene),
        seed=int(args.pinch_seed),
        random_offset_std=float(args.pinch_random_offset_std),
        trial="cycle",
        camera=str(args.camera),
        final_cameras="stage3_egg_closeup,stage3_egg_overview",
        width=int(args.width),
        height=int(args.height),
        min_vision_confidence=0.55,
        min_final_vision_confidence=0.35,
        min_vision_lift_height=0.045,
        min_hold_stable_fraction=0.60,
        min_hold_pinch_fraction=0.55,
        min_hold_pinch_purity=0.55,
        approach_steps=320,
        hand_steps=140,
        pinch_close_steps=260,
        min_contact_settle_steps=400,
        max_contact_settle_steps=1000,
        settle_stable_window_steps=120,
        gate_slip_threshold=0.22,
        gate_crush_threshold=0.35,
        gate_penetration_threshold=0.004,
        lift_steps=700,
        hold_steps=700,
        sample_every=200,
        render_vision_debug=False,
        debug_dir=DOCS / "visual_checks_stage3_act_dp_sequence_v0",
        capture_sequence=True,
    )


def phase_table_from_episodes(episodes: list[dict[str, Any]]) -> tuple[str, ...]:
    phases: list[str] = []
    seen: set[str] = set()
    for episode in episodes:
        rows = episode["sequence_rows"]
        for name in rows["phase_names"]:
            if str(name) not in seen:
                seen.add(str(name))
                phases.append(str(name))
    return tuple(phases)


def terminal_table_from_episodes(episodes: list[dict[str, Any]]) -> tuple[str, ...]:
    reasons = ["running"]
    seen = {"running"}
    for episode in episodes:
        for reason in episode["sequence_rows"]["terminal_reasons"]:
            if str(reason) not in seen:
                seen.add(str(reason))
                reasons.append(str(reason))
    return tuple(reasons)


def rows_array(rows: dict[str, list[Any]], key: str, dtype: Any, *, length: int, default: Any = None) -> np.ndarray:
    values = rows.get(key)
    if values is None:
        values = [default for _ in range(length)]
    return np.asarray(values, dtype=dtype)


def action_range_ok(model: Any, actions: np.ndarray) -> bool:
    limited = np.asarray(model.actuator_ctrllimited, dtype=bool)
    if not bool(limited.any()):
        return True
    ranges = np.asarray(model.actuator_ctrlrange, dtype=np.float32)
    low = ranges[:, 0]
    high = ranges[:, 1]
    bounded = actions[:, limited]
    return bool(np.all(bounded >= low[limited] - 1e-5) and np.all(bounded <= high[limited] + 1e-5))


def build_arrays(episodes: list[dict[str, Any]], model: Any) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], dict[str, Any]]:
    phase_table = phase_table_from_episodes(episodes)
    terminal_table = terminal_table_from_episodes(episodes)
    phase_to_id = {name: idx for idx, name in enumerate(phase_table)}
    terminal_to_id = {name: idx for idx, name in enumerate(terminal_table)}
    skill_to_id = {name: idx for idx, name in enumerate(SKILL_TABLE)}

    row_chunks: dict[str, list[np.ndarray]] = defaultdict(list)
    episode_rows: list[dict[str, Any]] = []
    row_start = 0

    for episode_index, episode in enumerate(episodes):
        rows = episode["sequence_rows"]
        n = len(rows["actions"])
        if n <= 0:
            raise ValueError(f"Episode {episode_index} has no dense sequence rows")
        skill_id = str(episode["skill_id"])
        obs = rows_array(rows, "obs", np.float32, length=n)
        actions = rows_array(rows, "actions", np.float32, length=n)
        next_obs = rows_array(rows, "next_obs", np.float32, length=n)
        rewards = rows_array(rows, "rewards", np.float32, length=n)
        dones = rows_array(rows, "dones", np.bool_, length=n)
        successes = rows_array(rows, "successes", np.bool_, length=n)
        failures = rows_array(rows, "failures", np.bool_, length=n)
        phase_names = [str(name) for name in rows["phase_names"]]
        terminal_reasons = [str(reason) for reason in rows["terminal_reasons"]]

        row_chunks["obs"].append(obs)
        row_chunks["actions"].append(actions)
        row_chunks["next_obs"].append(next_obs)
        row_chunks["rewards"].append(rewards)
        row_chunks["dones"].append(dones)
        row_chunks["successes"].append(successes)
        row_chunks["failures"].append(failures)
        row_chunks["episode_ids"].append(np.full(n, episode_index, dtype=np.int32))
        row_chunks["source_episode_ids"].append(np.full(n, int(episode["source_episode_id"]), dtype=np.int32))
        row_chunks["skill_ids"].append(np.full(n, skill_to_id[skill_id], dtype=np.int32))
        row_chunks["step_ids"].append(rows_array(rows, "step_ids", np.int32, length=n))
        row_chunks["phase_ids"].append(np.asarray([phase_to_id[name] for name in phase_names], dtype=np.int32))
        row_chunks["phase_step_ids"].append(rows_array(rows, "phase_step_ids", np.int32, length=n))
        row_chunks["phase_progress"].append(rows_array(rows, "phase_progress", np.float32, length=n, default=0.0))
        row_chunks["nominal_progress"].append(rows_array(rows, "nominal_progress", np.float32, length=n, default=0.0))
        row_chunks["control_progress"].append(rows_array(rows, "control_progress", np.float32, length=n, default=0.0))
        row_chunks["learned_hand"].append(rows_array(rows, "learned_hand", np.bool_, length=n, default=False))
        row_chunks["recovery_active"].append(rows_array(rows, "recovery_active", np.bool_, length=n, default=False))
        row_chunks["pinch_contact"].append(rows_array(rows, "pinch_contact", np.bool_, length=n, default=False))
        row_chunks["terminal_reason_ids"].append(np.asarray([terminal_to_id[name] for name in terminal_reasons], dtype=np.int32))
        row_chunks["lift_heights"].append(rows_array(rows, "lift_heights", np.float32, length=n, default=0.0))
        row_chunks["vision_pose_estimates"].append(rows_array(rows, "vision_pose_estimates", np.float32, length=n))
        row_chunks["vision_scalars"].append(rows_array(rows, "vision_scalars", np.float32, length=n))
        row_chunks["tactile_scalars"].append(rows_array(rows, "tactile_scalars", np.float32, length=n))
        row_chunks["tactile_region_masks"].append(rows_array(rows, "tactile_region_masks", np.float32, length=n))
        row_chunks["gt_object_positions"].append(rows_array(rows, "gt_object_positions", np.float32, length=n))
        row_chunks["gt_object_lift_heights"].append(rows_array(rows, "gt_object_lift_heights", np.float32, length=n))

        episode_rows.append(
            {
                "episode_id": int(episode_index),
                "source_episode_id": int(episode["source_episode_id"]),
                "skill_id": skill_id,
                "source_stage": str(episode["source_stage"]),
                "trial": str(episode["trial"]),
                "candidate": episode.get("candidate"),
                "row_start": int(row_start),
                "row_count": int(n),
                "success": bool(episode["success"]),
                "terminal_reason": str(episode["terminal_reason"]),
                "failure_reasons": list(episode.get("failure_reasons", [])),
                "risk_flags": list(episode.get("risk_flags", [])),
                "summary": episode.get("summary", {}),
            }
        )
        row_start += n

    arrays = {key: np.concatenate(chunks, axis=0) for key, chunks in row_chunks.items()}
    max_len = max(row["row_count"] for row in episode_rows)
    episode_count = len(episode_rows)
    obs_dim = int(arrays["obs"].shape[1])
    action_dim = int(arrays["actions"].shape[1])

    episode_obs = np.zeros((episode_count, max_len, obs_dim), dtype=np.float32)
    episode_next_obs = np.zeros_like(episode_obs)
    episode_actions = np.zeros((episode_count, max_len, action_dim), dtype=np.float32)
    episode_rewards = np.zeros((episode_count, max_len), dtype=np.float32)
    episode_mask = np.zeros((episode_count, max_len), dtype=np.bool_)
    episode_dones = np.zeros((episode_count, max_len), dtype=np.bool_)

    for row in episode_rows:
        eid = int(row["episode_id"])
        start = int(row["row_start"])
        count = int(row["row_count"])
        end = start + count
        episode_obs[eid, :count] = arrays["obs"][start:end]
        episode_next_obs[eid, :count] = arrays["next_obs"][start:end]
        episode_actions[eid, :count] = arrays["actions"][start:end]
        episode_rewards[eid, :count] = arrays["rewards"][start:end]
        episode_mask[eid, :count] = True
        episode_dones[eid, :count] = arrays["dones"][start:end]

    arrays.update(
        {
            "episode_obs": episode_obs,
            "episode_next_obs": episode_next_obs,
            "episode_actions": episode_actions,
            "episode_rewards": episode_rewards,
            "episode_mask": episode_mask,
            "episode_dones": episode_dones,
            "episode_lengths": np.asarray([row["row_count"] for row in episode_rows], dtype=np.int32),
            "episode_success": np.asarray([row["success"] for row in episode_rows], dtype=np.bool_),
            "episode_skill_ids": np.asarray([skill_to_id[row["skill_id"]] for row in episode_rows], dtype=np.int32),
            "episode_row_starts": np.asarray([row["row_start"] for row in episode_rows], dtype=np.int32),
            "episode_row_counts": np.asarray([row["row_count"] for row in episode_rows], dtype=np.int32),
            "skill_table": np.asarray(SKILL_TABLE, dtype=str),
            "phase_table": np.asarray(phase_table, dtype=str),
            "terminal_reason_table": np.asarray(terminal_table, dtype=str),
            "actuator_names": np.asarray(
                [
                    getattr(__import__("mujoco"), "mj_id2name")(model, getattr(__import__("mujoco"), "mjtObj").mjOBJ_ACTUATOR, i)
                    or f"actuator_{i}"
                    for i in range(model.nu)
                ],
                dtype=str,
            ),
            "actuator_ctrlrange": np.asarray(model.actuator_ctrlrange, dtype=np.float32),
            "actuator_ctrllimited": np.asarray(model.actuator_ctrllimited, dtype=np.bool_),
        }
    )

    training_mask = arrays["episode_success"].copy()
    training_rows = np.isin(arrays["episode_ids"], np.nonzero(training_mask)[0])
    obs_train = arrays["obs"][training_rows]
    action_train = arrays["actions"][training_rows]
    stats = {
        "obs_mean": obs_train.mean(axis=0).astype(np.float32),
        "obs_std": np.maximum(obs_train.std(axis=0), 1e-6).astype(np.float32),
        "action_mean": action_train.mean(axis=0).astype(np.float32),
        "action_std": np.maximum(action_train.std(axis=0), 1e-6).astype(np.float32),
        "action_min": action_train.min(axis=0).astype(np.float32),
        "action_max": action_train.max(axis=0).astype(np.float32),
    }
    arrays.update(stats)

    checks = readiness_checks(arrays, episode_rows, model)
    return arrays, episode_rows, checks


def readiness_checks(arrays: dict[str, np.ndarray], episode_rows: list[dict[str, Any]], model: Any) -> dict[str, Any]:
    episode_count = len(episode_rows)
    success_count = int(arrays["episode_success"].sum())
    per_skill = Counter(row["skill_id"] for row in episode_rows)
    per_skill_success = Counter(row["skill_id"] for row in episode_rows if row["success"])
    done_count_by_episode = Counter()
    for episode_id, done in zip(arrays["episode_ids"], arrays["dones"], strict=False):
        if bool(done):
            done_count_by_episode[int(episode_id)] += 1
    horizon_windows = {
        str(horizon): int(sum(max(0, int(row["row_count"]) - int(horizon) + 1) for row in episode_rows if row["success"]))
        for horizon in HORIZON_CANDIDATES
    }
    checks = {
        "episode_count": int(episode_count),
        "success_count": int(success_count),
        "total_rows": int(arrays["obs"].shape[0]),
        "obs_shape": list(arrays["obs"].shape),
        "actions_shape": list(arrays["actions"].shape),
        "padded_obs_shape": list(arrays["episode_obs"].shape),
        "padded_actions_shape": list(arrays["episode_actions"].shape),
        "finite_obs_actions": bool(np.isfinite(arrays["obs"]).all() and np.isfinite(arrays["actions"]).all() and np.isfinite(arrays["next_obs"]).all()),
        "one_done_per_episode": bool(all(done_count_by_episode.get(i, 0) == 1 for i in range(episode_count))),
        "action_range_ok": action_range_ok(model, arrays["actions"]),
        "per_skill_count": dict(per_skill),
        "per_skill_success": dict(per_skill_success),
        "horizon_windows": horizon_windows,
        "min_episode_length": int(arrays["episode_lengths"].min()),
        "max_episode_length": int(arrays["episode_lengths"].max()),
        "mean_episode_length": float(arrays["episode_lengths"].mean()),
    }
    checks["act_ready"] = bool(
        checks["finite_obs_actions"]
        and checks["one_done_per_episode"]
        and checks["action_range_ok"]
        and episode_count >= 40
        and success_count == episode_count
        and per_skill_success.get("full_hand_gentle_grasp", 0) >= 30
        and per_skill_success.get("thumb_index_middle_pinch", 0) >= 10
        and checks["horizon_windows"].get("16", 0) > 0
        and checks["horizon_windows"].get("32", 0) > 0
        and checks["horizon_windows"].get("64", 0) > 0
    )
    checks["dp_ready"] = bool(checks["act_ready"] and checks["horizon_windows"].get("128", 0) > 0)
    checks["act_dp_ready"] = bool(checks["act_ready"] and checks["dp_ready"])

    blockers: list[str] = []
    if episode_count < 40:
        blockers.append("canonical_episode_count_below_40")
    if success_count != episode_count:
        blockers.append("canonical_episode_failure_present")
    if per_skill_success.get("full_hand_gentle_grasp", 0) < 30:
        blockers.append("full_hand_success_count_below_30")
    if per_skill_success.get("thumb_index_middle_pinch", 0) < 10:
        blockers.append("pinch_success_count_below_10")
    for key in ("finite_obs_actions", "one_done_per_episode", "action_range_ok"):
        if not bool(checks[key]):
            blockers.append(key)
    if checks["horizon_windows"].get("64", 0) <= 0:
        blockers.append("no_64_step_training_windows")
    if checks["horizon_windows"].get("128", 0) <= 0:
        blockers.append("no_128_step_training_windows")
    checks["blockers"] = blockers
    return checks


def write_dataset(path: Path, arrays: dict[str, np.ndarray], checks: dict[str, Any], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        **arrays,
        task_name=np.asarray([TASK_NAME], dtype=str),
        contract_version=np.asarray([TASK_CONTRACT_VERSION], dtype=str),
        dataset_version=np.asarray(["stage3_skill_act_dp_sequence_dataset_v0"], dtype=str),
        scene=np.asarray([str(Path(args.scene).resolve())], dtype=str),
        collection_args_json=np.asarray([json.dumps(json_ready(vars(args)), ensure_ascii=False)], dtype=str),
        readiness_checks_json=np.asarray([json.dumps(json_ready(checks), ensure_ascii=False)], dtype=str),
        act_dp_ready=np.asarray([bool(checks["act_dp_ready"])], dtype=np.bool_),
    )


def write_jsonl(path: Path, episode_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in episode_rows:
            fh.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")


def write_metadata(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    c = payload["readiness_checks"]
    lines = [
        "# Stage3.9B3 ACT/DP Dense Sequence Dataset v0 报告\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{'PASS' if c['act_dp_ready'] else 'BLOCKED'}`\n",
        f"- ACT ready：`{c['act_ready']}`\n",
        f"- DP ready：`{c['dp_ready']}`\n",
        f"- ACT/DP ready：`{c['act_dp_ready']}`\n",
        f"- NPZ：`{payload['dataset']}`\n",
        f"- JSONL：`{payload['jsonl']}`\n",
        f"- metadata：`{payload['metadata']}`\n",
        f"- readiness definition：`{payload['readiness_definition']}`\n\n",
        "## 我们先怎么定义“能训练 ACT/DP”\n\n",
        "不是指模型已经训练成功，而是指下一步可以直接开始写/运行训练脚本。最低条件是：每个 timestep 有 `obs_t`、`action_t`、`next_obs_t`、`done_t`，所有 canonical episode 成功，action 合法，维度一致，且能按 horizon 切出训练窗口。\n\n",
        "## 数据规模\n\n",
        f"- episodes：`{c['episode_count']}`\n",
        f"- success：`{c['success_count']} / {c['episode_count']}`\n",
        f"- total rows：`{c['total_rows']}`\n",
        f"- obs shape：`{c['obs_shape']}`\n",
        f"- actions shape：`{c['actions_shape']}`\n",
        f"- padded obs shape：`{c['padded_obs_shape']}`\n",
        f"- padded actions shape：`{c['padded_actions_shape']}`\n",
        f"- episode length：min `{c['min_episode_length']}` / mean `{c['mean_episode_length']:.1f}` / max `{c['max_episode_length']}`\n\n",
        f"- diagnostic failed attempts：`{payload.get('diagnostic_attempt_count', 0)}`\n\n",
        "## 技能分布\n\n",
        "| skill | episodes | success |\n",
        "| --- | ---: | ---: |\n",
    ]
    for skill in SKILL_TABLE:
        lines.append(f"| `{skill}` | {c['per_skill_count'].get(skill, 0)} | {c['per_skill_success'].get(skill, 0)} |\n")
    lines.extend(["\n## Horizon 窗口检查\n\n", "| horizon | windows |\n", "| ---: | ---: |\n"])
    for horizon, windows in c["horizon_windows"].items():
        lines.append(f"| {horizon} | {windows} |\n")
    lines.extend(
        [
            "\n## Schema / 安全检查\n\n",
            f"- finite obs/actions/next_obs：`{c['finite_obs_actions']}`\n",
            f"- one done per episode：`{c['one_done_per_episode']}`\n",
            f"- action range ok：`{c['action_range_ok']}`\n",
            f"- blockers：`{c['blockers']}`\n\n",
            "## 失败 attempt 记录\n\n",
        ]
    )
    diagnostic_attempts = payload.get("diagnostic_attempts", [])
    if diagnostic_attempts:
        lines.extend(["| source ep | trial | reason | true lift | hold slip |\n", "| ---: | --- | --- | ---: | ---: |\n"])
        for item in diagnostic_attempts[:12]:
            summary = item.get("summary", {})
            lines.append(
                f"| {item.get('source_episode_id')} | `{item.get('trial')}` | `{item.get('terminal_reason')}` | "
                f"{float(summary.get('true_lift_height_m', math.nan)):.4f} | "
                f"{float(summary.get('hold_max_slip_score', math.nan)):.3f} |\n"
            )
        if len(diagnostic_attempts) > 12:
            lines.append(f"\n还有 `{len(diagnostic_attempts) - 12}` 条失败 attempt 详见 metadata。\n")
    else:
        lines.append("没有失败 attempt。\n")
    lines.extend(
        [
            "\n",
            "## 如果成功\n\n",
            "下一步进入 Stage3.9C/Stage3.10：写第一个 `train_stage3_act_dp_baseline_v0.py`，先做 dataloader + overfit smoke，再做 MuJoCo closed-loop eval。\n\n",
            "## 如果失败\n\n",
            "不训练模型。先看 blockers，修失败 episode、schema、action range 或 horizon 窗口问题。\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def collect_dense_episodes(args: argparse.Namespace) -> tuple[list[dict[str, Any]], Any, list[dict[str, Any]]]:
    import mujoco

    if str(args.device) == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    device = torch.device(str(args.device))
    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    policy, checkpoint = load_policy(Path(args.checkpoint), device)
    trials = sweep.trial_configs()
    episodes: list[dict[str, Any]] = []
    diagnostic_attempts: list[dict[str, Any]] = []

    r_args = full_hand_args(args)
    for local_id in range(int(args.full_hand_episodes)):
        trial = trials[local_id % len(trials)]
        row = recovery.run_recovery_episode(model, mujoco, policy, checkpoint, trial, local_id, r_args, device)
        row.update(
            {
                "skill_id": "full_hand_gentle_grasp",
                "source_stage": "Stage3.7D",
                "source_episode_id": int(local_id),
            }
        )
        episodes.append(row)
        summary = row.get("summary", {})
        print(
            f"full ep={local_id:03d} trial={trial.name} {row['status']} "
            f"rows={len(row.get('sequence_rows', {}).get('actions', []))} "
            f"lift={summary.get('final_lift_height_m', float('nan')):.4f} "
            f"hold_slip={summary.get('hold_max_slip_score', float('nan')):.3f}"
        )

    p_args = pinch_args(args)
    candidate = load_selected_pinch_candidate(Path(args.selected_pinch_config))
    pinch_successes = 0
    pinch_attempts = 0
    while pinch_successes < int(args.pinch_episodes) and pinch_attempts < int(args.pinch_max_attempts):
        trial = trials[pinch_successes % len(trials)]
        source_episode_id = int(args.pinch_source_episode_id_start) + int(pinch_attempts)
        row = pinch.run_pinch_episode(
            model,
            mujoco,
            candidate=candidate,
            trial=trial,
            episode_id=source_episode_id,
            args=p_args,
        )
        row.update(
            {
                "skill_id": "thumb_index_middle_pinch",
                "source_stage": "Stage3.8B",
                "source_episode_id": int(source_episode_id),
            }
        )
        summary = row.get("summary", {})
        row_count = len(row.get("sequence_rows", {}).get("actions", []))
        print(
            f"pinch attempt={pinch_attempts:03d} kept={pinch_successes:03d} "
            f"source_ep={source_episode_id:03d} candidate={candidate.name} trial={trial.name} {row['status']} "
            f"rows={row_count} "
            f"true_lift={summary.get('true_lift_height_m', float('nan')):.4f} "
            f"hold_slip={summary.get('hold_max_slip_score', float('nan')):.3f}"
        )
        if bool(row.get("success", False)):
            episodes.append(row)
            pinch_successes += 1
        else:
            diagnostic_attempts.append(
                {
                    "skill_id": "thumb_index_middle_pinch",
                    "source_episode_id": int(source_episode_id),
                    "trial": trial.name,
                    "candidate": candidate.name,
                    "terminal_reason": row.get("terminal_reason"),
                    "failure_reasons": row.get("failure_reasons", []),
                    "risk_flags": row.get("risk_flags", []),
                    "row_count": int(row_count),
                    "summary": summary,
                }
            )
        pinch_attempts += 1
    return episodes, model, diagnostic_attempts


def payload_from_run(
    args: argparse.Namespace,
    episodes: list[dict[str, Any]],
    checks: dict[str, Any],
    diagnostic_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.9B3",
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "scene": str(Path(args.scene).resolve()),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "selected_pinch_config": str(Path(args.selected_pinch_config).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "readiness_definition": str(Path(args.readiness_definition).resolve()),
        "readiness_checks": checks,
        "diagnostic_attempt_count": int(len(diagnostic_attempts)),
        "diagnostic_attempts": diagnostic_attempts,
        "episode_summaries": [
            {
                "episode_id": idx,
                "skill_id": row["skill_id"],
                "source_stage": row["source_stage"],
                "trial": row.get("trial"),
                "candidate": row.get("candidate"),
                "success": bool(row.get("success", False)),
                "terminal_reason": row.get("terminal_reason"),
                "row_count": len(row.get("sequence_rows", {}).get("actions", [])),
                "failure_reasons": row.get("failure_reasons", []),
                "risk_flags": row.get("risk_flags", []),
                "summary": row.get("summary", {}),
            }
            for idx, row in enumerate(episodes)
        ],
        "next_step_if_success_zh": "写 ACT/DP dataloader 和第一个训练 smoke，不再停留在数据整理。",
        "next_step_if_failure_zh": "先修失败 episode、schema 或 action range，不进入模型训练。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Stage3.9B3 dense ACT/DP-ready sequence dataset.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--selected-pinch-config", type=Path, default=DEFAULT_SELECTED_PINCH)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--readiness-definition", type=Path, default=DEFAULT_READINESS_DOC)
    parser.add_argument("--full-hand-episodes", type=int, default=30)
    parser.add_argument("--pinch-episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=170)
    parser.add_argument("--full-hand-random-offset-std", type=float, default=0.005)
    parser.add_argument("--pinch-random-offset-std", type=float, default=0.005)
    parser.add_argument("--pinch-seed", type=int, default=20230)
    parser.add_argument("--pinch-source-episode-id-start", type=int, default=78)
    parser.add_argument("--pinch-max-attempts", type=int, default=80)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    write_readiness_definition(Path(args.readiness_definition))
    episodes, model, diagnostic_attempts = collect_dense_episodes(args)
    arrays, episode_rows, checks = build_arrays(episodes, model)
    payload = payload_from_run(args, episodes, checks, diagnostic_attempts)
    write_dataset(Path(args.dataset), arrays, checks, args)
    write_jsonl(Path(args.jsonl), episode_rows)
    write_metadata(Path(args.metadata), payload)
    write_report(Path(args.report), payload)
    print(
        "Stage3.9B3 ACT/DP sequence dataset: "
        f"ready={checks['act_dp_ready']} episodes={checks['episode_count']} "
        f"success={checks['success_count']} rows={checks['total_rows']} "
        f"obs={checks['obs_shape']} actions={checks['actions_shape']}"
    )
    if checks["blockers"]:
        print(f"blockers={checks['blockers']}")
    print(f"dataset={Path(args.dataset).resolve()}")
    print(f"report={Path(args.report).resolve()}")
    return 0 if checks["act_dp_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
