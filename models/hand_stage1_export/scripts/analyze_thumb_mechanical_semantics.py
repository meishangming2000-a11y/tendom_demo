from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from clean_mesh_common import set_ball_position, write_json


ROOT = Path(__file__).resolve().parents[1]
URDF = ROOT / "robot.urdf"
MJCF = ROOT / "mjcf" / "hand_stage1_visual_clean_collision_proxy.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
REPORT_MD = DOCS_DIR / "thumb_mechanical_semantics_report.md"
REPORT_JSON = METADATA_DIR / "thumb_mechanical_semantics.json"
BALL_POSITION = [0.0, -0.1, 0.195]
THUMB_CHAIN = [
    ("thumb_root_connector_fixed_joint", "palm_link", "thumb_root_connector_link"),
    ("thumb_cmc_joint", "thumb_root_connector_link", "thumb_metacarpal_link"),
    ("thumb_mcp_joint", "thumb_metacarpal_link", "thumb_proximal_link"),
    ("thumb_ip_joint", "thumb_proximal_link", "thumb_distal_link"),
]
THUMB_HINGES = ["thumb_cmc_joint", "thumb_mcp_joint", "thumb_ip_joint"]


def parse_urdf() -> dict:
    if not URDF.exists():
        return {"exists": False, "path": str(URDF), "joints": {}}
    root = ET.parse(URDF).getroot()
    joints = {}
    for joint in root.findall("joint"):
        name = joint.get("name")
        if not name:
            continue
        parent = joint.find("parent")
        child = joint.find("child")
        axis = joint.find("axis")
        origin = joint.find("origin")
        joints[name] = {
            "type": joint.get("type"),
            "parent": parent.get("link") if parent is not None else None,
            "child": child.get("link") if child is not None else None,
            "axis": axis.get("xyz") if axis is not None else None,
            "origin_xyz": origin.get("xyz") if origin is not None else None,
            "origin_rpy": origin.get("rpy") if origin is not None else None,
        }
    return {"exists": True, "path": str(URDF), "joints": joints}


def parse_mjcf_tree() -> dict:
    root = ET.parse(MJCF).getroot()
    body_parent = {}
    body_pos_quat = {}
    joint_rows = {}

    def visit(body: ET.Element, parent_name: str | None) -> None:
        name = body.get("name")
        if not name:
            return
        body_parent[name] = parent_name
        body_pos_quat[name] = {"pos": body.get("pos", "0 0 0"), "quat": body.get("quat", "1 0 0 0")}
        for joint in body.findall("joint"):
            joint_rows[joint.get("name")] = {
                "type": joint.get("type", "hinge"),
                "parent_body": parent_name,
                "child_body": name,
                "axis_local": joint.get("axis"),
                "range": joint.get("range"),
            }
        for child in body.findall("body"):
            visit(child, name)

    for top in root.findall("./worldbody/body"):
        visit(top, None)

    if "thumb_root_connector_fixed_joint" not in joint_rows and body_parent.get("thumb_root_connector_link") == "palm_link":
        joint_rows["thumb_root_connector_fixed_joint"] = {
            "type": "fixed_implicit_body_parent",
            "parent_body": "palm_link",
            "child_body": "thumb_root_connector_link",
            "axis_local": None,
            "range": None,
        }
    return {"body_parent": body_parent, "body_pos_quat": body_pos_quat, "joints": joint_rows}


def load_model():
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(MJCF.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def name_id(mujoco, model, obj, name: str) -> int:
    return int(mujoco.mj_name2id(model, obj, name))


def set_joint(model, data, mujoco, joint_name: str, value: float) -> None:
    jid = name_id(mujoco, model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    adr = int(model.jnt_qposadr[jid])
    low, high = [float(v) for v in model.jnt_range[jid]]
    data.qpos[adr] = min(max(value, low), high)


def reset_pose(model, data, mujoco) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    set_ball_position(model, data, mujoco, BALL_POSITION)


def vector_metrics(delta: np.ndarray, target_vector: np.ndarray) -> dict:
    delta_norm = float(np.linalg.norm(delta))
    target_norm = float(np.linalg.norm(target_vector))
    if delta_norm <= 1e-12 or target_norm <= 1e-12:
        return {"dot": 0.0, "cosine": None, "projected_delta": 0.0}
    cosine = float(np.dot(delta, target_vector) / (delta_norm * target_norm))
    projection = float(np.dot(delta, target_vector / target_norm))
    return {"dot": float(np.dot(delta, target_vector)), "cosine": cosine, "projected_delta": projection}


def kinematic_audit() -> dict:
    mujoco, model, data = load_model()
    reset_pose(model, data, mujoco)
    mujoco.mj_forward(model, data)

    thumb_site = name_id(mujoco, model, mujoco.mjtObj.mjOBJ_SITE, "thumb_tip_site")
    index_site = name_id(mujoco, model, mujoco.mjtObj.mjOBJ_SITE, "index_tip_site")
    palm_body = name_id(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    ball_body = -1

    baseline_thumb = np.array(data.site_xpos[thumb_site], dtype=float)
    baseline_index = np.array(data.site_xpos[index_site], dtype=float)
    baseline_palm = np.array(data.xpos[palm_body], dtype=float)
    ball_center = np.array(BALL_POSITION, dtype=float)

    baseline = {
        "thumb_tip": baseline_thumb.tolist(),
        "index_tip": baseline_index.tolist(),
        "palm_pos": baseline_palm.tolist(),
        "ball_center": ball_center.tolist(),
        "thumb_to_ball": float(np.linalg.norm(baseline_thumb - ball_center)),
        "thumb_to_index": float(np.linalg.norm(baseline_thumb - baseline_index)),
        "thumb_to_palm": float(np.linalg.norm(baseline_thumb - baseline_palm)),
    }

    rows = []
    for joint_name in THUMB_HINGES:
        jid = name_id(mujoco, model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        low, high = [float(v) for v in model.jnt_range[jid]]
        step = min(0.2, max(0.05, high - 0.0)) if high > 0 else -0.2
        if joint_name == "thumb_cmc_joint":
            step = 0.2
        reset_pose(model, data, mujoco)
        set_joint(model, data, mujoco, joint_name, step)
        mujoco.mj_forward(model, data)
        pos_pos = np.array(data.site_xpos[thumb_site], dtype=float)

        reset_pose(model, data, mujoco)
        neg_step = -0.2 if low < 0 else 0.0
        if neg_step != 0.0:
            set_joint(model, data, mujoco, joint_name, neg_step)
        mujoco.mj_forward(model, data)
        pos_neg = np.array(data.site_xpos[thumb_site], dtype=float)

        reset_pose(model, data, mujoco)
        mujoco.mj_forward(model, data)
        try:
            world_axis = data.xaxis[jid].tolist()
        except Exception:
            world_axis = None

        delta_pos = pos_pos - baseline_thumb
        delta_neg = pos_neg - baseline_thumb
        toward_ball = ball_center - baseline_thumb
        toward_index = baseline_index - baseline_thumb
        toward_palm = baseline_palm - baseline_thumb

        rows.append(
            {
                "joint": joint_name,
                "range": [low, high],
                "axis_local": model.jnt_axis[jid].tolist(),
                "axis_world_at_zero": world_axis,
                "positive_test_angle": step,
                "positive_thumb_tip": pos_pos.tolist(),
                "positive_delta": delta_pos.tolist(),
                "positive_delta_norm": float(np.linalg.norm(delta_pos)),
                "positive_thumb_to_ball": float(np.linalg.norm(pos_pos - ball_center)),
                "positive_thumb_to_index": float(np.linalg.norm(pos_pos - baseline_index)),
                "positive_thumb_to_palm": float(np.linalg.norm(pos_pos - baseline_palm)),
                "positive_distance_changes": {
                    "ball": float(np.linalg.norm(pos_pos - ball_center) - baseline["thumb_to_ball"]),
                    "index": float(np.linalg.norm(pos_pos - baseline_index) - baseline["thumb_to_index"]),
                    "palm": float(np.linalg.norm(pos_pos - baseline_palm) - baseline["thumb_to_palm"]),
                },
                "positive_alignment": {
                    "toward_ball": vector_metrics(delta_pos, toward_ball),
                    "toward_index": vector_metrics(delta_pos, toward_index),
                    "toward_palm": vector_metrics(delta_pos, toward_palm),
                },
                "negative_test_angle": neg_step,
                "negative_thumb_tip": pos_neg.tolist(),
                "negative_delta": delta_neg.tolist(),
                "negative_distance_changes": {
                    "ball": float(np.linalg.norm(pos_neg - ball_center) - baseline["thumb_to_ball"]),
                    "index": float(np.linalg.norm(pos_neg - baseline_index) - baseline["thumb_to_index"]),
                    "palm": float(np.linalg.norm(pos_neg - baseline_palm) - baseline["thumb_to_palm"]),
                },
            }
        )
    return {"model": str(MJCF), "ball_position": BALL_POSITION, "baseline": baseline, "joint_motion": rows}


def infer_likely_issue(audit: dict) -> list[str]:
    rows = audit["joint_motion"]
    lines = []
    best_ball = min(rows, key=lambda row: row["positive_distance_changes"]["ball"])
    if all(row["positive_distance_changes"]["ball"] >= -0.01 for row in rows):
        lines.append("Positive motion of each individual thumb joint does not move thumb_tip_site meaningfully toward the ball.")
    else:
        lines.append(f"{best_ball['joint']} has the strongest positive single-joint improvement toward the ball.")
    mcp = next(row for row in rows if row["joint"] == "thumb_mcp_joint")
    cmc = next(row for row in rows if row["joint"] == "thumb_cmc_joint")
    if abs(cmc["positive_distance_changes"]["ball"]) < abs(mcp["positive_distance_changes"]["ball"]):
        lines.append("thumb_mcp_joint flexion changes thumb-to-ball distance more than thumb_cmc_joint, which is suspicious for an opposition DOF.")
    lines.append("Most likely issue to inspect first: thumb_cmc_joint axis/body frame, because CMC should provide the main opposition sweep.")
    lines.append("Do not automatically flip axes from this report; confirm axis/csys in SolidWorks/URDF first.")
    return lines


def write_markdown(report: dict) -> None:
    lines = [
        "# Thumb Mechanical Semantics Report",
        "",
        f"- MJCF: `{report['mjcf']['path']}`",
        f"- URDF: `{report['urdf']['path']}`",
        f"- Ball position used for audit: `{report['kinematic_audit']['ball_position']}`",
        "",
        "## Expected Thumb Chain",
        "",
        "| Joint | Expected parent | Expected child | URDF parent/child/type | MJCF parent/child/type | Status |",
        "|---|---|---|---|---|---|",
    ]
    for joint, expected_parent, expected_child in THUMB_CHAIN:
        urdf = report["urdf"]["joints"].get(joint, {})
        mjcf = report["mjcf"]["joints"].get(joint, {})
        urdf_text = f"{urdf.get('parent')} -> {urdf.get('child')} ({urdf.get('type')})" if urdf else "missing"
        mjcf_text = f"{mjcf.get('parent_body')} -> {mjcf.get('child_body')} ({mjcf.get('type')})" if mjcf else "missing"
        ok_parent = (urdf.get("parent") in (None, expected_parent) or not urdf) and mjcf.get("parent_body") == expected_parent
        ok_child = (urdf.get("child") in (None, expected_child) or not urdf) and mjcf.get("child_body") == expected_child
        status = "OK" if ok_parent and ok_child else "CHECK"
        lines.append(f"| `{joint}` | `{expected_parent}` | `{expected_child}` | `{urdf_text}` | `{mjcf_text}` | {status} |")

    lines.extend(
        [
            "",
            "## Joint Axes And Positive Motion",
            "",
            "| Joint | Local axis | World axis at zero | +angle | delta thumb tip | delta dist to ball | delta dist to index | delta dist to palm |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["kinematic_audit"]["joint_motion"]:
        lines.append(
            f"| `{row['joint']}` | `{row['axis_local']}` | `{row['axis_world_at_zero']}` | {row['positive_test_angle']:.3f} | "
            f"{row['positive_delta_norm']:.6f} | {row['positive_distance_changes']['ball']:.6f} | "
            f"{row['positive_distance_changes']['index']:.6f} | {row['positive_distance_changes']['palm']:.6f} |"
        )

    lines.extend(["", "## Baseline Distances", ""])
    base = report["kinematic_audit"]["baseline"]
    lines.append(f"- thumb to ball: {base['thumb_to_ball']:.6f} m")
    lines.append(f"- thumb to index: {base['thumb_to_index']:.6f} m")
    lines.append(f"- thumb to palm: {base['thumb_to_palm']:.6f} m")

    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in report["interpretation"])
    lines.extend(
        [
            "",
            "## TODO",
            "",
            "- Verify `thumb_cmc_axis` and `thumb_cmc_csys` in SolidWorks first.",
            "- Verify whether the CMC joint has enough modeled DOF for opposition, or if one axis is missing in stage1.",
            "- Verify that the thumb root connector body frame is not rotated so the CMC axis points along the wrong local direction.",
            "- Keep joint names and axes unchanged until the CAD/URDF semantics are confirmed.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    urdf = parse_urdf()
    mjcf = parse_mjcf_tree()
    kinematic = kinematic_audit()
    report = {
        "urdf": urdf,
        "mjcf": {"path": str(MJCF), **mjcf},
        "kinematic_audit": kinematic,
        "interpretation": infer_likely_issue(kinematic),
    }
    write_json(REPORT_JSON, report)
    write_markdown(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
