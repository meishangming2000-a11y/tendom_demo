from __future__ import annotations

import argparse
import json

from export3_common import HAND_XML, SCENE_XML, load_model


def summarize(xml_path):
    mujoco, model, data = load_model(xml_path)
    return {
        "xml": str(xml_path),
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nu": int(model.nu),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "nmesh": int(model.nmesh),
        "joint_names": [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
            for jid in range(model.njnt)
            if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        ],
        "actuator_names": [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
            for aid in range(model.nu)
            if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="View or summarize export3 hand MJCF.")
    parser.add_argument("--hand-only", action="store_true", help="Load hand_stage1_export3.xml instead of scene_ball_export3.xml.")
    parser.add_argument("--no-viewer", action="store_true")
    args = parser.parse_args()
    xml_path = HAND_XML if args.hand_only else SCENE_XML
    try:
        mujoco, model, data = load_model(xml_path)
    except Exception as exc:
        print(json.dumps({"load_success": False, "xml": str(xml_path), "error": f"{type(exc).__name__}: {exc}"}, indent=2, ensure_ascii=False))
        return 1
    summary = summarize(xml_path)
    summary["load_success"] = True
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.no_viewer:
        return 0
    try:
        import mujoco.viewer

        mujoco.viewer.launch(model, data)
    except Exception as exc:
        print(f"Viewer failed: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
