from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
ARCHIVE_DIR = ROOT / "archive"

SOURCE_HAND = MJCF_DIR / "hand_stage1_clean_mesh_export2_draft.xml"
SOURCE_SCENE = MJCF_DIR / "scene_ball_clean_mesh_export2_retry.xml"
OUT_HAND = MJCF_DIR / "hand_stage1_visual_clean_collision_proxy.xml"
OUT_SCENE = MJCF_DIR / "scene_ball_visual_clean_collision_proxy.xml"
COLLISION_REPORT = DOCS_DIR / "collision_proxy_design_report.md"
ACTUATOR_REPORT = DOCS_DIR / "actuator_setup_report.md"
SUMMARY_JSON = METADATA_DIR / "visual_clean_collision_proxy_summary.json"

DEFAULT_BALL_POSITION = [0.0, -0.1, 0.195]
CONTROLLED_JOINTS = [
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
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ARCHIVE_DIR / f"visual_clean_collision_proxy_pre_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, out_dir / path.name)


def actuator_kp(joint_name: str) -> float:
    if joint_name.startswith("wrist_"):
        return 5.0
    if joint_name.startswith("thumb_"):
        return 2.0
    if "_mcp_" in joint_name:
        return 3.0
    if "_pip_" in joint_name or "_dip_" in joint_name:
        return 2.0
    return 2.0


def fmt(values: list[float]) -> str:
    return " ".join(f"{value:.6g}" for value in values)


def classify_geom(geom: ET.Element) -> str:
    name = geom.get("name", "")
    if geom.get("type") == "mesh" or name.endswith("_clean_visual"):
        return "clean_visual"
    if (
        name.endswith("_marker")
        or "_marker" in name
        or name.endswith("_hub")
        or name.endswith("_base_marker")
        or name.endswith("_tip_marker")
    ):
        return "debug_marker"
    return "collision_proxy"


def rename_proxy_geom(name: str) -> str:
    replacements = [
        ("_primitive", "_collision_proxy"),
        ("_spoke", "_collision_proxy_spoke"),
        ("_ellipsoid", "_collision_proxy_ellipsoid"),
    ]
    updated = name
    for old, new in replacements:
        updated = updated.replace(old, new)
    if updated == name and not updated.endswith("_collision_proxy"):
        updated = f"{name}_collision_proxy"
    return updated


def build_hand() -> dict:
    if not SOURCE_HAND.exists():
        raise FileNotFoundError(SOURCE_HAND)
    tree = ET.parse(SOURCE_HAND)
    root = tree.getroot()
    root.set("model", "hand_stage1_visual_clean_collision_proxy")

    counts = {"clean_visual": 0, "collision_proxy": 0, "debug_marker": 0}
    proxy_rows = []
    for geom in root.findall("./worldbody//geom"):
        category = classify_geom(geom)
        counts[category] += 1
        if category == "clean_visual":
            geom.set("contype", "0")
            geom.set("conaffinity", "0")
            geom.set("group", "2")
            geom.set("rgba", "0.78 0.82 0.90 1")
        elif category == "debug_marker":
            geom.set("contype", "0")
            geom.set("conaffinity", "0")
            geom.set("group", "4")
            if "rgba" not in geom.attrib:
                geom.set("rgba", "0.20 0.55 1.0 0.55")
        else:
            old_name = geom.get("name", "")
            geom.set("name", rename_proxy_geom(old_name))
            geom.set("contype", "1")
            geom.set("conaffinity", "2")
            geom.set("condim", "3")
            geom.set("group", "3")
            geom.set("rgba", "0.16 0.90 0.58 0.34")
            geom.set("friction", geom.get("friction", "0.9 0.04 0.001"))
            proxy_rows.append(
                {
                    "source_name": old_name,
                    "proxy_name": geom.get("name"),
                    "type": geom.get("type", "sphere"),
                    "fromto": geom.get("fromto"),
                    "pos": geom.get("pos"),
                    "size": geom.get("size"),
                }
            )

    for actuator in root.findall("actuator"):
        root.remove(actuator)

    joint_ranges = {}
    for joint in root.findall(".//joint"):
        name = joint.get("name")
        if not name:
            continue
        range_text = joint.get("range", "-1 1").split()
        joint_ranges[name] = [float(range_text[0]), float(range_text[1])]

    actuator_elem = ET.Element("actuator")
    actuator_rows = []
    for joint_name in CONTROLLED_JOINTS:
        lower, upper = joint_ranges[joint_name]
        kp = actuator_kp(joint_name)
        ET.SubElement(
            actuator_elem,
            "position",
            {
                "name": f"{joint_name}_pos",
                "joint": joint_name,
                "kp": f"{kp:g}",
                "ctrllimited": "true",
                "ctrlrange": f"{lower:g} {upper:g}",
            },
        )
        actuator_rows.append({"joint": joint_name, "actuator": f"{joint_name}_pos", "kp": kp, "ctrlrange": [lower, upper]})
    root.append(actuator_elem)

    backup(OUT_HAND)
    tree.write(OUT_HAND, encoding="utf-8", xml_declaration=True)
    return {
        "source_hand": str(SOURCE_HAND),
        "output_hand": str(OUT_HAND),
        "geom_counts": counts,
        "collision_proxy_geoms": proxy_rows,
        "actuators": actuator_rows,
        "missing_controlled_joints": sorted(set(CONTROLLED_JOINTS) - set(joint_ranges)),
    }


def build_scene() -> dict:
    source = SOURCE_SCENE if SOURCE_SCENE.exists() else MJCF_DIR / "scene_ball_clean_mesh_export2_draft.xml"
    if not source.exists():
        raise FileNotFoundError(source)
    tree = ET.parse(source)
    root = tree.getroot()
    root.set("model", "hand_stage1_ball_scene_visual_clean_collision_proxy")
    include = root.find("include")
    if include is None:
        include = ET.Element("include")
        root.insert(0, include)
    include.set("file", OUT_HAND.name)
    ball = root.find(".//body[@name='ball']")
    if ball is not None:
        ball.set("pos", fmt(DEFAULT_BALL_POSITION))
        ball_geom = ball.find("geom")
        if ball_geom is not None:
            ball_geom.set("contype", "2")
            ball_geom.set("conaffinity", "1")
    ground = root.find(".//geom[@name='ground']")
    if ground is not None:
        ground.set("contype", "1")
        ground.set("conaffinity", "3")
    backup(OUT_SCENE)
    tree.write(OUT_SCENE, encoding="utf-8", xml_declaration=True)
    return {"source_scene": str(source), "output_scene": str(OUT_SCENE), "ball_position": DEFAULT_BALL_POSITION}


def load_summary() -> dict:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(OUT_SCENE.resolve()))
    return {
        "load_success": True,
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nu": int(model.nu),
        "ngeom": int(model.ngeom),
        "nmesh": int(model.nmesh),
        "nsite": int(model.nsite),
        "collision_geom_count": int(sum(1 for value in model.geom_contype if int(value) != 0)),
    }


def write_reports(summary: dict) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    hand = summary["hand"]
    scene = summary["scene"]
    load = summary.get("load", {})
    collision_lines = [
        "# Collision Proxy Design Report",
        "",
        f"- Source hand MJCF: `{hand['source_hand']}`",
        f"- Output hand MJCF: `{hand['output_hand']}`",
        f"- Output scene MJCF: `{scene['output_scene']}`",
        "- Clean STL visual geoms remain visual-only: `contype=0`, `conaffinity=0`, `group=2`.",
        "- Collision does not use STL mesh geoms.",
        "- Collision proxy uses the existing primitive skeleton geoms, renamed and marked as `group=3`.",
        "- Hand proxy collision mask is `contype=1`, `conaffinity=2`: it contacts the ball and ground, but not other hand proxy geoms.",
        "- Debug markers remain non-colliding in `group=4`.",
        "",
        "## Counts",
        "",
        f"- Clean visual geoms: {hand['geom_counts']['clean_visual']}",
        f"- Collision proxy geoms: {hand['geom_counts']['collision_proxy']}",
        f"- Debug marker geoms: {hand['geom_counts']['debug_marker']}",
        f"- Compiled collision geoms: {load.get('collision_geom_count', 'unknown')}",
        f"- Fingertip sites retained: {load.get('nsite', 'unknown')}",
        "",
        "## Proxy Source",
        "",
        "- Palm, wrist/base, long-finger phalanx, distal, and thumb segment collision proxies are inherited from the current primitive skeleton.",
        "- This is deliberate: uncertain clean CAD mesh shapes are not used as collision until body-local mesh/collision design is confirmed.",
        "- TODO: tune palm and thumb proxy shapes after SolidWorks axes and link-local frames are confirmed.",
        "",
        "## Proxy Geoms",
        "",
    ]
    for row in hand["collision_proxy_geoms"]:
        detail = row.get("fromto") or row.get("pos") or "body-local default"
        collision_lines.append(f"- `{row['proxy_name']}` type={row['type']} size=`{row.get('size')}` pose=`{detail}`")
    collision_lines.append("")
    COLLISION_REPORT.write_text("\n".join(collision_lines), encoding="utf-8")

    actuator_lines = [
        "# Actuator Setup Report",
        "",
        f"- Output hand MJCF: `{hand['output_hand']}`",
        f"- Output scene MJCF: `{scene['output_scene']}`",
        f"- Compiled actuator count: {load.get('nu', 'unknown')}",
        f"- Missing controlled joints: {', '.join(hand['missing_controlled_joints']) if hand['missing_controlled_joints'] else 'None'}",
        "",
        "## Position Actuators",
        "",
        "| Joint | Actuator | kp | ctrlrange |",
        "|---|---|---:|---|",
    ]
    for row in hand["actuators"]:
        actuator_lines.append(f"| `{row['joint']}` | `{row['actuator']}` | {row['kp']:g} | `{row['ctrlrange']}` |")
    actuator_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Wrist kp=5, MCP kp=3, PIP/DIP kp=2, thumb kp=2.",
            "- If runtime oscillation appears, lower kp before changing joint axes or limits.",
            "- Actuators are for scripted position-control smoke tests only; no tendon routing or training is introduced.",
            "",
        ]
    )
    ACTUATOR_REPORT.write_text("\n".join(actuator_lines), encoding="utf-8")


def main() -> int:
    hand = build_hand()
    scene = build_scene()
    try:
        load = load_summary()
    except Exception as exc:
        load = {"load_success": False, "error": f"{type(exc).__name__}: {exc}"}
    summary = {"hand": hand, "scene": scene, "load": load}
    write_reports(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if load.get("load_success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
