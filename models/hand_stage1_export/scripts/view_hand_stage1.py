from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball.xml"


def main() -> int:
    try:
        import mujoco
        import mujoco.viewer
    except Exception as exc:
        print("Failed to import mujoco or mujoco.viewer.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print("Possible cause: mujoco Python package/viewer dependencies are not installed.")
        return 2

    try:
        model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        data = mujoco.MjData(model)
    except Exception as exc:
        print(f"Failed to load MuJoCo scene: {SCENE_XML}")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print("Possible causes: missing mesh files, invalid MJCF, or a broken include path.")
        return 1

    print(f"Loaded {SCENE_XML}")
    print(f"nbody={model.nbody}, njnt={model.njnt}, nq={model.nq}, nv={model.nv}, ngeom={model.ngeom}")
    print("Opening MuJoCo viewer. Close the viewer window to exit.")
    try:
        mujoco.viewer.launch(model, data)
    except Exception as exc:
        print("MuJoCo viewer failed to open.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print("The model loaded successfully; this is likely a viewer/OpenGL/display issue.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
