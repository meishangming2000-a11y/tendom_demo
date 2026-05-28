from __future__ import annotations

import json

from clean_mesh_common import (
    BALL_POSITION,
    DOCS_DIR,
    METADATA_DIR,
    load_model,
    render_png,
    set_ball_position,
    write_json,
)


ROOT = DOCS_DIR.parent
ALIGNED_SCENE_XML = ROOT / "mjcf" / "scene_ball_clean_mesh_aligned.xml"
VISUAL_CHECK_ALIGNED_DIR = DOCS_DIR / "visual_checks_aligned"

VIEWS = [
    ("front", "front_view.png"),
    ("side", "side_view.png"),
    ("top", "top_view.png"),
    ("palm", "palm_view.png"),
    ("finger_root_closeup", "finger_root_closeup.png"),
    ("thumb_root_closeup", "thumb_root_closeup.png"),
    ("index_finger_closeup", "index_finger_closeup.png"),
    ("full_hand_with_ball", "full_hand_with_ball.png"),
]


def main() -> int:
    VISUAL_CHECK_ALIGNED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mujoco, model, data = load_model(ALIGNED_SCENE_XML)
        set_ball_position(model, data, mujoco, BALL_POSITION)
        mujoco.mj_forward(model, data)
    except Exception as exc:
        report = {"load_success": False, "error": f"{type(exc).__name__}: {exc}", "scene": str(ALIGNED_SCENE_XML)}
        write_json(METADATA_DIR / "clean_mesh_aligned_visual_render_summary.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    renders = []
    for camera, filename in VIEWS:
        renders.append(render_png(model, data, mujoco, camera, VISUAL_CHECK_ALIGNED_DIR / filename, width=1200, height=850))

    report = {
        "scene": str(ALIGNED_SCENE_XML),
        "load_success": True,
        "views": renders,
        "notes": [
            "Aligned clean mesh renders after MJCF-only translation correction.",
            "No CAD or STL files were modified; clean visual geoms remain visual-only.",
        ],
    }
    write_json(METADATA_DIR / "clean_mesh_aligned_visual_render_summary.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
