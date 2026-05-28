from __future__ import annotations

import json
import struct
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from xml.dom import minidom

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
MESHES_CLEAN_DIR = ROOT / "meshes_clean"
PRIMITIVE_XML = MJCF_DIR / "hand_stage1_primitive.xml"
CLEAN_DRAFT_XML = MJCF_DIR / "hand_stage1_clean_mesh_draft.xml"
ALIGNED_DRAFT_XML = MJCF_DIR / "hand_stage1_clean_mesh_aligned_draft.xml"
ANALYSIS_MD = DOCS_DIR / "mesh_body_transform_analysis.md"
ANALYSIS_JSON = METADATA_DIR / "mesh_body_transform_analysis.json"

SAMPLE_LINKS = {
    "hand_base_link",
    "wrist_middle_link",
    "palm_link",
    "index_mcp_flex_link",
    "index_proximal_phalanx_link",
    "index_distal_link",
    "thumb_metacarpal_link",
    "thumb_distal_link",
}


def parse_vec(text: str | None, fallback: tuple[float, ...] = (0.0, 0.0, 0.0)) -> np.ndarray:
    if not text:
        return np.array(fallback, dtype=float)
    return np.array([float(part) for part in text.split()], dtype=float)


def format_vec(values: np.ndarray) -> str:
    return " ".join(f"{float(value):.9g}" for value in values)


def pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def stl_vertices(path: Path, scale: float = 0.001) -> np.ndarray:
    data = path.read_bytes()
    if len(data) >= 84:
        tri_count = struct.unpack("<I", data[80:84])[0]
        if len(data) == 84 + tri_count * 50:
            vertices = []
            offset = 84
            for _ in range(tri_count):
                record = data[offset : offset + 50]
                offset += 50
                vals = struct.unpack("<9f", record[12:48])
                vertices.extend([vals[0:3], vals[3:6], vals[6:9]])
            return np.asarray(vertices, dtype=float) * scale

    vertices = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) == 4 and parts[0].lower() == "vertex":
                vertices.append([float(parts[1]) * scale, float(parts[2]) * scale, float(parts[3]) * scale])
    return np.asarray(vertices, dtype=float)


def bbox(values: np.ndarray) -> dict:
    mins = values.min(axis=0)
    maxs = values.max(axis=0)
    return {
        "min": mins.tolist(),
        "max": maxs.tolist(),
        "center": ((mins + maxs) * 0.5).tolist(),
        "extent": (maxs - mins).tolist(),
        "centroid": values.mean(axis=0).tolist(),
    }


def target_local_for_body(body_element: ET.Element) -> dict:
    body_name = body_element.get("name", "")
    preferred_names = [
        f"{body_name}_primitive",
        f"{body_name}_ellipsoid",
        f"{body_name}_hub",
    ]
    geoms = list(body_element.findall("geom"))
    chosen = None
    for preferred in preferred_names:
        chosen = next((geom for geom in geoms if geom.get("name") == preferred), None)
        if chosen is not None:
            break
    if chosen is None:
        chosen = next(
            (
                geom
                for geom in geoms
                if "primitive" in geom.get("name", "")
                or "ellipsoid" in geom.get("name", "")
                or geom.get("name", "").endswith("_hub")
            ),
            None,
        )
    if chosen is None:
        return {
            "geom_name": None,
            "local_center": [0.0, 0.0, 0.0],
            "local_extent": [0.0, 0.0, 0.0],
            "source": "body_origin_fallback",
        }

    if chosen.get("fromto"):
        vals = parse_vec(chosen.get("fromto"))
        start = vals[:3]
        end = vals[3:]
        radius = float(parse_vec(chosen.get("size"), (0.0,))[0])
        return {
            "geom_name": chosen.get("name"),
            "local_center": ((start + end) * 0.5).tolist(),
            "local_axis": ((end - start) / max(np.linalg.norm(end - start), 1e-12)).tolist(),
            "local_extent": (np.abs(end - start) + 2.0 * radius).tolist(),
            "source": "primitive_fromto",
        }

    local_center = parse_vec(chosen.get("pos"))
    size = parse_vec(chosen.get("size"), (0.0, 0.0, 0.0))
    geom_type = chosen.get("type")
    if geom_type in {"box", "ellipsoid"} and len(size) >= 3:
        local_extent = 2.0 * size[:3]
    elif len(size) > 0:
        local_extent = np.array([2.0 * float(size[0])] * 3)
    else:
        local_extent = np.zeros(3)
    return {
        "geom_name": chosen.get("name"),
        "local_center": local_center.tolist(),
        "local_extent": local_extent.tolist(),
        "source": f"primitive_{geom_type or 'unknown'}",
    }


def clean_geom_groups(root: ET.Element) -> dict[str, list[ET.Element]]:
    groups = defaultdict(list)
    for body in root.findall(".//body"):
        body_name = body.get("name")
        if not body_name:
            continue
        for geom in body.findall("geom"):
            if "clean_visual" in (geom.get("name") or ""):
                groups[body_name].append(geom)
    return dict(groups)


def world_bbox_for_geom(model, data, mujoco, geom_name: str) -> dict | None:
    geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
    if geom_id < 0:
        return None
    mesh_id = int(model.geom_dataid[geom_id])
    if mesh_id < 0:
        return None
    adr = int(model.mesh_vertadr[mesh_id])
    num = int(model.mesh_vertnum[mesh_id])
    vertices = model.mesh_vert[adr : adr + num]
    rotation = data.geom_xmat[geom_id].reshape(3, 3)
    world = data.geom_xpos[geom_id] + vertices @ rotation.T
    return bbox(world)


def combine_bbox(entries: list[dict]) -> dict:
    mins = np.array([entry["min"] for entry in entries], dtype=float).min(axis=0)
    maxs = np.array([entry["max"] for entry in entries], dtype=float).max(axis=0)
    centers = np.array([entry["centroid"] for entry in entries], dtype=float)
    return {
        "min": mins.tolist(),
        "max": maxs.tolist(),
        "center": ((mins + maxs) * 0.5).tolist(),
        "extent": (maxs - mins).tolist(),
        "centroid": centers.mean(axis=0).tolist(),
    }


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    import mujoco

    primitive_tree = ET.parse(PRIMITIVE_XML)
    primitive_root = primitive_tree.getroot()
    clean_tree = ET.parse(CLEAN_DRAFT_XML)
    clean_root = clean_tree.getroot()
    clean_root.set("model", "hand_stage1_clean_mesh_aligned_draft")
    clean_root.insert(
        0,
        ET.Comment(
            "TODO: Clean mesh visual geoms are translation-aligned only. "
            "Per-link CAD-to-body rotations remain unverified; final CAD mesh "
            "should come from body-local STL export or explicit per-link transforms."
        ),
    )
    mesh_file_by_name = {mesh.get("name"): mesh.get("file") for mesh in clean_root.findall(".//mesh")}
    primitive_body_by_name = {body.get("name"): body for body in primitive_root.findall(".//body") if body.get("name")}
    clean_groups = clean_geom_groups(clean_root)

    primitive_model = mujoco.MjModel.from_xml_path(str(PRIMITIVE_XML.resolve()))
    primitive_data = mujoco.MjData(primitive_model)
    mujoco.mj_forward(primitive_model, primitive_data)
    clean_model = mujoco.MjModel.from_xml_path(str(CLEAN_DRAFT_XML.resolve()))
    clean_data = mujoco.MjData(clean_model)
    mujoco.mj_forward(clean_model, clean_data)

    analysis_rows = []
    for body_name, geoms in sorted(clean_groups.items()):
        body_id_primitive = mujoco.mj_name2id(primitive_model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        body_id_clean = mujoco.mj_name2id(clean_model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if body_id_primitive < 0 or body_id_clean < 0:
            continue
        target_info = target_local_for_body(primitive_body_by_name.get(body_name, ET.Element("body")))
        target_local_center = np.array(target_info["local_center"], dtype=float)
        primitive_body_pos = primitive_data.xpos[body_id_primitive]
        primitive_body_rot = primitive_data.xmat[body_id_primitive].reshape(3, 3)
        target_world_center = primitive_body_pos + primitive_body_rot @ target_local_center

        geom_bboxes = []
        raw_mesh_rows = []
        for geom in geoms:
            geom_name = geom.get("name")
            mesh_name = geom.get("mesh")
            mesh_file = mesh_file_by_name.get(mesh_name)
            world_bbox = world_bbox_for_geom(clean_model, clean_data, mujoco, geom_name)
            if world_bbox is not None:
                geom_bboxes.append(world_bbox)
            if mesh_file:
                mesh_path = MESHES_CLEAN_DIR / mesh_file
                if mesh_path.exists():
                    raw_vertices = stl_vertices(mesh_path)
                    raw_mesh_rows.append(
                        {
                            "geom": geom_name,
                            "mesh": mesh_name,
                            "file": mesh_file,
                            "raw_mesh_bbox": bbox(raw_vertices),
                        }
                    )

        if not geom_bboxes:
            continue
        current_world_bbox = combine_bbox(geom_bboxes)
        current_world_center = np.array(current_world_bbox["center"], dtype=float)
        clean_body_rot = clean_data.xmat[body_id_clean].reshape(3, 3)
        delta_world = target_world_center - current_world_center
        delta_local = clean_body_rot.T @ delta_world
        current_distance = float(np.linalg.norm(delta_world))

        for geom in geoms:
            old_pos = parse_vec(geom.get("pos"))
            geom.set("pos", format_vec(old_pos + delta_local))
            geom.set("group", geom.get("group", "2"))

        raw_centroid_norms = [
            float(np.linalg.norm(np.array(row["raw_mesh_bbox"]["centroid"], dtype=float)))
            for row in raw_mesh_rows
        ]
        analysis_rows.append(
            {
                "body": body_name,
                "sample_link": body_name in SAMPLE_LINKS,
                "target_primitive_geom": target_info,
                "target_world_center": target_world_center.tolist(),
                "current_world_bbox": current_world_bbox,
                "translation_delta_world": delta_world.tolist(),
                "translation_delta_local_applied": delta_local.tolist(),
                "current_center_error_before_m": current_distance,
                "raw_meshes": raw_mesh_rows,
                "assembly_coordinate_like": bool(raw_centroid_norms and max(raw_centroid_norms) > 0.05),
                "alignment_method": "translation_only_to_primitive_body_main_geom_center",
                "rotation_method": "none; existing mesh/body orientation preserved",
                "todo": (
                    "Verify visually. If orientation remains wrong, CAD body-local export or known per-link CAD-to-body rotation is required."
                ),
            }
        )

    ALIGNED_DRAFT_XML.write_text(pretty_xml(clean_root), encoding="utf-8")

    summary = {
        "primitive_xml": str(PRIMITIVE_XML),
        "source_clean_draft_xml": str(CLEAN_DRAFT_XML),
        "aligned_draft_xml": str(ALIGNED_DRAFT_XML),
        "method": "center-align each clean visual mesh group to the matching primitive body's main local geometry center",
        "scale_preserved": "0.001 0.001 0.001",
        "joint_tree_changed": False,
        "joint_names_changed": False,
        "stl_files_modified": False,
        "sample_links": sorted(SAMPLE_LINKS),
        "links_aligned": [row["body"] for row in analysis_rows],
        "analysis": analysis_rows,
        "notes": [
            "This is an MJCF-only translation attempt. It does not edit CAD or STL files.",
            "The method can fix assembly/world translation offsets but cannot prove or repair unknown per-link rotations.",
            "If screenshots still show detached/rotated clean parts, SolidWorks body-local STL export is recommended.",
        ],
    }
    ANALYSIS_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def write_markdown(summary: dict) -> None:
    lines = [
        "# Mesh Body Transform Analysis",
        "",
        f"- Primitive XML: `{summary['primitive_xml']}`",
        f"- Source clean draft XML: `{summary['source_clean_draft_xml']}`",
        f"- Aligned draft XML: `{summary['aligned_draft_xml']}`",
        f"- Method: {summary['method']}",
        f"- Scale preserved: `{summary['scale_preserved']}`",
        f"- Joint tree changed: {summary['joint_tree_changed']}",
        f"- Joint names changed: {summary['joint_names_changed']}",
        f"- STL files modified: {summary['stl_files_modified']}",
        "",
        "## Interpretation",
        "",
        "- The previous clean mesh draft treated STL vertices as body-local coordinates.",
        "- The large visual offsets suggest many STL vertex clouds still contain CAD assembly/world position components.",
        "- This pass adds per-body MJCF `geom pos` translations so each clean mesh group center is moved to that body's primitive reference center.",
        "- No automatic rotation is applied because the required CAD-to-body rotations are not confirmed.",
        "",
        "## Per-Link Translation Analysis",
        "",
        "| Body | Sample | Error before m | Delta local applied | Target primitive geom | Assembly-coordinate-like |",
        "|---|---|---:|---|---|---|",
    ]
    for row in summary["analysis"]:
        delta = [round(float(value), 5) for value in row["translation_delta_local_applied"]]
        lines.append(
            f"| `{row['body']}` | {row['sample_link']} | {row['current_center_error_before_m']:.5f} | "
            f"`{delta}` | `{row['target_primitive_geom'].get('geom_name')}` | {row['assembly_coordinate_like']} |"
        )
    lines.extend(["", "## TODO / Limits", ""])
    for note in summary["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    ANALYSIS_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
