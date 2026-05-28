from __future__ import annotations

import math
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


ROOT = Path(__file__).resolve().parents[1]
URDF_PATH = ROOT / "robot.urdf"
MJCF_DIR = ROOT / "mjcf"
HAND_XML = MJCF_DIR / "hand_stage1.xml"
PRIMITIVE_XML = MJCF_DIR / "hand_stage1_primitive.xml"
MESH_DEBUG_XML = MJCF_DIR / "hand_stage1_mesh_debug.xml"
SCENE_XML = MJCF_DIR / "scene_ball.xml"
PRIMITIVE_SCENE_XML = MJCF_DIR / "scene_ball_primitive.xml"
BALL_POS = "0.01 -0.045 0.215"
BALL_RADIUS = "0.025"

FINGER_COLORS = {
    "index": "0.64 0.74 0.92 1",
    "middle": "0.62 0.82 0.72 1",
    "ring": "0.90 0.78 0.58 1",
    "little": "0.78 0.66 0.88 1",
    "thumb": "0.95 0.70 0.62 1",
}


def parse_xyz(value: str | None, default: str = "0 0 0") -> list[float]:
    return [float(item) for item in (value or default).split()]


def fmt(values: list[float]) -> str:
    return " ".join(f"{value:.8g}" for value in values)


def color_for_link(link_name: str, alpha: float = 1.0) -> str:
    for prefix, rgb_alpha in FINGER_COLORS.items():
        if link_name.startswith(prefix):
            rgb = rgb_alpha.split()[:3]
            return " ".join([*rgb, f"{alpha:.3g}"])
    return f"0.68 0.72 0.80 {alpha:.3g}"


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
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def get_link_data(robot: ET.Element) -> dict[str, dict]:
    links: dict[str, dict] = {}
    for link in robot.findall("link"):
        name = link.get("name")
        visual = link.find("visual")
        collision = link.find("collision")
        inertial = link.find("inertial")
        mesh_name = None
        rgba = "0.792 0.820 0.933 1"
        visual_origin = {"xyz": "0 0 0", "rpy": "0 0 0"}
        collision_origin = {"xyz": "0 0 0", "rpy": "0 0 0"}
        if visual is not None:
            visual_origin_element = visual.find("origin")
            if visual_origin_element is not None:
                visual_origin = visual_origin_element.attrib
            mesh = visual.find("./geometry/mesh")
            if mesh is not None and mesh.get("filename"):
                mesh_name = Path(mesh.get("filename")).name
            color = visual.find("./material/color")
            if color is not None and color.get("rgba"):
                rgba = color.get("rgba")
        if collision is not None:
            collision_origin_element = collision.find("origin")
            if collision_origin_element is not None:
                collision_origin = collision_origin_element.attrib
        mass = "0.01"
        diaginertia = "1e-5 1e-5 1e-5"
        inertial_pos = "0 0 0"
        if inertial is not None:
            origin = inertial.find("origin")
            mass_element = inertial.find("mass")
            inertia = inertial.find("inertia")
            if origin is not None and origin.get("xyz"):
                inertial_pos = origin.get("xyz")
            if mass_element is not None and mass_element.get("value"):
                mass = mass_element.get("value")
            if inertia is not None:
                diaginertia = " ".join(
                    [
                        inertia.get("ixx", "1e-5"),
                        inertia.get("iyy", "1e-5"),
                        inertia.get("izz", "1e-5"),
                    ]
                )
        links[name] = {
            "mesh_file": mesh_name,
            "rgba": rgba,
            "visual_origin": visual_origin,
            "collision_origin": collision_origin,
            "mass": mass,
            "diaginertia": diaginertia,
            "inertial_pos": inertial_pos,
        }
    return links


def get_joint_data(robot: ET.Element) -> list[dict]:
    joints = []
    for joint in robot.findall("joint"):
        origin = joint.find("origin")
        axis = joint.find("axis")
        limit = joint.find("limit")
        parent = joint.find("parent")
        child = joint.find("child")
        joints.append(
            {
                "name": joint.get("name"),
                "type": joint.get("type", "fixed"),
                "parent": parent.get("link") if parent is not None else None,
                "child": child.get("link") if child is not None else None,
                "xyz": parse_xyz(origin.get("xyz") if origin is not None else None),
                "quat": rpy_to_quat(parse_xyz(origin.get("rpy") if origin is not None else None)),
                "axis": axis.get("xyz") if axis is not None else "0 0 1",
                "limit": dict(limit.attrib) if limit is not None else None,
            }
        )
    return joints


def add_link_geoms(body: ET.Element, link_name: str, link_data: dict) -> None:
    ET.SubElement(
        body,
        "inertial",
        {
            "pos": link_data["inertial_pos"],
            "mass": link_data["mass"],
            "diaginertia": link_data["diaginertia"],
        },
    )
    mesh_asset = f"{link_name}_mesh"
    visual_origin = link_data["visual_origin"]
    collision_origin = link_data["collision_origin"]
    visual_pos = visual_origin.get("xyz", "0 0 0")
    visual_quat = fmt(rpy_to_quat(parse_xyz(visual_origin.get("rpy"))))
    collision_pos = collision_origin.get("xyz", "0 0 0")
    collision_quat = fmt(rpy_to_quat(parse_xyz(collision_origin.get("rpy"))))
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_visual",
            "type": "mesh",
            "mesh": mesh_asset,
            "pos": visual_pos,
            "quat": visual_quat,
            "rgba": link_data["rgba"],
            "contype": "0",
            "conaffinity": "0",
            "group": "2",
        },
    )
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_collision",
            "type": "mesh",
            "mesh": mesh_asset,
            "pos": collision_pos,
            "quat": collision_quat,
            "rgba": "0.35 0.42 0.55 0.18",
            "contype": "1",
            "conaffinity": "1",
            "group": "3",
            "friction": "0.8 0.04 0.001",
        },
    )


def infer_distal_vector(link_name: str, link_data: dict) -> list[float]:
    values = parse_xyz(link_data.get("inertial_pos"), default="0 0.025 0")
    length = math.sqrt(sum(value * value for value in values))
    if length > 1e-6:
        scale = 0.028 / length
        return [value * scale for value in values]
    if "thumb" in link_name:
        return [0.0, 0.025, 0.0]
    if "middle" in link_name or "ring" in link_name:
        return [0.028, 0.0, 0.0]
    return [0.0, 0.028, 0.0]


def add_skeleton_geom(body: ET.Element, link_name: str, child_joints: list[dict], link_data: dict) -> None:
    mass = max(float(link_data.get("mass") or 0.01), 0.001)
    ET.SubElement(
        body,
        "inertial",
        {
            "pos": "0 0 0",
            "mass": f"{mass:.8g}",
            "diaginertia": "1e-5 1e-5 1e-5",
        },
    )
    if link_name == "palm_link":
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_hub",
                "type": "sphere",
                "pos": "0 0 0",
                "size": "0.014",
                "rgba": "0.38 0.45 0.56 0.65",
                "contype": "0",
                "conaffinity": "0",
            },
        )
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_ellipsoid",
                "type": "ellipsoid",
                "pos": "0 0.048 0.002",
                "size": "0.030 0.064 0.024",
                "rgba": "0.42 0.50 0.62 0.50",
                "friction": "0.8 0.04 0.001",
            },
        )
        for index, joint in enumerate(child_joints):
            vector = joint["xyz"]
            if math.sqrt(sum(value * value for value in vector)) < 1e-6:
                continue
            ET.SubElement(
                body,
                "geom",
                {
                    "name": f"{link_name}_{joint['name']}_spoke",
                    "type": "capsule",
                    "fromto": f"0 0 0 {fmt(vector)}",
                    "size": "0.0055",
                    "rgba": "0.40 0.48 0.60 0.88",
                    "friction": "0.8 0.04 0.001",
                },
            )
            ET.SubElement(
                body,
                "geom",
                {
                    "name": f"{link_name}_{index}_joint_marker",
                    "type": "sphere",
                    "pos": fmt(vector),
                    "size": "0.0085",
                    "rgba": "0.78 0.84 0.94 0.95",
                    "contype": "0",
                    "conaffinity": "0",
                },
            )
        return
    if link_name == "hand_base_link":
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_primitive",
                "type": "box",
                "pos": "0 0 -0.006",
                "size": "0.026 0.020 0.014",
                "rgba": "0.36 0.40 0.48 1",
                "friction": "0.8 0.04 0.001",
            },
        )
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_axis_marker",
                "type": "capsule",
                "fromto": "0 0 -0.020 0 0 0.020",
                "size": "0.006",
                "rgba": "0.58 0.64 0.74 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )
        return
    if link_name == "wrist_middle_link":
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_primitive",
                "type": "capsule",
                "fromto": "0 -0.018 0 0 0.018 0",
                "size": "0.011",
                "rgba": "0.48 0.54 0.64 1",
                "friction": "0.8 0.04 0.001",
            },
        )
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{link_name}_joint_marker",
                "type": "sphere",
                "pos": "0 0 0",
                "size": "0.007",
                "rgba": "0.72 0.78 0.88 0.85",
                "contype": "0",
                "conaffinity": "0",
            },
        )
        return

    vector = child_joints[0]["xyz"] if child_joints else infer_distal_vector(link_name, link_data)
    if math.sqrt(sum(value * value for value in vector)) < 1e-6:
        vector = [0.0, 0.025, 0.0]
    radius = "0.0072"
    if "mcp_flex" in link_name or "root_connector" in link_name:
        radius = "0.0058"
    if "distal" in link_name:
        radius = "0.0062"
    if link_name.startswith("thumb"):
        radius = "0.0068"
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_primitive",
            "type": "capsule",
            "fromto": f"0 0 0 {fmt(vector)}",
            "size": radius,
            "rgba": color_for_link(link_name, 1.0),
            "friction": "0.9 0.04 0.001",
        },
    )
    if link_name.endswith("_distal_link"):
        prefix = link_name.removesuffix("_distal_link")
        ET.SubElement(
            body,
            "site",
            {
                "name": f"{prefix}_tip_site",
                "pos": fmt(vector),
                "size": "0.008",
                "rgba": "0.10 0.55 1.0 1",
                "type": "sphere",
            },
        )
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_base_marker",
            "type": "sphere",
            "pos": "0 0 0",
            "size": radius,
            "rgba": "0.78 0.83 0.91 0.9",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    ET.SubElement(
        body,
        "geom",
        {
            "name": f"{link_name}_tip_marker",
            "type": "sphere",
            "pos": fmt(vector),
            "size": radius,
            "rgba": "0.78 0.83 0.91 0.9",
            "contype": "0",
            "conaffinity": "0",
        },
    )


def build_body(link_name: str, children_by_parent: dict[str, list[dict]], links: dict[str, dict]) -> ET.Element:
    body = ET.Element("body", {"name": link_name})
    add_link_geoms(body, link_name, links[link_name])
    for joint in children_by_parent.get(link_name, []):
        child_body = build_body(joint["child"], children_by_parent, links)
        child_body.set("pos", fmt(joint["xyz"]))
        child_body.set("quat", fmt(joint["quat"]))
        if joint["type"] == "revolute":
            attrs = {
                "name": joint["name"],
                "type": "hinge",
                "axis": joint["axis"],
                "damping": "0.05",
                "armature": "0.0001",
            }
            if joint["limit"]:
                attrs["limited"] = "true"
                attrs["range"] = f"{joint['limit'].get('lower', '0')} {joint['limit'].get('upper', '0')}"
            child_body.insert(0, ET.Element("joint", attrs))
        elif joint["type"] != "fixed":
            child_body.insert(
                0,
                ET.Comment(f"TODO: unsupported URDF joint type {joint['type']} from {joint['name']}"),
            )
        body.append(child_body)
    return body


def build_skeleton_body(link_name: str, children_by_parent: dict[str, list[dict]], links: dict[str, dict]) -> ET.Element:
    body = ET.Element("body", {"name": link_name})
    child_joints = children_by_parent.get(link_name, [])
    add_skeleton_geom(body, link_name, child_joints, links[link_name])
    for joint in child_joints:
        child_body = build_skeleton_body(joint["child"], children_by_parent, links)
        child_body.set("pos", fmt(joint["xyz"]))
        child_body.set("quat", fmt(joint["quat"]))
        if joint["type"] == "revolute":
            attrs = {
                "name": joint["name"],
                "type": "hinge",
                "axis": joint["axis"],
                "damping": "0.08",
                "armature": "0.0001",
            }
            if joint["limit"]:
                attrs["limited"] = "true"
                attrs["range"] = f"{joint['limit'].get('lower', '0')} {joint['limit'].get('upper', '0')}"
            child_body.insert(0, ET.Element("joint", attrs))
        elif joint["type"] != "fixed":
            child_body.insert(
                0,
                ET.Comment(f"TODO: unsupported URDF joint type {joint['type']} from {joint['name']}"),
            )
        body.append(child_body)
    return body


def build_common_tree(robot: ET.Element) -> tuple[dict[str, dict], dict[str, list[dict]], list[str]]:
    links = get_link_data(robot)
    joints = get_joint_data(robot)
    children = [joint["child"] for joint in joints if joint["child"]]
    root_links = sorted(set(links) - set(children))
    if len(root_links) != 1:
        raise RuntimeError(f"Expected one root link, found {root_links}")
    children_by_parent: dict[str, list[dict]] = {}
    order = {
        "wrist_1_joint": 10,
        "wrist_2_joint": 20,
        "index_mcp_flex_joint": 100,
        "middle_mcp_flex_joint": 200,
        "ring_mcp_flex_joint": 300,
        "little_mcp_flex_joint": 400,
        "thumb_root_connector_fixed_joint": 500,
    }
    for joint in joints:
        children_by_parent.setdefault(joint["parent"], []).append(joint)
    for parent_children in children_by_parent.values():
        parent_children.sort(key=lambda item: (order.get(item["name"], 10_000), item["name"]))
    return links, children_by_parent, root_links


def build_hand_xml() -> None:
    robot = ET.parse(URDF_PATH).getroot()
    links, children_by_parent, root_links = build_common_tree(robot)

    mujoco = ET.Element("mujoco", {"model": "hand_stage1"})
    ET.SubElement(
        mujoco,
        "compiler",
        {
            "angle": "radian",
            "meshdir": "../meshes",
            "autolimits": "true",
        },
    )
    ET.SubElement(mujoco, "option", {"timestep": "0.002", "gravity": "0 0 -9.81"})
    default = ET.SubElement(mujoco, "default")
    ET.SubElement(default, "joint", {"damping": "0.05", "armature": "0.0001"})
    ET.SubElement(default, "geom", {"solref": "0.01 1", "solimp": "0.9 0.95 0.001"})
    ET.SubElement(
        mujoco,
        "statistic",
        {"center": "0.005 -0.045 0.18", "extent": "0.24"},
    )

    asset = ET.SubElement(mujoco, "asset")
    ET.SubElement(asset, "material", {"name": "stage1_blue", "rgba": "0.792 0.820 0.933 1"})
    ET.SubElement(asset, "material", {"name": "ball_mat", "rgba": "0.95 0.23 0.18 1"})
    for link_name, link_data in links.items():
        if not link_data["mesh_file"]:
            continue
        ET.SubElement(
            asset,
            "mesh",
            {"name": f"{link_name}_mesh", "file": link_data["mesh_file"]},
        )

    worldbody = ET.SubElement(mujoco, "worldbody")
    root_body = build_body(root_links[0], children_by_parent, links)
    root_body.set("pos", "0 0 0.05")
    root_body.insert(0, ET.Comment("TODO: base pose is provisional for stage1 visualization."))
    worldbody.append(root_body)
    MESH_DEBUG_XML.write_text(pretty_xml(mujoco), encoding="utf-8")

    skeleton = ET.Element("mujoco", {"model": "hand_stage1_primitive"})
    ET.SubElement(skeleton, "compiler", {"angle": "radian", "autolimits": "true"})
    ET.SubElement(skeleton, "option", {"timestep": "0.002", "gravity": "0 0 -9.81"})
    default = ET.SubElement(skeleton, "default")
    ET.SubElement(default, "joint", {"damping": "0.08", "armature": "0.0001"})
    ET.SubElement(default, "geom", {"solref": "0.01 1", "solimp": "0.9 0.95 0.001"})
    ET.SubElement(skeleton, "statistic", {"center": "0.005 -0.045 0.18", "extent": "0.24"})
    worldbody = ET.SubElement(skeleton, "worldbody")
    root_body = build_skeleton_body(root_links[0], children_by_parent, links)
    root_body.set("pos", "0 0 0.05")
    root_body.insert(0, ET.Comment("TODO: primitive geoms are provisional because exported STL meshes are not clean per-link visuals."))
    worldbody.append(root_body)
    primitive_text = pretty_xml(skeleton)
    PRIMITIVE_XML.write_text(primitive_text, encoding="utf-8")
    HAND_XML.write_text(primitive_text, encoding="utf-8")


def build_scene_xml() -> None:
    scene = ET.Element("mujoco", {"model": "hand_stage1_ball_scene_primitive"})
    ET.SubElement(scene, "include", {"file": "hand_stage1_primitive.xml"})
    visual = ET.SubElement(scene, "visual")
    ET.SubElement(visual, "global", {"azimuth": "145", "elevation": "-25", "offwidth": "1280", "offheight": "900"})
    asset = ET.SubElement(scene, "asset")
    ET.SubElement(
        asset,
        "texture",
        {
            "type": "2d",
            "name": "ground_checker",
            "builtin": "checker",
            "rgb1": "0.18 0.20 0.22",
            "rgb2": "0.28 0.30 0.32",
            "width": "300",
            "height": "300",
        },
    )
    ET.SubElement(
        asset,
        "material",
        {"name": "ground_mat", "texture": "ground_checker", "texrepeat": "4 4", "reflectance": "0.15"},
    )
    worldbody = ET.SubElement(scene, "worldbody")
    ET.SubElement(worldbody, "light", {"pos": "0 -0.3 0.8", "dir": "0 0 -1", "directional": "true"})
    ET.SubElement(worldbody, "light", {"pos": "-0.25 0.25 0.5"})
    ET.SubElement(
        worldbody,
        "geom",
        {
            "name": "ground",
            "type": "plane",
            "pos": "0 0 0",
            "size": "0.4 0.4 0.02",
            "material": "ground_mat",
            "contype": "1",
            "conaffinity": "1",
        },
    )
    ball_body = ET.SubElement(worldbody, "body", {"name": "ball", "pos": BALL_POS})
    ET.SubElement(ball_body, "freejoint", {"name": "ball_freejoint"})
    ET.SubElement(
        ball_body,
        "geom",
        {
            "name": "ball_geom",
            "type": "sphere",
            "size": BALL_RADIUS,
            "rgba": "0.95 0.23 0.18 1",
            "mass": "0.03",
            "friction": "0.8 0.05 0.001",
            "condim": "3",
        },
    )
    ET.SubElement(
        worldbody,
        "camera",
        {
            "name": "front",
            "pos": "0.20 -0.34 0.29",
            "xyaxes": "0.834219 0.551433 0 -0.16379 0.247785 0.954869",
            "fovy": "45",
        },
    )
    ET.SubElement(
        worldbody,
        "camera",
        {
            "name": "side",
            "pos": "0.34 0.02 0.24",
            "xyaxes": "-0.190477 0.981692 0 -0.169999 -0.0329848 0.984892",
            "fovy": "45",
        },
    )
    ET.SubElement(
        worldbody,
        "camera",
        {
            "name": "top",
            "pos": "0.02 -0.06 0.48",
            "xyaxes": "0.707107 0.707107 0 -0.705346 0.705346 0.0705346",
            "fovy": "45",
        },
    )
    scene_text = pretty_xml(scene)
    PRIMITIVE_SCENE_XML.write_text(scene_text, encoding="utf-8")
    SCENE_XML.write_text(scene_text, encoding="utf-8")


def main() -> None:
    MJCF_DIR.mkdir(parents=True, exist_ok=True)
    build_hand_xml()
    build_scene_xml()
    print(f"wrote {PRIMITIVE_XML}")
    print(f"wrote {HAND_XML}")
    print(f"wrote {MESH_DEBUG_XML}")
    print(f"wrote {PRIMITIVE_SCENE_XML}")
    print(f"wrote {SCENE_XML}")


if __name__ == "__main__":
    main()
