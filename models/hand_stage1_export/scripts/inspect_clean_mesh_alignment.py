from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from clean_mesh_common import CLEAN_SCENE_XML, DOCS_DIR, METADATA_DIR, ensure_dirs, load_model, mesh_files_from_draft, model_summary, write_json


REPORT_MD = DOCS_DIR / "clean_mesh_alignment_report.md"
REPORT_JSON = METADATA_DIR / "clean_mesh_alignment.json"


def geom_world_bbox(model, data, geom_id: int) -> tuple[list[float], list[float], list[float]]:
    mesh_id = int(model.geom_dataid[geom_id])
    adr = int(model.mesh_vertadr[mesh_id])
    num = int(model.mesh_vertnum[mesh_id])
    verts = model.mesh_vert[adr : adr + num]
    rot = data.geom_xmat[geom_id].reshape(3, 3)
    world = data.geom_xpos[geom_id] + verts @ rot.T
    mins = world.min(axis=0)
    maxs = world.max(axis=0)
    return mins.tolist(), maxs.tolist(), (maxs - mins).tolist()


def main() -> int:
    ensure_dirs()
    try:
        mujoco, model, data = load_model(CLEAN_SCENE_XML)
        mujoco.mj_forward(model, data)
    except Exception as exc:
        report = {"load_success": False, "error": f"{type(exc).__name__}: {exc}", "scene": str(CLEAN_SCENE_XML)}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    palm_pos = data.xpos[palm_id].copy() if palm_id >= 0 else np.zeros(3)

    bodies = []
    for bid in range(model.nbody):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, bid) or f"body_{bid}"
        pos = data.xpos[bid].copy()
        bodies.append(
            {
                "name": name,
                "world_position": [float(v) for v in pos],
                "distance_from_palm": float(np.linalg.norm(pos - palm_pos)),
                "far_from_palm": bool(np.linalg.norm(pos - palm_pos) > 0.45 and name not in {"world", "ball"}),
            }
        )

    mesh_geoms = []
    mesh_type = int(mujoco.mjtGeom.mjGEOM_MESH)
    for gid in range(model.ngeom):
        if int(model.geom_type[gid]) != mesh_type:
            continue
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid) or f"geom_{gid}"
        mesh_id = int(model.geom_dataid[gid])
        mesh_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, mesh_id) or f"mesh_{mesh_id}"
        mins, maxs, span = geom_world_bbox(model, data, gid)
        mesh_geoms.append(
            {
                "geom": name,
                "mesh": mesh_name,
                "world_center": [float(v) for v in data.geom_xpos[gid]],
                "bbox_min": mins,
                "bbox_max": maxs,
                "bbox_span": span,
                "max_span": float(max(span)),
                "bbox_over_1m": bool(max(span) > 1.0),
                "center_far_from_palm": bool(np.linalg.norm(data.geom_xpos[gid] - palm_pos) > 0.45),
            }
        )

    mesh_files = mesh_files_from_draft()
    missing_mesh_files = []
    mesh_dir = CLEAN_SCENE_XML.parent / ".." / "meshes_clean"
    for item in mesh_files:
        filename = item.get("file")
        if filename and not (mesh_dir / filename).resolve().exists():
            missing_mesh_files.append(filename)

    issues = []
    if missing_mesh_files:
        issues.append({"severity": "BLOCKER", "issue": "missing_mesh_files", "details": missing_mesh_files})
    if any(item["bbox_over_1m"] for item in mesh_geoms):
        issues.append({"severity": "BLOCKER", "issue": "mesh_bbox_over_1m", "details": [item["geom"] for item in mesh_geoms if item["bbox_over_1m"]]})
    if any(item["far_from_palm"] for item in bodies):
        issues.append({"severity": "MAJOR", "issue": "body_far_from_palm", "details": [item["name"] for item in bodies if item["far_from_palm"]]})
    if any(item["center_far_from_palm"] for item in mesh_geoms):
        issues.append({"severity": "MAJOR", "issue": "mesh_center_far_from_palm", "details": [item["geom"] for item in mesh_geoms if item["center_far_from_palm"]]})

    report = {
        "scene": str(CLEAN_SCENE_XML),
        "load_success": True,
        "model_summary": model_summary(model),
        "mesh_files_from_draft": mesh_files,
        "missing_mesh_files": missing_mesh_files,
        "body_positions": bodies,
        "mesh_geoms": mesh_geoms,
        "issues": issues,
        "overall_status": "ok" if not issues else ("blocked" if any(item["severity"] == "BLOCKER" for item in issues) else "needs_visual_review"),
        "notes": [
            "This numerical alignment check catches scale/path/outlier problems only.",
            "Visual screenshots remain required for palm, finger root, thumb root, and tip-site alignment.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall_status"] != "blocked" else 1


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Clean Mesh Alignment Report",
        "",
        f"- Scene: `{report.get('scene', CLEAN_SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    if report.get("model_summary"):
        lines.append(f"- Model summary: `{json.dumps(report['model_summary'], ensure_ascii=False)}`")
    lines.extend(
        [
            f"- Missing mesh files: {len(report.get('missing_mesh_files', []))}",
            f"- Overall status: {report.get('overall_status', 'failed')}",
            "",
            "## Issues",
            "",
        ]
    )
    issues = report.get("issues", [])
    if issues:
        for item in issues:
            lines.append(f"- {item['severity']}: {item['issue']} -> `{item['details']}`")
    else:
        lines.append("- No numeric BLOCKER/MAJOR issues detected by bbox/path thresholds.")
    lines.extend(["", "## Mesh Geom BBox", "", "| Geom | Mesh | Center | BBox span | Max span | Flags |", "|---|---|---|---|---:|---|"])
    for item in report.get("mesh_geoms", []):
        flags = []
        if item["bbox_over_1m"]:
            flags.append("bbox_over_1m")
        if item["center_far_from_palm"]:
            flags.append("center_far_from_palm")
        lines.append(
            f"| `{item['geom']}` | `{item['mesh']}` | `{[round(v, 4) for v in item['world_center']]}` | "
            f"`{[round(v, 4) for v in item['bbox_span']]}` | {item['max_span']:.4f} | {', '.join(flags) if flags else 'ok'} |"
        )
    lines.extend(["", "## Body Positions", "", "| Body | World position | Distance from palm | Flag |", "|---|---|---:|---|"])
    for item in report.get("body_positions", []):
        lines.append(
            f"| `{item['name']}` | `{[round(v, 4) for v in item['world_position']]}` | "
            f"{item['distance_from_palm']:.4f} | {'far_from_palm' if item['far_from_palm'] else 'ok'} |"
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
