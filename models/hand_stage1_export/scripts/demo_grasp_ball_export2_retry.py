from __future__ import annotations

import argparse
from pathlib import Path
import sys

import demo_grasp_ball_clean_mesh as clean_demo
from run_export2_ballpos_retry import RETRY_SCENE, write_retry_scene


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BALL_POSITION = [0.0, -0.1, 0.195]


def parse_ball_args(argv: list[str]) -> list[float]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ball-x", type=float, default=DEFAULT_BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=DEFAULT_BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=DEFAULT_BALL_POSITION[2])
    args, _ = parser.parse_known_args(argv)
    return [args.ball_x, args.ball_y, args.ball_z]


def main() -> int:
    ball_position = parse_ball_args(sys.argv[1:])
    write_retry_scene(ball_position)

    clean_demo.CLEAN_SCENE_XML = RETRY_SCENE
    clean_demo.BALL_POSITION = ball_position
    clean_demo.REPORT_MD = ROOT / "docs" / "export2_retry_clean_mesh_grasp_visual_report.md"
    clean_demo.REPORT_JSON = ROOT / "metadata" / "export2_retry_clean_mesh_grasp_demo.json"
    clean_demo.OUT_DIR = ROOT / "docs" / "visual_checks_export2_retry" / "live_demo"
    return clean_demo.main()


if __name__ == "__main__":
    raise SystemExit(main())
