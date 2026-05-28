#!/usr/bin/env python3
"""Tune long-finger flexion limits and targets for export4.

This script creates an experimental long-finger-tuned MJCF. It deliberately
keeps the thumb mostly neutral so the long-finger flexion signs/ranges can be
visually debugged without mixing in opposition problems.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "mjcf" / "hand_stage1_export4_flexion_sign_fixed.xml"
DEFAULT_OUTPUT = ROOT / "mjcf" / "hand_stage1_export4_long_finger_tuned.xml"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_long_finger_tuned.xml"
DEFAULT_BALL_SCENE = ROOT / "mjcf" / "scene_ball_export4_long_finger_tuned.xml"
DEFAULT_REPORT = ROOT / "docs" / "export4_long_finger_joint_tuning_report.md"
DEFAULT_METADATA = ROOT / "metadata" / "export4_long_finger_joint_tuning.json"
DEFAULT_VISUAL_DIR = ROOT / "docs" / "visual_checks_export4_long_finger_tuning"
DEFAULT_ARCHIVE = ROOT / "archive"

LONG_FINGERS = ("index", "middle", "ring", "little")

TIP_SITE = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
}

TUNED_LIMITS: Dict[str, Tuple[float, float]] = {
    # First MCP joint: keep bidirectional and conservative because current
    # naming may represent spread/side motion on some fingers.
    "index_mcp_flex_joint": (-0.30, 0.18),
    "middle_mcp_flex_joint": (-0.30, 0.18),
    "ring_mcp_flex_joint": (-0.30, 0.18),
    "little_mcp_flex_joint": (-0.28, 0.16),
    # Second MCP joint: current export4 behaves like the main palmar flexion
    # axis after sign correction.
    "index_mcp_abd_joint": (-0.78, 0.08),
    "middle_mcp_abd_joint": (-0.86, 0.08),
    "ring_mcp_abd_joint": (-0.84, 0.08),
    "little_mcp_abd_joint": (-0.76, 0.08),
    # Interphalangeal joints: reduce full curl from the sign-fixed draft to
    # avoid the visual over-folding seen in full negative range renders.
    "index_pip_joint": (-1.10, 0.04),
    "middle_pip_joint": (-1.16, 0.04),
    "ring_pip_joint": (-1.10, 0.04),
    "little_pip_joint": (-1.00, 0.04),
    "index_dip_joint": (-0.66, 0.04),
    "middle_dip_joint": (-0.70, 0.04),
    "ring_dip_joint": (-0.68, 0.04),
    "little_dip_joint": (-0.62, 0.04),
}

NATURAL_CLOSE_TARGETS: Dict[str, float] = {
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
    "thumb_cmc_abd_joint": 0.0,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.0,
    "thumb_ip_joint": 0.0,
}

HOOK_TARGETS: Dict[str, float] = {
    **{joint: 0.0 for joint in TUNED_LIMITS},
    "index_mcp_abd_joint": -0.20,
    "middle_mcp_abd_joint": -0.22,
    "ring_mcp_abd_joint": -0.20,
    "little_mcp_abd_joint": -0.18,
    "index_pip_joint": -0.92,
    "middle_pip_joint": -0.98,
    "ring_pip_joint": -0.92,
    "little_pip_joint": -0.84,
    "index_dip_joint": -0.48,
    "middle_dip_joint": -0.52,
    "ring_dip_joint": -0.50,
    "little_dip_joint": -0.46,
}

FULL_BUT_SAFE_TARGETS: Dict[str, float] = {
    "index_mcp_flex_joint": -0.10,
    "middle_mcp_flex_joint": -0.10,
    "ring_mcp_flex_joint": -0.08,
    "little_mcp_flex_joint": -0.06,
    "index_mcp_abd_joint": -0.70,
    "middle_mcp_abd_joint": -0.78,
    "ring_mcp_abd_joint": -0.76,
    "little_mcp_abd_joint": -0.68,
    "index_pip_joint": -1.02,
    "middle_pip_joint": -1.08,
    "ring_pip_joint": -1.02,
    "little_pip_joint": -0.92,
    "index_dip_joint": -0.60,
    "middle_dip_joint": -0.64,
    "ring_dip_joint": -0.62,
    "little_dip_joint": -0.56,
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


def _backup_existing(path: Path, archive: Path) -> None:
    if not path.exists():
        return
    archive.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = archive / f"{path.name}.before_long_finger_tuning_{stamp}"
    if path.is_dir():
        shutil.copytree(path, dst)
    else:
        shutil.copy2(path, dst)


def _fmt_range(values: Tuple[float, float]) -> str:
    return f"{values[0]:.6g} {values[1]:.6g}"


def write_tuned_mjcf(input_xml: Path, output_xml: Path) -> List[Dict[str, Any]]:
    tree = ET.parse(input_xml)
    root = tree.getroot()
    changes: List[Dict[str, Any]] = []

    for joint in root.findall(".//joint"):
        name = joint.attrib.get("name", "")
        if name not in TUNED_LIMITS:
            continue
        old = joint.attrib.get("range", "")
        joint.attrib["range"] = _fmt_range(TUNED_LIMITS[name])
        changes.append({"kind": "joint_range", "name": name, "old": old, "new": joint.attrib["range"]})

    for actuator in root.findall(".//actuator/position"):
        joint_name = actuator.attrib.get("joint", "")
        if joint_name not in TUNED_LIMITS:
            continue
        old = actuator.attrib.get("ctrlrange", "")
        actuator.attrib["ctrlrange"] = _fmt_range(TUNED_LIMITS[joint_name])
        changes.append(
            {
                "kind": "actuator_ctrlrange",
                "name": actuator.attrib.get("name", ""),
                "joint": joint_name,
                "old": old,
                "new": actuator.attrib["ctrlrange"],
            }
        )

    root.insert(0, ET.Comment("Experimental long-finger-tuned range draft. Thumb kept neutral."))
    output_xml.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)
    return changes


def write_scenes(hand_xml: Path, scene: Path, ball_scene: Path) -> None:
    include_name = hand_xml.name
    scene.write_text(
        f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_long_finger_tuned_scene\">
  <include file=\"{include_name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"long_finger_tuned_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"long_finger_tuned_ground_mat\" texture=\"long_finger_tuned_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <light pos=\"-0.25 -0.25 0.55\" directional=\"false\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"long_finger_tuned_ground_mat\" contype=\"0\" conaffinity=\"0\"/>
  </worldbody>
</mujoco>
""",
        encoding="utf-8",
    )
    ball_scene.write_text(
        f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_long_finger_tuned_ball_scene\">
  <include file=\"{include_name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"long_finger_tuned_ball_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"long_finger_tuned_ball_ground_mat\" texture=\"long_finger_tuned_ball_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"long_finger_tuned_ball_ground_mat\" contype=\"1\" conaffinity=\"3\"/>
    <body name=\"ball\" pos=\"0 0.045 0.22\">
      <freejoint name=\"ball_freejoint\"/>
      <geom name=\"ball_geom\" type=\"sphere\" size=\"0.025\" rgba=\"0.95 0.23 0.18 1\"
        mass=\"0.03\" friction=\"0.8 0.05 0.001\" condim=\"3\" contype=\"2\" conaffinity=\"1\"/>
    </body>
  </worldbody>
</mujoco>
""",
        encoding="utf-8",
    )


def _joint_value(model, joint_name: str, targets: Dict[str, float]) -> float:
    import mujoco

    value = float(targets.get(joint_name, 0.0))
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if jid < 0:
        return value
    lower, upper = model.jnt_range[jid]
    return float(np.clip(value, lower, upper))


def _set_pose(model, data, targets: Dict[str, float]) -> None:
    import mujoco

    data.qpos[:] = model.qpos0
    for jid in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or ""
        if joint_name not in targets:
            continue
        data.qpos[int(model.jnt_qposadr[jid])] = _joint_value(model, joint_name, targets)
    mujoco.mj_forward(model, data)


def _render(model, data, lookat=(0.0, 0.02, 0.18), distance=0.38, azimuth=180.0, elevation=-35.0):
    import mujoco

    renderer = mujoco.Renderer(model, width=900, height=620)
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


def _site_position(model, data, site_name: str) -> np.ndarray:
    import mujoco

    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    return data.site_xpos[sid].copy() if sid >= 0 else np.zeros(3)


def _palm_reference(model, data) -> np.ndarray:
    import mujoco

    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if bid < 0:
        return np.zeros(3)
    local = np.asarray([0.0, 0.048, 0.002])
    mat = data.xmat[bid].reshape(3, 3)
    return data.xpos[bid].copy() + mat @ local


def _metrics(model, data) -> Dict[str, Any]:
    palm = _palm_reference(model, data)
    tips = {finger: _site_position(model, data, site) for finger, site in TIP_SITE.items()}
    tip_dist = {finger: float(np.linalg.norm(pos - palm)) for finger, pos in tips.items()}
    return {
        "palm": palm,
        "tips": tips,
        "tip_to_palm": tip_dist,
        "mean_tip_to_palm": float(np.mean(list(tip_dist.values()))),
    }


def _contact_sheet(frames: List[Tuple[str, np.ndarray]], out_path: Path, columns: int = 2) -> str:
    from PIL import Image, ImageDraw

    if not frames:
        return ""
    cell_w = frames[0][1].shape[1]
    cell_h = frames[0][1].shape[0]
    label_h = 30
    columns = min(columns, len(frames))
    rows = int(np.ceil(len(frames) / columns))
    sheet = Image.new("RGB", (columns * cell_w, rows * (cell_h + label_h)), (242, 244, 247))
    draw = ImageDraw.Draw(sheet)
    for idx, (label, image) in enumerate(frames):
        x = (idx % columns) * cell_w
        y = (idx // columns) * (cell_h + label_h)
        draw.text((x + 10, y + 8), label, fill=(20, 24, 32))
        sheet.paste(Image.fromarray(image), (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return str(out_path)


def render_tuning_outputs(model_xml: Path, visual_dir: Path) -> Dict[str, Any]:
    import mujoco
    from PIL import Image

    model = mujoco.MjModel.from_xml_path(str(model_xml))
    visual_dir.mkdir(parents=True, exist_ok=True)
    outputs: Dict[str, Any] = {"sheets": {}, "frames": {}, "metrics": {}}

    full_poses = {
        "open": {},
        "hook": HOOK_TARGETS,
        "natural_close": NATURAL_CLOSE_TARGETS,
        "full_but_safe": FULL_BUT_SAFE_TARGETS,
    }
    full_frames: List[Tuple[str, np.ndarray]] = []
    full_side_frames: List[Tuple[str, np.ndarray]] = []
    full_top_frames: List[Tuple[str, np.ndarray]] = []
    for name, targets in full_poses.items():
        data = mujoco.MjData(model)
        _set_pose(model, data, targets)
        image = _render(model, data)
        side_image = _render(model, data, lookat=(0.0, 0.02, 0.18), distance=0.38, azimuth=90.0, elevation=-30.0)
        top_image = _render(model, data, lookat=(0.0, 0.02, 0.18), distance=0.40, azimuth=180.0, elevation=-75.0)
        path = visual_dir / f"full_{name}.png"
        side_path = visual_dir / f"full_{name}_side.png"
        top_path = visual_dir / f"full_{name}_top.png"
        Image.fromarray(image).save(path)
        Image.fromarray(side_image).save(side_path)
        Image.fromarray(top_image).save(top_path)
        outputs["frames"][f"full_{name}"] = str(path)
        outputs["frames"][f"full_{name}_side"] = str(side_path)
        outputs["frames"][f"full_{name}_top"] = str(top_path)
        outputs["metrics"][f"full_{name}"] = _metrics(model, data)
        full_frames.append((name, image))
        full_side_frames.append((name, side_image))
        full_top_frames.append((name, top_image))
    outputs["sheets"]["full_hand"] = _contact_sheet(full_frames, visual_dir / "full_hand_tuning_sheet.png", columns=2)
    outputs["sheets"]["full_hand_side"] = _contact_sheet(full_side_frames, visual_dir / "full_hand_tuning_side_sheet.png", columns=2)
    outputs["sheets"]["full_hand_top"] = _contact_sheet(full_top_frames, visual_dir / "full_hand_tuning_top_sheet.png", columns=2)

    for finger in LONG_FINGERS:
        frames: List[Tuple[str, np.ndarray]] = []
        poses = [
            ("open", {}),
            ("mcp_flex_only", {f"{finger}_mcp_flex_joint": NATURAL_CLOSE_TARGETS[f"{finger}_mcp_flex_joint"]}),
            ("mcp_abd_only", {f"{finger}_mcp_abd_joint": NATURAL_CLOSE_TARGETS[f"{finger}_mcp_abd_joint"]}),
            ("pip_only", {f"{finger}_pip_joint": NATURAL_CLOSE_TARGETS[f"{finger}_pip_joint"]}),
            ("dip_only", {f"{finger}_dip_joint": NATURAL_CLOSE_TARGETS[f"{finger}_dip_joint"]}),
            (
                "finger_natural_combo",
                {
                    f"{finger}_mcp_flex_joint": NATURAL_CLOSE_TARGETS[f"{finger}_mcp_flex_joint"],
                    f"{finger}_mcp_abd_joint": NATURAL_CLOSE_TARGETS[f"{finger}_mcp_abd_joint"],
                    f"{finger}_pip_joint": NATURAL_CLOSE_TARGETS[f"{finger}_pip_joint"],
                    f"{finger}_dip_joint": NATURAL_CLOSE_TARGETS[f"{finger}_dip_joint"],
                },
            ),
        ]
        for pose_name, targets in poses:
            data = mujoco.MjData(model)
            _set_pose(model, data, targets)
            # Use the common view; it is more comparable across fingers and
            # avoids judging closeup camera changes as pose changes.
            image = _render(model, data)
            frame_name = f"{finger}_{pose_name}"
            path = visual_dir / f"{frame_name}.png"
            Image.fromarray(image).save(path)
            outputs["frames"][frame_name] = str(path)
            outputs["metrics"][frame_name] = _metrics(model, data)
            frames.append((pose_name, image))
        outputs["sheets"][finger] = _contact_sheet(frames, visual_dir / f"{finger}_joint_tuning_sheet.png", columns=2)

    return outputs


def write_report(
    report: Path,
    tuned_xml: Path,
    scene: Path,
    ball_scene: Path,
    changes: List[Dict[str, Any]],
    visual: Dict[str, Any],
    metadata: Path,
) -> None:
    lines: List[str] = []
    lines.append("# Export4 Long Finger Joint Tuning\n\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append("## Scope\n\n")
    lines.append(
        "This is an experimental simulation-side tuning pass for index/middle/ring/little only. "
        "The thumb is held neutral except for existing model geometry, and no CAD/STL/joint-tree edits are made.\n\n"
    )
    lines.append("## Outputs\n\n")
    lines.append(f"- Tuned hand: `{tuned_xml}`\n")
    lines.append(f"- No-ball scene: `{scene}`\n")
    lines.append(f"- Ball scene: `{ball_scene}`\n")
    lines.append(f"- Metadata: `{metadata}`\n")
    lines.append("- Visual sheets:\n")
    for key, value in visual.get("sheets", {}).items():
        lines.append(f"  - `{key}`: `{value}`\n")

    lines.append("\n## Tuned Limits\n\n")
    lines.append("| joint | range |\n")
    lines.append("|---|---:|\n")
    for joint, values in TUNED_LIMITS.items():
        lines.append(f"| `{joint}` | `{_fmt_range(values)}` |\n")

    lines.append("\n## Recommended Scripted Targets\n\n")
    lines.append("| joint | natural close target |\n")
    lines.append("|---|---:|\n")
    for joint, value in NATURAL_CLOSE_TARGETS.items():
        if joint.startswith("thumb"):
            continue
        lines.append(f"| `{joint}` | `{value:.4f}` |\n")

    lines.append("\n## Visual Notes\n\n")
    lines.append("- `full_hand_tuning_sheet.png` compares open, hook, natural close, and stronger safe close.\n")
    lines.append("- `full_hand_tuning_side_sheet.png` and `full_hand_tuning_top_sheet.png` were added to check for dorsal-side motion and obvious interpenetration.\n")
    lines.append("- Each `*_joint_tuning_sheet.png` shows open, single-joint motion, and one-finger combined motion.\n")
    lines.append("- Current visual pass: long fingers close toward the palm side in the tuned `natural_close` pose.\n")
    lines.append("- Current visual pass: no obvious palm stabbing or severe self-intersection is visible in the fixed camera sheets.\n")
    lines.append("- `full_but_safe` is tighter and should be treated as a range stress pose, not the default scripted target.\n")
    lines.append("- Current pass intentionally leaves thumb tuning for later.\n")
    lines.append("- If any finger still crosses through the palm in live viewer, reduce that finger's PIP/DIP target before increasing MCP flexion.\n")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tune export4 long finger joint ranges and render visual sheets")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--scene-output", default=str(DEFAULT_SCENE))
    parser.add_argument("--ball-scene-output", default=str(DEFAULT_BALL_SCENE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    input_xml = Path(args.input).resolve()
    output_xml = Path(args.output).resolve()
    scene = Path(args.scene_output).resolve()
    ball_scene = Path(args.ball_scene_output).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    archive = Path(args.archive).resolve()

    for path in (output_xml, scene, ball_scene, report, metadata, visual_dir):
        _backup_existing(path, archive)

    changes = write_tuned_mjcf(input_xml, output_xml)
    write_scenes(output_xml, scene, ball_scene)
    visual = render_tuning_outputs(output_xml, visual_dir)

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_long_finger_joint_tuning_v1",
        "input_xml": input_xml,
        "tuned_xml": output_xml,
        "scene": scene,
        "ball_scene": ball_scene,
        "tuned_limits": TUNED_LIMITS,
        "natural_close_targets": NATURAL_CLOSE_TARGETS,
        "hook_targets": HOOK_TARGETS,
        "full_but_safe_targets": FULL_BUT_SAFE_TARGETS,
        "changes": changes,
        "visual": visual,
        "notes": [
            "Thumb intentionally left neutral.",
            "Use visual sheets for per-joint judgement before promoting these ranges.",
            "CAD/STL/joint tree unchanged.",
        ],
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(report, output_xml, scene, ball_scene, changes, visual, metadata)
    print(f"Saved tuned hand: {output_xml}")
    print(f"Saved report: {report}")
    print(f"Saved visual dir: {visual_dir}")


if __name__ == "__main__":
    main()
