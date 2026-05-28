from __future__ import annotations

import json
import math

import numpy as np

from clean_mesh_common import CLEAN_DRAFT_XML, DOCS_DIR, METADATA_DIR, ensure_dirs, load_model, model_summary, write_json


REPORT_MD = DOCS_DIR / "clean_mesh_joint_smoke_test_report.md"
REPORT_JSON = METADATA_DIR / "clean_mesh_joint_smoke_test.json"


def small_target(model, jid: int) -> float:
    lower, upper = [float(value) for value in model.jnt_range[jid]]
    if math.isclose(lower, upper):
        return lower
    if lower <= 0.12 <= upper:
        return 0.12
    if lower <= -0.12 <= upper:
        return -0.12
    return lower + 0.25 * (upper - lower)


def main() -> int:
    ensure_dirs()
    try:
        mujoco, model, data = load_model(CLEAN_DRAFT_XML)
        mujoco.mj_forward(model, data)
    except Exception as exc:
        report = {"load_success": False, "error": f"{type(exc).__name__}: {exc}", "xml": str(CLEAN_DRAFT_XML)}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    hinge_joint_ids = [jid for jid in range(model.njnt) if int(model.jnt_type[jid]) == hinge_type]
    neutral_qpos = data.qpos.copy()
    results = []
    mesh_type = int(mujoco.mjtGeom.mjGEOM_MESH)
    clean_geom_ids = [
        gid for gid in range(model.ngeom)
        if int(model.geom_type[gid]) == mesh_type
        and "clean_visual" in (mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid) or "")
    ]

    for jid in hinge_joint_ids:
        data.qpos[:] = neutral_qpos
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or f"joint_{jid}"
        adr = int(model.jnt_qposadr[jid])
        lower, upper = [float(value) for value in model.jnt_range[jid]]
        target = min(max(small_target(model, jid), lower), upper)
        data.qpos[adr] = target
        mujoco.mj_forward(model, data)
        finite = bool(np.isfinite(data.xpos).all() and np.isfinite(data.geom_xpos).all())
        max_abs_body_pos = float(np.max(np.abs(data.xpos)))
        max_abs_clean_geom_pos = float(np.max(np.abs(data.geom_xpos[clean_geom_ids]))) if clean_geom_ids else 0.0
        status = "ok" if finite and max_abs_body_pos < 2.0 and max_abs_clean_geom_pos < 2.0 else "needs_review"
        results.append(
            {
                "name": name,
                "range": [lower, upper],
                "target": target,
                "finite_pose": finite,
                "max_abs_body_pos": max_abs_body_pos,
                "max_abs_clean_geom_pos": max_abs_clean_geom_pos,
                "status": status,
            }
        )

    report = {
        "xml": str(CLEAN_DRAFT_XML),
        "load_success": True,
        "model_summary": model_summary(model),
        "hinge_joint_count": len(hinge_joint_ids),
        "joint_results": results,
        "overall_status": "ok" if all(item["status"] == "ok" for item in results) else "needs_visual_review",
        "notes": [
            "This smoke test sets qpos directly and checks numeric sanity for clean mesh geoms.",
            "It does not prove mesh origin/orientation correctness; screenshot-based visual audit is required.",
            "Collision remains primitive/provisional; clean mesh geoms are visual-only.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_status"] == "ok" else 1


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Clean Mesh Joint Smoke Test Report",
        "",
        f"- XML: `{report.get('xml', CLEAN_DRAFT_XML)}`",
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
            "## Per-Joint Qpos Smoke",
            "",
        ]
    )
    for item in report.get("joint_results", []):
        lines.append(
            f"- `{item['name']}` target={item['target']:.4g}, "
            f"range=[{item['range'][0]:.4g}, {item['range'][1]:.4g}], "
            f"finite={item['finite_pose']}, max_abs_body_pos={item['max_abs_body_pos']:.4g}, "
            f"max_abs_clean_geom_pos={item['max_abs_clean_geom_pos']:.4g}, status={item['status']}"
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
