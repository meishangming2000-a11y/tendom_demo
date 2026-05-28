from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


ROOT = Path(__file__).resolve().parents[1]
CLEAN_TEST_DIR = ROOT / "clean_mesh_test"
MESHES_CLEAN_DIR = ROOT / "meshes_clean"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
MJCF_DIR = ROOT / "mjcf"
PRIMITIVE_XML = MJCF_DIR / "hand_stage1_primitive.xml"
CLEAN_DRAFT_XML = MJCF_DIR / "hand_stage1_clean_mesh_draft.xml"
REPORT_MD = DOCS_DIR / "clean_mesh_test_report.md"
SUMMARY_JSON = METADATA_DIR / "clean_mesh_test_summary.json"
REPLACEMENT_STATUS_MD = DOCS_DIR / "clean_mesh_replacement_status.md"
CLEAN_MESH_SCALE = "0.001 0.001 0.001"
MJCF_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_.-]+$")

EXPECTED_LINKS = [
    "hand_base_link",
    "wrist_middle_link",
    "palm_link",
    "index_mcp_flex_link",
    "index_proximal_phalanx_link",
    "index_proximal_inter_link",
    "index_distal_link",
    "middle_mcp_flex_link",
    "middle_proximal_phalanx_link",
    "middle_proximal_inter_link",
    "middle_distal_link",
    "ring_mcp_flex_link",
    "ring_proximal_phalanx_link",
    "ring_proximal_inter_link",
    "ring_distal_link",
    "little_mcp_flex_link",
    "little_proximal_phalanx_link",
    "little_proximal_inter_link",
    "little_distal_link",
    "thumb_root_connector_link",
    "thumb_metacarpal_link",
    "thumb_proximal_link",
    "thumb_distal_link",
]


def logical_link_name(path: Path) -> str:
    stem = path.stem
    if stem.lower().startswith("thumb_root_connector_link"):
        return "thumb_root_connector_link"
    return stem


def mesh_asset_name(link_name: str, part_index: int, part_count: int) -> str:
    if part_count == 1:
        return f"{link_name}_clean_mesh"
    return f"{link_name}_clean_mesh_part_{part_index}"


def mesh_geom_name(link_name: str, part_index: int, part_count: int) -> str:
    if part_count == 1:
        return f"{link_name}_clean_visual"
    return f"{link_name}_clean_visual_part_{part_index}"


def mjcf_filename(filename: str, link_name: str, digest: str) -> str:
    if MJCF_SAFE_FILENAME.match(filename):
        return filename
    return f"{link_name}_{digest[:8]}.STL"


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
        handle.read(80)
        raw_count = handle.read(4)
        if len(raw_count) != 4:
            return None
        tri_count = struct.unpack("<I", raw_count)[0]
        expected = 84 + tri_count * 50
        if expected != size:
            return None
        mins = [float("inf"), float("inf"), float("inf")]
        maxs = [float("-inf"), float("-inf"), float("-inf")]
        for _ in range(tri_count):
            record = handle.read(50)
            if len(record) != 50:
                return None
            vertices = struct.unpack("<9f", record[12:48])
            for i in range(0, 9, 3):
                for axis in range(3):
                    value = float(vertices[i + axis])
                    mins[axis] = min(mins[axis], value)
                    maxs[axis] = max(maxs[axis], value)
    return tri_count, mins, maxs


def parse_ascii_stl(path: Path) -> tuple[int, list[float], list[float]]:
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    vertex_count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) == 4 and parts[0].lower() == "vertex":
                values = [float(parts[1]), float(parts[2]), float(parts[3])]
                vertex_count += 1
                for axis, value in enumerate(values):
                    mins[axis] = min(mins[axis], value)
                    maxs[axis] = max(maxs[axis], value)
    if vertex_count == 0:
        mins = [0.0, 0.0, 0.0]
        maxs = [0.0, 0.0, 0.0]
    return vertex_count // 3, mins, maxs


def parse_stl(path: Path) -> dict:
    binary = parse_binary_stl(path)
    if binary is None:
        tri_count, mins, maxs = parse_ascii_stl(path)
        stl_format = "ascii_or_nonstandard"
    else:
        tri_count, mins, maxs = binary
        stl_format = "binary"
    span = [maxs[i] - mins[i] for i in range(3)]
    digest = sha256(path)
    link_name = logical_link_name(path)
    return {
        "filename": path.name,
        "normalized_name": path.name.lower(),
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "triangle_count": tri_count,
        "bbox_min": mins,
        "bbox_max": maxs,
        "bbox_span": span,
        "bbox_volume_estimate": span[0] * span[1] * span[2],
        "sha256": digest,
        "stl_format": stl_format,
        "link_name": path.stem,
        "logical_link_name": link_name,
        "mjcf_filename": mjcf_filename(path.name, link_name, digest),
    }


def load_suspicious_baseline() -> dict:
    baseline_path = METADATA_DIR / "suspicious_export_mesh_manifest.json"
    if not baseline_path.exists():
        return {}
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def unique_count(rows: list[dict], key: str) -> int:
    return len({row[key] for row in rows})


def find_row(rows_by_link: dict[str, list[dict]], link_name: str) -> dict | None:
    rows = rows_by_link.get(link_name.lower(), [])
    if not rows:
        return None
    return rows[0]


def evaluate(rows: list[dict]) -> dict:
    rows_by_link = defaultdict(list)
    for row in rows:
        rows_by_link[row["logical_link_name"].lower()].append(row)
    hash_groups = defaultdict(list)
    for row in rows:
        hash_groups[row["sha256"]].append(row["filename"])
    duplicate_groups = [names for names in hash_groups.values() if len(names) > 1]

    palm = find_row(rows_by_link, "palm_link")
    index_distal = find_row(rows_by_link, "index_distal_link")
    hand_base = find_row(rows_by_link, "hand_base_link")
    thumb_root_parts = rows_by_link.get("thumb_root_connector_link", [])
    oversized_rows = [
        row
        for row in rows
        if max(row["bbox_span"]) > 300.0
    ]

    unique_sizes = unique_count(rows, "size_bytes")
    unique_triangles = unique_count(rows, "triangle_count")
    expected_present = sorted(set(rows_by_link) & {name.lower() for name in EXPECTED_LINKS})
    missing_expected = sorted(name for name in EXPECTED_LINKS if name.lower() not in rows_by_link)

    special = {
        "palm_link_present": palm is not None,
        "index_distal_link_present": index_distal is not None,
        "hand_base_link_present": hand_base is not None,
        "index_distal_smaller_than_palm_by_volume": None,
        "index_distal_smaller_than_palm_by_max_span": None,
        "hand_base_not_identical_to_palm": None,
        "hand_base_not_identical_to_index_distal": None,
        "thumb_metacarpal_link_present": find_row(rows_by_link, "thumb_metacarpal_link") is not None,
        "thumb_proximal_link_present": find_row(rows_by_link, "thumb_proximal_link") is not None,
        "thumb_distal_link_present": find_row(rows_by_link, "thumb_distal_link") is not None,
        "thumb_root_connector_link_part_count": len(thumb_root_parts),
        "thumb_root_connector_link_files": [row["filename"] for row in thumb_root_parts],
        "oversized_bbox_over_300mm_count": len(oversized_rows),
        "oversized_bbox_over_300mm_files": [row["filename"] for row in oversized_rows],
    }
    if palm and index_distal:
        special["index_distal_smaller_than_palm_by_volume"] = (
            index_distal["bbox_volume_estimate"] < palm["bbox_volume_estimate"]
        )
        special["index_distal_smaller_than_palm_by_max_span"] = (
            max(index_distal["bbox_span"]) < max(palm["bbox_span"])
        )
    if hand_base and palm:
        special["hand_base_not_identical_to_palm"] = hand_base["sha256"] != palm["sha256"]
    if hand_base and index_distal:
        special["hand_base_not_identical_to_index_distal"] = hand_base["sha256"] != index_distal["sha256"]

    more_credible_than_suspicious = (
        len(rows) > 0
        and unique_sizes > 1
        and unique_triangles > 1
        and len(duplicate_groups) == 0
        and len(oversized_rows) == 0
    )
    required_specials = [
        special["palm_link_present"],
        special["index_distal_link_present"],
        special["hand_base_link_present"],
        special["index_distal_smaller_than_palm_by_volume"],
        special["hand_base_not_identical_to_palm"],
        special["hand_base_not_identical_to_index_distal"],
        special["thumb_metacarpal_link_present"],
        special["thumb_proximal_link_present"],
        special["thumb_distal_link_present"],
        special["thumb_root_connector_link_part_count"] >= 1,
    ]
    passed = (
        more_credible_than_suspicious
        and all(value is True for value in required_specials)
        and len(missing_expected) == 0
    )

    return {
        "stl_count": len(rows),
        "unique_size_count": unique_sizes,
        "unique_triangle_count": unique_triangles,
        "duplicate_hash_groups": duplicate_groups,
        "expected_present": expected_present,
        "missing_expected_links": missing_expected,
        "special_checks": special,
        "more_credible_than_suspicious_export_mesh": more_credible_than_suspicious,
        "passed": passed,
    }


def pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def direct_body_children(root: ET.Element, body_name: str) -> ET.Element | None:
    for body in root.findall(".//body"):
        if body.get("name") == body_name:
            return body
    return None


def create_clean_mesh_draft(rows: list[dict]) -> list[str]:
    if not PRIMITIVE_XML.exists():
        return []
    rows_by_link = defaultdict(list)
    for row in rows:
        if row["logical_link_name"] in EXPECTED_LINKS:
            rows_by_link[row["logical_link_name"]].append(row)
    clean_links = sorted(rows_by_link)
    tree = ET.parse(PRIMITIVE_XML)
    root = tree.getroot()
    compiler = root.find("compiler")
    if compiler is None:
        compiler = ET.Element("compiler")
        root.insert(0, compiler)
    compiler.set("meshdir", "../meshes_clean")
    asset = root.find("asset")
    if asset is None:
        asset = ET.SubElement(root, "asset")
    for link_name in clean_links:
        part_count = len(rows_by_link[link_name])
        for part_index, row in enumerate(rows_by_link[link_name], start=1):
            mesh_name = mesh_asset_name(link_name, part_index, part_count)
            if asset.find(f"mesh[@name='{mesh_name}']") is None:
                ET.SubElement(
                    asset,
                    "mesh",
                    {
                        "name": mesh_name,
                        "file": row["mjcf_filename"],
                        "scale": CLEAN_MESH_SCALE,
                    },
                )

    for link_name in clean_links:
        body = direct_body_children(root, link_name)
        if body is None:
            continue
        part_count = len(rows_by_link[link_name])
        for part_index, _row in reversed(list(enumerate(rows_by_link[link_name], start=1))):
            geom_name = mesh_geom_name(link_name, part_index, part_count)
            mesh_name = mesh_asset_name(link_name, part_index, part_count)
            existing = body.find(f"geom[@name='{geom_name}']")
            if existing is None:
                body.insert(
                    0,
                    ET.Element(
                        "geom",
                        {
                            "name": geom_name,
                            "type": "mesh",
                            "mesh": mesh_name,
                            "rgba": "0.78 0.82 0.90 1",
                            "contype": "0",
                            "conaffinity": "0",
                            "group": "2",
                        },
                    ),
                )
        body.insert(0, ET.Comment("Clean mesh visual draft; primitive geoms retained as provisional collision/reference."))
    CLEAN_DRAFT_XML.write_text(pretty_xml(root), encoding="utf-8")
    return clean_links


def copy_clean_meshes(rows: list[dict]) -> list[dict]:
    MESHES_CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for row in rows:
        src = Path(row["path"])
        dst = MESHES_CLEAN_DIR / row["mjcf_filename"]
        shutil.copy2(src, dst)
        copied.append(
            {
                "source": str(src),
                "destination": str(dst),
                "original_filename": row["filename"],
                "mjcf_filename": row["mjcf_filename"],
                "sha256": row["sha256"],
            }
        )
    return copied


def write_missing_outputs() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "clean_mesh_test_dir": str(CLEAN_TEST_DIR),
        "status": "missing_clean_mesh_test_dir",
        "passed": False,
        "reason": "The clean_mesh_test directory does not exist, so no clean STL files could be scanned.",
        "no_files_copied": True,
        "clean_mesh_draft_created": False,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Clean Mesh Test Report",
                "",
                f"- Clean mesh test directory: `{CLEAN_TEST_DIR}`",
                "- Status: missing directory",
                "- Result: not passed",
                "",
                "No STL files were scanned because the directory does not exist.",
                "",
                "Place manually re-exported per-link STL files in this directory and rerun:",
                "",
                "```powershell",
                r"python D:\tendon_project\simulations\models\hand_stage1_export\scripts\validate_clean_mesh_test.py",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    REPLACEMENT_STATUS_MD.write_text(
        "\n".join(
            [
                "# Clean Mesh Replacement Status",
                "",
                "- Status: not attempted",
                "- Reason: `clean_mesh_test` directory was not found.",
                "- No files were copied to `meshes_clean`.",
                "- `hand_stage1_clean_mesh_draft.xml` was not generated.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1


def write_reports(summary: dict) -> None:
    rows = summary["stl_files"]
    evaluation = summary["evaluation"]
    lines = [
        "# Clean Mesh Test Report",
        "",
        f"- Clean mesh test directory: `{summary['clean_mesh_test_dir']}`",
        f"- STL count: {evaluation['stl_count']}",
        f"- Unique file size count: {evaluation['unique_size_count']}",
        f"- Unique triangle count: {evaluation['unique_triangle_count']}",
        f"- Duplicate exact STL groups: {len(evaluation['duplicate_hash_groups'])}",
        f"- More credible than `suspicious_export_mesh`: {'yes' if evaluation['more_credible_than_suspicious_export_mesh'] else 'no'}",
        f"- Overall pass: {'yes' if evaluation['passed'] else 'no'}",
        "",
        "## Expected Link Coverage",
        "",
        f"- Expected clean per-link STL count: {len(EXPECTED_LINKS)}",
        f"- Present expected links: {len(evaluation['expected_present'])}",
        f"- Missing expected links: {len(evaluation['missing_expected_links'])}",
        "",
    ]
    if evaluation["missing_expected_links"]:
        lines.extend(
            [
                "Missing links:",
                "",
                *[f"- `{name}`" for name in evaluation["missing_expected_links"]],
                "",
            ]
        )
    thumb_files = evaluation["special_checks"].get("thumb_root_connector_link_files", [])
    lines.extend(
        [
            "## Thumb Mesh Mapping",
            "",
            f"- `thumb_metacarpal_link` present: {evaluation['special_checks'].get('thumb_metacarpal_link_present')}",
            f"- `thumb_proximal_link` present: {evaluation['special_checks'].get('thumb_proximal_link_present')}",
            f"- `thumb_distal_link` present: {evaluation['special_checks'].get('thumb_distal_link_present')}",
            f"- `thumb_root_connector_link` STL part count: {evaluation['special_checks'].get('thumb_root_connector_link_part_count')}",
        ]
    )
    if thumb_files:
        lines.extend(["", "Thumb root connector files mapped to `thumb_root_connector_link` body:", ""])
        lines.extend(f"- `{filename}`" for filename in thumb_files)
    lines.extend(
        [
            "",
            "## Oversize / Whole-Hand Checks",
            "",
            f"- BBox over 300 mm count: {evaluation['special_checks'].get('oversized_bbox_over_300mm_count')}",
            f"- BBox over 300 mm files: {evaluation['special_checks'].get('oversized_bbox_over_300mm_files')}",
            "",
        ]
    )
    lines.extend(
        [
        "## Per-File Diagnostics",
        "",
            "| File | MJCF file | Logical link | Size bytes | Triangles | BBox span xyz | SHA-256 prefix | Exact duplicate group |",
            "|---|---|---|---:|---:|---|---|---|",
        ]
    )
    dup_lookup = {}
    for group in evaluation["duplicate_hash_groups"]:
        label = ", ".join(group)
        for name in group:
            dup_lookup[name] = label
    for row in rows:
        span = ", ".join(f"{value:.6g}" for value in row["bbox_span"])
        lines.append(
            f"| `{row['filename']}` | `{row['mjcf_filename']}` | `{row['logical_link_name']}` | {row['size_bytes']} | {row['triangle_count']} | "
            f"`{span}` | `{row['sha256'][:16]}` | {dup_lookup.get(row['filename'], 'no')} |"
        )
    lines.extend(["", "## Special Checks", ""])
    for key, value in evaluation["special_checks"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A clean per-link export should have different file sizes, triangle counts, and bounding boxes across large and small links.",
            "- `palm_link` should be palm-sized; `index_distal_link` should be much smaller than `palm_link`; `hand_base_link` should not look identical to either.",
            "- Current suspicious exports are still not used by the primitive model.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    status_lines = [
        "# Clean Mesh Replacement Status",
        "",
        f"- Clean mesh test passed: {'yes' if evaluation['passed'] else 'no'}",
        f"- Files copied to `meshes_clean`: {len(summary.get('copied_files', []))}",
        f"- Clean mesh MJCF draft created: {'yes' if summary.get('clean_mesh_draft_created') else 'no'}",
    ]
    if summary.get("clean_mesh_draft_created"):
        status_lines.append(f"- Draft MJCF: `{CLEAN_DRAFT_XML}`")
        status_lines.append("- Only clean-test link mesh visuals were added; primitive geoms remain as provisional collision/reference.")
    else:
        status_lines.append("- No files were copied and no draft was generated because the clean STL set did not pass.")
    status_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Original suspicious STL files were not deleted or overwritten.",
            "- Joint tree and joint names were not changed.",
            "- Non-ASCII or space-containing STL filenames are copied into `meshes_clean` with deterministic ASCII-safe MJCF filenames; original source/test filenames are not changed.",
            f"- Clean mesh assets use `scale=\"{CLEAN_MESH_SCALE}\"` because the manually exported STL bounding boxes are in millimeter-like dimensions while the MJCF skeleton is in meters.",
            "- Mesh local-frame alignment is still a draft item; verify per-link origin/orientation visually before promoting these mesh geoms beyond replacement testing.",
            "- This draft is a mesh replacement check, not a training or tendon-routing change.",
            "",
        ]
    )
    REPLACEMENT_STATUS_MD.write_text("\n".join(status_lines), encoding="utf-8")


def main() -> int:
    if not CLEAN_TEST_DIR.exists():
        return write_missing_outputs()

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    # Windows globbing is case-insensitive, so "*.stl" and "*.STL" can return
    # the same file twice. Deduplicate by resolved path before hashing.
    stl_paths = sorted(
        {
            path.resolve()
            for path in CLEAN_TEST_DIR.iterdir()
            if path.is_file() and path.suffix.lower() == ".stl"
        }
    )
    rows = [parse_stl(path) for path in stl_paths]
    evaluation = evaluate(rows)
    suspicious_baseline = load_suspicious_baseline()
    copied_files = []
    clean_links_used = []
    draft_created = False
    if evaluation["passed"]:
        copied_files = copy_clean_meshes(rows)
        clean_links_used = create_clean_mesh_draft(rows)
        draft_created = CLEAN_DRAFT_XML.exists()

    summary = {
        "clean_mesh_test_dir": str(CLEAN_TEST_DIR),
        "suspicious_baseline": {
            "classification": suspicious_baseline.get("classification"),
            "unique_byte_sizes": suspicious_baseline.get("unique_byte_sizes"),
            "unique_triangle_counts": suspicious_baseline.get("unique_triangle_counts"),
        },
        "stl_files": rows,
        "evaluation": evaluation,
        "copied_files": copied_files,
        "clean_links_used_in_draft": clean_links_used,
        "clean_mesh_draft_created": draft_created,
        "passed": evaluation["passed"],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_reports(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if evaluation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
