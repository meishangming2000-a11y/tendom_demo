from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
URDF_PATH = ROOT / "robot.urdf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"


def resolve_mesh(filename: str) -> tuple[Path, bool]:
    candidates: list[Path] = []
    if filename.startswith("package://hand_export/"):
        candidates.append(ROOT / filename.removeprefix("package://hand_export/"))
    elif filename.startswith("package://"):
        parts = filename.removeprefix("package://").split("/", 1)
        if len(parts) == 2:
            candidates.append(ROOT / parts[1])
        candidates.append(ROOT / Path(filename).name)
    else:
        candidates.append(ROOT / filename)
        candidates.append(ROOT / "meshes" / Path(filename).name)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve(), True
    return candidates[0].resolve(), False


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    text = URDF_PATH.read_text(encoding="utf-8")
    robot = ET.fromstring(text)
    link_names = [link.get("name") for link in robot.findall("link")]
    joints = robot.findall("joint")
    joint_names = [joint.get("name") for joint in joints]

    mesh_refs = []
    for mesh in robot.findall(".//mesh"):
        filename = mesh.get("filename", "")
        resolved, exists = resolve_mesh(filename)
        mesh_refs.append({"filename": filename, "resolved": str(resolved), "exists": exists})

    revolute_missing_limit = []
    joints_missing_parent = []
    joints_missing_child = []
    fixed_with_limit = []
    joint_records = []
    for joint in joints:
        parent = joint.find("parent")
        child = joint.find("child")
        limit = joint.find("limit")
        axis = joint.find("axis")
        joint_type = joint.get("type", "fixed")
        name = joint.get("name")
        if parent is None or not parent.get("link"):
            joints_missing_parent.append(name)
        if child is None or not child.get("link"):
            joints_missing_child.append(name)
        if joint_type == "revolute" and limit is None:
            revolute_missing_limit.append(name)
        if joint_type == "fixed" and limit is not None:
            fixed_with_limit.append(name)
        joint_records.append(
            {
                "name": name,
                "type": joint_type,
                "parent": parent.get("link") if parent is not None else None,
                "child": child.get("link") if child is not None else None,
                "axis": axis.get("xyz") if axis is not None else None,
                "limit": dict(limit.attrib) if limit is not None else None,
            }
        )

    duplicate_links = sorted(name for name, count in Counter(link_names).items() if count > 1)
    duplicate_joints = sorted(name for name, count in Counter(joint_names).items() if count > 1)
    missing_meshes = [mesh for mesh in mesh_refs if not mesh["exists"]]
    unresolved_package_paths = [
        mesh for mesh in mesh_refs if mesh["filename"].startswith("package://") and not mesh["exists"]
    ]
    joint_type_counts = Counter(joint.get("type", "fixed") for joint in joints)

    summary = {
        "urdf": str(URDF_PATH),
        "robot_name": robot.get("name"),
        "link_count": len(link_names),
        "joint_count": len(joints),
        "joint_type_counts": dict(sorted(joint_type_counts.items())),
        "mesh_file_count": len(list((ROOT / "meshes").glob("*"))),
        "mesh_reference_count": len(mesh_refs),
        "has_empty_link": "Empty_Link" in text,
        "duplicate_links": duplicate_links,
        "duplicate_joints": duplicate_joints,
        "missing_meshes": missing_meshes,
        "unresolved_package_paths": unresolved_package_paths,
        "joints_missing_parent": joints_missing_parent,
        "joints_missing_child": joints_missing_child,
        "revolute_missing_limit": revolute_missing_limit,
        "fixed_with_limit": fixed_with_limit,
        "joints": joint_records,
        "notes": [
            "CAD/URDF current names mcp_flex and mcp_abd may need later review against actual motion-axis semantics.",
            "This is a stage1 geometry/kinematics skeleton check only; no tendon routing or controller semantics are inferred.",
        ],
    }

    (METADATA_DIR / "urdf_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# URDF Integrity Report",
        "",
        f"- URDF: `{URDF_PATH}`",
        f"- Robot name: `{summary['robot_name']}`",
        f"- Links: {summary['link_count']}",
        f"- Joints: {summary['joint_count']}",
        f"- Revolute joints: {joint_type_counts.get('revolute', 0)}",
        f"- Fixed joints: {joint_type_counts.get('fixed', 0)}",
        f"- Mesh files in `meshes/`: {summary['mesh_file_count']}",
        f"- Mesh references in URDF: {summary['mesh_reference_count']}",
        f"- Contains `Empty_Link`: {'yes' if summary['has_empty_link'] else 'no'}",
        "",
        "## Checks",
        "",
        f"- Unique link names: {'yes' if not duplicate_links else 'no: ' + ', '.join(duplicate_links)}",
        f"- Unique joint names: {'yes' if not duplicate_joints else 'no: ' + ', '.join(duplicate_joints)}",
        f"- All mesh files exist: {'yes' if not missing_meshes else 'no'}",
        f"- All revolute joints have limits: {'yes' if not revolute_missing_limit else 'no: ' + ', '.join(revolute_missing_limit)}",
        f"- All joints have parent: {'yes' if not joints_missing_parent else 'no: ' + ', '.join(joints_missing_parent)}",
        f"- All joints have child: {'yes' if not joints_missing_child else 'no: ' + ', '.join(joints_missing_child)}",
        f"- Unresolved `package://` paths: {'none' if not unresolved_package_paths else str(len(unresolved_package_paths))}",
        "",
        "## Notes",
        "",
        "- `package://hand_export/meshes/...` paths were normalized in `robot.urdf` to local `meshes/...`; the pre-edit URDF is backed up under `archive/`.",
        "- CAD/URDF current names `mcp_flex` and `mcp_abd` may need later review against actual motion-axis semantics.",
        "- Tip coordinate systems are not represented as URDF links or joints in this export.",
        "",
    ]
    if missing_meshes:
        lines.extend(["## Missing Meshes", ""])
        lines.extend(f"- `{mesh['filename']}` -> `{mesh['resolved']}`" for mesh in missing_meshes)
        lines.append("")
    (DOCS_DIR / "urdf_integrity_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not missing_meshes and not duplicate_links and not duplicate_joints else 1


if __name__ == "__main__":
    raise SystemExit(main())
