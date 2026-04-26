import argparse
import importlib
from pathlib import Path

import mujoco


ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "scene.xml"
HOME_QPOS = [0.0, 0.0, 0.0, 0.0]
HOME_CTRL = [0.0, 0.0, 0.0, 0.0]
TARGETS = {
    "j1": 0.35,
    "j2": 0.25,
    "j3": -0.25,
    "j4": 0.35,
}


def load_model(path: Path) -> mujoco.MjModel:
    return mujoco.MjModel.from_xml_path(str(path))


def list_names(model: mujoco.MjModel) -> None:
    joints = [model.joint(i).name for i in range(model.njnt)]
    actuators = [model.actuator(i).name for i in range(model.nu)]
    print("joints:", joints)
    print("actuators:", actuators)


def reset_home(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    key_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    if key_id >= 0:
        mujoco.mj_resetDataKeyframe(model, data, key_id)
    else:
        data.qpos[:] = HOME_QPOS
        if model.nu:
            data.ctrl[:] = HOME_CTRL
        data.qvel[:] = 0
        data.act[:] = 0
    mujoco.mj_forward(model, data)


def run_single_test(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    joint_name: str,
    actuator_name: str,
    target: float,
    viewer=None,
) -> None:
    reset_home(model, data)
    act_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name)
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    qpos_adr = model.jnt_qposadr[joint_id]

    data.ctrl[:] = HOME_CTRL
    data.ctrl[act_id] = target

    print(f"testing actuator={actuator_name} joint={joint_name} target={target:.4f}")
    for _ in range(250):
        mujoco.mj_step(model, data)
        if viewer is not None:
            viewer.sync()

    actual = float(data.qpos[qpos_adr])
    print(f"result joint={joint_name} target={target:.4f} actual_qpos={actual:.4f}")


def run_tests(model_path: Path, with_viewer: bool) -> None:
    model = load_model(model_path)
    data = mujoco.MjData(model)
    list_names(model)

    actuator_map = {
        "j1": "a_j1",
        "j2": "a_j2",
        "j3": "a_j3",
        "j4": "a_j4",
    }

    if with_viewer:
        try:
            viewer_mod = importlib.import_module("mujoco.viewer")
        except Exception as exc:  # pragma: no cover
            print(f"viewer unavailable, falling back to headless: {exc}")
            with_viewer = False
            viewer_mod = None
    else:
        viewer_mod = None

    if with_viewer:
        with viewer_mod.launch_passive(model, data) as viewer:
            for joint_name, actuator_name in actuator_map.items():
                run_single_test(
                    model,
                    data,
                    joint_name,
                    actuator_name,
                    TARGETS[joint_name],
                    viewer=viewer,
                )
    else:
        for joint_name, actuator_name in actuator_map.items():
            run_single_test(
                model,
                data,
                joint_name,
                actuator_name,
                TARGETS[joint_name],
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    args = parser.parse_args()
    run_tests(Path(args.model), with_viewer=args.viewer)


if __name__ == "__main__":
    main()
