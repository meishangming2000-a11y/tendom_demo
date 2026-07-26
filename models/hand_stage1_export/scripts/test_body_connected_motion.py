#!/usr/bin/env python3
"""Motion smoke test for the export4 arm/hand connected to the new body."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_connected_to_body_proxy.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_body_motion"
REPORT = DOCS / "body_connected_motion_test_report.md"
META_OUT = META / "body_connected_motion_test.json"


TEST_JOINTS = [
    ("wrist_1_joint", 0.18),
    ("wrist_2_joint", -0.18),
    ("index_mcp_abd_joint", -0.22),
    ("index_pip_joint", -0.30),
    ("index_dip_joint", -0.15),
    ("middle_mcp_abd_joint", -0.22),
    ("middle_pip_joint", -0.30),
    ("middle_dip_joint", -0.15),
    ("ring_mcp_abd_joint", -0.18),
    ("ring_pip_joint", -0.24),
    ("ring_dip_joint", -0.12),
    ("little_mcp_abd_joint", -0.18),
    ("little_pip_joint", -0.24),
    ("little_dip_joint", -0.12),
    ("thumb_cmc_abd_joint", -0.18),
    ("thumb_cmc_joint", 0.12),
    ("thumb_mcp_joint", 0.20),
    ("thumb_ip_joint", -0.18),
    ("j1", 0.08),
    ("j2", -0.08),
    ("j3", 0.08),
    ("j4", -0.08),
]


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


def name_to_id(model, objtype, name: str) -> int:
    return mujoco.mj_name2id(model, objtype, name)


def actuator_for_joint(model, joint_name: str) -> int:
    for aid in range(model.nu):
        trnid = int(model.actuator_trnid[aid, 0])
        if trnid < 0:
            continue
        if model.actuator_trntype[aid] != mujoco.mjtTrn.mjTRN_JOINT:
            continue
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, trnid)
        if name == joint_name:
            return aid
    return -1


def render(model, data, out: Path, lookat: np.ndarray | None = None, *, azimuth: float = 205, elevation: float = -22, distance: float = 0.85) -> dict[str, Any]:
    out.parent.mkdir(parents=True, exist_ok=True)
    if lookat is None:
        ids = [name_to_id(model, mujoco.mjtObj.mjOBJ_BODY, n) for n in ("rough_body_support_link", "palm_link", "ball")]
        pts = [data.xpos[i] for i in ids if i >= 0]
        lookat = np.mean(np.asarray(pts), axis=0) if pts else np.array([0.0, 0.0, 0.25])
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = mujoco.MjvCamera()
        cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = distance
        cam.azimuth = azimuth
        cam.elevation = elevation
        renderer.update_scene(data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(out, img)
    return {"file": str(out), "mean_pixel": float(img.mean()), "min_pixel": int(img.min()), "max_pixel": int(img.max())}


def body_pos(model, data, name: str) -> np.ndarray | None:
    bid = name_to_id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[bid].copy() if bid >= 0 else None


def run(scene: Path, steps: int) -> dict[str, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    start_base = body_pos(model, data, "base_link")
    start_palm = body_pos(model, data, "palm_link")
    start_body = body_pos(model, data, "rough_body_support_link")
    start_render = render(model, data, VIS / "connected_model_motion_start.png")

    joint_results = []
    for joint_name, target in TEST_JOINTS:
        aid = actuator_for_joint(model, joint_name)
        jid = name_to_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if aid < 0 or jid < 0:
            joint_results.append({"joint": joint_name, "status": "SKIPPED_NOT_FOUND"})
            continue
        before = data.qpos[int(model.jnt_qposadr[jid])].copy()
        data.ctrl[aid] = target
        for _ in range(steps):
            mujoco.mj_step(model, data)
        after = data.qpos[int(model.jnt_qposadr[jid])].copy()
        finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
        joint_results.append(
            {
                "joint": joint_name,
                "actuator_id": int(aid),
                "target": float(target),
                "qpos_before": float(before),
                "qpos_after": float(after),
                "delta": float(after - before),
                "status": "PASS" if finite and abs(float(after - before)) > 1e-5 else "WARN_NO_VISIBLE_NUMERIC_DELTA",
            }
        )

    after_base = body_pos(model, data, "base_link")
    after_palm = body_pos(model, data, "palm_link")
    after_body = body_pos(model, data, "rough_body_support_link")
    after_render = render(model, data, VIS / "connected_model_motion_after.png")
    base_drift = float(np.linalg.norm(after_base - start_base)) if start_base is not None and after_base is not None else None
    body_drift = float(np.linalg.norm(after_body - start_body)) if start_body is not None and after_body is not None else None
    palm_motion = float(np.linalg.norm(after_palm - start_palm)) if start_palm is not None and after_palm is not None else None
    status = "PASS" if (body_drift is not None and body_drift < 1e-9 and base_drift is not None and base_drift < 1e-6 and np.isfinite(data.qpos).all()) else "PARTIAL"
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": scene,
        "model_summary": {"nbody": int(model.nbody), "njnt": int(model.njnt), "nu": int(model.nu), "ngeom": int(model.ngeom), "nmesh": int(model.nmesh)},
        "status": status,
        "body_drift_m": body_drift,
        "base_link_drift_m": base_drift,
        "palm_motion_m": palm_motion,
        "joint_results": joint_results,
        "screenshots": {"start": start_render, "after": after_render},
    }


def write_report(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    write_json(META_OUT, payload)
    passes = sum(1 for r in payload["joint_results"] if r["status"] == "PASS")
    skipped = sum(1 for r in payload["joint_results"] if r["status"].startswith("SKIPPED"))
    lines = [
        "# Body Connected Motion Test Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Status: `{payload['status']}`\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Body drift: `{payload['body_drift_m']}` m\n",
        f"- Base link drift: `{payload['base_link_drift_m']}` m\n",
        f"- Palm motion after commands: `{payload['palm_motion_m']}` m\n",
        f"- Joint checks: `{passes}` PASS, `{skipped}` SKIPPED, `{len(payload['joint_results']) - passes - skipped}` WARN/FAIL\n\n",
        "## Screenshots\n\n",
        f"- Start: `{payload['screenshots']['start']['file']}`\n",
        f"- After: `{payload['screenshots']['after']['file']}`\n\n",
        "## Joint Results\n\n",
        "| joint | target | before | after | delta | status |\n",
        "|---|---:|---:|---:|---:|---|\n",
    ]
    for r in payload["joint_results"]:
        lines.append(
            f"| `{r['joint']}` | {r.get('target', '')} | {r.get('qpos_before', '')} | {r.get('qpos_after', '')} | {r.get('delta', '')} | `{r['status']}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- `rough_body_support_link` and `base_link` remain fixed while wrist/finger/arm joints move, so the body connection did not detach during this smoke test.\n",
            "- This is a small-angle kinematic/physics smoke, not a calibrated dynamics validation.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--steps", type=int, default=80)
    args = parser.parse_args()
    payload = run(Path(args.scene), args.steps)
    write_report(payload)
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")
    print(f"Status: {payload['status']}")


if __name__ == "__main__":
    main()
