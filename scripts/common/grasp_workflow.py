#!/usr/bin/env python3
"""Shared helpers for grasp demo, data collection, and policy evaluation."""

from __future__ import annotations

import mujoco
import numpy as np

DEFAULT_PRE_GRASP_START_BIAS = np.array([0.01, 0.0, -0.005], dtype=np.float32)
STABLE_GRASP_PHASE_MODE_ZERO_ACTION = "zero_action"
STABLE_GRASP_PHASE_MODE_SCRIPTED_CONTROLLER = "scripted_controller"


def get_task_name(enable_catch_task, structured_task_name=None):
    """Return a stable task label for reports and metadata."""
    if structured_task_name:
        return str(structured_task_name)
    return "catch_and_hold" if enable_catch_task else "static_grasp"


def get_success_rule(enable_catch_task, structured_task_name=None):
    """Return the success-rule label for the current task variant."""
    if structured_task_name == "pre_grasp":
        return "palm_pose_matches_object_pose_plus_offset_for_hold_steps"
    if structured_task_name == "stable_grasp":
        return "stable_grasp_retained_contact_and_closure_for_hold_steps_shadow_backend_v1"
    if structured_task_name == "lift_and_hold":
        return "structured_lift_and_hold_rule"
    if enable_catch_task:
        return "palm_and_thumb_plus_3_finger_groups_contact_for_50_steps_and_object_not_on_floor"
    return "palm_and_thumb_plus_3_finger_groups_contact_for_50_steps"


def find_body_id_by_keywords(model, keywords):
    """Find the first body whose name contains any of the given keywords."""
    for body_id in range(model.nbody):
        body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id)
        if not body_name:
            continue
        lower_name = body_name.lower()
        if any(keyword in lower_name for keyword in keywords):
            return body_id
    return None


def configure_controller(controller, enable_catch_task, profile="default", max_steps=None):
    """Apply task-specific stage timing to the enhanced controller."""
    if not hasattr(controller, "phase_durations"):
        return

    if enable_catch_task:
        controller.phase_durations = {
            "approach": 80,
            "close_fingers": 30,
            "lift": 50,
        }
        if hasattr(controller, "hold_after_lift"):
            controller.hold_after_lift = True
        if hasattr(controller, "hold_wrist_strength"):
            controller.hold_wrist_strength = 0.05
    else:
        if profile == "expert_collection":
            episode_steps = max(int(max_steps or 400), 280)
            hold_budget = min(100, max(60, episode_steps // 4))
            motion_budget = max(180, episode_steps - hold_budget)
            approach_steps = max(110, int(round(motion_budget * 0.57)))
            close_fingers_steps = max(45, int(round(motion_budget * 0.23)))
            reserved_lift_steps = 50
            overflow = (approach_steps + close_fingers_steps + reserved_lift_steps) - motion_budget
            if overflow > 0:
                approach_reduction = min(overflow, max(0, approach_steps - 110))
                approach_steps -= approach_reduction
                overflow -= approach_reduction
            if overflow > 0:
                close_reduction = min(overflow, max(0, close_fingers_steps - 45))
                close_fingers_steps -= close_reduction
                overflow -= close_reduction
            lift_steps = max(50, motion_budget - approach_steps - close_fingers_steps)
            controller.phase_durations = {
                # Reach hold before the episode ends while leaving time to record it.
                "approach": approach_steps,
                "close_fingers": close_fingers_steps,
                "lift": lift_steps,
            }
        else:
            controller.phase_durations = {
                "approach": 200,
                "close_fingers": 100,
                "lift": 200,
            }
        if hasattr(controller, "hold_after_lift"):
            controller.hold_after_lift = True
        if hasattr(controller, "hold_wrist_strength"):
            controller.hold_wrist_strength = 0.03


def _set_object_pose(env, position):
    """Write the object's free-joint pose directly into qpos/qvel."""
    if env.object_joint_id is None:
        return False

    joint_qpos_adr = env.model.jnt_qposadr[env.object_joint_id]
    joint_dof_adr = env.model.jnt_dofadr[env.object_joint_id]
    preserved_qvel = env.data.qvel[joint_dof_adr:joint_dof_adr + 6].copy()
    env.data.qpos[joint_qpos_adr:joint_qpos_adr + 3] = position
    env.data.qpos[joint_qpos_adr + 3:joint_qpos_adr + 7] = np.array([1.0, 0.0, 0.0, 0.0])
    env.data.qvel[joint_dof_adr:joint_dof_adr + 6] = 0.0
    if getattr(env, "enable_catch_task", False):
        env.data.qvel[joint_dof_adr:joint_dof_adr + 6] = preserved_qvel
    mujoco.mj_forward(env.model, env.data)
    return True


def compute_demo_object_position(env):
    """Compute an object pose that sits between the palm and fingertips."""
    palm_body_id = find_body_id_by_keywords(env.model, ["rh_palm", "palm"])
    fingertip_body_id = find_body_id_by_keywords(env.model, ["mfdistal", "ffdistal", "distal"])
    if palm_body_id is None or fingertip_body_id is None:
        return None

    palm_pos = env.data.xpos[palm_body_id].copy()
    fingertip_pos = env.data.xpos[fingertip_body_id].copy()
    demo_object_pos = (palm_pos + fingertip_pos) / 2.0
    demo_object_pos[2] = max(palm_pos[2] + 0.03, 0.04)
    return demo_object_pos


def get_pre_grasp_pose_debug(env):
    """Return current and target task-space poses for the active pre-grasp task."""
    if getattr(env, "task", None) is None or env.get_task_name() != "pre_grasp":
        raise ValueError("get_pre_grasp_pose_debug requires an active pre_grasp task")

    target_pose = env.task.get_target_palm_pose(env)
    current_palm_pos = env._get_palm_reference_position().astype(np.float32)
    target_palm_pos = np.asarray(target_pose["target_palm_position"], dtype=np.float32)
    pos_error = target_palm_pos - current_palm_pos
    distance = float(np.linalg.norm(pos_error))
    return {
        "current_palm_pos": current_palm_pos,
        "target_palm_pos": target_palm_pos,
        "pos_error": pos_error.astype(np.float32),
        "distance": distance,
    }


def compute_pre_grasp_expert_action(env, gain_scale=1.0, clip_scale=1.0):
    """A minimal reach-style controller for pre-grasp without invoking IK."""
    pose_debug = get_pre_grasp_pose_debug(env)
    x_err, y_err, z_err = pose_debug["pos_error"].tolist()
    gain_scale = float(gain_scale)
    clip_scale = max(float(clip_scale), 1e-6)

    # Heuristic mapping tuned for the limited wrist/finger DOFs available in the hand-only model.
    wrist_y_cmd = np.clip(
        -gain_scale * (14.0 * y_err + 28.0 * z_err + 8.0 * x_err),
        -1.0 * clip_scale,
        1.0 * clip_scale,
    )
    wrist_x_cmd = np.clip(
        -gain_scale * (16.0 * x_err + 10.0 * y_err + 24.0 * z_err),
        -1.0 * clip_scale,
        1.0 * clip_scale,
    )
    finger_cmd = np.clip(
        gain_scale * 14.0 * (0.8 * x_err + 0.35 * y_err - 1.1 * z_err),
        -0.6 * clip_scale,
        0.8 * clip_scale,
    )
    abduct_cmd = np.clip(
        -gain_scale * 10.0 * y_err,
        -0.3 * clip_scale,
        0.3 * clip_scale,
    )

    action = np.zeros(env.nu, dtype=np.float32)
    action[0] = float(wrist_y_cmd)
    action[1] = float(wrist_x_cmd)

    # Thumb and fingers contribute a small palm-frame shift without closing aggressively.
    action[2] = float(np.clip(0.20 * finger_cmd, -0.4, 0.4))
    for idx in [3, 4, 5, 6]:
        action[idx] = float(np.clip(0.35 * finger_cmd, -0.5, 0.6))
    for idx in [7, 11, 15, 19]:
        action[idx] = float(np.clip(abduct_cmd, -0.3 * clip_scale, 0.3 * clip_scale))
    for idx in [8, 12, 16, 20]:
        action[idx] = float(np.clip(0.45 * finger_cmd, -0.5 * clip_scale, 0.6 * clip_scale))
    for idx in [9, 10, 13, 14, 17, 18, 21, 22, 23]:
        action[idx] = float(np.clip(0.55 * finger_cmd, -0.6 * clip_scale, 0.7 * clip_scale))
    return np.clip(action, -1.0, 1.0).astype(np.float32), pose_debug


def _get_shadow_actuator_groups(env):
    """Cache actuator groups for the temporary stable_grasp scripted backend."""
    cached = getattr(env, "_stable_grasp_scripted_actuator_groups", None)
    if cached is not None:
        return cached

    groups = {
        "wrist": [],
        "thumb": [],
        "index": [],
        "middle": [],
        "ring": [],
        "little": [],
    }
    for actuator_id in range(env.model.nu):
        actuator_name = mujoco.mj_id2name(
            env.model,
            mujoco.mjtObj.mjOBJ_ACTUATOR,
            actuator_id,
        )
        if not actuator_name:
            continue
        if "WRJ" in actuator_name:
            groups["wrist"].append((actuator_id, actuator_name))
        elif "THJ" in actuator_name:
            groups["thumb"].append((actuator_id, actuator_name))
        elif "FFJ" in actuator_name:
            groups["index"].append((actuator_id, actuator_name))
        elif "MFJ" in actuator_name:
            groups["middle"].append((actuator_id, actuator_name))
        elif "RFJ" in actuator_name:
            groups["ring"].append((actuator_id, actuator_name))
        elif "LFJ" in actuator_name:
            groups["little"].append((actuator_id, actuator_name))

    env._stable_grasp_scripted_actuator_groups = groups
    return groups


def _resolve_stable_grasp_entry_relation(env):
    """Return the task entry relation used to stabilize the temporary scripted backend."""
    if getattr(env, "task", None) is None or env.get_task_name() != "stable_grasp":
        return None
    if not hasattr(env.task, "get_entry_snapshot"):
        return None

    entry_snapshot = env.task.get_entry_snapshot()
    if entry_snapshot is None:
        return None
    return {
        "entry_snapshot": entry_snapshot,
        "relative_position": np.asarray(
            entry_snapshot.relative_palm_object_relation.get("position", [0.0, 0.0, 0.0]),
            dtype=np.float32,
        ),
    }


def _compute_shadow_digit_command(actuator_name: str, base_close: float, thumb_close: float) -> float:
    """Return a backend-specific joint command for the temporary scripted controller."""
    if "THJ" in actuator_name:
        if actuator_name.endswith("THJ5"):
            return 0.08 * thumb_close
        if actuator_name.endswith("THJ4"):
            return 0.14 * thumb_close
        if actuator_name.endswith("THJ3"):
            return 0.28 * thumb_close
        if actuator_name.endswith("THJ2"):
            return 0.18 * thumb_close
        if actuator_name.endswith("THJ1"):
            return 0.42 * thumb_close
        return 0.20 * thumb_close

    if actuator_name.endswith("J4") or actuator_name.endswith("LFJ5"):
        return 0.08 * base_close
    if actuator_name.endswith("J3"):
        return 0.30 * base_close
    if actuator_name.endswith("J2"):
        return 0.46 * base_close
    if actuator_name.endswith("J1"):
        return 0.58 * base_close
    return 0.20 * base_close


def compute_stable_grasp_scripted_action(env, close_rate=1.0, wrist_gain=1.0):
    """
    Temporary stable_grasp scripted backend.

    This is a minimal joint-level scripted controller for the current Shadow backend. It is
    not a learned policy, not a benchmark controller, and not a future real-hand controller.
    """
    if getattr(env, "task", None) is None or env.get_task_name() != "stable_grasp":
        raise ValueError("compute_stable_grasp_scripted_action requires an active stable_grasp task")

    adapter = env.get_hand_adapter()
    relative_pose = adapter.get_relative_palm_to_object()
    contact_summary = adapter.get_contact_summary()
    closure_summary = adapter.get_hand_closure()
    entry_relation = _resolve_stable_grasp_entry_relation(env)
    actuator_groups = _get_shadow_actuator_groups(env)

    if entry_relation is not None:
        entry_snapshot = entry_relation["entry_snapshot"]
        target_relative_position = entry_relation["relative_position"]
        stable_step_index = max(int(env.current_step - int(entry_snapshot.entry_step_index)), 0)
        entry_source = str(entry_snapshot.entry_source)
    else:
        entry_snapshot = None
        target_relative_position = np.asarray(relative_pose.position, dtype=np.float32)
        stable_step_index = 0
        entry_source = "entry_snapshot_unavailable"

    relative_error = target_relative_position - np.asarray(relative_pose.position, dtype=np.float32)
    wrist_gain = float(wrist_gain)
    close_rate = float(close_rate)

    closure_progress = min((stable_step_index + 1) / 6.0, 1.0)
    base_close = 0.22 + 0.42 * closure_progress
    thumb_close = 0.18 + 0.34 * closure_progress
    wrist_hold_scale = 1.0

    # Final minimal refinement attempt:
    # Once support contact is already present, stop pushing the hand as aggressively and move
    # earlier toward a hold-like continuation. This is a single failure-mode-driven adjustment
    # for insufficient sustained contact, not the start of an open-ended tuning loop.
    contact_hold_like = bool(
        contact_summary.support_region_count >= 3
        or (
            contact_summary.support_region_count >= 2
            and contact_summary.sustained_contact_steps >= 1
        )
    )

    if contact_summary.has_contact:
        wrist_hold_scale = 0.60

    if contact_summary.support_region_count >= 2:
        base_close *= 0.78
        thumb_close *= 0.86
    if contact_hold_like:
        base_close *= 0.72
        thumb_close *= 0.86
        wrist_hold_scale = 0.35
    if contact_summary.support_region_count >= 3 or closure_summary.closure_metric >= 0.22:
        base_close *= 0.70
        thumb_close *= 0.78
    if closure_summary.closure_metric >= 0.32:
        base_close *= 0.62
        thumb_close *= 0.70

    base_close = float(np.clip(base_close * close_rate, 0.0, 0.72))
    thumb_close = float(np.clip(thumb_close * close_rate, 0.0, 0.68))

    wrist_y_cmd = float(
        np.clip(
            -wrist_gain
            * wrist_hold_scale
            * (5.0 * relative_error[1] + 8.0 * relative_error[2] + 3.0 * relative_error[0]),
            -0.18,
            0.18,
        )
    )
    wrist_x_cmd = float(
        np.clip(
            -wrist_gain
            * wrist_hold_scale
            * (6.0 * relative_error[0] + 2.0 * relative_error[1] + 6.0 * relative_error[2]),
            -0.18,
            0.18,
        )
    )

    action = np.zeros(env.nu, dtype=np.float32)
    controller_group_commands = {
        "wrist": {"wrj2": wrist_y_cmd, "wrj1": wrist_x_cmd},
        "thumb": float(thumb_close),
        "index": float(base_close),
        "middle": float(base_close),
        "ring": float(base_close * 0.94),
        "little": float(base_close * 0.88),
    }

    for actuator_id, actuator_name in actuator_groups["wrist"]:
        if actuator_name.endswith("WRJ2"):
            action[actuator_id] = wrist_y_cmd
        elif actuator_name.endswith("WRJ1"):
            action[actuator_id] = wrist_x_cmd

    for group_name in ("thumb", "index", "middle", "ring", "little"):
        group_close = (
            thumb_close if group_name == "thumb" else controller_group_commands[group_name]
        )
        for actuator_id, actuator_name in actuator_groups[group_name]:
            action[actuator_id] = float(
                np.clip(
                    _compute_shadow_digit_command(
                        actuator_name=actuator_name,
                        base_close=float(group_close),
                        thumb_close=float(thumb_close),
                    ),
                    -1.0,
                    1.0,
                )
            )

    action = np.clip(action, -1.0, 1.0).astype(np.float32)
    debug = {
        "controller_name": "stable_grasp_scripted_shadow_backend_v1",
        "controller_type": "temporary_scripted_backend",
        "temporary_backend": True,
        "learned_policy": False,
        "benchmark_policy": False,
        "real_hand_controller": False,
        "notes": (
            "Temporary Shadow backend scripted controller. Uses joint-level closure plus small "
            "wrist stabilization. Replace for future learned or real-hand controllers."
        ),
        "stable_step_index": int(stable_step_index),
        "entry_source": entry_source,
        "support_region_count": int(contact_summary.support_region_count),
        "support_regions": list(contact_summary.support_regions),
        "closure_metric": float(closure_summary.closure_metric),
        "contact_hold_like": bool(contact_hold_like),
        "wrist_hold_scale": float(wrist_hold_scale),
        "relative_palm_object_distance": float(relative_pose.distance),
        "relative_position_error": relative_error.astype(np.float32).tolist(),
        "group_commands": controller_group_commands,
        "action_norm": float(np.linalg.norm(action)),
        "action_max_abs": float(np.max(np.abs(action))) if len(action) else 0.0,
    }
    return action, debug


def place_object(
    env,
    placement_mode="scene",
    placement_jitter=0.0,
    verbose=False,
    pre_grasp_start_bias=None,
):
    """
    Place the object according to the chosen mode.

    Modes:
    - scene: keep the scene-default pose and optionally add jitter
    - demo: move the object into the palm workspace and optionally add jitter
    """
    if placement_mode not in {"scene", "demo"}:
        raise ValueError(f"Unknown placement_mode: {placement_mode}")

    requested_mode = placement_mode
    effective_mode = placement_mode
    structured_task_name = env.get_task_name() if getattr(env, "task", None) is not None else None

    if env.enable_catch_task:
        # Catch-task episodes should keep the falling-object spawn in the scene,
        # but we still allow small jitter for robustness experiments.
        effective_mode = "scene"
        target_position = env._get_object_position().copy()
        repositioned = False
    elif placement_mode == "demo" and structured_task_name == "pre_grasp":
        target_position = compute_demo_object_position(env)
        if target_position is not None:
            start_bias = (
                np.asarray(pre_grasp_start_bias, dtype=np.float32)
                if pre_grasp_start_bias is not None
                else DEFAULT_PRE_GRASP_START_BIAS
            )
            target_position = target_position + start_bias
            target_position[2] = max(target_position[2], 0.035)
        repositioned = target_position is not None
    elif placement_mode == "demo":
        target_position = compute_demo_object_position(env)
        repositioned = target_position is not None
    else:
        target_position = env._get_object_position().copy()
        repositioned = False

    if target_position is None:
        target_position = env._get_object_position().copy()

    if placement_jitter > 0:
        jitter = np.random.uniform(-placement_jitter, placement_jitter, size=3)
        target_position = target_position + jitter
        target_position[2] = max(target_position[2], 0.035)

    _set_object_pose(env, target_position)

    if verbose:
        print(f"Requested placement mode: {requested_mode}")
        print(f"Effective placement mode: {effective_mode}")
        print(f"Object placement jitter: {placement_jitter:.4f} m")
        print(f"Object position after placement: {target_position}")

    return {
        "placement_mode": effective_mode,
        "requested_placement_mode": requested_mode,
        "effective_placement_mode": effective_mode,
        "placement_jitter": float(placement_jitter),
        "structured_task_name": structured_task_name,
        "repositioned": bool(repositioned),
        "pre_grasp_start_bias": (
            np.asarray(pre_grasp_start_bias, dtype=np.float32).tolist()
            if pre_grasp_start_bias is not None and structured_task_name == "pre_grasp"
            else DEFAULT_PRE_GRASP_START_BIAS.tolist()
            if structured_task_name == "pre_grasp"
            else None
        ),
        "position": target_position.tolist(),
    }
