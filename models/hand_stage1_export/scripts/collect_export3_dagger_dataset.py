from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from collect_export3_scripted_dataset import (
    DEFAULT_DATASET as BASE_DATASET,
    STAGE_NAMES,
    action_vector,
    ball_body_position,
    build_configs,
    make_feature_names,
    observation_vector,
)
from eval_export3_bc import load_policy, policy_action
from export3_common import (
    CONTROLLED_JOINTS,
    DOCS_DIR,
    METADATA_DIR,
    ROOT,
    SCENE_XML,
    actuator_map,
    blend,
    joint_map,
    load_model,
    set_ball_position,
    set_ctrl,
    stage_summary,
)
from run_export3_shadow_style_scripted_task import (
    MODES,
    STAGE_ORDER,
    TrialConfig,
    classify_trial,
    scaled_targets,
    stage_steps,
)
from train_export3_bc import parse_class_filter


DATA_DIR = ROOT / "data"
CHECKPOINT_DIR = ROOT / "checkpoints"
DEFAULT_MODEL = CHECKPOINT_DIR / "bc_hand_stage1_export3_pinned_wrap_v0.pth"
DEFAULT_OUTPUT = DATA_DIR / "export3_dagger_pinned_wrap_v1.npz"
DEFAULT_REPORT = DOCS_DIR / "export3_dagger_dataset_v1_report.md"
DEFAULT_METADATA = METADATA_DIR / "export3_dagger_dataset_v1.json"

DAGGER_CLASS = "DAGGER_CORRECTION"


def reset_state(model, data, mujoco, config: TrialConfig) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, list(config.ball_position))
    mujoco.mj_forward(model, data)


def load_base_samples(path: Path, class_filter: str) -> dict[str, np.ndarray | list[str]]:
    data = np.load(path, allow_pickle=True)
    class_names = [str(x) for x in data["class_names"].tolist()]
    filters = parse_class_filter(class_filter)
    if filters:
        missing = [name for name in filters if name not in class_names]
        if missing:
            raise ValueError(f"Missing base classes {missing!r}; available={class_names}")
        class_ids = {class_names.index(name) for name in filters}
        mask = np.array([int(value) in class_ids for value in data["sample_class"].astype(np.int16)], dtype=bool)
        episode_mask_ids = {int(i) for i, value in enumerate(data["episode_class"].astype(np.int16)) if int(value) in class_ids}
    else:
        mask = np.ones(data["observations"].shape[0], dtype=bool)
        episode_mask_ids = set(int(i) for i in np.unique(data["episode_id"]))
    episode_id = data["episode_id"].astype(np.int32)[mask]
    unique_old = sorted(set(int(x) for x in episode_id))
    remap = {old: idx for idx, old in enumerate(unique_old)}
    return {
        "observations": data["observations"].astype(np.float32)[mask],
        "actions": data["actions"].astype(np.float32)[mask],
        "episode_id": np.array([remap[int(x)] for x in episode_id], dtype=np.int32),
        "stage_id": data["stage_id"].astype(np.int16)[mask],
        "step_in_stage": data["step_in_stage"].astype(np.int16)[mask],
        "mode_id": data["mode_id"].astype(np.int16)[mask],
        "episode_count": len(unique_old),
        "feature_names": [str(x) for x in data["feature_names"].tolist()],
        "action_names": [str(x) for x in data["action_names"].tolist()],
        "stage_names": [str(x) for x in data["stage_names"].tolist()],
        "mode_names": [str(x) for x in data["mode_names"].tolist()],
        "episode_mask_ids": sorted(episode_mask_ids),
    }


def clip_action(model, act_map: dict[str, int], command: dict[str, float]) -> dict[str, float]:
    clipped = {}
    for name, value in command.items():
        aid = act_map.get(name)
        if aid is None:
            continue
        low, high = [float(v) for v in model.actuator_ctrlrange[aid]]
        clipped[name] = min(max(float(value), low), high)
    return clipped


def collect_dagger_episode(
    mujoco,
    model,
    data,
    policy,
    checkpoint: dict,
    device: torch.device,
    config: TrialConfig,
    episode_id: int,
    speed: float,
    step_stride: int,
    execute_expert_mix: float,
    arrays: dict[str, list] | None = None,
) -> tuple[dict, dict[str, list]]:
    local_arrays = {key: [] for key in ["observations", "actions", "episode_id", "stage_id", "step_in_stage", "mode_id"]}
    model.opt.gravity[:] = [0.0, 0.0, -9.81] if config.mode == "free_gravity" else [0.0, 0.0, 0.0]
    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    reset_state(model, data, mujoco, config)

    previous_scripted = scaled_targets("open_hand", config.finger_scale, dict(config.thumb_pose))
    previous_ctrl = np.zeros(len(CONTROLLED_JOINTS), dtype=np.float32)
    stages = {}
    sample_count = 0

    for stage_index, stage in enumerate(STAGE_NAMES):
        scripted_target = scaled_targets(stage, config.finger_scale, dict(config.thumb_pose))
        steps = stage_steps(stage, speed)
        applied = {}
        for step in range(max(steps, 1)):
            fraction = (step + 1) / max(steps, 1)
            expert_command = clip_action(model, act_map, blend(previous_scripted, scripted_target, fraction))
            obs = observation_vector(model, data, mujoco, joints, previous_ctrl, fraction, stage_index, config)
            expert_vec = action_vector(expert_command)
            student_vec = policy_action(policy, checkpoint, obs, device)
            exec_vec = (1.0 - execute_expert_mix) * student_vec + execute_expert_mix * expert_vec
            applied = set_ctrl(model, data, {name: float(exec_vec[idx]) for idx, name in enumerate(CONTROLLED_JOINTS)}, act_map)
            previous_ctrl = np.array([float(applied.get(name, previous_ctrl[idx])) for idx, name in enumerate(CONTROLLED_JOINTS)], dtype=np.float32)
            set_ball_position(model, data, mujoco, list(config.ball_position))
            mujoco.mj_step(model, data)
            if step % max(step_stride, 1) == 0 or step == steps - 1:
                local_arrays["observations"].append(obs)
                local_arrays["actions"].append(expert_vec)
                local_arrays["episode_id"].append(episode_id)
                local_arrays["stage_id"].append(stage_index)
                local_arrays["step_in_stage"].append(step)
                local_arrays["mode_id"].append(MODES.index(config.mode))
                sample_count += 1
        set_ball_position(model, data, mujoco, list(config.ball_position))
        mujoco.mj_forward(model, data)
        stages[stage] = stage_summary(model, data, mujoco, joints, scripted_target, applied)
        stages[stage]["ball_body_position"] = ball_body_position(model, data, mujoco).tolist()
        previous_scripted = scripted_target

    result = {
        "mode": config.mode,
        "ball_position": list(config.ball_position),
        "finger_scale": config.finger_scale,
        "thumb_rank": config.thumb_rank,
        "thumb_pose": dict(config.thumb_pose),
        "stages": stages,
        "release": None,
    }
    result["classification"] = classify_trial(result)
    result["sample_count"] = sample_count
    if arrays is not None:
        for key, values in local_arrays.items():
            arrays[key].extend(values)
    return result, local_arrays


def append_arrays(target: dict[str, list], source: dict[str, list]) -> None:
    for key, values in source.items():
        target[key].extend(values)


def save_combined_dataset(output: Path, base: dict, arrays: dict[str, list], dagger_results: list[dict], metadata: dict) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    base_obs = np.asarray(base["observations"], dtype=np.float32)
    dagger_obs = np.stack(arrays["observations"]).astype(np.float32) if arrays["observations"] else np.zeros((0, base_obs.shape[1]), dtype=np.float32)
    base_actions = np.asarray(base["actions"], dtype=np.float32)
    dagger_actions = np.stack(arrays["actions"]).astype(np.float32) if arrays["actions"] else np.zeros((0, base_actions.shape[1]), dtype=np.float32)
    observations = np.concatenate([base_obs, dagger_obs], axis=0)
    actions = np.concatenate([base_actions, dagger_actions], axis=0)

    base_episode_count = int(base["episode_count"])
    base_episode_id = np.asarray(base["episode_id"], dtype=np.int32)
    dagger_episode_id = np.asarray(arrays["episode_id"], dtype=np.int32) if arrays["episode_id"] else np.zeros((0,), dtype=np.int32)
    episode_id = np.concatenate([base_episode_id, dagger_episode_id], axis=0)
    stage_id = np.concatenate([np.asarray(base["stage_id"], dtype=np.int16), np.asarray(arrays["stage_id"], dtype=np.int16)], axis=0)
    step_in_stage = np.concatenate([np.asarray(base["step_in_stage"], dtype=np.int16), np.asarray(arrays["step_in_stage"], dtype=np.int16)], axis=0)
    mode_id = np.concatenate([np.asarray(base["mode_id"], dtype=np.int16), np.asarray(arrays["mode_id"], dtype=np.int16)], axis=0)

    class_names = ["PINNED_WRAP_PASS", DAGGER_CLASS]
    base_sample_class = np.zeros(base_obs.shape[0], dtype=np.int16)
    dagger_sample_class = np.ones(dagger_obs.shape[0], dtype=np.int16)
    sample_class = np.concatenate([base_sample_class, dagger_sample_class], axis=0)
    kept_dagger_episode_ids = sorted(set(int(item) for item in dagger_episode_id.tolist()))
    max_episode_id = max([base_episode_count - 1, *kept_dagger_episode_ids]) if base_episode_count else max(kept_dagger_episode_ids, default=-1)
    episode_class = np.zeros(max_episode_id + 1, dtype=np.int16)
    for episode in kept_dagger_episode_ids:
        episode_class[episode] = 1

    np.savez_compressed(
        output,
        observations=observations,
        actions=actions,
        episode_id=episode_id,
        stage_id=stage_id,
        step_in_stage=step_in_stage,
        mode_id=mode_id,
        episode_class=episode_class,
        sample_class=sample_class,
        feature_names=np.array(base["feature_names"], dtype=object),
        action_names=np.array(base["action_names"], dtype=object),
        stage_names=np.array(base["stage_names"], dtype=object),
        mode_names=np.array(base["mode_names"], dtype=object),
        class_names=np.array(class_names, dtype=object),
    )
    metadata["dataset_shape"] = {
        "observations": list(observations.shape),
        "actions": list(actions.shape),
        "base_samples": int(base_obs.shape[0]),
        "dagger_samples": int(dagger_obs.shape[0]),
        "base_episodes": base_episode_count,
        "dagger_episodes": len(kept_dagger_episode_ids),
        "dagger_episodes_collected": len(dagger_results),
        "dagger_episode_ids_kept": kept_dagger_episode_ids,
    }
    return metadata


def write_report(path: Path, metadata: dict, dagger_results: list[dict]) -> None:
    counts = Counter(item["classification"] for item in dagger_results)
    kept_counts = Counter(item["classification"] for item in dagger_results if item.get("kept_as_correction"))
    lines = [
        "# Export3 DAgger Dataset v1 Report",
        "",
        "Status: diagnostic DAgger correction dataset, not a promoted stable_grasp baseline.",
        "",
        f"- Base dataset: `{metadata['base_dataset']}`",
        f"- Policy used for on-policy states: `{metadata['policy_checkpoint']}`",
        f"- Output dataset: `{metadata['dataset_path']}`",
        f"- Metadata: `{metadata['metadata_path']}`",
        f"- Base samples retained: {metadata['dataset_shape']['base_samples']}",
        f"- DAgger correction samples: {metadata['dataset_shape']['dagger_samples']}",
        f"- DAgger rollout episodes collected: {metadata['dataset_shape']['dagger_episodes_collected']}",
        f"- DAgger rollout episodes kept as corrections: {metadata['dataset_shape']['dagger_episodes']}",
        f"- Observation dim: {metadata['dataset_shape']['observations'][1]}",
        f"- Action dim: {metadata['dataset_shape']['actions'][1]}",
        f"- DAgger rollout classification counts: `{dict(counts)}`",
        f"- Kept correction classification counts: `{dict(kept_counts)}`",
        f"- Execute expert mix: {metadata['execute_expert_mix']}",
        f"- Keep rollout classes: `{metadata['keep_rollout_classes']}`",
        "",
        "## Semantics",
        "",
        "- Base samples are successful scripted pinned-wrap samples.",
        "- DAgger samples are observations visited by the current BC policy; labels are scripted expert actuator targets at the same stage/fraction.",
        "- The ball is pinned during closing. This remains pinned-wrap training, not free-object stable grasp.",
        "",
        "## DAgger Episodes",
        "",
        "| Episode | Kept | Class under policy rollout | Ball | Finger scale | Thumb rank | Samples | Hold contacts | Penetration | Mean four-tip | Thumb-ball |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, item in enumerate(dagger_results):
        hold = item["stages"]["hold"]
        lines.append(
            f"| {idx} | {item.get('kept_as_correction', False)} | {item['classification']} | `{item['ball_position']}` | {item['finger_scale']:.2f} | "
            f"{item['thumb_rank']} | {item['sample_count']} | {hold.get('ball_contact_count', 0)} | "
            f"{hold.get('max_penetration', 0.0):.6f} | {hold.get('mean_four_tip_distance', 0.0):.6f} | "
            f"{hold.get('thumb_to_ball', 0.0):.6f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect export3 DAgger-style correction dataset.")
    parser.add_argument("--base-data", type=Path, default=BASE_DATASET)
    parser.add_argument("--base-class-filter", type=str, default="PINNED_WRAP_PASS")
    parser.add_argument("--policy", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--modes", nargs="+", default=["pinned"], choices=MODES)
    parser.add_argument("--thumb-candidates", type=int, default=5)
    parser.add_argument("--max-episodes", type=int, default=75)
    parser.add_argument("--speed", type=float, default=2.5)
    parser.add_argument("--step-stride", type=int, default=3)
    parser.add_argument("--execute-expert-mix", type=float, default=0.0)
    parser.add_argument(
        "--keep-rollout-classes",
        type=str,
        default="",
        help="Comma-separated policy rollout classes to keep as DAgger corrections; empty keeps all.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    base = load_base_samples(args.base_data, args.base_class_filter)
    expected_features = make_feature_names()
    if base["feature_names"] != expected_features:
        raise RuntimeError("Base dataset feature schema does not match current export3 observation schema.")

    policy, checkpoint = load_policy(args.policy, device)
    configs = build_configs(args.modes, args.thumb_candidates, args.max_episodes)
    mujoco, model, data = load_model(SCENE_XML)
    arrays = {key: [] for key in ["observations", "actions", "episode_id", "stage_id", "step_in_stage", "mode_id"]}
    dagger_results = []
    episode_offset = int(base["episode_count"])
    keep_classes = set(parse_class_filter(args.keep_rollout_classes))
    kept_count = 0
    for idx, config in enumerate(configs):
        result, local_arrays = collect_dagger_episode(
            mujoco,
            model,
            data,
            policy,
            checkpoint,
            device,
            config,
            episode_offset + idx,
            args.speed,
            args.step_stride,
            args.execute_expert_mix,
            None,
        )
        dagger_results.append(result)
        kept = not keep_classes or result["classification"] in keep_classes
        result["kept_as_correction"] = bool(kept)
        if kept:
            append_arrays(arrays, local_arrays)
            kept_count += 1
        print(
            f"dagger {idx + 1}/{len(configs)} rollout={result['classification']} "
            f"samples={result['sample_count']} kept={kept}"
        )

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_dagger_correction_dataset_not_promoted_baseline",
        "base_dataset": str(args.base_data),
        "base_class_filter": args.base_class_filter,
        "policy_checkpoint": str(args.policy),
        "dataset_path": str(args.output),
        "report_path": str(args.report),
        "metadata_path": str(args.metadata),
        "modes": args.modes,
        "thumb_candidates": args.thumb_candidates,
        "max_episodes": args.max_episodes,
        "speed": args.speed,
        "step_stride": args.step_stride,
        "execute_expert_mix": args.execute_expert_mix,
        "keep_rollout_classes": sorted(keep_classes) if keep_classes else ["ALL"],
        "kept_dagger_episodes": kept_count,
        "device": str(device),
        "feature_names": base["feature_names"],
        "action_names": base["action_names"],
        "dagger_results": dagger_results,
    }
    metadata = save_combined_dataset(args.output, base, arrays, dagger_results, metadata)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, metadata, dagger_results)
    print(json.dumps({"dataset": str(args.output), "report": str(args.report), "shape": metadata["dataset_shape"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
