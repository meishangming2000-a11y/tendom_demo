#!/usr/bin/env python3
"""Retarget visual 21-landmark palm traces to the Shadow Hand MuJoCo action layout."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from vision.palm_landmarks import frames_to_arrays, summarize_palm_trace
from vision.shadow_retarget import (
    SHADOW_ACTUATOR_NAMES,
    RetargetConfig,
    action_summary,
    config_to_metadata,
    retarget_landmark_sequence,
)


def _load_json_frames(path: Path) -> List[Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        frames = payload.get("frames", [])
    else:
        frames = payload
    if not isinstance(frames, list):
        raise ValueError("Expected JSON frames to be a list or {'frames': [...]} payload")
    return frames


def _metadata_dict(payload, key: str = "metadata") -> dict:
    if key not in payload:
        return {}
    raw = payload[key]
    return dict(raw.item() if hasattr(raw, "item") else raw)


def load_landmark_trace(args: argparse.Namespace) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Load landmarks from a palm-trace NPZ or a raw JSON frame payload."""
    if args.input_json:
        frames = _load_json_frames(Path(args.input_json))
        timestamps, landmarks, features, _ = frames_to_arrays(frames)
        metadata = {
            "source_kind": "json_landmarks",
            "source": args.input_json,
            "summary": summarize_palm_trace(features, timestamps),
        }
        return timestamps, landmarks, metadata

    if not args.palm_trace:
        raise ValueError("Provide --palm-trace or --input-json")

    palm_path = Path(args.palm_trace)
    if not palm_path.exists():
        raise FileNotFoundError(palm_path)

    payload = np.load(palm_path, allow_pickle=True)
    if "landmarks" not in payload:
        raise ValueError(f"Palm trace is missing 'landmarks': {palm_path}")

    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    timestamps = (
        np.asarray(payload["timestamps"], dtype=np.float32)
        if "timestamps" in payload
        else np.arange(landmarks.shape[0], dtype=np.float32)
    )
    metadata = _metadata_dict(payload)
    metadata.setdefault("source_kind", "vision_palm_trace_npz")
    metadata.setdefault("source", str(palm_path))
    return timestamps, landmarks, metadata


def build_retarget_config(args: argparse.Namespace) -> RetargetConfig:
    return RetargetConfig(
        open_action=float(args.open_action),
        proximal_closed_action=float(args.proximal_closed_action),
        distal_closed_action=float(args.distal_closed_action),
        abduction_scale=float(args.abduction_scale),
        thumb_open_action=float(args.thumb_open_action),
        thumb_closed_action=float(args.thumb_closed_action),
        wrist_scale=float(args.wrist_scale),
        smoothing_alpha=float(args.smoothing_alpha),
        mirror_x=bool(args.mirror_x),
    )


def slice_trace(
    timestamps: np.ndarray,
    landmarks: np.ndarray,
    start_frame: int,
    end_frame: int,
    stride: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Apply frame-range slicing to a loaded landmark trace."""
    timestamps = np.asarray(timestamps, dtype=np.float32)
    landmarks = np.asarray(landmarks, dtype=np.float32)
    total_frames = int(landmarks.shape[0])
    stride = max(1, int(stride))
    start = max(0, int(start_frame))
    end = total_frames if int(end_frame) <= 0 else min(total_frames, int(end_frame))
    if start >= end:
        raise ValueError(f"Empty frame slice: start={start}, end={end}, total_frames={total_frames}")

    indices = np.arange(start, end, stride, dtype=np.int64)
    sliced_timestamps = timestamps[indices].astype(np.float32)
    if sliced_timestamps.size:
        sliced_timestamps = sliced_timestamps - sliced_timestamps[0]
    return (
        sliced_timestamps,
        landmarks[indices].astype(np.float32),
        indices.astype(np.float32),
        {
            "total_source_frames": total_frames,
            "start_frame": int(start),
            "end_frame_exclusive": int(end),
            "stride": int(stride),
            "retained_frames": int(len(indices)),
        },
    )


def time_scale_trace(
    timestamps: np.ndarray,
    landmarks: np.ndarray,
    actions: np.ndarray,
    source_frame_indices: np.ndarray,
    action_time_scale: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Insert interpolated steps between landmark/action frames for slower replay."""
    timestamps = np.asarray(timestamps, dtype=np.float32)
    landmarks = np.asarray(landmarks, dtype=np.float32)
    actions = np.asarray(actions, dtype=np.float32)
    source_frame_indices = np.asarray(source_frame_indices, dtype=np.float32)
    scale = max(1, int(action_time_scale))
    frame_count = int(actions.shape[0])
    if scale <= 1 or frame_count <= 1:
        return (
            timestamps,
            landmarks,
            actions,
            source_frame_indices,
            {
                "action_time_scale": int(scale),
                "input_frames": frame_count,
                "output_steps": frame_count,
                "interpolation": "none",
            },
        )

    expanded_timestamps = []
    expanded_landmarks = []
    expanded_actions = []
    expanded_source_indices = []
    for frame_idx in range(frame_count - 1):
        for substep in range(scale):
            alpha = float(substep) / float(scale)
            inv_alpha = 1.0 - alpha
            expanded_timestamps.append(inv_alpha * timestamps[frame_idx] + alpha * timestamps[frame_idx + 1])
            expanded_landmarks.append(inv_alpha * landmarks[frame_idx] + alpha * landmarks[frame_idx + 1])
            expanded_actions.append(inv_alpha * actions[frame_idx] + alpha * actions[frame_idx + 1])
            expanded_source_indices.append(
                inv_alpha * source_frame_indices[frame_idx] + alpha * source_frame_indices[frame_idx + 1]
            )

    expanded_timestamps.append(timestamps[-1])
    expanded_landmarks.append(landmarks[-1])
    expanded_actions.append(actions[-1])
    expanded_source_indices.append(source_frame_indices[-1])

    return (
        np.asarray(expanded_timestamps, dtype=np.float32),
        np.asarray(expanded_landmarks, dtype=np.float32),
        np.asarray(expanded_actions, dtype=np.float32),
        np.asarray(expanded_source_indices, dtype=np.float32),
        {
            "action_time_scale": int(scale),
            "input_frames": frame_count,
            "output_steps": int((frame_count - 1) * scale + 1),
            "interpolation": "linear_actions_and_landmarks",
        },
    )


def save_retarget_output(
    output_path: Path,
    timestamps: np.ndarray,
    landmarks: np.ndarray,
    actions: np.ndarray,
    metadata: Dict[str, Any],
    debug: List[Dict[str, Any]],
    save_debug: bool,
    source_frame_indices: np.ndarray | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamps": timestamps.astype(np.float32),
        "landmarks": landmarks.astype(np.float32),
        "actions": actions.astype(np.float32),
        "actuator_names": np.asarray(SHADOW_ACTUATOR_NAMES, dtype=object),
        "metadata": metadata,
    }
    if source_frame_indices is not None:
        payload["source_frame_indices"] = np.asarray(source_frame_indices, dtype=np.float32)
    if save_debug:
        payload["frame_debug"] = np.asarray(debug, dtype=object)
    np.savez_compressed(output_path, **payload)


def rollout_actions(args: argparse.Namespace, actions: np.ndarray, source_metadata: Dict[str, Any]) -> Tuple[dict, dict]:
    """Replay retargeted Shadow actions in the current ShadowGraspEnv."""
    from scripts.common.grasp_workflow import place_object
    from src.environments.shadow_grasp_env import ShadowGraspEnv

    if actions.shape[0] == 0:
        raise ValueError("Cannot rollout an empty action sequence")

    step_limit = int(args.rollout_steps or actions.shape[0])
    step_limit = max(1, min(step_limit, actions.shape[0]))
    env = ShadowGraspEnv(max_steps=step_limit, observation_mode=args.observation_mode)
    obs = env.reset()
    placement_info = place_object(
        env,
        placement_mode=args.placement_mode,
        placement_jitter=float(args.placement_jitter),
        verbose=False,
    )
    obs = env.get_obs()

    observations = []
    rewards = []
    dones = []
    infos = []
    replayed_actions = []
    done = False

    for step_idx in range(step_limit):
        if done:
            break
        action = actions[step_idx].astype(np.float32)
        observations.append(obs.copy())
        replayed_actions.append(action.copy())
        obs, reward, done, info = env.step(action)
        rewards.append(float(reward))
        dones.append(bool(done))
        infos.append(info.copy())

    episode = {
        "observations": np.asarray(observations, dtype=np.float32),
        "actions": np.asarray(replayed_actions, dtype=np.float32),
        "rewards": np.asarray(rewards, dtype=np.float32),
        "dones": np.asarray(dones, dtype=bool),
        "infos": infos,
        "steps": int(len(replayed_actions)),
        "success": bool(any(item.get("success", False) for item in infos)),
        "terminal_success": bool(env.is_success()) if hasattr(env, "is_success") else False,
        "placement_info": placement_info,
        "metrics": {
            "contact_steps": int(sum(1 for item in infos if item.get("contact"))),
            "grasp_contact_steps": int(sum(1 for item in infos if item.get("grasp_contact"))),
            "max_contact_duration": int(max([item.get("contact_duration", 0) for item in infos] or [0])),
            "max_grasp_contact_duration": int(
                max([item.get("grasp_contact_duration", 0) for item in infos] or [0])
            ),
            "final_distance": float(infos[-1].get("distance", 0.0)) if infos else 0.0,
            "object_height": float(infos[-1].get("object_height", 0.0)) if infos else 0.0,
        },
    }
    metadata = {
        "num_episodes": 1,
        "obs_dim": int(episode["observations"].shape[1]) if episode["observations"].size else 0,
        "act_dim": int(episode["actions"].shape[1]) if episode["actions"].size else len(SHADOW_ACTUATOR_NAMES),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env": "ShadowGraspEnv",
        "task_name": "vision_shadow_retarget_replay",
        "controller": "vision_shadow_retarget_heuristic_v1",
        "success_rule": "diagnostic_replay_only_shadow_backend",
        "observation_mode": args.observation_mode,
        "placement_mode": args.placement_mode,
        "placement_jitter": float(args.placement_jitter),
        "source_retarget_metadata": source_metadata,
    }
    dataset = {
        "episodes": np.asarray([episode], dtype=object),
        "metadata": metadata,
    }
    summary = {
        "steps": int(episode["steps"]),
        "success": bool(episode["success"]),
        "terminal_success": bool(episode["terminal_success"]),
        "total_reward": float(np.sum(episode["rewards"])) if episode["rewards"].size else 0.0,
        "metrics": episode["metrics"],
    }
    return dataset, summary


def save_rollout_dataset(path: Path, dataset: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **dataset)


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def save_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retarget palm landmarks to Shadow Hand actions")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--palm-trace", default="", help="NPZ from collect_palm_trace.py")
    source.add_argument("--input-json", default="", help="Raw JSON landmark frames to convert and retarget")
    parser.add_argument(
        "--output",
        default="data/vision_shadow_retarget_latest.npz",
        help="Output NPZ containing timestamps, landmarks, and 24D Shadow actions",
    )
    parser.add_argument("--report", default="", help="Optional JSON report path")
    parser.add_argument("--rollout-output", default="", help="Optional Shadow replay dataset NPZ output")
    parser.add_argument("--rollout-steps", type=int, default=0, help="Replay at most N frames; 0 uses all frames")
    parser.add_argument(
        "--observation-mode",
        default="oracle",
        choices=["oracle", "deployable"],
        help="Observation mode for optional rollout dataset",
    )
    parser.add_argument(
        "--placement-mode",
        default="demo",
        choices=["scene", "demo"],
        help="Object placement mode for optional rollout",
    )
    parser.add_argument("--placement-jitter", type=float, default=0.0, help="Object placement jitter for rollout")
    parser.add_argument("--mirror-x", action="store_true", help="Mirror landmark x around the trace center before mapping")
    parser.add_argument("--save-debug", action="store_true", help="Store per-frame retarget debug metadata in the NPZ")
    parser.add_argument("--start-frame", type=int, default=0, help="First landmark frame to retarget")
    parser.add_argument(
        "--end-frame",
        type=int,
        default=0,
        help="Exclusive end frame; 0 retargets through the end of the trace",
    )
    parser.add_argument("--stride", type=int, default=1, help="Retarget every Nth landmark frame")
    parser.add_argument("--open-action", type=float, default=-0.65, help="Normalized action for an open non-thumb joint")
    parser.add_argument(
        "--proximal-closed-action",
        type=float,
        default=0.75,
        help="Normalized action for a closed proximal finger joint",
    )
    parser.add_argument(
        "--distal-closed-action",
        type=float,
        default=0.88,
        help="Normalized action for a closed middle/distal finger joint",
    )
    parser.add_argument("--abduction-scale", type=float, default=0.45, help="Scale for finger spread actions")
    parser.add_argument("--thumb-open-action", type=float, default=-0.55, help="Normalized action for an open thumb joint")
    parser.add_argument("--thumb-closed-action", type=float, default=0.82, help="Normalized action for a closed thumb joint")
    parser.add_argument(
        "--wrist-scale",
        type=float,
        default=0.0,
        help="Optional camera-frame palm-normal to wrist action scale; 0 keeps wrist neutral",
    )
    parser.add_argument(
        "--smoothing-alpha",
        type=float,
        default=0.15,
        help="Exponential smoothing alpha in [0, 0.99]; 0 disables smoothing",
    )
    parser.add_argument(
        "--action-time-scale",
        type=int,
        default=1,
        help="Insert N-1 interpolated MuJoCo action steps between adjacent visual frames; 1 keeps original speed",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    timestamps, landmarks, source_metadata = load_landmark_trace(args)
    timestamps, landmarks, source_frame_indices, slice_metadata = slice_trace(
        timestamps=timestamps,
        landmarks=landmarks,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        stride=args.stride,
    )
    config = build_retarget_config(args)
    actions, debug = retarget_landmark_sequence(landmarks, config=config)
    timestamps, landmarks, actions, source_frame_indices, time_scale_metadata = time_scale_trace(
        timestamps=timestamps,
        landmarks=landmarks,
        actions=actions,
        source_frame_indices=source_frame_indices,
        action_time_scale=args.action_time_scale,
    )
    if time_scale_metadata["action_time_scale"] > 1:
        debug = []
    slice_metadata["time_scale"] = time_scale_metadata

    retarget_metadata = {
        "dataset_type": "vision_shadow_retarget",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": source_metadata,
        "source_slice": slice_metadata,
        "landmark_schema": "mediapipe_21_xyz",
        "action_schema": "shadow_hand_normalized_action_v1",
        "retarget_method": "heuristic_finger_bend_and_spread_v1",
        "retarget_boundary": (
            "Diagnostic Shadow backend mapping only. No camera calibration, IK solve, "
            "object alignment, or real tendon-hand mapping is implied."
        ),
        "actuator_names": list(SHADOW_ACTUATOR_NAMES),
        "config": config_to_metadata(config),
        "summary": action_summary(actions),
        "source_frame_indices_schema": "float original-video frame index for each retargeted action step",
    }

    output_path = Path(args.output)
    save_retarget_output(
        output_path,
        timestamps,
        landmarks,
        actions,
        retarget_metadata,
        debug,
        args.save_debug,
        source_frame_indices=source_frame_indices,
    )
    print(f"Saved Shadow retarget actions: {output_path}")
    print(json.dumps(retarget_metadata["summary"], indent=2))

    rollout_summary = None
    if args.rollout_output:
        rollout_dataset, rollout_summary = rollout_actions(args, actions, retarget_metadata)
        rollout_path = Path(args.rollout_output)
        save_rollout_dataset(rollout_path, rollout_dataset)
        print(f"Saved Shadow rollout dataset: {rollout_path}")
        print(json.dumps(rollout_summary, indent=2))

    if args.report:
        report_payload = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": vars(args),
            "retarget": retarget_metadata,
            "rollout_summary": rollout_summary,
        }
        save_report(Path(args.report), report_payload)
        print(f"Saved report: {args.report}")


if __name__ == "__main__":
    main()
