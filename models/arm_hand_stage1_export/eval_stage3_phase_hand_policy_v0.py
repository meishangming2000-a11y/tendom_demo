#!/usr/bin/env python3
"""Closed-loop MuJoCo eval for Stage3.6 phase-specific learned hand policy."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
from arm_hand_stage1_v2_bc_common import load_policy
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_phase_hand_policy_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_phase_hand_policy_v0_eval_report.md"
DEFAULT_METADATA = META / "stage3_phase_hand_policy_v0_eval.json"


def predict_hand_action(
    policy,
    checkpoint: dict[str, Any],
    obs: np.ndarray,
    *,
    device: torch.device,
    clip_to_train_range: bool,
) -> np.ndarray:
    feature = np.asarray(obs, dtype=np.float32)
    feature_norm = (feature - checkpoint["feature_mean"]) / checkpoint["feature_std"]
    with torch.no_grad():
        pred_norm = policy(torch.from_numpy(feature_norm).to(device)).cpu().numpy()
    action = pred_norm * checkpoint["action_std"] + checkpoint["action_mean"]
    if clip_to_train_range:
        action = np.clip(action, checkpoint["action_min"], checkpoint["action_max"])
    return action.astype(np.float64)


def merge_phase_hand_action(
    expert_action: np.ndarray,
    hand_action: np.ndarray,
    checkpoint: dict[str, Any],
    *,
    phase_name: str,
    learned_phases: set[str],
) -> tuple[np.ndarray, bool]:
    merged = np.asarray(expert_action, dtype=np.float64).copy()
    if phase_name not in learned_phases:
        return merged, False
    hand_indices = np.asarray(checkpoint["hand_action_indices"], dtype=np.int32)
    if hand_indices.size != hand_action.size:
        raise ValueError(f"hand index/action mismatch: {hand_indices.size} vs {hand_action.size}")
    merged[hand_indices] = np.asarray(hand_action, dtype=np.float64)
    return merged, True


def run_policy_episode(model, mujoco, policy, checkpoint: dict[str, Any], trial: sweep.TrialConfig, episode_id: int, args, device: torch.device) -> dict[str, Any]:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    rng = np.random.default_rng(int(args.seed) + int(episode_id))
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)

    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )
    vision_estimate = vision_sensor.estimate(data, label=f"stage3_phase_hand_eval_{episode_id:04d}_vision_acquire")
    if not collect.accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence)):
        return {
            "episode_id": int(episode_id),
            "trial": trial.name,
            "status": "FAIL",
            "success": False,
            "terminal_reason": "vision_acquire_failed",
            "failure_reasons": ["vision_acquire_failed"],
        }
    vision = collect.make_vision_fields(vision_estimate)
    profile = collect.Stage3DatasetProfile("eval_clean_nominal", 1.0, 0.0, 0.0, 0)
    plan = collect.build_episode_plan(model, data, mujoco, trial=trial, egg_position=egg_position, vision_fields=vision, args=args, profile=profile)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    previous_action: np.ndarray | None = None
    actuator_names = plan["actuator_names"]
    learned_phases = set(str(name) for name in checkpoint.get("learned_phases", []))

    contact_acquired = False
    grip_stable_before_lift = False
    first_contact_phase = "none"
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    hold_steps = 0
    hold_stable_steps = 0
    hold_max_slip = 0.0
    trace = []
    step_count = 0
    learned_control_steps = 0
    approach_true_proxy_error = float("inf")
    approach_est_proxy_error = float("inf")

    for phase_name, start, end, steps in plan["phases"]:
        for local_step in range(max(1, int(steps))):
            progress = local_step / max(1, int(steps) - 1)
            tactile = tactile_sensor.sample(data)
            obs = collect.observation_vector(model, data, vision, tactile, phase_name=phase_name, progress=progress)
            expert_targets = sweep.blend_targets(start, end, progress)
            expert_action = sweep.actuator_targets(model, mujoco, actuator_names, expert_targets)
            hand_action = predict_hand_action(
                policy,
                checkpoint,
                obs,
                device=device,
                clip_to_train_range=not bool(args.no_train_range_clip),
            )
            action, used_learned_hand = merge_phase_hand_action(
                expert_action,
                hand_action,
                checkpoint,
                phase_name=phase_name,
                learned_phases=learned_phases,
            )
            learned_control_steps += int(bool(used_learned_hand))
            if previous_action is not None and float(args.action_smoothing) > 0.0:
                smoothing = float(np.clip(args.action_smoothing, 0.0, 0.99))
                action = smoothing * previous_action + (1.0 - smoothing) * action
            previous_action = action.copy()
            data.ctrl[:] = collect.clip_action(model, action)
            mujoco.mj_step(model, data)
            next_tactile = tactile_sensor.sample(data)
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_egg[2])
            if phase_name == "approach":
                proxy_now = sweep.proxy_position(model, data, mujoco, plan["grasp_local"])
                approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_egg))
                approach_est_proxy_error = float(np.linalg.norm(proxy_now - plan["approach_target"]))
            if next_tactile["contact_present"]:
                contact_acquired = True
                if first_contact_phase == "none":
                    first_contact_phase = phase_name
            if next_tactile["grip_stable"] and phase_name in {"gentle_close_thumb", "contact_settle"}:
                grip_stable_before_lift = True
            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(next_tactile["grip_stable"]))
                hold_max_slip = max(hold_max_slip, float(next_tactile["slip_score"]))
            max_slip = max(max_slip, float(next_tactile["slip_score"]))
            max_crush = max(max_crush, float(next_tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(next_tactile.get("max_penetration", 0.0)))
            if step_count % max(1, int(args.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "learned_hand": bool(used_learned_hand),
                        "lift_height_m": lift_height,
                        "contact": bool(next_tactile["contact_present"]),
                        "stable": bool(next_tactile["grip_stable"]),
                        "slip": float(next_tactile["slip_score"]),
                        "crush": float(next_tactile["crush_risk"]),
                        "penetration": float(next_tactile.get("max_penetration", 0.0)),
                    }
                )
            step_count += 1

    final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    hold_duration_s = float(hold_steps) * float(model.opt.timestep)
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
    summary = {
        "vision_accepted": True,
        "ik_approach_dxy_m": float(plan["approach_solution"]["dxy"]),
        "ik_approach_dz_m": float(plan["approach_solution"]["dz"]),
        "ik_lift_dxy_m": float(plan["lift_solution"]["dxy"]),
        "ik_lift_dz_m": float(plan["lift_solution"]["dz"]),
        "approach_true_proxy_error_m": float(approach_true_proxy_error),
        "approach_est_proxy_error_m": float(approach_est_proxy_error),
        "contact_acquired": bool(contact_acquired),
        "grip_stable_before_lift": bool(grip_stable_before_lift),
        "first_contact_phase": first_contact_phase,
        "final_lift_height_m": float(final_egg[2] - initial_egg[2]),
        "hold_duration_s": float(hold_duration_s),
        "hold_stable_fraction": float(hold_stable_fraction),
        "hold_max_slip_score": float(hold_max_slip),
        "hold_final_slip_score": float(final_tactile["slip_score"]),
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "finite_state": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "learned_control_steps": int(learned_control_steps),
        "total_steps": int(step_count),
    }
    reasons = collect.expert_failure_reasons(summary, args, thresholds)
    success = len(reasons) == 0
    risks = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_or_hold_slip")
    return {
        "episode_id": int(episode_id),
        "trial": trial.name,
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": "success_gentle_grasp_hold" if success else (reasons[0] if reasons else "unknown"),
        "failure_reasons": reasons,
        "risk_flags": risks,
        "summary": summary,
        "trace": trace,
        "policy_scope": "scripted_arm_wrist_phase_hand_policy",
        "learned_phases": sorted(learned_phases),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    reasons: dict[str, int] = {}
    risks: dict[str, int] = {}
    for row in results:
        reasons[row["terminal_reason"]] = reasons.get(row["terminal_reason"], 0) + 1
        for risk in row.get("risk_flags", []):
            risks[risk] = risks.get(risk, 0) + 1
    values = lambda key: np.asarray([row["summary"][key] for row in results if "summary" in row], dtype=np.float64)
    out: dict[str, Any] = {
        "status": "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL"),
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": reasons,
        "risk_flag_counts": risks,
    }
    for key in [
        "final_lift_height_m",
        "hold_stable_fraction",
        "hold_max_slip_score",
        "hold_final_slip_score",
        "max_crush_risk",
        "max_penetration_m",
        "approach_true_proxy_error_m",
        "learned_control_steps",
    ]:
        arr = values(key)
        if arr.size:
            out[f"{key}_mean"] = float(np.mean(arr))
            out[f"{key}_max"] = float(np.max(arr))
            out[f"{key}_min"] = float(np.min(arr))
    return out


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    lines = [
        "# Stage3.6 Phase Hand Policy V0 Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{s['status']}**\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Policy scope: `{payload['policy_scope']}`\n",
        f"- Learned phases: `{payload['learned_phases']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success count: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Risk flags: `{s['risk_flag_counts']}`\n",
        f"- Mean final lift: `{s.get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Mean hold stable fraction: `{s.get('hold_stable_fraction_mean', float('nan')):.3f}`\n",
        f"- Max hold slip: `{s.get('hold_max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max crush risk: `{s.get('max_crush_risk_max', float('nan')):.3f}`\n",
        f"- Max penetration: `{s.get('max_penetration_m_max', float('nan')):.6f} m`\n",
        f"- Mean learned-control steps: `{s.get('learned_control_steps_mean', float('nan')):.1f}`\n\n",
        "## Episode Results\n\n",
        "| ep | trial | status | reason | learned steps | lift m | stable | hold slip | final slip | crush | pen m | failures |\n",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for row in payload["results"]:
        if "summary" not in row:
            lines.append(f"| {row['episode_id']} | {row['trial']} | {row['status']} | {row['terminal_reason']} | 0 | nan | nan | nan | nan | nan | nan | `{row.get('failure_reasons', [])}` |\n")
            continue
        r = row["summary"]
        lines.append(
            f"| {row['episode_id']} | {row['trial']} | {row['status']} | {row['terminal_reason']} | "
            f"{r['learned_control_steps']} | {r['final_lift_height_m']:.5f} | {r['hold_stable_fraction']:.3f} | "
            f"{r['hold_max_slip_score']:.3f} | {r['hold_final_slip_score']:.3f} | "
            f"{r['max_crush_risk']:.3f} | {r['max_penetration_m']:.6f} | `{row.get('failure_reasons', [])}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is closed-loop MuJoCo evaluation of the formal Stage3.6 hand-only learned policy.\n",
            "- Arm and wrist targets remain scripted expert actions throughout the episode.\n",
            "- The learned policy replaces hand/finger actuator targets only in the configured contact/lift/hold phases.\n",
            "- Compare risk flags and contact metrics against the scripted expert before promotion.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage3.6 phase-specific hand policy closed-loop.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=150)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--functional-hit-threshold", type=float, default=0.015)
    parser.add_argument("--max-ik-dxy", type=float, default=0.006)
    parser.add_argument("--max-ik-dz", type=float, default=0.006)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.80)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--sample-every", type=int, default=200)
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=1500)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    device = torch.device(args.device)
    import mujoco

    policy, checkpoint = load_policy(args.checkpoint, device)
    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    trials = sweep.trial_configs()
    results = []
    for episode_id in range(int(args.episodes)):
        trial = trials[episode_id % len(trials)]
        row = run_policy_episode(model, mujoco, policy, checkpoint, trial, episode_id, args, device)
        results.append(row)
        summary = row.get("summary", {})
        print(
            f"ep={episode_id:03d} trial={trial.name} {row['status']} reason={row['terminal_reason']} "
            f"learned_steps={summary.get('learned_control_steps', 0)} "
            f"lift={summary.get('final_lift_height_m', float('nan')):.4f} "
            f"stable={summary.get('hold_stable_fraction', float('nan')):.3f}"
        )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_status": checkpoint.get("status"),
        "checkpoint_final_val_loss": float(checkpoint.get("final_val_loss", float("nan"))),
        "scene": str(Path(args.scene).resolve()),
        "device": str(device),
        "policy_scope": "scripted_arm_wrist_phase_hand_policy",
        "learned_phases": list(checkpoint.get("learned_phases", [])),
        "hand_action_indices": list(checkpoint.get("hand_action_indices", [])),
        "hand_action_names": list(checkpoint.get("hand_action_names", [])),
        "args": vars(args),
        "summary": summarize(results),
        "results": results,
        "training_ready": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
