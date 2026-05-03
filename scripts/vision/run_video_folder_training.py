#!/usr/bin/env python3
"""Run the video-folder to Shadow-retarget training workflow.

This is a convenience wrapper around the existing vision scripts. It keeps raw
videos and generated training products outside the simulation source tree by
default.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


SIM_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SIM_ROOT.parent


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _run(command: List[str], cwd: Path = SIM_ROOT) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd), check=True)


def _default_model_path() -> Path:
    return (
        PROJECT_ROOT
        / "artifacts"
        / "vision_real_hand"
        / "hand_example_20260429"
        / "one_command_compare"
        / "models"
        / "hand_landmarker.task"
    )


def _safe_clear_output_root(output_root: Path) -> None:
    resolved = output_root.resolve()
    artifacts_root = (PROJECT_ROOT / "artifacts").resolve()
    try:
        resolved.relative_to(artifacts_root)
    except ValueError as exc:
        raise ValueError(f"--force can only delete inside {artifacts_root}: {resolved}") from exc
    if resolved.exists():
        shutil.rmtree(resolved)


def _video_files(video_dir: Path) -> List[Path]:
    extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".ogv"}
    files = [path for path in video_dir.rglob("*") if path.is_file() and path.suffix.lower() in extensions]
    return sorted(files, key=lambda item: item.name.lower())


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train diagnostic Shadow retarget models from a folder of hand videos")
    parser.add_argument("--video-dir", default=str(PROJECT_ROOT / "videos"), help="Folder containing hand videos")
    parser.add_argument(
        "--output-root",
        default=str(PROJECT_ROOT / "artifacts" / "vision_real_hand" / f"video_folder_{time.strftime('%Y%m%d')}"),
        help="Output artifact root",
    )
    parser.add_argument(
        "--hand-landmarker-model",
        default=str(_default_model_path()),
        help="MediaPipe hand_landmarker.task path",
    )
    parser.add_argument("--force", action="store_true", help="Delete output-root first. Only allowed under artifacts/.")
    parser.add_argument("--max-frames", type=int, default=0, help="Detected hand-frame cap per video")
    parser.add_argument("--max-source-frames", type=int, default=0, help="Source video-frame cap per video")
    parser.add_argument("--mirror", action="store_true", help="Mirror frames before MediaPipe detection")
    parser.add_argument("--mirror-x", action="store_true", help="Mirror landmark x before Shadow retarget")
    parser.add_argument("--action-time-scale", type=int, default=5, help="Retarget time scale")
    parser.add_argument("--smoothing-alpha", type=float, default=0.25, help="Retarget smoothing")
    parser.add_argument("--skip-rollout", action="store_true", help="Skip per-video Shadow rollout datasets")
    parser.add_argument("--bc-epochs", type=int, default=150, help="Single-frame BC epochs")
    parser.add_argument("--hidden-dim", type=int, default=256, help="Hidden dimension for diagnostic models")
    parser.add_argument("--batch-size", type=int, default=256, help="Training batch size")
    parser.add_argument("--skip-bc", action="store_true", help="Skip single-frame BC training")
    parser.add_argument("--skip-sequence", action="store_true", help="Skip sequence TCN+GRU training")
    parser.add_argument("--sequence-epochs", type=int, default=80, help="Sequence model epochs")
    parser.add_argument("--history", type=int, default=32, help="Sequence model history window")
    parser.add_argument("--chunk", type=int, default=8, help="Sequence model action chunk")
    parser.add_argument("--sample-stride", type=int, default=2, help="Sequence model sample stride")
    parser.add_argument("--val-fraction", type=float, default=0.25, help="Episode-level validation fraction")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    video_dir = Path(args.video_dir).resolve()
    output_root = Path(args.output_root).resolve()
    hand_model = Path(args.hand_landmarker_model).resolve()

    if not video_dir.exists():
        raise FileNotFoundError(video_dir)
    if not hand_model.exists():
        raise FileNotFoundError(hand_model)
    if args.force:
        _safe_clear_output_root(output_root)

    data_dir = output_root / "data"
    reports_dir = output_root / "reports"
    retarget_dir = output_root / "retarget"
    training_dir = output_root / "training"
    for directory in (data_dir, reports_dir, retarget_dir, training_dir):
        directory.mkdir(parents=True, exist_ok=True)

    videos = _video_files(video_dir)
    if not videos:
        raise RuntimeError(f"No supported videos found in {video_dir}")

    results: List[Dict[str, Any]] = []
    retarget_paths: List[Path] = []
    rollout_paths: List[Path] = []

    for video in videos:
        stem = video.stem
        trace_path = data_dir / f"{stem}_palm_trace.npz"
        trace_report = reports_dir / f"{stem}_palm_trace.json"
        retarget_path = retarget_dir / f"{stem}_shadow_retarget.npz"
        retarget_report = reports_dir / f"{stem}_shadow_retarget.json"
        rollout_path = retarget_dir / f"{stem}_shadow_retarget_replay.npz"

        item: Dict[str, Any] = {
            "video": video,
            "trace": trace_path,
            "retarget": retarget_path,
            "rollout": rollout_path if not args.skip_rollout else "",
            "status": "pending",
        }
        try:
            collect_cmd = [
                sys.executable,
                "scripts/vision/collect_palm_trace.py",
                "--source",
                str(video),
                "--hand-landmarker-model",
                str(hand_model),
                "--source-label",
                video.name,
                "--output",
                str(trace_path),
                "--report",
                str(trace_report),
                "--max-frames",
                str(args.max_frames),
                "--max-source-frames",
                str(args.max_source_frames),
            ]
            if args.mirror:
                collect_cmd.append("--mirror")
            _run(collect_cmd)

            retarget_cmd = [
                sys.executable,
                "scripts/vision/retarget_palm_trace_to_shadow.py",
                "--palm-trace",
                str(trace_path),
                "--output",
                str(retarget_path),
                "--report",
                str(retarget_report),
                "--action-time-scale",
                str(args.action_time_scale),
                "--smoothing-alpha",
                str(args.smoothing_alpha),
            ]
            if args.mirror_x:
                retarget_cmd.append("--mirror-x")
            if not args.skip_rollout:
                retarget_cmd.extend(["--rollout-output", str(rollout_path)])
            _run(retarget_cmd)

            retarget_paths.append(retarget_path)
            if not args.skip_rollout:
                rollout_paths.append(rollout_path)
            item["status"] = "ok"
        except subprocess.CalledProcessError as exc:
            item["status"] = "failed"
            item["returncode"] = exc.returncode
        results.append(item)

    if not retarget_paths:
        raise RuntimeError("No videos produced usable retarget traces")

    dataset_path = training_dir / "video_folder_shadow_retarget_bc_dataset.npz"
    dataset_report = training_dir / "video_folder_shadow_retarget_bc_dataset.json"
    build_cmd = [
        sys.executable,
        "scripts/vision/build_shadow_retarget_bc_dataset.py",
        "--output",
        str(dataset_path),
        "--report",
        str(dataset_report),
        "--tag",
        f"video_folder_{time.strftime('%Y%m%d')}_shadow_retarget",
    ]
    for idx, retarget_path in enumerate(retarget_paths):
        build_cmd.extend(["--retarget", str(retarget_path)])
        if not args.skip_rollout and idx < len(rollout_paths):
            build_cmd.extend(["--rollout", str(rollout_paths[idx])])
    _run(build_cmd)

    bc_model = ""
    if not args.skip_bc:
        bc_model_path = training_dir / f"bc_video_folder_shadow_retarget_phase_h{args.hidden_dim}.pth"
        _run(
            [
                sys.executable,
                "scripts/train_bc.py",
                "--data",
                str(dataset_path),
                "--output",
                str(bc_model_path),
                "--epochs",
                str(args.bc_epochs),
                "--batch-size",
                str(args.batch_size),
                "--hidden-dim",
                str(args.hidden_dim),
                "--add-phase-feature",
            ]
        )
        bc_model = str(bc_model_path)

    sequence_model = ""
    sequence_report = ""
    if not args.skip_sequence:
        sequence_tag = f"h{args.history}_c{args.chunk}_vphase_h{args.hidden_dim}"
        sequence_model_path = training_dir / f"seq_video_folder_shadow_retarget_{sequence_tag}.pth"
        sequence_report_path = training_dir / f"seq_video_folder_shadow_retarget_{sequence_tag}_report.json"
        _run(
            [
                sys.executable,
                "scripts/vision/train_sequence_shadow_bc.py",
                "--data",
                str(dataset_path),
                "--output",
                str(sequence_model_path),
                "--report",
                str(sequence_report_path),
                "--history",
                str(args.history),
                "--chunk",
                str(args.chunk),
                "--sample-stride",
                str(args.sample_stride),
                "--add-velocity",
                "--add-phase-feature",
                "--val-fraction",
                str(args.val_fraction),
                "--epochs",
                str(args.sequence_epochs),
                "--batch-size",
                str(args.batch_size),
                "--hidden-dim",
                str(args.hidden_dim),
            ]
        )
        sequence_model = str(sequence_model_path)
        sequence_report = str(sequence_report_path)

    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "video_dir": video_dir,
        "output_root": output_root,
        "hand_landmarker_model": hand_model,
        "config": vars(args),
        "results": results,
        "dataset": dataset_path,
        "dataset_report": dataset_report,
        "bc_model": bc_model,
        "sequence_model": sequence_model,
        "sequence_report": sequence_report,
    }
    manifest_path = output_root / "training_manifest.json"
    manifest_path.write_text(json.dumps(_json_ready(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved training manifest: {manifest_path}")


if __name__ == "__main__":
    main()
