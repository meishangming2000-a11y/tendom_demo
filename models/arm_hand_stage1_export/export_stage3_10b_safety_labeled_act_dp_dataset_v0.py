#!/usr/bin/env python3
"""Export Stage3.10B safety-labeled ACT/DP sequence data.

This exporter runs the frozen Stage3.10A safety layer in MuJoCo with dense
sequence capture enabled. It keeps the old ACT/DP obs/action surface, then adds
row-level safety labels for recovery, pinch repair, final-verification
corroboration, and tactile risk.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CONFIGS = ROOT / "configs"

DEFAULT_CONFIG = CONFIGS / "stage3_10a_skillzoo_safety_layer_v0.json"
DEFAULT_DATASET = DATA / "stage3_10b_safety_labeled_act_dp_dataset_v0.npz"
DEFAULT_JSONL = DATA / "stage3_10b_safety_labeled_act_dp_dataset_v0.jsonl"
DEFAULT_METADATA = META / "stage3_10b_safety_labeled_act_dp_dataset_v0.json"
DEFAULT_REPORT = DOCS / "stage3_10b_safety_labeled_act_dp_dataset_v0_report.md"
DEFAULT_DATASET_VERSION = "stage3_10b_safety_labeled_act_dp_dataset_v0"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import eval_stage3_act_lite_chunk_policy_v0 as act_eval
import eval_stage3_contact_transition_recovery_v0 as recovery
import export_stage3_skill_act_dp_sequence_dataset_v0 as base_export


SAFETY_INTERVENTION_TABLE = (
    "none",
    "full_hand_recovery",
    "pinch_repair",
    "final_vision_corroboration",
)


def rel_or_abs(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def rows_array(rows: dict[str, list[Any]], key: str, dtype: Any, *, length: int, default: Any = None) -> np.ndarray:
    values = rows.get(key)
    if values is None:
        values = [default for _ in range(length)]
    return np.asarray(values, dtype=dtype)


def make_eval_args(args: argparse.Namespace, config: dict[str, Any]) -> argparse.Namespace:
    full_hand = config["control_stack"]["full_hand_gentle_grasp"]
    pinch = config["control_stack"]["thumb_index_middle_pinch"]
    final = config["control_stack"]["final_verification"]
    canonical = config["canonical_eval"]
    return argparse.Namespace(
        checkpoint=rel_or_abs(canonical["checkpoint"]),
        scene=Path(args.scene),
        selected_pinch_config=rel_or_abs(canonical["selected_pinch_config"]),
        report=Path(args.report),
        metadata=Path(args.metadata),
        skills="full_hand_gentle_grasp,thumb_index_middle_pinch",
        trials=str(args.trials),
        episodes_per_skill=int(args.episodes_per_skill),
        execution_mode="scripted_arm_predicted_hand",
        replan_interval=int(args.replan_interval),
        hand_start_index=6,
        full_hand_control_mode="stage3_7d_fallback",
        full_hand_fallback_checkpoint=rel_or_abs(full_hand["checkpoint"]),
        full_hand_fallback_transition_slip_threshold=float(full_hand["transition_slip_threshold"]),
        full_hand_fallback_max_transition_hold_steps_per_phase=int(full_hand["max_transition_hold_steps_per_phase"]),
        full_hand_fallback_recovery_progress_drop=float(full_hand["recovery_progress_drop"]),
        full_hand_fallback_recovery_stable_window_steps=int(full_hand["recovery_stable_window_steps"]),
        pinch_repair_mode=str(pinch["repair_mode"]),
        pinch_repair_phases=",".join(str(item) for item in pinch["repair_phases"]),
        pinch_repair_slip_threshold=float(args.pinch_repair_slip_threshold),
        pinch_repair_inactive_alpha=float(pinch["repair_inactive_alpha"]),
        pinch_repair_expert_alpha=0.20,
        pinch_repair_close_gain=float(pinch["repair_close_gain"]),
        pinch_repair_close_max=float(pinch["repair_close_max"]),
        pinch_repair_preclose_delta=float(pinch["repair_preclose_delta"]),
        pinch_repair_max_crush=float(pinch["repair_max_crush"]),
        pinch_repair_max_penetration=float(pinch["repair_max_penetration"]),
        pinch_final_verification_mode=str(final["pinch_mode"]),
        pinch_final_corroboration_min_confidence=float(final["min_corroboration_confidence"]),
        pinch_final_corroboration_min_mask_pixels=int(final["min_corroboration_mask_pixels"]),
        seed=int(args.seed),
        random_offset_std=float(args.random_offset_std),
        camera=str(config["control_stack"]["vision"]["camera"]),
        width=int(args.width),
        height=int(args.height),
        sample_every=int(args.sample_every),
        device=str(args.device),
        capture_sequence=True,
    )


def collect_episodes(eval_args: argparse.Namespace) -> tuple[list[dict[str, Any]], Any]:
    import mujoco

    if eval_args.device == "cuda" and not torch.cuda.is_available():
        eval_args.device = "cpu"
    device = torch.device(str(eval_args.device))
    policy, checkpoint = act_eval.load_chunk_policy(Path(eval_args.checkpoint), device)
    fallback_policy, fallback_checkpoint = recovery.load_policy(Path(eval_args.full_hand_fallback_checkpoint), device)
    model = mujoco.MjModel.from_xml_path(str(Path(eval_args.scene).resolve()))
    candidate = act_eval.load_selected_pinch_candidate(Path(eval_args.selected_pinch_config))
    skills = [item.strip() for item in str(eval_args.skills).split(",") if item.strip()]
    trials = act_eval.select_trials(str(eval_args.trials), int(eval_args.episodes_per_skill))

    rows: list[dict[str, Any]] = []
    episode_id = 0
    for skill in skills:
        for local_idx in range(int(eval_args.episodes_per_skill)):
            trial = trials[local_idx % len(trials)]
            if skill == "full_hand_gentle_grasp":
                row = act_eval.run_full_hand_fallback_episode(
                    model=model,
                    mujoco=mujoco,
                    fallback_policy=fallback_policy,
                    fallback_checkpoint=fallback_checkpoint,
                    trial=trial,
                    episode_id=episode_id,
                    args=eval_args,
                    device=device,
                )
                row["source_stage"] = "Stage3.10A-full_hand_fallback"
            else:
                row = act_eval.run_pinch_episode(
                    model=model,
                    mujoco=mujoco,
                    policy=policy,
                    checkpoint=checkpoint,
                    candidate=candidate,
                    trial=trial,
                    episode_id=episode_id,
                    args=eval_args,
                    device=device,
                )
                row["source_stage"] = "Stage3.10A-act_lite_pinch_repair"
            row["source_episode_id"] = int(episode_id)
            row_count = len(row.get("sequence_rows", {}).get("actions", []))
            summary = row.get("summary", {})
            lift = summary.get("final_lift_height_m", summary.get("true_lift_height_m", float("nan")))
            print(
                f"ep={episode_id:03d} skill={skill} trial={trial.name} {row['status']} "
                f"rows={row_count} lift={float(lift):.4f} "
                f"hold_slip={float(summary.get('hold_max_slip_score', float('nan'))):.3f}"
            )
            rows.append(row)
            episode_id += 1
    return rows, model


def concatenate_sequence_key(episodes: list[dict[str, Any]], key: str, dtype: Any, default: Any) -> np.ndarray:
    chunks: list[np.ndarray] = []
    for episode in episodes:
        rows = episode.get("sequence_rows", {})
        length = len(rows.get("actions", []))
        chunks.append(rows_array(rows, key, dtype, length=length, default=default))
    return np.concatenate(chunks, axis=0) if chunks else np.asarray([], dtype=dtype)


def add_safety_arrays(arrays: dict[str, np.ndarray], episodes: list[dict[str, Any]], episode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    thresholds = Stage3Thresholds()
    repair_active = concatenate_sequence_key(episodes, "repair_active", np.bool_, False)
    repair_close_delta = concatenate_sequence_key(episodes, "repair_close_delta", np.float32, 0.0)
    repair_expert_alpha = concatenate_sequence_key(episodes, "repair_expert_alpha", np.float32, 0.0)
    repair_inactive_alpha = concatenate_sequence_key(episodes, "repair_inactive_alpha", np.float32, 0.0)
    explicit_safety = concatenate_sequence_key(episodes, "safety_intervention_active", np.bool_, False)
    recovery_active = np.asarray(arrays.get("recovery_active", np.zeros_like(repair_active)), dtype=np.bool_)

    safety_active = np.logical_or.reduce((explicit_safety, recovery_active, repair_active))
    safety_type_ids = np.zeros(safety_active.shape[0], dtype=np.int32)
    safety_type_ids[recovery_active] = 1
    safety_type_ids[repair_active] = 2

    episode_final_corroborated = np.zeros(len(episode_rows), dtype=np.bool_)
    for row in episode_rows:
        eid = int(row["episode_id"])
        summary = row.get("summary", {})
        corroborated = bool(summary.get("final_vision_corroborated", False))
        episode_final_corroborated[eid] = corroborated
        if corroborated and int(row["row_count"]) > 0:
            idx = int(row["row_start"]) + int(row["row_count"]) - 1
            safety_active[idx] = True
            safety_type_ids[idx] = 3

    tactile = np.asarray(arrays["tactile_scalars"], dtype=np.float32)
    slip = tactile[:, 4]
    crush = tactile[:, 6]
    floor_contact = tactile[:, 9]
    penetration = tactile[:, 10]
    phase_names = np.asarray(arrays["phase_table"], dtype=str)[np.asarray(arrays["phase_ids"], dtype=np.int32)]
    post_lift_phase = np.isin(phase_names, np.asarray(["slow_lift", "hold"], dtype=str))
    risk_slip_high = slip > float(thresholds.success_max_slip_score)
    risk_crush_high = crush > float(thresholds.success_max_crush_risk)
    risk_penetration_high = penetration > float(thresholds.success_max_penetration_m)
    risk_floor_contact = np.logical_and(floor_contact > 0.0, post_lift_phase)
    risk_any = np.logical_or.reduce((risk_slip_high, risk_crush_high, risk_penetration_high, risk_floor_contact))
    safety_labels = np.stack(
        [
            np.asarray(arrays["learned_hand"], dtype=np.float32),
            recovery_active.astype(np.float32),
            repair_active.astype(np.float32),
            safety_active.astype(np.float32),
            risk_slip_high.astype(np.float32),
            risk_crush_high.astype(np.float32),
            risk_penetration_high.astype(np.float32),
            risk_floor_contact.astype(np.float32),
            risk_any.astype(np.float32),
        ],
        axis=1,
    ).astype(np.float32)

    episode_has_safety = np.zeros(len(episode_rows), dtype=np.bool_)
    episode_has_risk = np.zeros(len(episode_rows), dtype=np.bool_)
    for row in episode_rows:
        eid = int(row["episode_id"])
        start = int(row["row_start"])
        end = start + int(row["row_count"])
        episode_has_safety[eid] = bool(safety_active[start:end].any())
        episode_has_risk[eid] = bool(risk_any[start:end].any())
        row["safety_intervention_steps"] = int(safety_active[start:end].sum())
        row["repair_steps"] = int(repair_active[start:end].sum())
        row["recovery_steps_from_rows"] = int(recovery_active[start:end].sum())
        row["risk_label_steps"] = int(risk_any[start:end].sum())
        row["final_vision_corroborated"] = bool(episode_final_corroborated[eid])

    arrays.update(
        {
            "repair_active": repair_active,
            "repair_close_delta": repair_close_delta,
            "repair_expert_alpha": repair_expert_alpha,
            "repair_inactive_alpha": repair_inactive_alpha,
            "safety_intervention_active": safety_active.astype(np.bool_),
            "safety_intervention_type_ids": safety_type_ids,
            "safety_intervention_type_table": np.asarray(SAFETY_INTERVENTION_TABLE, dtype=str),
            "risk_slip_high": risk_slip_high.astype(np.bool_),
            "risk_crush_high": risk_crush_high.astype(np.bool_),
            "risk_penetration_high": risk_penetration_high.astype(np.bool_),
            "risk_floor_contact": risk_floor_contact.astype(np.bool_),
            "risk_any": risk_any.astype(np.bool_),
            "safety_labels": safety_labels,
            "episode_has_safety_intervention": episode_has_safety,
            "episode_has_risk_label": episode_has_risk,
            "episode_final_vision_corroborated": episode_final_corroborated,
        }
    )

    safety_checks = {
        "row_count": int(safety_active.shape[0]),
        "safety_intervention_steps": int(safety_active.sum()),
        "recovery_steps": int(recovery_active.sum()),
        "repair_steps": int(repair_active.sum()),
        "final_vision_corroborated_episodes": int(episode_final_corroborated.sum()),
        "risk_label_steps": int(risk_any.sum()),
        "risk_slip_high_steps": int(risk_slip_high.sum()),
        "episode_with_safety_intervention": int(episode_has_safety.sum()),
        "episode_with_risk_label": int(episode_has_risk.sum()),
        "safety_label_shape": list(safety_labels.shape),
    }
    safety_checks["safety_schema_ready"] = bool(
        safety_checks["row_count"] > 0
        and safety_checks["safety_intervention_steps"] > 0
        and safety_checks["risk_label_steps"] > 0
        and list(safety_labels.shape)[1] == 9
    )
    return safety_checks


def write_dataset(path: Path, arrays: dict[str, np.ndarray], payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        **arrays,
        dataset_version=np.asarray([str(payload["dataset_version"])], dtype=str),
        experiment_name=np.asarray([str(payload["experiment_name"])], dtype=str),
        stage=np.asarray(["Stage3.10B"], dtype=str),
        metadata_json=np.asarray([json.dumps(json_ready(payload), ensure_ascii=False)], dtype=str),
    )


def write_jsonl(path: Path, episode_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in episode_rows:
            fh.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    checks = payload["readiness_checks"]
    safety = payload["safety_checks"]
    lines = [
        "# Stage3.10B Safety-Labeled ACT/DP Dataset v0 Report\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{'PASS' if payload['stage3_10b_smoke_ready'] else 'BLOCKED'}`\n",
        f"- NPZ：`{payload['dataset']}`\n",
        f"- JSONL：`{payload['jsonl']}`\n",
        f"- metadata：`{payload['metadata']}`\n",
        f"- safety layer config：`{payload['safety_layer_config']}`\n\n",
        "## 这一步做了什么\n\n",
        "Stage3.10B 的第一步不是训练模型，而是把 Stage3.10A 冻结的 safety layer 跑成可训练数据。这个数据仍保留 `obs/action/next_obs/done/skill/phase`，同时新增 safety 标签，告诉后续模型哪些时刻发生了触觉恢复、捏持 repair、最终视觉/触觉佐证和滑移风险。\n\n",
        "## 数据规模\n\n",
        f"- episodes：`{checks['episode_count']}`\n",
        f"- success：`{checks['success_count']} / {checks['episode_count']}`\n",
        f"- total rows：`{checks['total_rows']}`\n",
        f"- obs shape：`{checks['obs_shape']}`\n",
        f"- actions shape：`{checks['actions_shape']}`\n",
        f"- padded obs shape：`{checks['padded_obs_shape']}`\n",
        f"- padded actions shape：`{checks['padded_actions_shape']}`\n\n",
        "## Safety 标签\n\n",
        f"- safety label shape：`{safety['safety_label_shape']}`\n",
        f"- safety intervention steps：`{safety['safety_intervention_steps']}`\n",
        f"- full-hand recovery steps：`{safety['recovery_steps']}`\n",
        f"- pinch repair steps：`{safety['repair_steps']}`\n",
        f"- final vision corroborated episodes：`{safety['final_vision_corroborated_episodes']}`\n",
        f"- risk label steps：`{safety['risk_label_steps']}`\n",
        f"- slip-high steps：`{safety['risk_slip_high_steps']}`\n",
        f"- episodes with safety intervention：`{safety['episode_with_safety_intervention']}`\n",
        f"- episodes with risk label：`{safety['episode_with_risk_label']}`\n\n",
        "## 技能分布\n\n",
        "| skill | episodes | success |\n",
        "| --- | ---: | ---: |\n",
    ]
    for skill, count in checks["per_skill_count"].items():
        lines.append(f"| `{skill}` | {count} | {checks['per_skill_success'].get(skill, 0)} |\n")
    lines.extend(
        [
            "\n## 验收\n\n",
            f"- finite obs/action：`{checks['finite_obs_actions']}`\n",
            f"- one done per episode：`{checks['one_done_per_episode']}`\n",
            f"- action range ok：`{checks['action_range_ok']}`\n",
            f"- safety schema ready：`{safety['safety_schema_ready']}`\n",
            f"- blockers：`{payload['blockers']}`\n\n",
            "注意：本轮默认是 Stage3.10B smoke/seed 数据，不声称已经完成大规模 ACT/DP 训练集。完整数据扩展要继续把 `--episodes-per-skill` 放大，并加入更多 pose-noise、遮挡和失败场景。\n\n",
            "## 如果成功\n\n",
            "下一步进入 Stage3.10B-full：扩大采集规模，并把这个 schema 固化为正式 ACT/CVAE 或 Diffusion Policy dataloader 的输入。\n\n",
            "## 如果失败\n\n",
            "先修 sequence capture、safety 标签或 action range；不进入模型训练，也不回到 Stage3.9 小参数微调。\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    checks = payload["readiness_checks"]
    safety = payload["safety_checks"]
    lines = [
        f"# {payload['experiment_name']} Report\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- schema/smoke 状态：`{'PASS' if payload['stage3_10b_smoke_ready'] else 'BLOCKED'}`\n",
        f"- 训练前数据状态：`{'READY' if payload['stage3_10b_train_ready'] else 'NOT_READY'}`\n",
        f"- dataset version：`{payload['dataset_version']}`\n",
        f"- NPZ：`{payload['dataset']}`\n",
        f"- JSONL：`{payload['jsonl']}`\n",
        f"- metadata：`{payload['metadata']}`\n",
        f"- safety layer config：`{payload['safety_layer_config']}`\n\n",
        "## 这一步做了什么\n\n",
        "这一步把 Stage3.10A 冻结的 safety layer 跑成可训练序列数据。数据保留 `obs/action/next_obs/done/skill/phase`，同时加入 safety 标签，用来记录 full-hand recovery、pinch repair、最终视觉/触觉校验和触觉风险。\n\n",
        "## 数据规模\n\n",
        f"- episodes：`{checks['episode_count']}`\n",
        f"- success：`{checks['success_count']} / {checks['episode_count']}`\n",
        f"- total rows：`{checks['total_rows']}`\n",
        f"- obs shape：`{checks['obs_shape']}`\n",
        f"- actions shape：`{checks['actions_shape']}`\n",
        f"- padded obs shape：`{checks['padded_obs_shape']}`\n",
        f"- padded actions shape：`{checks['padded_actions_shape']}`\n\n",
        "## Safety 标签\n\n",
        f"- safety label shape：`{safety['safety_label_shape']}`\n",
        f"- safety intervention steps：`{safety['safety_intervention_steps']}`\n",
        f"- full-hand recovery steps：`{safety['recovery_steps']}`\n",
        f"- pinch repair steps：`{safety['repair_steps']}`\n",
        f"- final vision corroborated episodes：`{safety['final_vision_corroborated_episodes']}`\n",
        f"- risk label steps：`{safety['risk_label_steps']}`\n",
        f"- slip-high steps：`{safety['risk_slip_high_steps']}`\n",
        f"- episodes with safety intervention：`{safety['episode_with_safety_intervention']}`\n",
        f"- episodes with risk label：`{safety['episode_with_risk_label']}`\n\n",
        "## 技能分布\n\n",
        "| skill | episodes | success |\n",
        "| --- | ---: | ---: |\n",
    ]
    for skill, count in checks["per_skill_count"].items():
        lines.append(f"| `{skill}` | {count} | {checks['per_skill_success'].get(skill, 0)} |\n")
    lines.extend(
        [
            "\n## 验收\n\n",
            f"- finite obs/action：`{checks['finite_obs_actions']}`\n",
            f"- one done per episode：`{checks['one_done_per_episode']}`\n",
            f"- action range ok：`{checks['action_range_ok']}`\n",
            f"- old ACT ready gate：`{checks['act_ready']}`\n",
            f"- old DP ready gate：`{checks['dp_ready']}`\n",
            f"- old ACT/DP ready gate：`{checks['act_dp_ready']}`\n",
            f"- safety schema ready：`{safety['safety_schema_ready']}`\n",
            f"- smoke blockers：`{payload['blockers']}`\n",
            f"- train-readiness blockers：`{payload['train_readiness_blockers']}`\n\n",
            "说明：`stage3_10b_smoke_ready` 只表示采集链路和 safety schema 跑通；`stage3_10b_train_ready` 才表示规模、成功率和 safety 标签都足够进入下一步 ACT/CVAE 或 DP 训练准备。\n\n",
            "## 如果成功\n\n",
            "进入 Stage3.10C：把这份 safety-labeled 数据接到正式 ACT Transformer/CVAE 或 Diffusion Policy dataloader，并和 Stage3.10A safety layer 做同场景闭环对比。\n\n",
            "## 如果失败\n\n",
            "先看失败属于规模不足、episode 失败、sequence capture 错误、动作越界，还是 safety/risk 标签太稀疏；只修对应问题，不回到 Stage3.9 的小参数微调。\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--dataset-version", default=DEFAULT_DATASET_VERSION)
    parser.add_argument("--experiment-name", default="Stage3.10B Safety-Labeled ACT/DP Dataset v0")
    parser.add_argument("--episodes-per-skill", type=int, default=5)
    parser.add_argument("--trials", default="cycle")
    parser.add_argument("--seed", type=int, default=3100)
    parser.add_argument("--random-offset-std", type=float, default=0.005)
    parser.add_argument("--replan-interval", type=int, default=16)
    parser.add_argument("--pinch-repair-slip-threshold", type=float, default=0.28)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--sample-every", type=int, default=240)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    eval_args = make_eval_args(args, config)
    episodes, model = collect_episodes(eval_args)
    arrays, episode_rows, checks = base_export.build_arrays(episodes, model)
    safety_checks = add_safety_arrays(arrays, episodes, episode_rows)

    blockers: list[str] = []
    if checks["success_count"] != checks["episode_count"]:
        blockers.append("episode_failure_present")
    for key in ("finite_obs_actions", "one_done_per_episode", "action_range_ok"):
        if not bool(checks[key]):
            blockers.append(key)
    if not bool(safety_checks["safety_schema_ready"]):
        blockers.append("safety_schema_not_ready")
    train_readiness_blockers = list(checks.get("blockers", []))
    if not bool(safety_checks["safety_schema_ready"]):
        train_readiness_blockers.append("safety_schema_not_ready")

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.10B",
        "experiment_name": str(args.experiment_name),
        "dataset_version": str(args.dataset_version),
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "safety_layer_config": str(Path(args.config).resolve()),
        "eval_args": vars(eval_args),
        "readiness_checks": checks,
        "safety_checks": safety_checks,
        "stage3_10b_smoke_ready": bool(not blockers),
        "stage3_10b_train_ready": bool(
            not blockers
            and not train_readiness_blockers
            and bool(checks.get("act_dp_ready", False))
            and bool(safety_checks["safety_schema_ready"])
        ),
        "blockers": blockers,
        "train_readiness_blockers": train_readiness_blockers,
        "episode_summaries": episode_rows,
        "boundary": "MuJoCo-only safety-labeled data export; not full-action ACT/DP success and not hardware integration.",
    }
    write_dataset(Path(args.dataset), arrays, payload)
    write_jsonl(Path(args.jsonl), episode_rows)
    Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metadata).write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(Path(args.report), payload)

    print(
        "Stage3.10B safety-labeled dataset: "
        f"ready={payload['stage3_10b_smoke_ready']} "
        f"train_ready={payload['stage3_10b_train_ready']} "
        f"episodes={checks['episode_count']} success={checks['success_count']} "
        f"rows={checks['total_rows']} safety_steps={safety_checks['safety_intervention_steps']} "
        f"risk_steps={safety_checks['risk_label_steps']}"
    )
    print(f"dataset={Path(args.dataset).resolve()}")
    print(f"report={Path(args.report).resolve()}")
    if blockers:
        print(f"blockers={blockers}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
