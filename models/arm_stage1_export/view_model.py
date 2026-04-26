from __future__ import annotations

import argparse
import math
import time
import tkinter as tk
from pathlib import Path
from queue import Empty, SimpleQueue
from typing import Callable

import glfw
import mujoco
import mujoco.viewer


ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "scene.xml"
DEFAULT_DURATION = 0.0
DEMO_SPEED = 1.2
UI_PERIOD_MS = 16
HOTKEY_HELP = "Hotkeys in viewer: H home | 0 zero | D demo | 1 overview | 2 side | 3 free | Esc close"
ACTUATOR_DEMO = {
    "a_j1": (0.35, 0.0),
    "a_j2": (0.22, 0.8),
    "a_j3": (-0.22, 1.6),
    "a_j4": (0.30, 2.4),
}
CAMERA_OPTIONS = (
    ("Overview", "arm_overview"),
    ("Side", "arm_side"),
    ("Free", None),
)


def obj_names(model: mujoco.MjModel, obj_type: mujoco.mjtObj, count: int) -> list[str]:
    names: list[str] = []
    for idx in range(count):
        name = mujoco.mj_id2name(model, obj_type, idx)
        names.append(name if name is not None else f"<unnamed_{idx}>")
    return names


def reset_to_home(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    if home_id >= 0:
        mujoco.mj_resetDataKeyframe(model, data, home_id)
    else:
        mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)


def clamp_ctrl(model: mujoco.MjModel, actuator_id: int, target: float) -> float:
    if model.actuator_ctrllimited[actuator_id]:
        low, high = model.actuator_ctrlrange[actuator_id]
        return min(max(target, low), high)
    return target


def default_targets(model: mujoco.MjModel) -> list[float]:
    targets = [0.0] * model.nu
    home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")
    if home_id >= 0 and model.nu > 0:
        for actuator_id in range(model.nu):
            targets[actuator_id] = float(model.key_ctrl[home_id, actuator_id])
    return targets


def print_summary(model: mujoco.MjModel, model_label: str) -> None:
    joints = obj_names(model, mujoco.mjtObj.mjOBJ_JOINT, model.njnt)
    actuators = obj_names(model, mujoco.mjtObj.mjOBJ_ACTUATOR, model.nu)
    bodies = obj_names(model, mujoco.mjtObj.mjOBJ_BODY, model.nbody)

    print(f"Loaded model: {model_label}")
    print(f"Joints ({len(joints)}): {', '.join(joints)}")
    print(f"Actuators ({len(actuators)}): {', '.join(actuators) if actuators else '(none)'}")
    print(f"Bodies ({len(bodies)}): {', '.join(bodies)}")


def run_check(model_path: Path, demo: bool) -> None:
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    reset_to_home(model, data)

    for step in range(240):
        if demo and model.nu > 0:
            for actuator_id in range(model.nu):
                name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_id)
                amplitude, phase = ACTUATOR_DEMO.get(name, (0.0, 0.0))
                data.ctrl[actuator_id] = clamp_ctrl(
                    model, actuator_id, amplitude * math.sin(DEMO_SPEED * step * model.opt.timestep + phase)
                )
        mujoco.mj_step(model, data)

    print_summary(model, model_path.name)
    print("Headless check passed.")


class InteractiveViewerApp:
    def __init__(self, model_path: Path, start_demo: bool, duration: float, show_right_ui: bool) -> None:
        self.model_path = model_path
        self.duration = duration
        self.show_right_ui = show_right_ui
        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        self.data = mujoco.MjData(self.model)
        reset_to_home(self.model, self.data)

        self.manual_targets = default_targets(self.model)
        self.demo_enabled = start_demo
        self.start_time = 0.0
        self.running = True
        self.command_queue: SimpleQueue[tuple[str, str | None]] = SimpleQueue()
        self.viewer: mujoco.viewer.Handle | None = None

        self.root = tk.Tk()
        self.root.title("arm_stage1_export controls")
        self.root.geometry("460x340")
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)

        self.status_var = tk.StringVar(value="Ready")
        self.camera_var = tk.StringVar(value="Free")
        self.demo_var = tk.StringVar()
        self.slider_vars: dict[int, tk.DoubleVar] = {}
        self.target_vars: dict[int, tk.StringVar] = {}
        self.qpos_vars: dict[int, tk.StringVar] = {}
        self.steps_per_tick = max(1, int(round(max(UI_PERIOD_MS / 1000.0, self.model.opt.timestep) / self.model.opt.timestep)))
        self.camera_labels = {label for label, _ in CAMERA_OPTIONS}

        self.build_panel()
        self.update_demo_status()

    def build_panel(self) -> None:
        root = self.root
        root.columnconfigure(0, weight=1)

        info = tk.Label(root, text=HOTKEY_HELP, justify="left", wraplength=430, anchor="w")
        info.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        top_bar = tk.Frame(root)
        top_bar.grid(row=1, column=0, sticky="ew", padx=10)
        for idx in range(5):
            top_bar.columnconfigure(idx, weight=1)

        tk.Button(top_bar, text="Home", command=self.reset_home_pose).grid(row=0, column=0, sticky="ew", padx=2)
        tk.Button(top_bar, text="Zero", command=self.zero_targets).grid(row=0, column=1, sticky="ew", padx=2)
        tk.Button(top_bar, textvariable=self.demo_var, command=self.toggle_demo).grid(row=0, column=2, sticky="ew", padx=2)

        camera_menu = tk.OptionMenu(top_bar, self.camera_var, *[label for label, _ in CAMERA_OPTIONS], command=self.select_camera)
        camera_menu.grid(row=0, column=3, sticky="ew", padx=2)

        tk.Button(top_bar, text="Quit", command=self.request_close).grid(row=0, column=4, sticky="ew", padx=2)

        slider_frame = tk.LabelFrame(root, text="Joint Targets")
        slider_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        root.rowconfigure(2, weight=1)
        slider_frame.columnconfigure(1, weight=1)

        if self.model.nu == 0:
            tk.Label(slider_frame, text="No actuators found in this model.").grid(row=0, column=0, sticky="w", padx=8, pady=8)
            return

        for actuator_id in range(self.model.nu):
            actuator_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_id) or f"actuator_{actuator_id}"
            low, high = (-1.0, 1.0)
            if self.model.actuator_ctrllimited[actuator_id]:
                low, high = self.model.actuator_ctrlrange[actuator_id]

            slider_var = tk.DoubleVar(value=self.manual_targets[actuator_id])
            target_var = tk.StringVar(value=f"target {self.manual_targets[actuator_id]:+.3f}")
            qpos_var = tk.StringVar(value="qpos +0.000")
            self.slider_vars[actuator_id] = slider_var
            self.target_vars[actuator_id] = target_var
            self.qpos_vars[actuator_id] = qpos_var

            row = actuator_id * 2
            tk.Label(slider_frame, text=actuator_name, width=8, anchor="w").grid(row=row, column=0, sticky="w", padx=(8, 4), pady=(6, 0))
            resolution = max((float(high) - float(low)) / 400.0, 0.001)
            slider = tk.Scale(
                slider_frame,
                from_=float(low),
                to=float(high),
                resolution=resolution,
                orient="horizontal",
                showvalue=False,
                variable=slider_var,
                command=lambda value, aid=actuator_id: self.on_slider(aid, value),
            )
            slider.grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=(6, 0))

            readout = tk.Frame(slider_frame)
            readout.grid(row=row + 1, column=1, sticky="ew", padx=(0, 8), pady=(0, 2))
            tk.Label(readout, textvariable=target_var, anchor="w").pack(side="left")
            tk.Label(readout, textvariable=qpos_var, anchor="e").pack(side="right")

        status_bar = tk.Label(root, textvariable=self.status_var, anchor="w")
        status_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

    def actuator_joint_name(self, actuator_id: int) -> str:
        joint_id = int(self.model.actuator_trnid[actuator_id, 0])
        if joint_id < 0:
            return "-"
        name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
        return name if name is not None else "-"

    def actuator_qpos(self, actuator_id: int) -> float:
        joint_id = int(self.model.actuator_trnid[actuator_id, 0])
        if joint_id < 0:
            return 0.0
        qpos_addr = int(self.model.jnt_qposadr[joint_id])
        return float(self.data.qpos[qpos_addr])

    def update_demo_status(self) -> None:
        self.demo_var.set("Demo On" if self.demo_enabled else "Demo Off")

    def sync_sliders(self) -> None:
        for actuator_id, slider_var in self.slider_vars.items():
            slider_var.set(self.manual_targets[actuator_id])

    def reset_home_pose(self) -> None:
        self.demo_enabled = False
        reset_to_home(self.model, self.data)
        self.manual_targets = default_targets(self.model)
        self.sync_sliders()
        self.update_demo_status()
        self.status_var.set("Reset to home keyframe")

    def zero_targets(self) -> None:
        self.demo_enabled = False
        for actuator_id in range(self.model.nu):
            self.manual_targets[actuator_id] = clamp_ctrl(self.model, actuator_id, 0.0)
        self.sync_sliders()
        self.update_demo_status()
        self.status_var.set("All actuator targets set to zero")

    def toggle_demo(self) -> None:
        self.demo_enabled = not self.demo_enabled
        self.update_demo_status()
        self.status_var.set("Demo motion enabled" if self.demo_enabled else "Manual slider control enabled")

    def on_slider(self, actuator_id: int, value: str) -> None:
        self.demo_enabled = False
        self.update_demo_status()
        target = clamp_ctrl(self.model, actuator_id, float(value))
        self.manual_targets[actuator_id] = target
        self.target_vars[actuator_id].set(f"target {target:+.3f}")
        self.status_var.set(f"{self.actuator_joint_name(actuator_id)} target -> {target:+.3f}")

    def set_camera(self, label: str) -> None:
        if self.viewer is None:
            return

        camera_name = dict(CAMERA_OPTIONS).get(label)
        if camera_name is None:
            self.viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            self.viewer.cam.fixedcamid = -1
            self.status_var.set("Camera -> Free")
            return

        cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
        if cam_id >= 0:
            self.viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
            self.viewer.cam.fixedcamid = cam_id
            self.status_var.set(f"Camera -> {label}")
        else:
            self.status_var.set(f"Camera {label} not found in model")

    def select_camera(self, label: str) -> None:
        if label not in self.camera_labels:
            return
        self.set_camera(label)

    def enqueue_hotkey(self, action: str, value: str | None = None) -> None:
        self.command_queue.put((action, value))

    def on_viewer_key(self, keycode: int) -> None:
        if keycode == glfw.KEY_H:
            self.enqueue_hotkey("home")
        elif keycode == glfw.KEY_0:
            self.enqueue_hotkey("zero")
        elif keycode == glfw.KEY_D:
            self.enqueue_hotkey("demo")
        elif keycode == glfw.KEY_1:
            self.enqueue_hotkey("camera", "Overview")
        elif keycode == glfw.KEY_2:
            self.enqueue_hotkey("camera", "Side")
        elif keycode == glfw.KEY_3:
            self.enqueue_hotkey("camera", "Free")
        elif keycode == glfw.KEY_ESCAPE:
            self.enqueue_hotkey("quit")

    def handle_hotkeys(self) -> None:
        while True:
            try:
                action, value = self.command_queue.get_nowait()
            except Empty:
                break

            if action == "home":
                self.reset_home_pose()
            elif action == "zero":
                self.zero_targets()
            elif action == "demo":
                self.toggle_demo()
            elif action == "camera" and value is not None:
                self.camera_var.set(value)
                self.set_camera(value)
            elif action == "quit":
                self.request_close()

    def apply_targets(self, elapsed: float) -> None:
        if self.model.nu == 0:
            return

        if self.demo_enabled:
            for actuator_id in range(self.model.nu):
                actuator_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_id)
                amplitude, phase = ACTUATOR_DEMO.get(actuator_name, (0.0, 0.0))
                self.data.ctrl[actuator_id] = clamp_ctrl(
                    self.model, actuator_id, amplitude * math.sin(DEMO_SPEED * elapsed + phase)
                )
        else:
            for actuator_id in range(self.model.nu):
                self.data.ctrl[actuator_id] = self.manual_targets[actuator_id]

    def update_readouts(self) -> None:
        for actuator_id in range(self.model.nu):
            if actuator_id in self.target_vars:
                self.target_vars[actuator_id].set(f"target {float(self.data.ctrl[actuator_id]):+.3f}")
            if actuator_id in self.qpos_vars:
                self.qpos_vars[actuator_id].set(f"qpos {self.actuator_qpos(actuator_id):+.3f}")

    def tick(self) -> None:
        if not self.running:
            return
        if self.viewer is None or not self.viewer.is_running():
            self.request_close()
            return

        self.handle_hotkeys()

        elapsed = time.time() - self.start_time
        if self.duration > 0 and elapsed >= self.duration:
            self.request_close()
            return

        self.apply_targets(elapsed)
        for _ in range(self.steps_per_tick):
            mujoco.mj_step(self.model, self.data)
        self.update_readouts()
        self.viewer.sync()

        if self.demo_enabled:
            self.status_var.set("Demo motion enabled")

        self.root.after(UI_PERIOD_MS, self.tick)

    def request_close(self) -> None:
        self.running = False
        try:
            self.root.quit()
        except tk.TclError:
            return

    def run(self) -> None:
        print_summary(self.model, self.model_path.name)
        print(HOTKEY_HELP)
        print("Control panel: drag sliders for j1-j4 targets, or use Home / Zero / Demo buttons.")

        with mujoco.viewer.launch_passive(
            self.model,
            self.data,
            key_callback=self.on_viewer_key,
            show_left_ui=False,
            show_right_ui=self.show_right_ui,
        ) as viewer:
            self.viewer = viewer
            self.start_time = time.time()
            self.set_camera(self.camera_var.get())
            self.root.after(0, self.tick)
            try:
                self.root.mainloop()
            finally:
                self.running = False
                self.viewer = None
                try:
                    self.root.destroy()
                except tk.TclError:
                    pass


def launch_simple_viewer(model_path: Path, demo: bool, duration: float) -> None:
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    reset_to_home(model, data)
    print_summary(model, model_path.name)
    print("Viewer controls: mouse to orbit, wheel to zoom, right panel to inspect bodies/joints.")
    if demo:
        print("Demo motion enabled.")

    start_time = time.time()
    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        viewer.cam.fixedcamid = -1

        while viewer.is_running():
            elapsed = time.time() - start_time
            if duration > 0 and elapsed >= duration:
                break

            if demo and model.nu > 0:
                for actuator_id in range(model.nu):
                    actuator_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_id)
                    amplitude, phase = ACTUATOR_DEMO.get(actuator_name, (0.0, 0.0))
                    data.ctrl[actuator_id] = clamp_ctrl(model, actuator_id, amplitude * math.sin(DEMO_SPEED * elapsed + phase))

            mujoco.mj_step(model, data)
            viewer.sync()
            time.sleep(max(model.opt.timestep, 0.01))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize the arm_stage1_export MuJoCo model.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="scene.xml or robot.xml to load")
    parser.add_argument("--demo", action="store_true", help="start with a small showcase motion")
    parser.add_argument("--check-only", action="store_true", help="load and step the model without opening a viewer")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help="seconds to keep the viewer open; 0 means until closed")
    parser.add_argument("--simple", action="store_true", help="open the old plain MuJoCo viewer without the control panel")
    parser.add_argument("--hide-right-ui", action="store_true", help="hide MuJoCo's built-in right UI panel")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = args.model.resolve()
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if args.check_only:
        run_check(model_path, args.demo)
        return

    if args.simple:
        launch_simple_viewer(model_path, args.demo, args.duration)
        return

    app = InteractiveViewerApp(
        model_path=model_path,
        start_demo=args.demo,
        duration=args.duration,
        show_right_ui=not args.hide_right_ui,
    )
    app.run()


if __name__ == "__main__":
    main()
