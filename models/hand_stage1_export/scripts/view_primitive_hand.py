from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball_primitive.xml"


def main() -> int:
    try:
        import mujoco
        import mujoco.viewer
    except Exception as exc:
        print("Failed to import mujoco or mujoco.viewer.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        return 2

    try:
        model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        data = mujoco.MjData(model)
    except Exception as exc:
        print(f"Failed to load primitive scene: {SCENE_XML}")
        print(f"Reason: {type(exc).__name__}: {exc}")
        return 1

    print(f"Loaded primitive scene: {SCENE_XML}")
    print(f"nbody={model.nbody}, njnt={model.njnt}, nq={model.nq}, nv={model.nv}, ngeom={model.ngeom}, nsite={model.nsite}")
    print("Opening MuJoCo viewer. Close the viewer window to exit.")
    try:
        mujoco.viewer.launch(model, data)
    except Exception as exc:
        print("MuJoCo viewer failed to open.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
