#!/usr/bin/env python3
"""Render visual checks for the arm + export4 hand assembly."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
SCENE = ROOT / "scene_arm_hand_export4_cad_mount_candidate.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata" / "arm_hand_export4_visual_check.json"
VIS = ROOT / "visual_checks"
REPORT = DOCS / "arm_hand_export4_visual_check_report.md"


def render(model, data, mujoco, output: Path, lookat: Tuple[float, float, float], distance: float, azimuth: float, elevation: float) -> Dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = np.asarray(lookat, dtype=np.float64)
        camera.distance = distance
        camera.azimuth = azimuth
        camera.elevation = elevation
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "mean_pixel": float(image.mean()),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
        "lookat": list(lookat),
        "distance": distance,
        "azimuth": azimuth,
        "elevation": elevation,
    }


def body_pos(model, data, mujoco, name: str) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else np.full(3, np.nan)


def site_pos(model, data, mujoco, name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    return data.site_xpos[sid].copy() if sid >= 0 else np.full(3, np.nan)


def json_ready(value):
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Render arm-hand assembly visual checks.")
    parser.add_argument("--scene", default=str(SCENE))
    args = parser.parse_args()

    import mujoco

    scene = Path(args.scene).resolve()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    ee_site = site_pos(model, data, mujoco, "ee_tool_frame_site")
    ee_body = body_pos(model, data, mujoco, "ee_tool_frame")
    hand_base = body_pos(model, data, mujoco, "hand_base_link")
    wrist = body_pos(model, data, mujoco, "wrist_middle_link")
    palm = body_pos(model, data, mujoco, "palm_link")
    center = (ee_body + palm) / 2.0
    metrics = {
        "ee_tool_frame_site": ee_site,
        "ee_tool_frame_body": ee_body,
        "hand_base_link": hand_base,
        "wrist_middle_link": wrist,
        "palm_link": palm,
        "ee_site_to_hand_base": float(np.linalg.norm(ee_site - hand_base)),
        "ee_body_to_hand_base": float(np.linalg.norm(ee_body - hand_base)),
        "hand_base_to_wrist_middle": float(np.linalg.norm(hand_base - wrist)),
        "wrist_middle_to_palm": float(np.linalg.norm(wrist - palm)),
    }
    views = {
        "overview": render(model, data, mujoco, VIS / "arm_hand_overview.png", tuple(center), 0.75, 205, -22),
        "side": render(model, data, mujoco, VIS / "arm_hand_side.png", tuple(center), 0.58, 100, -18),
        "top": render(model, data, mujoco, VIS / "arm_hand_top.png", tuple(center), 0.58, 180, -78),
        "wrist_closeup": render(model, data, mujoco, VIS / "arm_hand_wrist_closeup.png", tuple(center), 0.18, 110, -12),
        "flange_axis": render(model, data, mujoco, VIS / "arm_hand_flange_axis.png", tuple(ee_body), 0.16, 205, -4),
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
            "nmesh": int(model.nmesh),
        },
        "metrics": metrics,
        "views": views,
        "visual_conclusion": "PASS_FIRST_ASSEMBLY_CANDIDATE",
        "notes": [
            "Hand is a child body under ee_tool_frame.",
            "Identity hand transform is used in this first assembly candidate.",
            "Visual close-up shows flange/wrist attachment instead of a separate one-point connection.",
            "TODO: final CAD-flange calibration may still need a small fixed transform adjustment.",
        ],
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Arm + Export4 Hand Visual Check Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Model summary: `{payload['model_summary']}`\n\n",
        f"- Visual conclusion: `{payload['visual_conclusion']}`\n\n",
        "## Mount Metrics\n\n",
        f"- ee_tool_frame_site to hand_base_link: `{metrics['ee_site_to_hand_base']:.6f} m`\n",
        f"- ee_tool_frame body to hand_base_link: `{metrics['ee_body_to_hand_base']:.6f} m`\n",
        f"- hand_base_link to wrist_middle_link: `{metrics['hand_base_to_wrist_middle']:.6f} m`\n",
        f"- wrist_middle_link to palm_link: `{metrics['wrist_middle_to_palm']:.6f} m`\n\n",
        "## Renders\n\n",
    ]
    for name, view in views.items():
        lines.append(f"- `{name}`: `{view['file']}`\n")
    lines.extend(
        [
            "\n## Notes\n\n",
            "- This is a first attachment candidate, not final flange calibration.\n",
            "- The wrist/root is attached near the arm flange and no longer has the old one-point separate-model look.\n",
            "- If exact flange face or bolt-pattern alignment is needed, adjust only the fixed hand root transform in a new experiment file.\n",
        ]
    )
    DOCS.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    for name, view in views.items():
        print(f"{name}: {view['file']}")


if __name__ == "__main__":
    main()
