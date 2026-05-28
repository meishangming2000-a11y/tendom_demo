#!/usr/bin/env python3
"""Create an arm + export4 hand assembly from SolidWorks mount CSYS CSVs.

This uses the exported CAD frames:

    arm:  csys_j4 -> arm_flange_mount_csys
    hand: hand_base_csys -> hand_wrist_mount_csys

and computes the fixed MuJoCo transform:

    T_ee_mount_to_hand_base =
        T_csys_j4_to_arm_flange_mount * inv(T_hand_base_to_hand_wrist_mount)

No CAD, STL, hand model, arm model, joint tree, or joint names are modified.
"""

from __future__ import annotations

import csv
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT_ROOT = Path(__file__).resolve().parent
ARCHIVE = OUT_ROOT / "archive"
DOCS = OUT_ROOT / "docs"
META_DIR = OUT_ROOT / "metadata"
EXPORT_DIR = OUT_ROOT / "mount_csys_exports"

ARM_XML = ROOT / "simulations" / "models" / "arm_stage1_export" / "robot.xml"
HAND_XML = ROOT / "simulations" / "models" / "hand_stage1_export" / "mjcf" / "hand_stage1_export4_palmar_ypos_collision_candidate.xml"
OUT_XML = OUT_ROOT / "arm_hand_export4_cad_mount_candidate.xml"
SCENE_XML = OUT_ROOT / "scene_arm_hand_export4_cad_mount_candidate.xml"
REPORT = DOCS / "arm_hand_export4_cad_mount_candidate_report.md"
META = META_DIR / "arm_hand_export4_cad_mount_candidate.json"


def backup(path: Path, tag: str) -> None:
    if not path.exists():
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, ARCHIVE / f"{path.stem}.{tag}.{stamp}{path.suffix}")


def read_csv_rows(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "FOUND" and row.get("name") not in rows:
                rows[row["name"]] = row
    return rows


def find_mount_csvs() -> tuple[Path, dict[str, dict[str, str]], Path, dict[str, dict[str, str]]]:
    arm_path = None
    arm_rows = None
    hand_path = None
    hand_rows = None
    for path in EXPORT_DIR.glob("*_mount_csys_export.csv"):
        rows = read_csv_rows(path)
        if "arm_flange_mount_csys" in rows and "csys_j4" in rows:
            arm_path = path
            arm_rows = rows
        if "hand_wrist_mount_csys" in rows and "hand_base_csys" in rows:
            hand_path = path
            hand_rows = rows
    if arm_path is None or arm_rows is None:
        raise RuntimeError(f"Could not find arm CSV with arm_flange_mount_csys and csys_j4 in {EXPORT_DIR}")
    if hand_path is None or hand_rows is None:
        raise RuntimeError(f"Could not find hand CSV with hand_wrist_mount_csys and hand_base_csys in {EXPORT_DIR}")
    return arm_path, arm_rows, hand_path, hand_rows


def transform_from_row(row: dict[str, str]) -> np.ndarray:
    origin = np.array([float(row[f"origin_{axis}_m"]) for axis in "xyz"], dtype=np.float64)
    x_axis = np.array([float(row[f"x_axis_{axis}"]) for axis in "xyz"], dtype=np.float64)
    y_axis = np.array([float(row[f"y_axis_{axis}"]) for axis in "xyz"], dtype=np.float64)
    z_axis = np.array([float(row[f"z_axis_{axis}"]) for axis in "xyz"], dtype=np.float64)
    rotation = np.column_stack([x_axis, y_axis, z_axis])
    u, _, vt = np.linalg.svd(rotation)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        u[:, -1] *= -1
        rotation = u @ vt
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = origin
    return transform


def quat_from_rotation(rotation: np.ndarray) -> np.ndarray:
    trace = float(np.trace(rotation))
    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (rotation[2, 1] - rotation[1, 2]) / s
        y = (rotation[0, 2] - rotation[2, 0]) / s
        z = (rotation[1, 0] - rotation[0, 1]) / s
    elif rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
        s = np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2]) * 2.0
        w = (rotation[2, 1] - rotation[1, 2]) / s
        x = 0.25 * s
        y = (rotation[0, 1] + rotation[1, 0]) / s
        z = (rotation[0, 2] + rotation[2, 0]) / s
    elif rotation[1, 1] > rotation[2, 2]:
        s = np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2]) * 2.0
        w = (rotation[0, 2] - rotation[2, 0]) / s
        x = (rotation[0, 1] + rotation[1, 0]) / s
        y = 0.25 * s
        z = (rotation[1, 2] + rotation[2, 1]) / s
    else:
        s = np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1]) * 2.0
        w = (rotation[1, 0] - rotation[0, 1]) / s
        x = (rotation[0, 2] + rotation[2, 0]) / s
        y = (rotation[1, 2] + rotation[2, 1]) / s
        z = 0.25 * s
    quat = np.array([w, x, y, z], dtype=np.float64)
    quat /= np.linalg.norm(quat)
    if quat[0] < 0:
        quat *= -1
    return quat


def fmt_vec(values: np.ndarray) -> str:
    return " ".join(f"{float(v):.10g}" for v in values)


def find_body(root: ET.Element, name: str) -> ET.Element | None:
    for body in root.findall(".//body"):
        if body.get("name") == name:
            return body
    return None


def rewrite_mesh_files(root: ET.Element, prefix: str) -> None:
    for mesh in root.findall(".//mesh"):
        file_name = mesh.get("file")
        if file_name:
            mesh.set("file", f"{prefix}/{file_name}")


def add_site(body: ET.Element, name: str, pos: np.ndarray, rgba: str, size: str = "0.006") -> None:
    ET.SubElement(
        body,
        "site",
        {
            "name": name,
            "type": "sphere",
            "pos": fmt_vec(pos),
            "size": size,
            "rgba": rgba,
        },
    )


def add_axis_sites(body: ET.Element, prefix: str, transform: np.ndarray, scale: float) -> None:
    origin = transform[:3, 3]
    rotation = transform[:3, :3]
    add_site(body, f"{prefix}_origin", origin, "1 0.45 0.05 1", "0.006")
    add_site(body, f"{prefix}_x", origin + rotation[:, 0] * scale, "1 0 0 1", "0.004")
    add_site(body, f"{prefix}_y", origin + rotation[:, 1] * scale, "0 1 0 1", "0.004")
    add_site(body, f"{prefix}_z", origin + rotation[:, 2] * scale, "0.05 0.2 1 1", "0.004")


def compute_mount_transform() -> dict[str, Any]:
    arm_path, arm_rows, hand_path, hand_rows = find_mount_csvs()
    t_sw_j4 = transform_from_row(arm_rows["csys_j4"])
    t_sw_flange = transform_from_row(arm_rows["arm_flange_mount_csys"])
    t_j4_flange = np.linalg.inv(t_sw_j4) @ t_sw_flange

    t_sw_hand_base = transform_from_row(hand_rows["hand_base_csys"])
    t_sw_hand_wrist = transform_from_row(hand_rows["hand_wrist_mount_csys"])
    t_hand_base_wrist = np.linalg.inv(t_sw_hand_base) @ t_sw_hand_wrist

    t_j4_hand_base = t_j4_flange @ np.linalg.inv(t_hand_base_wrist)
    check = t_j4_hand_base @ t_hand_base_wrist
    pos = t_j4_hand_base[:3, 3]
    quat = quat_from_rotation(t_j4_hand_base[:3, :3])
    return {
        "arm_csv": str(arm_path),
        "hand_csv": str(hand_path),
        "t_j4_flange": t_j4_flange,
        "t_hand_base_wrist": t_hand_base_wrist,
        "t_j4_hand_base": t_j4_hand_base,
        "hand_base_pos_in_ee_mount": pos,
        "hand_base_quat_in_ee_mount": quat,
        "alignment_translation_error_m": float(np.linalg.norm(check[:3, 3] - t_j4_flange[:3, 3])),
        "alignment_rotation_error_fro": float(np.linalg.norm(check[:3, :3] - t_j4_flange[:3, :3])),
    }


def build_model(mount: dict[str, Any]) -> dict[str, Any]:
    arm_tree = ET.parse(ARM_XML)
    hand_tree = ET.parse(HAND_XML)
    arm_root = arm_tree.getroot()
    hand_root = hand_tree.getroot()

    rewrite_mesh_files(arm_root, "../arm_stage1_export/meshes")
    rewrite_mesh_files(hand_root, "../hand_stage1_export/meshes_export4")

    combined = ET.Element("mujoco", {"model": "arm_hand_export4_cad_mount_candidate"})
    ET.SubElement(combined, "compiler", {"angle": "radian", "autolimits": "true"})
    ET.SubElement(combined, "option", {"timestep": "0.002", "gravity": "0 0 -9.81"})
    visual = ET.SubElement(combined, "visual")
    ET.SubElement(visual, "global", {"azimuth": "205", "elevation": "-22", "offwidth": "1280", "offheight": "900"})

    hand_default = hand_root.find("default")
    if hand_default is not None:
        combined.append(hand_default)

    asset = ET.SubElement(combined, "asset")
    for source_root in (arm_root, hand_root):
        source_asset = source_root.find("asset")
        if source_asset is None:
            continue
        for child in list(source_asset):
            asset.append(child)

    world = ET.SubElement(combined, "worldbody")
    arm_world = arm_root.find("worldbody")
    if arm_world is None:
        raise RuntimeError(f"Arm XML has no worldbody: {ARM_XML}")
    for body in arm_world.findall("body"):
        world.append(body)

    ee_mount = find_body(combined, "ee_mount")
    if ee_mount is None:
        raise RuntimeError("Could not find ee_mount in arm model")

    hand_world = hand_root.find("worldbody")
    if hand_world is None:
        raise RuntimeError(f"Hand XML has no worldbody: {HAND_XML}")
    hand_bodies = list(hand_world.findall("body"))
    if len(hand_bodies) != 1:
        raise RuntimeError(f"Expected one hand root body, got {len(hand_bodies)}")
    hand_root_body = hand_bodies[0]
    hand_root_body.set("pos", fmt_vec(mount["hand_base_pos_in_ee_mount"]))
    hand_root_body.set("quat", fmt_vec(mount["hand_base_quat_in_ee_mount"]))

    add_axis_sites(ee_mount, "cad_arm_flange_mount", mount["t_j4_flange"], 0.018)
    add_axis_sites(hand_root_body, "cad_hand_wrist_mount", mount["t_hand_base_wrist"], 0.014)
    ee_mount.append(hand_root_body)

    actuator = ET.SubElement(combined, "actuator")
    for source_root in (arm_root, hand_root):
        source_actuator = source_root.find("actuator")
        if source_actuator is None:
            continue
        for child in list(source_actuator):
            actuator.append(child)

    backup(OUT_XML, "before_cad_mount_candidate")
    ET.indent(ET.ElementTree(combined), space="  ")
    ET.ElementTree(combined).write(OUT_XML, encoding="utf-8", xml_declaration=True)

    scene = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"arm_hand_export4_cad_mount_scene\">
  <include file=\"{OUT_XML.name}\"/>
  <statistic extent=\"0.9\" center=\"0 0 0.12\"/>
  <visual>
    <rgba haze=\"0.15 0.25 0.35 1\"/>
    <quality shadowsize=\"8192\"/>
    <global azimuth=\"205\" elevation=\"-22\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"skybox\" builtin=\"gradient\" rgb1=\"0.30 0.50 0.70\" rgb2=\"0.00 0.00 0.00\" width=\"512\" height=\"3072\"/>
    <texture type=\"2d\" name=\"ground_checker\" builtin=\"checker\" mark=\"edge\" rgb1=\"0.20 0.30 0.40\" rgb2=\"0.10 0.20 0.30\" markrgb=\"0.80 0.80 0.80\" width=\"300\" height=\"300\"/>
    <material name=\"ground\" texture=\"ground_checker\" texrepeat=\"5 5\" texuniform=\"true\" reflectance=\"0.20\"/>
  </asset>
  <worldbody>
    <light name=\"fill_light\" pos=\"0 0 1\"/>
    <light name=\"key_light\" pos=\"0.3 0 1.5\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"floor\" type=\"plane\" pos=\"0 0 -0.12\" size=\"0 0 0.05\" material=\"ground\" contype=\"0\" conaffinity=\"4\"/>
    <camera name=\"overview\" pos=\"-0.62 -0.72 0.42\" xyaxes=\"0.757769 -0.652523 0 0.147191 0.170932 0.974226\" fovy=\"45\"/>
  </worldbody>
</mujoco>
"""
    backup(SCENE_XML, "before_cad_mount_scene")
    SCENE_XML.write_text(scene, encoding="utf-8")
    return {
        "combined_xml": str(OUT_XML),
        "scene_xml": str(SCENE_XML),
        "attachment_parent": "ee_mount",
        "attached_body": "hand_base_link",
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    return value


def write_reports(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    backup(META, "before_cad_mount_meta")
    META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    mount = payload["mount"]
    lines = [
        "# Arm + Export4 CAD Mount Candidate\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Experimental MuJoCo assembly only. CAD, STL, joint tree, and joint names were not modified.\n\n",
        "## CSV Inputs\n\n",
        f"- Arm CSV: `{mount['arm_csv']}`\n",
        f"- Hand CSV: `{mount['hand_csv']}`\n\n",
        "## Formula\n\n",
        "`T_ee_mount_to_hand_base = T_csys_j4_to_arm_flange_mount * inverse(T_hand_base_to_hand_wrist_mount)`\n\n",
        "## Resulting Fixed Transform\n\n",
        f"- Parent body: `{payload['build']['attachment_parent']}`\n",
        f"- Child body: `{payload['build']['attached_body']}`\n",
        f"- hand_base pos in ee_mount: `{json_ready(mount['hand_base_pos_in_ee_mount'])}`\n",
        f"- hand_base quat in ee_mount: `{json_ready(mount['hand_base_quat_in_ee_mount'])}`\n",
        f"- alignment translation error: `{mount['alignment_translation_error_m']:.12g} m`\n",
        f"- alignment rotation Frobenius error: `{mount['alignment_rotation_error_fro']:.12g}`\n\n",
        "## Outputs\n\n",
        f"- MJCF: `{payload['build']['combined_xml']}`\n",
        f"- Scene: `{payload['build']['scene_xml']}`\n\n",
        "## Notes\n\n",
        "- The hand is attached directly under `ee_mount`, not under the earlier manually inserted `ee_tool_frame`.\n",
        "- Debug sites were added for the arm flange mount frame and hand wrist mount frame. If alignment is correct, their origins and axes overlap in the rendered model.\n",
        "- This assumes SolidWorks exported `csys_j4` corresponds to the MuJoCo `ee_mount` body frame and `hand_base_csys` corresponds to the MuJoCo `hand_base_link` body frame.\n",
    ]
    backup(REPORT, "before_cad_mount_report")
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    mount = compute_mount_transform()
    build = build_model(mount)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "arm_source": str(ARM_XML),
        "hand_source": str(HAND_XML),
        "mount": mount,
        "build": build,
    }
    write_reports(payload)
    print(f"Saved MJCF: {build['combined_xml']}")
    print(f"Saved scene: {build['scene_xml']}")
    print(f"Saved report: {REPORT}")
    print(f"hand_base pos in ee_mount: {mount['hand_base_pos_in_ee_mount']}")
    print(f"hand_base quat in ee_mount: {mount['hand_base_quat_in_ee_mount']}")


if __name__ == "__main__":
    main()
