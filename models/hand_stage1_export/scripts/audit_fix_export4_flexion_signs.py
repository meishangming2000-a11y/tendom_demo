#!/usr/bin/env python3
"""Audit and experimentally fix export4 finger flexion sign limits.

This script does not edit CAD, STL, joint names, or the joint tree. It compares
small positive and negative perturbations for each finger joint, then writes a
separate MJCF draft where only joint ranges and actuator ctrlranges are changed
for joints whose current positive-only limit appears opposite to closing.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "mjcf" / "hand_stage1_export4.xml"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_no_ball_compare.xml"
DEFAULT_OUTPUT = ROOT / "mjcf" / "hand_stage1_export4_flexion_sign_fixed.xml"
DEFAULT_SCENE_OUT = ROOT / "mjcf" / "scene_export4_flexion_sign_fixed.xml"
DEFAULT_BALL_SCENE_OUT = ROOT / "mjcf" / "scene_ball_export4_flexion_sign_fixed.xml"
DEFAULT_DOC = ROOT / "docs" / "export4_flexion_sign_audit.md"
DEFAULT_JSON = ROOT / "metadata" / "export4_flexion_sign_audit.json"
DEFAULT_VISUAL_DIR = ROOT / "docs" / "visual_checks_export4_flexion_sign"
DEFAULT_ARCHIVE = ROOT / "archive"


TIP_SITE_BY_FINGER = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}

FINGER_BY_JOINT = {
    "index_mcp_flex_joint": "index",
    "index_mcp_abd_joint": "index",
    "index_pip_joint": "index",
    "index_dip_joint": "index",
    "middle_mcp_flex_joint": "middle",
    "middle_mcp_abd_joint": "middle",
    "middle_pip_joint": "middle",
    "middle_dip_joint": "middle",
    "ring_mcp_flex_joint": "ring",
    "ring_mcp_abd_joint": "ring",
    "ring_pip_joint": "ring",
    "ring_dip_joint": "ring",
    "little_mcp_flex_joint": "little",
    "little_mcp_abd_joint": "little",
    "little_pip_joint": "little",
    "little_dip_joint": "little",
    "thumb_cmc_abd_joint": "thumb",
    "thumb_cmc_joint": "thumb",
    "thumb_mcp_joint": "thumb",
    "thumb_ip_joint": "thumb",
}

# These are the joints whose limits are expected to express closing/flexion.
# The mcp_flex joints are left as audit-only because current project notes say
# mcp_flex/mcp_abd naming may be semantically reversed.
FLEXION_LIMIT_CANDIDATES = {
    "index_mcp_abd_joint",
    "index_pip_joint",
    "index_dip_joint",
    "middle_mcp_abd_joint",
    "middle_pip_joint",
    "middle_dip_joint",
    "ring_mcp_abd_joint",
    "ring_pip_joint",
    "ring_dip_joint",
    "little_mcp_abd_joint",
    "little_pip_joint",
    "little_dip_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
}

THUMB_CMC_AUDIT_ONLY = {"thumb_cmc_abd_joint", "thumb_cmc_joint"}


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
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
    target = archive / f"{path.name}.before_flexion_sign_audit_{stamp}"
    if path.is_dir():
        shutil.copytree(path, target)
    else:
        shutil.copy2(path, target)


def _mj_name(model, obj_type, idx: int) -> str:
    import mujoco

    return mujoco.mj_id2name(model, obj_type, idx) or ""


def _parse_range(raw: str | None) -> Tuple[float, float]:
    if not raw:
        return 0.0, 0.0
    parts = [float(item) for item in raw.replace(",", " ").split()]
    if len(parts) != 2:
        return 0.0, 0.0
    return float(parts[0]), float(parts[1])


def _fmt_range(values: Tuple[float, float]) -> str:
    return f"{values[0]:.6g} {values[1]:.6g}"


def _new_flipped_range(old_range: Tuple[float, float], close_sign: str) -> Tuple[float, float]:
    lower, upper = old_range
    max_abs = max(abs(lower), abs(upper), 0.05)
    if close_sign == "negative":
        # Keep zero available as the open pose whenever the old limit was
        # positive-only. This makes viewer/reset behavior less surprising.
        return -max_abs, 0.0
    if close_sign == "positive":
        return 0.0, max_abs
    return lower, upper


def _current_limit_bias(joint_range: Tuple[float, float]) -> str:
    lower, upper = joint_range
    if lower >= 0.0 and upper > 0.0:
        return "positive_only"
    if upper <= 0.0 and lower < 0.0:
        return "negative_only"
    return "contains_zero_or_bidirectional"


def _range_needs_sign_rebalance(joint_range: Tuple[float, float], close_sign: str) -> bool:
    lower, upper = joint_range
    if close_sign == "negative":
        return upper > 0.0 and abs(lower) < abs(upper)
    if close_sign == "positive":
        return lower < 0.0 and abs(upper) < abs(lower)
    return False


def _palm_reference(model, data) -> np.ndarray:
    import mujoco

    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if palm_id < 0:
        return np.zeros(3, dtype=np.float32)
    palm_center_local = np.asarray([0.0, 0.048, 0.002], dtype=np.float32)
    mat = np.asarray(data.xmat[palm_id], dtype=np.float32).reshape(3, 3)
    return np.asarray(data.xpos[palm_id], dtype=np.float32) + mat @ palm_center_local


def _site_pos(model, data, site_name: str) -> np.ndarray:
    import mujoco

    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if site_id < 0:
        return np.zeros(3, dtype=np.float32)
    return np.asarray(data.site_xpos[site_id], dtype=np.float32).copy()


def _forward_with_joint(model, joint_name: str | None, value: float):
    import mujoco

    data = mujoco.MjData(model)
    data.qpos[:] = model.qpos0
    if joint_name:
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if joint_id >= 0:
            qadr = int(model.jnt_qposadr[joint_id])
            data.qpos[qadr] = float(value)
    mujoco.mj_forward(model, data)
    return data


def _finger_tip_metric(model, data, finger: str) -> Tuple[np.ndarray, float]:
    tip = _site_pos(model, data, TIP_SITE_BY_FINGER[finger])
    palm = _palm_reference(model, data)
    return tip, float(np.linalg.norm(tip - palm))


def audit_joint_signs(model_path: Path, perturb: float, tolerance: float) -> List[Dict[str, Any]]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(model_path))
    neutral_data = _forward_with_joint(model, None, 0.0)

    joint_ranges = {}
    joint_axes = {}
    for joint_id in range(model.njnt):
        name = _mj_name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
        if not name:
            continue
        joint_ranges[name] = tuple(float(v) for v in model.jnt_range[joint_id])
        joint_axes[name] = np.asarray(model.jnt_axis[joint_id], dtype=np.float32).tolist()

    results: List[Dict[str, Any]] = []
    for joint_name, finger in FINGER_BY_JOINT.items():
        if joint_name not in joint_ranges:
            results.append({"joint": joint_name, "finger": finger, "status": "missing"})
            continue

        neutral_tip, neutral_dist = _finger_tip_metric(model, neutral_data, finger)
        pos_data = _forward_with_joint(model, joint_name, perturb)
        neg_data = _forward_with_joint(model, joint_name, -perturb)
        pos_tip, pos_dist = _finger_tip_metric(model, pos_data, finger)
        neg_tip, neg_dist = _finger_tip_metric(model, neg_data, finger)

        pos_delta = pos_dist - neutral_dist
        neg_delta = neg_dist - neutral_dist
        pos_world_delta = pos_tip - neutral_tip
        neg_world_delta = neg_tip - neutral_tip
        pos_palmar_delta = float(pos_world_delta[1])
        neg_palmar_delta = float(neg_world_delta[1])

        if finger == "thumb":
            # Thumb opposition is multi-axis; keep the old distance criterion
            # only as a diagnostic signal and do not auto-flip CMC limits.
            delta_gap = abs(pos_delta - neg_delta)
            if delta_gap < tolerance:
                close_sign = "uncertain"
            elif neg_delta < pos_delta:
                close_sign = "negative"
            else:
                close_sign = "positive"
            criterion = "tip_to_palm_distance"
        else:
            # Previous palm-side audit established +Y as the palmar side for
            # export4. A long-finger closing angle should push the fingertip
            # toward +Y, not merely reduce distance to the palm center.
            delta_gap = abs(pos_palmar_delta - neg_palmar_delta)
            if delta_gap < tolerance:
                close_sign = "uncertain"
            elif neg_palmar_delta > pos_palmar_delta:
                close_sign = "negative"
            else:
                close_sign = "positive"
            criterion = "world_plus_y_palmar_displacement"

        joint_range = joint_ranges[joint_name]
        bias = _current_limit_bias(joint_range)
        planned_change = False
        reason = "audit_only"
        new_range = joint_range
        if joint_name in FLEXION_LIMIT_CANDIDATES and close_sign in {"positive", "negative"}:
            if close_sign == "negative" and _range_needs_sign_rebalance(joint_range, close_sign):
                planned_change = True
                reason = "current_limit_positive_or_positive_dominant_but_negative_angle_moves_palmar"
                new_range = _new_flipped_range(joint_range, close_sign)
            elif close_sign == "positive" and _range_needs_sign_rebalance(joint_range, close_sign):
                planned_change = True
                reason = "current_limit_negative_or_negative_dominant_but_positive_angle_moves_palmar"
                new_range = _new_flipped_range(joint_range, close_sign)
            else:
                reason = "limit_already_supports_observed_closing_sign"
        elif joint_name in THUMB_CMC_AUDIT_ONLY:
            reason = "thumb_cmc_audit_only_do_not_autoflip"
        elif "mcp_flex" in joint_name:
            reason = "mcp_flex_audit_only_possible_spread_joint"

        results.append(
            {
                "joint": joint_name,
                "finger": finger,
                "axis": joint_axes.get(joint_name, []),
                "old_range": joint_range,
                "new_range": new_range,
                "current_limit_bias": bias,
                "neutral_tip": neutral_tip,
                "positive_tip": pos_tip,
                "negative_tip": neg_tip,
                "neutral_tip_palm_distance": neutral_dist,
                "positive_tip_palm_distance": pos_dist,
                "negative_tip_palm_distance": neg_dist,
                "positive_distance_delta": pos_delta,
                "negative_distance_delta": neg_delta,
                "positive_world_delta": pos_world_delta,
                "negative_world_delta": neg_world_delta,
                "positive_palmar_y_delta": pos_palmar_delta,
                "negative_palmar_y_delta": neg_palmar_delta,
                "criterion": criterion,
                "observed_closing_sign": close_sign,
                "planned_change": planned_change,
                "reason": reason,
            }
        )
    return results


def apply_fixed_ranges(input_xml: Path, output_xml: Path, audit: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tree = ET.parse(input_xml)
    root = tree.getroot()
    changes = [item for item in audit if item.get("planned_change")]
    range_by_joint = {item["joint"]: tuple(item["new_range"]) for item in changes}
    change_log: List[Dict[str, Any]] = []

    for joint in root.findall(".//joint"):
        name = joint.attrib.get("name")
        if name not in range_by_joint:
            continue
        old = joint.attrib.get("range", "")
        joint.attrib["range"] = _fmt_range(range_by_joint[name])
        change_log.append({"kind": "joint_range", "name": name, "old": old, "new": joint.attrib["range"]})

    for actuator in root.findall(".//actuator/position"):
        joint_name = actuator.attrib.get("joint")
        if joint_name not in range_by_joint:
            continue
        old = actuator.attrib.get("ctrlrange", "")
        actuator.attrib["ctrlrange"] = _fmt_range(range_by_joint[joint_name])
        change_log.append(
            {
                "kind": "actuator_ctrlrange",
                "name": actuator.attrib.get("name", ""),
                "joint": joint_name,
                "old": old,
                "new": actuator.attrib["ctrlrange"],
            }
        )

    root.insert(0, ET.Comment("Experimental flexion-sign limit draft. CAD/STL/joint tree unchanged."))
    output_xml.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)
    return change_log


def write_scenes(fixed_hand: Path, scene_out: Path, ball_scene_out: Path) -> None:
    include_name = fixed_hand.name
    scene_text = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_flexion_sign_fixed_scene\">
  <include file=\"{include_name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"sign_fix_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"sign_fix_ground_mat\" texture=\"sign_fix_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <light pos=\"-0.25 -0.25 0.55\" directional=\"false\"/>
    <geom name=\"sign_fix_ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"sign_fix_ground_mat\" contype=\"0\" conaffinity=\"0\"/>
  </worldbody>
</mujoco>
"""
    ball_text = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"hand_stage1_export4_flexion_sign_fixed_ball_scene\">
  <include file=\"{include_name}\"/>
  <visual>
    <global azimuth=\"145\" elevation=\"-25\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"2d\" name=\"sign_fix_ball_ground_checker\" builtin=\"checker\"
      rgb1=\"0.18 0.20 0.22\" rgb2=\"0.28 0.30 0.32\" width=\"300\" height=\"300\"/>
    <material name=\"sign_fix_ball_ground_mat\" texture=\"sign_fix_ball_ground_checker\"
      texrepeat=\"4 4\" reflectance=\"0.15\"/>
  </asset>
  <worldbody>
    <light pos=\"0 -0.3 0.8\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"ground\" type=\"plane\" pos=\"0 0 0\" size=\"0.4 0.4 0.02\"
      material=\"sign_fix_ball_ground_mat\" contype=\"1\" conaffinity=\"3\"/>
    <body name=\"ball\" pos=\"0 0.045 0.22\">
      <freejoint name=\"ball_freejoint\"/>
      <geom name=\"ball_geom\" type=\"sphere\" size=\"0.025\" rgba=\"0.95 0.23 0.18 1\"
        mass=\"0.03\" friction=\"0.8 0.05 0.001\" condim=\"3\" contype=\"2\" conaffinity=\"1\"/>
    </body>
  </worldbody>
</mujoco>
"""
    scene_out.write_text(scene_text, encoding="utf-8")
    ball_scene_out.write_text(ball_text, encoding="utf-8")


def _set_joint_pose(model, data, targets: Dict[str, float]) -> None:
    import mujoco

    data.qpos[:] = model.qpos0
    for joint_name, value in targets.items():
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if joint_id < 0:
            continue
        qadr = int(model.jnt_qposadr[joint_id])
        data.qpos[qadr] = float(value)
    mujoco.mj_forward(model, data)


def _close_targets_from_audit(audit: List[Dict[str, Any]], fixed: bool) -> Dict[str, float]:
    targets: Dict[str, float] = {}
    for item in audit:
        joint_name = str(item.get("joint", ""))
        if joint_name not in FLEXION_LIMIT_CANDIDATES:
            continue
        close_sign = item.get("observed_closing_sign")
        old_range = tuple(float(v) for v in item.get("old_range", (0.0, 0.0)))
        new_range = tuple(float(v) for v in item.get("new_range", old_range))
        if fixed and item.get("planned_change"):
            targets[joint_name] = new_range[0] if close_sign == "negative" else new_range[1]
        else:
            targets[joint_name] = old_range[1] if old_range[1] > abs(old_range[0]) else old_range[0]
    # Keep CMC modest in the visual summary; this audit is about flexion limits.
    for joint_name in ("thumb_cmc_abd_joint", "thumb_cmc_joint"):
        targets[joint_name] = 0.0
    return targets


def render_visual_summary(
    original_xml: Path,
    fixed_xml: Path,
    audit: List[Dict[str, Any]],
    visual_dir: Path,
) -> Dict[str, Any]:
    import mujoco
    from PIL import Image, ImageDraw

    visual_dir.mkdir(parents=True, exist_ok=True)
    frames: List[Tuple[str, np.ndarray]] = []

    def render_model(label: str, xml_path: Path, targets: Dict[str, float]) -> None:
        model = mujoco.MjModel.from_xml_path(str(xml_path))
        data = mujoco.MjData(model)
        _set_joint_pose(model, data, targets)
        renderer = mujoco.Renderer(model, width=720, height=540)
        try:
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = np.asarray([0.0, 0.02, 0.18], dtype=np.float64)
            camera.distance = 0.38
            camera.azimuth = 180.0
            camera.elevation = -35.0
            renderer.update_scene(data, camera=camera)
            frames.append((label, renderer.render().copy()))
        finally:
            renderer.close()

    render_model("original_open", original_xml, {})
    render_model("original_old_positive_close", original_xml, _close_targets_from_audit(audit, fixed=False))
    render_model("fixed_observed_close", fixed_xml, _close_targets_from_audit(audit, fixed=True))

    individual = []
    for label, image in frames:
        path = visual_dir / f"{label}.png"
        Image.fromarray(image).save(path)
        individual.append(str(path))

    if not frames:
        return {"frames": [], "sheet": ""}

    cell_w, cell_h = frames[0][1].shape[1], frames[0][1].shape[0]
    label_h = 30
    sheet = Image.new("RGB", (cell_w, len(frames) * (cell_h + label_h)), (242, 244, 247))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for label, image in frames:
        draw.text((10, y + 8), label, fill=(25, 30, 36))
        sheet.paste(Image.fromarray(image), (0, y + label_h))
        y += cell_h + label_h
    sheet_path = visual_dir / "export4_flexion_sign_summary.png"
    sheet.save(sheet_path)
    return {"frames": individual, "sheet": str(sheet_path)}


def write_report(
    path: Path,
    audit: List[Dict[str, Any]],
    change_log: List[Dict[str, Any]],
    fixed_xml: Path,
    scene_out: Path,
    ball_scene_out: Path,
    visual: Dict[str, Any],
    metadata_path: Path,
) -> None:
    planned = [item for item in audit if item.get("planned_change")]
    uncertain = [item for item in audit if item.get("observed_closing_sign") == "uncertain"]
    lines: List[str] = []
    lines.append("# Export4 Flexion Sign Audit\n\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append("## Scope\n\n")
    lines.append(
        "This audit checks whether small positive or negative joint motion brings the relevant fingertip closer to the palm reference. "
        "It only generates an experimental MJCF with range/ctrlrange sign changes. CAD, STL, joint names, and joint tree are unchanged.\n\n"
    )
    lines.append("## Outputs\n\n")
    lines.append(f"- Fixed experimental hand: `{fixed_xml}`\n")
    lines.append(f"- No-ball scene: `{scene_out}`\n")
    lines.append(f"- Ball scene: `{ball_scene_out}`\n")
    lines.append(f"- Visual summary: `{visual.get('sheet', '')}`\n")
    lines.append(f"- Metadata: `{metadata_path}`\n\n")
    lines.append("## Summary\n\n")
    lines.append(f"- Audited joints: {len([item for item in audit if item.get('status') != 'missing'])}\n")
    lines.append(f"- Planned auto-fixes: {len(planned)}\n")
    lines.append(f"- Uncertain signs: {len(uncertain)}\n")
    lines.append("- For long fingers, the closing-sign criterion is fingertip displacement toward world `+Y`, which is the current export4 palmar side.\n")
    lines.append("- `mcp_flex` joints were audit-only because current project notes say MCP flex/abd naming may be reversed. Several also move palmar in the negative direction, so target sign may need follow-up.\n")
    lines.append("- Thumb CMC joints were audit-only because opposition is multi-axis and should not be auto-flipped from a single scalar metric.\n\n")

    lines.append("## Planned Limit / Ctrlrange Changes\n\n")
    if not planned:
        lines.append("No automatic range changes were recommended.\n\n")
    else:
        lines.append("| joint | old range | new range | observed closing sign | reason |\n")
        lines.append("|---|---:|---:|---|---|\n")
        for item in planned:
            lines.append(
                f"| `{item['joint']}` | `{_fmt_range(tuple(item['old_range']))}` | "
                f"`{_fmt_range(tuple(item['new_range']))}` | {item['observed_closing_sign']} | {item['reason']} |\n"
            )
        lines.append("\n")

    lines.append("## Per-Joint Audit\n\n")
    lines.append(
        "| joint | finger | old range | +angle delta m | -angle delta m | observed closing sign | planned change | note |\n"
    )
    lines.append("|---|---|---:|---:|---:|---|---|---|\n")
    for item in audit:
        if item.get("status") == "missing":
            lines.append(f"| `{item['joint']}` | {item['finger']} | missing | | | | no | missing in model |\n")
            continue
        lines.append(
        f"| `{item['joint']}` | {item['finger']} | `{_fmt_range(tuple(item['old_range']))}` | "
            f"{float(item['positive_distance_delta']):.6f} | {float(item['negative_distance_delta']):.6f} | "
            f"{item['observed_closing_sign']} | {item['planned_change']} | {item['reason']} |\n"
        )

    lines.append("\n## Interpretation\n\n")
    lines.append(
        "- For long fingers, `observed closing sign` means the sign whose fingertip moved further toward world `+Y`, the corrected palmar side.\n"
    )
    lines.append(
        "- For thumb CMC audit-only joints, the sign remains a distance/opposition diagnostic and is not auto-fixed.\n"
    )
    lines.append(
        "- If a joint was positive-only but negative perturbation closed the finger, the experimental model flips that limit to a negative range ending at zero.\n"
    )
    lines.append(
        "- This is a simulation-side repair for verification. If the result looks correct, the same sign convention should be repaired in SolidWorks/URDF limits later.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit and fix hand_stage1 export4 flexion sign limits")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--scene-output", default=str(DEFAULT_SCENE_OUT))
    parser.add_argument("--ball-scene-output", default=str(DEFAULT_BALL_SCENE_OUT))
    parser.add_argument("--report", default=str(DEFAULT_DOC))
    parser.add_argument("--metadata", default=str(DEFAULT_JSON))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--perturb", type=float, default=0.35)
    parser.add_argument("--tolerance", type=float, default=0.0008)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    input_xml = Path(args.input).resolve()
    output_xml = Path(args.output).resolve()
    scene_out = Path(args.scene_output).resolve()
    ball_scene_out = Path(args.ball_scene_output).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    archive = Path(args.archive).resolve()

    for path in (input_xml, output_xml, scene_out, ball_scene_out, report, metadata, visual_dir):
        _backup_existing(path, archive)

    audit = audit_joint_signs(input_xml, perturb=float(args.perturb), tolerance=float(args.tolerance))
    change_log = apply_fixed_ranges(input_xml, output_xml, audit)
    write_scenes(output_xml, scene_out, ball_scene_out)
    visual = render_visual_summary(input_xml, output_xml, audit, visual_dir)

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "export4_flexion_sign_audit_v1",
        "input_xml": input_xml,
        "fixed_xml": output_xml,
        "scene_output": scene_out,
        "ball_scene_output": ball_scene_out,
        "perturb": float(args.perturb),
        "tolerance": float(args.tolerance),
        "audit": audit,
        "change_log": change_log,
        "visual": visual,
        "notes": [
            "CAD/STL/joint tree unchanged.",
            "mcp_flex and thumb CMC joints are audit-only.",
            "Use this fixed MJCF as experimental evidence before repairing SolidWorks/URDF limits.",
        ],
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(report, audit, change_log, output_xml, scene_out, ball_scene_out, visual, metadata)

    planned = [item for item in audit if item.get("planned_change")]
    print(f"Audited {len(audit)} joints")
    print(f"Planned auto-fixes: {len(planned)}")
    for item in planned:
        print(f"  {item['joint']}: {_fmt_range(tuple(item['old_range']))} -> {_fmt_range(tuple(item['new_range']))}")
    print(f"Saved fixed MJCF: {output_xml}")
    print(f"Saved report: {report}")


if __name__ == "__main__":
    main()
