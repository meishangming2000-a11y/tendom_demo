#!/usr/bin/env python3
"""Build a training-preflight dataset from replay-validated teleop episodes."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np


SIM_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SIM_ROOT.parent

SEMANTIC_FEATURE_NAMES = (
    "thumb_curl",
    "thumb_opposition",
    "thumb_spread",
    "index_curl",
    "index_spread",
    "middle_curl",
    "middle_spread",
    "ring_curl",
    "ring_spread",
    "little_curl",
    "little_spread",
    "global_curl_mean",
    "index_little_tip_span",
)

OBS_MODE_DIMS = {
    "open_close": 35,
    "palm": 76,
    "semantic": len(SEMANTIC_FEATURE_NAMES),
    "palm_open_close": 111,
    "open_close_semantic": 35 + len(SEMANTIC_FEATURE_NAMES),
    "palm_open_close_semantic": 76 + 35 + len(SEMANTIC_FEATURE_NAMES),
}

SPLIT_CODE = {
    "train": 0,
    "val": 1,
    "heldout": 2,
    "review": 3,
    "reject": 4,
    "unassigned": 5,
}

QUALITY_CODE = {
    "pass": 0,
    "review": 1,
    "reject": 2,
    "unknown": 3,
}


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, Path):
        return str(value)
    return value


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _safe_id(text: str, max_len: int = 96) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in text]
    collapsed = "_".join(part for part in "".join(chars).split("_") if part)
    return (collapsed[:max_len].strip("_") or "teleop_training_preflight")


def _semantic_vector(frame: Dict[str, Any]) -> np.ndarray:
    values = frame.get("semantic_action_v0", {}).get("values", {}) or {}
    return np.asarray([float(values.get(name, 0.0) or 0.0) for name in SEMANTIC_FEATURE_NAMES], dtype=np.float32)


def _frame_observation(frame: Dict[str, Any], obs_mode: str) -> np.ndarray:
    palm = np.asarray(frame["palm_feature_76"], dtype=np.float32)
    open_close = np.asarray(frame["open_close_feature_35"], dtype=np.float32)
    semantic = _semantic_vector(frame)
    if obs_mode == "open_close":
        return open_close
    if obs_mode == "palm":
        return palm
    if obs_mode == "semantic":
        return semantic
    if obs_mode == "palm_open_close":
        return np.concatenate([palm, open_close]).astype(np.float32)
    if obs_mode == "open_close_semantic":
        return np.concatenate([open_close, semantic]).astype(np.float32)
    if obs_mode == "palm_open_close_semantic":
        return np.concatenate([palm, open_close, semantic]).astype(np.float32)
    raise ValueError(f"Unsupported obs mode: {obs_mode}")


def _load_manifest(path: Path) -> Dict[str, Any]:
    manifest = _read_json(path)
    if manifest.get("schema_version") != "teleop_dataset_manifest_v0":
        raise ValueError(f"Expected teleop_dataset_manifest_v0, got {manifest.get('schema_version')}")
    return manifest


def _episode_replay_status(entry: Dict[str, Any]) -> str:
    replay = entry.get("replay_validation", {}) if isinstance(entry.get("replay_validation"), dict) else {}
    return str(replay.get("status", "MISSING")).upper()


def _episode_exclusion_reasons(entry: Dict[str, Any], include_review: bool) -> List[str]:
    reasons: List[str] = []
    replay_status = _episode_replay_status(entry)
    if replay_status == "PASS":
        return reasons
    if replay_status == "REVIEW" and include_review:
        return reasons
    if replay_status == "MISSING":
        reasons.append("missing_replay_validation")
    elif replay_status == "REVIEW":
        reasons.append("replay_status_review")
    elif replay_status == "REJECT":
        reasons.append("replay_status_reject")
    else:
        reasons.append(f"replay_status_{replay_status.lower()}")
    failure_reasons = entry.get("failure_reasons", []) or []
    replay = entry.get("replay_validation", {}) if isinstance(entry.get("replay_validation"), dict) else {}
    for reason in failure_reasons:
        reasons.append(str(reason))
    for reason in replay.get("review_reasons", []) or []:
        reasons.append(str(reason))
    for reason in replay.get("reject_reasons", []) or []:
        reasons.append(str(reason))
    return sorted(set(reason for reason in reasons if reason))


def _is_train_ready(split_episode_counts: Counter[str], selected_episode_count: int, require_val: bool, require_heldout: bool) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if selected_episode_count <= 0:
        reasons.append("no_selected_episodes")
    if split_episode_counts.get("train", 0) <= 0:
        reasons.append("no_train_episode")
    if require_val and split_episode_counts.get("val", 0) <= 0:
        reasons.append("no_val_episode")
    if require_heldout and split_episode_counts.get("heldout", 0) <= 0:
        reasons.append("no_heldout_episode")
    return not reasons, reasons


def _least_squares_sanity(observations: np.ndarray, actions: np.ndarray, split_codes: np.ndarray) -> Dict[str, Any]:
    train_mask = split_codes == SPLIT_CODE["train"]
    if observations.size == 0 or actions.size == 0 or not np.any(train_mask):
        return {
            "status": "SKIPPED",
            "reason": "no_train_frames",
            "not_promoted": True,
        }
    x_train = observations[train_mask].astype(np.float64)
    y_train = actions[train_mask].astype(np.float64)
    x_mean = np.mean(x_train, axis=0, keepdims=True)
    x_std = np.std(x_train, axis=0, keepdims=True)
    x_std = np.where(x_std < 1e-6, 1.0, x_std)
    x_train_n = (x_train - x_mean) / x_std
    x_aug = np.concatenate([x_train_n, np.ones((x_train_n.shape[0], 1), dtype=np.float64)], axis=1)
    ridge = 1e-4
    gram = x_aug.T @ x_aug
    reg = ridge * np.eye(gram.shape[0], dtype=np.float64)
    reg[-1, -1] = 0.0
    weights = np.linalg.solve(gram + reg, x_aug.T @ y_train)
    pred_train = x_aug @ weights
    train_rmse = float(np.sqrt(np.mean((pred_train - y_train) ** 2)))
    train_mae = float(np.mean(np.abs(pred_train - y_train)))
    eval_splits: Dict[str, Dict[str, Any]] = {}
    for split_name, code in SPLIT_CODE.items():
        mask = split_codes == code
        if not np.any(mask):
            continue
        x = observations[mask].astype(np.float64)
        y = actions[mask].astype(np.float64)
        x_n = (x - x_mean) / x_std
        x_eval = np.concatenate([x_n, np.ones((x_n.shape[0], 1), dtype=np.float64)], axis=1)
        pred = x_eval @ weights
        eval_splits[split_name] = {
            "frames": int(np.sum(mask)),
            "rmse": float(np.sqrt(np.mean((pred - y) ** 2))),
            "mae": float(np.mean(np.abs(pred - y))),
        }
    return {
        "status": "PASS_DIAGNOSTIC",
        "model_type": "ridge_linear_obs_to_backend_action_sanity",
        "ridge": ridge,
        "train_frames": int(np.sum(train_mask)),
        "obs_dim": int(observations.shape[1]),
        "action_dim": int(actions.shape[1]),
        "train_rmse": train_rmse,
        "train_mae": train_mae,
        "split_metrics": eval_splits,
        "not_promoted": True,
        "not_claimed": [
            "policy_quality",
            "closed_loop_success",
            "generalization",
            "hardware_readiness",
        ],
    }


def _build_failure_bank(entries: Sequence[Dict[str, Any]], selected_ids: set[str]) -> Dict[str, Any]:
    reason_to_examples: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    excluded_count = 0
    for entry in entries:
        episode_id = str(entry.get("episode_id", ""))
        replay = entry.get("replay_validation", {}) if isinstance(entry.get("replay_validation"), dict) else {}
        reasons = list(entry.get("failure_reasons", []) or [])
        reasons.extend(replay.get("review_reasons", []) or [])
        reasons.extend(replay.get("reject_reasons", []) or [])
        replay_status = _episode_replay_status(entry)
        if episode_id not in selected_ids:
            excluded_count += 1
            if not reasons:
                reasons.append(f"not_selected_replay_{replay_status.lower()}")
        for reason in sorted(set(str(item) for item in reasons if item)):
            reason_to_examples[reason].append(
                {
                    "episode_id": episode_id,
                    "source_uri": entry.get("source_uri", ""),
                    "source_kind": entry.get("source_kind", ""),
                    "import_status": entry.get("status", ""),
                    "split": entry.get("split", ""),
                    "replay_status": replay_status,
                    "episode_path": entry.get("episode_path", ""),
                }
            )
    reasons_payload = []
    for reason, examples in sorted(reason_to_examples.items()):
        reasons_payload.append(
            {
                "reason": reason,
                "count": len(examples),
                "examples": examples[:5],
            }
        )
    return {
        "schema_version": "teleop_failure_bank_v0",
        "created_at_utc": _utc_stamp(),
        "excluded_episode_count": int(excluded_count),
        "reason_count": len(reasons_payload),
        "reasons": reasons_payload,
        "not_claimed": [
            "failure_labels_are_task_success_labels",
            "review_samples_are_train_ready",
        ],
    }


def _write_episode_index_csv(path: Path, entries: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "episode_id",
        "selected",
        "split",
        "replay_status",
        "frames",
        "source_kind",
        "episode_path",
        "exclusion_reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "episode_id": entry.get("episode_id", ""),
                    "selected": entry.get("selected", False),
                    "split": entry.get("split", ""),
                    "replay_status": entry.get("replay_status", ""),
                    "frames": entry.get("frames", 0),
                    "source_kind": entry.get("source_kind", ""),
                    "episode_path": entry.get("episode_path", ""),
                    "exclusion_reasons": ";".join(entry.get("exclusion_reasons", []) or []),
                }
            )


def _write_summary_md(path: Path, manifest: Dict[str, Any]) -> None:
    summary = manifest["summary"]
    lines = [
        f"# Teleop Training Preflight Summary: {manifest['dataset_id']}",
        "",
        f"Created: {manifest['created_at_utc']}",
        "",
        "## Status",
        "",
        f"- preflight status: `{manifest['preflight_status']}`",
        f"- train ready: `{manifest['train_ready']}`",
        f"- selected episodes: {summary['selected_episodes']}",
        f"- selected frames: {summary['selected_frames']}",
        f"- observation dim: {summary['observation_dim']}",
        f"- action dim: {summary['action_dim']}",
        f"- split episode counts: `{json.dumps(summary['split_episode_counts'], sort_keys=True)}`",
        f"- split frame counts: `{json.dumps(summary['split_frame_counts'], sort_keys=True)}`",
        "",
        "## Train-Ready Blockers",
        "",
        f"`{json.dumps(manifest['train_ready_blockers'], sort_keys=True)}`",
        "",
        "## Sanity Model",
        "",
        f"`{json.dumps(manifest.get('sanity_model', {'status': 'SKIPPED'}), sort_keys=True)}`",
        "",
        "## Boundary",
        "",
        "This is a training preflight data package. It does not promote a model,",
        "prove closed-loop success, or imply hardware readiness.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_training_preflight(args: argparse.Namespace) -> Dict[str, Any]:
    source_manifest_path = args.manifest.expanduser().resolve()
    source_manifest = _load_manifest(source_manifest_path)
    source_dataset_id = str(source_manifest.get("dataset_id", "teleop_dataset"))
    dataset_id = _safe_id(args.dataset_id or f"{source_dataset_id}_training_preflight_v0")
    output_root = args.output_root.expanduser().resolve() / dataset_id
    output_root.mkdir(parents=True, exist_ok=True)

    selected_episode_rows: List[Dict[str, Any]] = []
    episode_index_rows: List[Dict[str, Any]] = []
    selected_episode_ids: set[str] = set()

    observations: List[np.ndarray] = []
    actions: List[np.ndarray] = []
    palm_features: List[np.ndarray] = []
    open_close_features: List[np.ndarray] = []
    semantic_features: List[np.ndarray] = []
    landmarks: List[np.ndarray] = []
    episode_index: List[int] = []
    frame_index: List[int] = []
    timestamps: List[float] = []
    split_codes: List[int] = []
    quality_codes: List[int] = []
    episode_id_per_frame: List[str] = []
    skill_id_per_frame: List[str] = []
    phase_id_per_frame: List[str] = []

    action_dim: int | None = None
    obs_dim = OBS_MODE_DIMS[args.obs_mode]
    split_episode_counts: Counter[str] = Counter()
    split_frame_counts: Counter[str] = Counter()
    replay_status_counts: Counter[str] = Counter()

    entries = source_manifest.get("episodes", []) or []
    for raw_idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        episode_id = str(entry.get("episode_id", f"episode_{raw_idx}"))
        split = str(entry.get("split", "unassigned"))
        replay_status = _episode_replay_status(entry)
        replay_status_counts[replay_status] += 1
        exclusion_reasons = _episode_exclusion_reasons(entry, include_review=bool(args.include_review))
        selected = not exclusion_reasons
        episode_path = Path(entry.get("episode_path", "")).expanduser()
        row = {
            "episode_id": episode_id,
            "selected": selected,
            "split": split,
            "replay_status": replay_status,
            "frames": 0,
            "source_kind": entry.get("source_kind", ""),
            "episode_path": str(episode_path),
            "exclusion_reasons": exclusion_reasons,
        }
        if not selected:
            episode_index_rows.append(row)
            continue
        if not episode_path.exists():
            row["selected"] = False
            row["exclusion_reasons"] = ["episode_path_missing"]
            episode_index_rows.append(row)
            continue

        payload = _read_json(episode_path)
        frames = payload.get("frames", [])
        if not isinstance(frames, list) or not frames:
            row["selected"] = False
            row["exclusion_reasons"] = ["episode_has_no_frames"]
            episode_index_rows.append(row)
            continue

        this_action_dim = int(frames[0].get("backend_action_v0", {}).get("action_dim", 0))
        if action_dim is None:
            action_dim = this_action_dim
        elif action_dim != this_action_dim:
            row["selected"] = False
            row["exclusion_reasons"] = ["action_dim_mismatch"]
            episode_index_rows.append(row)
            continue

        selected_index = len(selected_episode_rows)
        selected_episode_ids.add(episode_id)
        split_episode_counts[split] += 1
        split_frame_counts[split] += len(frames)
        row["frames"] = len(frames)
        selected_episode_rows.append(
            {
                "episode_id": episode_id,
                "episode_path": str(episode_path),
                "split": split,
                "replay_status": replay_status,
                "source_kind": entry.get("source_kind", ""),
                "frames": len(frames),
            }
        )
        episode_index_rows.append(row)

        for frame in frames:
            obs = _frame_observation(frame, args.obs_mode)
            action = np.asarray(frame.get("backend_action_v0", {}).get("values", []), dtype=np.float32)
            if obs.shape != (obs_dim,):
                raise ValueError(f"Observation dim mismatch in {episode_id}: {obs.shape} vs {obs_dim}")
            if action.shape != (action_dim,):
                raise ValueError(f"Action dim mismatch in {episode_id}: {action.shape} vs {action_dim}")
            observations.append(obs)
            actions.append(action)
            palm_features.append(np.asarray(frame["palm_feature_76"], dtype=np.float32))
            open_close_features.append(np.asarray(frame["open_close_feature_35"], dtype=np.float32))
            semantic_features.append(_semantic_vector(frame))
            landmarks.append(np.asarray(frame["landmarks_21x3"], dtype=np.float32))
            episode_index.append(selected_index)
            frame_index.append(int(frame.get("frame_index", 0)))
            timestamps.append(float(frame.get("timestamp_s", 0.0)))
            split_codes.append(SPLIT_CODE.get(split, SPLIT_CODE["unassigned"]))
            quality_status = str(frame.get("quality", {}).get("status", "unknown"))
            quality_codes.append(QUALITY_CODE.get(quality_status, QUALITY_CODE["unknown"]))
            episode_id_per_frame.append(episode_id)
            labels = frame.get("labels", {}) if isinstance(frame.get("labels"), dict) else {}
            skill_id_per_frame.append(str(labels.get("skill_id", "")))
            phase_id_per_frame.append(str(labels.get("phase_id", "")))

    obs_arr = np.asarray(observations, dtype=np.float32).reshape((-1, obs_dim)) if observations else np.zeros((0, obs_dim), dtype=np.float32)
    action_dim = int(action_dim or 0)
    action_arr = np.asarray(actions, dtype=np.float32).reshape((-1, action_dim)) if actions else np.zeros((0, action_dim), dtype=np.float32)
    palm_arr = np.asarray(palm_features, dtype=np.float32).reshape((-1, 76)) if palm_features else np.zeros((0, 76), dtype=np.float32)
    open_close_arr = np.asarray(open_close_features, dtype=np.float32).reshape((-1, 35)) if open_close_features else np.zeros((0, 35), dtype=np.float32)
    semantic_arr = (
        np.asarray(semantic_features, dtype=np.float32).reshape((-1, len(SEMANTIC_FEATURE_NAMES)))
        if semantic_features
        else np.zeros((0, len(SEMANTIC_FEATURE_NAMES)), dtype=np.float32)
    )
    landmarks_arr = np.asarray(landmarks, dtype=np.float32).reshape((-1, 21, 3)) if landmarks else np.zeros((0, 21, 3), dtype=np.float32)
    split_codes_arr = np.asarray(split_codes, dtype=np.int16)

    train_ready, train_ready_blockers = _is_train_ready(
        split_episode_counts,
        selected_episode_count=len(selected_episode_rows),
        require_val=bool(args.require_val),
        require_heldout=bool(args.require_heldout),
    )
    preflight_status = "PASS_PREFLIGHT" if len(selected_episode_rows) > 0 and action_dim > 0 else "BLOCKED"
    if not train_ready:
        preflight_status = "PASS_PREFLIGHT_NOT_TRAIN_READY" if preflight_status == "PASS_PREFLIGHT" else "BLOCKED"

    sanity_model: Dict[str, Any] = {"status": "SKIPPED"}
    if args.run_linear_sanity:
        sanity_model = _least_squares_sanity(obs_arr, action_arr, split_codes_arr)

    failure_bank = _build_failure_bank(entries, selected_episode_ids)

    dataset_npz_path = output_root / "teleop_training_preflight_dataset_v0.npz"
    metadata = {
        "schema_version": "teleop_training_preflight_arrays_v0",
        "dataset_id": dataset_id,
        "source_dataset_id": source_dataset_id,
        "obs_mode": args.obs_mode,
        "obs_dim": obs_dim,
        "action_surface": "backend_action_v0",
        "action_schema": "shadow_hand_normalized_action_v1" if action_dim == 24 else "unknown",
        "action_dim": action_dim,
        "split_code": SPLIT_CODE,
        "quality_code": QUALITY_CODE,
        "semantic_feature_names": list(SEMANTIC_FEATURE_NAMES),
        "not_claimed": [
            "train_ready_without_split_gate",
            "policy_quality",
            "closed_loop_success",
            "hardware_readiness",
        ],
    }
    np.savez_compressed(
        dataset_npz_path,
        observations=obs_arr,
        actions=action_arr,
        palm_features=palm_arr,
        open_close_features=open_close_arr,
        semantic_features=semantic_arr,
        landmarks=landmarks_arr,
        episode_index=np.asarray(episode_index, dtype=np.int32),
        frame_index=np.asarray(frame_index, dtype=np.int32),
        timestamps=np.asarray(timestamps, dtype=np.float32),
        split_codes=split_codes_arr,
        quality_codes=np.asarray(quality_codes, dtype=np.int16),
        episode_id_per_frame=np.asarray(episode_id_per_frame, dtype=object),
        skill_id_per_frame=np.asarray(skill_id_per_frame, dtype=object),
        phase_id_per_frame=np.asarray(phase_id_per_frame, dtype=object),
        selected_episode_ids=np.asarray([item["episode_id"] for item in selected_episode_rows], dtype=object),
        metadata=_json_ready(metadata),
    )

    split_frame_counts_full = Counter()
    for code in split_codes:
        for split_name, split_code in SPLIT_CODE.items():
            if code == split_code:
                split_frame_counts_full[split_name] += 1
                break

    manifest = {
        "schema_version": "teleop_training_preflight_manifest_v0",
        "dataset_id": dataset_id,
        "created_at_utc": _utc_stamp(),
        "preflight_status": preflight_status,
        "train_ready": bool(train_ready),
        "train_ready_blockers": train_ready_blockers,
        "classification": "generated_diagnostic",
        "source_manifest": str(source_manifest_path),
        "source_dataset_id": source_dataset_id,
        "output_dir": str(output_root),
        "arrays_path": str(dataset_npz_path),
        "failure_bank_path": str(output_root / "failure_bank.json"),
        "episode_index_path": str(output_root / "episode_index.csv"),
        "summary_path": str(output_root / "training_preflight_summary.md"),
        "config": {
            "obs_mode": args.obs_mode,
            "include_review": bool(args.include_review),
            "require_val": bool(args.require_val),
            "require_heldout": bool(args.require_heldout),
            "run_linear_sanity": bool(args.run_linear_sanity),
        },
        "summary": {
            "source_episodes": len(entries),
            "selected_episodes": len(selected_episode_rows),
            "selected_frames": int(obs_arr.shape[0]),
            "observation_dim": int(obs_arr.shape[1]) if obs_arr.ndim == 2 else obs_dim,
            "action_dim": int(action_arr.shape[1]) if action_arr.ndim == 2 else action_dim,
            "split_episode_counts": dict(split_episode_counts),
            "split_frame_counts": dict(split_frame_counts_full),
            "replay_status_counts": dict(replay_status_counts),
            "failure_bank_reason_count": int(failure_bank["reason_count"]),
        },
        "selected_episodes": selected_episode_rows,
        "episode_index": episode_index_rows,
        "sanity_model": sanity_model,
        "not_claimed": [
            "final_model",
            "closed_loop_policy_success",
            "hardware_readiness",
            "full_action_act_dp_success",
            "review_samples_are_train_ready",
        ],
    }

    _write_json(output_root / "training_preflight_manifest.json", manifest)
    _write_json(output_root / "failure_bank.json", failure_bank)
    _write_episode_index_csv(output_root / "episode_index.csv", episode_index_rows)
    _write_summary_md(output_root / "training_preflight_summary.md", manifest)
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build teleop training-preflight arrays from replay-valid episodes")
    parser.add_argument("--manifest", required=True, type=Path, help="Phase 3 dataset_manifest.json with replay_validation")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "teleop_training_preflight",
    )
    parser.add_argument("--dataset-id", default="")
    parser.add_argument(
        "--obs-mode",
        choices=sorted(OBS_MODE_DIMS),
        default="palm_open_close_semantic",
    )
    parser.add_argument("--include-review", action="store_true", help="Include replay REVIEW episodes in arrays")
    parser.add_argument("--require-val", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--require-heldout", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--run-linear-sanity", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    manifest = build_training_preflight(args)
    print(
        json.dumps(
            _json_ready(
                {
                    "dataset_id": manifest["dataset_id"],
                    "preflight_status": manifest["preflight_status"],
                    "train_ready": manifest["train_ready"],
                    "arrays": manifest["arrays_path"],
                    "summary": manifest["summary"],
                    "sanity_model": manifest.get("sanity_model", {"status": "SKIPPED"}),
                }
            ),
            indent=2,
            ensure_ascii=True,
        )
    )
    if manifest["preflight_status"] == "BLOCKED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
