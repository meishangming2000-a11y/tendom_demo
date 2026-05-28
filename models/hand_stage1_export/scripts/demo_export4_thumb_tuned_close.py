#!/usr/bin/env python3
"""Run the export4 long-finger + thumb-tuned close demo.

This is still a scripted/diagnostic pose demo. It uses position actuators and
does not change CAD, STL, joint names, axes, or the joint tree.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_thumb_tuned.xml"
DEFAULT_REPORT = ROOT / "docs" / "export4_thumb_tuned_close_demo_report.md"
DEFAULT_METADATA = ROOT / "metadata" / "export4_thumb_tuned_close_demo.json"
DEFAULT_VISUAL_DIR = ROOT / "docs" / "visual_checks_export4_thumb_tuned_close"

PRESHAPE_TARGETS = {
    "index_mcp_flex_joint": -0.035,
    "middle_mcp_flex_joint": -0.035,
    "ring_mcp_flex_joint": -0.02,
    "little_mcp_flex_joint": -0.015,
    "index_mcp_abd_joint": -0.34,
    "middle_mcp_abd_joint": -0.38,
    "ring_mcp_abd_joint": -0.20,
    "little_mcp_abd_joint": -0.15,
    "index_pip_joint": -0.48,
    "middle_pip_joint": -0.52,
    "ring_pip_joint": -0.20,
    "little_pip_joint": -0.16,
    "index_dip_joint": -0.22,
    "middle_dip_joint": -0.24,
    "ring_dip_joint": -0.10,
    "little_dip_joint": -0.08,
}

LONG_FINGER_TARGETS = {
    "index_mcp_flex_joint": -0.06,
    "middle_mcp_flex_joint": -0.06,
    "ring_mcp_flex_joint": -0.05,
    "little_mcp_flex_joint": -0.04,
    "index_mcp_abd_joint": -0.58,
    "middle_mcp_abd_joint": -0.64,
    "ring_mcp_abd_joint": -0.62,
    "little_mcp_abd_joint": -0.54,
    "index_pip_joint": -0.82,
    "middle_pip_joint": -0.88,
    "ring_pip_joint": -0.84,
    "little_pip_joint": -0.76,
    "index_dip_joint": -0.42,
    "middle_dip_joint": -0.46,
    "ring_dip_joint": -0.44,
    "little_dip_joint": -0.40,
}

THUMB_VISUAL_TARGET = {
    "thumb_cmc_abd_joint": -0.3,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run export4 thumb-tuned scripted close")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--phase-steps", type=int, default=160)
    parser.add_argument("--hold-steps", type=int, default=220)
    parser.add_argument("--viewer", action="store_true")
    return parser


def _apply_debug_colors(model) -> None:
    import mujoco

    for geom_id in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""
        if name.startswith("thumb_") or "_thumb_" in name:
            model.geom_rgba[geom_id] = np.asarray([1.0, 0.48, 0.08, 1.0])

    colors = {
        "thumb_tip_site": [1.0, 0.05, 0.02, 1.0],
        "index_tip_site": [0.10, 1.0, 0.15, 1.0],
        "middle_tip_site": [0.0, 0.85, 1.0, 1.0],
        "ring_tip_site": [0.10, 0.35, 1.0, 0.9],
        "little_tip_site": [0.10, 0.35, 1.0, 0.9],
    }
    for site_name, rgba in colors.items():
        site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        if site_id >= 0:
            model.site_rgba[site_id] = np.asarray(rgba)


def _actuator_names(model) -> List[str]:
    import mujoco

    return [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) or f"actuator_{idx}"
        for idx in range(model.nu)
    ]


def _target_vector(model, actuator_names: List[str], joint_targets: Dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for idx, actuator_name in enumerate(actuator_names):
        joint_name = actuator_name[:-4] if actuator_name.endswith("_pos") else actuator_name
        value = float(joint_targets.get(joint_name, 0.0))
        low, high = model.actuator_ctrlrange[idx]
        ctrl[idx] = float(np.clip(value, low, high))
    return ctrl


def _site(model, data, site_name: str) -> np.ndarray:
    import mujoco

    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if site_id < 0:
        return np.zeros(3, dtype=np.float64)
    return data.site_xpos[site_id].copy()


def _metrics(model, data) -> Dict[str, Any]:
    thumb = _site(model, data, "thumb_tip_site")
    index = _site(model, data, "index_tip_site")
    middle = _site(model, data, "middle_tip_site")
    ring = _site(model, data, "ring_tip_site")
    little = _site(model, data, "little_tip_site")
    long_tips = [index, middle, ring, little]
    centroid = np.mean(np.vstack(long_tips), axis=0)
    contact_distances = [float(data.contact[i].dist) for i in range(data.ncon)]
    return {
        "thumb_index_distance": float(np.linalg.norm(thumb - index)),
        "thumb_middle_distance": float(np.linalg.norm(thumb - middle)),
        "thumb_long_tip_centroid_distance": float(np.linalg.norm(thumb - centroid)),
        "long_tip_spread_mean": float(np.mean([np.linalg.norm(tip - centroid) for tip in long_tips])),
        "contact_count": int(data.ncon),
        "max_penetration": float(max([0.0] + [-dist for dist in contact_distances if dist < 0.0])),
        "tip_positions": {
            "thumb": thumb,
            "index": index,
            "middle": middle,
            "ring": ring,
            "little": little,
        },
    }


def _render(model, data, *, lookat=(0.0, 0.055, 0.20), distance=0.30, azimuth=145, elevation=-28):
    import mujoco

    renderer = mujoco.Renderer(model, width=1100, height=760)
    try:
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = np.asarray(lookat, dtype=np.float64)
        camera.distance = float(distance)
        camera.azimuth = float(azimuth)
        camera.elevation = float(elevation)
        renderer.update_scene(data, camera=camera)
        return renderer.render().copy()
    finally:
        renderer.close()


def _save_stage_images(model, data, visual_dir: Path, stem: str) -> Dict[str, str]:
    from PIL import Image

    visual_dir.mkdir(parents=True, exist_ok=True)
    views: List[Tuple[str, Dict[str, Any]]] = [
        ("front", {"lookat": (0.0, 0.045, 0.19), "distance": 0.32, "azimuth": 145, "elevation": -28}),
        ("top", {"lookat": (0.0, 0.055, 0.20), "distance": 0.28, "azimuth": 180, "elevation": -78}),
        ("thumbside", {"lookat": (-0.015, 0.04, 0.19), "distance": 0.24, "azimuth": 75, "elevation": -16}),
    ]
    paths: Dict[str, str] = {}
    for view_name, kwargs in views:
        path = visual_dir / f"{stem}_{view_name}.png"
        Image.fromarray(_render(model, data, **kwargs)).save(path)
        paths[view_name] = str(path)
    return paths


def _step_to_target(model, data, target_ctrl: np.ndarray, steps: int, viewer=None) -> None:
    import mujoco

    start = data.ctrl.copy()
    for step in range(max(1, int(steps))):
        alpha = step / max(1, int(steps) - 1)
        data.ctrl[:] = (1.0 - alpha) * start + alpha * target_ctrl
        mujoco.mj_step(model, data)
        if viewer is not None:
            viewer.sync()
            time.sleep(0.006)


def write_report(report: Path, payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# Export4 Thumb-Tuned Close Demo\n\n")
    lines.append(f"Generated: {payload['generated_at']}\n\n")
    lines.append("## Scope\n\n")
    lines.append(
        "Position-actuator scripted close using the long-finger-tuned export4 model plus the visual thumb target. "
        "No CAD, STL, joint tree, joint names, or tendon routing were changed.\n\n"
    )
    lines.append("## Target Summary\n\n")
    lines.append("| joint | target |\n|---|---:|\n")
    for joint, value in THUMB_VISUAL_TARGET.items():
        lines.append(f"| `{joint}` | `{value:.4f}` |\n")
    lines.append("\n## Stage Metrics\n\n")
    lines.append("| stage | contact | max penetration | thumb-index | thumb-middle | thumb-long-centroid |\n")
    lines.append("|---|---:|---:|---:|---:|---:|\n")
    for stage in payload["stages"]:
        metrics = stage["metrics"]
        lines.append(
            f"| {stage['name']} | {metrics['contact_count']} | {metrics['max_penetration']:.5f} | "
            f"{metrics['thumb_index_distance']:.4f} | {metrics['thumb_middle_distance']:.4f} | "
            f"{metrics['thumb_long_tip_centroid_distance']:.4f} |\n"
        )
    lines.append("\n## Visual Notes\n\n")
    lines.append("- Screenshots are color-coded for debugging: thumb link orange, thumb tip red, index tip green, middle tip cyan.\n")
    lines.append("- Visual target is preferred over the pure score-best target because it adds mild thumb MCP/IP flexion.\n")
    lines.append("- This is acceptable as a scripted smoke-test target, but not yet a training-ready contact policy.\n")
    lines.append("\n## Screenshots\n\n")
    for stage in payload["stages"]:
        lines.append(f"- `{stage['name']}`: {stage['images']}\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    _apply_debug_colors(model)
    actuator_names = _actuator_names(model)

    stage_targets = [
        ("open_hand", {}),
        ("preshape", PRESHAPE_TARGETS),
        ("four_fingers_closed", LONG_FINGER_TARGETS),
        ("thumb_visual_close", {**LONG_FINGER_TARGETS, **THUMB_VISUAL_TARGET}),
        ("hold", {**LONG_FINGER_TARGETS, **THUMB_VISUAL_TARGET}),
    ]

    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(model, data)

    stages: List[Dict[str, Any]] = []
    try:
        for idx, (stage_name, joint_targets) in enumerate(stage_targets):
            steps = args.hold_steps if stage_name == "hold" else args.phase_steps
            target_ctrl = _target_vector(model, actuator_names, joint_targets)
            _step_to_target(model, data, target_ctrl, steps, viewer=viewer)
            mujoco.mj_forward(model, data)
            stages.append(
                {
                    "name": stage_name,
                    "joint_targets": joint_targets,
                    "ctrl": target_ctrl,
                    "metrics": _metrics(model, data),
                    "images": _save_stage_images(model, data, visual_dir, f"{idx + 1:02d}_{stage_name}"),
                }
            )
    finally:
        if viewer is not None:
            viewer.close()

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_thumb_tuned_close_demo_v1",
        "scene": scene,
        "thumb_visual_target": THUMB_VISUAL_TARGET,
        "long_finger_targets": LONG_FINGER_TARGETS,
        "preshape_targets": PRESHAPE_TARGETS,
        "stages": stages,
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(report, payload)
    print(f"Loaded: {scene}")
    print(f"Saved report: {report}")
    print(f"Saved metadata: {metadata}")
    print(f"Saved screenshots: {visual_dir}")
    final = stages[-1]["metrics"]
    print(
        "hold metrics: "
        f"thumb-index={final['thumb_index_distance']:.4f}, "
        f"thumb-middle={final['thumb_middle_distance']:.4f}, "
        f"contacts={final['contact_count']}, "
        f"max_penetration={final['max_penetration']:.5f}"
    )


if __name__ == "__main__":
    main()
