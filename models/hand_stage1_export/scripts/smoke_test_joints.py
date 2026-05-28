from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"


def joint_name(model, mujoco, jid: int) -> str:
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or f"joint_{jid}"


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def small_target(model, jid: int) -> float:
    lower, upper = model.jnt_range[jid]
    if math.isclose(lower, upper):
        return lower
    if lower <= 0.1 <= upper:
        return 0.1
    if lower <= -0.1 <= upper:
        return -0.1
    return lower + 0.25 * (upper - lower)


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import mujoco
        import numpy as np
    except Exception as exc:
        report = {
            "load_success": False,
            "error": f"import failed: {type(exc).__name__}: {exc}",
            "joint_results": [],
        }
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    try:
        model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
    except Exception as exc:
        report = {
            "load_success": False,
            "error": f"scene load failed: {type(exc).__name__}: {exc}",
            "joint_results": [],
        }
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    hinge_joint_ids = [jid for jid in range(model.njnt) if int(model.jnt_type[jid]) == hinge_type]
    all_joint_names = [joint_name(model, mujoco, jid) for jid in range(model.njnt)]
    joint_results = []

    neutral_qpos = data.qpos.copy()
    for jid in hinge_joint_ids:
        data.qpos[:] = neutral_qpos
        name = joint_name(model, mujoco, jid)
        adr = int(model.jnt_qposadr[jid])
        lower, upper = [float(v) for v in model.jnt_range[jid]]
        target = clamp(small_target(model, jid), lower, upper)
        data.qpos[adr] = target
        mujoco.mj_forward(model, data)
        finite = bool(np.isfinite(data.xpos).all() and np.isfinite(data.xquat).all())
        max_abs_body_pos = float(np.max(np.abs(data.xpos)))
        joint_results.append(
            {
                "name": name,
                "qpos_address": adr,
                "range": [lower, upper],
                "test_target": target,
                "finite_pose": finite,
                "max_abs_body_pos": max_abs_body_pos,
                "status": "ok" if finite and max_abs_body_pos < 2.0 else "needs_review",
            }
        )

    report = {
        "scene": str(SCENE_XML),
        "load_success": True,
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nq": int(model.nq),
            "nv": int(model.nv),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
            "nu": int(model.nu),
        },
        "all_joint_names": all_joint_names,
        "hinge_joint_count": len(hinge_joint_ids),
        "joint_results": joint_results,
        "overall_status": "ok"
        if all(item["status"] == "ok" for item in joint_results)
        else "needs_review",
        "notes": [
            "This smoke test sets qpos directly; no actuator or controller is implied.",
            "No severe numeric explosion was detected if max_abs_body_pos stays below 2 m.",
            "Joint axis direction, mesh fly-away, and penetration still need human visual confirmation in the viewer.",
            "CAD/URDF current names mcp_flex and mcp_abd may need later review against actual motion-axis semantics.",
        ],
    }
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_status"] == "ok" else 1


def write_report(report: dict) -> None:
    (METADATA_DIR / "joint_smoke_test.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Joint Smoke Test Report",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    if report.get("model_summary"):
        lines.append(f"- Model summary: `{json.dumps(report['model_summary'], ensure_ascii=False)}`")
    lines.extend(
        [
            f"- Hinge joints tested: {report.get('hinge_joint_count', 0)}",
            f"- Overall status: {report.get('overall_status', 'failed')}",
            "",
            "## Joint Names",
            "",
        ]
    )
    lines.extend(f"- `{name}`" for name in report.get("all_joint_names", []))
    lines.extend(["", "## Per-Joint Qpos Smoke", ""])
    for item in report.get("joint_results", []):
        lines.append(
            f"- `{item['name']}` target={item['test_target']:.4g}, "
            f"range=[{item['range'][0]:.4g}, {item['range'][1]:.4g}], "
            f"finite={item['finite_pose']}, max_abs_body_pos={item['max_abs_body_pos']:.4g}, "
            f"status={item['status']}"
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    (DOCS_DIR / "joint_smoke_test_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
