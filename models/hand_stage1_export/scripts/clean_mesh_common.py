from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MJCF_DIR = ROOT / "mjcf"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
VISUAL_CHECK_DIR = DOCS_DIR / "visual_checks"
CLEAN_DRAFT_XML = MJCF_DIR / "hand_stage1_clean_mesh_draft.xml"
CLEAN_SCENE_XML = MJCF_DIR / "scene_ball_clean_mesh_draft.xml"
BALL_POSITION = [0.01, -0.045, 0.215]
BALL_RADIUS = 0.025


def ensure_dirs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    VISUAL_CHECK_DIR.mkdir(parents=True, exist_ok=True)


def load_model(xml_path: Path):
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(xml_path.resolve()))
    data = mujoco.MjData(model)
    return mujoco, model, data


def model_summary(model) -> dict:
    return {
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "nmesh": int(model.nmesh),
        "nu": int(model.nu),
        "ncam": int(model.ncam),
    }


def mesh_files_from_draft() -> list[dict]:
    if not CLEAN_DRAFT_XML.exists():
        return []
    tree = ET.parse(CLEAN_DRAFT_XML)
    rows = []
    for mesh in tree.findall(".//mesh"):
        rows.append(
            {
                "name": mesh.get("name"),
                "file": mesh.get("file"),
                "scale": mesh.get("scale"),
            }
        )
    return rows


def joint_map(model, mujoco) -> dict[str, int]:
    return {
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid): jid
        for jid in range(model.njnt)
        if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
    }


def set_ball_position(model, data, mujoco, position: list[float]) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
    if joint_id < 0:
        return
    adr = int(model.jnt_qposadr[joint_id])
    data.qpos[adr : adr + 3] = position
    data.qpos[adr + 3 : adr + 7] = [1.0, 0.0, 0.0, 0.0]


def clamp_to_joint_range(model, jid: int, value: float) -> float:
    lower, upper = [float(v) for v in model.jnt_range[jid]]
    return min(max(float(value), lower), upper)


def apply_targets(model, data, mujoco, targets: dict[str, float]) -> dict[str, float]:
    mapping = joint_map(model, mujoco)
    applied = {}
    for name, target in targets.items():
        jid = mapping.get(name)
        if jid is None:
            continue
        adr = int(model.jnt_qposadr[jid])
        value = clamp_to_joint_range(model, jid, target)
        data.qpos[adr] = value
        applied[name] = value
    return applied


def render_png(model, data, mujoco, camera: str, output: Path, width: int = 1100, height: int = 800) -> dict:
    import imageio.v2 as imageio

    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=width, height=height)
    try:
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "camera": camera,
        "shape": list(image.shape),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
        "mean_pixel": float(image.mean()),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
