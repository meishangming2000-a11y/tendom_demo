from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
URDF_PATH = ROOT / "robot.urdf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"

REQUIRED_JOINTS = [
    "wrist_1_joint",
    "wrist_2_joint",
    "index_mcp_flex_joint",
    "index_mcp_abd_joint",
    "index_pip_joint",
    "index_dip_joint",
    "middle_mcp_flex_joint",
    "middle_mcp_abd_joint",
    "middle_pip_joint",
    "middle_dip_joint",
    "ring_mcp_flex_joint",
    "ring_mcp_abd_joint",
    "ring_pip_joint",
    "ring_dip_joint",
    "little_mcp_flex_joint",
    "little_mcp_abd_joint",
    "little_pip_joint",
    "little_dip_joint",
    "thumb_root_connector_fixed_joint",
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]

TIP_FRAMES = [
    "index_tip_csys",
    "middle_tip_csys",
    "ring_tip_csys",
    "little_tip_csys",
    "thumb_tip_csys",
]

TREE_ORDER = {
    "wrist_1_joint": 10,
    "wrist_2_joint": 20,
    "index_mcp_flex_joint": 100,
    "middle_mcp_flex_joint": 200,
    "ring_mcp_flex_joint": 300,
    "little_mcp_flex_joint": 400,
    "thumb_root_connector_fixed_joint": 500,
}


def resolve_mesh_path(filename: str) -> Path:
    if filename.startswith("package://hand_export/"):
        rel = filename.removeprefix("package://hand_export/")
        return ROOT / rel
    if filename.startswith("package://"):
        without_scheme = filename.removeprefix("package://")
        parts = without_scheme.split("/", 1)
        rel = parts[1] if len(parts) == 2 else parts[0]
        return ROOT / rel
    return (ROOT / filename).resolve()


def read_manifest() -> dict:
    manifest_path = METADATA_DIR / "export_source_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def joint_record(joint: ET.Element) -> dict:
    parent = joint.find("parent")
    child = joint.find("child")
    axis = joint.find("axis")
    origin = joint.find("origin")
    limit = joint.find("limit")
    return {
        "name": joint.get("name"),
        "type": joint.get("type", "fixed"),
        "parent": parent.get("link") if parent is not None else None,
        "child": child.get("link") if child is not None else None,
        "axis": axis.get("xyz") if axis is not None else None,
        "origin": dict(origin.attrib) if origin is not None else None,
        "limit": dict(limit.attrib) if limit is not None else None,
    }


def build_tree(root_link: str, children_by_parent: dict[str, list[dict]]) -> dict:
    return {
        "link": root_link,
        "children": [
            {
                "joint": child["name"],
                "joint_type": child["type"],
                "child_link": child["child"],
                "subtree": build_tree(child["child"], children_by_parent),
            }
            for child in sorted(
                children_by_parent.get(root_link, []),
                key=lambda item: (TREE_ORDER.get(item["name"], 10_000), item["name"] or ""),
            )
        ],
    }


def render_tree_md(node: dict, depth: int = 0) -> list[str]:
    indent = "  " * depth
    lines = [f"{indent}- `{node['link']}`"]
    for child in node["children"]:
        lines.append(
            f"{indent}  - `{child['joint']}` ({child['joint_type']}) -> `{child['child_link']}`"
        )
        lines.extend(render_tree_md(child["subtree"], depth + 2))
    return lines


def bool_text(value: bool) -> str:
    return "yes" if value else "no"


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    urdf_text = URDF_PATH.read_text(encoding="utf-8")
    robot = ET.fromstring(urdf_text)
    links = [link.get("name") for link in robot.findall("link")]
    joints = [joint_record(joint) for joint in robot.findall("joint")]
    joint_names = [joint["name"] for joint in joints]
    link_counts = Counter(links)
    joint_counts = Counter(joint_names)
    joint_type_counts = Counter(joint["type"] for joint in joints)

    mesh_refs = []
    for mesh in robot.findall(".//mesh"):
        filename = mesh.get("filename")
        resolved = resolve_mesh_path(filename)
        mesh_refs.append(
            {
                "filename": filename,
                "resolved": str(resolved),
                "exists": resolved.exists(),
            }
        )

    mesh_files = sorted((ROOT / "meshes").glob("*"))
    children = [joint["child"] for joint in joints if joint["child"]]
    parents = [joint["parent"] for joint in joints if joint["parent"]]
    root_links = sorted(set(links) - set(children))
    children_by_parent: dict[str, list[dict]] = defaultdict(list)
    for joint in joints:
        if joint["parent"] and joint["child"]:
            children_by_parent[joint["parent"]].append(joint)

    trees = [build_tree(root_link, children_by_parent) for root_link in root_links]

    missing_meshes = [mesh for mesh in mesh_refs if not mesh["exists"]]
    duplicate_links = sorted(name for name, count in link_counts.items() if count > 1)
    duplicate_joints = sorted(name for name, count in joint_counts.items() if count > 1)
    joints_missing_parent = sorted(joint["name"] for joint in joints if not joint["parent"])
    joints_missing_child = sorted(joint["name"] for joint in joints if not joint["child"])
    revolute_missing_limit = sorted(
        joint["name"] for joint in joints if joint["type"] == "revolute" and not joint["limit"]
    )
    fixed_with_limit = sorted(
        joint["name"] for joint in joints if joint["type"] == "fixed" and joint["limit"]
    )
    duplicate_children = sorted(name for name, count in Counter(children).items() if count > 1)
    missing_required_joints = sorted(set(REQUIRED_JOINTS) - set(joint_names))
    present_required_joints = sorted(set(REQUIRED_JOINTS) & set(joint_names))
    present_tip_frames = sorted((set(links) | set(joint_names)) & set(TIP_FRAMES))
    missing_tip_frames = sorted(set(TIP_FRAMES) - set(present_tip_frames))

    exact_automatic_generate = "Automatically Generate" in urdf_text
    standard_exporter_header = "automatically created by SolidWorks to URDF Exporter" in urdf_text

    issues = []
    if "Empty_Link" in urdf_text:
        issues.append("Found Empty_Link in URDF text.")
    if exact_automatic_generate:
        issues.append("Found exact 'Automatically Generate' text in URDF.")
    if missing_meshes:
        issues.append(f"Missing mesh references: {len(missing_meshes)}.")
    if duplicate_links:
        issues.append(f"Duplicate link names: {', '.join(duplicate_links)}.")
    if duplicate_joints:
        issues.append(f"Duplicate joint names: {', '.join(duplicate_joints)}.")
    if joints_missing_parent:
        issues.append(f"Joints missing parent: {', '.join(joints_missing_parent)}.")
    if joints_missing_child:
        issues.append(f"Joints missing child: {', '.join(joints_missing_child)}.")
    if revolute_missing_limit:
        issues.append(f"Revolute joints missing limit: {', '.join(revolute_missing_limit)}.")
    if fixed_with_limit:
        issues.append(f"Fixed joints with limit tags: {', '.join(fixed_with_limit)}.")
    if duplicate_children:
        issues.append(f"Child links attached by multiple joints: {', '.join(duplicate_children)}.")
    if missing_required_joints:
        issues.append(f"Missing required stage1 joints: {', '.join(missing_required_joints)}.")
    if len(root_links) != 1:
        issues.append(f"Expected one root link, found {len(root_links)}: {', '.join(root_links)}.")

    recommendations = [
        "CAD/URDF current names mcp_flex and mcp_abd may need later review against actual motion-axis semantics.",
        "Tip coordinate systems are not represented as URDF links/joints in this export; keep them for later MuJoCo site/fingertip-frame work.",
        "Keep this export as a stage1 skeleton; do not infer tendon routing or high-confidence dynamics from it yet.",
    ]
    if not issues:
        recommendations.insert(0, "No blocking URDF text-structure issue was found by this pass.")

    archive_files = sorted(path.name for path in (ROOT / "archive").glob("robot.urdf.bak_*"))
    cleanup_notes = [
        "mesh filenames normalized from package://hand_export/meshes/... to meshes/...",
        "index_mcp_abd_joint and middle_mcp_abd_joint lower limits normalized to -0.2 per tonight's default MCP-abd range.",
        "thumb_ip_joint lower limit normalized to 0 per tonight's default thumb-IP range.",
    ]

    manifest = read_manifest()
    result = {
        "export_package_location": manifest.get("source", r"D:\tendon_project\hardwares\hand\hand_export"),
        "urdf_file": str(URDF_PATH),
        "robot_name": robot.get("name"),
        "mesh_file_count": len([path for path in mesh_files if path.is_file()]),
        "mesh_reference_count": len(mesh_refs),
        "unique_mesh_reference_count": len({mesh["filename"] for mesh in mesh_refs}),
        "link_count": len(links),
        "joint_count": len(joints),
        "joint_type_counts": dict(sorted(joint_type_counts.items())),
        "root_links": root_links,
        "links": links,
        "joints": joints,
        "checks": {
            "has_empty_link": "Empty_Link" in urdf_text,
            "has_exact_automatically_generate_text": exact_automatic_generate,
            "has_standard_solidworks_exporter_header": standard_exporter_header,
            "missing_meshes": missing_meshes,
            "duplicate_links": duplicate_links,
            "duplicate_joints": duplicate_joints,
            "joints_missing_parent": joints_missing_parent,
            "joints_missing_child": joints_missing_child,
            "revolute_missing_limit": revolute_missing_limit,
            "fixed_with_limit": fixed_with_limit,
            "duplicate_child_links": duplicate_children,
            "missing_required_joints": missing_required_joints,
            "present_required_joints": present_required_joints,
            "present_tip_frames": present_tip_frames,
            "missing_tip_frames": missing_tip_frames,
        },
        "trees": trees,
        "issues": issues,
        "recommendations": recommendations,
        "cleanup_notes": cleanup_notes,
        "urdf_backups": archive_files,
    }

    (METADATA_DIR / "urdf_structure_check.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (METADATA_DIR / "link_joint_tree.json").write_text(
        json.dumps({"root_links": root_links, "trees": trees, "joints": joints}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    tree_lines = ["# Link-Joint Tree", ""]
    for tree in trees:
        tree_lines.extend(render_tree_md(tree))
        tree_lines.append("")
    tree_lines.extend(
        [
            "## Notes",
            "",
            "- Tip coordinate systems currently not present as URDF link/joint nodes: "
            + ", ".join(f"`{name}`" for name in missing_tip_frames)
            + ".",
            "- CAD/URDF current names `mcp_flex` and `mcp_abd` may need later review against actual motion-axis semantics.",
            "",
        ]
    )
    (DOCS_DIR / "link_joint_tree.md").write_text("\n".join(tree_lines), encoding="utf-8")

    issue_lines = [f"- {issue}" for issue in issues] if issues else ["- No blocking issue found."]
    rec_lines = [f"- {rec}" for rec in recommendations]
    cleanup_lines = [f"- {note}" for note in cleanup_notes]
    missing_mesh_lines = (
        [f"- `{mesh['filename']}` -> `{mesh['resolved']}`" for mesh in missing_meshes]
        if missing_meshes
        else ["- None."]
    )
    required_joint_lines = [
        f"- present: {len(present_required_joints)} / {len(REQUIRED_JOINTS)}",
        f"- missing: {', '.join(missing_required_joints) if missing_required_joints else 'None'}",
    ]
    report_lines = [
        "# URDF Export Structure Check",
        "",
        "## Summary",
        "",
        f"- Export package location: `{result['export_package_location']}`",
        f"- URDF file: `{URDF_PATH.name}`",
        f"- Mesh file count: {result['mesh_file_count']}",
        f"- Link count: {result['link_count']}",
        f"- Joint count: {result['joint_count']}",
        f"- Revolute joint count: {joint_type_counts.get('revolute', 0)}",
        f"- Fixed joint count: {joint_type_counts.get('fixed', 0)}",
        f"- Found `Empty_Link`: {bool_text(result['checks']['has_empty_link'])}",
        f"- Found missing mesh: {bool_text(bool(missing_meshes))}",
        f"- Found exact `Automatically Generate` text: {bool_text(exact_automatic_generate)}",
        f"- Standard SolidWorks exporter header remains: {bool_text(standard_exporter_header)}",
        "",
        "## Required Stage1 Joints",
        "",
        *required_joint_lines,
        "",
        "## Mesh Path Check",
        "",
        *missing_mesh_lines,
        "",
        "## Joint Integrity Check",
        "",
        f"- Joints missing parent: {', '.join(joints_missing_parent) if joints_missing_parent else 'None'}",
        f"- Joints missing child: {', '.join(joints_missing_child) if joints_missing_child else 'None'}",
        f"- Revolute joints missing limit: {', '.join(revolute_missing_limit) if revolute_missing_limit else 'None'}",
        f"- Fixed joints with limit tags: {', '.join(fixed_with_limit) if fixed_with_limit else 'None'}",
        f"- Duplicate link names: {', '.join(duplicate_links) if duplicate_links else 'None'}",
        f"- Duplicate joint names: {', '.join(duplicate_joints) if duplicate_joints else 'None'}",
        f"- Root links: {', '.join(root_links) if root_links else 'None'}",
        "",
        "## Stage1 Main Chain Tree",
        "",
    ]
    for tree in trees:
        report_lines.extend(render_tree_md(tree))
        report_lines.append("")
    report_lines.extend(
        [
            "## Cleanup Applied",
            "",
            *cleanup_lines,
            f"- URDF backups: {', '.join(archive_files) if archive_files else 'None'}",
            "",
            "## Issues",
            "",
            *issue_lines,
            "",
            "## Recommendations",
            "",
            *rec_lines,
            "",
        ]
    )
    (DOCS_DIR / "urdf_export_structure_check.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    print(json.dumps(result["checks"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
