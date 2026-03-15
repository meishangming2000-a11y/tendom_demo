#!/usr/bin/env python3
"""Shared helpers for grasp demo, data collection, and policy evaluation."""

from __future__ import annotations

import mujoco
import numpy as np


def get_task_name(enable_catch_task):
    """Return a stable task label for reports and metadata."""
    return "catch_and_hold" if enable_catch_task else "static_grasp"


def get_success_rule(enable_catch_task):
    """Return the success-rule label for the current task variant."""
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


def place_object(env, placement_mode="scene", placement_jitter=0.0, verbose=False):
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

    if env.enable_catch_task:
        # Catch-task episodes should keep the falling-object spawn in the scene,
        # but we still allow small jitter for robustness experiments.
        effective_mode = "scene"
        target_position = env._get_object_position().copy()
        repositioned = False
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
        "repositioned": bool(repositioned),
        "position": target_position.tolist(),
    }
