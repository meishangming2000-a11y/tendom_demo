from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[2]
HAND_XML = ROOT / "mjcf" / "hand_stage1.xml"
HAND_MESH_DEBUG_XML = ROOT / "mjcf" / "hand_stage1_mesh_debug.xml"
SHADOW_XML = PROJECT / "simulations" / "models" / "shadow_hand" / "right_hand.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"


def model_summary(path: Path) -> dict:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(path))
    joint_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid) or f"joint_{jid}"
        for jid in range(model.njnt)
    ]
    actuator_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid) or f"actuator_{aid}"
        for aid in range(model.nu)
    ]
    site_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SITE, sid) or f"site_{sid}"
        for sid in range(model.nsite)
    ]
    fingertip_sites = [name for name in site_names if "tip" in name.lower()]
    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    return {
        "path": str(path),
        "load_success": True,
        "body_count_excluding_world": int(model.nbody - 1),
        "joint_count": int(model.njnt),
        "hinge_count": int(sum(1 for value in model.jnt_type if int(value) == hinge_type)),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "actuator_count": int(model.nu),
        "tendon_count": int(model.ntendon),
        "geom_count": int(model.ngeom),
        "collision_geom_count": int(sum(1 for value in model.geom_contype if int(value) != 0)),
        "mesh_asset_count": int(model.nmesh),
        "site_count": int(model.nsite),
        "site_names": site_names,
        "fingertip_sites": fingertip_sites,
        "joint_names": joint_names,
        "actuator_names": actuator_names,
    }


def xml_counts(path: Path) -> dict:
    if not path.exists():
        return {}
    root = ET.parse(path).getroot()
    return {
        "xml_body_elements": len(root.findall(".//body")),
        "xml_joint_elements": len(root.findall(".//joint")),
        "xml_geom_elements": len(root.findall(".//geom")),
        "xml_site_elements": len(root.findall(".//site")),
        "xml_actuator_children": len(root.findall(".//actuator/*")),
        "xml_tendon_children": len(root.findall(".//tendon/*")),
    }


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    hand = model_summary(HAND_XML)
    hand_mesh_debug = model_summary(HAND_MESH_DEBUG_XML) if HAND_MESH_DEBUG_XML.exists() else None
    shadow_found = SHADOW_XML.exists()
    shadow = model_summary(SHADOW_XML) if shadow_found else None

    comparison = {
        "hand_stage1": hand,
        "hand_stage1_mesh_debug": hand_mesh_debug,
        "shadow_model_found": shadow_found,
        "shadow": shadow,
        "shadow_xml_counts": xml_counts(SHADOW_XML) if shadow_found else {},
        "conclusions": [
            "hand_stage1 is currently a stage1 geometry/kinematics skeleton, not a Shadow Hand equivalent.",
            "Default hand_stage1 MJCF uses primitive geoms for inspection because raw exported STL link meshes are not suitable for clean per-link visualization.",
            "Shadow has position actuators and a mature collision setup; hand_stage1 has no actuators, no tendons, and no fingertip sites yet.",
            "The current hand_stage1 scene can run a visual scripted ball-wrap demo, but it is not a stable grasp task.",
        ],
        "next_steps": [
            "Fix or re-export per-link mesh geometry from SolidWorks/SW2URDF.",
            "Review joint axes and limits, especially possible mcp_flex/mcp_abd semantic reversal.",
            "Add fingertip sites.",
            "Add clean collision geoms.",
            "Add actuators and a simple controller.",
            "Only then consider imitating Shadow-style grasp tasks.",
        ],
    }
    (METADATA_DIR / "shadow_comparison.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# Shadow Comparison Report",
        "",
        f"- Local Shadow model found: {'yes' if shadow_found else 'no'}",
        f"- Shadow model path: `{SHADOW_XML if shadow_found else 'not found'}`",
        "",
        "## Structure Counts",
        "",
        "| Item | hand_stage1 | Shadow Hand |",
        "|---|---:|---:|",
        f"| Links/bodies | {hand['body_count_excluding_world']} | {shadow['body_count_excluding_world'] if shadow else 'N/A'} |",
        f"| Joints | {hand['joint_count']} | {shadow['joint_count'] if shadow else 'N/A'} |",
        f"| Hinge/revolute joints | {hand['hinge_count']} | {shadow['hinge_count'] if shadow else 'N/A'} |",
        f"| Sites | {hand['site_count']} | {shadow['site_count'] if shadow else 'N/A'} |",
        f"| Fingertip sites | {len(hand['fingertip_sites'])} | {len(shadow['fingertip_sites']) if shadow else 'N/A'} |",
        f"| Actuators | {hand['actuator_count']} | {shadow['actuator_count'] if shadow else 'N/A'} |",
        f"| Tendons | {hand['tendon_count']} | {shadow['tendon_count'] if shadow else 'N/A'} |",
        f"| Collision geoms | {hand['collision_geom_count']} | {shadow['collision_geom_count'] if shadow else 'N/A'} |",
        f"| Mesh assets | {hand['mesh_asset_count']} | {shadow['mesh_asset_count'] if shadow else 'N/A'} |",
        "",
        "## Grasp Ball Demo Readiness",
        "",
        "- hand_stage1: can load in MuJoCo as a primitive stage1 skeleton, can run joint smoke tests, and can show a scripted visual ball-wrap pose.",
        "- hand_stage1 raw mesh debug: loads, but exported STL visuals are not clean per-link meshes and produce duplicated geometry during articulation.",
        "- Shadow Hand: local model has actuators and collision geoms and is closer to a real grasp-task baseline.",
        "",
        "## Gap Summary",
        "",
    ]
    lines.extend(f"- {item}" for item in comparison["conclusions"])
    lines.extend(["", "## Required Next Steps", ""])
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(comparison["next_steps"], 1))
    lines.extend(["", "## Notes", ""])
    if shadow:
        fingertip_text = ", ".join(shadow["fingertip_sites"]) if shadow["fingertip_sites"] else "none named with `tip`"
        lines.append(f"- Shadow site names: {', '.join(shadow['site_names']) if shadow['site_names'] else 'none'}. Fingertip-like sites: {fingertip_text}.")
        lines.append("- Local Shadow XML uses actuators; no explicit MuJoCo tendon elements were found in the compiled model.")
    else:
        lines.append("- 未找到本地 Shadow 模型；未下载，也未联网。")
    lines.append("")
    (DOCS_DIR / "shadow_comparison_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
