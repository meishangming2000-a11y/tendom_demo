#!/usr/bin/env python3
"""Tune export4 thumb opposition targets on top of long-finger tuning.

This is an experimental MJCF/control-target pass. CAD, STL, joint names, and
the joint tree are not changed. Long fingers are held in the previously tuned
natural-close pose while thumb CMC/MCP/IP combinations are scored and rendered.
"""

from __future__ import annotations

import argparse
import itertools
import json
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "mjcf" / "hand_stage1_export4_long_finger_tuned.xml"
DEFAULT_OUTPUT = ROOT / "mjcf" / "hand_stage1_export4_thumb_tuned.xml"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_thumb_tuned.xml"
DEFAULT_BALL_SCENE = ROOT / "mjcf" / "scene_ball_export4_thumb_tuned.xml"
DEFAULT_REPORT = ROOT / "docs" / "export4_thumb_joint_tuning_report.md"
DEFAULT_METADATA = ROOT / "metadata" / "export4_thumb_joint_tuning.json"
DEFAULT_VISUAL_DIR = ROOT / "docs" / "visual_checks_export4_thumb_tuning"
DEFAULT_ARCHIVE = ROOT / "archive"

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

THUMB_LIMITS = {
    # Keep CMC bidirectional until SolidWorks axis semantics are finally signed
    # off. The selected target is written as metadata/control, not hard-coded as
    # a new joint origin or axis.
    "thumb_cmc_abd_joint": (-1.05, 1.05),
    "thumb_cmc_joint": (-0.95, 0.95),
    "thumb_mcp_joint": (-0.10, 1.20),
    # The sign audit indicated the current thumb IP closes in the negative
    # direction in this coordinate convention.
    "thumb_ip_joint": (-0.85, 0.05),
}

THUMB_SCAN = {
    "thumb_cmc_abd_joint": [-0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9],
    "thumb_cmc_joint": [-0.8, -0.5, -0.2, 0.0, 0.25, 0.5, 0.8],
    "thumb_mcp_joint": [0.0, 0.25, 0.5, 0.8, 1.05],
    "thumb_ip_joint": [-0.75, -0.5, -0.25, 0.0],
}

# Visual inspection showed that the minimum-distance candidate can hide the
# thumb under the long fingers. This target gives up a few millimeters of pure
# tip proximity for a more natural-looking opposition pose with mild MCP/IP
# flexion. It remains an experimental control target, not a CAD or joint-axis
# change.
VISUAL_RECOMMENDED_THUMB_TARGET = {
    "thumb_cmc_abd_joint": -0.3,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}

PRESHAPE_FINGER_TARGETS = {
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
    dst = archive / f"{path.name}.before_thumb_tuning_{stamp}"
    if path.is_dir():
        shutil.copytree(path, dst)
    else:
        shutil.copy2(path, dst)


def _fmt_range(values: Tuple[float, float]) -> str:
    return f"{values[0]:.6g} {values[1]:.6g}"


def write_thumb_tuned_mjcf(input_xml: Path, output_xml: Path) -> List[Dict[str, Any]]:
    tree = ET.parse(input_xml)
    root = tree.getroot()
    changes: List[Dict[str, Any]] = []
    for joint in root.findall(".//joint"):
        name = joint.attrib.get("name", "")
        if name not in THUMB_LIMITS:
            continue
        old = joint.attrib.get("range", "")
        joint.attrib["range"] = _fmt_range(THUMB_LIMITS[name])
        changes.append({"kind": "joint_range", "name": name, "old": old, "new": joint.attrib["range"]})
    for actuator in root.findall(".//actuator/position"):
        joint_name = actuator.attrib.get("joint", "")
        if joint_name not in THUMB_LIMITS:
            continue
        old = actuator.attrib.get("ctrlrange", "")
        actuator.attrib["ctrlrange"] = _fmt_range(THUMB_LIMITS[joint_name])
        changes.append(
            {
                "kind": "actuator_ctrlrange",
                "name": actuator.attrib.get("name", ""),
                "joint": joint_name,
                "old": old,
                "new": actuator.attrib["ctrlrange"],
            }
        )
    root.insert(0, ET.Comment("Experimental thumb-tuned range draft. CAD/STL/joint tree unchanged."))
    output_xml.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)
    return changes


def write_scenes(hand_xml: Path, scene: Path, ball_scene: Path) -> None:
    include_name = hand_xml.name
    scene.write_text(
        f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_thumb_tuned_scene\">
  <include file=\"{include_name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"thumb_tuned_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"thumb_tuned_ground_mat\" texture=\"thumb_tuned_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <light pos=\"-0.25 -0.25 0.55\" directional=\"false\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"thumb_tuned_ground_mat\" contype=\"0\" conaffinity=\"0\"/>
  </worldbody>
</mujoco>
""",
        encoding="utf-8",
    )
    ball_scene.write_text(
        f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_thumb_tuned_ball_scene\">
  <include file=\"{include_name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"thumb_tuned_ball_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"thumb_tuned_ball_ground_mat\" texture=\"thumb_tuned_ball_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"thumb_tuned_ball_ground_mat\" contype=\"1\" conaffinity=\"3\"/>
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


def _set_pose(model, data, targets: Dict[str, float]) -> None:
    import mujoco

    data.qpos[:] = model.qpos0
    for joint_id in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id) or ""
        if joint_name not in targets:
            continue
        low, high = model.jnt_range[joint_id]
        value = float(np.clip(targets[joint_name], low, high))
        data.qpos[int(model.jnt_qposadr[joint_id])] = value
    mujoco.mj_forward(model, data)


def _site(model, data, name: str) -> np.ndarray:
    import mujoco

    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    return data.site_xpos[sid].copy() if sid >= 0 else np.zeros(3)


def _body(model, data, name: str) -> np.ndarray:
    import mujoco

    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else np.zeros(3)


def _palm_reference(model, data) -> np.ndarray:
    import mujoco

    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if bid < 0:
        return np.zeros(3)
    local = np.asarray([0.0, 0.048, 0.002])
    mat = data.xmat[bid].reshape(3, 3)
    return data.xpos[bid].copy() + mat @ local


def _score_pose(model, values: Dict[str, float]) -> Dict[str, Any]:
    data = __import__("mujoco").MjData(model)
    targets = {**LONG_FINGER_TARGETS, **values}
    _set_pose(model, data, targets)
    thumb = _site(model, data, "thumb_tip_site")
    index = _site(model, data, "index_tip_site")
    middle = _site(model, data, "middle_tip_site")
    ring = _site(model, data, "ring_tip_site")
    palm = _palm_reference(model, data)
    thumb_mcp = _body(model, data, "thumb_proximal_link")

    ti = float(np.linalg.norm(thumb - index))
    tm = float(np.linalg.norm(thumb - middle))
    tr = float(np.linalg.norm(thumb - ring))
    tp = float(np.linalg.norm(thumb - palm))
    palmar_advancement = float(thumb[1] - thumb_mcp[1])
    height_penalty = max(0.0, float(abs(thumb[2] - index[2]) - 0.06))
    awkward_penalty = 0.0
    if thumb[1] < palm[1] - 0.02:
        awkward_penalty += 0.04
    if ti < 0.018:
        awkward_penalty += 0.04
    if tm < 0.014:
        awkward_penalty += 0.04
    if tr < 0.012:
        awkward_penalty += 0.04

    score = (
        ti
        + 0.55 * tm
        + 0.20 * tr
        + 0.20 * tp
        + height_penalty
        + awkward_penalty
        - 0.045 * palmar_advancement
    )
    return {
        "targets": values,
        "score": float(score),
        "thumb_index_distance": ti,
        "thumb_middle_distance": tm,
        "thumb_ring_distance": tr,
        "thumb_palm_distance": tp,
        "palmar_advancement_y": palmar_advancement,
        "thumb_tip": thumb,
        "index_tip": index,
        "middle_tip": middle,
        "palm_reference": palm,
        "awkward_penalty": awkward_penalty,
        "height_penalty": height_penalty,
    }


def scan_thumb_candidates(model_xml: Path, max_candidates: int) -> List[Dict[str, Any]]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(model_xml))
    keys = list(THUMB_SCAN)
    candidates: List[Dict[str, Any]] = []
    for combo in itertools.product(*(THUMB_SCAN[key] for key in keys)):
        values = {key: float(value) for key, value in zip(keys, combo)}
        candidates.append(_score_pose(model, values))
    candidates.sort(key=lambda item: item["score"])
    return candidates[: int(max_candidates)]


def _candidate_for_target(candidates: List[Dict[str, Any]], target: Dict[str, float]) -> Dict[str, Any] | None:
    for candidate in candidates:
        values = candidate.get("targets", {})
        if all(abs(float(values.get(key, 999.0)) - float(value)) < 1e-9 for key, value in target.items()):
            return candidate
    return None


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


def _sheet(frames: List[Tuple[str, np.ndarray]], out_path: Path, columns: int = 2) -> str:
    from PIL import Image, ImageDraw

    if not frames:
        return ""
    w = frames[0][1].shape[1]
    h = frames[0][1].shape[0]
    label_h = 38
    columns = min(columns, len(frames))
    rows = int(np.ceil(len(frames) / columns))
    sheet = Image.new("RGB", (columns * w, rows * (h + label_h)), (242, 244, 247))
    draw = ImageDraw.Draw(sheet)
    for idx, (label, image) in enumerate(frames):
        x = (idx % columns) * w
        y = (idx // columns) * (h + label_h)
        draw.text((x + 10, y + 8), label, fill=(20, 24, 32))
        sheet.paste(Image.fromarray(image), (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return str(out_path)


def render_candidates(model_xml: Path, candidates: List[Dict[str, Any]], visual_dir: Path) -> Dict[str, Any]:
    import mujoco
    from PIL import Image

    model = mujoco.MjModel.from_xml_path(str(model_xml))
    visual_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    side_frames = []
    top_frames = []
    paths: List[str] = []

    # Include open and long-finger-only reference poses.
    references = [
        ("open_thumb_neutral", LONG_FINGER_TARGETS | {key: 0.0 for key in THUMB_SCAN}),
    ]
    best = candidates[:10]
    for label, targets in references:
        data = mujoco.MjData(model)
        _set_pose(model, data, targets)
        image = _render(model, data)
        side = _render(model, data, azimuth=90, elevation=-30)
        top = _render(model, data, azimuth=180, elevation=-75, distance=0.40)
        path = visual_dir / f"{label}.png"
        Image.fromarray(image).save(path)
        paths.append(str(path))
        frames.append((label, image))
        side_frames.append((label, side))
        top_frames.append((label, top))

    for idx, candidate in enumerate(best, start=1):
        targets = {**LONG_FINGER_TARGETS, **candidate["targets"]}
        label = (
            f"cand{idx:02d} score={candidate['score']:.3f} "
            f"TI={candidate['thumb_index_distance']:.3f}"
        )
        data = mujoco.MjData(model)
        _set_pose(model, data, targets)
        image = _render(model, data)
        side = _render(model, data, azimuth=90, elevation=-30)
        top = _render(model, data, azimuth=180, elevation=-75, distance=0.40)
        stem = f"candidate_{idx:02d}"
        for suffix, frame in (("", image), ("_side", side), ("_top", top)):
            path = visual_dir / f"{stem}{suffix}.png"
            Image.fromarray(frame).save(path)
            paths.append(str(path))
        frames.append((label, image))
        side_frames.append((label, side))
        top_frames.append((label, top))

    return {
        "frames": paths,
        "front_sheet": _sheet(frames, visual_dir / "thumb_candidates_front_sheet.png", columns=2),
        "side_sheet": _sheet(side_frames, visual_dir / "thumb_candidates_side_sheet.png", columns=2),
        "top_sheet": _sheet(top_frames, visual_dir / "thumb_candidates_top_sheet.png", columns=2),
    }


def _apply_thumb_debug_colors(model) -> None:
    import mujoco

    for geom_id in range(model.ngeom):
        geom_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""
        if geom_name.startswith("thumb_") or "_thumb_" in geom_name:
            model.geom_rgba[geom_id] = np.asarray([1.0, 0.48, 0.08, 1.0])

    site_colors = {
        "thumb_tip_site": [1.0, 0.05, 0.02, 1.0],
        "index_tip_site": [0.10, 1.0, 0.15, 1.0],
        "middle_tip_site": [0.0, 0.85, 1.0, 1.0],
        "ring_tip_site": [0.10, 0.35, 1.0, 0.9],
        "little_tip_site": [0.10, 0.35, 1.0, 0.9],
    }
    for site_name, rgba in site_colors.items():
        site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        if site_id >= 0:
            model.site_rgba[site_id] = np.asarray(rgba)


def render_visual_focus(model_xml: Path, visual_dir: Path) -> Dict[str, Any]:
    """Render thumb-colored focus sheets for human visual judgment."""
    import mujoco
    from PIL import Image

    focus_dir = visual_dir / "focus_pass_colored"
    focus_dir.mkdir(parents=True, exist_ok=True)

    selected = [
        ("score_best", {"thumb_cmc_abd_joint": -0.3, "thumb_cmc_joint": 0.25, "thumb_mcp_joint": 0.0, "thumb_ip_joint": 0.0}),
        ("visual_recommended", VISUAL_RECOMMENDED_THUMB_TARGET),
        ("cmc_ip_variant", {"thumb_cmc_abd_joint": -0.3, "thumb_cmc_joint": 0.25, "thumb_mcp_joint": 0.0, "thumb_ip_joint": -0.25}),
        ("palmar_variant", {"thumb_cmc_abd_joint": 0.0, "thumb_cmc_joint": 0.25, "thumb_mcp_joint": 0.0, "thumb_ip_joint": 0.0}),
        ("strong_mcp_variant", {"thumb_cmc_abd_joint": -0.3, "thumb_cmc_joint": -0.2, "thumb_mcp_joint": 0.8, "thumb_ip_joint": 0.0}),
        ("neutral_abd_mild", {"thumb_cmc_abd_joint": 0.0, "thumb_cmc_joint": 0.25, "thumb_mcp_joint": 0.25, "thumb_ip_joint": -0.25}),
    ]
    pose_sets = {
        "preshape": PRESHAPE_FINGER_TARGETS,
        "fullclose": LONG_FINGER_TARGETS,
    }

    paths: Dict[str, str] = {}
    summary: List[Dict[str, Any]] = []
    model = mujoco.MjModel.from_xml_path(str(model_xml))
    _apply_thumb_debug_colors(model)

    def render_focus(data, *, lookat, distance, azimuth, elevation):
        renderer = mujoco.Renderer(model, width=820, height=620)
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

    for pose_name, finger_targets in pose_sets.items():
        top_frames: List[Tuple[str, np.ndarray]] = []
        front_frames: List[Tuple[str, np.ndarray]] = []
        thumbside_frames: List[Tuple[str, np.ndarray]] = []
        for label, thumb_target in selected:
            data = mujoco.MjData(model)
            _set_pose(model, data, {**finger_targets, **thumb_target})
            thumb = _site(model, data, "thumb_tip_site")
            index = _site(model, data, "index_tip_site")
            middle = _site(model, data, "middle_tip_site")
            ti = float(np.linalg.norm(thumb - index))
            tm = float(np.linalg.norm(thumb - middle))
            sheet_label = f"{label}\nTI={ti:.3f} TM={tm:.3f} y={thumb[1]:.3f}"
            top_frames.append(
                (
                    sheet_label,
                    render_focus(
                        data,
                        lookat=(0.0, 0.055, 0.20),
                        distance=0.26,
                        azimuth=180,
                        elevation=-78,
                    ),
                )
            )
            front_frames.append(
                (
                    sheet_label,
                    render_focus(
                        data,
                        lookat=(0.0, 0.045, 0.19),
                        distance=0.30,
                        azimuth=145,
                        elevation=-28,
                    ),
                )
            )
            thumbside_frames.append(
                (
                    sheet_label,
                    render_focus(
                        data,
                        lookat=(-0.015, 0.04, 0.19),
                        distance=0.22,
                        azimuth=75,
                        elevation=-16,
                    ),
                )
            )
            summary.append(
                {
                    "pose": pose_name,
                    "label": label,
                    "targets": thumb_target,
                    "thumb_index_distance": ti,
                    "thumb_middle_distance": tm,
                    "thumb_tip": thumb,
                    "index_tip": index,
                    "middle_tip": middle,
                }
            )

        for view_name, frames in (
            ("top", top_frames),
            ("front", front_frames),
            ("thumbside", thumbside_frames),
        ):
            path = focus_dir / f"{pose_name}_{view_name}_colored_sheet.png"
            paths[f"{pose_name}_{view_name}_colored_sheet"] = _sheet(frames, path, columns=3)

        # Save the visual-recommended full-close frame as a standalone image for
        # later status docs and quick inspection.
        if pose_name == "fullclose":
            data = mujoco.MjData(model)
            _set_pose(model, data, {**finger_targets, **VISUAL_RECOMMENDED_THUMB_TARGET})
            standalone = focus_dir / "fullclose_visual_recommended_top.png"
            Image.fromarray(
                render_focus(
                    data,
                    lookat=(0.0, 0.055, 0.20),
                    distance=0.26,
                    azimuth=180,
                    elevation=-78,
                )
            ).save(standalone)
            paths["fullclose_visual_recommended_top"] = str(standalone)

    paths["summary_json"] = str(focus_dir / "colored_focus_summary.json")
    (focus_dir / "colored_focus_summary.json").write_text(
        json.dumps(_json_ready(summary), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return paths


def write_report(
    report: Path,
    tuned_xml: Path,
    scene: Path,
    ball_scene: Path,
    changes: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    visual: Dict[str, Any],
    visual_focus: Dict[str, Any],
    metadata: Path,
) -> None:
    best = candidates[0] if candidates else {}
    visual_best = _candidate_for_target(candidates, VISUAL_RECOMMENDED_THUMB_TARGET) or best
    lines: List[str] = []
    lines.append("# Export4 Thumb Joint Tuning\n\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append("## Scope\n\n")
    lines.append(
        "This pass tunes thumb target ranges on top of the long-finger-tuned export4 hand. "
        "Long fingers are held in the natural close pose. No CAD, STL, joint names, axes, or joint tree are changed.\n\n"
    )
    lines.append("## Outputs\n\n")
    lines.append(f"- Thumb tuned hand: `{tuned_xml}`\n")
    lines.append(f"- No-ball scene: `{scene}`\n")
    lines.append(f"- Ball scene: `{ball_scene}`\n")
    lines.append(f"- Metadata: `{metadata}`\n")
    for key in ("front_sheet", "side_sheet", "top_sheet"):
        lines.append(f"- `{key}`: `{visual.get(key, '')}`\n")
    for key in ("preshape_top_colored_sheet", "fullclose_top_colored_sheet", "fullclose_visual_recommended_top"):
        lines.append(f"- `{key}`: `{visual_focus.get(key, '')}`\n")

    lines.append("\n## Tuned Thumb Limits\n\n")
    lines.append("| joint | range |\n|---|---:|\n")
    for joint, values in THUMB_LIMITS.items():
        lines.append(f"| `{joint}` | `{_fmt_range(values)}` |\n")

    if best:
        lines.append("\n## Score-Best Thumb Target\n\n")
        lines.append("| joint | target |\n|---|---:|\n")
        for joint, value in best["targets"].items():
            lines.append(f"| `{joint}` | `{float(value):.4f}` |\n")
        lines.append("\nMetrics for best target:\n\n")
        lines.append(f"- thumb-index distance: `{best['thumb_index_distance']:.4f} m`\n")
        lines.append(f"- thumb-middle distance: `{best['thumb_middle_distance']:.4f} m`\n")
        lines.append(f"- thumb-palm distance: `{best['thumb_palm_distance']:.4f} m`\n")
        lines.append(f"- palmar advancement Y: `{best['palmar_advancement_y']:.4f} m`\n")

    if visual_best:
        lines.append("\n## Visual Recommended Thumb Target\n\n")
        lines.append(
            "The visual recommendation is preferred for scripted grasp because it adds mild thumb MCP/IP flexion "
            "and looks more like opposition in the color-coded focus renders. It is not the pure minimum-distance candidate.\n\n"
        )
        lines.append("| joint | target |\n|---|---:|\n")
        for joint, value in VISUAL_RECOMMENDED_THUMB_TARGET.items():
            lines.append(f"| `{joint}` | `{float(value):.4f}` |\n")
        lines.append("\nMetrics for visual recommended target in full-close context:\n\n")
        lines.append(f"- thumb-index distance: `{visual_best['thumb_index_distance']:.4f} m`\n")
        lines.append(f"- thumb-middle distance: `{visual_best['thumb_middle_distance']:.4f} m`\n")
        lines.append(f"- thumb-palm distance: `{visual_best['thumb_palm_distance']:.4f} m`\n")
        lines.append(f"- palmar advancement Y: `{visual_best['palmar_advancement_y']:.4f} m`\n")

    lines.append("\n## Candidate Table\n\n")
    lines.append("| rank | score | cmc_abd | cmc | mcp | ip | thumb-index | thumb-middle | note |\n")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for idx, candidate in enumerate(candidates[:10], start=1):
        target = candidate["targets"]
        note = "score best" if idx == 1 else ""
        if all(
            abs(float(target.get(key, 999.0)) - float(value)) < 1e-9
            for key, value in VISUAL_RECOMMENDED_THUMB_TARGET.items()
        ):
            note = "visual recommended"
        lines.append(
            f"| {idx} | {candidate['score']:.4f} | {target['thumb_cmc_abd_joint']:.2f} | "
            f"{target['thumb_cmc_joint']:.2f} | {target['thumb_mcp_joint']:.2f} | "
            f"{target['thumb_ip_joint']:.2f} | {candidate['thumb_index_distance']:.4f} | "
            f"{candidate['thumb_middle_distance']:.4f} | {note} |\n"
        )

    lines.append("\n## Visual Notes\n\n")
    lines.append("- Candidate sheets include front, side, and top fixed-camera views.\n")
    lines.append("- Color-coded focus sheets use orange thumb links, red thumb tip, green index tip, and cyan middle tip.\n")
    lines.append("- The scoring function rewards thumb-index/thumb-middle proximity and palmar movement, while penalizing extremely tiny distances that likely indicate visual overlap.\n")
    lines.append("- Visual inspection selected the mild MCP/IP flexion target because it shows the thumb crossing toward the index/middle side without the fully extended thumb look.\n")
    lines.append("- This remains a target tuning pass; final thumb CMC axis semantics still need SolidWorks confirmation if the motion looks mechanically implausible in viewer.\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tune export4 thumb opposition targets")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--scene-output", default=str(DEFAULT_SCENE))
    parser.add_argument("--ball-scene-output", default=str(DEFAULT_BALL_SCENE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--max-candidates", type=int, default=30)
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

    changes = write_thumb_tuned_mjcf(input_xml, output_xml)
    write_scenes(output_xml, scene, ball_scene)
    candidates = scan_thumb_candidates(output_xml, args.max_candidates)
    visual = render_candidates(output_xml, candidates, visual_dir)
    visual_focus = render_visual_focus(output_xml, visual_dir)
    visual_recommended = _candidate_for_target(candidates, VISUAL_RECOMMENDED_THUMB_TARGET) or (candidates[0] if candidates else {})

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_thumb_joint_tuning_v1",
        "input_xml": input_xml,
        "thumb_tuned_xml": output_xml,
        "scene": scene,
        "ball_scene": ball_scene,
        "thumb_limits": THUMB_LIMITS,
        "long_finger_targets": LONG_FINGER_TARGETS,
        "scan_grid": THUMB_SCAN,
        "score_best_thumb_target": candidates[0]["targets"] if candidates else {},
        "visual_recommended_thumb_target": VISUAL_RECOMMENDED_THUMB_TARGET,
        "visual_recommended_metrics": visual_recommended,
        "candidates": candidates,
        "changes": changes,
        "visual": visual,
        "visual_focus": visual_focus,
        "notes": [
            "Long fingers held at natural close.",
            "Visual recommended target uses mild thumb MCP/IP flexion instead of pure minimum-distance ranking.",
            "No CAD/STL/joint tree changes.",
            "Thumb CMC axes are still mechanical-semantics TODO if visuals look implausible.",
        ],
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(report, output_xml, scene, ball_scene, changes, candidates, visual, visual_focus, metadata)
    if candidates:
        print("Best thumb target:", candidates[0]["targets"])
        print("thumb-index distance:", f"{candidates[0]['thumb_index_distance']:.4f}")
        print("thumb-middle distance:", f"{candidates[0]['thumb_middle_distance']:.4f}")
    if visual_recommended:
        print("Visual recommended thumb target:", VISUAL_RECOMMENDED_THUMB_TARGET)
        print("visual thumb-index distance:", f"{visual_recommended['thumb_index_distance']:.4f}")
        print("visual thumb-middle distance:", f"{visual_recommended['thumb_middle_distance']:.4f}")
    print(f"Saved thumb tuned hand: {output_xml}")
    print(f"Saved report: {report}")
    print(f"Saved visual dir: {visual_dir}")


if __name__ == "__main__":
    main()
