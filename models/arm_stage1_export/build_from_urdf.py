from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco


ROOT = Path(__file__).resolve().parent
URDF_PATH = ROOT / "robot.urdf"
MJCF_PATH = ROOT / "robot.xml"

EE_TOOL_POS = "0.02175 0.01956 0.05656"
EE_TOOL_EULER = "-1.5708 0 -0.7854"


def indent(elem: ET.Element, level: int = 0) -> None:
    indent_str = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent_str + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent_str
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent_str


def compile_urdf() -> None:
    model = mujoco.MjModel.from_xml_path(str(URDF_PATH))
    mujoco.mj_saveLastXML(str(MJCF_PATH), model)


def ensure_base_link_body(root: ET.Element) -> None:
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("MJCF has no worldbody")

    base_body = worldbody.find("./body[@name='base_link']")
    if base_body is not None:
        return

    children = list(worldbody)
    base_body = ET.Element("body", {"name": "base_link"})
    for child in children:
        worldbody.remove(child)
        base_body.append(child)
    worldbody.append(base_body)


def ensure_ee_tool_frame(root: ET.Element) -> None:
    ee_mount = root.find(".//body[@name='ee_mount']")
    if ee_mount is None:
        raise RuntimeError("Could not find ee_mount body in MJCF")

    existing = ee_mount.find("./body[@name='ee_tool_frame']")
    if existing is not None:
        return

    tool_body = ET.SubElement(
        ee_mount,
        "body",
        {
            "name": "ee_tool_frame",
            "pos": EE_TOOL_POS,
            "euler": EE_TOOL_EULER,
        },
    )
    ET.SubElement(
        tool_body,
        "site",
        {
            "name": "ee_tool_frame_site",
            "pos": "0 0 0",
            "size": "0.004",
            "rgba": "1 0.5 0.2 1",
        },
    )


def patch_mjcf() -> None:
    tree = ET.parse(MJCF_PATH)
    root = tree.getroot()
    ensure_base_link_body(root)
    ensure_ee_tool_frame(root)
    indent(root)
    tree.write(MJCF_PATH, encoding="utf-8", xml_declaration=False)


if __name__ == "__main__":
    compile_urdf()
    patch_mjcf()
    print(f"Built {MJCF_PATH}")
