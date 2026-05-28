#!/usr/bin/env python3
"""Compare Shadow Hand and the arm+hand export4 collision-v2 assembly.

This keeps the same recorded-video open/close diagnostic used earlier for the
hand-only export4 baseline, but runs our current arm+hand v2 model. The first
four arm actuators stay at zero; only the hand actuators receive the mapped
open/close controls. No ball and no training are used.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[2]
HAND_SCRIPT = PROJECT_ROOT / "simulations" / "models" / "hand_stage1_export" / "scripts" / "run_export4_shadow_video_comparison.py"
REPORT = ROOT / "docs" / "arm_hand_stage1_v2_shadow_video_comparison_report.md"
META = ROOT / "metadata" / "arm_hand_stage1_v2_shadow_video_comparison.json"
VIS = ROOT / "docs" / "visual_checks_arm_hand_stage1_v2_shadow_video_compare"
ARCHIVE = ROOT / "archive"
ARM_HAND_XML = ROOT / "mjcf" / "scene_arm_hand_export4_collision_proxy_v2.xml"


def load_hand_compare_module():
    if not HAND_SCRIPT.exists():
        raise FileNotFoundError(HAND_SCRIPT)
    spec = importlib.util.spec_from_file_location("export4_shadow_video_comparison", HAND_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import comparison helper: {HAND_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = ARCHIVE / f"{path.name}.before_arm_hand_v2_compare_{stamp}"
    if path.is_dir():
        shutil.copytree(path, dst)
    else:
        shutil.copy2(path, dst)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def arm_hand_controls_from_features(comp, features: np.ndarray, model, mujoco) -> np.ndarray:
    actuator_names = [comp._mj_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) for idx in range(model.nu)]
    actuator_index = {name: idx for idx, name in enumerate(actuator_names)}
    missing = [name for name in comp.EXPORT4_ACTUATOR_NAMES if name not in actuator_index]
    if missing:
        raise ValueError(f"arm+hand scene is missing hand actuators: {missing}")

    hand_ctrlrange = np.asarray(
        [model.actuator_ctrlrange[actuator_index[name]] for name in comp.EXPORT4_ACTUATOR_NAMES],
        dtype=np.float32,
    )
    hand_controls = comp.export4_controls_from_open_close(features, hand_ctrlrange)
    full_controls = np.zeros((features.shape[0], model.nu), dtype=np.float32)
    for hand_idx, actuator_name in enumerate(comp.EXPORT4_ACTUATOR_NAMES):
        full_controls[:, actuator_index[actuator_name]] = hand_controls[:, hand_idx]
    return full_controls


def install_arm_hand_closeup_renderer(comp) -> None:
    original_render_frame = comp._render_frame

    def render_frame(model, data, camera_name: str | None, width: int, height: int):
        if camera_name != "__free_arm_hand_palm_closeup":
            return original_render_frame(model, data, camera_name, width, height)

        import mujoco

        palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
        lookat = data.xpos[palm_id].copy() if palm_id >= 0 else model.stat.center.copy()
        renderer = mujoco.Renderer(model, width=width, height=height)
        try:
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = lookat
            camera.distance = 0.34
            camera.azimuth = 205.0
            camera.elevation = -24.0
            renderer.update_scene(data, camera=camera)
            return renderer.render().copy()
        finally:
            renderer.close()

    comp._render_frame = render_frame


def write_report(report_path: Path, metadata_path: Path, payload: dict[str, Any]) -> None:
    aggregate = payload["aggregate"]
    results = payload["results"]
    lines = [
        "# Arm+Hand Stage1 v2 vs Shadow Video Comparison\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This diagnostic maps the same recorded open/close video features to Shadow Hand and to the current arm+hand export4 v2 assembly. "
        "The ball is removed; the purpose is to check whether both hands can replay closure-like motion and produce comparable geometry metrics. "
        "No training, tendon routing, CAD edit, STL edit, joint-tree edit, or joint-name edit was performed.\n\n",
        "## Inputs\n\n",
        f"- Manifest: `{payload['manifest']}`\n",
        f"- Shadow scene: `{payload['shadow_xml']}`\n",
        f"- Arm+hand scene: `{payload['arm_hand_xml']}`\n",
        f"- Visual output: `{payload['visual_dir']}`\n\n",
        "## Aggregate\n\n",
        f"- Videos processed: `{aggregate['videos_processed']}` / `{aggregate['videos_total']}`\n",
        f"- Shadow failures: `{aggregate['shadow_failures']}`\n",
        f"- Arm+hand failures: `{aggregate['arm_hand_failures']}`\n",
        f"- Shadow mean closure score: `{aggregate['shadow_closure_score_mean']:.4f}`\n",
        f"- Arm+hand v2 mean closure score: `{aggregate['arm_hand_closure_score_mean']:.4f}`\n",
        f"- Score correlation: `{aggregate['score_correlation']}`\n\n",
    ]
    first_ok = next((item for item in results if item.get("shadow", {}).get("status") == "ok" and item.get("arm_hand", {}).get("status") == "ok"), None)
    if first_ok:
        shadow_summary = first_ok["shadow"]["model_summary"]
        arm_summary = first_ok["arm_hand"]["model_summary"]
        lines.extend(
            [
                "## Model Summary\n\n",
                f"- Shadow: `{shadow_summary.get('bodies')}` bodies, `{shadow_summary.get('joints')}` joints, `{shadow_summary.get('actuators')}` actuators, `{shadow_summary.get('geoms')}` geoms, `{shadow_summary.get('sites')}` sites.\n",
                f"- Arm+hand v2: `{arm_summary.get('bodies')}` bodies, `{arm_summary.get('joints')}` joints, `{arm_summary.get('actuators')}` actuators, `{arm_summary.get('geoms')}` geoms, `{arm_summary.get('sites')}` sites.\n\n",
            ]
        )
    lines.extend(
        [
            "## Per-Video Results\n\n",
            "| video | frames | curl range | Shadow score | Arm+hand v2 score | Shadow tip delta | Arm+hand tip delta | Arm+hand thumb-index close | sheet |\n",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for item in results:
        if item.get("shadow", {}).get("status") != "ok" or item.get("arm_hand", {}).get("status") != "ok":
            lines.append(
                f"| {item.get('video_stem', 'unknown')[:10]} | - | - | fail | fail | - | - | - | {item.get('reason', '')} |\n"
            )
            continue
        shadow = item["shadow"]
        arm = item["arm_hand"]
        sheet = f"`{item.get('comparison_sheet', '')}`" if item.get("comparison_sheet") else ""
        lines.append(
            f"| {item['video_stem'][:10]} | {item['input']['frames']} | {item['input']['curl_range']:.3f} | "
            f"{shadow['closure_score']:.3f} | {arm['closure_score']:.3f} | "
            f"{shadow['tip_palm_distance_reduction']:.4f} | {arm['tip_palm_distance_reduction']:.4f} | "
            f"{arm['close_thumb_index_distance']:.4f} | {sheet} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- Passing here means the video-to-control pathway can drive both the Shadow reference model and our arm+hand stage1 model through a comparable open/close motion.\n",
            "- This does not prove stable object grasp, because the ball is intentionally removed from this comparison.\n",
            "- The arm+hand model now includes the mechanical arm context; arm actuators are held at zero during this hand-closure diagnostic.\n",
            "- Current collision v2 is useful for smoke tests, but collision fidelity is still not training-ready.\n\n",
            f"Machine-readable summary: `{metadata_path}`\n",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    comp = load_hand_compare_module()
    defaults = comp._default_paths()
    parser = argparse.ArgumentParser(description="Run arm+hand stage1 v2 vs Shadow video open/close comparison.")
    parser.add_argument("--manifest", default=str(defaults["manifest"]))
    parser.add_argument("--shadow-xml", default=str(defaults["shadow_xml"]))
    parser.add_argument("--arm-hand-xml", default=str(ARM_HAND_XML))
    parser.add_argument("--report", default=str(REPORT))
    parser.add_argument("--metadata", default=str(META))
    parser.add_argument("--visual-dir", default=str(VIS))
    parser.add_argument("--max-videos", type=int, default=0, help="0 means all videos")
    parser.add_argument("--max-keyframes", type=int, default=5)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--substeps", type=int, default=2)
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--no-render", action="store_true")
    return parser


def main() -> None:
    comp = load_hand_compare_module()
    install_arm_hand_closeup_renderer(comp)
    args = build_arg_parser().parse_args()
    manifest_path = Path(args.manifest).resolve()
    shadow_xml = Path(args.shadow_xml).resolve()
    arm_hand_xml = Path(args.arm_hand_xml).resolve()
    report_path = Path(args.report).resolve()
    metadata_path = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    for path in (manifest_path, shadow_xml, arm_hand_xml):
        if not path.exists():
            raise FileNotFoundError(path)
    for output in (report_path, metadata_path):
        backup_existing(output)
    if visual_dir.exists():
        backup_existing(visual_dir)

    import mujoco

    manifest = comp._load_json(manifest_path)
    items = list(manifest.get("items", []))
    if args.max_videos > 0:
        items = items[: args.max_videos]

    shadow_model = mujoco.MjModel.from_xml_path(str(shadow_xml))
    arm_model = mujoco.MjModel.from_xml_path(str(arm_hand_xml))
    shadow_spec = comp.ModelSpec(
        name="shadow",
        xml_path=shadow_xml,
        palm_body="rh_palm",
        palm_site="grasp_site",
        actuator_names=[comp._mj_name(shadow_model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) for idx in range(shadow_model.nu)],
        closure_joint_names=comp.SHADOW_CLOSURE_JOINTS,
        camera_name="shadow_compare_front",
    )
    arm_hand_spec = comp.ModelSpec(
        name="export4",
        xml_path=arm_hand_xml,
        palm_body="palm_link",
        palm_site=None,
        actuator_names=[comp._mj_name(arm_model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) for idx in range(arm_model.nu)],
        closure_joint_names=comp.EXPORT4_CLOSURE_JOINTS,
        camera_name="__free_arm_hand_palm_closeup",
    )

    visual_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for item in items:
        video_name = str(item.get("video_name") or Path(str(item.get("video", ""))).name)
        video_stem = Path(video_name).stem
        retarget_path = comp._resolve_repo_relative(item.get("retarget", ""))
        if not retarget_path.exists():
            results.append({"video_stem": video_stem, "status": "failed", "reason": f"missing retarget: {retarget_path}"})
            continue

        npz = np.load(retarget_path, allow_pickle=True)
        landmarks = np.asarray(npz["landmarks"], dtype=np.float32)
        shadow_actions = np.asarray(npz["actions"], dtype=np.float32)
        features = comp.open_close_features_from_landmarks(landmarks)
        if features.shape[0] != shadow_actions.shape[0]:
            n = min(features.shape[0], shadow_actions.shape[0])
            features = features[:n]
            shadow_actions = shadow_actions[:n]

        global_curl = features[:, comp._feature_index("global_curl_mean")]
        open_idx = int(np.argmin(global_curl))
        close_idx = int(np.argmax(global_curl))
        keyframes = comp._keyframes(features.shape[0], open_idx, close_idx, args.max_keyframes)
        shadow_controls = comp._normalized_to_ctrl(shadow_actions, shadow_model.actuator_ctrlrange)
        arm_controls = arm_hand_controls_from_features(comp, features, arm_model, mujoco)

        video_visual_dir = visual_dir / video_stem
        render_shadow = None if args.no_render else video_visual_dir / "shadow"
        render_arm = None if args.no_render else video_visual_dir / "arm_hand_stage1_v2"
        result = {
            "video_name": video_name,
            "video_stem": video_stem,
            "manifest_status": item.get("status", "unknown"),
            "review_reasons": item.get("review_reasons", []),
            "input": {
                "frames": int(features.shape[0]),
                "feature_dim": int(features.shape[1]),
                "curl_min": float(np.min(global_curl)),
                "curl_max": float(np.max(global_curl)),
                "curl_range": float(np.max(global_curl) - np.min(global_curl)),
                "open_idx": open_idx,
                "close_idx": close_idx,
                "keyframes": keyframes,
                "retarget": str(retarget_path),
            },
        }

        try:
            shadow_sim = comp.simulate_controls(
                shadow_spec,
                shadow_controls,
                keyframes=keyframes,
                render_dir=render_shadow,
                width=args.width,
                height=args.height,
                substeps=args.substeps,
                settle_steps=args.settle_steps,
            )
            result["shadow"] = comp.summarize_model_run(shadow_sim, shadow_controls, open_idx, close_idx)
            result["shadow"]["model_summary"] = shadow_sim["model_summary"]
        except Exception as exc:
            result["shadow"] = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}", "closure_score": 0.0}

        try:
            arm_sim = comp.simulate_controls(
                arm_hand_spec,
                arm_controls,
                keyframes=keyframes,
                render_dir=render_arm,
                width=args.width,
                height=args.height,
                substeps=args.substeps,
                settle_steps=args.settle_steps,
            )
            result["arm_hand"] = comp.summarize_model_run(arm_sim, arm_controls, open_idx, close_idx)
            result["arm_hand"]["model_summary"] = arm_sim["model_summary"]
        except Exception as exc:
            result["arm_hand"] = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}", "closure_score": 0.0}

        if not args.no_render:
            sheet = comp._write_contact_sheet(
                {
                    "Shadow Hand": result.get("shadow", {}).get("render_paths", []),
                    "arm+hand stage1 v2": result.get("arm_hand", {}).get("render_paths", []),
                },
                video_visual_dir / "shadow_arm_hand_v2_keyframe_comparison.png",
            )
            result["comparison_sheet"] = sheet

        print(
            f"{video_stem}: shadow={result['shadow'].get('closure_score', 0):.3f} "
            f"arm_hand_v2={result['arm_hand'].get('closure_score', 0):.3f}"
        )
        results.append(result)

    ok_results = [
        item
        for item in results
        if item.get("shadow", {}).get("status") == "ok" and item.get("arm_hand", {}).get("status") == "ok"
    ]
    shadow_scores = np.asarray([item["shadow"]["closure_score"] for item in ok_results], dtype=np.float32)
    arm_scores = np.asarray([item["arm_hand"]["closure_score"] for item in ok_results], dtype=np.float32)
    score_corr = None
    if shadow_scores.size >= 2 and float(np.std(shadow_scores)) > 1e-8 and float(np.std(arm_scores)) > 1e-8:
        score_corr = float(np.corrcoef(shadow_scores, arm_scores)[0, 1])

    aggregate = {
        "videos_total": len(items),
        "videos_processed": len(ok_results),
        "shadow_failures": sum(1 for item in results if item.get("shadow", {}).get("status") != "ok"),
        "arm_hand_failures": sum(1 for item in results if item.get("arm_hand", {}).get("status") != "ok"),
        "shadow_closure_score_mean": float(np.mean(shadow_scores)) if shadow_scores.size else 0.0,
        "arm_hand_closure_score_mean": float(np.mean(arm_scores)) if arm_scores.size else 0.0,
        "score_correlation": score_corr,
        "rendered_video_count": sum(1 for item in results if item.get("comparison_sheet")),
    }
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": "arm_hand_stage1_v2_shadow_video_open_close_comparison_v1",
        "manifest": manifest_path,
        "shadow_xml": shadow_xml,
        "arm_hand_xml": arm_hand_xml,
        "visual_dir": visual_dir,
        "adapter": {
            "shadow": "existing vision_shadow_retarget 24D normalized action",
            "arm_hand_stage1_v2": "hand_open_close_feature_v1_to_export4_hand_position_control; arm actuators held at zero",
            "training_used": False,
            "ball_used": False,
        },
        "manifest_summary": manifest.get("summary", {}),
        "aggregate": aggregate,
        "results": results,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(report_path, metadata_path, json_ready(payload))
    print(f"Saved report: {report_path}")
    print(f"Saved metadata: {metadata_path}")


if __name__ == "__main__":
    main()
