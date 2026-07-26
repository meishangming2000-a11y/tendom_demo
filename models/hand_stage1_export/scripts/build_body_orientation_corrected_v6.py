#!/usr/bin/env python3
"""Apply the v6 whole-arm mount correction selected from the v5 candidates.

The user identified `world_z_-90_side.png` as the correct candidate. V5 used
`world_z_+90`, so the whole arm was mounted backwards. V6 keeps the v5 body
lift/support-column changes but rotates the whole arm chain at `base_link`
with -90 deg about world Z, equivalent to a 180 deg correction from v5 around
the body/arm contact point.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

import build_body_orientation_corrected_v5 as v5


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v3.xml"
OUT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v6.xml"
DOCS = ROOT / "docs"
VIS = DOCS / "visual_checks_body_connection_corrected_v6"
CANDIDATE_DIR = VIS / "candidates"
REPORT = DOCS / "body_connection_orientation_corrected_v6_report.md"
META = ROOT / "metadata" / "body_connection_orientation_corrected_v6.json"

BODY_ROOT_NAME = "rough_body_support_link"
ARM_ROOT_NAME = "base_link"
SUPPORT_COLUMN_NAME = "body_support_column_visual_v6"
ARM_WORLD_YAW_DEG = -90.0
REJECTED_V5_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_corrected_v5.xml"
REFERENCE_CANDIDATE = (
    ROOT
    / "docs"
    / "visual_checks_body_connection_corrected_v5"
    / "candidates"
    / "world_z_-90_side.png"
)


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def configure_v5_module() -> None:
    v5.SOURCE_SCENE = SOURCE_SCENE
    v5.OUT_SCENE = OUT_SCENE
    v5.VIS = VIS
    v5.CANDIDATE_DIR = CANDIDATE_DIR
    v5.REPORT = REPORT
    v5.META = META
    v5.SUPPORT_COLUMN_NAME = SUPPORT_COLUMN_NAME
    v5.ARM_WORLD_YAW_DEG = ARM_WORLD_YAW_DEG


def write_scene() -> dict[str, Any]:
    configure_v5_module()
    tree = ET.parse(SOURCE_SCENE)
    delta = v5.apply_v5_delta(tree)
    tree.getroot().set("model", "export4_connected_to_body_corrected_v6")
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    OUT_SCENE.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUT_SCENE, encoding="utf-8", xml_declaration=True)
    return delta


def inspect_scene() -> dict[str, Any]:
    configure_v5_module()
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    metrics = v5.pose_metrics(model, data)
    pts = list(metrics["positions"].values())
    center = np.mean(np.asarray(pts), axis=0)
    base = metrics["positions"].get(ARM_ROOT_NAME, center)
    palm = metrics["positions"].get("palm_link", center)
    arm_center = 0.5 * (base + palm)
    shots = {
        "front": v5.render(model, data, CANDIDATE_DIR / "selected_v6_front.png", center, distance=1.18, azimuth=205, elevation=-20),
        "side": v5.render(model, data, CANDIDATE_DIR / "selected_v6_side.png", center, distance=1.18, azimuth=110, elevation=-16),
        "mount": v5.render(model, data, CANDIDATE_DIR / "selected_v6_mount.png", arm_center, distance=0.72, azimuth=205, elevation=-14),
    }
    return {
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
        },
        "finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "metrics": metrics,
        "screenshots": shots,
        "blank_flags": {name: (shot["max_pixel"] - shot["min_pixel"] < 5) for name, shot in shots.items()},
    }


def motion_check() -> dict[str, Any]:
    configure_v5_module()
    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    start_body = v5.body_pos(model, data, BODY_ROOT_NAME)
    start_base = v5.body_pos(model, data, ARM_ROOT_NAME)
    for _ in range(60):
        mujoco.mj_step(model, data)
    after_body = v5.body_pos(model, data, BODY_ROOT_NAME)
    after_base = v5.body_pos(model, data, ARM_ROOT_NAME)
    return {
        "finite_after_step": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "body_drift_m": float(np.linalg.norm(after_body - start_body)) if start_body is not None and after_body is not None else None,
        "base_link_drift_m": float(np.linalg.norm(after_base - start_base)) if start_base is not None and after_base is not None else None,
    }


def build_payload() -> dict[str, Any]:
    delta = write_scene()
    inspection = inspect_scene()
    motion = motion_check()
    load_gate = inspection["finite"] and motion["finite_after_step"] and not any(inspection["blank_flags"].values())
    return {
        "generated_at": now(),
        "source_scene": SOURCE_SCENE,
        "output_scene": OUT_SCENE,
        "status": "v6_world_z_minus90_whole_arm_alignment_selected_needs_user_confirmation",
        "supersedes": {
            "scene": REJECTED_V5_SCENE,
            "reason": "v5 used world_z_+90 and mounted the arm backwards; user selected the v5 `world_z_-90_side.png` candidate.",
        },
        "reference_candidate_image": REFERENCE_CANDIDATE,
        "load_finite_render_gate": "PASS" if load_gate else "FAIL",
        "v6_delta": delta,
        "inspection": inspection,
        "motion_check": motion,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(v5.json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    delta = payload["v6_delta"]
    metrics = payload["inspection"]["metrics"]
    lines = [
        "# Body Connection Orientation Corrected V6 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Source scene: `{payload['source_scene']}`\n",
        f"- Corrected scene: `{payload['output_scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Supersedes v5 reason: `{payload['supersedes']['reason']}`\n",
        f"- Reference accepted candidate: `{payload['reference_candidate_image']}`\n",
        f"- Load/finite/render gate: `{payload['load_finite_render_gate']}`\n",
        f"- Body root z lift: `{delta['body_root_z_lift_m']:.3f} m`\n",
        f"- Whole-arm yaw: `{delta['arm_world_yaw_deg']:.1f} deg about {delta['arm_world_yaw_axis']}`\n",
        f"- New arm quat wxyz: `{v5.fmt_vec(delta['new_arm_quat_wxyz'])}`\n",
        f"- Hand local twist applied: `{delta['hand_local_twist_applied']}`\n",
        f"- Support column: `{delta['support_column']['name']}` contact-disabled visual cylinder\n\n",
        "## Selected Metrics\n\n",
        f"- floor_z_m: `{metrics['floor_z_m']}`\n",
        f"- support_column_z_bounds_m: `{metrics['support_column_z_bounds_m']}`\n",
        f"- base_to_palm: `{v5.fmt_vec(metrics['base_to_palm'])}`\n",
        f"- base_to_palm_horizontal_ratio: `{metrics['base_to_palm_horizontal_ratio']:.6f}`\n",
        f"- base_to_palm_z_delta_m: `{metrics['base_to_palm_z_delta_m']:.6f}`\n\n",
        "## Final Screenshots\n\n",
    ]
    for name, shot in payload["inspection"]["screenshots"].items():
        lines.append(f"- `{name}`: `{shot['file']}`\n")
    lines.extend(
        [
            "\n## Motion Smoke\n\n",
            f"- finite_after_step: `{payload['motion_check']['finite_after_step']}`\n",
            f"- body_drift_m: `{payload['motion_check']['body_drift_m']}`\n",
            f"- base_link_drift_m: `{payload['motion_check']['base_link_drift_m']}`\n\n",
            "## Notes\n\n",
            "- V6 rotates the entire arm chain at `base_link`; it does not rotate the palm or hand independently.\n",
            "- Compared with rejected v5, v6 changes only the whole-arm world-Z yaw direction: +90 deg -> -90 deg.\n",
            "- The support column is a contact-disabled placeholder until the CAD column/pillar part is exported into the runtime asset.\n",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_payload()
    write_outputs(payload)
    print(f"Saved scene: {OUT_SCENE}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META}")
    print(f"Gate: {payload['load_finite_render_gate']}")


if __name__ == "__main__":
    main()
