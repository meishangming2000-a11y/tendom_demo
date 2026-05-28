from __future__ import annotations

from pathlib import Path

import numpy as np

from clean_mesh_common import render_png, set_ball_position, write_json


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
ARCHIVE_DIR = ROOT / "archive"
HAND_XML = MJCF_DIR / "hand_stage1_export3.xml"
RAW_HAND_XML = MJCF_DIR / "hand_stage1_export3_raw_mesh.xml"
SCENE_XML = MJCF_DIR / "scene_ball_export3.xml"
BALL_POSITION = [0.0, -0.1, 0.21]
BALL_RADIUS = 0.025

CONTROLLED_JOINTS = [
    "wrist_1_joint",
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
    "thumb_cmc_abd_joint",
    "thumb_cmc_flex_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]

FOUR_FINGER_JOINTS = [
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
]

THUMB_JOINTS = [
    "thumb_cmc_abd_joint",
    "thumb_cmc_flex_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]

TIP_SITES = [
    "index_tip_site",
    "middle_tip_site",
    "ring_tip_site",
    "little_tip_site",
    "thumb_tip_site",
]

STAGE_ORDER = [
    "open_hand",
    "approach_pre_shape",
    "close_four_fingers",
    "close_thumb",
    "hold",
]

STAGE_TO_FILE = {
    "open_hand": "open_hand.png",
    "approach_pre_shape": "preshape.png",
    "close_four_fingers": "four_fingers_closed.png",
    "close_thumb": "thumb_closed.png",
    "hold": "hold.png",
}

FOUR_FINGER_CLOSE_TARGETS = {
    "index_mcp_flex_joint": -0.08,
    "index_mcp_abd_joint": 0.45,
    "index_pip_joint": 0.65,
    "index_dip_joint": 0.35,
    "middle_mcp_flex_joint": 0.0,
    "middle_mcp_abd_joint": 0.5,
    "middle_pip_joint": 0.7,
    "middle_dip_joint": 0.38,
    "ring_mcp_flex_joint": 0.04,
    "ring_mcp_abd_joint": 0.5,
    "ring_pip_joint": 0.7,
    "ring_dip_joint": 0.38,
    "little_mcp_flex_joint": 0.08,
    "little_mcp_abd_joint": 0.45,
    "little_pip_joint": 0.65,
    "little_dip_joint": 0.35,
}

# Provisional export3 thumb pose. It is seeded from the 2-DoF CMC audit results
# at runtime by demo scripts when possible; keep this conservative fallback.
THUMB_CLOSE_TARGETS = {
    "thumb_cmc_abd_joint": 0.0,
    "thumb_cmc_flex_joint": 0.4,
    "thumb_mcp_joint": 0.4,
    "thumb_ip_joint": 0.2,
}


def full_stage_targets(stage_name: str) -> dict[str, float]:
    targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    if stage_name == "open_hand":
        return targets
    if stage_name == "approach_pre_shape":
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * 0.32
        for name, value in THUMB_CLOSE_TARGETS.items():
            targets[name] = value * 0.25
        return targets
    if stage_name == "close_four_fingers":
        targets.update(FOUR_FINGER_CLOSE_TARGETS)
        for name, value in THUMB_CLOSE_TARGETS.items():
            targets[name] = value * 0.25
        return targets
    if stage_name in {"close_thumb", "hold"}:
        targets.update(FOUR_FINGER_CLOSE_TARGETS)
        targets.update(THUMB_CLOSE_TARGETS)
        return targets
    raise KeyError(stage_name)


def blend(start: dict[str, float], end: dict[str, float], fraction: float) -> dict[str, float]:
    names = sorted(set(start) | set(end))
    return {
        name: float(start.get(name, 0.0)) + (float(end.get(name, 0.0)) - float(start.get(name, 0.0))) * fraction
        for name in names
    }


def load_model(xml_path: Path = SCENE_XML):
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(xml_path.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def actuator_map(model, mujoco) -> dict[str, int]:
    mapping = {}
    for aid in range(model.nu):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
        if name and name.endswith("_pos"):
            mapping[name[: -len("_pos")]] = aid
    return mapping


def joint_map(model, mujoco) -> dict[str, int]:
    return {
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid): jid
        for jid in range(model.njnt)
        if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
    }


def set_ctrl(model, data, targets: dict[str, float], act_map: dict[str, int]) -> dict[str, float]:
    applied = {}
    for name, target in targets.items():
        aid = act_map.get(name)
        if aid is None:
            continue
        low, high = [float(value) for value in model.actuator_ctrlrange[aid]]
        value = min(max(float(target), low), high)
        data.ctrl[aid] = value
        applied[name] = value
    return applied


def set_joint_qpos(model, data, joints: dict[str, int], targets: dict[str, float]) -> dict[str, float]:
    applied = {}
    for name, target in targets.items():
        jid = joints.get(name)
        if jid is None:
            continue
        adr = int(model.jnt_qposadr[jid])
        low, high = [float(value) for value in model.jnt_range[jid]]
        value = min(max(float(target), low), high)
        data.qpos[adr] = value
        applied[name] = value
    return applied


def actual_qpos(model, data, joints: dict[str, int], names: list[str] | None = None) -> dict[str, float]:
    values = {}
    for name in names or CONTROLLED_JOINTS:
        jid = joints.get(name)
        if jid is None:
            continue
        values[name] = float(data.qpos[int(model.jnt_qposadr[jid])])
    return values


def ball_contact_summary(model, data, mujoco) -> dict:
    ball_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
    contacts = []
    for cid in range(data.ncon):
        con = data.contact[cid]
        if int(con.geom1) != ball_geom and int(con.geom2) != ball_geom:
            continue
        other = int(con.geom2) if int(con.geom1) == ball_geom else int(con.geom1)
        contacts.append(
            {
                "dist": float(con.dist),
                "other_geom": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, other) or f"geom_{other}",
            }
        )
    min_dist = min((item["dist"] for item in contacts), default=0.0)
    return {
        "ball_contact_count": len(contacts),
        "max_penetration": float(max(0.0, -min_dist)),
        "ball_contacts": contacts,
    }


def fingertip_distances(model, data, mujoco) -> dict:
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    center = np.array(data.xpos[ball_body], dtype=float)
    distances = {}
    positions = {}
    for site in TIP_SITES:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site)
        if sid < 0:
            distances[site] = None
            positions[site] = None
        else:
            pos = np.array(data.site_xpos[sid], dtype=float)
            distances[site] = float(np.linalg.norm(pos - center))
            positions[site] = pos.tolist()
    four = [distances[name] for name in TIP_SITES[:4] if distances[name] is not None]
    all_tips = [value for value in distances.values() if value is not None]
    index = distances.get("index_tip_site")
    thumb = distances.get("thumb_tip_site")
    thumb_to_index = None
    if positions.get("thumb_tip_site") is not None and positions.get("index_tip_site") is not None:
        thumb_to_index = float(
            np.linalg.norm(np.array(positions["thumb_tip_site"], dtype=float) - np.array(positions["index_tip_site"], dtype=float))
        )
    return {
        "ball_center": center.tolist(),
        "distances": distances,
        "site_positions": positions,
        "mean_four_tip_distance": float(np.mean(four)) if four else None,
        "mean_all_tip_distance": float(np.mean(all_tips)) if all_tips else None,
        "thumb_to_ball": thumb,
        "index_to_ball": index,
        "thumb_to_index": thumb_to_index,
    }


def stage_summary(model, data, mujoco, joints: dict[str, int], targets: dict[str, float], applied: dict[str, float]) -> dict:
    summary = {}
    summary.update(ball_contact_summary(model, data, mujoco))
    summary.update(fingertip_distances(model, data, mujoco))
    summary["target_angles"] = dict(targets)
    summary["ctrl_applied"] = dict(applied)
    summary["qpos_actual"] = actual_qpos(model, data, joints)
    return summary
