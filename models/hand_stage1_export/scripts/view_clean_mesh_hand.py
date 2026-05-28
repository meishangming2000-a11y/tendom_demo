from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from clean_mesh_common import CLEAN_DRAFT_XML, CLEAN_SCENE_XML, load_model, mesh_files_from_draft, model_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="View the hand_stage1 clean mesh draft in MuJoCo.")
    parser.add_argument(
        "--xml",
        type=Path,
        default=CLEAN_SCENE_XML,
        help="MJCF file to load. Defaults to scene_ball_clean_mesh_draft.xml.",
    )
    parser.add_argument("--no-viewer", action="store_true", help="Only load and print summary.")
    args = parser.parse_args()

    try:
        mujoco, model, data = load_model(args.xml)
        mujoco.mj_forward(model, data)
    except Exception as exc:
        print(f"Clean mesh model load failed: {type(exc).__name__}: {exc}")
        print("Possible causes: missing meshes_clean files, unsupported STL filename, invalid MJCF include, or scale/path mismatch.")
        return 1

    summary = {
        "xml": str(args.xml),
        "model_summary": model_summary(model),
        "mesh_files_from_draft": mesh_files_from_draft(),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.no_viewer:
        return 0

    try:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(model, data)
        print("Clean mesh viewer launched. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(0.01)
        viewer.close()
    except Exception as exc:
        print(f"Clean mesh viewer launch failed: {type(exc).__name__}: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
