from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball_primitive.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"


def joint_name(model, mujoco, jid: int) -> str:
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or f"joint_{jid}"


def small_target(model, jid: int) -> float:
    lower, upper = [float(value) for value in model.jnt_range[jid]]
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
        report = {"load_success": False, "error": f"import failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    try:
        model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
    except Exception as exc:
        report = {"load_success": False, "error": f"primitive scene load failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    hinge_joint_ids = [jid for jid in range(model.njnt) if int(model.jnt_type[jid]) == hinge_type]
    neutral_qpos = data.qpos.copy()
    results = []
    for jid in hinge_joint_ids:
        data.qpos[:] = neutral_qpos
        name = joint_name(model, mujoco, jid)
        adr = int(model.jnt_qposadr[jid])
        lower, upper = [float(value) for value in model.jnt_range[jid]]
        target = min(max(small_target(model, jid), lower), upper)
        data.qpos[adr] = target
        mujoco.mj_forward(model, data)
        finite = bool(np.isfinite(data.xpos).all() and np.isfinite(data.xquat).all())
        max_abs_body_pos = float(np.max(np.abs(data.xpos)))
        results.append(
            {
                "name": name,
                "range": [lower, upper],
                "target": target,
                "finite_pose": finite,
                "max_abs_body_pos": max_abs_body_pos,
                "status": "ok" if finite and max_abs_body_pos < 2.0 else "needs_review",
            }
        )

    site_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SITE, sid) or f"site_{sid}"
        for sid in range(model.nsite)
    ]
    report = {
        "scene": str(SCENE_XML),
        "load_success": True,
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nq": int(model.nq),
            "nv": int(model.nv),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
            "nmesh": int(model.nmesh),
            "nu": int(model.nu),
        },
        "site_names": site_names,
        "hinge_joint_count": len(hinge_joint_ids),
        "joint_results": results,
        "overall_status": "ok" if all(item["status"] == "ok" for item in results) else "needs_review",
        "notes": [
            "Primitive smoke test does not use suspicious STL meshes.",
            "This test sets qpos directly and validates kinematic/numeric sanity only.",
            "Axis signs and mechanical semantics still need viewer/manual confirmation.",
        ],
    }
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_status"] == "ok" else 1


def write_report(report: dict) -> None:
    (METADATA_DIR / "primitive_joint_smoke_test.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Primitive Joint Smoke Test Report",
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
            "## Fingertip Sites",
            "",
        ]
    )
    lines.extend(f"- `{name}`" for name in report.get("site_names", []))
    lines.extend(["", "## Per-Joint Qpos Smoke", ""])
    for item in report.get("joint_results", []):
        lines.append(
            f"- `{item['name']}` target={item['target']:.4g}, "
            f"range=[{item['range'][0]:.4g}, {item['range'][1]:.4g}], "
            f"finite={item['finite_pose']}, max_abs_body_pos={item['max_abs_body_pos']:.4g}, "
            f"status={item['status']}"
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    (DOCS_DIR / "primitive_joint_smoke_test_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
