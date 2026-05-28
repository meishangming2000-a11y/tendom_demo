from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import xml.etree.ElementTree as ET
from xml.dom import minidom

from export3_common import (
    ARCHIVE_DIR,
    BALL_POSITION,
    BALL_RADIUS,
    CONTROLLED_JOINTS,
    DOCS_DIR,
    HAND_XML,
    METADATA_DIR,
    MJCF_DIR,
    RAW_HAND_XML,
    ROOT,
    SCENE_XML,
    write_json,
)


SOURCE_DIR = Path(r"D:\tendon_project\hardwares\hand\hand_export3")
EXPORT3_DIR = ROOT / "export3"
MESHES_EXPORT3_DIR = ROOT / "meshes_export3"

IMPORT_REPORT = DOCS_DIR / "export3_import_report.md"
URDF_REPORT = DOCS_DIR / "export3_urdf_integrity_report.md"
URDF_SUMMARY_JSON = METADATA_DIR / "export3_urdf_summary.json"
TREE_REPORT = DOCS_DIR / "export3_link_joint_tree.md"
TREE_JSON = METADATA_DIR / "export3_link_joint_tree.json"
MESH_REPORT = DOCS_DIR / "export3_mesh_diagnostics.md"
MESH_MANIFEST_JSON = METADATA_DIR / "export3_mesh_manifest.json"
LOAD_REPORT = DOCS_DIR / "export3_mujoco_load_report.md"

EXPECTED_THUMB_CHAIN = [
    ("thumb_root_connector_fixed_joint", "palm_link", "thumb_root_connector_link"),
    ("thumb_cmc_abd_joint", "thumb_root_connector_link", "thumb_trapezium1_link"),
    ("thumb_cmc_flex_joint", "thumb_trapezium1_link", "thumb_metacarpal_link"),
    ("thumb_mcp_joint", "thumb_metacarpal_link", "thumb_proximal_link"),
    ("thumb_ip_joint", "thumb_proximal_link", "thumb_distal_link"),
]

FINGER_COLORS = {
    "index": "0.64 0.74 0.92 1",
    "middle": "0.62 0.82 0.72 1",
    "ring": "0.90 0.78 0.58 1",
    "little": "0.78 0.66 0.88 1",
    "thumb": "0.95 0.70 0.62 1",
}


def backup(path: Path, tag: str) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = ARCHIVE_DIR / f"{tag}_{stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        shutil.copytree(path, target_dir / path.name, dirs_exist_ok=True)
    else:
        shutil.copy2(path, target_dir / path.name)


def backup_outputs() -> None:
    for path in [
        IMPORT_REPORT,
        URDF_REPORT,
        URDF_SUMMARY_JSON,
        TREE_REPORT,
        TREE_JSON,
        MESH_REPORT,
        MESH_MANIFEST_JSON,
        RAW_HAND_XML,
        HAND_XML,
        SCENE_XML,
        LOAD_REPORT,
    ]:
        backup(path, "export3_pre")


def copy_export3() -> dict:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(SOURCE_DIR)
    backup(EXPORT3_DIR, "export3_import_dir_pre")
    EXPORT3_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_DIR, EXPORT3_DIR, dirs_exist_ok=True)
    urdfs = sorted(EXPORT3_DIR.rglob("*.urdf"))
    mesh_dirs = [path for path in EXPORT3_DIR.rglob("*") if path.is_dir() and path.name.lower() == "meshes"]
    package_files = sorted(EXPORT3_DIR.rglob("package.xml"))
    mesh_count = sum(1 for path in (mesh_dirs[0].iterdir() if mesh_dirs else []) if path.is_file()) if mesh_dirs else 0
    empty_link_hits = []
    for urdf in urdfs:
        text = urdf.read_text(encoding="utf-8", errors="ignore")
        if "Empty_Link" in text:
            empty_link_hits.append(str(urdf))
    report = {
        "source_dir": str(SOURCE_DIR),
        "target_dir": str(EXPORT3_DIR),
        "urdf_files": [str(path) for path in urdfs],
        "selected_urdf": str(urdfs[0]) if urdfs else None,
        "mesh_dirs": [str(path) for path in mesh_dirs],
        "selected_mesh_dir": str(mesh_dirs[0]) if mesh_dirs else None,
        "mesh_file_count": mesh_count,
        "package_files": [str(path) for path in package_files],
        "package_exists": bool(package_files),
        "multiple_urdf": len(urdfs) > 1,
        "empty_link_hits": empty_link_hits,
    }
    write_import_report(report)
    return report


def parse_xyz(value: str | None, default: str = "0 0 0") -> list[float]:
    return [float(item) for item in (value or default).split()]


def fmt(values: list[float]) -> str:
    return " ".join(f"{value:.8g}" for value in values)


def rpy_to_quat(rpy: list[float]) -> list[float]:
    roll, pitch, yaw = rpy
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    return [
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ]


def pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def selected_paths(import_report: dict) -> tuple[Path, Path]:
    urdf = Path(import_report["selected_urdf"])
    mesh_dir = Path(import_report["selected_mesh_dir"])
    return urdf, mesh_dir


def mesh_uri_to_path(uri: str, package_root: Path) -> Path | None:
    if uri.startswith("package://"):
        rest = uri[len("package://") :]
        parts = rest.replace("\\", "/").split("/")
        if not parts:
            return None
        package = parts[0]
        relative = Path(*parts[1:])
        if package == "hand_export3":
            return package_root / relative
        return None
    path = Path(uri)
    if path.is_absolute():
        return path
    return package_root / path


def parse_urdf(urdf_path: Path) -> dict:
    robot = ET.parse(urdf_path).getroot()
    package_root = urdf_path.parents[1]
    links = {}
    mesh_refs = []
    for link in robot.findall("link"):
        name = link.get("name")
        visual = link.find("visual")
        collision = link.find("collision")
        inertial = link.find("inertial")
        visual_origin = {"xyz": "0 0 0", "rpy": "0 0 0"}
        mesh_filename = None
        rgba = "0.78 0.82 0.90 1"
        if visual is not None:
            origin = visual.find("origin")
            if origin is not None:
                visual_origin = dict(origin.attrib)
            mesh = visual.find("./geometry/mesh")
            if mesh is not None and mesh.get("filename"):
                mesh_filename = mesh.get("filename")
            color = visual.find("./material/color")
            if color is not None and color.get("rgba"):
                rgba = color.get("rgba")
        for source_name, parent in [("visual", visual), ("collision", collision)]:
            if parent is None:
                continue
            for mesh in parent.findall("./geometry/mesh"):
                uri = mesh.get("filename")
                if not uri:
                    continue
                resolved = mesh_uri_to_path(uri, package_root)
                mesh_refs.append(
                    {
                        "link": name,
                        "source": source_name,
                        "uri": uri,
                        "resolved": str(resolved) if resolved else None,
                        "exists": bool(resolved and resolved.exists()),
                    }
                )
        mass = 0.01
        inertial_pos = "0 0 0"
        if inertial is not None:
            origin = inertial.find("origin")
            mass_element = inertial.find("mass")
            if origin is not None and origin.get("xyz"):
                inertial_pos = origin.get("xyz")
            if mass_element is not None and mass_element.get("value"):
                try:
                    mass = max(float(mass_element.get("value")), 0.001)
                except ValueError:
                    mass = 0.01
        mesh_path = mesh_uri_to_path(mesh_filename, package_root) if mesh_filename else None
        links[name] = {
            "name": name,
            "mesh_uri": mesh_filename,
            "mesh_file": mesh_path.name if mesh_path else None,
            "mesh_exists": bool(mesh_path and mesh_path.exists()),
            "visual_origin": visual_origin,
            "rgba": rgba,
            "mass": mass,
            "inertial_pos": inertial_pos,
        }

    joints = []
    for joint in robot.findall("joint"):
        origin = joint.find("origin")
        axis = joint.find("axis")
        parent = joint.find("parent")
        child = joint.find("child")
        limit = joint.find("limit")
        joints.append(
            {
                "name": joint.get("name"),
                "type": joint.get("type", "fixed"),
                "parent": parent.get("link") if parent is not None else None,
                "child": child.get("link") if child is not None else None,
                "xyz": parse_xyz(origin.get("xyz") if origin is not None else None),
                "rpy": parse_xyz(origin.get("rpy") if origin is not None else None),
                "axis": axis.get("xyz") if axis is not None else "0 0 1",
                "limit": dict(limit.attrib) if limit is not None else None,
            }
        )
    return {"links": links, "joints": joints, "mesh_refs": mesh_refs, "robot_name": robot.get("name"), "urdf_path": str(urdf_path)}


def default_limit(joint_name: str) -> dict[str, str]:
    if joint_name.startswith("wrist"):
        return {"lower": "-0.8", "upper": "0.8", "effort": "1", "velocity": "1"}
    if "mcp_flex" in joint_name:
        return {"lower": "-0.5", "upper": "0.5", "effort": "1", "velocity": "1"}
    if "mcp_abd" in joint_name:
        return {"lower": "-0.2", "upper": "1.2", "effort": "1", "velocity": "1"}
    if "pip" in joint_name:
        return {"lower": "0", "upper": "1.57", "effort": "1", "velocity": "1"}
    if "dip" in joint_name or "ip" in joint_name:
        return {"lower": "0", "upper": "1.2", "effort": "1", "velocity": "1"}
    if "cmc" in joint_name:
        return {"lower": "-0.8", "upper": "0.8", "effort": "1", "velocity": "1"}
    return {"lower": "-1", "upper": "1", "effort": "1", "velocity": "1"}


def urdf_integrity(parsed: dict) -> dict:
    links = parsed["links"]
    joints = parsed["joints"]
    link_names = list(links)
    joint_names = [joint["name"] for joint in joints]
    link_counts = Counter(link_names)
    joint_counts = Counter(joint_names)
    missing_parent_child = [joint["name"] for joint in joints if not joint.get("parent") or not joint.get("child")]
    revolute_missing_limit = [joint["name"] for joint in joints if joint["type"] in {"revolute", "continuous"} and not joint.get("limit")]
    fixed_with_limit = [joint["name"] for joint in joints if joint["type"] == "fixed" and joint.get("limit")]
    missing_mesh_refs = [ref for ref in parsed["mesh_refs"] if not ref["exists"]]
    unresolved_package_refs = [ref for ref in parsed["mesh_refs"] if ref["uri"].startswith("package://") and ref["resolved"] is None]
    text = Path(parsed["urdf_path"]).read_text(encoding="utf-8", errors="ignore")
    empty_link = "Empty_Link" in text
    obvious_name_issues = [name for name in [*link_names, *joint_names] if not name or " " in name or "Automatically" in name]
    joint_by_name = {joint["name"]: joint for joint in joints}
    thumb_chain_checks = []
    for joint_name, expected_parent, expected_child in EXPECTED_THUMB_CHAIN:
        actual = joint_by_name.get(joint_name)
        thumb_chain_checks.append(
            {
                "joint": joint_name,
                "expected_parent": expected_parent,
                "expected_child": expected_child,
                "actual_parent": actual.get("parent") if actual else None,
                "actual_child": actual.get("child") if actual else None,
                "actual_type": actual.get("type") if actual else None,
                "ok": bool(actual and actual.get("parent") == expected_parent and actual.get("child") == expected_child),
            }
        )
    old_thumb_cmc = joint_by_name.get("thumb_cmc_joint")
    return {
        "link_count": len(link_names),
        "joint_count": len(joints),
        "revolute_count": sum(1 for joint in joints if joint["type"] == "revolute"),
        "fixed_count": sum(1 for joint in joints if joint["type"] == "fixed"),
        "duplicate_links": [name for name, count in link_counts.items() if count > 1],
        "duplicate_joints": [name for name, count in joint_counts.items() if count > 1],
        "missing_parent_child": missing_parent_child,
        "revolute_missing_limit": revolute_missing_limit,
        "fixed_with_limit": fixed_with_limit,
        "missing_mesh_refs": missing_mesh_refs,
        "unresolved_package_refs": unresolved_package_refs,
        "empty_link": empty_link,
        "obvious_name_issues": obvious_name_issues,
        "thumb_chain_checks": thumb_chain_checks,
        "thumb_chain_ok": all(item["ok"] for item in thumb_chain_checks),
        "old_thumb_cmc_joint_present": bool(old_thumb_cmc),
        "old_thumb_cmc_joint": old_thumb_cmc,
        "passed": not (
            empty_link
            or link_counts and any(count > 1 for count in link_counts.values())
            or any(count > 1 for count in joint_counts.values())
            or missing_parent_child
            or revolute_missing_limit
            or missing_mesh_refs
            or unresolved_package_refs
        ),
    }


def build_tree(parsed: dict) -> dict:
    joints = parsed["joints"]
    links = parsed["links"]
    children = {joint["child"] for joint in joints if joint["child"]}
    roots = sorted(set(links) - children)
    by_parent: dict[str, list[dict]] = defaultdict(list)
    for joint in joints:
        by_parent[joint["parent"]].append(joint)
    order = {
        "wrist_1_joint": 10,
        "wrist_2_joint": 20,
        "index_mcp_flex_joint": 100,
        "middle_mcp_flex_joint": 200,
        "ring_mcp_flex_joint": 300,
        "little_mcp_flex_joint": 400,
        "thumb_root_connector_fixed_joint": 500,
    }
    for rows in by_parent.values():
        rows.sort(key=lambda joint: (order.get(joint["name"], 10_000), joint["name"]))

    def node(link: str) -> dict:
        return {
            "link": link,
            "children": [
                {
                    "joint": joint["name"],
                    "type": joint["type"],
                    "axis": joint["axis"],
                    "child": node(joint["child"]),
                }
                for joint in by_parent.get(link, [])
            ],
        }

    trees = [node(root) for root in roots]
    return {"roots": roots, "trees": trees, "children_by_parent": {key: value for key, value in by_parent.items()}}


def tree_lines(node: dict, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    lines = [f"{prefix}- `{node['link']}`"]
    for child in node.get("children", []):
        lines.append(f"{prefix}  -> `{child['joint']}` ({child['type']}, axis `{child['axis']}`)")
        lines.extend(tree_lines(child["child"], indent + 1))
    return lines


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_binary_stl(path: Path) -> tuple[int, list[float], list[float]] | None:
    size = path.stat().st_size
    if size < 84:
        return None
    with path.open("rb") as handle:
        handle.seek(80)
        count = struct.unpack("<I", handle.read(4))[0]
        if 84 + count * 50 != size:
            return None
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        for _ in range(count):
            record = handle.read(50)
            values = struct.unpack("<12fH", record)
            vertices = values[3:12]
            for index in range(0, 9, 3):
                xyz = vertices[index : index + 3]
                for axis in range(3):
                    mins[axis] = min(mins[axis], xyz[axis])
                    maxs[axis] = max(maxs[axis], xyz[axis])
    return int(count), mins, maxs


def parse_ascii_stl(path: Path) -> tuple[int, list[float], list[float]] | None:
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    vertex_count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) == 4 and parts[0].lower() == "vertex":
                xyz = [float(parts[1]), float(parts[2]), float(parts[3])]
                vertex_count += 1
                for axis in range(3):
                    mins[axis] = min(mins[axis], xyz[axis])
                    maxs[axis] = max(maxs[axis], xyz[axis])
    if vertex_count == 0:
        return None
    return vertex_count // 3, mins, maxs


def analyze_mesh(path: Path) -> dict:
    parsed = parse_binary_stl(path)
    stl_format = "binary"
    if parsed is None:
        parsed = parse_ascii_stl(path)
        stl_format = "ascii" if parsed else "unknown"
    if parsed is None:
        tri_count, mins, maxs = 0, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    else:
        tri_count, mins, maxs = parsed
    span = [maxs[i] - mins[i] for i in range(3)]
    return {
        "filename": path.name,
        "link_name": path.stem,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "triangle_count": tri_count,
        "bbox_min": mins,
        "bbox_max": maxs,
        "bbox_span": span,
        "bbox_volume_estimate": span[0] * span[1] * span[2],
        "sha256": sha256(path),
        "stl_format": stl_format,
    }


def mesh_diagnostics(mesh_dir: Path) -> dict:
    rows = [analyze_mesh(path) for path in sorted(mesh_dir.iterdir()) if path.is_file() and path.suffix.lower() == ".stl"]
    hash_groups = defaultdict(list)
    for row in rows:
        hash_groups[row["sha256"]].append(row["filename"])
    duplicate_hash_groups = [names for names in hash_groups.values() if len(names) > 1]
    unique_size_count = len({row["size_bytes"] for row in rows})
    unique_triangle_count = len({row["triangle_count"] for row in rows})
    rows_by_link = {row["link_name"]: row for row in rows}
    palm = rows_by_link.get("palm_link")
    index_distal = rows_by_link.get("index_distal_link")
    hand_base = rows_by_link.get("hand_base_link")
    spans = [max(row["bbox_span"]) for row in rows if row["triangle_count"]]
    mesh_scale = "0.001 0.001 0.001" if spans and max(spans) > 2.0 else "1 1 1"
    checks = {
        "all_size_triangle_identical": unique_size_count == 1 and unique_triangle_count == 1,
        "palm_link_present": bool(palm),
        "index_distal_link_present": bool(index_distal),
        "hand_base_link_present": bool(hand_base),
        "palm_link_bbox_span": palm["bbox_span"] if palm else None,
        "index_distal_link_bbox_span": index_distal["bbox_span"] if index_distal else None,
        "hand_base_link_bbox_span": hand_base["bbox_span"] if hand_base else None,
        "index_distal_smaller_than_palm_by_max_span": bool(palm and index_distal and max(index_distal["bbox_span"]) < max(palm["bbox_span"])),
        "index_distal_smaller_than_palm_by_volume": bool(palm and index_distal and index_distal["bbox_volume_estimate"] < palm["bbox_volume_estimate"]),
        "hand_base_not_identical_to_palm": bool(hand_base and palm and hand_base["sha256"] != palm["sha256"]),
        "thumb_trapezium1_link_present": "thumb_trapezium1_link" in rows_by_link,
        "thumb_root_connector_link_present": "thumb_root_connector_link" in rows_by_link,
        "thumb_metacarpal_link_present": "thumb_metacarpal_link" in rows_by_link,
        "thumb_proximal_link_present": "thumb_proximal_link" in rows_by_link,
        "thumb_distal_link_present": "thumb_distal_link" in rows_by_link,
        "mesh_scale_for_mjcf": mesh_scale,
    }
    credible = bool(rows) and not duplicate_hash_groups and not checks["all_size_triangle_identical"] and checks["palm_link_present"] and checks["thumb_trapezium1_link_present"]
    return {
        "mesh_dir": str(mesh_dir),
        "mesh_count": len(rows),
        "rows": rows,
        "duplicate_hash_groups": duplicate_hash_groups,
        "unique_size_count": unique_size_count,
        "unique_triangle_count": unique_triangle_count,
        "checks": checks,
        "more_credible_than_suspicious_export_mesh": credible,
        "passed": credible,
    }


def copy_meshes_if_passed(diagnostics: dict, mesh_dir: Path) -> None:
    if not diagnostics["passed"]:
        return
    backup(MESHES_EXPORT3_DIR, "meshes_export3_pre")
    MESHES_EXPORT3_DIR.mkdir(parents=True, exist_ok=True)
    for row in diagnostics["rows"]:
        shutil.copy2(mesh_dir / row["filename"], MESHES_EXPORT3_DIR / row["filename"])


def color_for_link(link_name: str, alpha: float = 1.0) -> str:
    for prefix, rgba in FINGER_COLORS.items():
        if link_name.startswith(prefix):
            return " ".join([*rgba.split()[:3], f"{alpha:.3g}"])
    return f"0.68 0.72 0.80 {alpha:.3g}"


def proxy_radius(link_name: str) -> str:
    if link_name in {"hand_base_link", "wrist_middle_link"}:
        return "0.010"
    if "mcp_flex" in link_name or "root_connector" in link_name or "trapezium" in link_name:
        return "0.0058"
    if link_name.endswith("_distal_link"):
        return "0.0062"
    if link_name.startswith("thumb"):
        return "0.0068"
    return "0.0072"


def distal_vector(link_name: str, link_data: dict) -> list[float]:
    values = parse_xyz(link_data.get("inertial_pos"), default="0 0.025 0")
    length = math.sqrt(sum(value * value for value in values))
    if length > 1e-6:
        scale = 0.028 / length
        return [value * scale for value in values]
    if link_name.startswith("thumb"):
        return [0, 0.025, 0]
    return [0, 0.028, 0]


def add_link_geoms(body: ET.Element, link_name: str, links: dict, child_joints: list[dict]) -> None:
    link_data = links[link_name]
    ET.SubElement(body, "inertial", {"pos": "0 0 0", "mass": f"{max(float(link_data['mass']), 0.001):.8g}", "diaginertia": "1e-5 1e-5 1e-5"})
    if link_data.get("mesh_file"):
        origin = link_data.get("visual_origin", {})
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_export3_visual",
                "type": "mesh",
                "mesh": f"{link_name}_mesh",
                "pos": origin.get("xyz", "0 0 0"),
                "quat": fmt(rpy_to_quat(parse_xyz(origin.get("rpy")))),
                "rgba": link_data.get("rgba") or "0.78 0.82 0.90 1",
                "contype": "0",
                "conaffinity": "0",
                "group": "2",
            },
        )

    if link_name == "palm_link":
        ET.SubElement(
            body,
            "geom",
            {
                "name": "palm_link_collision_proxy_ellipsoid",
                "type": "ellipsoid",
                "pos": "0 0.048 0.002",
                "size": "0.030 0.064 0.024",
                "rgba": "0.16 0.90 0.58 0.34",
                "contype": "1",
                "conaffinity": "2",
                "group": "3",
                "friction": "0.9 0.04 0.001",
            },
        )
        for joint in child_joints:
            vector = joint["xyz"]
            if math.sqrt(sum(value * value for value in vector)) < 1e-6:
                continue
            ET.SubElement(
                body,
                "geom",
                {
                    "name": f"palm_link_{joint['name']}_collision_proxy_spoke",
                    "type": "capsule",
                    "fromto": f"0 0 0 {fmt(vector)}",
                    "size": "0.0055",
                    "rgba": "0.16 0.90 0.58 0.34",
                    "contype": "1",
                    "conaffinity": "2",
                    "group": "3",
                    "friction": "0.9 0.04 0.001",
                },
            )
        return

    if link_name == "hand_base_link":
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_collision_proxy",
                "type": "box",
                "pos": "0 0 -0.006",
                "size": "0.026 0.020 0.014",
                "rgba": "0.16 0.90 0.58 0.34",
                "contype": "1",
                "conaffinity": "2",
                "group": "3",
            },
        )
        return

    if link_name == "wrist_middle_link":
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_collision_proxy",
                "type": "capsule",
                "fromto": "0 -0.018 0 0 0.018 0",
                "size": "0.011",
                "rgba": "0.16 0.90 0.58 0.34",
                "contype": "1",
                "conaffinity": "2",
                "group": "3",
            },
        )
        return

    vector = child_joints[0]["xyz"] if child_joints else distal_vector(link_name, link_data)
    if math.sqrt(sum(value * value for value in vector)) < 1e-6:
        vector = [0.0, 0.025, 0.0]
    radius = proxy_radius(link_name)
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_collision_proxy",
            "type": "capsule",
            "fromto": f"0 0 0 {fmt(vector)}",
            "size": radius,
            "rgba": "0.16 0.90 0.58 0.34",
            "contype": "1",
            "conaffinity": "2",
            "group": "3",
            "friction": "0.9 0.04 0.001",
        },
    )
    if link_name.endswith("_distal_link"):
        prefix = link_name.removesuffix("_distal_link")
        ET.SubElement(body, "site", {"name": f"{prefix}_tip_site", "pos": fmt(vector), "size": "0.008", "rgba": "0.10 0.55 1.0 1", "type": "sphere"})


def build_mjcf_body(link_name: str, links: dict, children_by_parent: dict[str, list[dict]]) -> ET.Element:
    body = ET.Element("body", {"name": link_name})
    child_joints = children_by_parent.get(link_name, [])
    add_link_geoms(body, link_name, links, child_joints)
    for joint in child_joints:
        child_body = build_mjcf_body(joint["child"], links, children_by_parent)
        child_body.set("pos", fmt(joint["xyz"]))
        child_body.set("quat", fmt(rpy_to_quat(joint["rpy"])))
        if joint["type"] == "revolute":
            limit = joint.get("limit") or default_limit(joint["name"])
            child_body.insert(
                0,
                ET.Element(
                    "joint",
                    {
                        "name": joint["name"],
                        "type": "hinge",
                        "axis": joint["axis"],
                        "limited": "true",
                        "range": f"{limit.get('lower', '0')} {limit.get('upper', '0')}",
                        "damping": "0.08",
                        "armature": "0.0001",
                    },
                ),
            )
        elif joint["type"] != "fixed":
            child_body.insert(0, ET.Comment(f"TODO: unsupported export3 joint type {joint['type']} from {joint['name']}"))
        body.append(child_body)
    return body


def actuator_kp(joint_name: str) -> float:
    if joint_name.startswith("wrist"):
        return 5.0
    if "_mcp_" in joint_name:
        return 3.0
    if "_pip_" in joint_name or "_dip_" in joint_name:
        return 2.0
    if joint_name.startswith("thumb"):
        return 2.0
    return 2.0


def build_hand_mjcf(parsed: dict, tree_data: dict, mesh_diagnostics_payload: dict, output: Path, model_name: str) -> dict:
    links = parsed["links"]
    joints = parsed["joints"]
    roots = tree_data["roots"]
    if len(roots) != 1:
        raise RuntimeError(f"Expected one root link, found {roots}")
    mesh_scale = mesh_diagnostics_payload["checks"]["mesh_scale_for_mjcf"]
    mujoco = ET.Element("mujoco", {"model": model_name})
    ET.SubElement(mujoco, "compiler", {"angle": "radian", "meshdir": "../meshes_export3", "autolimits": "true"})
    ET.SubElement(mujoco, "option", {"timestep": "0.002", "gravity": "0 0 -9.81"})
    visual = ET.SubElement(mujoco, "visual")
    ET.SubElement(visual, "global", {"azimuth": "145", "elevation": "-25", "offwidth": "1280", "offheight": "900"})
    default = ET.SubElement(mujoco, "default")
    ET.SubElement(default, "joint", {"damping": "0.08", "armature": "0.0001"})
    ET.SubElement(default, "geom", {"solref": "0.01 1", "solimp": "0.9 0.95 0.001"})
    ET.SubElement(mujoco, "statistic", {"center": "0.005 -0.045 0.18", "extent": "0.24"})
    asset = ET.SubElement(mujoco, "asset")
    for link_name, data in links.items():
        if not data.get("mesh_file"):
            continue
        ET.SubElement(asset, "mesh", {"name": f"{link_name}_mesh", "file": data["mesh_file"], "scale": mesh_scale})
    worldbody = ET.SubElement(mujoco, "worldbody")
    root_body = build_mjcf_body(roots[0], links, tree_data["children_by_parent"])
    root_body.set("pos", "0 0 0.05")
    worldbody.append(root_body)
    actuator = ET.SubElement(mujoco, "actuator")
    actuator_rows = []
    for joint in joints:
        if joint["type"] != "revolute":
            continue
        limit = joint.get("limit") or default_limit(joint["name"])
        kp = actuator_kp(joint["name"])
        ET.SubElement(
            actuator,
            "position",
            {
                "name": f"{joint['name']}_pos",
                "joint": joint["name"],
                "kp": f"{kp:g}",
                "ctrllimited": "true",
                "ctrlrange": f"{limit.get('lower', '0')} {limit.get('upper', '0')}",
            },
        )
        actuator_rows.append({"joint": joint["name"], "actuator": f"{joint['name']}_pos", "kp": kp, "ctrlrange": [limit.get("lower"), limit.get("upper")]})
    output.write_text(pretty_xml(mujoco), encoding="utf-8")
    return {"path": str(output), "model": model_name, "mesh_scale": mesh_scale, "actuators": actuator_rows}


def build_scene() -> dict:
    scene = ET.Element("mujoco", {"model": "hand_stage1_export3_ball_scene"})
    ET.SubElement(scene, "include", {"file": HAND_XML.name})
    visual = ET.SubElement(scene, "visual")
    ET.SubElement(visual, "global", {"azimuth": "145", "elevation": "-25", "offwidth": "1280", "offheight": "900"})
    asset = ET.SubElement(scene, "asset")
    ET.SubElement(asset, "texture", {"type": "2d", "name": "ground_checker", "builtin": "checker", "rgb1": "0.18 0.20 0.22", "rgb2": "0.28 0.30 0.32", "width": "300", "height": "300"})
    ET.SubElement(asset, "material", {"name": "ground_mat", "texture": "ground_checker", "texrepeat": "4 4", "reflectance": "0.15"})
    worldbody = ET.SubElement(scene, "worldbody")
    ET.SubElement(worldbody, "light", {"pos": "0 -0.3 0.8", "dir": "0 0 -1", "directional": "true"})
    ET.SubElement(worldbody, "light", {"pos": "-0.25 0.25 0.5"})
    ET.SubElement(worldbody, "geom", {"name": "ground", "type": "plane", "pos": "0 0 0", "size": "0.4 0.4 0.02", "material": "ground_mat", "contype": "1", "conaffinity": "3"})
    ball = ET.SubElement(worldbody, "body", {"name": "ball", "pos": fmt(BALL_POSITION)})
    ET.SubElement(ball, "freejoint", {"name": "ball_freejoint"})
    ET.SubElement(ball, "geom", {"name": "ball_geom", "type": "sphere", "size": f"{BALL_RADIUS:g}", "rgba": "0.95 0.23 0.18 1", "mass": "0.03", "friction": "0.8 0.05 0.001", "condim": "3", "contype": "2", "conaffinity": "1"})
    cameras = [
        ("full_hand_with_ball", "0.20 -0.34 0.29", "0.834219 0.551433 0 -0.16379 0.247785 0.954869", "45"),
        ("front", "0.20 -0.34 0.29", "0.834219 0.551433 0 -0.16379 0.247785 0.954869", "45"),
        ("side", "0.34 0.02 0.24", "-0.190477 0.981692 0 -0.169999 -0.0329848 0.984892", "45"),
        ("top", "0.02 -0.06 0.48", "0.707107 0.707107 0 -0.705346 0.705346 0.0705346", "45"),
        ("palm", "0.03 -0.23 0.21", "0.995037 0.0995037 0 -0.030061 0.30061 0.953268", "38"),
        ("thumb_root_closeup", "-0.12 -0.22 0.20", "0.85264 -0.522499 0 0.171595 0.280048 0.944552", "28"),
        ("index_finger_closeup", "0.10 -0.20 0.29", "0.894427 0.447214 0 -0.19518 0.39036 0.8998", "28"),
    ]
    for name, pos, xyaxes, fovy in cameras:
        ET.SubElement(worldbody, "camera", {"name": name, "pos": pos, "xyaxes": xyaxes, "fovy": fovy})
    SCENE_XML.write_text(pretty_xml(scene), encoding="utf-8")
    return {"path": str(SCENE_XML), "ball_position": BALL_POSITION}


def load_model_summary() -> dict:
    import mujoco

    out = {}
    for label, path in [("hand", HAND_XML), ("scene", SCENE_XML), ("raw", RAW_HAND_XML)]:
        try:
            model = mujoco.MjModel.from_xml_path(str(path.resolve()))
            out[label] = {
                "path": str(path),
                "load_success": True,
                "nbody": int(model.nbody),
                "njnt": int(model.njnt),
                "nu": int(model.nu),
                "ngeom": int(model.ngeom),
                "nsite": int(model.nsite),
                "nmesh": int(model.nmesh),
                "joint_names": [
                    mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
                    for jid in range(model.njnt)
                    if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
                ],
                "actuator_names": [
                    mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
                    for aid in range(model.nu)
                    if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
                ],
            }
        except Exception as exc:
            out[label] = {"path": str(path), "load_success": False, "error": f"{type(exc).__name__}: {exc}"}
    return out


def write_import_report(report: dict) -> None:
    lines = [
        "# Export3 Import Report",
        "",
        f"- Source directory: `{report['source_dir']}`",
        f"- Target directory: `{report['target_dir']}`",
        f"- Selected URDF: `{report.get('selected_urdf')}`",
        f"- URDF files found: {len(report['urdf_files'])}",
        f"- Multiple URDF: {'yes' if report['multiple_urdf'] else 'no'}",
        f"- Selected mesh directory: `{report.get('selected_mesh_dir')}`",
        f"- Mesh file count: {report['mesh_file_count']}",
        f"- Package files: {len(report['package_files'])}",
        f"- Package exists: {'yes' if report['package_exists'] else 'no'}",
        f"- Empty_Link hits: {len(report['empty_link_hits'])}",
        "",
        "## Copied Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in report["urdf_files"])
    lines.append("")
    IMPORT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_urdf_reports(parsed: dict, integrity: dict, tree_data: dict) -> None:
    write_json(URDF_SUMMARY_JSON, {"parsed": parsed, "integrity": integrity})
    write_json(TREE_JSON, {"roots": tree_data["roots"], "trees": tree_data["trees"]})
    lines = [
        "# Export3 URDF Integrity Report",
        "",
        f"- URDF: `{parsed['urdf_path']}`",
        f"- Robot name: `{parsed.get('robot_name')}`",
        f"- Links: {integrity['link_count']}",
        f"- Joints: {integrity['joint_count']}",
        f"- Revolute joints: {integrity['revolute_count']}",
        f"- Fixed joints: {integrity['fixed_count']}",
        f"- Empty_Link: {'yes' if integrity['empty_link'] else 'no'}",
        f"- Duplicate links: {integrity['duplicate_links'] or 'None'}",
        f"- Duplicate joints: {integrity['duplicate_joints'] or 'None'}",
        f"- Missing parent/child joints: {integrity['missing_parent_child'] or 'None'}",
        f"- Revolute joints missing limit: {integrity['revolute_missing_limit'] or 'None'}",
        f"- Missing mesh refs: {len(integrity['missing_mesh_refs'])}",
        f"- Unresolved package refs: {len(integrity['unresolved_package_refs'])}",
        f"- Old `thumb_cmc_joint` present: {'yes' if integrity['old_thumb_cmc_joint_present'] else 'no'}",
        f"- Expected export3 thumb chain OK: {'yes' if integrity['thumb_chain_ok'] else 'no'}",
        f"- Overall pass: {'yes' if integrity['passed'] else 'no'}",
        "",
        "## Export3 Thumb Chain Check",
        "",
        "| Joint | Expected | Actual | Type | OK |",
        "|---|---|---|---|---|",
    ]
    for item in integrity["thumb_chain_checks"]:
        lines.append(
            f"| `{item['joint']}` | `{item['expected_parent']} -> {item['expected_child']}` | "
            f"`{item['actual_parent']} -> {item['actual_child']}` | `{item['actual_type']}` | {'yes' if item['ok'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `wrist_2_joint` is recorded exactly as exported. If it is fixed in export3, this report does not change it.",
            "- If a name differs from the target chain, this report records the actual name and does not force a rename.",
            "- TODO: manually confirm MCP flex/abd semantics against actual axes.",
            "",
        ]
    )
    URDF_REPORT.write_text("\n".join(lines), encoding="utf-8")

    tree_lines_md = ["# Export3 Link-Joint Tree", "", f"- Roots: `{tree_data['roots']}`", ""]
    for tree in tree_data["trees"]:
        tree_lines_md.extend(tree_lines(tree))
    tree_lines_md.append("")
    TREE_REPORT.write_text("\n".join(tree_lines_md), encoding="utf-8")


def write_mesh_reports(diagnostics: dict) -> None:
    write_json(MESH_MANIFEST_JSON, diagnostics)
    checks = diagnostics["checks"]
    lines = [
        "# Export3 Mesh Diagnostics",
        "",
        f"- Mesh directory: `{diagnostics['mesh_dir']}`",
        f"- STL count: {diagnostics['mesh_count']}",
        f"- Unique file size count: {diagnostics['unique_size_count']}",
        f"- Unique triangle count: {diagnostics['unique_triangle_count']}",
        f"- Exact duplicate hash groups: {len(diagnostics['duplicate_hash_groups'])}",
        f"- All size/triangle identical: {'yes' if checks['all_size_triangle_identical'] else 'no'}",
        f"- More credible than suspicious mesh: {'yes' if diagnostics['more_credible_than_suspicious_export_mesh'] else 'no'}",
        f"- Overall pass: {'yes' if diagnostics['passed'] else 'no'}",
        f"- MJCF mesh scale selected: `{checks['mesh_scale_for_mjcf']}`",
        "",
        "## Special Checks",
        "",
        f"- `palm_link` present: {checks['palm_link_present']}, bbox span `{checks['palm_link_bbox_span']}`",
        f"- `index_distal_link` present: {checks['index_distal_link_present']}, bbox span `{checks['index_distal_link_bbox_span']}`",
        f"- `index_distal_link` smaller than `palm_link` by max span: {checks['index_distal_smaller_than_palm_by_max_span']}",
        f"- `index_distal_link` smaller than `palm_link` by volume: {checks['index_distal_smaller_than_palm_by_volume']}",
        f"- `hand_base_link` present: {checks['hand_base_link_present']}, bbox span `{checks['hand_base_link_bbox_span']}`",
        f"- `hand_base_link` not identical to `palm_link`: {checks['hand_base_not_identical_to_palm']}",
        f"- `thumb_trapezium1_link` present: {checks['thumb_trapezium1_link_present']}",
        f"- `thumb_root_connector_link` present: {checks['thumb_root_connector_link_present']}",
        f"- `thumb_metacarpal_link` present: {checks['thumb_metacarpal_link_present']}",
        f"- `thumb_proximal_link` present: {checks['thumb_proximal_link_present']}",
        f"- `thumb_distal_link` present: {checks['thumb_distal_link_present']}",
        "",
        "## Per Mesh",
        "",
        "| File | Size bytes | Triangles | BBox span xyz | SHA-256 prefix | Duplicate group |",
        "|---|---:|---:|---|---|---|",
    ]
    dup_lookup = {}
    for group in diagnostics["duplicate_hash_groups"]:
        label = ", ".join(group)
        for name in group:
            dup_lookup[name] = label
    for row in diagnostics["rows"]:
        span = ", ".join(f"{value:.6g}" for value in row["bbox_span"])
        lines.append(
            f"| `{row['filename']}` | {row['size_bytes']} | {row['triangle_count']} | `{span}` | `{row['sha256'][:16]}` | {dup_lookup.get(row['filename'], 'no')} |"
        )
    lines.extend(["", "## Notes", "", "- Export3 meshes are copied to `meshes_export3` only when this diagnostics pass is credible.", "- No old suspicious mesh directory is used.", ""])
    MESH_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_load_report(load_summary: dict, hand_build: dict, raw_build: dict, scene_build: dict) -> None:
    lines = [
        "# Export3 MuJoCo Load Report",
        "",
        f"- Raw hand MJCF: `{raw_build['path']}`",
        f"- Export3 hand MJCF: `{hand_build['path']}`",
        f"- Scene MJCF: `{scene_build['path']}`",
        f"- Mesh scale: `{hand_build['mesh_scale']}`",
        "- Mesh geoms are visual-only; simplified primitive geoms provide collision proxy.",
        "- No suspicious STL is used.",
        "",
        "## Load Summary",
        "",
        "| Model | Load | Bodies | Joints | Actuators | Geoms | Sites | Meshes |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, item in load_summary.items():
        lines.append(
            f"| {label} | {'yes' if item.get('load_success') else 'no'} | {item.get('nbody', 'N/A')} | {item.get('njnt', 'N/A')} | "
            f"{item.get('nu', 'N/A')} | {item.get('ngeom', 'N/A')} | {item.get('nsite', 'N/A')} | {item.get('nmesh', 'N/A')} |"
        )
    lines.extend(["", "## Actuators", ""])
    lines.extend(f"- `{row['actuator']}` -> `{row['joint']}` kp={row['kp']} ctrlrange=`{row['ctrlrange']}`" for row in hand_build["actuators"])
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `wrist_2_joint` is fixed in export3 if it appears that way in the URDF; no actuator is added for fixed joints.",
            "- `thumb_cmc_abd_joint` and `thumb_cmc_flex_joint` are included as position actuated hinge joints when present in the URDF.",
            "- Raw and main export3 MJCF currently use the same mesh/body transform path. If visual inspection shows assembly/world-coordinate offsets, generate an aligned draft later and document it.",
            "",
        ]
    )
    LOAD_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    MJCF_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    backup_outputs()
    import_report = copy_export3()
    urdf_path, mesh_dir = selected_paths(import_report)
    parsed = parse_urdf(urdf_path)
    integrity = urdf_integrity(parsed)
    tree_data = build_tree(parsed)
    write_urdf_reports(parsed, integrity, tree_data)
    diagnostics = mesh_diagnostics(mesh_dir)
    write_mesh_reports(diagnostics)
    copy_meshes_if_passed(diagnostics, mesh_dir)
    raw_build = build_hand_mjcf(parsed, tree_data, diagnostics, RAW_HAND_XML, "hand_stage1_export3_raw_mesh")
    hand_build = build_hand_mjcf(parsed, tree_data, diagnostics, HAND_XML, "hand_stage1_export3")
    scene_build = build_scene()
    load_summary = load_model_summary()
    write_load_report(load_summary, hand_build, raw_build, scene_build)
    print(
        json.dumps(
            {
                "import": import_report,
                "integrity": integrity,
                "mesh": {key: diagnostics[key] for key in ("mesh_count", "duplicate_hash_groups", "checks", "passed")},
                "load": load_summary,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if load_summary.get("scene", {}).get("load_success") and integrity["passed"] and diagnostics["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
