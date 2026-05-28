from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from collect_export3_scripted_dataset import (
    DEFAULT_DATASET,
    ball_body_position,
    build_configs,
    observation_vector,
)
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
from train_export3_bc import BCPolicy


CHECKPOINT_DIR = ROOT / "checkpoints"
DEFAULT_CHECKPOINT = CHECKPOINT_DIR / "bc_hand_stage1_export3_pinned_wrap_v0.pth"
DEFAULT_REPORT = DOCS_DIR / "export3_bc_pinned_wrap_v0_eval_report.md"
DEFAULT_METADATA = METADATA_DIR / "export3_bc_pinned_wrap_v0_eval.json"


def load_policy(path: Path, device: torch.device) -> tuple[BCPolicy, dict]:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    model = BCPolicy(
        obs_dim=int(checkpoint["obs_dim"]),
        act_dim=int(checkpoint["act_dim"]),
        hidden_dim=int(checkpoint["hidden_dim"]),
        depth=int(checkpoint.get("depth", 3)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


def reset_state(model, data, mujoco, config: TrialConfig) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, list(config.ball_position))
    mujoco.mj_forward(model, data)


def policy_action(
    policy: BCPolicy,
    checkpoint: dict,
    obs: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    obs_mean = np.asarray(checkpoint["obs_mean"], dtype=np.float32)
    obs_std = np.asarray(checkpoint["obs_std"], dtype=np.float32)
    act_mean = np.asarray(checkpoint["action_mean"], dtype=np.float32)
    act_std = np.asarray(checkpoint["action_std"], dtype=np.float32)
    act_min = np.asarray(checkpoint.get("action_min", act_mean - 3.0 * act_std), dtype=np.float32)
    act_max = np.asarray(checkpoint.get("action_max", act_mean + 3.0 * act_std), dtype=np.float32)
    obs_norm = (obs.astype(np.float32) - obs_mean) / obs_std
    with torch.no_grad():
        pred_norm = policy(torch.from_numpy(obs_norm).float().to(device)).cpu().numpy()
    pred = (pred_norm * act_std + act_mean).astype(np.float32)
    return np.clip(pred, act_min, act_max).astype(np.float32)


def action_dict(vec: np.ndarray) -> dict[str, float]:
    return {name: float(vec[idx]) for idx, name in enumerate(CONTROLLED_JOINTS)}


def rollout_policy(
    mujoco,
    sim_model,
    data,
    policy: BCPolicy,
    checkpoint: dict,
    device: torch.device,
    config: TrialConfig,
    speed: float,
    release_steps: int,
    action_smoothing: float,
) -> dict:
    mode = config.mode
    sim_model.opt.gravity[:] = [0.0, 0.0, -9.81] if mode == "free_gravity" else [0.0, 0.0, 0.0]
    act_map = actuator_map(sim_model, mujoco)
    joints = joint_map(sim_model, mujoco)
    reset_state(sim_model, data, mujoco, config)

    previous_scripted = scaled_targets("open_hand", config.finger_scale, dict(config.thumb_pose))
    previous_ctrl = np.zeros(len(CONTROLLED_JOINTS), dtype=np.float32)
    stages = {}

    for stage in STAGE_ORDER:
        scripted_target = scaled_targets(stage, config.finger_scale, dict(config.thumb_pose))
        steps = stage_steps(stage, speed)
        applied = {}
        for step in range(max(steps, 1)):
            fraction = (step + 1) / max(steps, 1)
            # Scripted blend is used only to provide the same phase context as the dataset.
            _ = blend(previous_scripted, scripted_target, fraction)
            obs = observation_vector(sim_model, data, mujoco, joints, previous_ctrl, fraction, STAGE_ORDER.index(stage), config)
            target_vec = policy_action(policy, checkpoint, obs, device)
            if action_smoothing > 0.0:
                target_vec = (1.0 - action_smoothing) * target_vec + action_smoothing * previous_ctrl
            applied = set_ctrl(sim_model, data, action_dict(target_vec), act_map)
            previous_ctrl = np.array([float(applied.get(name, previous_ctrl[idx])) for idx, name in enumerate(CONTROLLED_JOINTS)], dtype=np.float32)
            set_ball_position(sim_model, data, mujoco, list(config.ball_position))
            mujoco.mj_step(sim_model, data)
        set_ball_position(sim_model, data, mujoco, list(config.ball_position))
        mujoco.mj_forward(sim_model, data)
        stages[stage] = stage_summary(sim_model, data, mujoco, joints, scripted_target, applied)
        stages[stage]["ball_body_position"] = ball_body_position(sim_model, data, mujoco).tolist()
        previous_scripted = scripted_target

    release = None
    if mode != "pinned":
        release_start = ball_body_position(sim_model, data, mujoco)
        for _ in range(max(release_steps, 1)):
            set_ctrl(sim_model, data, action_dict(previous_ctrl), act_map)
            mujoco.mj_step(sim_model, data)
        mujoco.mj_forward(sim_model, data)
        release_end = ball_body_position(sim_model, data, mujoco)
        release = {
            "release_start_ball": release_start.tolist(),
            "release_end_ball": release_end.tolist(),
            "ball_drift_after_release": float(np.linalg.norm(release_end - release_start)),
            "ball_z_drop_after_release": float(release_start[2] - release_end[2]),
            "summary": stage_summary(sim_model, data, mujoco, joints, action_dict(previous_ctrl), action_dict(previous_ctrl)),
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
    result["classification"] = classify_trial(result)
    return result


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Export3 BC Pinned-Wrap v0 Online Eval Report",
        "",
        "Status: diagnostic rollout evaluation, not a promoted stable_grasp baseline.",
        "",
        f"- Scene: `{SCENE_XML}`",
        f"- Checkpoint: `{report['checkpoint']}`",
        f"- Dataset reference: `{report['dataset_reference']}`",
        f"- Episode count: {report['episode_count']}",
        f"- Modes: `{report['modes']}`",
        f"- Classification counts: `{report['classification_counts']}`",
        f"- Action smoothing: {report['action_smoothing']}",
        "",
        "## Summary",
        "",
        f"- Pinned wrap pass rate: {report['pinned_wrap_pass_rate']:.3f}",
        f"- Mean hold contacts: {report['mean_hold_contacts']:.3f}",
        f"- Mean hold penetration: {report['mean_hold_penetration']:.6f}",
        f"- Mean four-tip distance: {report['mean_four_tip_distance']:.6f}",
        f"- Mean thumb-ball distance: {report['mean_thumb_to_ball']:.6f}",
        "",
        "## Interpretation",
        "",
        "- This checks whether the offline BC policy can reproduce the scripted pinned-wrap target pattern in MuJoCo rollout.",
        "- The ball is still pinned during closing, so this is not free-object stable grasp.",
        "- If pass rate is low, the dataset needs stage identity or more episodes before RL.",
        "",
        "## Episodes",
        "",
        "| Episode | Mode | Class | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, item in enumerate(report["episodes"]):
        hold = item["stages"]["hold"]
        lines.append(
            f"| {idx} | {item['mode']} | {item['classification']} | `{item['ball_position']}` | "
            f"{item['finger_scale']:.2f} | {item['thumb_rank']} | {hold.get('ball_contact_count', 0)} | "
            f"{hold.get('max_penetration', 0.0):.6f} | {hold.get('mean_four_tip_distance', 0.0):.6f} | "
            f"{hold.get('thumb_to_ball', 0.0):.6f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize(results: list[dict]) -> dict:
    counts = Counter(item["classification"] for item in results)
    pinned = [item for item in results if item["mode"] == "pinned"]
    pass_count = sum(1 for item in pinned if item["classification"] == "PINNED_WRAP_PASS")
    holds = [item["stages"]["hold"] for item in results]
    return {
        "classification_counts": dict(counts),
        "pinned_wrap_pass_rate": pass_count / max(len(pinned), 1),
        "mean_hold_contacts": float(np.mean([h.get("ball_contact_count", 0) for h in holds])),
        "mean_hold_penetration": float(np.mean([h.get("max_penetration", 0.0) for h in holds])),
        "mean_four_tip_distance": float(np.mean([h.get("mean_four_tip_distance", 0.0) or 0.0 for h in holds])),
        "mean_thumb_to_ball": float(np.mean([h.get("thumb_to_ball", 0.0) or 0.0 for h in holds])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate export3 BC policy in MuJoCo rollout.")
    parser.add_argument("--model", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--dataset-reference", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--modes", nargs="+", default=["pinned"], choices=MODES)
    parser.add_argument("--thumb-candidates", type=int, default=5)
    parser.add_argument("--max-episodes", type=int, default=15)
    parser.add_argument("--speed", type=float, default=2.5)
    parser.add_argument("--release-steps", type=int, default=180)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    policy, checkpoint = load_policy(args.model, device)
    configs = build_configs(args.modes, args.thumb_candidates, args.max_episodes)
    mujoco, sim_model, data = load_model(SCENE_XML)
    results = []
    for idx, config in enumerate(configs, 1):
        result = rollout_policy(
            mujoco,
            sim_model,
            data,
            policy,
            checkpoint,
            device,
            config,
            args.speed,
            args.release_steps,
            args.action_smoothing,
        )
        results.append(result)
        print(f"episode {idx}/{len(configs)} {result['classification']}")

    summary = summarize(results)
    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_rollout_eval_not_promoted_baseline",
        "checkpoint": str(args.model),
        "dataset_reference": str(args.dataset_reference),
        "report": str(args.report),
        "metadata": str(args.metadata),
        "episode_count": len(results),
        "modes": args.modes,
        "thumb_candidates": args.thumb_candidates,
        "max_episodes": args.max_episodes,
        "speed": args.speed,
        "release_steps": args.release_steps,
        "action_smoothing": args.action_smoothing,
        "device": str(device),
        "episodes": results,
    }
    report.update(summary)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, report)
    print(json.dumps({k: report[k] for k in ["episode_count", "classification_counts", "pinned_wrap_pass_rate", "mean_hold_contacts", "mean_hold_penetration"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
