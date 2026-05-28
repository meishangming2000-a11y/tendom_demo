#!/usr/bin/env python3
"""Open the current hand_stage1 export4 model in the MuJoCo viewer."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="View hand_stage1 export4 in MuJoCo")
    parser.add_argument(
        "--scene",
        default="",
        help="Explicit MJCF path. Overrides --ball/--model-only.",
    )
    parser.add_argument(
        "--ball",
        action="store_true",
        help="Open scene_ball_export4.xml instead of the no-ball comparison scene.",
    )
    parser.add_argument(
        "--sign-fixed",
        action="store_true",
        help="Open the experimental flexion-sign-fixed export4 scene.",
    )
    parser.add_argument(
        "--long-finger-tuned",
        action="store_true",
        help="Open the experimental long-finger-tuned export4 scene.",
    )
    parser.add_argument(
        "--thumb-tuned",
        action="store_true",
        help="Open the experimental thumb-tuned export4 scene.",
    )
    parser.add_argument(
        "--current-baseline",
        action="store_true",
        help="Open the promoted export4 current baseline scene.",
    )
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="Open hand_stage1_export4.xml directly without ground/camera scene.",
    )
    return parser


def choose_scene(args: argparse.Namespace) -> Path:
    if args.scene:
        return Path(args.scene).resolve()
    if args.current_baseline:
        if args.model_only:
            return ROOT / "mjcf" / "hand_stage1_export4_current_baseline.xml"
        if args.ball:
            return ROOT / "mjcf" / "scene_ball_export4_current_baseline.xml"
        return ROOT / "mjcf" / "scene_export4_current_baseline.xml"
    if args.thumb_tuned:
        if args.model_only:
            return ROOT / "mjcf" / "hand_stage1_export4_thumb_tuned.xml"
        if args.ball:
            return ROOT / "mjcf" / "scene_ball_export4_thumb_tuned.xml"
        return ROOT / "mjcf" / "scene_export4_thumb_tuned.xml"
    if args.long_finger_tuned:
        if args.model_only:
            return ROOT / "mjcf" / "hand_stage1_export4_long_finger_tuned.xml"
        if args.ball:
            return ROOT / "mjcf" / "scene_ball_export4_long_finger_tuned.xml"
        return ROOT / "mjcf" / "scene_export4_long_finger_tuned.xml"
    if args.model_only:
        if args.sign_fixed:
            return ROOT / "mjcf" / "hand_stage1_export4_flexion_sign_fixed.xml"
        return ROOT / "mjcf" / "hand_stage1_export4.xml"
    if args.ball:
        if args.sign_fixed:
            return ROOT / "mjcf" / "scene_ball_export4_flexion_sign_fixed.xml"
        return ROOT / "mjcf" / "scene_ball_export4.xml"
    if args.sign_fixed:
        return ROOT / "mjcf" / "scene_export4_flexion_sign_fixed.xml"
    return ROOT / "mjcf" / "scene_export4_no_ball_compare.xml"


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = choose_scene(args)
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco
    import mujoco.viewer

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)

    print(f"Loaded: {scene}")
    print(
        f"bodies={model.nbody}, joints={model.njnt}, "
        f"actuators={model.nu}, geoms={model.ngeom}, sites={model.nsite}"
    )
    print("Close the MuJoCo viewer window to return to PowerShell.")
    mujoco.viewer.launch(model, data)


if __name__ == "__main__":
    main()
