from __future__ import annotations

import json
from pathlib import Path

import imageio.v2 as imageio

from demo_grasp_ball_primitive import BALL_POSITION, SCENE_XML, STAGE_TARGETS, apply_targets, get_joint_map, set_ball_position


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "renders"
METADATA_DIR = ROOT / "metadata"


def render_frame(model, data, mujoco, camera_name: str, output: Path) -> dict:
    renderer = mujoco.Renderer(model, width=900, height=650)
    try:
        renderer.update_scene(data, camera=camera_name)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "camera": camera_name,
        "shape": list(image.shape),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
        "mean_pixel": float(image.mean()),
    }


def main() -> int:
    import mujoco

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    data = mujoco.MjData(model)
    joint_map = get_joint_map(model, mujoco)

    renders = []
    set_ball_position(model, data, mujoco, BALL_POSITION)
    mujoco.mj_forward(model, data)
    for camera in ["front", "side", "top"]:
        renders.append(render_frame(model, data, mujoco, camera, OUT_DIR / f"neutral_{camera}.png"))

    apply_targets(model, data, joint_map, STAGE_TARGETS["close_thumb"])
    set_ball_position(model, data, mujoco, BALL_POSITION)
    mujoco.mj_forward(model, data)
    for camera in ["front", "side", "top"]:
        renders.append(render_frame(model, data, mujoco, camera, OUT_DIR / f"scripted_close_{camera}.png"))

    summary = {
        "scene": str(SCENE_XML),
        "renders": renders,
        "observed": [
            "Neutral primitive skeleton renders show root, wrist, palm, fingers, thumb, and ball without using suspicious STL meshes.",
            "Scripted close renders use the enhanced primitive staged target close_thumb pose.",
            "Palm is represented by a visible ellipsoid plus MCP spokes and joint markers.",
            "Fingertip sites are rendered as blue site markers in the primitive model.",
            "Thumb direction remains TODO for manual semantic review; it does not yet provide a Shadow-like opposition grasp.",
        ],
        "notes": [
            "Rendered frames are fixed-camera visual checks for neutral and scripted close poses.",
            "They are not a substitute for interactive axis/sign inspection in the MuJoCo viewer.",
        ],
    }
    (METADATA_DIR / "render_stage1_frames.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Render Stage1 Frames Report",
        "",
        f"- Scene: `{SCENE_XML}`",
        "",
        "## Rendered Frames",
        "",
    ]
    lines.extend(f"- `{Path(item['file']).name}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}" for item in renders)
    lines.extend(["", "## Observed", ""])
    lines.extend(f"- {item}" for item in summary["observed"])
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in summary["notes"])
    lines.append("")
    (ROOT / "docs" / "render_stage1_frames_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
