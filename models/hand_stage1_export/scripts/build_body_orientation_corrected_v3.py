#!/usr/bin/env python3
"""Build and inspect v3 body/arm orientation candidates.

This is still a frame-correction experiment branch. It keeps the imported CAD,
URDF, and previous MJCF scenes unchanged, then writes a selected v3 scene plus
candidate renders for visual review.
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - labels are convenience only.
    Image = ImageDraw = ImageFont = None


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_proxy.xml"
OUT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v3.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_corrected_v3"
CANDIDATE_DIR = VIS / "candidates"
REPORT = DOCS / "body_connection_orientation_corrected_v3_report.md"
META = ROOT / "metadata" / "body_connection_orientation_corrected_v3.json"

BODY_VISUAL_NAME = "rough_body_support_link_visual"
BODY_PROXY_NAME = "rough_body_support_collision_proxy_bbox_disabled"
ARM_ROOT_NAME = "base_link"
PREFERRED_SELECTED_CANDIDATE_ID = "rz180_then_ry_pos90"

# MuJoCo quaternions are w x y z. v2 used +90 deg about X and the user
# rejected it as upside down. v3 flips the body to the opposite vertical sense.
BODY_UPRIGHT_QUAT = np.array([math.sqrt(0.5), -math.sqrt(0.5), 0.0, 0.0], dtype=np.float64)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    quat: np.ndarray
    note: str


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def fmt_vec(values: np.ndarray | list[float]) -> str:
    return " ".join(f"{float(v):.10g}" for v in values)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def axis_angle(axis: tuple[float, float, float], angle_deg: float) -> np.ndarray:
    axis_v = np.asarray(axis, dtype=np.float64)
    axis_v = axis_v / np.linalg.norm(axis_v)
    half = math.radians(angle_deg) * 0.5
    return np.array([math.cos(half), *(math.sin(half) * axis_v)], dtype=np.float64)


def quat_mul(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return np.array(
        [
            lw * rw - lx * rx - ly * ry - lz * rz,
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
        ],
        dtype=np.float64,
    )


def quat_rotate(quat: np.ndarray, vec: np.ndarray) -> np.ndarray:
    w, x, y, z = quat
    qv = np.array([x, y, z], dtype=np.float64)
    return vec + 2.0 * np.cross(qv, np.cross(qv, vec) + w * vec)


def candidates() -> list[Candidate]:
    rx90 = axis_angle((1, 0, 0), 90)
    rxn90 = axis_angle((1, 0, 0), -90)
    ry90 = axis_angle((0, 1, 0), 90)
    ryn90 = axis_angle((0, 1, 0), -90)
    rz90 = axis_angle((0, 0, 1), 90)
    rzn90 = axis_angle((0, 0, 1), -90)
    rz180 = axis_angle((0, 0, 1), 180)
    return [
        Candidate("identity_reference", np.array([1.0, 0.0, 0.0, 0.0]), "No arm-root correction."),
        Candidate("rz180_v2_reference", rz180, "The v2 arm flip that stayed too vertical."),
        Candidate("rx_pos90", rx90, "Pitch arm root +90 deg about body/mount X."),
        Candidate("rx_neg90", rxn90, "Pitch arm root -90 deg about body/mount X."),
        Candidate("ry_pos90", ry90, "Pitch arm root +90 deg about body/mount Y."),
        Candidate("ry_neg90", ryn90, "Pitch arm root -90 deg about body/mount Y."),
        Candidate("rz_pos90", rz90, "Clock arm root +90 deg about body/mount Z."),
        Candidate("rz_neg90", rzn90, "Clock arm root -90 deg about body/mount Z."),
        Candidate("rz180_then_rx_pos90", quat_mul(rx90, rz180), "Keep v2 180 flip, then pitch +90 about X."),
        Candidate("rz180_then_rx_neg90", quat_mul(rxn90, rz180), "Keep v2 180 flip, then pitch -90 about X."),
        Candidate("rz180_then_ry_pos90", quat_mul(ry90, rz180), "Keep v2 180 flip, then pitch +90 about Y."),
        Candidate("rz180_then_ry_neg90", quat_mul(ryn90, rz180), "Keep v2 180 flip, then pitch -90 about Y."),
        Candidate("rx_pos90_then_rz180", quat_mul(rz180, rx90), "Pitch +90 about X, then apply v2 180 flip."),
        Candidate("rx_neg90_then_rz180", quat_mul(rz180, rxn90), "Pitch -90 about X, then apply v2 180 flip."),
        Candidate("ry_pos90_then_rz180", quat_mul(rz180, ry90), "Pitch +90 about Y, then apply v2 180 flip."),
        Candidate("ry_neg90_then_rz180", quat_mul(rz180, ryn90), "Pitch -90 about Y, then apply v2 180 flip."),
    ]


def find_required(root: ET.Element, path: str, *, label: str) -> ET.Element:
    item = root.find(path)
    if item is None:
        raise RuntimeError(f"Missing {label}: {path}")
    return item


def apply_correction(tree: ET.ElementTree, arm_quat: np.ndarray, model_name: str) -> dict[str, Any]:
    root = tree.getroot()
    root.set("model", model_name)

    body_visual = find_required(root, f".//geom[@name='{BODY_VISUAL_NAME}']", label=BODY_VISUAL_NAME)
    body_visual.set("quat", fmt_vec(BODY_UPRIGHT_QUAT))

    body_proxy = root.find(f".//geom[@name='{BODY_PROXY_NAME}']")
    original_proxy_pos = None
    corrected_proxy_pos = None
    if body_proxy is not None:
        original_proxy_pos = np.fromstring(body_proxy.get("pos", "0 0 0"), sep=" ")
        corrected_proxy_pos = quat_rotate(BODY_UPRIGHT_QUAT, original_proxy_pos)
        body_proxy.set("pos", fmt_vec(corrected_proxy_pos))
        body_proxy.set("quat", fmt_vec(BODY_UPRIGHT_QUAT))

    arm_root = find_required(root, f".//body[@name='{ARM_ROOT_NAME}']", label=ARM_ROOT_NAME)
    arm_root.set("quat", fmt_vec(arm_quat))
    return {"original_proxy_pos": original_proxy_pos, "corrected_proxy_pos": corrected_proxy_pos}


def write_scene(path: Path, arm_quat: np.ndarray, model_name: str) -> dict[str, Any]:
    tree = ET.parse(SOURCE_SCENE)
    payload = apply_correction(tree, arm_quat, model_name)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return payload


def body_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray | None:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def render(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    output: Path,
    lookat: np.ndarray,
    *,
    distance: float,
    azimuth: float,
    elevation: float,
    width: int = 960,
    height: int = 680,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=width, height=height)
    try:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = distance
        cam.azimuth = azimuth
        cam.elevation = elevation
        renderer.update_scene(data, camera=cam)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "mean_pixel": float(image.mean()),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
    }


def pose_metrics(model: mujoco.MjModel, data: mujoco.MjData) -> dict[str, Any]:
    names = ["rough_body_support_link", "base_link", "link_1", "link_2", "link_3", "ee_mount", "hand_base_link", "palm_link"]
    positions = {name: body_pos(model, data, name) for name in names}
    base = positions["base_link"]
    palm = positions["palm_link"]
    ee = positions["ee_mount"]
    link2 = positions["link_2"]
    arm_vec = palm - base if base is not None and palm is not None else np.zeros(3)
    ee_vec = ee - base if base is not None and ee is not None else np.zeros(3)
    link2_vec = link2 - base if base is not None and link2 is not None else np.zeros(3)

    def horizontal_ratio(vec: np.ndarray) -> float:
        norm = float(np.linalg.norm(vec))
        if norm <= 1e-12:
            return 0.0
        return float(np.linalg.norm(vec[:2]) / norm)

    def z_delta(vec: np.ndarray) -> float:
        return float(vec[2])

    return {
        "positions": {name: pos for name, pos in positions.items() if pos is not None},
        "base_to_palm": arm_vec,
        "base_to_ee_mount": ee_vec,
        "base_to_link2": link2_vec,
        "base_to_palm_horizontal_ratio": horizontal_ratio(arm_vec),
        "base_to_ee_horizontal_ratio": horizontal_ratio(ee_vec),
        "base_to_link2_horizontal_ratio": horizontal_ratio(link2_vec),
        "base_to_palm_z_delta_m": z_delta(arm_vec),
        "base_to_ee_z_delta_m": z_delta(ee_vec),
        "base_to_link2_z_delta_m": z_delta(link2_vec),
    }


def candidate_score(metrics: dict[str, Any]) -> float:
    # Prefer a horizontally extending chain. Penalize a palm far above/below the
    # root because the user explicitly rejected the vertical default posture.
    palm_ratio = float(metrics["base_to_palm_horizontal_ratio"])
    ee_ratio = float(metrics["base_to_ee_horizontal_ratio"])
    palm_z = abs(float(metrics["base_to_palm_z_delta_m"]))
    ee_z = abs(float(metrics["base_to_ee_z_delta_m"]))
    return 0.65 * palm_ratio + 0.35 * ee_ratio - 0.8 * palm_z - 0.5 * ee_z


def inspect_scene(scene_path: Path, candidate_id: str) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene_path.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    metrics = pose_metrics(model, data)

    pts = list(metrics["positions"].values())
    full_center = np.mean(np.asarray(pts), axis=0)
    base = metrics["positions"].get("base_link", full_center)
    palm = metrics["positions"].get("palm_link", full_center)
    arm_center = 0.5 * (base + palm)
    shots = {
        "front": render(
            model,
            data,
            CANDIDATE_DIR / f"{candidate_id}_front.png",
            full_center,
            distance=1.10,
            azimuth=205,
            elevation=-20,
        ),
        "side": render(
            model,
            data,
            CANDIDATE_DIR / f"{candidate_id}_side.png",
            full_center,
            distance=1.10,
            azimuth=110,
            elevation=-16,
        ),
        "mount": render(
            model,
            data,
            CANDIDATE_DIR / f"{candidate_id}_mount.png",
            arm_center,
            distance=0.52,
            azimuth=205,
            elevation=-14,
        ),
    }
    return {
        "candidate_id": candidate_id,
        "scene": str(scene_path),
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
        },
        "finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "metrics": metrics,
        "score": candidate_score(metrics),
        "screenshots": shots,
        "blank_flags": {name: (shot["max_pixel"] - shot["min_pixel"] < 5) for name, shot in shots.items()},
    }


def make_contact_sheet(records: list[dict[str, Any]], view_name: str, output: Path) -> str | None:
    if Image is None:
        return None
    images = []
    thumb_w, thumb_h = 360, 255
    label_h = 70
    for idx, record in enumerate(records):
        image_path = record["screenshots"][view_name]["file"]
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (thumb_w, thumb_h + label_h), (245, 245, 245))
        tile.paste(img, ((thumb_w - img.width) // 2, 0))
        draw = ImageDraw.Draw(tile)
        font = ImageFont.load_default()
        metrics = record["metrics"]
        label = (
            f"{idx:02d} {record['candidate_id']}\n"
            f"score={record['score']:.3f} palm_hr={metrics['base_to_palm_horizontal_ratio']:.3f}\n"
            f"palm_dz={metrics['base_to_palm_z_delta_m']:.3f} ee_dz={metrics['base_to_ee_z_delta_m']:.3f}"
        )
        draw.multiline_text((8, thumb_h + 4), label, fill=(20, 20, 20), font=font, spacing=3)
        images.append(tile)

    cols = 4
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (230, 230, 230))
    for idx, tile in enumerate(images):
        row, col = divmod(idx, cols)
        sheet.paste(tile, (col * thumb_w, row * (thumb_h + label_h)))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return str(output)


def actuator_for_joint(model: mujoco.MjModel, joint_name: str) -> int:
    for aid in range(model.nu):
        if model.actuator_trntype[aid] != mujoco.mjtTrn.mjTRN_JOINT:
            continue
        jid = int(model.actuator_trnid[aid, 0])
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        if name == joint_name:
            return aid
    return -1


def final_motion_check(scene_path: Path, selected_id: str) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene_path.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    metrics = pose_metrics(model, data)

    body = metrics["positions"].get("rough_body_support_link")
    base = metrics["positions"].get("base_link")
    palm = metrics["positions"].get("palm_link")
    start_body = body.copy() if body is not None else None
    start_base = base.copy() if base is not None else None
    start_palm = palm.copy() if palm is not None else None

    for joint_name, target in [("j1", 0.05), ("j2", -0.05), ("wrist_1_joint", 0.10), ("index_pip_joint", -0.25)]:
        aid = actuator_for_joint(model, joint_name)
        if aid >= 0:
            data.ctrl[aid] = target
    for _ in range(120):
        mujoco.mj_step(model, data)

    after_body = body_pos(model, data, "rough_body_support_link")
    after_base = body_pos(model, data, "base_link")
    after_palm = body_pos(model, data, "palm_link")

    return {
        "selected_id": selected_id,
        "finite_after_step": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "body_drift_m": float(np.linalg.norm(after_body - start_body)) if start_body is not None and after_body is not None else None,
        "base_link_drift_m": float(np.linalg.norm(after_base - start_base)) if start_base is not None and after_base is not None else None,
        "palm_motion_m": float(np.linalg.norm(after_palm - start_palm)) if start_palm is not None and after_palm is not None else None,
    }


def build_all() -> dict[str, Any]:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    tmp_paths: list[Path] = []
    try:
        for item in candidates():
            # Keep temporary XML files beside the source MJCF so relative mesh
            # paths such as ../../arm_stage1_export/... resolve identically.
            scene_path = ROOT / "mjcf" / f"_tmp_body_orientation_v3_{item.candidate_id}.xml"
            tmp_paths.append(scene_path)
            write_scene(scene_path, item.quat, f"export4_body_v3_candidate_{item.candidate_id}")
            record = inspect_scene(scene_path, item.candidate_id)
            record["quat_wxyz"] = item.quat
            record["note"] = item.note
            records.append(record)
    finally:
        for path in tmp_paths:
            if path.exists():
                path.unlink()

    records.sort(key=lambda record: record["score"], reverse=True)
    preferred = next((record for record in records if record["candidate_id"] == PREFERRED_SELECTED_CANDIDATE_ID), None)
    if preferred is not None and preferred["score"] >= records[0]["score"] - 0.01:
        selected = preferred
        selection_rule = (
            "manual tie-break: preserve the user-requested 180 deg body-arm mount flip, "
            "then apply a 90 deg Y pitch so the arm default is horizontal."
        )
    else:
        selected = records[0]
        selection_rule = "highest horizontal arm-chain score; user still needs to visually confirm mount side."
    selected_candidate = next(item for item in candidates() if item.candidate_id == selected["candidate_id"])
    final_extra = write_scene(OUT_SCENE, selected_candidate.quat, "export4_connected_to_body_corrected_v3")
    final_record = inspect_scene(OUT_SCENE, "selected_v3")
    motion = final_motion_check(OUT_SCENE, selected["candidate_id"])

    sheets = {
        "front": make_contact_sheet(records, "front", VIS / "v3_candidate_front_contact_sheet.png"),
        "side": make_contact_sheet(records, "side", VIS / "v3_candidate_side_contact_sheet.png"),
        "mount": make_contact_sheet(records, "mount", VIS / "v3_candidate_mount_contact_sheet.png"),
    }

    payload = {
        "generated_at": now(),
        "source_scene": SOURCE_SCENE,
        "output_scene": OUT_SCENE,
        "body_visual_name": BODY_VISUAL_NAME,
        "body_orientation_correction": {
            "axis": "X",
            "angle_deg": -90,
            "quat_wxyz": BODY_UPRIGHT_QUAT,
            "reason": "v2 +90 deg stood the body up but was visually upside down; v3 flips the vertical sense.",
        },
        "arm_root_name": ARM_ROOT_NAME,
        "selected_arm_candidate": {
            "candidate_id": selected["candidate_id"],
            "quat_wxyz": selected_candidate.quat,
            "note": selected_candidate.note,
            "selection_rule": selection_rule,
            "score": selected["score"],
            "metrics": selected["metrics"],
        },
        "body_proxy_adjustment": {
            "proxy_name": BODY_PROXY_NAME,
            "original_pos": final_extra.get("original_proxy_pos") if final_extra else None,
            "corrected_pos": final_extra.get("corrected_proxy_pos") if final_extra else None,
            "contact_enabled": False,
        },
        "candidate_records": records,
        "final_record": final_record,
        "motion_check": motion,
        "contact_sheets": sheets,
        "status": "needs_user_visual_confirmation",
    }
    return payload


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    load_gate = (
        payload["final_record"]["finite"]
        and payload["motion_check"]["finite_after_step"]
        and not any(payload["final_record"]["blank_flags"].values())
    )
    selected = payload["selected_arm_candidate"]
    lines = [
        "# Body Connection Orientation Corrected V3 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Corrected scene: `{payload['output_scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Load/finite/render gate: `{'PASS' if load_gate else 'FAIL'}`\n",
        f"- Selected arm candidate: `{selected['candidate_id']}`\n",
        f"- Selected arm quat wxyz: `{fmt_vec(selected['quat_wxyz'])}`\n",
        f"- Selected arm score: `{selected['score']:.6f}`\n",
        f"- Body visual `{BODY_VISUAL_NAME}`: -90 deg about X, quat `{fmt_vec(BODY_UPRIGHT_QUAT)}`.\n",
        "- Body collision proxy remains contact-disabled; this is visual/load/motion only.\n\n",
        "## Candidate Contact Sheets\n\n",
    ]
    for view_name, path in payload["contact_sheets"].items():
        if path:
            lines.append(f"- `{view_name}`: `{path}`\n")
    lines.extend(
        [
            "\n## Selected Metrics\n\n",
            f"- base_to_palm_horizontal_ratio: `{selected['metrics']['base_to_palm_horizontal_ratio']:.6f}`\n",
            f"- base_to_palm_z_delta_m: `{selected['metrics']['base_to_palm_z_delta_m']:.6f}`\n",
            f"- base_to_ee_horizontal_ratio: `{selected['metrics']['base_to_ee_horizontal_ratio']:.6f}`\n",
            f"- base_to_ee_z_delta_m: `{selected['metrics']['base_to_ee_z_delta_m']:.6f}`\n\n",
            "## Final Screenshots\n\n",
        ]
    )
    for name, shot in payload["final_record"]["screenshots"].items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Motion Smoke\n\n",
            f"- finite_after_step: `{payload['motion_check']['finite_after_step']}`\n",
            f"- body_drift_m: `{payload['motion_check']['body_drift_m']}`\n",
            f"- base_link_drift_m: `{payload['motion_check']['base_link_drift_m']}`\n",
            f"- palm_motion_m: `{payload['motion_check']['palm_motion_m']}`\n\n",
            "## Interpretation\n\n",
            "- V3 encodes the user's latest feedback: the body should not be upside down and the arm default should be horizontal/parallel to the ground.\n",
            "- Candidate selection is based on a horizontal-chain metric, not mechanical truth. The selected frame still needs user/CAD confirmation before it becomes the upstream SolidWorks mount coordinate system.\n",
            "- If v3 is visually accepted, mirror these corrections into the body-arm mount frame and then regenerate the URDF/MJCF instead of piling more frame patches into runtime files.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_all()
    write_outputs(payload)
    print(f"Saved scene: {OUT_SCENE}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    print(f"Selected candidate: {payload['selected_arm_candidate']['candidate_id']}")
    for view_name, path in payload["contact_sheets"].items():
        if path:
            print(f"{view_name} contact sheet: {path}")


if __name__ == "__main__":
    main()
