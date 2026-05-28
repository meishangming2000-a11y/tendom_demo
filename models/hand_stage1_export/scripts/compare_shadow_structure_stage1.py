from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[2]
HAND_XML = ROOT / "mjcf" / "hand_stage1_visual_clean_collision_proxy.xml"
HAND_SCENE = ROOT / "mjcf" / "scene_ball_visual_clean_collision_proxy.xml"
SHADOW_XML = PROJECT_ROOT / "simulations" / "models" / "shadow_hand" / "right_hand.xml"
SHADOW_SCENE = PROJECT_ROOT / "simulations" / "models" / "shadow_hand" / "scene_right.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
REPORT_MD = DOCS_DIR / "shadow_structure_comparison.md"
REPORT_JSON = METADATA_DIR / "shadow_structure_comparison.json"


def xml_count(path: Path, tag: str) -> int:
    if not path.exists():
        return 0
    root = ET.parse(path).getroot()
    return len(root.findall(f".//{tag}"))


def summary(path: Path) -> dict:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(path.resolve()))
    joint_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) or f"joint_{i}" for i in range(model.njnt)]
    actuator_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or f"actuator_{i}" for i in range(model.nu)]
    site_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SITE, i) or f"site_{i}" for i in range(model.nsite)]
    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    collision_count = int(sum(1 for i in range(model.ngeom) if int(model.geom_contype[i]) != 0 or int(model.geom_conaffinity[i]) != 0))
    return {
        "path": str(path),
        "load_success": True,
        "body_count_excluding_world": int(model.nbody - 1),
        "joint_count": int(model.njnt),
        "hinge_count": int(sum(1 for value in model.jnt_type if int(value) == hinge_type)),
        "actuator_count": int(model.nu),
        "tendon_count": int(model.ntendon),
        "site_count": int(model.nsite),
        "fingertip_site_count": int(sum(1 for name in site_names if "tip" in name.lower())),
        "geom_count": int(model.ngeom),
        "collision_geom_count": collision_count,
        "mesh_count": int(model.nmesh),
        "joint_names": joint_names,
        "actuator_names": actuator_names,
        "site_names": site_names,
        "xml_tendon_elements": xml_count(path, "tendon"),
        "xml_actuator_children": xml_count(path, "actuator/*"),
    }


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    hand = summary(HAND_XML)
    hand_scene = summary(HAND_SCENE)
    shadow_found = SHADOW_XML.exists()
    shadow = summary(SHADOW_XML) if shadow_found else None
    shadow_scene = summary(SHADOW_SCENE) if SHADOW_SCENE.exists() else None
    report = {
        "hand_stage1": hand,
        "hand_stage1_scene": hand_scene,
        "shadow_model_found": shadow_found,
        "shadow": shadow,
        "shadow_scene": shadow_scene,
        "conclusion": [
            "hand_stage1 is a stage1 kinematic + clean visual + simplified collision proxy prototype, not a Shadow Hand equivalent.",
            "hand_stage1 now has 21 position actuators and 5 fingertip sites, enough for scripted smoke tests.",
            "The local Shadow MJCF has more joints/actuators and a mature collision setup, but no MuJoCo tendon elements in this local XML.",
            "hand_stage1 thumb opposition remains unresolved and should be confirmed in SolidWorks/URDF before Shadow-style grasp tasks are promoted.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_markdown(report: dict) -> None:
    hand = report["hand_stage1"]
    scene = report["hand_stage1_scene"]
    shadow = report.get("shadow")
    shadow_scene = report.get("shadow_scene")
    lines = [
        "# Shadow Structure Comparison",
        "",
        f"- hand_stage1 model: `{hand['path']}`",
        f"- hand_stage1 scene: `{scene['path']}`",
        f"- Local Shadow model found: {'yes' if report['shadow_model_found'] else 'no'}",
        f"- Shadow model: `{shadow['path'] if shadow else 'not found'}`",
        "",
        "## Counts",
        "",
        "| Item | hand_stage1 | Shadow right_hand |",
        "|---|---:|---:|",
        f"| Bodies/links excluding world | {hand['body_count_excluding_world']} | {shadow['body_count_excluding_world'] if shadow else 'N/A'} |",
        f"| Joints | {hand['joint_count']} | {shadow['joint_count'] if shadow else 'N/A'} |",
        f"| Hinge joints | {hand['hinge_count']} | {shadow['hinge_count'] if shadow else 'N/A'} |",
        f"| Actuators | {hand['actuator_count']} | {shadow['actuator_count'] if shadow else 'N/A'} |",
        f"| Sites | {hand['site_count']} | {shadow['site_count'] if shadow else 'N/A'} |",
        f"| Fingertip-like sites | {hand['fingertip_site_count']} | {shadow['fingertip_site_count'] if shadow else 'N/A'} |",
        f"| Geoms | {hand['geom_count']} | {shadow['geom_count'] if shadow else 'N/A'} |",
        f"| Collision geoms | {hand['collision_geom_count']} | {shadow['collision_geom_count'] if shadow else 'N/A'} |",
        f"| Mesh assets | {hand['mesh_count']} | {shadow['mesh_count'] if shadow else 'N/A'} |",
        f"| Tendons | {hand['tendon_count']} | {shadow['tendon_count'] if shadow else 'N/A'} |",
        "",
        "## Design Comparison",
        "",
        "- hand_stage1 visual: clean SolidWorks STL meshes from export2, visual-only.",
        "- hand_stage1 collision: simplified primitive proxy geoms, not STL mesh collision.",
        "- hand_stage1 actuation: 21 MuJoCo position actuators added for smoke tests.",
        "- Shadow visual/collision: local MJCF uses mesh visuals plus many curated primitive/mesh collision geoms with collision masks.",
        "- Shadow actuation: local MJCF uses position actuators from defaults/classes.",
        "- Tendon routing: no MuJoCo tendon elements are present in either current hand_stage1 or the local Shadow right_hand XML.",
        "",
        "## Grasp Ball Readiness",
        "",
        "- hand_stage1 can run a scripted position-control ball smoke test with the low-penetration ball position.",
        "- hand_stage1 four long fingers close toward the ball; thumb opposition remains a TODO.",
        "- Shadow right_hand has enough actuators/collisions for scripted grasp experiments, but this report did not run a Shadow ball demo.",
        "",
        "## Gap",
        "",
    ]
    lines.extend(f"- {item}" for item in report["conclusion"])
    lines.extend(["", "## Notes", ""])
    if shadow:
        lines.append(f"- Shadow sites: `{', '.join(shadow['site_names']) if shadow['site_names'] else 'none'}`.")
        lines.append(f"- Shadow scene path: `{shadow_scene['path'] if shadow_scene else 'not found'}`.")
    else:
        lines.append("- 未找到本地 Shadow 模型，未联网下载。")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
