from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from export3_common import (
    ARCHIVE_DIR,
    CONTROLLED_JOINTS,
    DOCS_DIR,
    METADATA_DIR,
    ROOT,
    SCENE_XML,
    TIP_SITES,
    THUMB_JOINTS,
    actuator_map,
    ball_contact_summary,
    blend,
    fingertip_distances,
    joint_map,
    load_model,
    set_ball_position,
    set_ctrl,
    stage_summary,
)
from run_export3_shadow_style_scripted_task import (
    BALL_SWEEP,
    FINGER_SCALES,
    MODES,
    STAGE_ORDER,
    TrialConfig,
    classify_trial,
    load_thumb_candidates,
    scaled_targets,
    stage_steps,
)


DATA_DIR = ROOT / "data"
DEFAULT_DATASET = DATA_DIR / "export3_scripted_pinned_wrap_v0.npz"
DEFAULT_REPORT = DOCS_DIR / "export3_scripted_dataset_v0_report.md"
DEFAULT_METADATA = METADATA_DIR / "export3_scripted_dataset_v0.json"


STAGE_NAMES = list(STAGE_ORDER)
DEFAULT_MODES = ["pinned"]


@dataclass
class EpisodeCollection:
    config: TrialConfig
    classification: str
    score_hint: float
    sample_count: int
    stages: dict
    release: dict | None


def backup_existing(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ARCHIVE_DIR / f"export3_dataset_backup_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.copy2(path, backup_dir / path.name)
    return backup_dir


def ball_body_position(model, data, mujoco) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    return np.array(data.xpos[bid], dtype=np.float32)


def ball_body_velocity(model, data, mujoco) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    if bid < 0:
        return np.zeros(3, dtype=np.float32)
    # MuJoCo cvel is a 6D spatial velocity; the last 3 entries are linear.
    return np.array(data.cvel[bid][3:6], dtype=np.float32)


def controlled_qpos_qvel(model, data, joints: dict[str, int]) -> tuple[np.ndarray, np.ndarray]:
    qpos = []
    qvel = []
    for name in CONTROLLED_JOINTS:
        jid = joints.get(name)
        if jid is None:
            qpos.append(np.nan)
            qvel.append(np.nan)
            continue
        qpos.append(float(data.qpos[int(model.jnt_qposadr[jid])]))
        qvel.append(float(data.qvel[int(model.jnt_dofadr[jid])]))
    return np.array(qpos, dtype=np.float32), np.array(qvel, dtype=np.float32)


def make_feature_names() -> list[str]:
    names: list[str] = []
    names.extend([f"qpos:{name}" for name in CONTROLLED_JOINTS])
    names.extend([f"qvel:{name}" for name in CONTROLLED_JOINTS])
    names.extend(["ball_pos:x", "ball_pos:y", "ball_pos:z"])
    names.extend(["ball_vel:x", "ball_vel:y", "ball_vel:z"])
    for site in TIP_SITES:
        names.extend([f"{site}:x", f"{site}:y", f"{site}:z"])
    names.extend([f"tip_ball_dist:{site}" for site in TIP_SITES])
    names.extend(["mean_four_tip_distance", "thumb_to_ball", "thumb_to_index"])
    names.extend(["ball_contact_count", "max_penetration"])
    names.extend([f"prev_ctrl:{name}" for name in CONTROLLED_JOINTS])
    names.extend(["stage_fraction", "finger_scale", "thumb_rank"])
    names.extend([f"stage_onehot:{name}" for name in STAGE_NAMES])
    names.extend([f"thumb_target:{name}" for name in THUMB_JOINTS])
    names.extend([f"ball_target:{axis}" for axis in ("x", "y", "z")])
    return names


def observation_vector(
    model,
    data,
    mujoco,
    joints: dict[str, int],
    prev_ctrl: np.ndarray,
    stage_fraction: float,
    stage_index: int,
    config: TrialConfig,
) -> np.ndarray:
    qpos, qvel = controlled_qpos_qvel(model, data, joints)
    tips = fingertip_distances(model, data, mujoco)
    contact = ball_contact_summary(model, data, mujoco)
    site_positions = []
    for site in TIP_SITES:
        pos = tips["site_positions"].get(site)
        site_positions.extend([np.nan, np.nan, np.nan] if pos is None else pos)
    tip_distances = [
        np.nan if tips["distances"].get(site) is None else float(tips["distances"][site])
        for site in TIP_SITES
    ]
    values = []
    values.extend(qpos.tolist())
    values.extend(qvel.tolist())
    values.extend(ball_body_position(model, data, mujoco).tolist())
    values.extend(ball_body_velocity(model, data, mujoco).tolist())
    values.extend(site_positions)
    values.extend(tip_distances)
    values.extend(
        [
            np.nan if tips["mean_four_tip_distance"] is None else float(tips["mean_four_tip_distance"]),
            np.nan if tips["thumb_to_ball"] is None else float(tips["thumb_to_ball"]),
            np.nan if tips["thumb_to_index"] is None else float(tips["thumb_to_index"]),
            float(contact["ball_contact_count"]),
            float(contact["max_penetration"]),
        ]
    )
    values.extend(prev_ctrl.tolist())
    values.extend([float(stage_fraction), float(config.finger_scale), float(config.thumb_rank)])
    values.extend([1.0 if idx == stage_index else 0.0 for idx in range(len(STAGE_NAMES))])
    thumb_pose = dict(config.thumb_pose)
    values.extend([float(thumb_pose.get(name, 0.0)) for name in THUMB_JOINTS])
    values.extend(list(config.ball_position))
    return np.nan_to_num(np.array(values, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)


def reset_state(model, data, mujoco, config: TrialConfig) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, list(config.ball_position))
    mujoco.mj_forward(model, data)


def action_vector(applied: dict[str, float]) -> np.ndarray:
    return np.array([float(applied.get(name, 0.0)) for name in CONTROLLED_JOINTS], dtype=np.float32)


def collect_episode(
    mujoco,
    model,
    data,
    config: TrialConfig,
    speed: float,
    step_stride: int,
    release_steps: int,
    arrays: dict[str, list],
    episode_index: int,
) -> EpisodeCollection:
    mode = config.mode
    model.opt.gravity[:] = [0.0, 0.0, -9.81] if mode == "free_gravity" else [0.0, 0.0, 0.0]
    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    reset_state(model, data, mujoco, config)

    previous = scaled_targets("open_hand", config.finger_scale, dict(config.thumb_pose))
    previous_ctrl = np.zeros(len(CONTROLLED_JOINTS), dtype=np.float32)
    stages = {}
    sample_count = 0

    for stage_index, stage in enumerate(STAGE_NAMES):
        targets = scaled_targets(stage, config.finger_scale, dict(config.thumb_pose))
        steps = stage_steps(stage, speed)
        applied: dict[str, float] = {}
        for step in range(max(steps, 1)):
            fraction = (step + 1) / max(steps, 1)
            command = blend(previous, targets, fraction)
            applied = set_ctrl(model, data, command, act_map)
            set_ball_position(model, data, mujoco, list(config.ball_position))
            mujoco.mj_step(model, data)
            if step % max(step_stride, 1) == 0 or step == steps - 1:
                obs = observation_vector(model, data, mujoco, joints, previous_ctrl, fraction, stage_index, config)
                act = action_vector(applied)
                arrays["observations"].append(obs)
                arrays["actions"].append(act)
                arrays["episode_id"].append(episode_index)
                arrays["stage_id"].append(stage_index)
                arrays["step_in_stage"].append(step)
                arrays["mode_id"].append(MODES.index(mode))
                sample_count += 1
                previous_ctrl = act
        set_ball_position(model, data, mujoco, list(config.ball_position))
        mujoco.mj_forward(model, data)
        stages[stage] = stage_summary(model, data, mujoco, joints, targets, applied)
        stages[stage]["ball_body_position"] = ball_body_position(model, data, mujoco).tolist()
        previous = targets

    release = None
    if mode != "pinned":
        release_start = ball_body_position(model, data, mujoco)
        for _ in range(max(release_steps, 1)):
            set_ctrl(model, data, previous, act_map)
            mujoco.mj_step(model, data)
        mujoco.mj_forward(model, data)
        release_end = ball_body_position(model, data, mujoco)
        release = {
            "release_start_ball": release_start.tolist(),
            "release_end_ball": release_end.tolist(),
            "ball_drift_after_release": float(np.linalg.norm(release_end - release_start)),
            "ball_z_drop_after_release": float(release_start[2] - release_end[2]),
            "summary": stage_summary(model, data, mujoco, joints, previous, {name: float(data.ctrl[aid]) for name, aid in act_map.items()}),
        }

    result = {
        "mode": mode,
        "ball_position": list(config.ball_position),
        "finger_scale": config.finger_scale,
        "thumb_rank": config.thumb_rank,
        "thumb_pose": dict(config.thumb_pose),
        "stages": stages,
        "release": release,
    }
    classification = classify_trial(result)
    return EpisodeCollection(
        config=config,
        classification=classification,
        score_hint=float(stages["hold"].get("mean_four_tip_distance") or 1.0),
        sample_count=sample_count,
        stages=stages,
        release=release,
    )


def build_configs(modes: list[str], thumb_limit: int, max_episodes: int) -> list[TrialConfig]:
    thumbs = load_thumb_candidates(thumb_limit)
    configs: list[TrialConfig] = []
    for mode in modes:
        for ball in BALL_SWEEP:
            for scale in FINGER_SCALES:
                for rank, thumb in enumerate(thumbs, 1):
                    configs.append(TrialConfig(mode, tuple(float(v) for v in ball), float(scale), tuple(sorted(thumb.items())), rank))
    if max_episodes > 0:
        configs = configs[:max_episodes]
    return configs


def save_dataset(
    output: Path,
    arrays: dict[str, list],
    episodes: list[EpisodeCollection],
    metadata: dict,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    observations = np.stack(arrays["observations"]).astype(np.float32)
    actions = np.stack(arrays["actions"]).astype(np.float32)
    episode_id = np.array(arrays["episode_id"], dtype=np.int32)
    stage_id = np.array(arrays["stage_id"], dtype=np.int16)
    step_in_stage = np.array(arrays["step_in_stage"], dtype=np.int16)
    mode_id = np.array(arrays["mode_id"], dtype=np.int16)
    class_names = sorted({ep.classification for ep in episodes})
    class_to_id = {name: idx for idx, name in enumerate(class_names)}
    episode_class = np.array([class_to_id[ep.classification] for ep in episodes], dtype=np.int16)
    sample_class = np.array([episode_class[eid] for eid in episode_id], dtype=np.int16)
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
        feature_names=np.array(metadata["feature_names"], dtype=object),
        action_names=np.array(CONTROLLED_JOINTS, dtype=object),
        stage_names=np.array(STAGE_NAMES, dtype=object),
        mode_names=np.array(MODES, dtype=object),
        class_names=np.array(class_names, dtype=object),
    )
    metadata["dataset_shape"] = {
        "observations": list(observations.shape),
        "actions": list(actions.shape),
        "episodes": len(episodes),
    }
    metadata["class_names"] = class_names
    metadata["class_to_id"] = class_to_id


def write_report(path: Path, metadata: dict, episodes: list[EpisodeCollection], backup_dir: Path | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    class_counts = Counter(ep.classification for ep in episodes)
    mode_counts = Counter(ep.config.mode for ep in episodes)
    lines = [
        "# Export3 Scripted Dataset v0 Report",
        "",
        "Status: diagnostic training asset, not a promoted stable_grasp baseline.",
        "",
        f"- Scene: `{SCENE_XML}`",
        f"- Dataset: `{metadata['dataset_path']}`",
        f"- Metadata: `{metadata['metadata_path']}`",
        f"- Backup directory: `{backup_dir}`" if backup_dir else "- Backup directory: none needed",
        f"- Episode count: {len(episodes)}",
        f"- Sample count: {metadata['dataset_shape']['observations'][0]}",
        f"- Observation dim: {metadata['dataset_shape']['observations'][1]}",
        f"- Action dim: {metadata['dataset_shape']['actions'][1]}",
        f"- Modes: `{dict(mode_counts)}`",
        f"- Classification counts: `{dict(class_counts)}`",
        f"- Step stride: {metadata['step_stride']}",
        f"- Speed: {metadata['speed']}",
        "",
        "## Dataset Semantics",
        "",
        "- `observations`: state vector built from controlled joint qpos/qvel, ball pose/velocity, fingertip site positions, fingertip-ball distances, contact summary, previous ctrl, stage fraction, finger scale, thumb rank, and target ball position.",
        "- `actions`: 21-D MuJoCo position actuator target vector after actuator ctrlrange clipping.",
        "- `episode_class` / `sample_class`: scripted-trial diagnostic classification labels.",
        "- This dataset is meant for first-pass BC/DAgger scaffolding over export3 scripted behavior.",
        "",
        "## Limits",
        "",
        "- The ball is pinned during scripted closing for collected `pinned` episodes.",
        "- Successful pinned wrap is not equivalent to stable free-object grasp.",
        "- Collision is still primitive proxy; clean STL remains visual-only.",
        "- Thumb/wrist mechanical semantics still need manual confirmation before final task training.",
        "",
        "## Episodes",
        "",
        "| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Samples | Hold contacts | Hold penetration | Mean four-tip | Thumb-ball |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, ep in enumerate(episodes):
        hold = ep.stages["hold"]
        lines.append(
            f"| {idx} | {ep.config.mode} | {ep.classification} | `{list(ep.config.ball_position)}` | "
            f"{ep.config.finger_scale:.2f} | {ep.config.thumb_rank} | {ep.sample_count} | "
            f"{hold.get('ball_contact_count', 0)} | {hold.get('max_penetration', 0.0):.6f} | "
            f"{hold.get('mean_four_tip_distance', 0.0):.6f} | {hold.get('thumb_to_ball', 0.0):.6f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect export3 scripted diagnostic dataset for first-pass BC.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES, choices=MODES)
    parser.add_argument("--thumb-candidates", type=int, default=5)
    parser.add_argument("--max-episodes", type=int, default=30, help="0 means collect all generated configs.")
    parser.add_argument("--speed", type=float, default=4.0)
    parser.add_argument("--step-stride", type=int, default=4)
    parser.add_argument("--release-steps", type=int, default=180)
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_existing([args.output, args.report, args.metadata])

    configs = build_configs(args.modes, args.thumb_candidates, args.max_episodes)
    if not configs:
        raise RuntimeError("No export3 scripted dataset configs were generated.")

    mujoco, model, data = load_model(SCENE_XML)
    arrays = {key: [] for key in ["observations", "actions", "episode_id", "stage_id", "step_in_stage", "mode_id"]}
    episodes: list[EpisodeCollection] = []
    for idx, config in enumerate(configs):
        ep = collect_episode(mujoco, model, data, config, args.speed, args.step_stride, args.release_steps, arrays, idx)
        episodes.append(ep)
        print(f"episode {idx + 1}/{len(configs)} {config.mode} {ep.classification} samples={ep.sample_count}")

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_training_asset_not_promoted_baseline",
        "scene_xml": str(SCENE_XML),
        "dataset_path": str(args.output),
        "report_path": str(args.report),
        "metadata_path": str(args.metadata),
        "modes": args.modes,
        "thumb_candidates": args.thumb_candidates,
        "max_episodes": args.max_episodes,
        "speed": args.speed,
        "step_stride": args.step_stride,
        "release_steps": args.release_steps,
        "feature_names": make_feature_names(),
        "action_names": list(CONTROLLED_JOINTS),
        "stage_names": STAGE_NAMES,
        "mode_names": MODES,
        "episodes": [
            {
                "episode_id": idx,
                "mode": ep.config.mode,
                "ball_position": list(ep.config.ball_position),
                "finger_scale": ep.config.finger_scale,
                "thumb_rank": ep.config.thumb_rank,
                "thumb_pose": dict(ep.config.thumb_pose),
                "classification": ep.classification,
                "sample_count": ep.sample_count,
                "hold": {
                    "ball_contact_count": ep.stages["hold"].get("ball_contact_count"),
                    "max_penetration": ep.stages["hold"].get("max_penetration"),
                    "mean_four_tip_distance": ep.stages["hold"].get("mean_four_tip_distance"),
                    "thumb_to_ball": ep.stages["hold"].get("thumb_to_ball"),
                    "thumb_to_index": ep.stages["hold"].get("thumb_to_index"),
                },
            }
            for idx, ep in enumerate(episodes)
        ],
    }
    save_dataset(args.output, arrays, episodes, metadata)
    args.metadata.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, metadata, episodes, backup_dir)
    print(json.dumps({"dataset": str(args.output), "report": str(args.report), "metadata": str(args.metadata), "shape": metadata["dataset_shape"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
