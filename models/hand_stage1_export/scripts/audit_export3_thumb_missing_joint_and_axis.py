from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from clean_mesh_common import render_png, set_ball_position, write_json
from export3_common import BALL_POSITION, DOCS_DIR, METADATA_DIR, ROOT, joint_map, load_model, set_joint_qpos


URDF_PATH = ROOT / "export3" / "urdf" / "hand_export3.urdf"
SCENE_XML = ROOT / "mjcf" / "scene_ball_export3_thumb_limit_tuned.xml"
REPORT_MD = DOCS_DIR / "export3_thumb_missing_joint_axis_audit.md"
REPORT_JSON = METADATA_DIR / "export3_thumb_missing_joint_axis_audit.json"
OUT_DIR = DOCS_DIR / "visual_checks_export3_thumb_axis_audit"

THUMB_CHAIN_LINKS = [
    "palm_link",
    "thumb_root_connector_link",
    "thumb_trapezium1_link",
    "thumb_metacarpal_link",
    "thumb_proximal_link",
    "thumb_distal_link",
]

THUMB_JOINTS = [
    "thumb_root_connector_fixed_joint",
    "thumb_cmc_abd_joint",
    "thumb_cmc_flex_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]

ACTIVE_THUMB_JOINTS = [
    "thumb_cmc_abd_joint",
    "thumb_cmc_flex_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]


def parse_urdf() -> dict:
    root = ET.parse(URDF_PATH).getroot()
    links = [link.get("name") for link in root.findall("link")]
    children: dict[str, list[dict]] = defaultdict(list)
    joints = {}
    for joint in root.findall("joint"):
        name = joint.get("name") or ""
        parent = joint.find("parent").get("link") if joint.find("parent") is not None else None
        child = joint.find("child").get("link") if joint.find("child") is not None else None
        origin = joint.find("origin")
        axis = joint.find("axis")
        limit = joint.find("limit")
        row = {
            "name": name,
            "type": joint.get("type"),
            "parent": parent,
            "child": child,
            "origin_xyz": origin.get("xyz") if origin is not None else None,
            "origin_rpy": origin.get("rpy") if origin is not None else None,
            "axis": axis.get("xyz") if axis is not None else None,
            "limit": dict(limit.attrib) if limit is not None else None,
        }
        joints[name] = row
        children[parent].append(row)

    chain = []
    current = "palm_link"
    visited = set()
    while current and current not in visited:
        visited.add(current)
        next_rows = [row for row in children.get(current, []) if row["child"] in THUMB_CHAIN_LINKS or "thumb" in (row["child"] or "")]
        if not next_rows:
            break
        row = next_rows[0]
        chain.append(row)
        current = row["child"]

    thumb_links = [name for name in links if name and ("thumb" in name or "trapez" in name.lower())]
    thumb_joints = [
        row
        for row in joints.values()
        if "thumb" in row["name"]
        or "trapez" in row["name"].lower()
        or (row["parent"] and "thumb" in row["parent"])
        or (row["child"] and "thumb" in row["child"])
    ]
    return {
        "urdf": str(URDF_PATH),
        "thumb_links": thumb_links,
        "thumb_joints": thumb_joints,
        "chain_from_palm": chain,
        "active_thumb_joint_count": sum(1 for row in thumb_joints if row["type"] in {"revolute", "continuous"}),
        "fixed_thumb_joint_count": sum(1 for row in thumb_joints if row["type"] == "fixed"),
    }


def site_pos(model, data, mujoco, name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if sid < 0:
        raise RuntimeError(f"Missing site {name}")
    return np.array(data.site_xpos[sid], dtype=float)


def body_pos(model, data, mujoco, name: str) -> np.ndarray:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid < 0:
        raise RuntimeError(f"Missing body {name}")
    return np.array(data.xpos[bid], dtype=float)


def measure_pose(model, data, mujoco, joints: dict[str, int], targets: dict[str, float], ball_position: list[float]) -> dict:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    applied = set_joint_qpos(model, data, joints, targets)
    mujoco.mj_forward(model, data)
    thumb = site_pos(model, data, mujoco, "thumb_tip_site")
    index = site_pos(model, data, mujoco, "index_tip_site")
    middle = site_pos(model, data, mujoco, "middle_tip_site")
    palm = body_pos(model, data, mujoco, "palm_link")
    ball = body_pos(model, data, mujoco, "ball")
    return {
        "targets": dict(targets),
        "applied": applied,
        "thumb_tip": thumb.tolist(),
        "index_tip": index.tolist(),
        "middle_tip": middle.tolist(),
        "palm_pos": palm.tolist(),
        "ball_center": ball.tolist(),
        "thumb_to_ball": float(np.linalg.norm(thumb - ball)),
        "thumb_to_index": float(np.linalg.norm(thumb - index)),
        "thumb_to_middle": float(np.linalg.norm(thumb - middle)),
        "thumb_to_palm": float(np.linalg.norm(thumb - palm)),
    }


def axis_audit(ball_position: list[float], angle: float) -> dict:
    mujoco, model, data = load_model(SCENE_XML)
    model.opt.gravity[:] = 0.0
    joints = joint_map(model, mujoco)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    baseline = measure_pose(model, data, mujoco, joints, {}, ball_position)
    renders = [render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / "baseline_thumb_root.png", width=1200, height=850)]
    rows = {}
    for joint in ACTIVE_THUMB_JOINTS:
        joint_rows = {}
        for label, value in [("positive", angle), ("negative", -angle)]:
            pose = {joint: value}
            item = measure_pose(model, data, mujoco, joints, pose, ball_position)
            delta = np.array(item["thumb_tip"], dtype=float) - np.array(baseline["thumb_tip"], dtype=float)
            item["thumb_tip_delta_from_zero"] = delta.tolist()
            item["thumb_tip_delta_norm"] = float(np.linalg.norm(delta))
            item["ball_distance_delta_from_zero"] = item["thumb_to_ball"] - baseline["thumb_to_ball"]
            item["index_distance_delta_from_zero"] = item["thumb_to_index"] - baseline["thumb_to_index"]
            item["moves_thumb_toward_ball"] = bool(item["ball_distance_delta_from_zero"] < 0)
            item["moves_thumb_toward_index"] = bool(item["index_distance_delta_from_zero"] < 0)
            joint_rows[label] = item
            filename = f"{joint}_{label}_{abs(value):.2f}".replace(".", "d") + ".png"
            renders.append(render_png(model, data, mujoco, "thumb_root_closeup", OUT_DIR / filename, width=1200, height=850))
        rows[joint] = joint_rows
    return {"scene": str(SCENE_XML), "angle": angle, "baseline": baseline, "joints": rows, "renders": renders}


def write_report(payload: dict) -> None:
    write_json(REPORT_JSON, payload)
    urdf = payload["urdf_analysis"]
    axis = payload["axis_audit"]
    lines = [
        "# Export3 Thumb Missing-Joint And Axis Audit",
        "",
        "Status: diagnostic report. No CAD/STL/tree/name edits were made.",
        "",
        f"- URDF: `{urdf['urdf']}`",
        f"- MJCF scene: `{axis['scene']}`",
        f"- Axis test angle: `{axis['angle']}` rad",
        "",
        "## Actual Export3 Thumb Chain",
        "",
        "| Parent | Joint | Type | Axis | Origin xyz | Origin rpy | Child |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in urdf["chain_from_palm"]:
        lines.append(
            f"| `{row['parent']}` | `{row['name']}` | `{row['type']}` | `{row['axis']}` | `{row['origin_xyz']}` | `{row['origin_rpy']}` | `{row['child']}` |"
        )
    lines.extend(
        [
            "",
            "## Missing-Joint Finding",
            "",
            f"- Thumb-related links exported: `{urdf['thumb_links']}`",
            f"- Thumb active revolute/continuous joint count: `{urdf['active_thumb_joint_count']}`",
            f"- Thumb fixed joint count: `{urdf['fixed_thumb_joint_count']}`",
            "- Export3 has one fixed root connector plus four active thumb joints: CMC abd, CMC flex, MCP, IP.",
            "- If the real SolidWorks thumb root should contain another active joint between palm/root connector and `thumb_trapezium1_link`, it is absent from export3 URDF/MJCF.",
            "- There is no exported link between `thumb_root_connector_link` and `thumb_trapezium1_link` other than `thumb_cmc_abd_joint`.",
            "",
            "## Axis Direction Audit",
            "",
            "| Joint | + angle thumb-ball delta | - angle thumb-ball delta | + toward ball? | - toward ball? | + thumb-index delta | - thumb-index delta |",
            "|---|---:|---:|---|---|---:|---:|",
        ]
    )
    for joint, rows in axis["joints"].items():
        pos = rows["positive"]
        neg = rows["negative"]
        lines.append(
            f"| `{joint}` | {pos['ball_distance_delta_from_zero']:.6f} | {neg['ball_distance_delta_from_zero']:.6f} | "
            f"{pos['moves_thumb_toward_ball']} | {neg['moves_thumb_toward_ball']} | "
            f"{pos['index_distance_delta_from_zero']:.6f} | {neg['index_distance_delta_from_zero']:.6f} |"
        )
    lines.extend(["", "## Rendered Evidence", ""])
    for item in axis["renders"]:
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `thumb_cmc_abd_joint` is numerically reversed relative to the desired intuitive positive-opposition convention: negative angle moves the thumb toward the ball/index side.",
            "- `thumb_cmc_flex_joint` also shows direction ambiguity and should be checked in SolidWorks against the intended flexion axis.",
            "- `thumb_mcp_joint` was mechanically confirmed by the user, but export3 still needs sign convention confirmation because a negative MCP value was selected by the tuned scripted pose.",
            "- The likely missing item is not a mesh file; it is a missing active root/CMC degree of freedom or a missing exported intermediate moving link at the thumb base.",
            "- Do not fix this by more target tuning. The next correct step is SolidWorks joint/CSYS/export correction or an explicitly named experimental MJCF with axis-sign flips for visualization only.",
            "",
            "## SolidWorks / Export4 Checklist",
            "",
            "1. Confirm whether there should be an additional active thumb root joint between `thumb_root_connector_link` and `thumb_trapezium1_link`, or between `palm_link` and `thumb_root_connector_link`.",
            "2. If yes, add/export a distinct link and joint name, for example `thumb_cmc_root_joint` / `thumb_cmc_root_link` or the CAD-native name you prefer.",
            "3. Verify that `thumb_cmc_abd_joint` positive rotation should oppose toward palm/index. If so, flip the SolidWorks CSYS/axis so positive angle, not negative angle, gives opposition.",
            "4. Verify `thumb_cmc_flex_joint` positive direction in SolidWorks; current export3 range originally blocked negative values and may still have reversed sign convention.",
            "5. Re-export as export4 without overwriting export3, then rerun this audit and thumb opposition/grasp smoke tests.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit export3 thumb missing root joint and axis signs.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--angle", type=float, default=0.6)
    args = parser.parse_args()
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_missing_joint_axis_audit_no_model_edits",
        "urdf_analysis": parse_urdf(),
        "axis_audit": axis_audit([args.ball_x, args.ball_y, args.ball_z], args.angle),
    }
    write_report(payload)
    print(json.dumps({"report": str(REPORT_MD), "metadata": str(REPORT_JSON)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
