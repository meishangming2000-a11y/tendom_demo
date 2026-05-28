from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from export3_common import (
    BALL_POSITION,
    CONTROLLED_JOINTS,
    DOCS_DIR,
    FOUR_FINGER_CLOSE_TARGETS,
    METADATA_DIR,
    SCENE_XML,
    STAGE_TO_FILE,
    THUMB_CLOSE_TARGETS,
    THUMB_JOINTS,
    actuator_map,
    blend,
    joint_map,
    load_model,
    render_png,
    set_ball_position,
    set_ctrl,
    stage_summary,
    write_json,
)


REPORT_MD = DOCS_DIR / "export3_shadow_style_scripted_report.md"
REPORT_JSON = METADATA_DIR / "export3_shadow_style_scripted_trials.json"
OUT_DIR = DOCS_DIR / "visual_checks_export3_shadow_style"
THUMB_AUDIT_JSON = METADATA_DIR / "export3_thumb_opposition_candidates.json"

BALL_SWEEP = [
    [0.0, -0.1, 0.21],
    [0.0, -0.1, 0.195],
    [0.01, -0.1, 0.21],
    [-0.01, -0.1, 0.21],
    [0.0, -0.09, 0.21],
]
FINGER_SCALES = [0.85, 1.0, 1.15]
MODES = ["pinned", "free_zero_g", "free_gravity"]
STAGE_ORDER = ["open_hand", "preshape", "close_four_fingers", "close_thumb", "hold"]


@dataclass(frozen=True)
class TrialConfig:
    mode: str
    ball_position: tuple[float, float, float]
    finger_scale: float
    thumb_pose: tuple[tuple[str, float], ...]
    thumb_rank: int


def load_thumb_candidates(limit: int) -> list[dict[str, float]]:
    fallback = [dict(THUMB_CLOSE_TARGETS)]
    if not THUMB_AUDIT_JSON.exists():
        return fallback
    try:
        payload = json.loads(THUMB_AUDIT_JSON.read_text(encoding="utf-8"))
        rows = payload.get("best_by_score", [])
    except Exception:
        return fallback
    candidates: list[dict[str, float]] = []
    seen = set()
    for row in rows:
        pose = {name: float(row.get("applied_pose", {}).get(name, 0.0)) for name in THUMB_JOINTS}
        key = tuple(sorted(pose.items()))
        if key in seen:
            continue
        seen.add(key)
        candidates.append(pose)
        if len(candidates) >= limit:
            break
    return candidates or fallback


def scaled_targets(stage: str, finger_scale: float, thumb_pose: dict[str, float]) -> dict[str, float]:
    targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    if stage == "open_hand":
        return targets
    if stage == "preshape":
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * 0.30 * finger_scale
        for name, value in thumb_pose.items():
            targets[name] = value * 0.25
        return targets
    if stage == "close_four_fingers":
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * finger_scale
        for name, value in thumb_pose.items():
            targets[name] = value * 0.25
        return targets
    if stage in {"close_thumb", "hold"}:
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * finger_scale
        targets.update(thumb_pose)
        return targets
    raise KeyError(stage)


def ball_body_position(model, data, mujoco) -> list[float]:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    return np.array(data.xpos[bid], dtype=float).tolist()


def reset_state(model, data, mujoco, ball_position: list[float]) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if data.ctrl.size:
        data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)


def step_stage(
    mujoco,
    model,
    data,
    act_map: dict[str, int],
    start_targets: dict[str, float],
    end_targets: dict[str, float],
    ball_position: list[float],
    steps: int,
    pin_ball: bool,
) -> dict[str, float]:
    applied = {}
    for step in range(max(steps, 1)):
        command = blend(start_targets, end_targets, (step + 1) / max(steps, 1))
        applied = set_ctrl(model, data, command, act_map)
        if pin_ball:
            set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_step(model, data)
    if pin_ball:
        set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    return applied


def stage_steps(stage: str, speed: float) -> int:
    base = {
        "open_hand": 80,
        "preshape": 120,
        "close_four_fingers": 220,
        "close_thumb": 260,
        "hold": 220,
    }[stage]
    return max(20, int(base / max(speed, 0.05)))


def classify_trial(result: dict) -> str:
    open_stage = result["stages"]["open_hand"]
    hold = result["stages"]["hold"]
    if open_stage["ball_contact_count"] != 0:
        return "FAIL_INITIAL_OVERLAP"
    if hold["mean_four_tip_distance"] is None or hold["thumb_to_ball"] is None:
        return "FAIL_MISSING_METRICS"
    wrap = (
        hold["ball_contact_count"] >= 2
        and hold["mean_four_tip_distance"] <= 0.045
        and hold["thumb_to_ball"] <= 0.10
        and hold["max_penetration"] <= 0.015
    )
    if result["mode"] == "pinned":
        return "PINNED_WRAP_PASS" if wrap else "PINNED_PARTIAL"
    release = result.get("release") or {}
    drift = release.get("ball_drift_after_release")
    drop = release.get("ball_z_drop_after_release")
    release_contacts = int((release.get("summary") or {}).get("ball_contact_count", 0))
    if wrap and drift is not None and drift <= 0.035 and release_contacts >= 1:
        if result["mode"] == "free_zero_g":
            return "ZERO_G_RELEASE_RETAINED"
        if result["mode"] == "free_gravity" and drop is not None and drop <= 0.04:
            return "GRAVITY_RELEASE_RETAINED"
    if wrap:
        return "WRAP_BEFORE_RELEASE_ONLY"
    return "PARTIAL_OR_FAIL"


def score_trial(result: dict) -> float:
    hold = result["stages"]["hold"]
    mean_four = hold.get("mean_four_tip_distance") or 1.0
    thumb_ball = hold.get("thumb_to_ball") or 1.0
    contacts = min(int(hold.get("ball_contact_count", 0)), 5)
    penetration = float(hold.get("max_penetration", 0.0))
    release = result.get("release") or {}
    drift = release.get("ball_drift_after_release", 0.0 if result["mode"] == "pinned" else 1.0)
    release_contacts = int((release.get("summary") or {}).get("ball_contact_count", 0))
    release_contact_penalty = 0.04 if result["mode"] != "pinned" and release_contacts == 0 else 0.0
    return float(mean_four + 0.6 * thumb_ball + 1.5 * penetration + 0.6 * drift + release_contact_penalty - 0.004 * contacts)


def run_trial(mujoco, model, data, config: TrialConfig, speed: float, release_steps: int) -> dict:
    mode = config.mode
    ball_position = list(config.ball_position)
    thumb_pose = dict(config.thumb_pose)
    if mode == "free_gravity":
        model.opt.gravity[:] = [0.0, 0.0, -9.81]
    else:
        model.opt.gravity[:] = [0.0, 0.0, 0.0]
    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    reset_state(model, data, mujoco, ball_position)
    previous = scaled_targets("open_hand", config.finger_scale, thumb_pose)
    set_ctrl(model, data, previous, act_map)
    mujoco.mj_forward(model, data)
    stages = {}
    for stage in STAGE_ORDER:
        targets = scaled_targets(stage, config.finger_scale, thumb_pose)
        pin_ball = True
        applied = step_stage(
            mujoco,
            model,
            data,
            act_map,
            previous,
            targets,
            ball_position,
            stage_steps(stage, speed),
            pin_ball,
        )
        stages[stage] = stage_summary(model, data, mujoco, joints, targets, applied)
        stages[stage]["ball_body_position"] = ball_body_position(model, data, mujoco)
        previous = targets

    release = None
    if mode != "pinned":
        release_start = np.array(ball_body_position(model, data, mujoco), dtype=float)
        for _ in range(max(release_steps, 1)):
            set_ctrl(model, data, previous, act_map)
            mujoco.mj_step(model, data)
        mujoco.mj_forward(model, data)
        release_end = np.array(ball_body_position(model, data, mujoco), dtype=float)
        release_summary = stage_summary(model, data, mujoco, joints, previous, {name: float(data.ctrl[aid]) for name, aid in act_map.items()})
        release = {
            "release_start_ball": release_start.tolist(),
            "release_end_ball": release_end.tolist(),
            "ball_drift_after_release": float(np.linalg.norm(release_end - release_start)),
            "ball_z_drop_after_release": float(release_start[2] - release_end[2]),
            "summary": release_summary,
        }

    result = {
        "mode": mode,
        "ball_position": ball_position,
        "finger_scale": config.finger_scale,
        "thumb_rank": config.thumb_rank,
        "thumb_pose": thumb_pose,
        "stages": stages,
        "release": release,
        "notes": [
            "Position actuators are driven through data.ctrl; this script does not train or use tendon routing.",
            "The ball is pinned through scripted closing, then released after hold for free modes to probe retention.",
        ],
    }
    result["classification"] = classify_trial(result)
    result["score"] = score_trial(result)
    return result


def render_trial(result: dict, suffix: str) -> list[dict]:
    mujoco, model, data = load_model(SCENE_XML)
    mode = result["mode"]
    model.opt.gravity[:] = [0.0, 0.0, -9.81] if mode == "free_gravity" else [0.0, 0.0, 0.0]
    act_map = actuator_map(model, mujoco)
    thumb_pose = result["thumb_pose"]
    ball_position = result["ball_position"]
    reset_state(model, data, mujoco, ball_position)
    previous = scaled_targets("open_hand", result["finger_scale"], thumb_pose)
    renders = []
    out_dir = OUT_DIR / suffix
    out_dir.mkdir(parents=True, exist_ok=True)
    for stage in STAGE_ORDER:
        targets = scaled_targets(stage, result["finger_scale"], thumb_pose)
        pin_ball = True
        step_stage(mujoco, model, data, act_map, previous, targets, ball_position, stage_steps(stage, 3.0), pin_ball)
        renders.append(render_png(model, data, mujoco, "full_hand_with_ball", out_dir / STAGE_TO_FILE.get(stage, f"{stage}.png"), width=1200, height=850))
        if stage == "hold":
            renders.append(render_png(model, data, mujoco, "palm", out_dir / "hold_palm.png", width=1200, height=850))
        previous = targets
    if mode != "pinned":
        for _ in range(260):
            set_ctrl(model, data, previous, act_map)
            mujoco.mj_step(model, data)
        mujoco.mj_forward(model, data)
        renders.append(render_png(model, data, mujoco, "full_hand_with_ball", out_dir / "release_end.png", width=1200, height=850))
        renders.append(render_png(model, data, mujoco, "palm", out_dir / "release_end_palm.png", width=1200, height=850))
    return renders


def capability_ladder(results: list[dict]) -> dict:
    classes = {item["classification"] for item in results}
    return {
        "pinned_wrap": "PINNED_WRAP_PASS" in classes,
        "zero_g_release_retained": "ZERO_G_RELEASE_RETAINED" in classes,
        "gravity_release_retained": "GRAVITY_RELEASE_RETAINED" in classes,
        "best_level": (
            "gravity_release_retained"
            if "GRAVITY_RELEASE_RETAINED" in classes
            else "zero_g_release_retained"
            if "ZERO_G_RELEASE_RETAINED" in classes
            else "pinned_wrap"
            if "PINNED_WRAP_PASS" in classes
            else "partial"
        ),
    }


def classification_rank(item: dict) -> tuple[int, float]:
    ranks = {
        "GRAVITY_RELEASE_RETAINED": 0,
        "ZERO_G_RELEASE_RETAINED": 0,
        "PINNED_WRAP_PASS": 0,
        "WRAP_BEFORE_RELEASE_ONLY": 1,
        "PINNED_PARTIAL": 2,
        "PARTIAL_OR_FAIL": 3,
        "FAIL_MISSING_METRICS": 4,
        "FAIL_INITIAL_OVERLAP": 5,
    }
    return (ranks.get(item.get("classification"), 9), float(item.get("score", 999.0)))


def count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Export3 Shadow-Style Scripted Task Report",
        "",
        f"- Scene: `{report['scene']}`",
        f"- Trial count: {report['trial_count']}",
        f"- Modes: `{report['modes']}`",
        f"- Ball sweep: `{report['ball_sweep']}`",
        f"- Finger scales: `{report['finger_scales']}`",
        f"- Thumb candidates used: {report['thumb_candidate_count']}",
        f"- Capability best level: **{report['capability_ladder']['best_level']}**",
        "",
        "## Capability Ladder",
        "",
        f"- Pinned visual/contact wrap: {'PASS' if report['capability_ladder']['pinned_wrap'] else 'not achieved'}",
        f"- Zero-gravity release retained: {'PASS' if report['capability_ladder']['zero_g_release_retained'] else 'not achieved'}",
        f"- Gravity release retained: {'PASS' if report['capability_ladder']['gravity_release_retained'] else 'not achieved'}",
        "",
        "## Classification Counts",
        "",
    ]
    for name, count in report["classification_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Classification Counts By Mode", ""])
    for mode, counts in report["classification_counts_by_mode"].items():
        lines.append(f"- {mode}: `{counts}`")
    lines.extend(
        [
            "",
        "## Best By Mode",
        "",
        "| Mode | Class | Ball | Finger scale | Thumb pose | Contacts | Penetration | Mean four-tip | Thumb-ball | Release drift |",
        "|---|---|---|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for mode, item in report["best_by_mode"].items():
        hold = item["stages"]["hold"]
        release = item.get("release") or {}
        lines.append(
            f"| {mode} | {item['classification']} | `{item['ball_position']}` | {item['finger_scale']:.2f} | `{item['thumb_pose']}` | "
            f"{hold.get('ball_contact_count', 0)} | {hold.get('max_penetration', 0.0):.6f} | "
            f"{hold.get('mean_four_tip_distance', 0.0):.6f} | {hold.get('thumb_to_ball', 0.0):.6f} | "
            f"{release.get('ball_drift_after_release', 0.0):.6f} |"
        )
    lines.extend(["", "## Best Overall Trials", ""])
    lines.extend(
        [
            "| Rank | Mode | Class | Ball | Finger scale | Thumb-ball | Mean four-tip | Penetration | Score |",
            "|---:|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for idx, item in enumerate(report["best_overall"][:12], 1):
        hold = item["stages"]["hold"]
        lines.append(
            f"| {idx} | {item['mode']} | {item['classification']} | `{item['ball_position']}` | {item['finger_scale']:.2f} | "
            f"{hold.get('thumb_to_ball', 0.0):.6f} | {hold.get('mean_four_tip_distance', 0.0):.6f} | "
            f"{hold.get('max_penetration', 0.0):.6f} | {item['score']:.6f} |"
        )
    lines.extend(["", "## Rendered Best Trials", ""])
    for item in report.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(
        [
            "",
            "## Shadow-Style Task API Sketch",
            "",
            "- Reset: set hand to exported open/neutral actuator limits and place a ball from a small pose grid.",
            "- Observation: joint qpos, actuator targets, fingertip-to-ball distances, thumb-index distance, ball pose, and ball contact summary.",
            "- Action: 21-D position actuator target vector, currently generated by a staged scripted policy.",
            "- Success metrics: no initial overlap, multi-finger contact, low penetration, thumb close to ball/index, and object retention after release.",
            "- Current status: diagnostic scripted scaffold only; not training-ready.",
            "",
            "## Interpretation",
            "",
        ]
    )
    lines.extend(f"- {line}" for line in report["interpretation"])
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def interpret(report: dict) -> list[str]:
    ladder = report["capability_ladder"]
    lines = []
    if ladder["pinned_wrap"]:
        lines.append("Export3 can achieve a Shadow-style scripted pinned-ball wrap/contact smoke test.")
    else:
        lines.append("Export3 did not reliably achieve even pinned-ball wrap under this sweep.")
    if ladder["zero_g_release_retained"]:
        lines.append("At least one zero-gravity release trial retained the ball near the hand after closing.")
    else:
        lines.append("Zero-gravity release did not satisfy the retention threshold; the grasp is still mainly a pinned-ball smoke test.")
    if ladder["gravity_release_retained"]:
        lines.append("A gravity release trial passed the retention threshold.")
    else:
        lines.append("Gravity release retention was not achieved; do not treat this as a stable physical grasp.")
    lines.append("The current ceiling is diagnostic scripted grasp scaffolding, not RL/BC training or final Shadow equivalence.")
    lines.append("Next limiting factors are collision proxy fidelity, actuator gain/contact tuning, and final thumb axis/limit confirmation.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Run export3 Shadow-style staged scripted grasp task sweep.")
    parser.add_argument("--thumb-candidates", type=int, default=5)
    parser.add_argument("--speed", type=float, default=3.0)
    parser.add_argument("--release-steps", type=int, default=260)
    parser.add_argument("--render-best", action="store_true", default=True)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    thumb_candidates = load_thumb_candidates(args.thumb_candidates)
    configs = []
    for mode in MODES:
        for ball in BALL_SWEEP:
            for scale in FINGER_SCALES:
                for idx, thumb in enumerate(thumb_candidates, 1):
                    configs.append(TrialConfig(mode, tuple(ball), scale, tuple(sorted(thumb.items())), idx))
    mujoco, model, data = load_model(SCENE_XML)
    results = []
    for index, config in enumerate(configs, 1):
        result = run_trial(mujoco, model, data, config, args.speed, args.release_steps)
        results.append(result)
        if index % 25 == 0:
            print(f"completed {index}/{len(configs)} trials")
    best_overall = sorted(results, key=classification_rank)
    best_by_mode = {}
    renders = []
    class_counts = count_by(results, "classification")
    class_counts_by_mode = {}
    for mode in MODES:
        mode_rows = [item for item in results if item["mode"] == mode]
        best_by_mode[mode] = sorted(mode_rows, key=classification_rank)[0]
        class_counts_by_mode[mode] = count_by(mode_rows, "classification")
    if args.render_best and not args.no_render:
        for mode, item in best_by_mode.items():
            renders.extend(render_trial(item, f"best_{mode}"))
    report = {
        "scene": str(SCENE_XML),
        "trial_count": len(results),
        "modes": MODES,
        "ball_sweep": BALL_SWEEP,
        "finger_scales": FINGER_SCALES,
        "thumb_candidate_count": len(thumb_candidates),
        "results": results,
        "best_overall": best_overall[:20],
        "best_by_mode": best_by_mode,
        "capability_ladder": capability_ladder(results),
        "classification_counts": class_counts,
        "classification_counts_by_mode": class_counts_by_mode,
        "renders": renders,
    }
    report["interpretation"] = interpret(report)
    write_outputs(report)
    compact_best = {}
    for mode, item in best_by_mode.items():
        hold = item["stages"]["hold"]
        compact_best[mode] = {
            "classification": item["classification"],
            "ball_position": item["ball_position"],
            "finger_scale": item["finger_scale"],
            "thumb_pose": item["thumb_pose"],
            "hold_contacts": hold.get("ball_contact_count"),
            "hold_penetration": hold.get("max_penetration"),
            "mean_four_tip_distance": hold.get("mean_four_tip_distance"),
            "thumb_to_ball": hold.get("thumb_to_ball"),
            "release_drift": (item.get("release") or {}).get("ball_drift_after_release"),
        }
    print(
        json.dumps(
            {
                "trial_count": report["trial_count"],
                "capability_ladder": report["capability_ladder"],
                "best_by_mode": compact_best,
                "interpretation": report["interpretation"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
