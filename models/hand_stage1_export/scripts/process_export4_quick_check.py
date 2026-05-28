from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import math
import shutil
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"D:\tendon_project\hardwares\hand\hand_export4")
EXPORT4_DIR = ROOT / "export4"
MESHES_EXPORT4_DIR = ROOT / "meshes_export4"
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
ARCHIVE_DIR = ROOT / "archive"
VIS_DIR = DOCS_DIR / "visual_checks_export4_thumb"

HAND_XML = MJCF_DIR / "hand_stage1_export4.xml"
SCENE_XML = MJCF_DIR / "scene_ball_export4.xml"
REPORT_MD = DOCS_DIR / "export4_thumb_fix_check_report.md"
SUMMARY_JSON = METADATA_DIR / "export4_thumb_fix_check.json"

BALL_POSITION = [0.0, 0.045, 0.22]

THUMB_CHAIN_CANDIDATES = [
    "thumb_root_connector_link",
    "thumb_trapezium1_link",
    "thumb_metacarpal_link",
    "thumb_proximal_link",
    "thumb_distal_link",
]

EXPECTED_THUMB_JOINTS = [
    "thumb_root_connector_fixed_joint",
    "thumb_cmc_abd_joint",
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]


def backup_if_exists(path: Path, tag: str) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = ARCHIVE_DIR / f"{tag}_{stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        shutil.copytree(path, target_dir / path.name, dirs_exist_ok=True)
    else:
        shutil.copy2(path, target_dir / path.name)


def pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def fmt(values: list[float] | np.ndarray) -> str:
    return " ".join(f"{float(value):.8g}" for value in values)


def parse_xyz(text: str | None, default: str = "0 0 0") -> list[float]:
    return [float(item) for item in (text or default).split()]


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


def mesh_uri_to_path(uri: str, package_root: Path) -> Path | None:
    if uri.startswith("package://"):
        rest = uri[len("package://") :]
        parts = rest.replace("\\", "/").split("/")
        if not parts:
            return None
        package = parts[0]
        relative = Path(*parts[1:])
        if package == "hand_export4":
            return package_root / relative
        return None
    path = Path(uri)
    if path.is_absolute():
        return path
    return package_root / path


def copy_export4() -> dict:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(SOURCE_DIR)
    backup_if_exists(EXPORT4_DIR, "export4_import_dir_pre")
    EXPORT4_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_DIR, EXPORT4_DIR, dirs_exist_ok=True)
    urdfs = sorted(EXPORT4_DIR.rglob("*.urdf"))
    mesh_dirs = [path for path in EXPORT4_DIR.rglob("*") if path.is_dir() and path.name.lower() == "meshes"]
    package_files = sorted(EXPORT4_DIR.rglob("package.xml"))
    return {
        "source_dir": str(SOURCE_DIR),
        "target_dir": str(EXPORT4_DIR),
        "urdfs": [str(path) for path in urdfs],
        "selected_urdf": str(urdfs[0]) if urdfs else None,
        "mesh_dirs": [str(path) for path in mesh_dirs],
        "selected_mesh_dir": str(mesh_dirs[0]) if mesh_dirs else None,
        "package_files": [str(path) for path in package_files],
        "package_exists": bool(package_files),
    }


def parse_urdf(urdf_path: Path) -> dict:
    robot = ET.parse(urdf_path).getroot()
    package_root = urdf_path.parents[1]
    links: dict[str, dict] = {}
    for link in robot.findall("link"):
        name = link.get("name") or ""
        visual = link.find("visual")
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
                mesh_path = mesh_uri_to_path(mesh.get("filename") or "", package_root)
                mesh_filename = mesh_path.name if mesh_path else None
            color = visual.find("./material/color")
            if color is not None and color.get("rgba"):
                rgba = color.get("rgba") or rgba
        mass = 0.01
        inertial_pos = "0 0 0"
        if inertial is not None:
            origin = inertial.find("origin")
            mass_el = inertial.find("mass")
            if origin is not None and origin.get("xyz"):
                inertial_pos = origin.get("xyz") or inertial_pos
            if mass_el is not None and mass_el.get("value"):
                try:
                    mass = float(mass_el.get("value") or mass)
                except ValueError:
                    pass
        links[name] = {
            "name": name,
            "mesh_file": mesh_filename,
            "visual_origin": visual_origin,
            "rgba": rgba,
            "mass": mass,
            "inertial_pos": inertial_pos,
        }
    joints = []
    for joint in robot.findall("joint"):
        origin = joint.find("origin")
        parent = joint.find("parent")
        child = joint.find("child")
        axis = joint.find("axis")
        limit = joint.find("limit")
        xyz = parse_xyz(origin.get("xyz") if origin is not None else None)
        joints.append(
            {
                "name": joint.get("name") or "",
                "type": joint.get("type") or "",
                "parent": parent.get("link") if parent is not None else None,
                "child": child.get("link") if child is not None else None,
                "xyz": xyz,
                "origin_norm": float(math.sqrt(sum(value * value for value in xyz))),
                "rpy": parse_xyz(origin.get("rpy") if origin is not None else None),
                "axis": axis.get("xyz") if axis is not None else "0 0 1",
                "limit": dict(limit.attrib) if limit is not None else None,
            }
        )
    return {"links": links, "joints": joints, "robot_name": robot.get("name"), "urdf_path": str(urdf_path)}


def build_tree(parsed: dict) -> dict:
    joints = parsed["joints"]
    links = parsed["links"]
    children = {joint["child"] for joint in joints if joint["child"]}
    roots = sorted(set(links) - children)
    by_parent: dict[str, list[dict]] = {}
    for joint in joints:
        by_parent.setdefault(joint["parent"], []).append(joint)
    for rows in by_parent.values():
        rows.sort(key=lambda item: item["name"])
    return {"roots": roots, "children_by_parent": by_parent}


def copy_meshes(mesh_dir: Path) -> None:
    backup_if_exists(MESHES_EXPORT4_DIR, "meshes_export4_pre")
    MESHES_EXPORT4_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(mesh_dir.glob("*.STL")):
        shutil.copy2(path, MESHES_EXPORT4_DIR / path.name)


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
    return [0.0, 0.028, 0.0]


def add_link_geoms(body: ET.Element, link_name: str, links: dict, child_joints: list[dict]) -> None:
    link_data = links[link_name]
    ET.SubElement(body, "inertial", {"pos": "0 0 0", "mass": f"{max(float(link_data['mass']), 0.001):.8g}", "diaginertia": "1e-5 1e-5 1e-5"})
    if link_data.get("mesh_file"):
        origin = link_data.get("visual_origin", {})
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_export4_visual",
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
        ET.SubElement(body, "geom", {"name": "palm_link_collision_proxy_ellipsoid", "type": "ellipsoid", "pos": "0 0.048 0.002", "size": "0.030 0.064 0.024", "rgba": "0.16 0.90 0.58 0.34", "contype": "1", "conaffinity": "2", "group": "3", "friction": "0.9 0.04 0.001"})
        return
    if link_name == "hand_base_link":
        ET.SubElement(body, "geom", {"name": f"{link_name}_collision_proxy", "type": "box", "pos": "0 0 -0.006", "size": "0.026 0.020 0.014", "rgba": "0.16 0.90 0.58 0.34", "contype": "1", "conaffinity": "2", "group": "3"})
        return
    if link_name == "wrist_middle_link":
        ET.SubElement(body, "geom", {"name": f"{link_name}_collision_proxy", "type": "capsule", "fromto": "0 -0.018 0 0 0.018 0", "size": "0.011", "rgba": "0.16 0.90 0.58 0.34", "contype": "1", "conaffinity": "2", "group": "3"})
        return
    vector = child_joints[0]["xyz"] if child_joints else distal_vector(link_name, link_data)
    if math.sqrt(sum(value * value for value in vector)) < 1e-6:
        vector = distal_vector(link_name, link_data)
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_collision_proxy",
            "type": "capsule",
            "fromto": f"0 0 0 {fmt(vector)}",
            "size": proxy_radius(link_name),
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


def default_limit(joint_name: str) -> dict[str, str]:
    if joint_name.startswith("wrist"):
        return {"lower": "-0.8", "upper": "0.8"}
    if "mcp_flex" in joint_name:
        return {"lower": "-0.5", "upper": "0.5"}
    if "mcp_abd" in joint_name:
        return {"lower": "-0.2", "upper": "1.2"}
    if "pip" in joint_name:
        return {"lower": "0", "upper": "1.57"}
    if "dip" in joint_name or "ip" in joint_name:
        return {"lower": "0", "upper": "1.2"}
    if "cmc" in joint_name:
        return {"lower": "-1.2", "upper": "1.2"}
    return {"lower": "-1", "upper": "1"}


def build_body(link_name: str, links: dict, children_by_parent: dict[str, list[dict]]) -> ET.Element:
    body = ET.Element("body", {"name": link_name})
    child_joints = children_by_parent.get(link_name, [])
    add_link_geoms(body, link_name, links, child_joints)
    for joint in child_joints:
        child_body = build_body(joint["child"], links, children_by_parent)
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
        body.append(child_body)
    return body


def actuator_kp(joint_name: str) -> str:
    if joint_name.startswith("wrist"):
        return "5"
    if "_mcp_" in joint_name:
        return "3"
    return "2"


def build_mjcf(parsed: dict, tree: dict) -> None:
    roots = tree["roots"]
    if roots != ["hand_base_link"]:
        raise RuntimeError(f"Unexpected roots: {roots}")
    mujoco = ET.Element("mujoco", {"model": "hand_stage1_export4"})
    ET.SubElement(mujoco, "compiler", {"angle": "radian", "meshdir": "../meshes_export4", "autolimits": "true"})
    ET.SubElement(mujoco, "option", {"timestep": "0.002", "gravity": "0 0 -9.81"})
    visual = ET.SubElement(mujoco, "visual")
    ET.SubElement(visual, "global", {"azimuth": "145", "elevation": "-25", "offwidth": "1280", "offheight": "900"})
    default = ET.SubElement(mujoco, "default")
    ET.SubElement(default, "joint", {"damping": "0.08", "armature": "0.0001"})
    ET.SubElement(default, "geom", {"solref": "0.01 1", "solimp": "0.9 0.95 0.001"})
    ET.SubElement(mujoco, "statistic", {"center": "0.005 0.02 0.18", "extent": "0.24"})
    asset = ET.SubElement(mujoco, "asset")
    for link_name, data in parsed["links"].items():
        if data.get("mesh_file"):
            ET.SubElement(asset, "mesh", {"name": f"{link_name}_mesh", "file": data["mesh_file"], "scale": "1 1 1"})
    worldbody = ET.SubElement(mujoco, "worldbody")
    root_body = build_body("hand_base_link", parsed["links"], tree["children_by_parent"])
    root_body.set("pos", "0 0 0.05")
    worldbody.append(root_body)
    actuator = ET.SubElement(mujoco, "actuator")
    for joint in parsed["joints"]:
        if joint["type"] != "revolute":
            continue
        limit = joint.get("limit") or default_limit(joint["name"])
        ET.SubElement(
            actuator,
            "position",
            {
                "name": f"{joint['name']}_pos",
                "joint": joint["name"],
                "kp": actuator_kp(joint["name"]),
                "ctrllimited": "true",
                "ctrlrange": f"{limit.get('lower', '0')} {limit.get('upper', '0')}",
            },
        )
    backup_if_exists(HAND_XML, "before_export4_hand")
    HAND_XML.write_text(pretty_xml(mujoco), encoding="utf-8")


def build_scene() -> None:
    scene = ET.Element("mujoco", {"model": "hand_stage1_export4_ball_scene"})
    ET.SubElement(scene, "include", {"file": HAND_XML.name})
    visual = ET.SubElement(scene, "visual")
    ET.SubElement(visual, "global", {"azimuth": "145", "elevation": "-25", "offwidth": "1280", "offheight": "900"})
    asset = ET.SubElement(scene, "asset")
    ET.SubElement(asset, "texture", {"type": "2d", "name": "ground_checker", "builtin": "checker", "rgb1": "0.18 0.20 0.22", "rgb2": "0.28 0.30 0.32", "width": "300", "height": "300"})
    ET.SubElement(asset, "material", {"name": "ground_mat", "texture": "ground_checker", "texrepeat": "4 4", "reflectance": "0.15"})
    worldbody = ET.SubElement(scene, "worldbody")
    ET.SubElement(worldbody, "light", {"pos": "0 -0.3 0.8", "dir": "0 0 -1", "directional": "true"})
    ET.SubElement(worldbody, "geom", {"name": "ground", "type": "plane", "pos": "0 0 0", "size": "0.4 0.4 0.02", "material": "ground_mat", "contype": "1", "conaffinity": "3"})
    ball = ET.SubElement(worldbody, "body", {"name": "ball", "pos": fmt(BALL_POSITION)})
    ET.SubElement(ball, "freejoint", {"name": "ball_freejoint"})
    ET.SubElement(ball, "geom", {"name": "ball_geom", "type": "sphere", "size": "0.025", "rgba": "0.95 0.23 0.18 1", "mass": "0.03", "friction": "0.8 0.05 0.001", "condim": "3", "contype": "2", "conaffinity": "1"})
    backup_if_exists(SCENE_XML, "before_export4_scene")
    SCENE_XML.write_text(pretty_xml(scene), encoding="utf-8")


def thumb_chain(parsed: dict) -> list[dict]:
    by_name = {joint["name"]: joint for joint in parsed["joints"]}
    return [by_name[name] for name in EXPECTED_THUMB_JOINTS if name in by_name]


def measure_mujoco() -> dict:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    body_positions = {}
    distances = []
    previous_name = None
    previous_pos = None
    for name in ["palm_link", *THUMB_CHAIN_CANDIDATES]:
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        if bid < 0:
            body_positions[name] = None
            continue
        pos = np.array(data.xpos[bid], dtype=float)
        body_positions[name] = pos.tolist()
        if previous_name is not None and previous_pos is not None:
            distances.append({"from": previous_name, "to": name, "distance_m": float(np.linalg.norm(pos - previous_pos))})
        previous_name = name
        previous_pos = pos
    geom_positions = {}
    for gid in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid) or ""
        if "thumb" in name:
            body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[gid]))
            geom_positions[name] = {
                "body": body,
                "xpos": np.array(data.geom_xpos[gid], dtype=float).tolist(),
                "group": int(model.geom_group[gid]),
                "type": int(model.geom_type[gid]),
            }
    return {
        "load_success": True,
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nu": int(model.nu),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "nmesh": int(model.nmesh),
        "body_positions": body_positions,
        "thumb_body_distances": distances,
        "thumb_geom_positions": geom_positions,
    }


def render_views() -> list[dict]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML.resolve()))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    cameras = {
        "thumb_root_front": {"lookat": [-0.005, 0.025, 0.135], "distance": 0.22, "azimuth": 180.0, "elevation": -25.0},
        "thumb_root_high": {"lookat": [-0.005, 0.025, 0.135], "distance": 0.22, "azimuth": 180.0, "elevation": -55.0},
        "thumb_root_side": {"lookat": [-0.005, 0.025, 0.135], "distance": 0.22, "azimuth": 95.0, "elevation": -28.0},
        "full_hand": {"lookat": [0.0, 0.02, 0.18], "distance": 0.38, "azimuth": 180.0, "elevation": -35.0},
    }
    outputs = []
    for name, cfg in cameras.items():
        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.lookat[:] = cfg["lookat"]
        camera.distance = cfg["distance"]
        camera.azimuth = cfg["azimuth"]
        camera.elevation = cfg["elevation"]
        renderer = mujoco.Renderer(model, width=1200, height=850)
        try:
            renderer.update_scene(data, camera=camera)
            image = renderer.render()
        finally:
            renderer.close()
        out = VIS_DIR / f"{name}.png"
        imageio.imwrite(out, image)
        outputs.append({"file": str(out), "camera": name, "mean_pixel": float(image.mean()), "min_pixel": int(image.min()), "max_pixel": int(image.max())})
    return outputs


def write_outputs(summary: dict) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Export4 Thumb Fix Check Report",
        "",
        f"- Source: `{SOURCE_DIR}`",
        f"- Imported to: `{EXPORT4_DIR}`",
        f"- URDF: `{summary['import']['selected_urdf']}`",
        f"- Mesh dir: `{summary['import']['selected_mesh_dir']}`",
        f"- Generated hand MJCF: `{HAND_XML}`",
        f"- Generated scene MJCF: `{SCENE_XML}`",
        "",
        "## Thumb Chain",
        "",
        "| Joint | Parent | Child | Axis | Origin xyz | Origin norm (m) | Limit |",
        "|---|---|---|---|---|---:|---|",
    ]
    for joint in summary["thumb_chain"]:
        lines.append(
            f"| `{joint['name']}` | `{joint['parent']}` | `{joint['child']}` | `{joint['axis']}` | "
            f"`{fmt(joint['xyz'])}` | {joint['origin_norm']:.6f} | `{joint.get('limit')}` |"
        )
    lines.extend(["", "## MuJoCo Load", ""])
    load = summary["mujoco"]
    lines.extend(
        [
            f"- Load success: {load.get('load_success')}",
            f"- Bodies / joints / actuators / geoms / sites / meshes: {load.get('nbody')} / {load.get('njnt')} / {load.get('nu')} / {load.get('ngeom')} / {load.get('nsite')} / {load.get('nmesh')}",
            "",
            "## Thumb Body Distances",
            "",
            "| From | To | Distance (m) |",
            "|---|---|---:|",
        ]
    )
    for item in load.get("thumb_body_distances", []):
        lines.append(f"| `{item['from']}` | `{item['to']}` | {item['distance_m']:.6f} |")
    lines.extend(["", "## Visual Renders", ""])
    for item in summary.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in summary["interpretation"])
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def interpret(summary: dict) -> list[str]:
    lines = []
    chain_names = [item["name"] for item in summary["thumb_chain"]]
    if "thumb_cmc_abd_joint" in chain_names and "thumb_cmc_joint" in chain_names:
        lines.append("Export4 keeps a 2-DoF CMC chain, but the second CMC joint is named `thumb_cmc_joint`, not `thumb_cmc_flex_joint`.")
    else:
        lines.append("Export4 thumb CMC chain is incomplete or unexpectedly named; inspect the URDF manually.")
    bad = [item for item in summary["mujoco"]["thumb_body_distances"] if item["distance_m"] > 0.08]
    if bad:
        lines.append(f"BLOCKER: at least one adjacent thumb body distance is still too large: {bad}.")
    else:
        lines.append("The previous 0.13-0.15 m thumb body separation is fixed at the body/joint level.")
    joint_by_name = {item["name"]: item for item in summary["thumb_chain"]}
    cmc = joint_by_name.get("thumb_cmc_joint")
    if cmc and cmc["origin_norm"] < 1e-5:
        lines.append("`thumb_cmc_joint` now has zero translation from `thumb_trapezium1_link` to `thumb_metacarpal_link`; visually verify whether this is intended or whether the joint center is coincident by design.")
    lines.append("Use the saved renders to decide whether thumb visual STL pieces are also attached; if visual meshes remain separated, the remaining issue is mesh-local coordinates rather than joint tree.")
    return lines


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    import_report = copy_export4()
    urdf = Path(import_report["selected_urdf"])
    mesh_dir = Path(import_report["selected_mesh_dir"])
    copy_meshes(mesh_dir)
    parsed = parse_urdf(urdf)
    tree = build_tree(parsed)
    build_mjcf(parsed, tree)
    build_scene()
    mujoco_summary = measure_mujoco()
    renders = render_views()
    summary = {
        "import": import_report,
        "thumb_chain": thumb_chain(parsed),
        "mujoco": mujoco_summary,
        "renders": renders,
    }
    summary["interpretation"] = interpret(summary)
    write_outputs(summary)
    print(json.dumps({"report": str(REPORT_MD), "summary": str(SUMMARY_JSON), "interpretation": summary["interpretation"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
