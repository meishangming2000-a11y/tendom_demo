#!/usr/bin/env python3
"""Diagnostic-only rollout verification for pre_grasp -> stable_grasp task contracts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import mujoco
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scripts.common.grasp_workflow import (  # noqa: E402
    DEFAULT_PRE_GRASP_START_BIAS,
    compute_pre_grasp_expert_action,
    compute_stable_grasp_scripted_action,
    place_object,
    STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
    STABLE_GRASP_PHASE_MODE_ZERO_ACTION,
)
from src.environments.shadow_grasp_env import ShadowGraspEnv  # noqa: E402
from tasks import (  # noqa: E402
    EpisodeEvaluationResult,
    StableGraspTask,
    build_report_payload,
    create_stable_grasp_entry_snapshot,
)


ROLLOUT_MODE_DIAGNOSTIC_SEEDED = "diagnostic_seeded"
ROLLOUT_MODE_ENVIRONMENT_ONLY = "environment_only"
CANONICAL_ENTRY_SNAPSHOT_OWNER = "rollout_evaluator"


def _set_object_for_pre_grasp_entry(env, target_offset) -> Dict[str, Any]:
    """Teleport the object into a transition-ready relation for diagnostics only."""
    if env.object_joint_id is None:
        raise ValueError("Object joint is unavailable; cannot build the rollout diagnostic.")

    target_offset = np.asarray(target_offset, dtype=np.float32)
    desired_object_position = env._get_palm_reference_position() - target_offset
    qpos_adr = int(env.model.jnt_qposadr[env.object_joint_id])
    dof_adr = int(env.model.jnt_dofadr[env.object_joint_id])

    env.data.qpos[qpos_adr : qpos_adr + 3] = desired_object_position
    if (qpos_adr + 7) <= len(env.data.qpos):
        env.data.qpos[qpos_adr + 3 : qpos_adr + 7] = np.array(
            [1.0, 0.0, 0.0, 0.0],
            dtype=np.float32,
        )
    if (dof_adr + 6) <= len(env.data.qvel):
        env.data.qvel[dof_adr : dof_adr + 6] = 0.0

    mujoco.mj_forward(env.model, env.data)
    return {
        "mode": "diagnostic_transition_seed",
        "diagnostic_only": True,
        "desired_object_position": desired_object_position.astype(np.float32).tolist(),
        "target_offset": target_offset.astype(np.float32).tolist(),
    }


def _build_transition_info(pre_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the machine-readable transition payload used by episode summaries."""
    return dict(pre_info.get("pre_to_stable_transition", {}))


def _build_entry_snapshot(env, notes: str) -> Dict[str, Any]:
    """Create the canonical stable_grasp entry snapshot owned by rollout evaluation."""
    entry_snapshot = create_stable_grasp_entry_snapshot(
        adapter=env.get_hand_adapter(),
        step_index=int(env.current_step),
        control_timestep=float(env.control_timestep),
        entry_source="pre_grasp_to_stable_grasp_transition_ready",
        notes=notes,
        fallback_created=False,
    )
    return entry_snapshot


def _prepare_episode_start(env, rollout_mode: str) -> Dict[str, Any]:
    """Prepare one episode start without hiding whether it is diagnostic or environment-driven."""
    env.reset()
    if rollout_mode == ROLLOUT_MODE_DIAGNOSTIC_SEEDED:
        return _set_object_for_pre_grasp_entry(env, env.task.target_offset)
    if rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY:
        placement_info = place_object(
            env,
            placement_mode="demo",
            placement_jitter=0.0,
            pre_grasp_start_bias=DEFAULT_PRE_GRASP_START_BIAS,
        )
        return {
            "mode": "environment_reset_placement",
            "diagnostic_only": False,
            **placement_info,
        }
    raise ValueError(f"Unsupported rollout mode: {rollout_mode}")


def _compute_pre_grasp_action(env, rollout_mode: str) -> tuple[np.ndarray, Dict[str, Any]]:
    """Return the minimal pre_grasp action for the selected rollout mode."""
    if rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY:
        action, pose_debug = compute_pre_grasp_expert_action(
            env,
            gain_scale=1.0,
            clip_scale=1.0,
        )
        return action, {"pose_debug": pose_debug, "action_mode": "pre_grasp_expert_action"}
    return (
        np.zeros(env.nu, dtype=np.float32),
        {"pose_debug": {}, "action_mode": "zero_action"},
    )


def _run_pre_grasp_phase(
    env,
    rollout_mode: str,
    pre_grasp_steps: int,
) -> Dict[str, Any]:
    """Run pre_grasp until transition ready, failure, or the phase budget is exhausted."""
    pre_info: Dict[str, Any] = {}
    action_debug: Dict[str, Any] = {}
    done = False
    executed_steps = 0

    while executed_steps < max(1, pre_grasp_steps):
        action, action_debug = _compute_pre_grasp_action(env, rollout_mode)
        _, _, done, pre_info = env.step(action)
        executed_steps += 1
        transition_info = _build_transition_info(pre_info)
        if transition_info.get("ready", False) or bool(pre_info.get("failure")) or done:
            break

    return {
        "info": pre_info,
        "done": bool(done),
        "executed_steps": int(executed_steps),
        "action_debug": action_debug,
    }


def _run_stable_grasp_phase(env, stable_grasp_steps: int) -> Dict[str, Any]:
    """Run a minimal stable_grasp continuation after task entry."""
    return _run_stable_grasp_phase_with_mode(
        env=env,
        stable_grasp_steps=stable_grasp_steps,
        stable_grasp_phase_mode=STABLE_GRASP_PHASE_MODE_ZERO_ACTION,
    )


def _run_stable_grasp_phase_with_mode(
    env,
    stable_grasp_steps: int,
    stable_grasp_phase_mode: str,
) -> Dict[str, Any]:
    """Run the stable_grasp phase with the selected continuation mode."""
    stable_info: Dict[str, Any] = {}
    done = False
    stable_step_count = 0
    zero_action = np.zeros(env.nu, dtype=np.float32)
    controller_name = ""
    controller_summaries = []
    official_metric_history = []

    while stable_step_count < max(1, stable_grasp_steps) and not done:
        if stable_grasp_phase_mode == STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER:
            action, action_debug = compute_stable_grasp_scripted_action(env)
            controller_name = str(action_debug.get("controller_name", ""))
        elif stable_grasp_phase_mode == STABLE_GRASP_PHASE_MODE_ZERO_ACTION:
            action = zero_action
            action_debug = {
                "controller_name": "stable_grasp_zero_action_compatibility_mode",
                "controller_type": "compatibility_mode",
                "temporary_backend": True,
                "learned_policy": False,
                "benchmark_policy": False,
                "real_hand_controller": False,
                "notes": (
                    "Compatibility mode only. No scripted closure is applied during stable_grasp."
                ),
                "action_norm": 0.0,
                "action_max_abs": 0.0,
            }
            controller_name = str(action_debug["controller_name"])
        else:
            raise ValueError(f"Unsupported stable_grasp phase mode: {stable_grasp_phase_mode}")

        _, _, done, stable_info = env.step(action)
        stable_step_count += 1
        controller_summaries.append(
            {
                "stable_step_index": int(stable_step_count),
                "controller_summary": action_debug,
                "checker_reason": str(stable_info.get("stable_grasp_reason", "")),
                "success": bool(stable_info.get("success", False)),
                "failure": bool(stable_info.get("failure", False)),
            }
        )
        official_metric_history.append(
            dict(stable_info.get("stable_grasp_official_metrics", {}))
        )
        if stable_info.get("success") or stable_info.get("failure"):
            break

    return {
        "info": stable_info,
        "done": bool(done),
        "executed_steps": int(stable_step_count),
        "action_mode": str(stable_grasp_phase_mode),
        "controller_name": controller_name,
        "controller_summaries": controller_summaries,
        "official_metric_history": official_metric_history,
    }


def run_pre_grasp_to_stable_grasp_episode(
    rollout_mode: str,
    pre_grasp_steps: int,
    stable_grasp_steps: int,
    include_debug: bool,
    stable_grasp_phase_mode: str = STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
    max_steps: int | None = None,
) -> Dict[str, Any]:
    """Run one transition-based episode and return structured evaluation artifacts."""
    if rollout_mode == ROLLOUT_MODE_DIAGNOSTIC_SEEDED:
        pre_grasp_task_kwargs = {
            "transition_to_stable_grasp": {
                "required_ready_steps": 1,
            },
        }
    else:
        pre_grasp_task_kwargs = {}

    resolved_max_steps = int(
        max(max_steps or 0, pre_grasp_steps + stable_grasp_steps + 4, 8)
    )
    env = ShadowGraspEnv(
        max_steps=resolved_max_steps,
        task_name="pre_grasp",
        task_kwargs=pre_grasp_task_kwargs,
    )

    try:
        state_preparation = _prepare_episode_start(env, rollout_mode=rollout_mode)
        pre_phase = _run_pre_grasp_phase(
            env,
            rollout_mode=rollout_mode,
            pre_grasp_steps=pre_grasp_steps,
        )
        pre_info = dict(pre_phase["info"])
        transition_info = _build_transition_info(pre_info)
        transition_ready = bool(transition_info.get("ready", False))
        backend_info = env.get_hand_adapter().get_backend_metadata()

        entry_snapshot = {}
        episode_result = None
        stable_phase: Dict[str, Any] = {
            "info": {},
            "done": False,
            "executed_steps": 0,
            "action_mode": "not_entered",
        }

        if transition_ready:
            entry_snapshot_obj = _build_entry_snapshot(
                env,
                notes=(
                    "Created by the rollout evaluator from the transition-ready handoff state "
                    "before the first stable_grasp evaluation step."
                ),
            )
            entry_snapshot = entry_snapshot_obj.to_payload()

            stable_task = StableGraspTask()
            stable_task.set_entry_snapshot(entry_snapshot_obj)
            env.set_task(task=stable_task)
            stable_task.reset_task(env)

            stable_phase = _run_stable_grasp_phase_with_mode(
                env=env,
                stable_grasp_steps=stable_grasp_steps,
                stable_grasp_phase_mode=stable_grasp_phase_mode,
            )
            stable_info = dict(stable_phase["info"])
            stable_phase_note = (
                "temporary stable_grasp scripted execution"
                if stable_grasp_phase_mode == STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER
                else "zero_action compatibility continuation"
            )
            episode_result = EpisodeEvaluationResult.from_task_info(
                task_name="stable_grasp",
                info=stable_info,
                step_count=int(stable_phase["executed_steps"]),
                max_steps=int(env.max_steps),
                transition_info=transition_info,
                entry_snapshot=stable_info.get("stable_grasp_entry_snapshot", entry_snapshot),
                notes=(
                    f"Environment-driven minimal rollout with {stable_phase_note}."
                    if rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY
                    else (
                        "Diagnostic-only seeded rollout for contract and report-chain verification "
                        f"with {stable_phase_note}."
                    )
                ),
                reached_time_limit=bool(stable_phase["done"] and env.current_step >= env.max_steps),
            )
        else:
            episode_result = EpisodeEvaluationResult.from_transition_blocked(
                task_name="stable_grasp",
                transition_info=transition_info,
                step_count=0,
                max_steps=int(env.max_steps),
                backend_info=backend_info,
                notes=(
                    "stable_grasp entry was blocked before the task could start."
                    if rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY
                    else "Diagnostic seeded rollout did not reach stable_grasp entry."
                ),
                reached_time_limit=bool(pre_phase["done"] and env.current_step >= env.max_steps),
            )

        episode_report = build_report_payload(
            config={
                "script": "scripts/diagnostics/structured_rollout_eval.py",
                "task_name": "stable_grasp",
                "eval_mode": rollout_mode,
                "official_eval_eligible": bool(rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY),
                "entry_snapshot_owner": CANONICAL_ENTRY_SNAPSHOT_OWNER,
                "entry_snapshot_fallback_owner": "stable_grasp_checker",
                "pre_grasp_steps": int(pre_grasp_steps),
                "stable_grasp_steps": int(stable_grasp_steps),
                "stable_grasp_phase_mode": str(stable_grasp_phase_mode),
                "max_steps": int(env.max_steps),
                "backend": "shadow_backend_temporary",
            },
            episode_results=[episode_result],
            include_debug=include_debug,
        )

        return {
            "rollout_mode": rollout_mode,
            "environment_driven": bool(rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY),
            "official_eval_eligible": bool(rollout_mode == ROLLOUT_MODE_ENVIRONMENT_ONLY),
            "entry_snapshot_owner": CANONICAL_ENTRY_SNAPSHOT_OWNER,
            "state_preparation": state_preparation,
            "pre_grasp_task_kwargs": pre_grasp_task_kwargs,
            "stable_grasp_phase_mode": str(stable_grasp_phase_mode),
            "pre_grasp_transition_input": dict(pre_info.get("pre_to_stable_transition_input", {})),
            "transition_decision": transition_info,
            "entry_snapshot": entry_snapshot,
            "episode_result": episode_result,
            "episode_payload": episode_result.to_payload(include_debug=include_debug),
            "episode_report": episode_report,
            "phase_debug": {
                "pre_grasp": {
                    "executed_steps": int(pre_phase["executed_steps"]),
                    "action_mode": pre_phase["action_debug"].get("action_mode", ""),
                    "pose_debug": pre_phase["action_debug"].get("pose_debug", {}),
                },
                "stable_grasp": {
                    "executed_steps": int(stable_phase["executed_steps"]),
                    "action_mode": stable_phase.get("action_mode", ""),
                    "controller_name": stable_phase.get("controller_name", ""),
                    "controller_summaries": stable_phase.get("controller_summaries", []),
                    "official_metric_history": stable_phase.get("official_metric_history", []),
                },
            },
        }
    finally:
        env.close()


def run_structured_rollout(
    pre_grasp_steps: int,
    stable_grasp_steps: int,
    include_debug: bool,
    stable_grasp_phase_mode: str = STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
) -> Dict[str, Any]:
    """Run the diagnostic-only structured rollout verification path."""
    episode_artifact = run_pre_grasp_to_stable_grasp_episode(
        rollout_mode=ROLLOUT_MODE_DIAGNOSTIC_SEEDED,
        pre_grasp_steps=pre_grasp_steps,
        stable_grasp_steps=stable_grasp_steps,
        include_debug=include_debug,
        stable_grasp_phase_mode=stable_grasp_phase_mode,
    )
    return {
        "structured_rollout_path": (
            "pre_grasp_transition_input -> transition_decision -> "
            "stable_grasp_entry_snapshot -> stable_grasp_episode_summary"
        ),
        "rollout_mode": episode_artifact["rollout_mode"],
        "stable_grasp_phase_mode": episode_artifact["stable_grasp_phase_mode"],
        "official_eval_eligible": False,
        "entry_snapshot_owner": episode_artifact["entry_snapshot_owner"],
        "backend": "shadow_backend_temporary",
        "pre_grasp_transition_input": episode_artifact["pre_grasp_transition_input"],
        "transition_decision": episode_artifact["transition_decision"],
        "entry_snapshot": episode_artifact["entry_snapshot"],
        "state_preparation": episode_artifact["state_preparation"],
        "teleport_info": (
            episode_artifact["state_preparation"]
            if episode_artifact["state_preparation"].get("diagnostic_only", False)
            else {}
        ),
        "stable_grasp_episode": episode_artifact["episode_payload"],
        "official_report": episode_artifact["episode_report"],
        "phase_debug": episode_artifact["phase_debug"] if include_debug else {},
        "notes": (
            "Diagnostic-only rollout. This path may use transition-seeded state preparation and "
            "must not be interpreted as official task-performance evaluation."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnostic-only rollout verification for pre_grasp -> stable_grasp contracts. "
            "This is not an official task-performance evaluation script."
        )
    )
    parser.add_argument(
        "--pre-grasp-steps",
        type=int,
        default=2,
        help="Maximum pre_grasp steps before switching or stopping",
    )
    parser.add_argument(
        "--stable-grasp-steps",
        type=int,
        default=3,
        help="Stable_grasp steps to evaluate after entry snapshot creation",
    )
    parser.add_argument(
        "--stable-grasp-phase-mode",
        type=str,
        default=STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
        choices=[
            STABLE_GRASP_PHASE_MODE_ZERO_ACTION,
            STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER,
        ],
        help="Stable_grasp continuation mode for diagnostic rollout verification",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="",
        help="Optional JSON report path for the official episode payload",
    )
    parser.add_argument(
        "--include-debug",
        action="store_true",
        help="Include debug metrics in the emitted payload and saved report",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent level",
    )
    args = parser.parse_args()

    payload = run_structured_rollout(
        pre_grasp_steps=args.pre_grasp_steps,
        stable_grasp_steps=args.stable_grasp_steps,
        include_debug=args.include_debug,
        stable_grasp_phase_mode=args.stable_grasp_phase_mode,
    )

    text = json.dumps(payload, indent=args.indent, ensure_ascii=False)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_text = json.dumps(
            payload["official_report"],
            indent=args.indent,
            ensure_ascii=False,
        )
        report_path.write_text(report_text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
